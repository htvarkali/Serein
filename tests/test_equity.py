import numpy as np
import pandas as pd

from serein.eval import equity


def test_haversine_one_degree_of_latitude_is_about_111_km():
    assert abs(equity.haversine_km(37.0, -120.0, 38.0, -120.0) - 111.2) < 0.5


def test_summary_weights_by_population_and_counts_far_residents():
    t = pd.DataFrame({
        "income": np.repeat([20_000, 40_000, 60_000, 80_000, 100_000], 2),
        "population": [100, 300, 100, 100, 100, 100, 100, 100, 100, 100],
        "km": [60, 5, 10, 10, 10, 10, 10, 10, 10, 10],
    })
    s = equity.summarize(t)
    lowest = s.iloc[0]
    assert lowest["people"] == 400
    assert lowest["share_people_over_50km"] == 0.25
    assert s.iloc[-1]["share_people_over_25km"] == 0.0


REGION = {"lat_min": 32.0, "lat_max": 49.0, "lon_min": -125.0, "lon_max": -114.0}


def test_distance_to_box_edge():
    t = pd.DataFrame({"lat": [40.0, 32.5, 40.0], "lon": [-120.0, -120.0, -114.5]})
    km = equity.km_to_box_edge(t, REGION)
    assert abs(km[0] - 5 * 111.2 * np.cos(np.radians(40))) < 0.1   # nearest: east edge
    assert abs(km[1] - 0.5 * 111.2) < 0.1                            # south edge
    assert abs(km[2] - 0.5 * 111.2 * np.cos(np.radians(40))) < 0.1   # east edge


def test_edge_check_counts_only_far_people_nearer_the_edge_than_a_monitor():
    t = pd.DataFrame({
        "income": np.repeat([20_000, 40_000, 60_000, 80_000, 100_000], 2),
        "population": [100, 300, 100, 100, 100, 100, 100, 100, 100, 100],
        "km":      [60, 5, 30, 10, 10, 10, 10, 10, 10, 10],
        "edge_km": [20, 1, 300, 1, 1, 1, 1, 1, 1, 1],
    })
    e = equity.edge_check(t)
    low, q2 = e.iloc[0], e.iloc[1]
    assert low["people_over_25km"] == 100
    assert low["of_them_possibly_closer_outside_box"] == 100   # edge 20 km < monitor 60 km
    assert low["share_of_quintile_if_all_removed"] == 0.0
    assert q2["people_over_25km"] == 100
    assert q2["of_them_possibly_closer_outside_box"] == 0      # edge 300 km > monitor 30 km
    assert q2["share_of_quintile_if_all_removed"] == 0.5
