import numpy as np

from serein.eval.backtest import cutoff_for_hit_rate


def test_dial_cutoff_reaches_the_target_hit_rate_on_calibration_rows():
    obs = np.array([40.0, 50.0, 60.0, 70.0, 10.0, 5.0])
    prob = np.array([0.9, 0.7, 0.5, 0.3, 0.2, 0.1])
    c = cutoff_for_hit_rate(prob, obs, target=0.75)
    events = obs >= 35.5
    assert np.mean(prob[events] >= c) >= 0.75
    # the highest such cut-off: 0.5 catches 3 of 4 events, a higher one would not
    assert abs(c - 0.5) < 0.0125 + 1e-9


def test_dial_cutoff_is_missing_without_events():
    assert np.isnan(cutoff_for_hit_rate(np.array([0.2, 0.4]), np.array([5.0, 10.0]), 0.8))
