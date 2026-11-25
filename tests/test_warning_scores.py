import numpy as np
import pytest

from serein.eval.backtest import warning_scores


def test_warning_scores_count_usg_days_and_skip_missing_readings():
    warn = np.array([True, True, False, False, True, False, True, False])
    obs = np.array([40.0, 20.0, 50.0, 10.0, 35.5, 35.4, np.nan, 5.0])
    # Readings at or above 35.5: rows 0, 2 and 4. Warned: 0, 1, 4 and 6 (no reading).
    # FAR is false alarms over warnings (1 of 3), not over clean days (1 of 4).
    s = warning_scores(warn, obs)
    assert s["usg_events"] == 3
    assert s["usg_pod"] == pytest.approx(2 / 3)
    assert s["usg_far"] == pytest.approx(1 / 3)
    assert s["usg_csi"] == pytest.approx(2 / 4)


def test_warning_scores_leave_undefined_rates_missing():
    s = warning_scores(np.array([False, False]), np.array([10.0, 20.0]))
    assert s["usg_events"] == 0
    assert all(np.isnan(s[k]) for k in ("usg_pod", "usg_far", "usg_csi"))

    s = warning_scores(np.array([False, True]), np.array([40.0, 20.0]))
    assert (s["usg_pod"], s["usg_far"], s["usg_csi"]) == (0.0, 1.0, 0.0)
