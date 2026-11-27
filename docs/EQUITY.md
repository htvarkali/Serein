# Who lives far from an air monitor? (2026-11-23)

`uv run python -m serein.eval.equity --out outputs/equity` (inputs and method in
`src/serein/eval/equity.py`: ACS 2019-2023 5-year median household income and
population by census tract, 2023 tract boundaries, the 425 EPA PM2.5 monitors in the
study box). 13,086 tracts, about 56.2 million people.

| Tract income quintile | Income range | People | Median km to a monitor | Share 25+ km away | Share 50+ km away |
|---|---|---|---|---|---|
| 1 (lowest) | $7,000-$62,998 | 10,040,679 | 6.1 | 10.8% | 3.7% |
| 2 | $63,003-$81,339 | 11,028,149 | 6.8 | 6.6% | 1.6% |
| 3 | $81,346-$101,171 | 11,505,102 | 7.4 | 4.8% | 0.7% |
| 4 | $101,173-$130,500 | 11,656,626 | 8.1 | 2.2% | 0.3% |
| 5 (highest) | $130,521-$250,001 | 11,747,941 | 8.8 | 0.6% | 0.0% |

Reading it honestly: the typical lower-income resident lives slightly closer to a
monitor (many live in cities), but the share living 25 km or more from any monitor is
about 18 times higher in the lowest-income fifth than in the highest (10.8% vs. 0.6%,
roughly 1.1 million people). Those are mostly rural tracts. Low-cost sensors such as
PurpleAir are not counted here.

## Does Serein work far from a monitor?

Development run `dev_holdout_prepfix` (2026-11-27; 2023 scoring weeks, 20% of monitors
hidden from the model with seed 1234, preprocessing fitted without them). RMSE in µg/m³
at the hidden monitors, by distance to the nearest monitor the model could see:

| Distance band | Hidden sites | Day 1: Serein vs. NOAA best | Day 2: Serein vs. NOAA best |
|---|---|---|---|
| under 15 km | 35 | 6.6 vs. 7.5 | 6.4 vs. 7.5 |
| 15-30 km | 26 | 10.8 vs. 14.0 | 12.3 vs. 14.5 |
| 30-60 km | 21 | 8.1 vs. 12.3 | 12.1 vs. 14.7 |
| 60 km or more | 3 | 2.7 vs. 3.7 | 3.3 vs. 4.2 |

Recomputed from the run's saved predictions (great-circle distance to the nearest
visible monitor, rows where both forecasts and the observation exist). The same
method on the earlier `dev_holdout` run gives the table this page used to show,
except one site that it counts under 15 km where the old table had 34.

Serein is better than NOAA's best forecast in every band. The 60+ km band has only 3
sites, too few to rely on. These are development numbers; the final test repeats the
hidden-monitor run on 2024-25.
