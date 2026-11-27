# Summary of west_us_dev (development run (not the final test))

Primary criterion (BACKTEST_PROTOCOL.md section 6): PASS
PASS needs the 95% day-bootstrap interval of RMSE(SmokeCast) - RMSE(noaa_best) entirely below 0 at lead 1 and lead 2.

## Primary comparison, all rows

```
 lead     n  rmse_smokecast  rmse_noaa_best   diff  ci_lo  ci_hi
    0 25030           4.362          10.138 -5.775 -8.468 -3.299
    1 25041           7.776          11.022 -3.246 -4.599 -1.754
    2 24730           9.721          12.348 -2.626 -3.782 -1.479
    3 23787          11.398          15.475 -4.077 -6.964 -1.756
```

## Split by season year

```
 year  lead     n  rmse_smokecast  rmse_noaa_best   diff  ci_lo  ci_hi
 2023     0 25030           4.362          10.138 -5.775 -8.468 -3.299
 2023     1 25041           7.776          11.022 -3.246 -4.599 -1.754
 2023     2 24730           9.721          12.348 -2.626 -3.782 -1.479
 2023     3 23787          11.398          15.475 -4.077 -6.964 -1.756
```

## Every competitor on its own rows

```
 lead             model     n   rmse
    0         smokecast 25030  4.362
    0         noaa_best 25030 10.138
    0            aqm_bc 25030 10.138
    0        hrrr_smoke 25030 12.630
    0       persistence 24732 10.149
    0       climatology 23944 13.439
    0               gbm 25030  5.444
    0 smokecast_nograph 25030  4.454
    1         smokecast 25041  7.776
    1         noaa_best 25041 11.022
    1            aqm_bc 25041 11.022
    1        hrrr_smoke 25041  9.053
    1       persistence 24562 13.795
    1       climatology 23948 13.756
    1               gbm 25041  8.824
    1 smokecast_nograph 25041  8.199
    2         smokecast 24730  9.721
    2         noaa_best 24730 12.348
    2            aqm_bc 24730 12.348
    2        hrrr_smoke     0    NaN
    2       persistence 24144 14.965
    2       climatology 23649 13.811
    2               gbm 24730 10.989
    2 smokecast_nograph 24730 10.125
    3         smokecast 24432 11.584
    3         noaa_best 23787 15.475
    3            aqm_bc     0    NaN
    3        hrrr_smoke     0    NaN
    3       persistence 23787 15.475
    3       climatology 23365 13.708
    3               gbm 24432 12.640
    3 smokecast_nograph 24432 12.014
```

## SHA-256 of the files behind these numbers

- `predictions.parquet`: effa4fcd41d6b9bb85a45c2d7225e4e2113206c4bb552a79addf9b15d759b670
- `smokecast.pt`: d0581993f53c5a5fcdf7cc85a97a56ce21a22d2d756c7e1f7d6da59b9e65dd4f
- `model.json`: 1ab2b22b303efbb992c48fd830f2123d37ef8739abfb88ea18df7f0803e64527
- `conformal.json`: bf22f5c29cb398077045c83d0bb9aade1b79e8adfeafd5ca1c05787d2ef00387
- `report.md`: 9a7ac83b849b3705d2a24def3af3525a03eb156c77a66679fee846c1ca4c917a
- `table:table_calibrate.parquet`: 2d03fda7fe34955e1a146933f0c5c8fc3ebe0795c2e11f79e9830938bbc9c7ff
