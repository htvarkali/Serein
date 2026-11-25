import numpy as np
import pandas as pd

from serein.features.prepare import Prep
from serein.models.baselines import baselines

NAN = np.nan


def frame():
    # A: AQM on day 0 only, HRRR both days. B: HRRR day 1 only, no clean-air history.
    # C: nothing. D: AQM forecasts exactly 0 on day 0. No lead-2 columns at all.
    return pd.DataFrame({
        "point_id": ["A", "B", "C", "D"],
        "obs_prevday": [7.0, 9.0, NAN, 11.0],
        "aqm_mean_L0": [20.0, NAN, NAN, 0.0],
        "aqm_mean_L1": [NAN, NAN, NAN, NAN],
        "hrrr_smoke_mean_L0": [10.0, NAN, NAN, 50.0],
        "hrrr_smoke_mean_L1": [6.0, 2.0, NAN, NAN],
    })


def prep():
    return Prep(site_clim={"A": np.log1p(8.0), "B": np.log1p(6.0), "D": np.log1p(5.0)},
                site_bg={"A": np.log1p(4.0)}, global_clim=np.log1p(3.0))


def test_baselines_take_aqm_then_hrrr_with_background_then_persistence():
    df = frame()
    before = df.copy()
    out = baselines(df, prep(), [0, 1, 2])

    assert set(out) == {"persistence", "persistence_morning", "climatology", "hrrr_smoke",
                        "aqm_bc", "noaa_best"}
    assert all(v.shape == (4, 3) for v in out.values())
    np.testing.assert_allclose(out["persistence"], [[7.0] * 3, [9.0] * 3, [NAN] * 3, [11.0] * 3])
    np.testing.assert_allclose(out["climatology"], [[8.0] * 3, [6.0] * 3, [NAN] * 3, [5.0] * 3])
    # HRRR-Smoke models smoke only: the site's clean-air background is added, or the
    # median of all training days where the site has no clean-day history (B).
    np.testing.assert_allclose(out["hrrr_smoke"], [[14.0, 10.0, NAN], [NAN, 5.0, NAN],
                                                   [NAN, NAN, NAN], [53.0, NAN, NAN]])
    np.testing.assert_allclose(out["aqm_bc"], [[20.0, NAN, NAN], [NAN, NAN, NAN],
                                               [NAN, NAN, NAN], [0.0, NAN, NAN]])
    # A zero AQM forecast is a forecast, not a gap; a row with no source stays missing.
    np.testing.assert_allclose(out["noaa_best"], [[20.0, 10.0, 7.0], [9.0, 5.0, 9.0],
                                                  [NAN, NAN, NAN], [0.0, 11.0, 11.0]])
    pd.testing.assert_frame_equal(df, before)
