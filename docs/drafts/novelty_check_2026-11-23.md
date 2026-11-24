# Novelty check for Brief Q4 "What is new" (2026-11-23)

A literature and product search for the three claims. Sources marked "opened" were
read; the rest were seen in search results only and need a full read before citing.
Absence of evidence here is not proof that no prior work exists.

## Claim 1: graph network correcting NOAA forecasts, scored against official forecasts

- Huang, J., et al. 2017. Weather and Forecasting. https://doi.org/10.1175/WAF-D-16-0118.1 (opened). NOAA's analog bias correction of NAQFC PM2.5 against AirNow; the authors note it works poorly for wildfire smoke.
- Hamer, Sleeman, Stajner. 2023. arXiv:2303.12963 (opened). Machine-learning correction of NOAA air quality guidance with AirNow monitors (ozone and PM2.5); not a graph network.
- Liao, K., Buch, J., Lamb, K., Gentine, P. 2025. Environmental Data Science 4: e11. https://doi.org/10.1017/eds.2025.4 (opened). Graph network over 112 California monitors, 48 h PM2.5; no NOAA inputs, no hidden-monitor test, no official comparison.
- Dimri et al. 2024. AGATNet, JGR Machine Learning and Computation. https://doi.org/10.1029/2024JH000244 (search only). Graph network correcting CMAQ 72 h PM2.5 over 183 Korean monitors; NAQFC is CMAQ-based, so this is the closest method.
- Dong, Mao, et al. ACS ES&T Air. Machine-learning bias correction of HRRR-Smoke surface PM2.5 in the Alaska wildfire season (search only; the page returned 404). 1D CNN, not a graph.
- Berlinghieri et al. 2026, BAMS (already in the reference list). Evaluates HRRR-Smoke and NAQFC against AirNow; no correction model.

Verdict: the parts exist; the exact combination (graph network, HRRR-Smoke and AQM inputs, U.S. monitors, held-out comparison with EPA's AQI forecast) was not found.

## Claim 2: forecasts where there is no monitor

- Wang et al. 2025. SPIN, arXiv:2511.16013 (opened). Graph network estimating current PM2.5 at 46 unseen monitors in China; not a forecast.
- AirNow Fire and Smoke Map FAQ (opened). Corrected PurpleAir readings fill gaps; current readings only.
- Google Air Quality API (opened). Hourly forecasts to 96 h on a 500 m grid; method not described.

Verdict: grid forecasts are not new. The contribution is a measured accuracy check at hidden monitors for a corrected U.S. smoke forecast.

## Claim 3: per-child sensitivity from a parent check-in

- AirRater (opened, App Store listing). Symptom logging, personal trigger analysis, alerts, child profiles, smoke forecasts; Australia only; no Bayesian model described. Strongest overlap.
- Su, J. G., et al. 2017. Environmental Health Perspectives. https://doi.org/10.1289/EHP266 (opened). Propeller inhaler sensors and air pollution; group-level effects, not per-person.
- EPA Smoke Sense (opened). Taken offline on 2024-12-08.
- JMIR preprint 84513 and kHealth (JMIR Pediatrics 2019) (search only). Personal trigger detection in children.

Verdict: personal trigger apps exist; a partial-pooling per-child estimate that sets the action-plan thresholds was not found published.

## Not verified

AGATNet and Dong full texts and years; the JMIR preprint and kHealth details; whether
Propeller's personalized forecasts still exist; how Google, BreezoMeter, IQAir, Plume
Labs and Ambee build forecasts; whether NOAA runs an operational machine-learning
correction; paywalled and very recent work.
