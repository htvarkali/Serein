"""The forecasts we must beat. All return µg/m³, shape [rows, n_leads], NaN = no forecast.

* persistence      tomorrow = yesterday's observed daily mean (hard to beat on clean days)
* climatology      the site's median from training seasons
* hrrr_smoke       NOAA HRRR-Smoke near-surface smoke + the site's clean-air background
                   (HRRR-Smoke only models smoke, so we add typical non-smoke PM2.5)
* aqm_bc           NOAA's official AQM PM2.5 forecast, bias-corrected (to 72 h)
* persistence_morning  L0-L1 only: mean of the 6 observed hours ending at the issue-time
                   cutoff (hours starting 11-16 UTC), carried forward. Pre-registered on
                   2026-11-23 (review item 7, after Berlinghieri et al. 2026); L2-L3 are NaN.
* noaa_best        legacy key: AQM-bc where it exists, else HRRR+bg, else persistence.
                   This is an availability fallback, including a non-NOAA last resort.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from serein.features.prepare import Prep


def _col(df, c):
    return df[c].to_numpy(dtype=float) if c in df else np.full(len(df), np.nan)


def baselines(df: pd.DataFrame, prep: Prep, leads: list[int]) -> dict[str, np.ndarray]:
    d = prep._add_derived(df)
    persist = _col(d, "obs_prevday")
    clim = np.expm1(d["point_id"].map(prep.site_clim).to_numpy(dtype=float))
    out = {
        "persistence": np.stack([persist] * len(leads), 1),
        "climatology": np.stack([clim] * len(leads), 1),
        "hrrr_smoke": np.stack([_col(d, f"hrrr_pm_L{lead}") for lead in leads], 1),
        "aqm_bc": np.stack([_col(d, f"aqm_mean_L{lead}") for lead in leads], 1),
    }
    morning = _col(d, "obs_last6")
    out["persistence_morning"] = np.stack(
        [morning if lead <= 1 else np.full(len(d), np.nan) for lead in leads], 1)
    best = out["aqm_bc"].copy()
    best = np.where(np.isfinite(best), best, out["hrrr_smoke"])
    best = np.where(np.isfinite(best), best, out["persistence"])
    out["noaa_best"] = best
    return out
