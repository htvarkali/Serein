# Forecast context for family plans (C-10b)

The family-plan simulation can use NOAA AQM ozone and HRRR temperature forecasts
at its selected location and forecast day. The child and symptom history remain
synthetic. Daily check-ins are separate and accept optional Yes / No / Not sure
pollen answers; today's pollen answer is not assumed to describe a future day.

## Use with an existing development forecast

Use the same study configuration and point registry as the existing map workflow.
The example below assumes the `west_us` registry and `west_us_dev` model artifacts
already exist; it does not download the full training dataset or fit a model.

```bash
uv run serein download context --config configs/west_us.yaml --start 2023-08-18 --end 2023-08-18 --workers 2
uv run serein map --config configs/west_us.yaml --date 2023-08-18 --run west_us_dev
uv run streamlit run app/streamlit_app.py
```

`download context` explicitly fetches hourly ozone and hourly temperature into
separate study-specific caches. It does not replace the PM2.5 or three-hour
weather caches used by SmokeCast. `download all` keeps its existing scope.
Map export reads the available context caches without making additional network
requests. The app reads the exported columns without downloading weather.

In **Family plan (simulation)**, select the forecast day and location. The
**Forecast context** panel shows the ozone and temperature used for that day.
Older forecasts and the bundled sample remain usable: missing context displays
**Not available**. Download failures or incomplete hours do not become clean-air
or cool-day measurements.

## Definitions and coverage

Each location uses its registry's fixed `gmt_offset`, consistent with the project's
local standard-day forecasts. This is a 24-hour standard-time day, including
dates when civil daylight-saving time changes.

| Exported field | Definition |
|---|---|
| `ozone_max8h_ppb` | Maximum of the 17 complete eight-hour means wholly within a local standard day, from AQM bias-corrected hourly ozone in ppb. All 24 distinct hourly values must be finite and nonnegative. This is the defined model-context statistic, not a regulatory ozone AQI calculation. |
| `temperature_max_c` | Maximum of 24 distinct finite hourly HRRR 2 m temperature forecasts, converted from Kelvin to Celsius. It is an hourly-sample maximum used as a proxy for daily maximum temperature. |
| `ozone_hours`, `temperature_hours` | Number of usable hourly values for the local day. An aggregate remains missing unless coverage is complete. |
| `ozone_statistic`, `temperature_statistic` | Explicit aggregation names: `max_8h_within_local_day` and `maximum_hourly_forecast`. |
| `ozone_source`, `temperature_source` | Source descriptions for the cached forecast data. |
| `ozone_cycle_utc`, `temperature_cycle_utc` | UTC initialization time of the source forecast cycle. This is distinct from the forecast's local valid date. |

The standard three-hour HRRR weather samples cannot establish this hourly
maximum. The separate temperature download requests every hour. HRRR's available
horizon is at most 48 hours; later or partially covered local days remain missing.
The current cycle may also lack early hours of the issue day. Values are not
interpolated, extended beyond the available horizon, or borrowed from later cycles.

## Issue-time assumptions and cache identity

Only the configured cycle for the requested issue date is eligible. Eligibility
uses the project's source-posting lag checks. HRRR retains its two-hour lag.
Ozone uses a separate provisional **6.25-hour** lag: a 12 UTC cycle becomes eligible
at 18:15 UTC. This allowance is informed by recent ozone archive listings; it is
an explicit availability assumption, not proof of historical publication times.
An archived file's later re-upload time cannot establish when it first became
available in 2023. See the source-check notes below.

Cache validation checks the requested point registry, coordinates and issue cycle.
Moved points, duplicate timestamps, inconsistent forecast steps, missing source
fields and unrecognized units are not silently treated as valid context. The
cache and exported coverage preserve unavailable data.

## Personal-model boundary

`forecast_context_values` exposes only validated complete-day values to the app.
`forecast_confounders` maps those values to the existing `make_plan` arguments:

- Ozone supplies `ozone_ppb`; unknown ozone uses `None`, omitting that model term.
- Complete hourly maximum temperature supplies the existing `hot_day` feature at
  **32 °C**. Unknown temperature uses the established neutral-zero heat term.

The saved forecast still distinguishes missing values from actual low readings.
Both the smoke forecast and the paired clean-smoke comparison receive the same
ozone and heat context. These inputs do not independently create a smoke warning.
Existing AQI floors, message templates and clinical design thresholds are unchanged.

Context is attached after SmokeCast inference. It does not enter the training
feature table, alter model weights, change the artifact feature count, or revise
historical performance results. C-7/C-8 translation and clinical review remain
separate open tasks. This integration does not establish clinical benefit.

## Source check and validation

On November 7, 2026, the extractors were exercised against the **August 18, 2023,
12 UTC** public forecast cycle at a demonstration point near Sacramento
(38.58, -121.49; standard UTC offset -8). The native
[AQM hourly ozone file](https://noaa-nws-naqfc-pds.s3.amazonaws.com/AQMv6/CS/20230818/12/aqm.t12z.ave_1hr_o3_bc.20230818.227.grib2)
contains `ozcon`, surface `sigma:1`, one-hour average intervals and **ppb** units.
HRRR's [surface inventory](https://noaa-hrrr-bdp-pds.s3.amazonaws.com/hrrr.20230818/conus/hrrr.t12z.wrfsfcf20.grib2.idx)
identifies `TMP:2 m above ground`; its decoded field is `2t`, instantaneous at the
requested forecast hour, in **Kelvin**. The source cycle is checked in each decoded
message. The test downloaded 72 hourly ozone means and 49 temperature samples
(forecast hours 0–48).

The generated local audit is `outputs/context-verification/20230818.json`. These
results are from the new extractors and cache aggregation, rather than manually
entered context:

| Local valid day | Ozone hours | Ozone max 8-hour mean (ppb) | Temperature hours | Maximum hourly temperature (°C) |
|---|---:|---:|---:|---:|
| 2023-08-18 | 20 | Unavailable | 20 | Unavailable |
| 2023-08-19 | 24 | 52.19 | 24 | 34.59 |
| 2023-08-20 | 24 | 52.03 | 5 | Unavailable |
| 2023-08-21 | 4 | Unavailable | 0 | Unavailable |

The August 19 adapter supplies `ozone_ppb ≈ 52.19` and `hot_day = 1`. Incomplete
days preserve missing values. This is a source-parsing, unit-conversion and
aggregation check; it does not measure forecast accuracy or clinical benefit.
No reserved-season scoring or model fitting was performed for this check.

For the provisional ozone schedule allowance, official archive listings showed
the November 5 and 6, 2026 12 UTC ozone files posted at 18:06:20 and 18:05:49 UTC.
The 18:15 eligibility threshold adds an allowance to those observations. The
2023 file's later archive re-upload timestamp is not used to claim its original
publication time. Future operational use should verify ongoing source latency.

Synthetic regression tests cover exact local-day windows, missing and duplicate
hours, invalid units and values, source field/initialization mismatches, moved
locations, source horizons, issue-time cutoffs, export alignment, legacy forecasts,
the Streamlit day selector, and the paired clean-smoke context. The new context
download command exits with failure when a source cycle is missing or fails to
decode; existing download commands retain their behavior.
