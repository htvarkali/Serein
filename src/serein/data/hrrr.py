"""NOAA HRRR-Smoke and HRRR weather, sampled at points.

We only download the bytes we need. Every HRRR GRIB2 file on AWS has a
``.idx`` sidecar that lists where each field starts, so we can request just
the near-surface smoke field (``MASSDEN:8 m above ground``, ~0.8 MB) instead of
the whole 140 MB file. Example .idx line::

    76:50783879:d=2024090100:MASSDEN:8 m above ground:6 hour fcst:

Unit gotcha: MASSDEN was labeled µg/m³ before 2021-12-21 and kg/m³ after. We
decide by magnitude: a CONUS smoke field whose max is < 1 must be kg/m³.
"""

from __future__ import annotations

import hashlib
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta
from numbers import Integral

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
from serein.http import get, get_range

BUCKET = "https://noaa-hrrr-bdp-pds.s3.amazonaws.com"
SMOKE = "MASSDEN:8 m above ground"
DEFAULT_MET = ["UGRD:10 m above ground", "VGRD:10 m above ground", "HPBL:surface",
               "TMP:2 m above ground", "RH:2 m above ground",
               "COLMD:entire atmosphere (considered as a single layer)"]
SHORT = {"MASSDEN:8 m above ground": "smoke", "UGRD:10 m above ground": "u10",
         "VGRD:10 m above ground": "v10", "HPBL:surface": "pbl",
         "TMP:2 m above ground": "t2m", "RH:2 m above ground": "rh2m",
         "COLMD:entire atmosphere (considered as a single layer)": "colmd"}
COLMD = "COLMD:entire atmosphere (considered as a single layer)"
TEMPERATURE = "TMP:2 m above ground"


def temperature_to_c(values: np.ndarray, units: str) -> np.ndarray:
    """Convert the explicitly identified GRIB temperature unit, never infer it."""
    if units not in ("K", "degC", "C"):
        raise ValueError(f"Unsupported HRRR temperature units: {units!r}")
    values = np.asarray(values, dtype=float)
    celsius = values - 273.15 if units == "K" else values
    return np.where(np.isfinite(celsius) & (celsius >= -273.15), celsius, np.nan)


def file_url(d: date, cycle: int, fhr: int) -> str:
    return f"{BUCKET}/hrrr.{d:%Y%m%d}/conus/hrrr.t{cycle:02d}z.wrfsfcf{fhr:02d}.grib2"


def parse_idx(text: str) -> list[tuple[int, int | None, str]]:
    """Return [(start, end_inclusive_or_None, 'VAR:level'), ...]."""
    rows = []
    lines = [ln for ln in text.splitlines() if ln.strip()]
    for i, ln in enumerate(lines):
        parts = ln.split(":")
        start = int(parts[1])
        end = int(lines[i + 1].split(":")[1]) - 1 if i + 1 < len(lines) else None
        rows.append((start, end, f"{parts[3]}:{parts[4]}"))
    return rows


def colmd_to_mgm2(values: np.ndarray) -> np.ndarray:
    """Column smoke: kg/m2 -> mg/m2 (same magnitude rule as MASSDEN)."""
    v = values.astype(np.float32)
    finite = v[np.isfinite(v)]
    if finite.size and np.nanmax(finite) < 1.0:
        v = v * 1e6
    return v


def smoke_to_ugm3(values: np.ndarray) -> np.ndarray:
    v = values.astype(np.float32)
    finite = v[np.isfinite(v)]
    if finite.size and np.nanmax(finite) < 1.0:
        v = v * 1e9  # kg/m³ -> µg/m³
    return v


def _fetch_fields(d: date, cycle: int, fhr: int, wanted: list[str]):
    url = file_url(d, cycle, fhr)
    r = get(url + ".idx", allow_404=True)
    if r is None:
        return None
    try:
        entries = parse_idx(r.text)
    finally:
        r.close()
    blobs = []
    for start, end, name in entries:
        if name in wanted:
            blobs.append((name, get_range(url, start, end)))
    return blobs


def extract_cycle(d: date, points: pd.DataFrame, cycle: int = 12, max_fhr: int = 48,
                  smoke_every: int = 1, met_every: int = 3,
                  met_vars: list[str] | None = None, overwrite: bool = False,
                  workers: int = 12, store: str = "west_us", *,
                  _temperature_only: bool = False) -> pd.DataFrame | None:
    """Sample HRRR smoke + weather at points for one cycle. Cached as parquet.

    Output columns: point_id, valid_utc, fhr, var, value.
    Use met_vars=None for default weather fields or [] for smoke only.
    Caches without matching request metadata are rebuilt. A failed rebuild raises
    if an old extraction exists, preserving it without silently reusing it.
    Partial extractions remain loadable but are retried on the next extraction.
    Missing samples within the grid are incomplete; points outside it are allowed.
    """
    validate_cycle_hour(cycle)
    validate_point_coordinates(points["lat"], points["lon"])
    validate_point_ids(points["point_id"])
    for name, value in (("max_fhr", max_fhr), ("smoke_every", smoke_every),
                        ("met_every", met_every), ("workers", workers)):
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise TypeError(f"{name} must be an integer")
    if max_fhr < 0:
        raise ValueError("max_fhr must be nonnegative")
    if smoke_every <= 0:
        raise ValueError("smoke_every must be positive")
    if met_every <= 0:
        raise ValueError("met_every must be positive")
    if workers <= 0:
        raise ValueError("workers must be positive")
    met_vars = DEFAULT_MET if met_vars is None else met_vars
    if _temperature_only:
        met_vars, met_every = [TEMPERATURE], 1
    point_hash = hashlib.sha256(pd.util.hash_pandas_object(
        points[["point_id", "lat", "lon"]], index=False).to_numpy().tobytes()).hexdigest()
    request = {"version": 2, "points": point_hash, "max_fhr": max_fhr, "smoke_every": smoke_every,
               "met_every": met_every, "met_vars": list(met_vars)}
    t0 = datetime(d.year, d.month, d.day, cycle)
    if _temperature_only:
        request["temperature_units"] = "degC"
    # Cached per study ("store"): different studies sample different points.
    folder = "hrrr_temperature" if _temperature_only else "hrrr"
    out_path = interim_dir(f"{store}/{folder}") / f"{d:%Y%m%d}_{cycle:02d}z.parquet"
    if out_path.exists() and not overwrite:
        cached = pd.read_parquet(out_path)
        if (cached.attrs.get("hrrr_request") == request
                and cached.attrs.get("hrrr_complete") is True
                and (not _temperature_only or cached.attrs.get("context_cycle_utc") == t0.isoformat())):
            return cached

    jobs = []
    for fhr in range(max_fhr + 1):
        wanted = []
        if not _temperature_only and fhr % smoke_every == 0:
            wanted.append(SMOKE)
        if fhr % met_every == 0:
            wanted += met_vars
        if wanted:
            jobs.append((fhr, wanted))

    with ThreadPoolExecutor(workers) as ex:
        results = list(ex.map(lambda j: (j[0], _fetch_fields(d, cycle, j[0], j[1])), jobs))

    if all(b is None for _, b in results):
        if out_path.exists():
            raise RuntimeError(f"Cannot rebuild cached extraction {out_path}: no HRRR data")
        return None

    index = None
    rows = []
    decoded = set()
    samples_complete = True
    t0 = datetime(d.year, d.month, d.day, cycle)
    for fhr, blobs in results:
        if not blobs:
            continue
        for name, blob in blobs:
            fields, grid = decode_messages(blob, with_grid=index is None)
            if not fields:
                continue
            decoded.add((fhr, name))
            if index is None:
                index = PointIndex("hrrr", grid[0], grid[1],
                                   points["lat"].to_numpy(), points["lon"].to_numpy(),
                                   max_km=5.0)
            for f in fields:
                if _temperature_only:
                    if (f.short_name != "2t" or f.step_type != "instant"
                            or f.reference_time != t0):
                        raise ValueError("HRRR temperature identity or initialization does not match request")
                    if f.start_step != fhr or f.end_step != fhr:
                        raise ValueError("HRRR temperature must be instantaneous at its forecast hour")
                    if f.level != "heightAboveGround:2":
                        raise ValueError("HRRR temperature must be at 2 m above ground")
                    vals = temperature_to_c(f.values, f.units)
                elif name == SMOKE:
                    vals = smoke_to_ugm3(f.values)
                elif name == COLMD:
                    vals = colmd_to_mgm2(f.values)
                else:
                    vals = f.values
                sampled = index.sample(vals)
                samples_complete &= bool(np.isfinite(sampled[index.valid]).all())
                rows.append(pd.DataFrame({
                    "point_id": points["point_id"].to_numpy(),
                    "valid_utc": t0 + timedelta(hours=fhr),
                    "fhr": np.int16(fhr),
                    "var": SHORT.get(name, name),
                    "value": sampled,
                    **({"lat": points["lat"].to_numpy(), "lon": points["lon"].to_numpy()}
                       if _temperature_only else {}),
                }))
    if not rows:
        if out_path.exists():
            raise RuntimeError(f"Cannot rebuild cached extraction {out_path}: no decoded fields")
        return None
    df = pd.concat(rows, ignore_index=True)
    df["var"] = df["var"].astype("category")
    df.attrs["hrrr_request"] = request
    df.attrs["hrrr_complete"] = samples_complete and all(
        (fhr, name) in decoded for fhr, wanted in jobs for name in wanted)
    if _temperature_only:
        df.attrs["temperature_units"] = "degC"
        df.attrs["context_cycle_utc"] = t0.isoformat()
    df.to_parquet(out_path, index=False)
    return df


def extract_temperature_cycle(d: date, points: pd.DataFrame, cycle: int = 12,
                              max_fhr: int = 48, overwrite: bool = False,
                              workers: int = 12, store: str = "west_us") -> pd.DataFrame | None:
    """Cache hourly instantaneous 2 m temperature in Celsius, separately from smoke features.

    A daily maximum of these samples is a maximum hourly forecast, not a true
    interval maximum (TMAX). HRRR's shorter horizon leaves later days unknown.
    """
    if max_fhr > 48:
        raise ValueError("HRRR temperature context cannot extend beyond 48 hours")
    return extract_cycle(d, points, cycle=cycle, max_fhr=max_fhr, overwrite=overwrite,
                         workers=workers, store=store, _temperature_only=True)


def load_cycles(days: list[date], cycle: int = 12, store: str = "west_us", *,
                _temperature_only: bool = False) -> pd.DataFrame:
    validate_cycle_hour(cycle)
    parts = []
    for d in days:
        folder = "hrrr_temperature" if _temperature_only else "hrrr"
        p = interim_dir(f"{store}/{folder}") / f"{d:%Y%m%d}_{cycle:02d}z.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            if _temperature_only and df.attrs.get("temperature_units") != "degC":
                raise ValueError(f"Temperature cache lacks verified Celsius units: {p}")
            if (_temperature_only and df.attrs.get("context_cycle_utc")
                    != datetime(d.year, d.month, d.day, cycle).isoformat()):
                raise ValueError(f"Temperature cache initialization does not match request: {p}")
            df["issue_date"] = d
            parts.append(df)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def load_temperature_cycles(days: list[date], cycle: int = 12,
                            store: str = "west_us") -> pd.DataFrame:
    return load_cycles(days, cycle=cycle, store=store, _temperature_only=True)
