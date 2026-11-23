"""GOES ABI aerosol optical depth (AOD) at monitor points: satellite smoke haze.

AOD measures how much light the whole air column scatters or absorbs. Thick wildfire
smoke raises it, so the satellite sees a plume over places with no monitor. It is a
column value (not ground-level PM2.5), it needs daylight, and clouds hide it.

Source (free, no key): NOAA's public AWS buckets, product ABI-L2-AODC (CONUS sector,
a scan about every 5 minutes):
  https://noaa-goes17.s3.amazonaws.com/ABI-L2-AODC/YYYY/DDD/HH/OR_ABI-L2-AODC-...nc
For the western US we use the GOES-West satellite: GOES-17 until it was replaced by
GOES-18 as GOES-West on 2023-01-04.

No peeking: we read scans that start in the hours 14-17 UTC of the issue day, the last
one ending before 17:10 UTC, well before the 18:30 UTC issue time (products appear on
AWS within minutes of the scan).

Per day we keep only point values, never the raw files: for each point the mean of
high-quality AOD pixels (quality flag 0) within a small box around it, per scan hour.
"""

from __future__ import annotations

import io
import re
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd

from serein.config import interim_dir
from serein.http import get

BUCKET = "https://{sat}.s3.amazonaws.com"
PRODUCT = "ABI-L2-AODC"
HOURS_UTC = (14, 15, 16, 17)
GOES18_WEST_FROM = date(2023, 1, 4)
BOX_PIXELS = 2  # +-2 pixels of 2 km: about a 10 km box around each point


def west_satellite(d: date) -> str:
    return "noaa-goes18" if d >= GOES18_WEST_FROM else "noaa-goes17"


def list_keys(sat: str, d: date, hour: int) -> list[str]:
    doy = d.timetuple().tm_yday
    url = f"{BUCKET.format(sat=sat)}/?list-type=2&prefix={PRODUCT}/{d:%Y}/{doy:03d}/{hour:02d}/"
    r = get(url, timeout=60)
    try:
        return sorted(re.findall(r"<Key>([^<]+\.nc)</Key>", r.text))
    finally:
        r.close()


def latlon_to_scan(lat, lon, proj: dict) -> tuple[np.ndarray, np.ndarray]:
    """Geodetic lat/lon (degrees) to ABI fixed-grid scan angles x, y (radians).

    GOES-R Product User Guide, section 4.2.8 (forward navigation).
    """
    r_eq, r_pol = proj["semi_major_axis"], proj["semi_minor_axis"]
    h = proj["perspective_point_height"] + r_eq
    lon0 = np.radians(proj["longitude_of_projection_origin"])
    lat, lon = np.radians(np.asarray(lat, float)), np.radians(np.asarray(lon, float))
    e2 = 1 - (r_pol / r_eq) ** 2
    phi_c = np.arctan((r_pol**2 / r_eq**2) * np.tan(lat))
    r_c = r_pol / np.sqrt(1 - e2 * np.cos(phi_c) ** 2)
    sx = h - r_c * np.cos(phi_c) * np.cos(lon - lon0)
    sy = -r_c * np.cos(phi_c) * np.sin(lon - lon0)
    sz = r_c * np.sin(phi_c)
    # A point is visible only if it faces the satellite.
    visible = h * (h - sx) >= sy**2 + (r_eq**2 / r_pol**2) * sz**2
    y = np.arctan(sz / sx)
    x = np.arcsin(-sy / np.sqrt(sx**2 + sy**2 + sz**2))
    return np.where(visible, x, np.nan), np.where(visible, y, np.nan)


def point_values(ds, points: pd.DataFrame) -> pd.DataFrame:
    """Mean of quality-0 AOD in a small box around each point, and the pixel count."""
    proj = ds["goes_imager_projection"].attrs
    proj = {
        k: float(np.asarray(proj[k]).ravel()[0])
        for k in (
            "semi_major_axis",
            "semi_minor_axis",
            "perspective_point_height",
            "longitude_of_projection_origin",
        )
    }
    xs, ys = ds["x"].values, ds["y"].values
    px, py = latlon_to_scan(points["lat"].to_numpy(), points["lon"].to_numpy(), proj)
    aod = ds["AOD"].values
    good = ds["DQF"].values == 0
    aod = np.where(good & np.isfinite(aod), aod, np.nan)
    # x increases with column index, y decreases with row index on the ABI grid.
    col = np.searchsorted(xs, px)
    row = np.searchsorted(-ys, -py)
    out_mean, out_n = np.full(len(points), np.nan), np.zeros(len(points), int)
    dx = abs(xs[1] - xs[0])
    for i in range(len(points)):
        if not (np.isfinite(px[i]) and np.isfinite(py[i])):
            continue
        if (
            px[i] < xs.min() - dx
            or px[i] > xs.max() + dx
            or py[i] < ys.min() - dx
            or py[i] > ys.max() + dx
        ):
            continue
        r0, c0 = row[i], col[i]
        box = aod[
            max(r0 - BOX_PIXELS, 0) : r0 + BOX_PIXELS + 1,
            max(c0 - BOX_PIXELS, 0) : c0 + BOX_PIXELS + 1,
        ]
        n = int(np.isfinite(box).sum())
        out_n[i] = n
        if n:
            out_mean[i] = float(np.nanmean(box))
    return pd.DataFrame({"point_id": points["point_id"].to_numpy(), "aod": out_mean, "n_px": out_n})


def day_path(study_name: str, d: date) -> Path:
    return interim_dir(f"{study_name}/goes_aod") / f"{d:%Y%m%d}.parquet"


def extract_day(
    d: date, points: pd.DataFrame, study_name: str, overwrite: bool = False
) -> Path | None:
    """Point AOD for the first scan of each hour in HOURS_UTC; one parquet per day."""
    import xarray as xr

    out = day_path(study_name, d)
    if out.exists() and not overwrite:
        return out
    sat = west_satellite(d)
    parts = []
    for hour in HOURS_UTC:
        # Use the first readable scan of the hour; a damaged file falls through to the next.
        for key in list_keys(sat, d, hour)[:3]:
            r = get(f"{BUCKET.format(sat=sat)}/{key}", timeout=180)
            try:
                data = r.content
            finally:
                r.close()
            try:
                # Read from memory: no temporary file for Windows to keep locked.
                with xr.open_dataset(io.BytesIO(data), engine="h5netcdf", decode_times=False) as ds:
                    ds = ds[["AOD", "DQF", "goes_imager_projection"]].load()
            except OSError:
                continue
            vals = point_values(ds, points)
            vals["hour_utc"] = hour
            vals["satellite"] = sat.removeprefix("noaa-")
            parts.append(vals)
            break
    if not parts:
        return None
    df = pd.concat(parts, ignore_index=True)
    df.insert(0, "date", pd.Timestamp(d))
    df.to_parquet(out, index=False)
    return out


def daily_features(days, study_name: str) -> pd.DataFrame:
    """Per issue day and point: morning mean AOD, its max over hours, and coverage."""
    rows = []
    for d in days:
        p = day_path(study_name, d)
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        g = df.groupby("point_id")
        rows.append(
            pd.DataFrame(
                {
                    "issue_date": d,
                    "point_id": g.size().index,
                    "goes_aod_mean": g["aod"].mean().to_numpy(),
                    "goes_aod_max": g["aod"].max().to_numpy(),
                    "goes_aod_hours": g["aod"].count().to_numpy(),
                }
            )
        )
    if not rows:
        return pd.DataFrame(
            columns=["issue_date", "point_id", "goes_aod_mean", "goes_aod_max", "goes_aod_hours"]
        )
    return pd.concat(rows, ignore_index=True)
