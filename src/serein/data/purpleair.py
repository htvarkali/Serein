"""PurpleAir low-cost sensors: client, cost estimator, QC, and EPA correction.

API docs: https://api.purpleair.com/  (key in .env as PURPLEAIR_API_KEY=...)

PurpleAir charges "points" per call: a small per-call base plus a per-row cost for
each field. ALWAYS run ``estimate_history_points`` and get the team's OK before a
big download. Real prices live on the PurpleAir Developer Dashboard (Billing ->
Pricing); the defaults below are placeholders to update from that page.
"""

from __future__ import annotations

import math
import os
import time
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from numbers import Integral, Real

import numpy as np
import pandas as pd

from serein.config import Region, load_env, raw_dir
from serein.http import get

API = "https://api.purpleair.com/v1"
HISTORY_FIELDS = ["pm2.5_cf_1_a", "pm2.5_cf_1_b", "humidity"]


def _headers() -> dict:
    load_env()
    k = os.environ.get("PURPLEAIR_API_KEY")
    if not k:
        raise RuntimeError("PURPLEAIR_API_KEY is not set (put it in .env)")
    return {"X-API-Key": k}


# --------------------------------------------------------------------------- cost
def _validate_history_fields(fields: list[str]) -> None:
    if not isinstance(fields, list) or not fields or not all(
        isinstance(field, str) and field and field == field.strip() and "," not in field
        for field in fields
    ):
        raise ValueError("fields must be a nonempty list of nonblank, comma-free names")
    if len(set(fields)) != len(fields):
        raise ValueError("fields must be unique")
    if set(fields) & {"time_utc", "sensor_index"}:
        raise ValueError("fields contain reserved history metadata names: time_utc, sensor_index")


@dataclass
class PointPrices:
    """UPDATE these from the Developer Dashboard before trusting the estimate."""
    base_per_call: float = 2.0
    per_field_row: float = 1.0
    max_days_per_call_hourly: int = 14  # history call span limit for 60-min averages


def estimate_history_points(n_sensors: int, days: int, average_minutes: int = 60,
                            fields: list[str] = HISTORY_FIELDS,
                            prices: PointPrices | None = None) -> dict:
    """Estimate points, rounding fractional totals up for budgeting.

    Counts must be integers; zero sensors or days produce a zero-cost estimate.
    """
    _validate_history_fields(fields)
    prices = prices or PointPrices()
    for name, value, minimum in (
        ("n_sensors", n_sensors, 0), ("days", days, 0),
        ("average_minutes", average_minutes, 1),
        ("max_days_per_call_hourly", prices.max_days_per_call_hourly, 1),
    ):
        if isinstance(value, bool) or not isinstance(value, Integral) or value < minimum:
            raise ValueError(f"{name} must be an integer >= {minimum}")
    for name in ("base_per_call", "per_field_row"):
        value = getattr(prices, name)
        if not math.isfinite(value) or value < 0:
            raise ValueError(f"{name} must be finite and nonnegative")
    rows_per_sensor = days * 24 * 60 / average_minutes
    calls = n_sensors * int(np.ceil(days / prices.max_days_per_call_hourly))
    points = calls * prices.base_per_call + n_sensors * rows_per_sensor * len(fields) * prices.per_field_row
    return {"sensors": n_sensors, "days": days, "calls": calls,
            "rows": int(n_sensors * rows_per_sensor), "points": math.ceil(points)}


# ------------------------------------------------------------------------ client
def list_outdoor_sensors(region: Region) -> pd.DataFrame:
    params = {
        "fields": "name,latitude,longitude,location_type,date_created,last_seen",
        "location_type": 0,  # outdoor only
        "nwlng": region.lon_min, "nwlat": region.lat_max,
        "selat": region.lat_min, "selng": region.lon_max,
    }
    r = get(f"{API}/sensors", headers=_headers(), params=params)
    try:
        js = r.json()
    finally:
        r.close()
    df = pd.DataFrame(js["data"], columns=js["fields"])
    df = df.rename(columns={"latitude": "lat", "longitude": "lon"})
    df.to_parquet(raw_dir("purpleair") / "sensors.parquet", index=False)
    return df


def download_history(sensor_index: int, start: datetime, end: datetime,
                     average_minutes: int = 60, fields: list[str] = HISTORY_FIELDS,
                     max_days: int = 14, pause_s: float = 1.0) -> pd.DataFrame:
    """Download history for a UTC range; naive datetimes are interpreted as UTC.

    Cache entries include the exact range, averaging interval and ordered fields.
    Legacy date-only caches are ignored because their request settings are unknown.
    Overlapping chunk timestamps keep the later response and are sorted in UTC.
    Range boundaries must use whole seconds to avoid API timestamp truncation.
    """
    if (isinstance(sensor_index, bool) or not isinstance(sensor_index, Integral)
            or sensor_index <= 0):
        raise ValueError("sensor_index must be a positive integer")
    sensor_index = int(sensor_index)
    _validate_history_fields(fields)
    for name, value in (("max_days", max_days), ("average_minutes", average_minutes)):
        if isinstance(value, bool) or not isinstance(value, Integral) or value <= 0:
            raise ValueError(f"{name} must be a positive integer")
    if not math.isfinite(pause_s) or pause_s < 0:
        raise ValueError("pause_s must be finite and nonnegative")
    max_days, average_minutes = int(max_days), int(average_minutes)
    start = start.replace(tzinfo=UTC) if start.tzinfo is None else start.astimezone(UTC)
    end = end.replace(tzinfo=UTC) if end.tzinfo is None else end.astimezone(UTC)
    if start.microsecond or end.microsecond:
        raise ValueError("start and end must use whole seconds")
    if start >= end:
        raise ValueError("start must be before end")
    request_key = f"{start.isoformat()}|{end.isoformat()}|{average_minutes}|{','.join(fields)}"
    digest = sha256(request_key.encode()).hexdigest()
    path = raw_dir("purpleair") / "history" / f"{sensor_index}_{digest}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        cached = pd.read_parquet(path)
        required = {"time_stamp", "time_utc", "sensor_index", *fields}
        missing = required - set(cached.columns)
        if missing:
            raise ValueError(f"history cache missing columns: {sorted(missing)}")
        if not all(
            isinstance(sensor, Integral) and not isinstance(sensor, (bool, np.bool_))
            and sensor == sensor_index
            for sensor in cached["sensor_index"]
        ):
            raise ValueError("history cache sensor_index must match the requested sensor")
        if not all(
            isinstance(stamp, Real) and not isinstance(stamp, (bool, np.bool_))
            and math.isfinite(stamp) and stamp == int(stamp)
            and start.timestamp() <= stamp <= end.timestamp()
            for stamp in cached["time_stamp"]
        ):
            raise ValueError("history cache time_stamp must contain whole seconds within the request")
        if (not cached["time_stamp"].is_unique
                or not cached["time_stamp"].is_monotonic_increasing):
            raise ValueError("history cache time_stamp must be unique and sorted")
        expected = pd.to_datetime(cached["time_stamp"], unit="s", utc=True)
        actual = pd.to_datetime(cached["time_utc"], utc=True, errors="coerce", format="mixed")
        if not (actual == expected).all():
            raise ValueError("history cache time_utc must match time_stamp")
        return cached
    parts, t = [], start
    while t < end:
        t1 = min(t + timedelta(days=max_days), end)
        params = {
            "start_timestamp": int(t.timestamp()),
            "end_timestamp": int(t1.timestamp()),
            "average": average_minutes, "fields": ",".join(fields),
        }
        r = get(f"{API}/sensors/{sensor_index}/history", headers=_headers(), params=params)
        try:
            js = r.json()
        finally:
            r.close()
        if not isinstance(js, dict) or not isinstance(js.get("data"), list):
            raise ValueError("history response data must be a list")  # noqa: TRY004
        response_fields = js.get("fields")
        if not isinstance(response_fields, list) or not all(
            isinstance(field, str) and field.strip() for field in response_fields
        ):
            raise ValueError("history response fields must be a list of nonblank names")
        if len(set(response_fields)) != len(response_fields):
            raise ValueError("history response fields must be unique")
        if set(response_fields) & {"time_utc", "sensor_index"}:
            raise ValueError("history response fields contain reserved metadata names")
        if "time_stamp" not in response_fields:
            raise ValueError("history response must include time_stamp")
        if js["data"]:
            if not all(
                isinstance(row, list) and len(row) == len(js["fields"])
                for row in js["data"]
            ):
                raise ValueError("history response rows must match the response fields")
            part = pd.DataFrame(js["data"], columns=js["fields"])
            if not all(
                isinstance(stamp, Real) and not isinstance(stamp, (bool, np.bool_))
                and math.isfinite(stamp) and stamp == int(stamp)
                for stamp in part["time_stamp"]
            ):
                raise ValueError("history time_stamp must contain finite whole-second timestamps")
            if not part["time_stamp"].between(
                params["start_timestamp"], params["end_timestamp"]
            ).all():
                raise ValueError("history time_stamp must be within the requested chunk")
        missing = set(fields) - set(response_fields)
        if missing:
            raise ValueError(f"history response missing requested fields: {sorted(missing)}")
        if js["data"]:
            parts.append(part)
        t = t1
        time.sleep(pause_s)
    if not parts:
        empty = pd.DataFrame({field: pd.Series(dtype=float)
                              for field in dict.fromkeys(["time_stamp", *fields])})
        empty["time_utc"] = pd.Series(dtype="datetime64[ns]")
        empty["sensor_index"] = pd.Series(dtype="int64")
        return empty
    df = (pd.concat(parts, ignore_index=True)
          .drop_duplicates("time_stamp", keep="last")
          .sort_values("time_stamp").reset_index(drop=True))
    df["time_utc"] = pd.to_datetime(df["time_stamp"], unit="s")
    df["sensor_index"] = sensor_index
    df.to_parquet(path, index=False)
    return df


# --------------------------------------------------------------------- QC + fix
def qc_ab(a, b, abs_tol: float = 5.0, rel_tol: float = 0.7):
    """Keep finite, nonnegative channels that agree (within 5 µg/m³ OR 70%).

    Returns (mean of A and B, keep mask). Mirrors the A/B agreement check used
    by EPA for the AirNow Fire and Smoke Map.
    """
    a = np.asarray(a, dtype=float)
    b = np.asarray(b, dtype=float)
    mean = (a + b) / 2
    diff = np.abs(a - b)
    rel = np.where(mean > 0, diff / np.maximum(mean, 1e-9), 0)
    keep = (np.isfinite(a) & np.isfinite(b) & (a >= 0) & (b >= 0)
            & ((diff <= abs_tol) | (rel <= rel_tol)))
    return mean, keep


def epa_correction(pa_cf1, rh):
    """EPA U.S.-wide PurpleAir correction with the extension for heavy smoke.

    Barkjohn et al. (2021, AMT 14:4617) for typical levels, extended for wildfire
    smoke by Barkjohn et al. (2022, Sensors 22:9669). Input: mean cf_1 PM2.5 of
    channels A and B (µg/m³) and the sensor's relative humidity (%).
    Inputs follow NumPy broadcasting rules, including scalar humidity.
    TODO(A-12): coefficients checked 2026-11-27 (docs/PURPLEAIR_CORRECTION_CHECK.md);
    the sources apply this extended correction to cf_atm, not cf_1. Decide before A-14.
    """
    x, rh = np.broadcast_arrays(np.asarray(pa_cf1, dtype=float), np.asarray(rh, dtype=float))
    out = np.full(x.shape, np.nan)

    m = x < 30
    out[m] = 0.524 * x[m] - 0.0862 * rh[m] + 5.75

    m = (x >= 30) & (x < 50)
    w = x[m] / 20 - 3 / 2
    out[m] = (0.786 * w + 0.524 * (1 - w)) * x[m] - 0.0862 * rh[m] + 5.75

    m = (x >= 50) & (x < 210)
    out[m] = 0.786 * x[m] - 0.0862 * rh[m] + 5.75

    m = (x >= 210) & (x < 260)
    w = x[m] / 50 - 21 / 5
    out[m] = ((0.69 * w + 0.786 * (1 - w)) * x[m] - 0.0862 * rh[m] * (1 - w)
              + 2.966 * w + 5.75 * (1 - w) + 8.84e-4 * x[m] ** 2 * w)

    m = x >= 260
    out[m] = 2.966 + 0.69 * x[m] + 8.84e-4 * x[m] ** 2
    return np.clip(out, 0, None)


def clean_history(df: pd.DataFrame) -> pd.DataFrame:
    """A/B QC + finite EPA corrections -> time_utc, sensor_index, pm25."""
    required = {"sensor_index", "time_utc", "pm2.5_cf_1_a", "pm2.5_cf_1_b", "humidity"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"history missing required columns: {sorted(missing)}")
    duplicates = required & set(df.columns[df.columns.duplicated()])
    if duplicates:
        raise ValueError(f"history duplicate required columns: {sorted(duplicates)}")
    if df["sensor_index"].isna().any():
        raise ValueError("history sensor_index must not contain missing identifiers")
    if any(isinstance(sensor, bool) or not isinstance(sensor, Integral) or sensor <= 0
           for sensor in df["sensor_index"]):
        raise ValueError("history sensor_index must contain positive integers")
    if any(isinstance(stamp, Real) for stamp in df["time_utc"]):
        raise ValueError("history time_utc must contain datetimes, not numeric timestamps")
    timestamps = pd.to_datetime(df["time_utc"], utc=True, errors="coerce", format="mixed")
    if timestamps.isna().any():
        raise ValueError("history time_utc must contain valid observation timestamps")
    keys = pd.DataFrame({"sensor_index": df["sensor_index"], "time_utc": timestamps})
    if keys.duplicated().any():
        raise ValueError("history contains duplicate sensor/timestamp pairs")
    measurements = []
    for column in ("pm2.5_cf_1_a", "pm2.5_cf_1_b", "humidity"):
        if any(isinstance(value, (bool, np.bool_, complex, np.complexfloating))
               for value in df[column]):
            raise ValueError(f"history measurement {column} must contain real numeric values")
        try:
            measurements.append(df[column].to_numpy(dtype=float, na_value=np.nan))
        except (TypeError, ValueError) as exc:
            raise ValueError(
                f"history measurement {column} must contain real numeric values"
            ) from exc
    a, b, humidity = measurements
    mean, keep = qc_ab(a, b)
    humidity = pd.Series(humidity, index=df.index)
    humidity = humidity.where(np.isfinite(humidity) & humidity.between(0, 100))
    sensor_median = humidity.groupby(df["sensor_index"]).transform("median")
    rh = humidity.fillna(sensor_median).to_numpy()
    pm = epa_correction(mean, rh)
    out = pd.DataFrame({"time_utc": df["time_utc"], "sensor_index": df["sensor_index"], "pm25": pm})
    return out[keep & np.isfinite(pm)].reset_index(drop=True)
