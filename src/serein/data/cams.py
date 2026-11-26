"""CAMS global PM2.5 forecasts (ECMWF, Copernicus Atmosphere Monitoring Service).

An independent forecast model from NOAA's, out to 4+ days. Free with a Copernicus
Atmosphere Data Store account (key in ~/.cdsapirc; the dataset licence must be accepted
on its download page). Grid 0.4 degrees; pm2p5 in kg/m3 (x1e9 = micrograms/m3).

We use the 00 UTC run of the issue day (available well before the 18:30 UTC issue time),
3-hourly lead times 0-96 h, for the study box.
"""

from __future__ import annotations

import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

from serein.config import raw_dir

DATASET = "cams-global-atmospheric-composition-forecasts"
LEADS = [str(h) for h in range(0, 97, 3)]
AREA = [49, -125, 32, -114]  # north, west, south, east


def month_path(year: int, month: int) -> Path:
    return raw_dir("cams") / f"cams_pm25_{year}{month:02d}.nc"


def download_month(year: int, month: int, overwrite: bool = False) -> Path:
    import calendar

    import cdsapi

    out = month_path(year, month)
    if out.exists() and not overwrite:
        return out
    last = calendar.monthrange(year, month)[1]
    req = {"date": [f"{year}-{month:02d}-01/{year}-{month:02d}-{last:02d}"], "type": ["forecast"],
           "data_format": "netcdf_zip", "variable": ["particulate_matter_2.5um"], "time": ["00:00"],
           "leadtime_hour": LEADS, "area": AREA}
    tmp = out.with_suffix(".zip")
    cdsapi.Client(quiet=True).retrieve(DATASET, req, str(tmp))
    with zipfile.ZipFile(tmp) as z:
        name = next(n for n in z.namelist() if n.endswith(".nc"))
        out.write_bytes(z.read(name))
    tmp.unlink()
    return out


def point_forecasts(days, points) -> pd.DataFrame:
    """The 00 UTC run of each issue day at each point (nearest 0.4 degree cell).

    Returns ``issue_date, point_id, valid_utc, value`` with value in µg/m³, the
    format ``serein.features.daily.model_daily`` expects. Days whose month file is
    missing, or that are not in it, are left out (the table marks them missing).
    """
    import xarray as xr

    lat = xr.DataArray(points["lat"].to_numpy(float), dims="p")
    lon = xr.DataArray(points["lon"].to_numpy(float), dims="p")
    ids = points["point_id"].to_numpy()
    by_month: dict[tuple[int, int], list] = {}
    for d in days:
        by_month.setdefault((d.year, d.month), []).append(d)
    parts = []
    for (year, month), month_days in sorted(by_month.items()):
        path = month_path(year, month)
        if not path.exists():
            continue
        with xr.open_dataset(path) as ds:
            runs = pd.to_datetime(ds["forecast_reference_time"].values)
            for d in month_days:
                run = pd.Timestamp(d.year, d.month, d.day)  # 00 UTC of the issue day
                if run not in runs:
                    continue
                field = ds["pm2p5"].sel(forecast_reference_time=run)
                vals = field.sel(latitude=lat, longitude=lon, method="nearest").values * 1e9
                steps = run + pd.to_timedelta(ds["forecast_period"].values)
                n_steps, n_pts = vals.shape
                parts.append(pd.DataFrame({
                    "issue_date": d,
                    "point_id": np.tile(ids, n_steps),
                    "valid_utc": np.repeat(steps, n_pts),
                    "value": vals.reshape(-1).astype(float),
                }))
    if not parts:
        return pd.DataFrame(columns=["issue_date", "point_id", "valid_utc", "value"])
    return pd.concat(parts, ignore_index=True)
