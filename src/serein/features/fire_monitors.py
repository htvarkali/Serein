"""Inputs from nearby temporary fire monitors (TODO B-8, free alternative to PurpleAir).

For each forecast point and issue day, readings of AirFire's temporary monitors
(``serein.data.airfire``) within ``RADIUS_KM``, up to the same hour cutoff as the
AirNow readings:

  tmon_n             monitors that reported in the last 24 h
  tmon_near_km       distance to the nearest one (``FAR_KM`` if none)
  tmon_idw_last6     inverse-distance mean of their last-6 h means
  tmon_idw_last24    inverse-distance mean of their last-24 h means
  tmon_max24         highest hourly reading among them in the last 24 h
  tmon_upwind_max24  the same, only monitors upwind of the point (within 60 degrees
                     of the direction the wind comes from at issue time)

Readings are missing (NaN) when no monitor qualifies; the model then sees the
missing flag. The settings were fixed before the first run (docs/EXPERIMENTS.md).
"""

from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd

from serein.data.availability import Availability
from serein.data.firms import bearing_rad, haversine_km

RADIUS_KM = 150.0
FAR_KM = 300.0
MIN_DIST_KM = 10.0  # inverse-distance weights stop growing inside this distance
UPWIND_COS = 0.5  # cos(60 degrees)
COLUMNS = [
    "tmon_n",
    "tmon_near_km",
    "tmon_idw_last6",
    "tmon_idw_last24",
    "tmon_max24",
    "tmon_upwind_max24",
]


def _empty(n: int) -> dict:
    out = {c: np.full(n, np.nan) for c in COLUMNS}
    out["tmon_n"] = np.zeros(n)
    out["tmon_near_km"] = np.full(n, FAR_KM)
    return out


def monitor_features(
    monitors: pd.DataFrame,
    hourly: pd.DataFrame,
    points: pd.DataFrame,
    day: date,
    av: Availability,
    u=None,
    v=None,
) -> pd.DataFrame:
    """Features for one issue day. ``points`` needs ``point_id, lat, lon``."""
    n = len(points)
    out = _empty(n)
    t = pd.Timestamp(av.last_obs_hour_start(day))
    win = hourly[(hourly["time_utc"] > t - pd.Timedelta(hours=24)) & (hourly["time_utc"] <= t)]
    if win.empty:
        return pd.DataFrame({"point_id": points["point_id"].to_numpy(), **out})
    last6 = win[win["time_utc"] > t - pd.Timedelta(hours=6)].groupby("site_id")["pm25"].mean()
    g = win.groupby("site_id")["pm25"]
    stats = pd.DataFrame({"last24": g.mean(), "max24": g.max()}).join(last6.rename("last6"))
    m = monitors.set_index("site_id").loc[stats.index]
    mlat, mlon = m["lat"].to_numpy(float), m["lon"].to_numpy(float)
    plat, plon = points["lat"].to_numpy(float), points["lon"].to_numpy(float)

    dist = haversine_km(plat[:, None], plon[:, None], mlat[None], mlon[None])  # [points, monitors]
    near = dist <= RADIUS_KM
    w = np.where(near, 1.0 / np.maximum(dist, MIN_DIST_KM), 0.0)

    def idw(values):
        ok = np.isfinite(values)[None] & near
        ww = np.where(ok, w, 0.0)
        s = ww.sum(1)
        num = (ww * np.nan_to_num(values)[None]).sum(1)
        return np.where(s > 0, num / np.where(s > 0, s, 1.0), np.nan)

    def masked_max(values, mask):
        x = np.where(mask, values[None], -np.inf).max(1)
        return np.where(np.isfinite(x), x, np.nan)

    max24 = stats["max24"].to_numpy(float)
    out["tmon_n"] = near.sum(1).astype(float)
    out["tmon_near_km"] = np.minimum(dist.min(1), FAR_KM)
    out["tmon_idw_last6"] = idw(stats["last6"].to_numpy(float))
    out["tmon_idw_last24"] = idw(stats["last24"].to_numpy(float))
    out["tmon_max24"] = masked_max(max24, near)
    if u is not None and v is not None:
        u, v = np.asarray(u, float), np.asarray(v, float)
        ok = np.isfinite(u) & np.isfinite(v)
        # Bearing from monitor to point vs. the direction the wind blows toward.
        b = bearing_rad(mlat[None], mlon[None], plat[:, None], plon[:, None])
        wind_to = np.arctan2(np.where(ok, u, 0.0), np.where(ok, v, 0.0))[:, None]
        upwind = near & (np.cos(b - wind_to) >= UPWIND_COS) & ok[:, None]
        out["tmon_upwind_max24"] = masked_max(max24, upwind)
    return pd.DataFrame({"point_id": points["point_id"].to_numpy(), **out})
