# Offline PurpleAir quality control

Task A-12 adds a screening stage for downloaded histories. It makes **no network
requests** and does not spend PurpleAir points. Adding accepted sensors to the
forecast graph and measuring their benefit is still task B-8.

## Run it

```bash
uv run serein purpleair qc history.parquet \
  --sensors-file data/raw/purpleair/sensors.parquet \
  --output outputs/purpleair/qc_audit.parquet \
  --clean-output outputs/purpleair/accepted.parquet
```

Inputs and outputs may be `.csv` or `.parquet`. `--output` is required and keeps
all original rows with audit columns. `--clean-output` is optional and writes
only accepted rows as `time_utc`, `sensor_index`, `pm25` (corrected µg/m³).
The command prints counts per rule as JSON. Counts overlap when a row fails
multiple rules. Neither output may overwrite an input or the other output.

## Input schema

The history uses the existing PurpleAir downloader's fields:

| Field | Meaning |
|---|---|
| `sensor_index` | Positive integer PurpleAir sensor identifier |
| `time_utc` | Timestamp; offset-aware values are converted to UTC, naive values are interpreted as UTC |
| `time_stamp` | Epoch seconds; used only if `time_utc` is absent |
| `pm2.5_cf_1_a`, `pm2.5_cf_1_b` | Both raw CF=1 channel measurements, µg/m³ |
| `humidity` | Relative humidity, 0–100 percent |
| `lat`, `lon` | Sensor location; `latitude`, `longitude` are accepted aliases |
| `location_type` | PurpleAir metadata: 0 outdoor, 1 indoor; `outdoor`/`indoor` strings are also accepted |
| `indoor` | Alternative location indicator: boolean or `true`/`false`, `yes`/`no`, `1`/`0` strings |

The optional sensor metadata file is keyed by unique `sensor_index` and may fill
missing coordinates and location indicators. History values take precedence.
Conflicting indoor/location indicators are rejected. Indoor readings are excluded;
missing channel, location, coordinate or humidity information is **flagged**, not
assumed valid. Do not fabricate outdoor status for an unverified sensor.

## Rules and audit fields

- `qc_invalid_sensor`, `qc_invalid_time`: unparseable or missing identifiers/times.
- `qc_duplicate`: every duplicate sensor/timestamp pair, after UTC normalization.
- `qc_indoor`, `qc_unknown_location`: indoor, unknown or conflicting placement.
- `qc_invalid_channels`: nonfinite or negative channels, or an unrepresentable
  mean/correction. `qc_ab_disagreement`: finite channels failing both the absolute
  and relative agreement tests. Defaults use the existing client's 5 µg/m³ **or**
  70% agreement rule.
- `qc_invalid_humidity`: missing/nonfinite humidity or values outside 0–100%.
- `qc_missing_coordinates`: missing/nonfinite/out-of-range latitude or longitude.
- `qc_stuck`: both channels stay within 0.01 µg/m³ of a run's first reading for
  at least 24 consecutive hourly readings. A gap or invalid reading breaks the
  run. Only the observation completing the required run, and subsequent flat
  observations, are flagged; preceding observations are not retroactively removed.
- `qc_neighbor_outlier`: when at least three other otherwise eligible sensors are within
  25 km in the same UTC hour, compare with their median corrected PM. A reading
  is flagged only when its difference exceeds **both** 30 µg/m³ and twice that
  median (with a 1 µg/m³ floor). Each peer contributes one average per hour,
  independent of how many readings it has. Only peers at or before the target
  timestamp are used. Broad regional smoke increases are not, by themselves,
  disagreement with nearby sensors.

`qc_keep` is true only when no rejection flag is set. `qc_flags` lists rejection
reasons separated by semicolons. `qc_neighbor_evaluated` separately reports whether
there were enough peers: **false means unassessed, not a passed neighbor test**.
A row can pass the other checks while lacking enough peers. All original columns,
row order and index are preserved by the Python API; extra normalized timestamp,
raw channel-mean and audit fields are appended. `pm25` is populated only for
accepted rows; rejected rows retain their raw measurements but get no corrected PM.

Use `uv run serein purpleair qc --help` for threshold flags. `--average` specifies
the expected sampling interval in minutes; the stuck run's required sample count
is adjusted to that interval. A run always requires at least two samples.

## Scientific limits

The A/B function and EPA correction reuse the existing implementation in
`src/serein/data/purpleair.py`. The coefficients were checked on 2026-11-27
([correction check](PURPLEAIR_CORRECTION_CHECK.md)): they match EPA's, but the sources
apply them to the cf_atm channels, not cf_1, which needs a decision before A-14. These new stuck and neighbor thresholds are
**configurable engineering heuristics**, not experimentally validated fault labels.
A genuine localized plume can disagree with nearby sensors; inspect the audit
rather than claiming every rejected reading is wrong. Sparse areas may have no
neighbor assessment. A flat real background can be flagged as stuck.

For historical forecasting, apply the project's availability cutoff **before**
running QC, and use metadata known at that time. Timestamp-causal measurement
checks do not prove that historical API records or current placement metadata
were available when a forecast was issued. No new forecast-accuracy result is
claimed by implementing this stage.

## Python API

```python
from serein.data.purpleair_qc import QCConfig, quality_control, accepted_history, summarize_qc

audit = quality_control(history, sensors=metadata, config=QCConfig())
clean = accepted_history(audit)
counts = summarize_qc(audit)
```

`quality_control` preserves inputs. It rejects duplicate column names and previous
QC output columns rather than silently overwriting them. The earlier
`purpleair.clean_history` helper remains available for compatibility; the CLI
above is the complete A-12 audit path.

Before future B-8 integration, canonicalize sensor identifiers and prefix them
with `PA` in the combined points registry so they cannot collide with EPA IDs.
