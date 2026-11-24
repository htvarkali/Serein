import numpy as np
import pandas as pd

from serein.features.prepare import Prep
from serein.models.baselines import baselines


def _table():
    return pd.DataFrame(
        {
            "issue_date": pd.to_datetime(["2023-08-01", "2023-08-01"]).date,
            "point_id": ["a", "b"],
            "kind": ["epa", "epa"],
            "obs_prevday": [10.0, 4.0],
            "obs_last6": [22.0, np.nan],
            "obs_last24": [15.0, 5.0],
            "hms_prev": [1, 0],
        }
    )


def test_morning_persistence_uses_the_last_six_hours_for_leads_0_and_1_only():
    out = baselines(_table(), Prep(site_clim={"a": 1.0, "b": 1.0}), [0, 1, 2, 3])
    m = out["persistence_morning"]
    assert m.shape == (2, 4)
    np.testing.assert_array_equal(m[0, :2], [22.0, 22.0])
    assert np.isnan(m[1, :2]).all()  # no morning readings stays missing, never filled
    assert np.isnan(m[:, 2:]).all()  # pre-registered for L0-L1 only


def test_morning_persistence_does_not_change_the_other_baselines():
    out = baselines(_table(), Prep(site_clim={"a": 1.0, "b": 1.0}), [0, 1, 2, 3])
    np.testing.assert_array_equal(out["persistence"][:, 0], [10.0, 4.0])
    # noaa_best still falls back to yesterday's value, not the morning mean
    np.testing.assert_array_equal(out["noaa_best"][:, 0], [10.0, 4.0])
