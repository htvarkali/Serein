# Methods (plain English first, math second)

## Model 1: SmokeCast

### The problem with today's forecasts
NOAA's HRRR-Smoke simulates where smoke goes using estimated fire emissions and
weather. It's physically smart but often wrong about *how much* smoke reaches
the ground at a given place, and it doesn't look at live sensor readings. NOAA's
AQM is bias-corrected, but only against regulatory monitors and with a slow
statistical correction.

### Our idea
Treat the air sensors as a **network** (a graph). Every sensor is a node; it is
connected to its 10 nearest neighbors within 300 km. A graph neural network (GNN)
lets every sensor "listen" to its neighbors, paying more attention to neighbors
that are **upwind** (our original hypothesis; see the ablation note below). Smoke that is over Redding this morning, with a north wind,
will be over Sacramento tonight.

The GNN doesn't forecast from scratch. It **corrects** NOAA's forecast:

```
forecast = NOAA's AQM forecast  +  learned correction
           (or yesterday's value when AQM doesn't reach that far)
```

So it starts from the physics and only needs to learn where the physics goes
wrong. This is much easier to learn with a few seasons of data.

### Inputs at every node (see `serein/features/table.py`)
- Sensor readings available at issue time: last 1, 3, 6, 24 h, yesterday's mean, 24 h max
- HRRR-Smoke near-surface smoke for each lead day (mean, max)
- HRRR column smoke (smoke aloft that can mix down), wind, boundary-layer height, temperature, humidity
- NOAA AQM bias-corrected PM2.5 for each lead day
- Yesterday's HMS smoke-plume density
- Fire radiative power within 50/100/250 km, and an "upwind fire" index (NOAA HMS fire points; no key needed)
- Location and day of year

### Network
1. Encoder: a small neural net turns each node's inputs into a 64-number summary by default.
2. Two rounds of message passing by default. In each round every node gathers messages
   from its neighbors. A neighbor's weight (attention) depends on both nodes'
   summaries, the distance and direction between them, and **how strongly the
   wind blows from the neighbor toward the node**.
3. Output head: for each lead day, 5 quantiles (5/25/50/75/95%) of the correction.

### Training
- Loss: pinball (quantile) loss, so the model learns ranges, not just one number.
- **Node masking:** each step hides 15% of sensors' readings but still asks the
  model to forecast there. This teaches it to forecast where there is *no*
  sensor, which is how we make neighborhood maps.
- Early stopping on even weeks of the calibration season.

### Honest uncertainty: conformal prediction
Neural nets tend to be over-confident. We use **Conformalized Quantile
Regression** (Romano et al., 2019). On calibration days we measure how far
reality fell outside our 90% range, then widen (or narrow) all future ranges by
just enough that 90% of calibration outcomes would have been inside. We do this
separately for clean, moderate, and smoky forecasts, so the range stays honest
on smoke days.

### Exporting the evaluated forecast

New runs save every seed's weights in a versioned artifact. Evaluation, map inference
and transfer use the same mean of member quantiles in log1p space, followed by one
shared calibration operation. Graph and no-graph comparisons use equal seed counts.
The calibrated interval is constrained to contain the median; inner quantiles are
constrained to that interval, and PM2.5 is bounded below by zero. Explanations retain
gradients through the ensemble and average last-layer attention across members.

Older artifacts still load with a warning, but their missing ensemble members cannot
be reconstructed. Regenerate them using development training. Historical numbers below
predate these fixes and need a development rerun before describing the revised system.

Unavailable HMS maps produce missing features, not zero smoke. Only an available map
reporting zero smoke contributes to the clean-day site background. This changes the
feature table: rebuild cached tables before retraining.

### Math summary
Let x_i be node i's features, h_i^0 = MLP(x_i). For layer ℓ:

    e_ji = [static_ji, w_j·u_ji, w_i·u_ji, |w_j|]        (u_ji = unit vector j→i, w = wind)
    a_ji = softmax_j( MLP_a([h_j, h_i, e_ji]) )           (per head)
    h_i ← LN(h_i + Σ_j a_ji · MLP_m([h_j, h_i, e_ji]));  h_i ← LN(h_i + FFN(h_i))

Output: q_i,L = base_i,L + [m − Σ softplus(·), m, m + Σ softplus(·)] (non-crossing),
in log1p(µg/m³) space. Loss Σ_τ max(τ(y−q_τ), (τ−1)(y−q_τ)).

### Which inputs matter? (ablations, 2026-11-01, dev weeks of 2023)

Each row hides one input group from SmokeCast (3-seed ensembles; `scripts/run_ablations.sh`).
RMSE in µg/m³; percentages are how much worse than the full model.

| Removed | Today | +1 day | +2 days | +3 days |
|---|---|---|---|---|
| nothing (full model) | 4.45 | 7.85 | 9.71 | 11.33 |
| live sensor readings | 7.37 (+66%) | 8.79 (+12%) | 10.48 (+8%) | 12.13 (+7%) |
| HRRR-Smoke + HRRR weather | 5.04 (+13%) | 10.15 (+29%) | 11.28 (+16%) | 11.85 (+5%) |
| NOAA AQM | 5.07 (+14%) | 8.39 (+7%) | 10.72 (+10%) | 12.47 (+10%) |
| HMS smoke plumes | 4.47 (0%) | 8.23 (+5%) | 10.18 (+5%) | 11.68 (+3%) |
| satellite fire detections | 4.64 (+4%) | 8.19 (+4%) | 9.85 (+1%) | 11.52 (+2%) |
| wind direction on graph edges | 4.52 (+1%) | 7.85 (0%) | 9.73 (0%) | 11.32 (0%) |

(Rerun 2026-11-02 with repeatable training: the same seed now gives the same model, so
these numbers reproduce exactly. Earlier fixes still apply: no self-edges in the graph,
and the no-sensor row also hides `hrrr_pm`, which carries each site's clean-air history.)

What this means:
- **No single source is enough.** Live sensors carry "today"; NOAA's physics models
  (HRRR, AQM) carry days 1-3. Serein's value is combining them.
- **Small gains.** Fire detections and HMS plume maps help only a little (1-5% on
  days 1-3; fires 4% today), likely because HRRR-Smoke already uses satellite fire
  data. Wind direction on graph edges adds nothing:
  every node already gets the wind as an input, so the network doesn't need it twice.
  Our original "listen to upwind neighbors" idea was not needed; the graph's value
  shows up as forecasting places with no sensor (leave-sites-out test).
- Differences under ~0.2 µg/m³ are within seed-to-seed noise.

### Why this forecast? (explainability, B-11)

`serein explain --date 2023-08-18 --point 530630047 --lead 1` answers two
questions for one place and day (code: `serein/eval/explain.py`):

- **Which inputs moved it.** Integrated gradients (Sundararajan et al., ICML 2017)
  from an "average day" (every input at its training mean, same missing-data
  pattern, same base forecast) to the real day. The parts add up exactly to the
  gap, shown as multipliers on PM2.5 + 1, grouped by source.
- **Which neighbors it listened to.** Attention weights from the last graph layer,
  averaged over heads (they add up to 1 for each place).

Example, Spokane, issued Aug 18, 2023, one day ahead: median 84 µg/m³ vs. 29 for an
average day. HRRR smoke raised it x9.2, fire detections x1.3; live readings (x0.52)
and AQM (x0.39) pulled it down. Top neighbors: monitors 14, 47 and 14 km away
(weights 0.34, 0.26, 0.15). Attention weights show what the model weighed, not
proof of cause; they are one layer of two.

## Model 2: AirPlan

### Idea
Every child starts with the same prior belief from published studies; each
logged day updates the belief about *this* child (Bayes' rule). We use logistic
regression for "symptom day yes/no" with a Gaussian prior and the Laplace
approximation (Newton's method with a line search, then the curvature as the
uncertainty). Features: forecast PM2.5, PM2.5 of the 2 previous days,
PM2.5 × time outdoors, colds, missed controller doses.

### From risk to a plan
We compare the child's predicted risk under tomorrow's forecast against the
same child on a clean-air day. The **smoke-caused** extra risk sets the zone.
Uncertainty from both the smoke forecast and the child model is carried through
by Monte Carlo sampling. Public EPA guidance sets a floor: personal plans can
only be stricter, never looser.

### Simulation study (synthetic children, `serein.personal.simulate`)
300 synthetic children, deliberately varied (25% very smoke-sensitive, 50%
typical, 25% not sensitive). Each child gets a simulated 150-day smoke season;
AirPlan learns from the first k days and is scored on the last 50 days, using
smoke *forecasts* with realistic error.

Result (2026-11-01, literature priors, `outputs/airplan/simulation_summary.csv`):
improvement in Brier score over the one-size-fits-all population model:

| days logged | very sensitive | typical | not sensitive |
|---|---|---|---|
| 14 | +2.5% | +2.6% | +2.5% |
| 30 | +5.6% | +3.6% | +3.7% |
| 60 | +8.4% | +4.1% | +4.8% |
| 100 | +10.2% | +5.0% | +6.9% |

After 100 days the 90% credible range of each child's smoke sensitivity contained
the true value 91% (very sensitive) to 98-100% (others) of the time. These are
SIMULATED children: the result shows the method can learn, not that real
children behave this way.

Lesson learned while building: the first version's Newton optimizer could
overshoot on extreme smoke days (PM2.5/10 = 25) and produce absurd estimates. A
line search fixed it (see `tests/test_personal.py`).

### Priors (TODO C-5, 2026-11-01) {#priors}

| Coefficient | Prior (odds ratio) | Evidence | Caveat |
|---|---|---|---|
| Clean-day symptom rate | 12% of days | In CDC's Asthma Call-back Survey classification, symptoms on more than 8 of 30 days (≥ 9, about 30%) make asthma *not well controlled* (adult survey table, Mazurek et al. 2015 supplement; used here for children as an approximation). Well controlled: 56% of children with current asthma in CDC's 21-state data, 2018-2020; 78% in Illinois, 2017 | Our assumption, below that threshold |
| Same-day PM2.5, per +10 µg/m³ | 1.04 (prior SD 0.25 on log scale) | Sugrue et al. 2026, *GeoHealth* 10(2):e2025GH001530: pediatric asthma hospital encounters, wildfire-specific PM2.5, RR 1.04 (0-8%) at lag 0 | Severe events, not daily symptoms; one region (Alameda/Contra Costa) |
| Prior 2 days PM2.5, per +10 µg/m³ | 1.03 (SD 0.20) | Same study: RR 1.02-1.04 at lags 3-4; cumulative RR 1.13 (1.09-1.18) over lags 0-5 | We simplify the lag structure to the 2 previous days (TODO: test longer lags) |
| Extra effect when outdoors | 1.02 (SD 0.15) | No pediatric estimate found | Assumption; outdoor time raises dose |
| Respiratory virus / cold | 4.0 (SD 0.5) | Khetsuriani et al. 2007, *J Allergy Clin Immunol* 119:314: any virus OR 5.6 (2.7-11.6), rhinovirus OR 6.8; a Hong Kong study found OR 2.77 (1.51-5.11) | Exacerbations, not daily symptoms |
| Missed controller medicine | 1.6 (SD 0.4) | Williams et al. 2011, *J Allergy Clin Immunol* 128:1185: HR 0.61 (0.41-0.90) for > 75% vs ≤ 25% ICS adherence; 24% of exacerbations attributable to nonadherence | Mixed-age cohort; some pediatric studies find reverse associations (confounding by severity) |
| 8-h ozone above 30 ppb, per +10 ppb (C-10) | 1.027 (SD 0.10) | Strickland et al. 2010, *Am J Respir Crit Care Med* 182:307, Table 2: pediatric asthma ED visits, Atlanta, warm season RR 1.082 (1.043-1.123) per 29.2 ppb (IQR) of 3-day average 8-h ozone; dose-response from about 30 ppb | ED visits, one city; scaled linearly to 10 ppb |
| Hot day, max ≥ 32 °C / 90 °F (C-10) | 1.0 (SD 0.4) | No verified pediatric per-day estimate: studies disagree (Brisbane: hot days raise child asthma ED visits; New York: lower risk for children with asthma) | Assumption centered on "no effect"; the child's log decides |
| High pollen day (C-10) | 1.0 (SD 0.4) | Only all-age evidence found (Atlanta, Darrow et al.: about +10-15% ED visits on 95th-percentile grass and oak days, as reported in the press; primary paper not yet checked) | Assumption centered on "no effect"; no free US pollen forecast, so this comes from the family's check-in |

Why the confounders (C-10): smoke season is also ozone, heat and pollen season.
Without these terms the model would blame smoke for their effect and
overestimate a child's smoke sensitivity. They also stay fixed in the clean-air
baseline that decides the zone (only the smoke is swapped out), so a hot or high-pollen
day by itself never triggers a smoke warning. All three default to "unknown" (no
effect), and the synthetic-children study gives identical results with them added.

Evidence we checked and chose **not** to use: Gent et al. 2009 (*Environ Health
Perspect* 117:1168), 149 children in New Haven, found no significant link between
total PM2.5 and daily symptoms, only for traffic-related particle sources (OR 1.10
per 5 µg/m³ for wheeze, 3-day average). An "OR 1.20 per 10 µg/m³" figure for
asthma attacks that turned up in search results could not be verified against
the paper, so it is not used.

Why wide SDs: published numbers are population averages for severe events. The
whole point of AirPlan is that individual children differ, so the prior must let
the log pull a child far from the average.
