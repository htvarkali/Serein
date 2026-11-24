from datetime import datetime

import numpy as np

from serein import world


def test_each_local_day_is_scaled_to_serein_daily_mean_and_keeps_its_shape():
    start = datetime(2023, 8, 18, 19)
    hours = np.arange(world.HOURS)
    shape = 20 + 5 * np.sin(hours / 24 * 2 * np.pi)       # one point, a daily cycle
    noaa = shape[None, :].copy()
    daily = {L: np.array([40.0 + 10 * L]) for L in range(4)}
    out = world.scale_to_daily(noaa, start, np.array([-7.0]), datetime(2023, 8, 18), daily)
    local_day = np.array([((start.hour + h - 7) // 24) for h in hours])
    for L in (1, 2):
        m = local_day == L
        assert abs(out[0, m].mean() - daily[L][0]) < 1e-6
        assert np.allclose(out[0, m] / noaa[0, m], out[0, m][0] / noaa[0, m][0])  # same shape


def test_scaling_is_bounded():
    start = datetime(2023, 8, 18, 19)
    noaa = np.full((1, world.HOURS), 5.0)
    out = world.scale_to_daily(noaa, start, np.array([-7.0]), datetime(2023, 8, 18),
                               {1: np.array([500.0])})
    assert np.nanmax(out) == 5.0 * world.SCALE_BOUNDS[1]
