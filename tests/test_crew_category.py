import numpy as np

from serein import crew
from serein.aqi import BREAKPOINTS_2024, CATEGORIES, pm25_to_category


def test_crew_category_matches_the_aqi_module_at_every_breakpoint():
    edges = [x for lo, hi, _, _ in BREAKPOINTS_2024 for x in (lo, hi)] + [325.5, 400.0]
    medians = sorted({round(x, 2) for e in edges for x in (e - 0.05, e, e + 0.05) if x >= 0})
    for m in medians:
        o = crew.outlook([m * 0.5, m * 0.8, m, m * 1.2, m * 1.5], lead=1)
        assert o.category == CATEGORIES[int(pm25_to_category(np.array([m]))[0])], m
