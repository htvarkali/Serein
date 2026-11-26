# Experiments

Every model experiment, written down before it runs, with its result, including
failures. All runs are development runs: train 2021-22, calibrate 2023, scored on
the odd ISO weeks of 2023. The 2024-25 test seasons are never built or read.

Acceptance rule for a model change (all on numbers produced the same day):

1. Primary: RMSE vs. the current model per lead, day-block bootstrap (1000
   resamples). The 95% interval of RMSE(new) - RMSE(current) lies entirely below 0
   at lead 1 or lead 2, and no lead is worse with its interval entirely above 0.
2. Not worse: hidden-monitor RMSE (`--holdout-sites 0.2 --no-gbm`), smoke-day RMSE,
   USG CSI.
3. 90% interval coverage stays within 0.88-0.92.
4. Inner fold (train 2021, score 2022) also improves.

A change reaches `main` only with a line `ACCEPTANCE: PASS <run tags>`; otherwise
the record says `ACCEPTANCE: FAIL <reason>` and no model code is merged.

## 2026-11-23 B-15: peaks under-predicted at days 2-3

Current model (dev run `dev` on code 7334216, 2026-11-23): on site-days that turned
out at or above 35.5 µg/m³, the median forecast is a median 91% / 76% / 55% / 29% of
the observed value at leads 0-3. The shortfall grows with lead.

### Try 1: point forecast from the predictive mean (no retraining)

Hypothesis: RMSE is minimized by the mean, and the median of a right-skewed
distribution sits below it, so part of the peak shortfall could be the choice of
the median as the point forecast. Change: point = expm1(mu + k * s^2 / 2), with
mu = log1p(median) and s from the calibrated 90% range in log space (a log-normal
reading of the quantiles), k = 0.5 or 1. Evaluated on the saved dev predictions.

Result (RMSE current -> new, 95% interval of the difference):

| Lead | k = 0.5 | k = 1 |
|---|---|---|
| 0 | 4.362 -> 4.364 (-0.05, +0.05) | 4.362 -> 4.402 (-0.06, +0.14) |
| 1 | 7.776 -> 7.818 (-0.19, +0.32) | 7.776 -> 8.187 (-0.06, +0.95) |
| 2 | 9.721 -> 9.743 (-0.25, +0.42) | 9.721 -> 10.054 (-0.26, +1.17) |
| 3 | 11.584 -> 11.740 (-0.11, +0.51) | 11.584 -> 12.146 (-0.04, +1.36) |

Worse at every lead. The 6x smoke-day weight (B-13) already moves the median up,
so the shortfall at days 2-3 is not a median-versus-mean effect.
ACCEPTANCE: FAIL no lead improves; point-forecast rule unchanged.

### Try 2: larger smoke-day loss weight for leads 2 and 3

Hypothesis: one weight (6x) for every lead is a compromise. At days 2-3 the model
has fewer smoke inputs (HRRR stops at lead 1, AQM at lead 2), so the loss pulls it
toward clean air harder there. Raising the smoke-day weight for leads 2 and later
only (`--smoke-weight-late 12`, leads 0-1 stay at 6) should raise the day-2 and
day-3 peak capture. Expected cost: some false alarms on clean days. It passes only
if the acceptance rule above holds, which needs RMSE to improve at lead 2, not
only peak capture.

Result (run `b15_late12` vs. `dev`, same tables and seeds; RMSE new - current with
95% day-bootstrap interval):

| Lead | RMSE current -> new | Interval | Smoke-day RMSE | Peak ratio | USG CSI |
|---|---|---|---|---|---|
| 0 | 4.362 -> 4.543 | (-0.02, +0.41) | 6.33 -> 6.59 | 0.91 -> 0.91 | 0.665 -> 0.665 |
| 1 | 7.776 -> 8.053 | (-0.03, +0.61) | 11.04 -> 11.40 | 0.76 -> 0.76 | 0.515 -> 0.496 |
| 2 | 9.721 -> 9.952 | (+0.00, +0.62) | 13.83 -> 14.17 | 0.55 -> 0.61 | 0.435 -> 0.405 |
| 3 | 11.584 -> 11.884 | (-0.17, +1.02) | 16.71 -> 17.18 | 0.29 -> 0.36 | 0.273 -> 0.271 |

Peak capture rose at days 2-3 as expected, but RMSE got worse at every lead (lead 2
with its interval entirely above 0) and warnings got slightly worse. Leads 0-1 also
moved although their weight did not change, because all leads share one network.
90% coverage stayed 0.89-0.91. The hidden-monitor and inner-fold runs were stopped
once the primary test failed. The `--smoke-weight-late` option is not merged.
ACCEPTANCE: FAIL b15_late12: lead 2 RMSE worse with the interval above 0; no lead better.

B-15 stays open. Remaining options: 2020 as extra training data (needs the 2020
download, no HRRR smoke that year), or new inputs for days 2-3 (HRRR runs to 48 h,
but the tables only use leads 0-1).

## 2026-11-23 B-16: fire growth input

Background: the 2026-11-02 ablation (3 seeds) showed that dropping the fire inputs
made RMSE worse at every lead (4.45 / 7.85 / 9.71 / 11.33 with fires vs.
4.64 / 8.19 / 9.85 / 11.52 without), so the "drop fire inputs to simplify" option
is not taken.

### Try 1: FRP from the previous day (`build-table --fire-growth`)

Hypothesis: the existing fire inputs only say how much fire there was in the 24 h
before issue. Smoke arriving at days 1-3 depends on whether nearby fires are
growing or dying down. Adding the FRP within
250 km from 24-48 h before issue (`frp_prev24_250`, same HMS VIIRS/MODIS points and
availability rule as the existing `frp_*` inputs; missing when that day's fire file
is absent) lets the model see growth. Expected: lower RMSE at leads 1-2 on smoke
days, little change on clean days. Tables `train_b16`, `calibrate_b16` (and the inner
fold `train_y2021_b16`, `calibrate_y2022_b16`) are the provided tables plus this one
column; the run tag is `b16_growth`.

Result, dev (run `b16_growth` vs. `dev`, same rows and seeds; tables identical except
the new column, checked column by column):

| Lead | RMSE current -> new | Interval | Smoke-day RMSE | USG CSI |
|---|---|---|---|---|
| 0 | 4.362 -> 4.440 | (-0.02, +0.20) | 6.33 -> 6.44 | 0.665 -> 0.667 |
| 1 | 7.776 -> 7.978 | (-0.07, +0.49) | 11.04 -> 11.32 | 0.515 -> 0.517 |
| 2 | 9.721 -> 9.714 | (-0.12, +0.13) | 13.83 -> 13.82 | 0.435 -> 0.438 |
| 3 | 11.584 -> 11.482 | (-0.60, +0.41) | 16.71 -> 16.57 | 0.273 -> 0.296 |

Inner fold (train 2021, score 2022; `inner_b16_growth` vs. `inner_base`):

| Lead | RMSE current -> new | Interval |
|---|---|---|
| 0 | 4.040 -> 4.317 | (+0.01, +0.56) |
| 1 | 6.463 -> 6.578 | (-0.01, +0.26) |
| 2 | 8.034 -> 8.028 | (-0.14, +0.14) |
| 3 | 10.439 -> 10.688 | (+0.10, +0.43) |

No lead improved on dev, and on the inner fold leads 0 and 3 got worse with their
intervals above 0. The day-3 warning gain on dev did not repeat on the inner fold
(0.119 -> 0.115). 90% coverage stayed 0.89-0.91. The `--fire-growth` option is not
merged. Hidden-monitor run not made because the primary test failed.
ACCEPTANCE: FAIL b16_growth, inner_b16_growth: no lead better; inner fold worse at leads 0 and 3.

B-16 stays open. One untested explanation is that a single day-over-day FRP change is too noisy; a
plume-age or transport input (HRRR smoke beyond lead 1, HMS plume history) is the
remaining idea.

### Try 2: the forecast hours that exist for a partly covered day (`build-table --partial-days`)

Hypothesis: the 12z HRRR run ends 48 h after 12z, about 6 hours into local day 2,
and the 12z AQM run ends about 6 hours into day 3. The daily features need at least
12 hours, so those hours are thrown away and day 2 has no HRRR smoke input and day 3
no AQM input. Adding the mean of the hours that do exist (`hrrr_smoke_first_L2`,
`aqm_first_L3`, at least 3 hours, otherwise missing; same runs and availability as the
existing inputs, no new download) gives the model official smoke information for the
overnight start of day 2 and day 3. Expected: lower RMSE at lead 2, maybe lead 3; no
change at leads 0-1. Tags `b16_partial` (dev) and `inner_b16_partial` (2021/2022).

Result, dev (`b16_partial` vs. `dev`) and inner fold (`inner_b16_partial` vs. `inner_base`):

| Lead | Dev RMSE | Dev interval | Inner RMSE | Inner interval |
|---|---|---|---|---|
| 0 | 4.362 -> 4.453 | (+0.01, +0.19) | 4.040 -> 4.063 | (-0.11, +0.13) |
| 1 | 7.776 -> 8.051 | (-0.19, +0.86) | 6.463 -> 6.532 | (-0.12, +0.27) |
| 2 | 9.721 -> 9.630 | (-0.47, +0.21) | 8.034 -> 7.905 | (-0.31, +0.06) |
| 3 | 11.584 -> 11.342 | (-0.50, -0.07) | 10.439 -> 10.476 | (-0.18, +0.31) |

Day 3 improved on dev with the interval below 0, and day 2 moved the right way on
both folds without reaching significance, but day 0 got worse on dev with its
interval above 0, so the rule fails. Leads 0-1 change although their inputs did not,
because all leads share one network. USG CSI rose at leads 2-3 on both folds
(dev 0.435 -> 0.448 and 0.273 -> 0.306; inner 0.230 -> 0.251 and 0.119 -> 0.126).
The `--partial-days` option is not merged.
ACCEPTANCE: FAIL b16_partial, inner_b16_partial: lead 0 worse on dev with the interval above 0; lead 2 not significant.

Possible follow-up (not run): feed the partial-day inputs only to the lead 2-3
outputs, so leads 0-1 cannot drift.

## 2026-11-23 B-15: 2020 as extra training data

Hypothesis: the model has seen two training seasons (2021-22). 2020 was one of the
worst Western smoke seasons on record (the September 2020 fires), so it adds many
heavy-smoke days, which is what the model under-forecasts at days 2-3. HRRR-Smoke
fields are missing or labelled differently in 2020 and AQM was v5 (48 h); the model
already treats missing inputs as missing. Training on 2020-22 (calibration 2023
unchanged) should raise the day 2-3 peak capture and lower smoke-day RMSE. Tags
`b15_2020` (train 2020-22, dev) and `inner_b15_2020` (train 2020-21, score 2022).

Result, dev (`b15_2020` vs. `dev`) and inner fold (`inner_b15_2020` vs. `inner_base`):

| Lead | Dev RMSE | Dev interval | Inner RMSE | Inner interval |
|---|---|---|---|---|
| 0 | 4.362 -> 4.542 | (-0.02, +0.36) | 4.040 -> 4.076 | (-0.11, +0.17) |
| 1 | 7.776 -> 8.068 | (-0.12, +0.83) | 6.463 -> 6.356 | (-0.33, +0.12) |
| 2 | 9.721 -> 9.586 | (-0.47, +0.20) | 8.034 -> 8.185 | (-0.18, +0.49) |
| 3 | 11.584 -> 11.464 | (-0.64, +0.40) | 10.439 -> 10.020 | (-0.91, +0.13) |

No lead changed significantly on either fold, and leads 1 and 2 moved in opposite
directions on the two folds. Day-3 peak capture rose on both (0.29 -> 0.36 and
0.24 -> 0.36) and day-1 USG CSI rose on both (0.515 -> 0.539; 0.388 -> 0.488), but
the rule is decided on RMSE. 90% coverage stayed 0.89-0.91. 2020 is not added to
training. The 2020 caches stay in the development worktree only.
ACCEPTANCE: FAIL b15_2020, inner_b15_2020: no lead better with its interval below 0.

B-15 stays open; every listed option has now been tried once.

## 2026-11-23 Phase 1 product ideas (diagnostics; no model change)

### Blending forecasters (not built)

Question: does a fixed weighted average of SmokeCast with the boosted-tree model,
NOAA's best, persistence and the no-graph model beat SmokeCast alone? Cross-fitted on
the dev predictions: weights fit on alternate pairs of scoring weeks, applied to the
other half, convex weights (nonnegative, sum to 1). Result: worse at every lead
(for example SmokeCast + trees: lead 1 RMSE 7.776 -> 8.547, interval +0.05 to +1.53;
lead 2 9.721 -> 10.840, +0.15 to +1.94). NOAA and persistence got weight near 0; the
trees got about 0.4 in one half and hurt in the other, because the two halves contain
different smoke episodes. Not built.

### Warning probabilities and a sensitivity dial (built as outputs only)

The backtest now saves `smokecast_prob_L<lead>`, P(daily PM2.5 >= 35.5), and writes
`warn_dial.csv`: hit rate and false alarms on the scoring rows for the CSI-best cut-off
and for cut-offs chosen on calibration rows to reach an 80% or 90% hit rate. Dev 2023:
the 80% and 90% settings collapse to cut-offs near 0.01 at leads 1-3 (false-alarm ratio
about 0.98), so a more sensitive dial is not useful beyond day 0; at day 0 the 90%
setting catches 90% of unhealthy site-days with a false-alarm ratio of 0.35 (vs. 78%
and 0.18 at the CSI-best cut-off). The CSI-best rule stays the default.

Reliability on dev 2023 (lead 1): Brier 0.0095 vs. 0.0175 for always predicting the
base rate. Probabilities are too high in the middle: forecasts near 0.39 verified 0.16,
near 0.59 verified 0.39, near 0.81 verified 0.64; near 0.95 verified 0.95. Lead 2 is
similar. Recalibrating them on calibration rows is the next step.

### Low-confidence flag (diagnostic)

Flag = the 10% of site-days with the widest 90% interval (log scale). Dev 2023 lead 1:
mean absolute error 10.6 on flagged rows vs. 1.8 on the rest, 39% of all error on 10%
of rows; lead 2: 13.1 vs. 2.1, 41%. Inner fold 2022: 9.3 vs. 1.8 (36%) and 12.6 vs. 2.4
(37%). Within the same forecast level (quintiles of the point forecast), flagged rows
still have 1.2-5x the error of the rest on both folds, so the flag is not only a proxy
for smoky days. Disagreement between SmokeCast and NOAA's best is a weaker flag (28-29%
of error on dev). The interval-width flag will be used in the product, with its
threshold taken from calibration rows.

### Recalibrated warning probabilities (accepted as an output change)

Isotonic regression from the raw P(PM2.5 >= 35.5) to the event frequency on calibration
rows only (`smokecast_probcal_L<lead>`); point forecasts, intervals and the warning
cut-off are unchanged. Brier score, raw -> recalibrated, with the 95% day-bootstrap
interval of the difference:

| Lead | Dev 2023 | Interval | Inner 2022 | Interval |
|---|---|---|---|---|
| 0 | 0.0053 -> 0.0048 | (-0.0008, -0.0002) | 0.0059 -> 0.0048 | (-0.0014, -0.0007) |
| 1 | 0.0095 -> 0.0081 | (-0.0018, -0.0008) | 0.0091 -> 0.0078 | (-0.0019, -0.0008) |
| 2 | 0.0118 -> 0.0102 | (-0.0027, -0.0004) | 0.0144 -> 0.0105 | (-0.0053, -0.0026) |
| 3 | 0.0153 -> 0.0136 | (-0.0032, -0.0002) | 0.0212 -> 0.0148 | (-0.0090, -0.0041) |

Reliability, lead 1 dev: stated 0.40 verified 0.34, 0.57 verified 0.52, 0.83 verified
0.69 (raw: 0.39/0.16, 0.59/0.39, 0.81/0.64). Better at every lead on both folds. Note:
this rule (Brier interval below 0 at every lead on both folds) was written after the
first dev run, so the result is reported as development evidence; the final test
scores both versions.
PROBABILITY ACCEPTANCE: PASS dev, inner_base (Brier); RMSE unchanged by construction.

### Blending, second look (2026-11-23, after a literature review)

The literature explains the first result: estimated combination weights often lose to
the best single forecaster when the effective sample is small (the "forecast
combination puzzle"; Smith and Wallis 2009, doi:10.1111/j.1468-0084.2008.00541.x;
Claeskens et al. 2016, doi:10.1016/j.ijforecast.2015.12.005). Here the effective sample
is a handful of smoke episodes, and the members share inputs: SmokeCast and the boosted
trees have error correlations of 0.79, 0.90, 0.91 and 0.92 at leads 0-3 (dev 2023).
NOAA's forecasts and persistence are already SmokeCast inputs, which is why they get
weight near 0.

More variants, all cross-fitted or tuned on another season, all compared with
SmokeCast alone on dev 2023 (RMSE change, 95% day-bootstrap interval):

| Variant | Lead 1 | Lead 2 |
|---|---|---|
| Equal weights, SmokeCast + trees | +0.32 (-0.16, +0.82) | +0.39 (-0.27, +0.91) |
| Convex weights in log space | +0.67 (-0.07, +1.44) | +0.63 (-0.14, +1.28) |
| Separate weights on smoke / no-smoke days (with NOAA) | +0.79 (+0.03, +1.59) | +1.29 (+0.14, +2.25) |
| Online exponentially weighted aggregation (Mallet et al. 2009, doi:10.1029/2008JD009978), learning rate chosen on 2022, weights from past errors only | +0.34 (-0.03, +0.83) | +0.97 (+0.04, +1.74) |

None is better at any lead. Blending is closed for this model; the 5-seed ensemble
inside SmokeCast is already an equal-weight combination.

## 2026-11-23 New information: GOES-West satellite smoke haze (AOD)

Hypothesis: every failed attempt so far reused the same information (NOAA forecasts,
monitors, fire detections, HMS plumes). GOES-West measures aerosol optical depth over
the whole West every few minutes, including places with no monitor, so it adds
independent evidence of smoke that is present now and upwind. Inputs: mean and max of
quality-0 AOD within about 10 km of each monitor over the first scan of each hour
14-17 UTC on the issue day (before the 18:30 UTC issue time), plus how many hours had
a clear view (`build-table --goes-aod`; GOES-17 through 2023-01-03, GOES-18 after).
Expected: lower RMSE at leads 0-1 on smoke days and at hidden monitors; possibly lead 2.
Same acceptance rule; tags `goes_aod` (dev) and `inner_goes_aod` (2021/2022).

Not possible: NASA's GEOS-FP forecasts as an independent forecast input. Its public
forecast archive holds only 2026 (checked 2026-11-23), so 2021-2025 cannot be trained
or tested.

Result. Point AOD covered 63% of site-days (clouds, early-morning sun angle; 4 of 459
days had no scans). It tracks smoke: median AOD 0.06 under no HMS smoke, 0.08 light,
0.16 medium, 0.41 heavy; Spearman 0.29 with morning PM2.5 and 0.19 with next-day PM2.5.

| Lead | Dev RMSE | Dev interval | Inner RMSE | Inner interval | Hidden monitors (dev) |
|---|---|---|---|---|---|
| 0 | 4.362 -> 4.278 | (-0.24, +0.04) | 4.040 -> 4.028 | (-0.13, +0.10) | 6.92 -> 6.72 |
| 1 | 7.776 -> 8.021 | (-0.22, +0.81) | 6.463 -> 6.457 | (-0.14, +0.15) | 8.39 -> 8.51 |
| 2 | 9.721 -> 9.994 | (-0.06, +0.61) | 8.034 -> 8.157 | (-0.05, +0.32) | 9.90 -> 10.26 |
| 3 | 11.584 -> 11.401 | (-0.46, +0.10) | 10.439 -> 10.672 | (+0.04, +0.41) | 11.38 -> 11.50 |

Satellite haze helps only the same-day forecast (lead 0, not significant) and does
not help the forecast days, also not at hidden monitors. Lead 3 is worse on the inner
fold with its interval above 0. Not merged; the extraction code is kept on branch
`conrad/goes-aod` for possible same-day use.
ACCEPTANCE: FAIL goes_aod, inner_goes_aod: no lead 1-2 gain; inner lead 3 worse.

### Day-3-only use of the partial-day inputs (closed without a new run)

Using `b16_partial` only for the lead-3 forecast: dev 2023 lead 3 RMSE 11.584 -> 11.342
(interval -0.50 to -0.07), but the inner fold did not repeat it (10.439 -> 10.476,
-0.18 to +0.31). The acceptance rule also needs a lead 1 or lead 2 gain, which a
lead-3-only change cannot give. Closed.

## 2026-11-23 W-13: hour-by-hour accuracy (evaluation, no model change)

Full results in `docs/HOURLY_ACCURACY.md`. The Serein-scaled hourly field beats NOAA's raw
hourly AQM on days 0-2 (2023) and 0-1 (2022), but a flat line at SmokeCast's daily median is
as accurate or better, and neither NOAA's hourly shape nor a learned per-monitor daily rhythm
predicts which hours of a day are worst (within-day correlations 0.04-0.30). The daily-rhythm
idea was tried after seeing the first result and did not help (profile vs. flat within
+/-0.1 µg/m³). Consequence for the product: present the daily level as the tested forecast
and do not give hour-specific advice from the hourly pattern.

## 2026-11-25 B-8: temporary fire monitors (free replacement for PurpleAir)

Why: B-8 asked whether extra sensors help, but PurpleAir history costs money and the
project uses free data only. The USDA Forest Service AirFire archive publishes the
hourly PM2.5 of temporary fire monitors (E-BAMs reported through WRCC and AIRSIS) on a
public S3 bucket with no key. Their IDs (for example `MMCA81013`) are not in the
AirNow hourly files Serein reads, so they are new information, and they are placed
next to active fires, where the peaks are missed (B-15). In the West study area,
June-October, 74 (2021), 51 (2022) and 69 (2023) monitors more than 5 km from any
Serein monitor reported at least 24 hours; 20% of their 2021 hours were 35.5 µg/m³
or higher.

Hypothesis: recent readings of nearby fire monitors lower RMSE at leads 1-2,
mostly on smoke days, and help hidden monitors.

Inputs (`build-table --fire-monitors`, `serein.features.fire_monitors`), fixed before
the first run: monitors within 150 km that reported in the 24 h before the AirNow
cutoff; count, distance to the nearest (300 km if none), inverse-distance means of
their last-6 h and last-24 h means (weights stop growing inside 10 km), their 24 h
maximum, and the 24 h maximum of monitors upwind (within 60 degrees of where the
issue-time HRRR wind comes from). Readings outside 0-1500 µg/m³ are dropped. The
monitors are inputs only: no new targets, scoring stays on the same EPA rows.

Caveat: these are AirFire's quality-controlled yearly files, not the raw real-time
feed, so a real-time forecast could have seen a few readings that were later removed.
Readings are used only up to the AirNow cutoff (newest hour starting 16:00 UTC).

Runs (same code, same day): baselines `b8_base`, `b8_base_holdout`, `inner_b8_base`;
new `b8_tmon`, `b8_tmon_holdout`, `inner_b8_tmon`. Same acceptance rule.

Result. Fire monitors were within 150 km on 37-42% of monitor-days and 38-57% of
smoke-yesterday monitor-days. The rebuilt tables match the old ones in every existing
column; only the six `tmon_` columns differ. The baseline reproduced the job's
2026-11-25 run exactly.

| Lead | Dev RMSE | Dev interval | Inner RMSE | Inner interval | Hidden monitors (dev) |
|---|---|---|---|---|---|
| 0 | 4.362 -> 4.519 | (-0.01, +0.32) | 4.040 -> 4.351 | (+0.01, +0.56) | 6.92 -> 6.69 |
| 1 | 7.776 -> 7.932 | (-0.18, +0.49) | 6.463 -> 6.655 | (-0.02, +0.42) | 8.39 -> 8.37 |
| 2 | 9.721 -> 9.935 | (-0.16, +0.53) | 8.034 -> 7.849 | (-0.43, +0.05) | 9.90 -> 10.03 |
| 3 | 11.584 -> 11.418 | (-0.45, +0.01) | 10.439 -> 10.652 | (+0.08, +0.39) | 11.38 -> 11.54 |

Smoke-day RMSE is worse at leads 0-2 (11.04 -> 11.25 at lead 1), USG CSI drops at
lead 1 (0.535 -> 0.505), coverage stays within 0.89-0.91. The extra readings do not
help the forecast days. The same pattern as GOES haze and the FRP inputs: information
about smoke that is already present is mostly in the EPA monitors and NOAA's runs,
and six more inputs on a third of the rows add noise. Not merged; the loader and the
features are kept on branch `b8-fire-monitors`. Not tried: the monitors as graph
nodes (needs HRRR and AQM extracted at their locations) or as extra training targets.
ACCEPTANCE: FAIL b8_tmon, inner_b8_tmon: no lead 1-2 gain; inner leads 0 and 3 worse.

## 2026-11-25 Ensemble size: 10 seeds instead of 5 (`--seeds 10`)

Hypothesis: the differences between runs in the records above are often 0.2-0.5
µg/m³ at leads 1-3, which is the size of the effects being tested, so part of the
forecast error is the randomness of training. Averaging 10 networks instead of 5
should lower RMSE a little at every lead, most at days 2-3. No input or setting
changes; seeds 0-9 include the current seeds 0-4. Cost: twice the training time
for each model update; the daily forecast stays seconds. Tags `ens10`,
`ens10_holdout`, `inner_ens10` against `b8_base`, `b8_base_holdout`,
`inner_b8_base` (same code, same day). Same acceptance rule.

## 2026-11-25 CAMS: an independent forecast model as input (`build-table --cams`)

Hypothesis: every input so far comes from NOAA's models or from observations, and
the misses are at days 2-3, where HRRR has ended and AQM is the only model. ECMWF's
CAMS global forecast is built separately (its own emissions, satellite fire
assimilation and weather) and runs to 5 days, so it adds independent information
exactly there. Expected: lower RMSE at leads 2-3 and possibly 1, mostly on smoke days.

Inputs, fixed before the first run: the CAMS 00 UTC run of the issue day (ECMWF
guarantees it by 10:00 UTC, 8.5 h before the 18:30 UTC issue time), PM2.5 at the
nearest 0.4 degree cell, 3-hourly steps 0-96 h, local-day mean and max for leads 0-3
(`cams_mean_L*`, `cams_max_L*`; day 3 has 6 of its 8 steps, at least 6 required).

Caveats: CAMS is upgraded every year or so (dates not checked here), so a version
change can sit between the training and scoring seasons; the inner fold is a second
season pair. CAMS files come from the free Copernicus
Atmosphere Data Store account. Tags `cams`, `cams_holdout`, `inner_cams` against the
same-day baselines. Same acceptance rule.

## 2026-11-25 B-8 try 2: fire monitors as input-only graph nodes (`--aux-kinds tmon`)

Hypothesis: as six summary inputs (try 1) the fire monitors added noise, but the
graph can weigh each neighbor by its distance, direction and the wind, which a fixed
summary cannot. As graph nodes they should help where a fire monitor is upwind of an
EPA monitor, at leads 0-2.

Design, fixed before the first run: the 352 AirFire deployments in the study area in
2021-2023 become nodes of kind `tmon` (`serein add-monitor-nodes`). Each EPA monitor
keeps its current 10 EPA neighbors and also receives one-way edges from its 5 nearest
fire monitors within 150 km; fire monitors receive nothing, have no targets and are
never calibrated or scored, so scoring stays on the same EPA rows. Their readings use
the AirNow cutoff; their NOAA inputs (HRRR, AQM) come from the nearest 0.25 degree
grid cell (median 9 km, at most 16 km away), because HRRR and AQM were never
extracted at their sites. On days a monitor is not deployed its node has the NOAA
inputs but no readings. Runs use `--no-gbm` (the trees are not part of the rule). Tags `gn`,
`gn_holdout`, `inner_gn` against the same-day baselines.

Result. 352 extra nodes, 1,671 extra edges (graph 777 nodes, 5,921 edges). With no
extra kinds the changed code reproduces the baseline exactly (`gn_regress`, RMSE equal
to 4 decimals at every lead), and the EPA rows of the new tables equal the old ones.

| Lead | Dev RMSE | Dev interval | Inner RMSE | Inner interval | Hidden monitors (dev) |
|---|---|---|---|---|---|
| 0 | 4.362 -> 4.400 | (-0.04, +0.14) | 4.040 -> 4.193 | (-0.03, +0.30) | 6.92 -> 6.98 |
| 1 | 7.776 -> 7.828 | (-0.08, +0.20) | 6.463 -> 6.500 | (-0.04, +0.10) | 8.39 -> 8.50 |
| 2 | 9.721 -> 9.778 | (-0.20, +0.37) | 8.034 -> 8.127 | (-0.01, +0.18) | 9.90 -> 10.14 |
| 3 | 11.584 -> 11.537 | (-0.31, +0.16) | 10.439 -> 10.690 | (+0.15, +0.35) | 11.38 -> 11.34 |

USG CSI rises slightly at leads 2-3 (0.435 -> 0.449, 0.287 -> 0.311) and coverage is
unchanged, but RMSE does not improve anywhere and the inner fold is worse at lead 3.
Both ways of using the fire monitors (summary inputs and graph nodes) fail, so B-8 is
answered for the free sensors available: extra temporary monitors do not improve this
model. Code kept on branch `gn-fire-monitors`, not merged.
ACCEPTANCE: FAIL gn, inner_gn: no lead better; inner lead 3 worse.
