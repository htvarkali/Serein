from datetime import datetime

import numpy as np

from serein.eval import hourly
from serein.world import HOURS


def test_flat_forecast_repeats_each_local_days_value():
    start, issue = datetime(2023, 8, 18, 19), datetime(2023, 8, 18)
    daily = {L: np.array([10.0 * (L + 1)]) for L in range(4)}
    out = hourly.flat_daily(start, np.array([-7.0]), issue, daily, 1)
    leads = hourly.lead_of_hour(start, np.array([-7.0]), issue)[0]
    for L in range(4):
        assert np.all(out[0, leads == L] == 10.0 * (L + 1))


def test_profile_forecast_keeps_the_daily_mean_and_follows_the_shape():
    start = datetime(2023, 8, 19, 7)  # local midnight at UTC-7, so 3 whole local days
    prof = np.ones((1, 24))
    prof[0, :12], prof[0, 12:] = 1.5, 0.5
    flat = np.full((1, HOURS), 20.0)
    out = hourly.profile_forecast(start, np.array([-7.0]), flat, prof)
    assert np.isclose(out[0, :24].mean(), 20.0)
    assert out[0, 0] == 30.0 and out[0, 12] == 10.0


def test_summary_reports_rmse_per_lead_and_method():
    rows = []
    for d in range(10):
        row = {"issue_date": d, "lead": 1, "n": 100, "shape_den_o": 1.0}
        for m, sse in (("noaa", 400.0), ("serein", 100.0), ("flat", 100.0), ("profile", 100.0)):
            row[f"sse_{m}"] = sse
        for m in ("noaa", "serein", "profile"):
            row[f"shape_num_{m}"], row[f"shape_den_f_{m}"] = 0.5, 1.0
        rows.append(row)
    import pandas as pd
    s = hourly.summarize(pd.DataFrame(rows), n_boot=50).iloc[0]
    assert np.isclose(s["rmse_noaa"], 2.0) and np.isclose(s["rmse_serein"], 1.0)
    assert np.isclose(s["serein_minus_noaa"], -1.0)
