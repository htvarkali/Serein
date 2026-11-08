# Backtest protocol (pre-registration)

> **Status: DRAFT. Freeze before Dec 7, 2026 (TODO D-4).** Freezing = the commit that
> changes this line to "FROZEN" and is pushed *before* anyone runs
> `serein backtest --final`. The commit hash and time are our timestamp.

Why this matters: if we tune the model while peeking at the test seasons, our
"beats NOAA" result would be fake. Judges and scientists trust a result more
when the rules were written down *before* the answer was known.

## 1. Question

Does SmokeCast forecast the daily-average PM2.5 at EPA monitors 0-3 days ahead
more accurately than (a) NOAA's operational forecasts and (b) EPA's official AQI
forecasts, on wildfire-season days it never trained on?

## 2. Data split (by whole season; never by random rows)

| Split | Seasons (Jun-Oct) | Used for |
|---|---|---|
| Train | 2021, 2022 | fitting model weights |
| Calibrate | 2023 | even ISO weeks: early stopping; odd weeks: conformal calibration |
| **Test** | **2024, 2025** | **scored once, at the end** |

Region: `configs/west_us.yaml` (CA, OR, WA, NV, ID, west AZ).
Splitting by season matters: neighboring days are nearly identical, so a random
row split would leak tomorrow into training.

Out-of-region check (secondary): June 2023 Canadian-smoke episode in the
Northeast US with the West-trained model (TODO D-6). Since 2023 is a calibration
year for the West, this is a test of spatial transfer, not of time.

## 3. What a forecast may know ("no peeking")

Issue time **18:30 UTC** daily (11:30 am PDT). Allowed inputs, enforced in
`serein/data/availability.py` and tested in `tests/test_data_parsing.py`:

- EPA hourly PM2.5 for hours starting ≤ 16:00 UTC that day;
- HRRR 12z run of the issue day (posted ≈ 13:55 UTC);
- AQM 12z run of the issue day (posted ≈ 18:03 UTC on AWS);
- HMS smoke polygons of the previous day;
- FIRMS detections in the 24 h before issue time.

Posting times were measured from AWS S3 `LastModified` stamps on 2026-11-01.

## 4. Target

Local-standard-time calendar-day mean PM2.5 (µg/m³) at each EPA monitor, with at
least 18 valid hours (EPA completeness rule). Lead L = days after the issue day
(L = 0 is "today", the rest of the day).

## 5. Competitors (all scored on identical rows)

| Name | What |
|---|---|
| `persistence` | yesterday's observed daily mean |
| `climatology` | site's median over training seasons |
| `hrrr_smoke` | HRRR-Smoke near-surface smoke + the site's clean-day background (L0-L1) |
| `aqm_bc` | NOAA AQM bias-corrected PM2.5 (L0-L2) |
| `noaa_best` | AQM-bc → HRRR+bg → persistence, whichever exists |
| `gbm` | gradient boosting on the same inputs + neighbor averages (no learned graph) |
| `smokecast_nograph` | our network with message passing turned off (ablation) |
| **EPA forecast** | official reporting-area AQI forecast (category scores only) |

Note on EPA: their forecasts are issued late morning-afternoon local time, i.e.
*after* our 18:30 UTC issue time. This favors EPA.

## 6. Metrics (decided now)

**Primary:** RMSE of daily PM2.5 vs. `noaa_best`, per lead, all site-days, with
95% confidence intervals from a day-block bootstrap (1000 resamples of whole
days). Success = the CI of RMSE(SmokeCast) − RMSE(noaa_best) is entirely below 0
for leads 1 and 2.

**Secondary:**
0. RMSE at monitors hidden from the model entirely (20% of sites, fixed seed 1234;
   `--holdout-sites 0.2`): the "neighborhood without a sensor" case.
1. RMSE on smoke-affected days (HMS plume over the site the day before).
2. USG+ (≥ 35.5 µg/m³) warnings: POD, FAR, CSI.
3. AQI category accuracy vs. the EPA forecast, per reporting area.
4. 90% interval coverage (target 0.88-0.92) and CRPS.

We report every metric for every lead, including ones where we lose.

## 6b. Model settings chosen on dev weeks (2026-11-01)

Chosen using ONLY the 2023 calibration season (`scripts/sweep_graph.sh`, logs in
`outputs/logs/sweep_*.log`). Frozen for the final run:

| Setting | Value |
|---|---|
| Hidden size / message-passing layers / heads | 64 / 2 / 4 |
| Dropout / weight decay / learning rate | 0.3 / 1e-3 / 2e-3 (AdamW, cosine) |
| Node masking during training | 15% of sensors per step |
| Ensemble | 5 seeds (0-4), quantiles averaged, then conformal calibration |
| Graph | 10 nearest monitors within 300 km |
| Warning rule | warn if P(≥ 35.5) ≥ cut-off tuned per lead on calibration weeks |
| Smoke-day loss weight | 6× for observed days ≥ 35.5 µg/m³ (B-13: tested 1, 3, 6; 6 captured most of each peak) |
| Base forecast without own sensor | distance-weighted neighbors' readings (used for masked sensors in training, hidden monitors, map grid) |

Dev-mode results with these settings (scored on odd ISO weeks of 2023; NOT the
test result): RMSE 4.5 / 7.9 / 9.7 / 11.4 µg/m³ at leads 0-3 vs. best NOAA
10.1 / 11.0 / 12.3 / 15.5; at monitors hidden from the model (leave-sites-out):
7.0 / 8.5 / 10.1 / 11.3 vs. NOAA 10.5 / 11.1 / 11.9 / 14.1. (Rerun 2026-11-02 with
repeatable training; see the change log.)
See `outputs/backtest/west_us_dev/report.md`.

Caveat for the write-up: these settings were picked by looking at dev-week
scores, so dev numbers are slightly optimistic. The test seasons are the honest
number.

## 7. Allowed after freezing

- Bug fixes that don't change model choices, with a note here explaining them.
- Running the test once. If a bug is found *after* the final run, we fix it,
  re-run, and report **both** results.

## 7b. Live test (prospective; rules written 2026-11-03, before the first live forecast)

The backtest replays the past. The live test forecasts days that have not happened
yet (`serein live`, run daily at 11:45 AM Pacific by `scripts/run_live.sh`).

- **What is scored:** every EPA monitor-day in the West with a forecast, smoke or not,
  against the same local-day mean PM2.5 target as section 4. Same competitors as
  section 5 (`noaa_best`, `aqm_bc`, persistence, EPA's official forecast), same rows.
- **Primary:** RMSE vs. `noaa_best` per lead, with the day-block bootstrap of section 6.
  The main live window is the **June-October 2027 fire season**. November-May is
  reported separately as off-season: the model never trained on winter days.
- **On time only:** a forecast counts only if it was made within 6 h of the 18:30 UTC
  issue time. A missed day stays missed; it is never filled in afterwards.
- **No edits:** a forecast file is never changed after it is written. Each file's
  SHA-256 is appended to `outputs/live/west_us/forecast_hashes.txt` when it is made.
  Committing that list regularly is what makes the dates checkable by anyone.
- **Model changes:** each forecast records which trained model made it. If the model
  is replaced, the scoreboard is split at that date and both parts are reported.

## 8. Change log

| Date | Change | Why |
|---|---|---|
| 2026-11-01 | First draft | |
| 2026-11-01 | Added 6b (settings chosen on dev weeks); leave-sites-out secondary metric | Graph only helped clearly once regularized; benefit is largest where there is no sensor |
| 2026-11-01 | Smoke-day loss weight 6 | Peaks were under-predicted (59% of true value at day 1 → 72%); overall calibration unchanged |
| 2026-11-01 | Neighbor-based base for places without a sensor | Grid/hidden sites fell back to generic clean air on day 3; hidden-monitor day-3 error 12.9 → 11.5 |
| 2026-11-01 | Code-review bug fixes, dev suite rerun (no settings changed) | (1) `hrrr_pm` carried each site's own clean-air history and is now hidden wherever sensor data is hidden (masking, leave-sites-out, no-sensor ablation); (2) co-located monitors no longer get self-edges; (3) EPA comparison now matches reporting areas by name AND state, inside the study region only; (4) `figures.py` crashed before the calibration chart, improvement map and peak report, so those had not been regenerated since an earlier run. New dev numbers: RMSE 4.5 / 7.9 / 9.8 / 11.4; hidden monitors 6.9 / 8.6 / 10.1 / 11.3; day-1 warnings 71% vs. EPA 46%; day-1 peak capture 78%. Test seasons still untouched |
| 2026-11-02 | Repeatable training (deterministic GPU algorithms), faster code, dev suite rerun (no settings changed) | Two runs of the same code gave different results because the graph step sums messages with GPU atomics in a changing order: the day-2 warning rate moved from 70% to 63%. With `torch.use_deterministic_algorithms` the same seed now gives the identical model (test added), so the one-shot final test can be reproduced exactly. The vectorized CQR, GBM features and warning probabilities gave identical numbers to the old loops. New dev numbers: RMSE 4.5 / 7.9 / 9.7 / 11.4; hidden monitors 7.0 / 8.5 / 10.1 / 11.3; day-1 warnings 71% vs. EPA 46% (81 vs. 98 false alarms); day-2 66% vs. 37%; day-1 peak capture 80%. Test seasons still untouched |
| 2026-11-03 | Added 7b (live test rules), before the first live forecast | Daily prospective forecasts start 2026-11-03; scored like the backtest, on-time forecasts only, hashed when made |
