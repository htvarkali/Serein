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
