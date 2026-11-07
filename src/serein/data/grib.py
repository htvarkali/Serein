"""GRIB2 decoding + nearest-grid-point lookup, shared by HRRR and AQM."""

from __future__ import annotations

import hashlib
import threading
from dataclasses import dataclass
from datetime import datetime

import eccodes
import numpy as np
from scipy.spatial import cKDTree

from serein.config import interim_dir

# ecCodes is not guaranteed thread-safe; serialize decoding and index building.
_LOCK = threading.RLock()


def validate_point_coordinates(lat, lon):
    """Require nonempty geographic coordinates before forecast downloads."""
    lat = np.asarray(lat, dtype=float)
    lon = np.asarray(lon, dtype=float)
    if (lat.ndim != 1 or lon.shape != lat.shape or not lat.size
            or not np.isfinite(lat).all() or not np.isfinite(lon).all()
            or (np.abs(lat) > 90).any() or (np.abs(lon) > 180).any()):
        raise ValueError("Point coordinates must be nonempty, finite latitudes in [-90, 90] "
                         "and longitudes in [-180, 180]")


def validate_point_ids(ids):
    """Keep sampled forecast rows unambiguous for each location."""
    if (ids.isna().any() or ids.duplicated().any()
            or ids.astype(str).str.strip().eq("").any()):
        raise ValueError("Point identifiers must be unique, nonmissing, and nonblank")


def _unit_xyz(lat, lon):
    lat = np.radians(np.asarray(lat, dtype=float))
    lon = np.radians(np.asarray(lon, dtype=float))
    return np.stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)], -1)


@dataclass
class GribField:
    short_name: str
    level: str
    start_step: int
    end_step: int
    values: np.ndarray  # flat, NaN for missing
    units: str
    reference_time: datetime | None = None
    step_type: str = ""


def decode_messages(blob: bytes, with_grid: bool = False):
    """Decode every GRIB message in ``blob``.

    Returns (fields, (lat, lon) or None).
    """
    with _LOCK:
        return _decode(blob, with_grid)


def _decode(blob: bytes, with_grid: bool):
    fields, grid = [], None
    pos = 0
    while True:
        i = blob.find(b"GRIB", pos)
        if i < 0:
            break
        if len(blob) - i < 16:
            raise ValueError(f"Truncated GRIB header at byte {i}")
        if blob[i + 7] != 2:
            raise ValueError(f"Expected GRIB edition 2 at byte {i}")
        length = int.from_bytes(blob[i + 8:i + 16], "big")  # GRIB2 total length
        if length < 20 or length > len(blob) - i:
            raise ValueError(f"Invalid GRIB message length at byte {i}: {length}")
        msg = blob[i:i + length]
        if msg[-4:] != b"7777":
            raise ValueError(f"Missing GRIB end marker at byte {i}")
        pos = i + length
        h = eccodes.codes_new_from_message(msg)
        try:
            vals = eccodes.codes_get_values(h).astype(np.float32)
            missing = eccodes.codes_get_double(h, "missingValue")
            if eccodes.codes_get_long(h, "bitmapPresent"):
                vals[vals == missing] = np.nan
            vals[vals >= 9999.0] = np.nan  # AQM uses 9999 as fill
            if with_grid and grid is None:
                lat = eccodes.codes_get_array(h, "latitudes")
                lon = eccodes.codes_get_array(h, "longitudes")
                lon = np.where(lon > 180, lon - 360, lon)
                grid = (lat, lon)

            def s(key, h=h):
                try:
                    return eccodes.codes_get_string(h, key)
                except Exception:  # noqa: BLE001 - missing key just means blank
                    return ""

            try:
                reference_day, reference_clock = s("dataDate"), s("dataTime")
                reference = (datetime.strptime(reference_day + reference_clock.zfill(4), "%Y%m%d%H%M")
                             if reference_day and reference_clock else None)
            except ValueError:
                reference = None
            fields.append(GribField(
                short_name=s("shortName"), level=s("typeOfLevel") + ":" + s("level"),
                start_step=int(eccodes.codes_get_long(h, "startStep")),
                end_step=int(eccodes.codes_get_long(h, "endStep")),
                values=vals, units=s("units"),
                reference_time=reference, step_type=s("stepType"),
            ))
        finally:
            eccodes.codes_release(h)
    return fields, grid


class PointIndex:
    """Nearest grid cell for each point; cached on disk per (grid, points)."""

    def __init__(self, grid_name: str, lat_grid, lon_grid, pt_lat, pt_lon,
                 max_km: float = 10.0):
        if not np.isfinite(max_km) or max_km < 0:
            raise ValueError("max_km must be finite and nonnegative")
        validate_point_coordinates(lat_grid, lon_grid)
        validate_point_coordinates(pt_lat, pt_lon)
        self._grid_size = len(lat_grid)
        points_key = hashlib.sha1(
            np.ascontiguousarray(np.c_[pt_lat, pt_lon]).astype(np.float64).tobytes()
        ).hexdigest()[:12]
        grid_key = hashlib.sha1()
        for coords in (lat_grid, lon_grid):
            grid_key.update(np.ascontiguousarray(coords, dtype=np.float64).tobytes())
        cache = interim_dir("grid_index") / (
            f"{grid_name}_{len(lat_grid)}_{grid_key.hexdigest()[:12]}_{points_key}.npz"
        )
        with _LOCK:
            self._load_or_build(cache, lat_grid, lon_grid, pt_lat, pt_lon)
        # Disk caches store chord lengths scaled by Earth's radius.
        self.dist_km = 2 * 6371.0 * np.arcsin(np.clip(self.dist_km / (2 * 6371.0), 0, 1))
        self.valid = self.dist_km <= max_km

    def _load_or_build(self, cache, lat_grid, lon_grid, pt_lat, pt_lon):
        if cache.exists():
            with np.load(cache) as z:
                self.idx, self.dist_km = z["idx"], z["dist_km"]
            if (self.idx.shape != (len(pt_lat),)
                    or self.dist_km.shape != (len(pt_lat),)
                    or self.idx.dtype.kind not in "iu"
                    or (self.idx < 0).any() or (self.idx >= len(lat_grid)).any()
                    or self.dist_km.dtype.kind not in "fiu"
                    or not np.isfinite(self.dist_km).all()
                    or (self.dist_km < 0).any() or (self.dist_km > 2 * 6371.0).any()):
                raise ValueError(f"Invalid grid index cache: {cache}")
        else:
            tree = cKDTree(_unit_xyz(lat_grid, lon_grid))
            d, idx = tree.query(_unit_xyz(pt_lat, pt_lon))
            self.idx, self.dist_km = idx.astype(np.int64), d * 6371.0
            np.savez(cache, idx=self.idx, dist_km=self.dist_km)

    def sample(self, values: np.ndarray) -> np.ndarray:
        if values.shape != (self._grid_size,):
            raise ValueError("Forecast field shape must match the indexed grid")
        out = values[self.idx].astype(np.float32)
        out[~self.valid] = np.nan
        return out
