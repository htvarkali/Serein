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


def test_recalibration_maps_overconfident_probabilities_to_observed_frequency():
    from serein.eval.backtest import fit_probability_recalibration

    rng = np.random.default_rng(0)
    raw = rng.uniform(0, 1, 4000)
    # events really happen at half the stated rate
    obs = np.where(rng.uniform(0, 1, 4000) < raw / 2, 50.0, 5.0)
    iso = fit_probability_recalibration(raw, obs)
    cal = iso.predict(np.array([0.2, 0.6, 1.0]))
    assert np.all(np.diff(cal) >= 0)
    assert abs(cal[1] - 0.3) < 0.08


def test_recalibration_is_skipped_without_events():
    from serein.eval.backtest import fit_probability_recalibration

    assert fit_probability_recalibration(np.array([0.1, 0.9]), np.array([5.0, 6.0])) is None
