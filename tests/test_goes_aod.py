from datetime import date

import numpy as np

from serein.data import goes_aod

PROJ = {"semi_major_axis": 6378137.0, "semi_minor_axis": 6356752.31414,
        "perspective_point_height": 35786023.0, "longitude_of_projection_origin": -137.0}


def test_subsatellite_point_maps_to_zero_scan_angles():
    x, y = goes_aod.latlon_to_scan([0.0], [-137.0], PROJ)
    assert abs(x[0]) < 1e-9 and abs(y[0]) < 1e-9


def test_scan_angles_follow_direction_and_hide_the_far_side():
    x, y = goes_aod.latlon_to_scan([38.0, 38.0, 0.0], [-122.0, -150.0, 43.0], PROJ)
    assert x[0] > 0 and y[0] > 0  # east and north of the subpoint
    assert x[1] < 0                # west of the subpoint
    assert np.isnan(x[2]) and np.isnan(y[2])  # other side of the Earth


def test_goes_west_switches_to_goes18_in_2023():
    assert goes_aod.west_satellite(date(2022, 9, 1)) == "noaa-goes17"
    assert goes_aod.west_satellite(date(2023, 1, 4)) == "noaa-goes18"
