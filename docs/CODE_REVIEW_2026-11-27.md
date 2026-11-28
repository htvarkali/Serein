# Code review before the protocol freeze, 2026-11-27

A read of the code that every headline number depends on, done before the protocol is
frozen (D-4, Dec 17). Nothing in `src/` was changed by this review. Findings that would
change model inputs or scores are written up here for the team to decide, because the
protocol says such changes go through its change log.

Main at `7e7193a`. Checks run: the full test suite (3,257 passed, 7 skipped: one needs a
GPU, six are Windows-only), `ruff check .` (clean), and a stricter one-off ruff pass
(`--select B,F,PLE,PLW,...`) that found only style patterns, none of them bugs.

## Read and found sound

| Area | File | What was checked |
|---|---|---|
| Scores | `eval/metrics.py` | RMSE, MAE, bias, warning hits, misses and false alarms, CSI, CRPS from quantiles, interval coverage, day-block bootstrap (resamples whole days, as the protocol says) |
| AQI | `aqi.py` | Both EPA scales, switch on 2024-05-06, truncation to 0.1 µg/m³, NaN handling. NumPy rounds an AQI of exactly x.5 to the even number, but no category edge falls on a .5, so categories are unaffected |
| Comparison with EPA | `eval/backtest.py` `compare_with_epa`, `data/airnow.py` | Areas matched on name and state; EPA's observed area AQI as truth; the forecast in force on each day; the AQI scale of the day; documented that EPA's later issue time favors EPA |
| Truth values | `features/daily.py` | Local standard-time days, at least 18 of 24 hours, each hour counted once |
| Baselines | `models/baselines.py` | Each baseline uses only what existed at issue time; climatology from training seasons |
| Final-test lock | `eval/backtest.py` `run_backtest` | 2024-25 loads only with `--final`; refuses a second run without `--force`; refuses uncommitted code; writes a lock file |
| Ranges | `models/conformal.py` | Conformalized quantile regression with a finite-sample rank, grouped by predicted level, pooled fallback for small groups, order and zero floor kept |
| Safety floor | `personal/action_plan.py`, `messages/en.yaml` | "Unhealthy for Sensitive Groups" or worse is at least YELLOW, "Very Unhealthy" or worse is RED; personal risk can only raise the zone. YELLOW's actions (indoor activity instead of hard outdoor activity) fit EPA's advice for sensitive groups at "Unhealthy". Tested in `tests/test_personal.py` |
| Live scoring | `live.py` `score`, `model_parts` | Only complete days are scored (14-hour margin), late forecasts excluded, scoreboard split when the model changes |
| Units | `data/aqm.py` | Ozone converted from the GRIB unit label, not from magnitude |

## Needs a team decision before the freeze

### 1. Fire detections: what the backtest sees vs. what a live forecast sees (medium)

`features/table.py` uses NASA FIRMS if a FIRMS cache exists, otherwise NOAA HMS fire
points (`hms.load_fires`), keeping VIIRS and MODIS detections. `firms.fire_features`
then counts every detection in the 24 hours up to the issue time itself
(`time_utc <= issue_time`), and `Availability.firms_window` has no posting delay.

- In the backtest, HMS points come from the archived daily file for the issue day,
  which is the finished, analyst-checked file.
- In a live run, `live.fetch_inputs` downloads that day's file at about 18:30 UTC, when
  it holds only the detections posted so far.

So the backtest can use detections from the last hours before 18:30 UTC, and analyst
removals of false detections, that a live forecast would not have had. Protocol
section 3 also says "FIRMS detections in the 24 h before issue time", while the default
path is HMS.

How much it matters: removing all fire inputs changed RMSE by 1-4% (`docs/METHODS.md`
ablation), so this cannot move the headline numbers by more than that, and probably far
less. It is still a "no peeking" question a reviewer could ask.

Options, cheapest first:

1. **Say it in the protocol** (section 3): the default fire source is HMS fire points
   from the archived daily file, with no posting delay modeled, and the fire ablation is
   the upper bound on its effect.
2. **Add a posting delay** for fire detections, for example only detections at least
   3 hours before issue time. This changes model inputs, so it needs a rebuilt table and
   a dev rerun under the acceptance rule, before the freeze.
3. **Use yesterday's HMS fire file only**, like the smoke polygons (`hms_lag_days: 1`).
   Same cost as option 2.

### 2. HRRR smoke units are decided by magnitude (low)

`hrrr.smoke_to_ugm3` multiplies by 1e9 when the whole CONUS field's maximum is below 1,
because NOAA's label changed from µg/m³ to kg/m³ on 2021-12-21. A field truly in µg/m³
with every value below 1 would be inflated a billion times. That needs a smoke-free
CONUS, which is unlikely, and the caches are already built. A one-off check on the
machine with the data settles it:

```python
# uv run python, with SEREIN_DATA set as for the backtest
import pandas as pd
from serein.config import interim_dir
big = []
for p in sorted(interim_dir("west_us/hrrr").glob("*.parquet")):
    df = pd.read_parquet(p, columns=["var", "value"])
    if df.loc[df["var"] == "smoke", "value"].max() > 1e5:
        big.append(p.name)
print(len(big), big[:5])   # expect 0
```

For future extractions, deciding from the GRIB unit label (as `aqm.ozone_to_ppb` does),
with the magnitude rule as a cross-check, would remove the risk.

### 3. Development coverage is slightly optimistic (note only)

In dev mode, the even weeks of 2023 are used both for early stopping and for calibrating
the 90% ranges (`run_backtest`: `conf = val`). The 89-91% development coverage is
therefore measured on ranges calibrated on data that also chose the stopping point. The
final run keeps them apart (even weeks stop, odd weeks calibrate, 2024-25 scores), so
this affects only how the development coverage is described.

### 4. PurpleAir correction channel

Already written up in [PURPLEAIR_CORRECTION_CHECK.md](PURPLEAIR_CORRECTION_CHECK.md):
EPA's smoke correction is for the cf_atm channels; the code feeds it cf_1. No current
result uses PurpleAir.

## Not reviewed line by line

The evaluation diagnostics (`eval/spatial*.py`, `episodes.py`, `discrimination.py`,
`map_support.py`, `split_*`, plotting) and the model and training code (`models/gnn.py`,
`models/train.py`, `models/infer.py`) were covered only by the test suite and the lint
passes. A deeper check of the model code would mean rerunning experiments on the
machine with the 150 GB of data.
