from datetime import date

import numpy as np
import pandas as pd
import pytest

from serein.data.availability import Availability
from serein.features.fire_monitors import FAR_KM, monitor_features

AV = Availability()  # issue 18:30 UTC, newest allowed reading starts 16:00 UTC
DAY = date(2023, 8, 10)
POINT = pd.DataFrame({"point_id": ["P"], "lat": [40.0], "lon": [-120.0]})


def _hourly(site, values_by_hour):
    return pd.DataFrame(
        {
            "site_id": site,
            "time_utc": [
                pd.Timestamp("2023-08-10") + pd.Timedelta(hours=h) for h in values_by_hour
            ],
            "pm25": list(values_by_hour.values()),
        }
    )


def test_readings_after_the_cutoff_are_never_used():
    mons = pd.DataFrame({"site_id": ["A"], "lat": [40.1], "lon": [-120.0]})
    hourly = _hourly("A", {15: 20.0, 16: 40.0, 17: 900.0, 18: 900.0})
    f = monitor_features(mons, hourly, POINT, DAY, AV).iloc[0]
    assert f["tmon_max24"] == 40.0
    assert f["tmon_idw_last6"] == pytest.approx(30.0)
    assert f["tmon_n"] == 1


def test_far_monitors_are_ignored_and_no_monitor_means_missing():
    mons = pd.DataFrame({"site_id": ["FAR"], "lat": [43.0], "lon": [-120.0]})  # ~330 km north
    f = monitor_features(mons, _hourly("FAR", {12: 300.0}), POINT, DAY, AV).iloc[0]
    assert f["tmon_n"] == 0
    assert f["tmon_near_km"] == FAR_KM
    assert np.isnan(f["tmon_max24"]) and np.isnan(f["tmon_idw_last24"])

    none = pd.DataFrame({"site_id": pd.Series(dtype=str),
                         "time_utc": pd.Series(dtype="datetime64[ns]"),
                         "pm25": pd.Series(dtype=float)})
    empty = monitor_features(mons, none, POINT, DAY, AV).iloc[0]
    assert empty["tmon_n"] == 0 and np.isnan(empty["tmon_upwind_max24"])


def test_closer_monitors_weigh_more():
    mons = pd.DataFrame({"site_id": ["NEAR", "MID"], "lat": [40.2, 41.0], "lon": [-120.0, -120.0]})
    hourly = pd.concat([_hourly("NEAR", {16: 100.0}), _hourly("MID", {16: 10.0})])
    f = monitor_features(mons, hourly, POINT, DAY, AV).iloc[0]
    assert 55.0 < f["tmon_idw_last6"] < 100.0  # weights 1/22 km vs 1/111 km
    assert f["tmon_max24"] == 100.0


def test_upwind_keeps_only_monitors_the_wind_blows_from():
    # North monitor is smoky, south one is clean. A north wind (blowing toward the
    # south, v < 0) carries the north monitor's smoke to the point.
    mons = pd.DataFrame({"site_id": ["N", "S"], "lat": [40.5, 39.5], "lon": [-120.0, -120.0]})
    hourly = pd.concat([_hourly("N", {16: 200.0}), _hourly("S", {16: 5.0})])
    from_north = monitor_features(mons, hourly, POINT, DAY, AV, u=[0.0], v=[-5.0]).iloc[0]
    from_south = monitor_features(mons, hourly, POINT, DAY, AV, u=[0.0], v=[5.0]).iloc[0]
    no_wind = monitor_features(mons, hourly, POINT, DAY, AV, u=[np.nan], v=[np.nan]).iloc[0]
    assert from_north["tmon_upwind_max24"] == 200.0
    assert from_south["tmon_upwind_max24"] == 5.0
    assert np.isnan(no_wind["tmon_upwind_max24"])
