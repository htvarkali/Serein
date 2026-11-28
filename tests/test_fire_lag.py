"""Optional posting delay for fire detections (docs/CODE_REVIEW_2026-11-27.md, item 1).

The default (0 hours) must leave every existing feature table unchanged.
"""

from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from serein.data import firms
from serein.data.availability import Availability

ISSUE = datetime(2023, 8, 18, 18, 30)
POINT = pd.DataFrame({"lat": [45.0], "lon": [-120.0]})


def _fires(*hours_before_issue, frp=100.0):
    return pd.DataFrame({
        "latitude": [45.01] * len(hours_before_issue),
        "longitude": [-120.0] * len(hours_before_issue),
        "frp": [frp] * len(hours_before_issue),
        "time_utc": [ISSUE - timedelta(hours=h) for h in hours_before_issue],
    })


def test_default_window_ends_at_issue_time():
    av = Availability()
    assert av.fire_lag_hours == 0
    start, end = av.firms_window(date(2023, 8, 18))
    assert end == ISSUE and start == ISSUE - timedelta(hours=24)


def test_lag_moves_the_window_earlier_and_keeps_its_length():
    av = Availability(fire_lag_hours=3)
    start, end = av.firms_window(date(2023, 8, 18))
    assert end == ISSUE - timedelta(hours=3)
    assert end - start == timedelta(hours=24)


def test_lag_is_read_from_the_study_config_and_must_be_valid():
    av = Availability.from_study({"issue_hour_utc": 18.5, "availability": {"fire_lag_hours": 3}})
    assert av.fire_lag_hours == 3
    for bad in (-1, float("nan"), True):
        with pytest.raises((ValueError, TypeError)):
            Availability(fire_lag_hours=bad)


def test_fire_features_skip_detections_inside_the_posting_delay():
    fires = _fires(0.5, 2.0, 5.0)          # half an hour, 2 h and 5 h before issue
    now = firms.fire_features(fires, POINT, ISSUE, 24)
    lagged = firms.fire_features(fires, POINT, ISSUE, 24, acquisition_lag_hours=3)
    assert now.loc[0, "frp_50"] == pytest.approx(300.0)
    assert lagged.loc[0, "frp_50"] == pytest.approx(100.0)   # only the 5 h one
    # The window keeps 24 h: a detection 26 h before issue counts only with the lag.
    old = _fires(26.0)
    assert firms.fire_features(old, POINT, ISSUE, 24).loc[0, "frp_50"] == 0
    assert firms.fire_features(old, POINT, ISSUE, 24, acquisition_lag_hours=3).loc[0, "frp_50"] == 100


def test_default_lag_gives_the_same_features_as_before():
    rng = np.random.default_rng(0)
    fires = _fires(*rng.uniform(0, 30, 40))
    a = firms.fire_features(fires, POINT, ISSUE, 24)
    b = firms.fire_features(fires, POINT, ISSUE, 24, acquisition_lag_hours=0)
    pd.testing.assert_frame_equal(a, b)
    with pytest.raises(ValueError):
        firms.fire_features(fires, POINT, ISSUE, 24, acquisition_lag_hours=-1)
