from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from serein import world

START = datetime(2023, 8, 18, 19)


def utc(hours):
    return pd.Timestamp(START + timedelta(hours=hours), tz="UTC")


def test_hourly_noaa_places_values_by_utc_hour_and_skips_unknown_points():
    aqm = pd.DataFrame(
        {
            "point_id": ["A", "B", "Z", "A", "A"],
            "valid_utc": [utc(0), utc(10), utc(1), utc(world.HOURS), utc(-1)],
            "value": [1.0, 2.0, 3.0, 4.0, 5.0],
        }
    )
    out = world.hourly_noaa(aqm, ["A", "B"], START)
    assert out.shape == (2, world.HOURS)
    assert out[0, 0] == 1.0 and out[1, 10] == 2.0
    assert (
        np.isfinite(out).sum() == 2
    )  # point Z and the hours outside the 72-hour window are dropped
    assert np.isnan(world.hourly_noaa(pd.DataFrame(), ["A"], START)).all()


def test_wind_keeps_hours_in_the_window_and_places_u_and_v():
    rows = [
        ("u10", 0, "A", 1.0),
        ("v10", 0, "A", -1.0),
        ("u10", 3, "B", 2.0),
        ("v10", 3, "B", -2.0),
        ("u10", 3, "Z", 9.0),  # unknown point
        ("u10", world.HOURS + 3, "A", 9.0),  # after the window
        ("t2m", 6, "A", 300.0),  # not wind
    ]
    hrrr = pd.DataFrame(
        [(var, utc(h), p, x) for var, h, p, x in rows],
        columns=["var", "valid_utc", "point_id", "value"],
    )
    hours, u, v = world.wind(hrrr, ["A", "B"], START)
    assert hours == [0, 3]
    assert u[0, 0] == 1.0 and v[0, 0] == -1.0 and u[1, 1] == 2.0 and v[1, 1] == -2.0
    assert np.isnan(u[0, 1]) and np.isnan(u[1, 0])
    empty_hours, eu, ev = world.wind(pd.DataFrame(), ["A", "B"], START)
    assert empty_hours == [] and eu.shape == ev.shape == (2, 0)
