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
