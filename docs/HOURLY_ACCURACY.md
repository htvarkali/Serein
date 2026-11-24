# Hour-by-hour accuracy of the Smoke World field (task W-13, 2026-11-23)

`uv run python -m serein.eval.hourly outputs/backtest/west_us_dev --out outputs/hourly`
(code in `src/serein/eval/hourly.py`). Smoke World and AirPlan show 72 hourly values per
place. SmokeCast is tested on daily averages only, so this checks the hourly values against
real hourly EPA readings at monitors, on the same hours for every method.

Forecasts compared, all made at the 18:30 UTC issue time the day before:

- **NOAA**: AQM bias-corrected hourly PM2.5 (the hourly shape Smoke World uses).
- **Serein hourly**: the NOAA shape scaled per local day to SmokeCast's daily median. This is
  what Smoke World shows in Serein mode.
- **Flat**: SmokeCast's daily median for every hour of the day (no hourly shape).
- **Daily rhythm**: SmokeCast's daily median spread over the hours by each monitor's typical
  fire-season daily shape, learned from earlier seasons only (2021-22 for 2023; 2021 for 2022).

## Results

RMSE in µg/m³ per hour; 95% intervals from resampling issue days (1000 resamples).
"Shape" is the correlation between the forecast's and the observed hour-to-hour pattern
within each place-day (0 = no information about which hours are worse).

Development 2023 (odd weeks, 77 issue days, about 1.6 million monitor-hours):

| Day | NOAA | Serein hourly | Flat | Daily rhythm | Serein vs. NOAA | Serein vs. flat | Shape NOAA | Shape rhythm |
|---|---|---|---|---|---|---|---|---|
| 0 | 13.9 | 11.8 | 11.7 | 11.7 | -2.1 (-3.8, -0.3) | +0.1 (-0.2, +0.4) | 0.20 | 0.10 |
| 1 | 14.8 | 12.7 | 12.1 | 12.1 | -2.0 (-3.0, -1.0) | +0.6 (+0.1, +1.3) | 0.16 | 0.06 |
| 2 | 15.2 | 13.4 | 12.9 | 13.0 | -1.8 (-2.8, -0.9) | +0.4 (+0.3, +0.7) | 0.17 | 0.06 |
| 3 | 15.5 | 15.5 | 13.3 | 13.2 | 0 | +2.2 (+1.4, +3.0) | 0.04 | 0.09 |

Inner fold, trained on 2021 and scored on 2022:

| Day | NOAA | Serein hourly | Flat | Daily rhythm | Serein vs. NOAA | Serein vs. flat |
|---|---|---|---|---|---|---|
| 0 | 12.2 | 10.7 | 10.6 | 10.7 | -1.4 (-2.3, -0.5) | +0.1 (-0.1, +0.4) |
| 1 | 11.5 | 10.2 | 10.1 | 10.2 | -1.3 (-1.8, -0.6) | +0.0 (-0.2, +0.3) |
| 2 | 11.7 | 11.2 | 11.1 | 11.1 | -0.4 (-1.1, +0.2) | +0.2 (-0.0, +0.4) |
| 3 | 11.1 | 11.1 | 11.0 | 11.1 | 0 | +0.1 (-0.7, +0.9) |

On day 3 NOAA's 72-hour AQM run ends early that morning, so there is too little of the day to
scale and Serein hourly equals NOAA.

## What it means

1. **Serein's correction helps hour by hour.** The scaled hourly values beat NOAA's raw hourly
   forecast on days 0-2 in 2023 and days 0-1 in 2022, with intervals below 0.
2. **The hour-to-hour pattern is not reliable.** Neither NOAA's hourly shape nor each monitor's
   typical daily rhythm tells much about which hours of a given day will be worst
   (correlations 0.04-0.30). A flat line at the daily value is as accurate or more accurate.
3. So the site should present the **daily level** as the tested forecast, and must not give
   "go out at this hour" advice based on the hourly pattern. The animation can still show
   NOAA's hourly pattern, labelled as such.
