"""NOAA Air Quality Model (NAQFC / AQM): NOAA's official 72-hour PM2.5 forecast.

Public on AWS (bucket ``noaa-nws-naqfc-pds``). Versions by date:
  AQMv5 (CMAQ) ... 2021-07-19, AQMv6 2021-07-20 ... 2024-05-13, AQMv7 2024-05-14 ...
Each cycle (06z, 12z) has an hourly file with 72 one-hour averages:
  aqm.t12z.ave_1hr_pm25_bc.YYYYMMDD.227.grib2   (bias-corrected, NOAA's best)
  aqm.t12z.ave_1hr_pm25.YYYYMMDD.227.grib2      (raw model)

We do NOT use the ready-made 24 h average files: their averaging window is not
the local calendar day, so they can't be compared fairly with observations.
A message with steps (s, s+1) is the mean over [cycle+s, cycle+s+1) UTC.
"""

from __future__ import annotations

import hashlib
from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd

from serein.config import interim_dir
from serein.data.availability import validate_cycle_hour
from serein.data.grib import (
    PointIndex,
    decode_messages,
    validate_point_coordinates,
    validate_point_ids,
)
from serein.http import get

BUCKET = "https://noaa-nws-naqfc-pds.s3.amazonaws.com"
VERSIONS = [  # (first day, prefix)
    (date(2024, 5, 14), "AQMv7"),
    (date(2021, 7, 20), "AQMv6"),
    (date(2000, 1, 1), "AQMv5"),
]


def candidate_urls(d: date, cycle: int, bias_corrected: bool,
                   pollutant: str = "pm25") -> list[str]:
    if pollutant not in ("pm25", "o3"):
        raise ValueError("AQM pollutant must be pm25 or o3")
    suffix = "_bc" if bias_corrected else ""
    name = f"aqm.t{cycle:02d}z.ave_1hr_{pollutant}{suffix}.{d:%Y%m%d}.227.grib2"
    # Try the expected version first, then the others (transition dates overlap).
    ordered = [p for start, p in VERSIONS if d >= start][:1]
    ordered += [p for _, p in VERSIONS if p not in ordered]
    return [f"{BUCKET}/{p}/CS/{d:%Y%m%d}/{cycle:02d}/{name}" for p in ordered]


def ozone_to_ppb(values: np.ndarray, units: str) -> np.ndarray:
    """Use GRIB units, never concentration magnitude, to convert ozone mixing ratios."""
    factors = {"ppb": 1.0, "ppbV": 1.0, "ppm": 1000.0, "ppmV": 1000.0,
               "mol mol**-1": 1e9, "mol mol-1": 1e9, "mol/mol": 1e9}
    if units not in factors:
        raise ValueError(f"Unsupported AQM ozone units: {units!r}")
    result = np.asarray(values, dtype=float) * factors[units]
    return np.where(np.isfinite(result) & (result >= 0), result, np.nan)


def extract_cycle(d: date, points: pd.DataFrame, cycle: int = 12,
                  bias_corrected: bool = True, overwrite: bool = False,
                  store: str = "west_us", pollutant: str = "pm25") -> pd.DataFrame | None:
    """Sample hourly PM2.5 (µg/m³) or ozone (ppb), in separate caches.

    Output: point_id, valid_utc (interval start), step, value.

    Caches without matching points or all expected hours are rebuilt. Partial
    results remain loadable. Missing in-grid samples also trigger a rebuild;
    points outside the grid are allowed. A failed rebuild raises if an old extraction exists,
    preserving it without silently reusing it.
    """
    validate_cycle_hour(cycle)
    if pollutant not in ("pm25", "o3"):
        raise ValueError("AQM pollutant must be pm25 or o3")
    validate_point_coordinates(points["lat"], points["lon"])
    validate_point_ids(points["point_id"])
    point_hash = hashlib.sha256(pd.util.hash_pandas_object(
        points[["point_id", "lat", "lon"]], index=False).to_numpy().tobytes()).hexdigest()
    tag = "bc" if bias_corrected else "raw"
    t0 = datetime(d.year, d.month, d.day, cycle)
    hours = 48 if d < date(2021, 7, 20) else 72
    folder = f"aqm_{tag}" if pollutant == "pm25" else f"aqm_o3_{tag}"
    out_path = interim_dir(f"{store}/{folder}") / f"{d:%Y%m%d}_{cycle:02d}z.parquet"
    if out_path.exists() and not overwrite:
        cached = pd.read_parquet(out_path)
        if (cached.attrs.get("aqm_points") == point_hash
                and cached.attrs.get("aqm_samples_complete") is True
                and (pollutant == "pm25" or (cached.attrs.get("ozone_units") == "ppb"
                     and cached.attrs.get("context_cycle_utc") == t0.isoformat()))
                and set(range(hours)).issubset(cached["step"])):
            return cached
    blob = None
    for url in candidate_urls(d, cycle, bias_corrected, pollutant):
        r = get(url, allow_404=True, timeout=300)
        if r is not None:
            try:
                blob = r.content
            finally:
                r.close()
            break
    if blob is None:
        if out_path.exists():
            raise RuntimeError(f"Cannot rebuild cached extraction {out_path}: no AQM data")
        return None
    # AQM version changes can move cells without changing the grid dimensions.
    fields, grid = decode_messages(blob, with_grid=True)
    fields = [f for f in fields if f.end_step - f.start_step == 1]
    if not fields:
        if out_path.exists():
            raise RuntimeError(f"Cannot rebuild cached extraction {out_path}: no hourly fields")
        return None
    index = PointIndex(f"aqm{len(grid[0])}", grid[0], grid[1],
                       points["lat"].to_numpy(), points["lon"].to_numpy(), max_km=10.0)
    t0 = datetime(d.year, d.month, d.day, cycle)
    rows = []
    samples_complete = True
    for f in fields:
        if pollutant == "o3" and (f.short_name != "ozcon" or f.level != "sigma:1"
                                   or f.step_type != "avg" or f.reference_time != t0
                                   or not 0 <= f.start_step < hours):
            raise ValueError("AQM ozone field identity or initialization does not match the request")
        values = ozone_to_ppb(f.values, f.units) if pollutant == "o3" else f.values
        sampled = index.sample(values)
        samples_complete &= bool(np.isfinite(sampled[index.valid]).all())
        rows.append(pd.DataFrame({
            "point_id": points["point_id"].to_numpy(),
            "valid_utc": t0 + timedelta(hours=f.start_step),
            "step": np.int16(f.start_step),
            "value": sampled,
            **({"lat": points["lat"].to_numpy(), "lon": points["lon"].to_numpy()}
               if pollutant == "o3" else {}),
        }))
    df = pd.concat(rows, ignore_index=True)
    df.attrs["aqm_points"] = point_hash
    df.attrs["aqm_samples_complete"] = samples_complete
    if pollutant == "o3":
        df.attrs["ozone_units"] = "ppb"
        df.attrs["context_cycle_utc"] = t0.isoformat()
        df.attrs["source_url"] = url
    df.to_parquet(out_path, index=False)
    return df


def load_cycles(days: list[date], cycle: int = 12, bias_corrected: bool = True,
                store: str = "west_us", pollutant: str = "pm25") -> pd.DataFrame:
    validate_cycle_hour(cycle)
    if pollutant not in ("pm25", "o3"):
        raise ValueError("AQM pollutant must be pm25 or o3")
    tag = "bc" if bias_corrected else "raw"
    folder = f"aqm_{tag}" if pollutant == "pm25" else f"aqm_o3_{tag}"
    parts = []
    for d in days:
        p = interim_dir(f"{store}/{folder}") / f"{d:%Y%m%d}_{cycle:02d}z.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            if pollutant == "o3" and df.attrs.get("ozone_units") != "ppb":
                raise ValueError(f"Ozone cache lacks verified ppb units: {p}")
            if (pollutant == "o3" and df.attrs.get("context_cycle_utc")
                    != datetime(d.year, d.month, d.day, cycle).isoformat()):
                raise ValueError(f"Ozone cache initialization does not match request: {p}")
            df["issue_date"] = d
            parts.append(df)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()
