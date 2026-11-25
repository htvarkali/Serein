"""EPA Air Quality Index for 24-hour PM2.5.

EPA revised the PM2.5 breakpoints on 2024-02-07, effective 2024-05-06.
Use the scale that was in force on the day being scored, because the EPA
forecasts we compare against were issued on that scale.
"""

from __future__ import annotations

from datetime import date

import numpy as np

NEW_SCALE_START = date(2024, 5, 6)

# (conc_lo, conc_hi, aqi_lo, aqi_hi)
BREAKPOINTS_2024 = [
    (0.0, 9.0, 0, 50),
    (9.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 125.4, 151, 200),
    (125.5, 225.4, 201, 300),
    (225.5, 325.4, 301, 500),
]
BREAKPOINTS_2012 = [
    (0.0, 12.0, 0, 50),
    (12.1, 35.4, 51, 100),
    (35.5, 55.4, 101, 150),
    (55.5, 150.4, 151, 200),
    (150.5, 250.4, 201, 300),
    (250.5, 350.4, 301, 400),
    (350.5, 500.4, 401, 500),
]

CATEGORIES = [
    "Good",
    "Moderate",
    "Unhealthy for Sensitive Groups",
    "Unhealthy",
    "Very Unhealthy",
    "Hazardous",
]
CATEGORY_INDEX = {c.lower(): i for i, c in enumerate(CATEGORIES)}
USG_THRESHOLD = 35.5  # µg/m³; the same on both scales


def _table(on: date | None):
    if on is None or on >= NEW_SCALE_START:
        return BREAKPOINTS_2024
    return BREAKPOINTS_2012


def pm25_to_aqi(conc, on: date | None = None):
    """24-h PM2.5 (µg/m³) to AQI. Vectorized. NaN stays NaN."""
    c = np.floor(np.asarray(conc, dtype=float) * 10 + 1e-6) / 10  # EPA truncates to 0.1
    c = np.clip(c, 0, None)
    out = np.full(c.shape, np.nan)
    table = _table(on)
    for lo, hi, alo, ahi in table:
        m = (c >= lo - 1e-9) & (c <= hi + 1e-9)
        out[m] = (ahi - alo) / (hi - lo) * (c[m] - lo) + alo
    top = table[-1]
    out[c > top[1]] = 500
    return np.round(out)


def aqi_to_category(aqi):
    a = np.asarray(aqi, dtype=float)
    bins = [50, 100, 150, 200, 300]
    cat = np.digitize(a, bins, right=True).astype(float)
    return np.where(np.isnan(a), np.nan, cat)


def pm25_to_category(conc, on: date | None = None):
    """Category index 0..5 (Good..Hazardous)."""
    c = np.asarray(conc, dtype=float)
    c = np.floor(np.clip(c, 0, None) * 10 + 1e-6) / 10
    table = _table(on)
    upper = [hi for _, hi, _, _ in table][:5]
    cat = np.digitize(c, upper, right=True).astype(float)
    cat = np.minimum(cat, 5)
    return np.where(np.isnan(np.asarray(conc, dtype=float)), np.nan, cat)


def category_from_name(name: str) -> float:
    if not isinstance(name, str):
        return np.nan
    return float(CATEGORY_INDEX.get(name.strip().lower(), np.nan))
