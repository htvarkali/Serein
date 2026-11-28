"""NASA FIRMS active-fire detections (VIIRS), and fire features at points.

Needs a free MAP_KEY: https://firms.modaps.eosdis.nasa.gov/api/map_key/
Put it in .env as FIRMS_MAP_KEY=...

Area API: /api/area/csv/{key}/{source}/{west,south,east,north}/{day_range}/{start_date}
For past seasons use the standard-processing ("_SP") archives; for live use "_NRT".
"""

from __future__ import annotations

import io
import os
from datetime import date, datetime, timedelta
from hashlib import sha256

import numpy as np
import pandas as pd

from serein.config import Region, load_env, raw_dir
from serein.http import get

API = "https://firms.modaps.eosdis.nasa.gov/api/area/csv"
SOURCES_SP = ["VIIRS_SNPP_SP", "VIIRS_NOAA20_SP"]
SOURCES_NRT = ["VIIRS_SNPP_NRT", "VIIRS_NOAA20_NRT", "VIIRS_NOAA21_NRT"]
MAX_DAYS_PER_CALL = 5


def _key() -> str:
    load_env()
    k = os.environ.get("FIRMS_MAP_KEY")
    if not k:
        raise RuntimeError("FIRMS_MAP_KEY is not set. Get a free key and put it in .env")
    return k


def contiguous_runs(days) -> list[tuple[date, date]]:
    """[(first, last), ...] for each run of consecutive days."""
    runs: list[tuple[date, date]] = []
    for d in sorted(set(days)):
        if runs and (d - runs[-1][1]).days == 1:
            runs[-1] = (runs[-1][0], d)
        else:
            runs.append((d, d))
    return runs


def download_range(start: date, end: date, region: Region, nrt: bool = False) -> pd.DataFrame:
    """Download detections for [start, end] (inclusive), cached per 5-day chunk."""
    sources = SOURCES_NRT if nrt else SOURCES_SP
    # Pad the box so smoke from fires just outside the region is counted.
    box = f"{region.lon_min - 5},{region.lat_min - 5},{region.lon_max + 5},{region.lat_max + 5}"
    box_key = sha256(box.encode("ascii")).hexdigest()[:16]
    parts = []
    d = start
    while d <= end:
        n = min(MAX_DAYS_PER_CALL, (end - d).days + 1)
        for src in sources:
            path = raw_dir("firms") / f"{src}_{d:%Y%m%d}_{n}d_{box_key}.parquet"
            if path.exists():
                parts.append(pd.read_parquet(path))
                continue
            r = get(f"{API}/{_key()}/{src}/{box}/{n}/{d:%Y-%m-%d}", allow_404=True)
            if r is None:
                continue
            try:
                text = r.text
            finally:
                r.close()
            if not text.strip() or text.lower().startswith("invalid"):
                continue
            df = pd.read_csv(io.StringIO(text))
            df["source"] = src
            df.to_parquet(path, index=False)
            parts.append(df)
        d += timedelta(days=n)
    if not parts:
        return pd.DataFrame()
    df = pd.concat(parts, ignore_index=True)
    return add_time(df)


def add_time(df: pd.DataFrame) -> pd.DataFrame:
    hhmm = df["acq_time"].astype(int).astype(str).str.zfill(4)
    df["time_utc"] = pd.to_datetime(df["acq_date"].astype(str) + " " + hhmm, format="%Y-%m-%d %H%M")
    return df


def load_cached() -> pd.DataFrame:
    files = sorted(raw_dir("firms").glob("*.parquet"))
    if not files:
        return pd.DataFrame()
    df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    df = df.drop_duplicates(subset=["latitude", "longitude", "acq_date", "acq_time", "source"])
    return add_time(df)


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (np.sin((lat2 - lat1) / 2) ** 2
         + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2)
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def bearing_rad(lat1, lon1, lat2, lon2):
    """Initial bearing from point 1 to point 2 (radians, 0 = north, clockwise)."""
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    x = np.sin(lon2 - lon1) * np.cos(lat2)
    y = np.cos(lat1) * np.sin(lat2) - np.sin(lat1) * np.cos(lat2) * np.cos(lon2 - lon1)
    return np.arctan2(x, y)


def fire_features(fires: pd.DataFrame, points: pd.DataFrame, issue_time: datetime,
                  window_hours: float = 24, u: np.ndarray | None = None,
                  v: np.ndarray | None = None,
                  acquisition_lag_hours: float = 0) -> pd.DataFrame:
    """Fire radiative power (FRP, MW) near each point in the window before issue time.

    The window is (end - window_hours, end], with end = issue_time minus
    ``acquisition_lag_hours`` (0 keeps detections right up to issue time).

    ``frp_upwind_250`` weights each fire by how much the point is downwind of it,
    using the point's wind (u east, v north, m/s).
    """
    cols = ["frp_50", "frp_100", "frp_250", "frp_upwind_250", "fire_dist_km"]
    out = pd.DataFrame(0.0, index=range(len(points)), columns=cols)
    out["fire_dist_km"] = 1000.0
    if fires is None or fires.empty:
        return out
    if not np.isfinite(acquisition_lag_hours) or acquisition_lag_hours < 0:
        raise ValueError("acquisition_lag_hours must be finite and nonnegative")
    end = issue_time - timedelta(hours=acquisition_lag_hours)
    t0 = end - timedelta(hours=window_hours)
    f = fires[(fires["time_utc"] > t0) & (fires["time_utc"] <= end)]
    if f.empty:
        return out
    flat, flon, frp = (f["latitude"].to_numpy(), f["longitude"].to_numpy(),
                       f["frp"].clip(lower=0).to_numpy())
    plat, plon = points["lat"].to_numpy(), points["lon"].to_numpy()
    has_wind = u is not None and v is not None
    # Blocks of points x all fires at once; ~4M distances per block keeps memory small.
    step = max(1, 4_000_000 // max(len(f), 1))
    for s0 in range(0, len(points), step):
        sl = slice(s0, min(s0 + step, len(points)))
        dist = haversine_km(plat[sl, None], plon[sl, None], flat[None], flon[None])
        out.loc[out.index[sl], "fire_dist_km"] = np.minimum(dist.min(1), 1000.0)
        for r in (50, 100, 250):
            out.loc[out.index[sl], f"frp_{r}"] = np.where(dist <= r, frp[None], 0.0).sum(1)
        if has_wind:
            uu, vv = u[sl], v[sl]
            ok = np.isfinite(uu) & np.isfinite(vv)
            # Direction smoke would travel from fire to point vs. wind direction.
            b = bearing_rad(flat[None], flon[None], plat[sl, None], plon[sl, None])
            wind_to = np.arctan2(np.where(ok, uu, 0), np.where(ok, vv, 0))[:, None]
            align = np.clip(np.cos(b - wind_to), 0, None)
            w = np.where(dist <= 250, frp[None] * align / np.maximum(dist, 10), 0.0).sum(1)
            out.loc[out.index[sl], "frp_upwind_250"] = np.where(ok, w, 0.0)
    return out
