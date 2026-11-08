"""Optional forecast context for family plans, separate from SmokeCast features.

Only complete local standard-time days are scored: 24 distinct finite hourly
values. Ozone is the maximum of the 17 complete eight-hour windows wholly inside
that day, not the regulatory ozone AQI statistic. Temperature is the maximum of
hourly instantaneous forecasts, not a GRIB interval maximum or observed TMAX.
No interpolation, later cycle, observed value or three-hour weather cache is used.
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd

from serein.config import Study
from serein.data import aqm, hrrr
from serein.data.availability import HRRR_POSTED_LAG_H, Availability
from serein.features.daily import add_local_date

# Provisional ozone-specific schedule allowance. The 12z ozone files on Nov 5/6,
# 2026 were posted at 18:06:20/18:05:49 UTC; use 18:15, not the PM2.5 lag.
# These recent timestamps do not establish original posting times in 2023.
AQM_OZONE_POSTED_LAG_H = 6.25


def _daily_values(frame: pd.DataFrame, points: pd.DataFrame, day: date,
                  cycle: int, ozone: bool) -> pd.DataFrame:
    """Validate cache identity and aggregate only exact local clock hours."""
    columns = ["point_id", "valid_date", "hours", "value"]
    if frame.empty:
        return pd.DataFrame(columns=columns)
    # Context caches carry sampling coordinates so a moved/reused ID cannot
    # silently receive the old location's weather or ozone.
    frame = frame.merge(points[["point_id", "lat", "lon", "gmt_offset"]],
                        on="point_id", suffixes=("_cached", ""), validate="many_to_one")
    frame = frame[(frame.lat == frame.lat_cached) & (frame.lon == frame.lon_cached)].copy()
    if frame.empty:
        return pd.DataFrame(columns=columns)
    issue = pd.to_datetime(frame["issue_date"], format="mixed").dt.date
    times = pd.to_datetime(frame["valid_utc"], utc=True, format="mixed").dt.tz_localize(None)
    step = frame["step" if ozone else "fhr"]
    if (not pd.api.types.is_numeric_dtype(step) or pd.api.types.is_bool_dtype(step)
            or not np.isfinite(step).all() or (step != np.floor(step)).any()):
        raise ValueError("Context forecast steps must be finite integer hours")
    expected = pd.Timestamp(day) + pd.Timedelta(hours=cycle) + pd.to_timedelta(step, unit="h")
    last_step = (47 if day < date(2021, 7, 20) else 71) if ozone else 48
    if (issue.ne(day).any() or times.isna().any() or step.isna().any()
            or times.ne(expected).any() or (step < 0).any()
            or (step > last_step).any()):
        raise ValueError("Context cache timestamps do not match the requested issue cycle")
    if frame.duplicated(["point_id", "valid_utc"]).any():
        raise ValueError("Context cache contains duplicate point/timestamp samples")
    offsets = points.set_index("point_id")["gmt_offset"]
    frame = add_local_date(frame, offsets, time_col="valid_utc")
    frame["_local_time"] = times + pd.to_timedelta(frame["_off"], unit="h")
    rows = []
    for (point, valid), group in frame.groupby(["point_id", "local_date"], observed=True):
        clock = pd.date_range(pd.Timestamp(valid), periods=24, freq="h")
        series = group.set_index("_local_time")["value"].reindex(clock)
        values = series.to_numpy(float)
        finite = np.isfinite(values)
        if ozone:
            finite &= values >= 0
        else:
            finite &= values >= -273.15
        count = int(finite.sum())
        value = np.nan
        if count == 24:
            value = float(np.convolve(values, np.ones(8) / 8, mode="valid").max()
                          if ozone else values.max())
        rows.append({"point_id": point, "valid_date": valid, "hours": count, "value": value})
    return pd.DataFrame(rows, columns=columns)


def forecast_context(study: Study, day: date, points: pd.DataFrame,
                     leads: list[int]) -> pd.DataFrame:
    """Read already-cached context from the configured, issue-time-eligible cycles.

    Uses the study's HRRR lag and the separate provisional ozone posting allowance.
    Historical archive re-upload timestamps are not evidence of original posting
    time. This function performs no downloads and does not change model inputs.
    """
    out = pd.DataFrame([{"point_id": point, "valid_date": day + timedelta(days=int(lead))}
                        for lead in leads for point in points["point_id"]])
    specs = [
        ("ozone", "ozone_max8h_ppb", "AQM bias-corrected hourly ozone",
         "max_8h_within_local_day"),
        ("temperature", "temperature_max_c", "HRRR hourly 2 m temperature",
         "maximum_hourly_forecast"),
    ]
    for prefix, value, _, _ in specs:
        out[value], out[f"{prefix}_hours"] = np.nan, 0
        out[f"{prefix}_source"] = pd.Series(None, index=out.index, dtype=object)
        out[f"{prefix}_statistic"] = pd.Series(None, index=out.index, dtype=object)
        out[f"{prefix}_cycle_utc"] = pd.NaT
    # Old/synthetic forecast inputs without offsets still work, with unknown context.
    if "gmt_offset" not in points:
        return out
    points = points[np.isfinite(points["gmt_offset"])].copy()
    if points.empty:
        return out
    av = Availability.from_study(study.raw)
    for prefix, value, source, statistic in specs:
        ozone = prefix == "ozone"
        cycle, lag = ((av.aqm_cycle, AQM_OZONE_POSTED_LAG_H) if ozone
                      else (av.hrrr_cycle, HRRR_POSTED_LAG_H))
        if not av.check_model_cycle(day, cycle, lag):
            continue
        hourly = (aqm.load_cycles([day], cycle=cycle, store=study.name, pollutant="o3")
                  if ozone else hrrr.load_temperature_cycles([day], cycle=cycle, store=study.name))
        daily = _daily_values(hourly, points, day, cycle, ozone)
        if daily.empty:
            continue
        daily = daily.rename(columns={"hours": f"{prefix}_hours", "value": value})
        out = out.drop(columns=[value, f"{prefix}_hours"]).merge(
            daily, how="left", on=["point_id", "valid_date"], validate="one_to_one")
        present = out[f"{prefix}_hours"].notna()
        out[f"{prefix}_hours"] = out[f"{prefix}_hours"].fillna(0).astype(int)
        out.loc[present, f"{prefix}_source"] = source
        out.loc[present, f"{prefix}_statistic"] = statistic
        out.loc[present, f"{prefix}_cycle_utc"] = pd.Timestamp(day) + pd.Timedelta(hours=cycle)
    return out
