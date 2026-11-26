"""Temporary wildfire smoke monitors from the USDA Forest Service AirFire archive.

Fire crews and air agencies set up portable PM2.5 monitors (mostly E-BAMs) near
active fires. Their hourly readings are collected by two telemetry networks:
WRCC (Western Regional Climate Center) and AIRSIS. AirFire quality-controls both
and publishes yearly files on a public S3 bucket (free, no key):

    https://airfire-data-exports.s3.us-west-2.amazonaws.com/monitoring/v2/
        {wrcc,airsis}/{year}/data/{source}_PM2.5_{year}_{data,meta}.csv.gz

These monitors use IDs such as ``MMCA81013`` and are not in the AirNow hourly
files that the rest of Serein reads, so they are new sensors for the model.

Caveat: the yearly files are AirFire's quality-controlled copy. A forecast made in
real time would have seen the raw feed, which can contain readings AirFire later
removed. Readings are still used only up to the same cutoff as AirNow.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from serein.config import Region, raw_dir
from serein.http import get

BASE = "https://airfire-data-exports.s3.us-west-2.amazonaws.com/monitoring/v2"
SOURCES = ("wrcc", "airsis")
# Hourly PM2.5 outside this range is an instrument fault, not smoke (µg/m³).
VALID_RANGE = (0.0, 1500.0)


def _path(source: str, year: int, part: str):
    return raw_dir("airfire") / f"{source}_PM2.5_{year}_{part}.csv.gz"


def download_year(year: int, overwrite: bool = False) -> list:
    """Save the yearly data and metadata files of both networks. Returns the paths."""
    paths = []
    for source in SOURCES:
        for part in ("data", "meta"):
            p = _path(source, year, part)
            if overwrite or not p.exists():
                url = f"{BASE}/{source}/{year}/data/{source}_PM2.5_{year}_{part}.csv.gz"
                r = get(url, timeout=120)
                tmp = p.with_suffix(".part")
                tmp.write_bytes(r.content)
                tmp.replace(p)
            paths.append(p)
    return paths


def load_monitors(years: list[int], region: Region) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Monitors inside the region and their hourly readings.

    Returns ``(monitors, hourly)``. ``monitors`` has ``site_id, lat, lon, source``;
    ``hourly`` has ``site_id, time_utc, pm25`` (``time_utc`` is the start of the hour,
    as in the AirNow files).
    """
    mons, hours = [], []
    for year in sorted(set(years)):
        for source in SOURCES:
            meta_p, data_p = _path(source, year, "meta"), _path(source, year, "data")
            if not (meta_p.exists() and data_p.exists()):
                raise FileNotFoundError(
                    f"{data_p.name} missing. Run `serein download airfire --years {year}`."
                )
            meta = pd.read_csv(meta_p, usecols=["deviceDeploymentID", "latitude", "longitude"])
            meta = meta.dropna(subset=["latitude", "longitude"])
            meta = meta[region.contains(meta["latitude"], meta["longitude"])]
            data = pd.read_csv(data_p)
            keep = [c for c in meta["deviceDeploymentID"] if c in data.columns]
            if not keep:
                continue
            long = (
                data[["datetime", *keep]]
                .melt(id_vars="datetime", var_name="site_id", value_name="pm25")
                .dropna(subset=["pm25"])
            )
            hours.append(long)
            m = meta[meta["deviceDeploymentID"].isin(keep)].rename(
                columns={"deviceDeploymentID": "site_id", "latitude": "lat", "longitude": "lon"}
            )
            mons.append(m.assign(source=source))
    if not hours:
        return (
            pd.DataFrame(columns=["site_id", "lat", "lon", "source"]),
            pd.DataFrame(columns=["site_id", "time_utc", "pm25"]),
        )
    hourly = pd.concat(hours, ignore_index=True)
    hourly["time_utc"] = pd.to_datetime(hourly["datetime"], utc=True).dt.tz_localize(None)
    hourly["pm25"] = pd.to_numeric(hourly["pm25"], errors="coerce")
    lo, hi = VALID_RANGE
    hourly = hourly[hourly["pm25"].between(lo, hi)]
    hourly = hourly.groupby(["site_id", "time_utc"], as_index=False)["pm25"].mean()
    monitors = pd.concat(mons, ignore_index=True).drop_duplicates("site_id").reset_index(drop=True)
    monitors = monitors[monitors["site_id"].isin(hourly["site_id"].unique())]
    for c in ("lat", "lon"):
        monitors[c] = monitors[c].astype(float)
    if not np.isfinite(monitors[["lat", "lon"]].to_numpy()).all():
        raise ValueError("monitor coordinates must be finite")
    return monitors.reset_index(drop=True), hourly
