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
year for the West, this is a test of spatial transfer, not of time. It uses the
West-calibrated conformal offsets and warning cut-offs unchanged, so its interval
coverage may be off; that is expected and will be reported as it comes out.

**AQM version.** NOAA's AQM changed from v6 to v7 on 2024-05-14 (`src/serein/data/aqm.py`).
Training (2021-22) saw AQMv5 and v6 and calibration (2023) saw v6, but every test day
(June-October 2024 and 2025) uses AQMv7, a version the model never trained on. We
report the test results for 2024 and 2025 separately as a secondary split, so a shift
caused by the new AQM version, or by one unusual season, is visible.

**Test-season file check (2026-11-23, file names only, no file opened).** Every issue
day of June-October 2024 and 2025 (153 per season) has a file in each of
`raw/airnow/hourly`, `raw/airnow/reportingarea`, `raw/hms`, `raw/hms_fire`,
`interim/west_us/aqm_bc` and `interim/west_us/hrrr`: 0 missing days. A file being
present does not prove every hour inside it is present; missing hours are handled by
the 18-hour completeness rule in section 4. There are no November files, so the last
issue days of October lose the leads that fall in November, exactly as in 2023.

## 3. What a forecast may know ("no peeking")

Issue time **18:30 UTC** daily (11:30 am PDT). Allowed inputs, enforced in
`serein/data/availability.py` and tested in `tests/test_data_parsing.py`:

- EPA hourly PM2.5 for hours starting ≤ 16:00 UTC that day;
- HRRR 12z run of the issue day (posted ≈ 13:55 UTC);
- AQM 12z run of the issue day (posted ≈ 18:03 UTC on AWS);
- HMS smoke polygons of the previous day;
- FIRMS detections in the 24 h before issue time.

Posting times were measured from AWS S3 `LastModified` stamps on 2026-11-01.
Limitation: those stamps were read in 2026, so for 2024-25 files they may show a
later re-upload, not the original posting time. The input that matters most is the
AQM 12z run, which lands about 27 minutes before the 18:30 UTC issue time.
Pre-registered sensitivity: if AQM had been late, the forecast would have had HRRR,
sensors and persistence only. We report that case with the existing no-AQM ablation
(`--drop aqm_`, dev error +7-14%) next to the main result.

## 4. Target

Local-standard-time calendar-day mean PM2.5 (µg/m³) at each EPA monitor, with at
least 18 valid hours (EPA completeness rule). Lead L = days after the issue day
(L = 0 is "today", the rest of the day).

## 5. Competitors (all scored on identical rows)

| Name | What |
|---|---|
| `persistence` | yesterday's observed daily mean |
| `persistence_morning` | mean of the 6 observed hours ending at the issue-time cutoff (hours starting 11-16 UTC), carried forward; L0-L1 only (added 2026-11-23, before the freeze) |
| `climatology` | site's median over training seasons |
| `hrrr_smoke` | HRRR-Smoke near-surface smoke + the site's clean-day background (L0-L1) |
| `aqm_bc` | NOAA AQM bias-corrected PM2.5 (L0-L2) |
| `noaa_best` | AQM-bc → HRRR+bg → persistence, whichever exists |
| `gbm` | gradient boosting on the same inputs + neighbor averages (no learned graph) |
| `smokecast_nograph` | our network with message passing turned off (ablation) |
| **EPA forecast** | official reporting-area AQI forecast (category scores only) |

Note on EPA: their forecasts are issued late morning-afternoon local time, i.e.
*after* our 18:30 UTC issue time. This favors EPA.

Why `noaa_best` is the primary competitor: it is not a NOAA product but our
availability chain, the best official number that exists at issue time for each
row and lead. To show we are not only beating a chain of our own design, the final
report also gives `aqm_bc` and `hrrr_smoke` alone on the rows where each exists,
with the row count for every competitor at every lead.

Why `persistence_morning`: Berlinghieri et al. (BAMS 2026) found that morning
AirNow persistence matched or beat operational models for day-level decisions.
Yesterday's mean is a weaker naive forecast for "the rest of today", so this
stronger one is added for L0 and L1 before the freeze. Adding it after would not be
allowed.

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

5. Lead 3 has no official NOAA competitor, so it is outside the primary criterion.
   We report it against persistence and climatology as a secondary result.
6. Day-level Diebold-Mariano test of squared errors, SmokeCast vs. each baseline,
   per lead, two-sided, Bartlett calendar-day covariances with the default bandwidth
   q = max(lead - 1, 0), Holm correction across the report
   (`python -m serein.eval.comparison`, formulas in `docs/FORECAST_COMPARISON.md`).
   It is reported next to the bootstrap interval, never in place of it.

We report every metric for every lead, including ones where we lose. If the
primary criterion is not met, that is the headline result and the Brief will say so.

### The final evaluation, exactly (each command runs once, after the freeze)

1. `uv run serein backtest --final` (main result, all monitors).
2. `uv run serein backtest --final --tag final_holdout --holdout-sites 0.2 --no-gbm`
   (hidden-monitor result; the hidden 20% is fixed by seed 1234, chosen in advance).
3. `uv run serein transfer --run west_us_final` (Northeast June 2023, out of region).
4. Then, reading only those saved outputs: figures, impact, the comparison report
   with the Diebold-Mariano test (metric 6), the 2024 vs. 2025 split (section 2) and
   the no-AQM sensitivity (section 3).

That is the whole final evaluation. Steps 1-3 are three runs, written down now, not
three tries at the same question.

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
test result; rerun 2026-11-23 on current code, see the change log): RMSE
4.4 / 7.8 / 9.7 / 11.6 µg/m³ at leads 0-3 vs. best NOAA 10.1 / 11.0 / 12.3 / 15.5;
at monitors hidden from the model (leave-sites-out, now also hidden from early
stopping and calibration): 6.9 / 8.4 / 9.9 / 11.4 vs. NOAA 10.5 / 11.1 / 11.9 / 14.1.
Morning persistence at lead 0: 7.4 (better than NOAA's 10.1, worse than SmokeCast).
USG warnings vs. EPA's official forecast (reporting areas): hit rate 72% vs. 46% at
day 1 and 62% vs. 37% at day 2.
See `outputs/backtest/west_us_dev/report.md`.

Caveat for the write-up: these settings were picked by looking at dev-week
scores, so dev numbers are slightly optimistic. The test seasons are the honest
number. Interval coverage and the warning hit rate on dev weeks are partly
in-sample: the same odd weeks set the conformal offsets and the warning cut-offs.
The 2024-25 test is the only fully out-of-sample estimate of either.

## 7. Allowed after freezing

- Bug fixes that don't change model choices, with a note here explaining them.
- Running the test once. If a bug is found *after* the final run, we fix it,
  re-run, and report **both** results.
- Archiving: right after the final run, the SHA-256 of the test feature table, the
  model export (`smokecast.pt`) and `predictions.parquet` go into the change-log row
  for that run, and the files are kept unchanged, so anyone can reproduce the
  reported numbers from the same inputs.

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
| 2026-11-04 | Input validation and observation features (no settings changed; rows added 2026-11-23 for review item 1) | Commits f9d83ac to 9a39ab0 and the PurpleAir/grid validation series: rolling sensor features are averaged per hour after the availability cutoff (several readings inside one hour no longer count extra), timestamps are normalized to UTC, duplicate or non-finite observations and targets are rejected instead of used, and forecast grids or cached indices that do not match are refused. Scored numbers can move slightly because of the hourly averaging; the 2026-11-23 dev rerun (below) is on code that includes all of it |
| 2026-11-04 | PR #2 (htvarkali): full-ensemble export, shared calibration, missing-HMS handling, EPA areas by state (no settings changed) | The saved inference model held only the first seed although evaluation used 5; now every member is exported and maps, transfer and live use the same quantile average and calibration as the backtest (6b7800f). Forecast quantiles are kept nonnegative and ordered by one shared function; a missing HMS map is "unknown", never "no smoke"; EPA reporting areas are matched by name and state. Graph/no-graph comparisons use equal seed counts |
| 2026-11-06 | Evaluation tools added, scoring unchanged | Paired comparison with day-bootstrap and Diebold-Mariano tests (c93f8aa, now metric 6), Brier and reliability reports, interval and episode diagnostics, development split audits. These read saved predictions; they do not change the primary metric or any model choice |
| 2026-11-07 | Transfer scoring fix and optional context (Kwilier, PRs #3, #6, #9) | Transfer test AQI categories now use the breakpoints in force on each historical day (e3f1e91); this changes how the Northeast check is scored, not the model. Ozone and heat context goes to family plans only and is not a SmokeCast input |
| 2026-11-07 | Fire history features (b947bbe) | Added with availability and coverage checks as an option for experiments; not part of the frozen settings in 6b |
| 2026-11-08 | Live and spatial development evaluation merged (c73c9c0, bd19765, 74972ac) | Adds `serein live` and the kilometer-grid development evaluation; the backtest scoring is unchanged. A failing optional context cache no longer drops the smoke forecast |
| 2026-11-18 | Live forecast bounds fix (e08486c, htvarkali) | Live forecasts now calibrate their intervals with the same shared function as the backtest (`calibrate_quantiles`), and a forecast counts as on time only if it was made after the issue time and within 6 h of it (section 7b). Backtest scoring is unchanged; research scripts now stop on the first failure |
| 2026-11-19 | Hidden monitors are also left out of early stopping, interval calibration and warning tuning (no settings changed) | Leave-sites-out removed hidden monitors' targets from training only, so their readings still chose the stopping epoch and tuned the 90% intervals and warning cut-offs. This answers item 10 of the 2026-11-08 pre-freeze review. The hidden-monitor dev numbers above (7.0 / 8.5 / 10.1 / 11.3) came from the old code and need a rerun |
| 2026-11-22 | Live forecast pinned to its own trained run, `west_us_live_v1`, from the 2026-11-23 forecast (no settings changed) | `serein live` used `west_us_dev`, which every development rerun overwrites, so a rerun would have replaced the live model without notice; that run was also a legacy single-member export. `scripts/run_live.sh` now passes `--run "${SEREIN_LIVE_RUN:-west_us_dev}"`. `west_us_live_v1` was trained on code 565bbba with rebuilt train and calibrate tables (dev mode, test seasons untouched): 5 members, seeds 0-4, model fingerprint `66c772b333a9...`. Dev numbers: RMSE 4.4 / 7.8 / 9.7 / 11.4; 90% coverage 0.89-0.91. Forecasts through 2026-11-22 came from `west_us_dev`; as section 7b says, the live scoreboard is split at 2026-11-23 and both parts are reported. The points registry kept its monitors and gained a state column taken from 2021-2023 AirNow metadata only |
| 2026-11-23 | D-4 preparation from the 2026-11-08 review (no model settings changed) | Change-log rows for Nov 4-18 (item 1); in-sample caveat (2); the exact final commands (3); Diebold-Mariano test written in as metric 6 (4); posting-time limitation and no-AQM sensitivity (5); why `noaa_best` and per-product rows (6); `persistence_morning` competitor for L0-L1, code in `src/serein/models/baselines.py` (7); AQM v7 covers the whole test period, results split 2024 vs. 2025 (8); lead 3 framing (9); test-season files counted by name, 0 missing days (11); what "we lose" looks like (12); Northeast uses West calibration (13); archive hashes (14). Dev and hidden-monitor backtests rerun on code 7334216 with the rebuilt 2026-11-22 tables (figures, map and ablations not rerun): RMSE 4.4 / 7.8 / 9.7 / 11.6; hidden monitors 6.9 / 8.4 / 9.9 / 11.4 (the rerun the 2026-11-19 row asked for); 90% coverage 0.89-0.91. Test seasons still untouched |
