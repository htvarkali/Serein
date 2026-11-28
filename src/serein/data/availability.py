"""The "no peeking" rules: which data existed at the moment a forecast is issued.

A backtest is only honest if, for every past day, the model sees exactly what it
would have seen live. Every feature builder asks these functions what is allowed.

Example (issue day 2024-09-01, issue_hour_utc 18.5, obs_lag_hours 1.5):
  * the latest usable sensor hour STARTS at 16:00 UTC (it ends 17:00, and 17:00 is
    1.5 h before 18:30);
  * the HRRR and AQM runs are the 12z runs of 2024-09-01 (posted ~14Z and ~18Z);
  * the HMS smoke map is the one for 2024-08-31;
  * fires detected 2024-08-31 18:30 .. 2024-09-01 18:30 UTC are usable.

``fire_lag_hours`` (default 0) moves the end of that fire window earlier, for
detections that are posted some hours after the satellite pass: with 3, fires
detected 2024-08-31 15:30 .. 2024-09-01 15:30 UTC are used. The default keeps every
existing table unchanged (see docs/CODE_REVIEW_2026-11-27.md, item 1).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from math import isfinite
from numbers import Integral, Real


def validate_cycle_hour(cycle: int) -> None:
    if isinstance(cycle, bool) or not isinstance(cycle, Integral):
        raise TypeError("cycle must be an integer UTC hour")
    if not 0 <= cycle <= 23:
        raise ValueError("cycle must be between 0 and 23")


def _validate_hours(name: str, value: float) -> None:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise TypeError(f"{name} must be a real number")
    if not isfinite(value) or value < 0:
        raise ValueError(f"{name} must be finite and nonnegative")


@dataclass
class Availability:
    issue_hour_utc: float = 18.5
    hrrr_cycle: int = 12
    aqm_cycle: int = 12
    obs_lag_hours: float = 1.5
    hms_lag_days: int = 1
    firms_window_hours: float = 24
    fire_lag_hours: float = 0

    def __post_init__(self) -> None:
        for name in ("issue_hour_utc", "obs_lag_hours", "firms_window_hours", "fire_lag_hours"):
            _validate_hours(name, getattr(self, name))
        if self.issue_hour_utc >= 24:
            raise ValueError("issue_hour_utc must be less than 24")
        validate_cycle_hour(self.hrrr_cycle)
        validate_cycle_hour(self.aqm_cycle)
        if isinstance(self.hms_lag_days, bool) or not isinstance(self.hms_lag_days, Integral):
            raise TypeError("hms_lag_days must be an integer")
        if self.hms_lag_days < 0:
            raise ValueError("hms_lag_days must be nonnegative")

    @classmethod
    def from_study(cls, raw: dict) -> Availability:
        a = raw.get("availability", {})
        return cls(issue_hour_utc=raw.get("issue_hour_utc", 18.5), **a)

    def issue_time(self, d: date) -> datetime:
        return datetime(d.year, d.month, d.day) + timedelta(hours=self.issue_hour_utc)

    def last_obs_hour_start(self, d: date) -> datetime:
        """Start time of the newest hourly observation allowed (UTC, whole hour)."""
        t = self.issue_time(d) - timedelta(hours=self.obs_lag_hours) - timedelta(hours=1)
        return t.replace(minute=0, second=0, microsecond=0)

    def hms_day(self, d: date) -> date:
        return d - timedelta(days=self.hms_lag_days)

    def firms_window(self, d: date) -> tuple[datetime, datetime]:
        """(start, end] of the fire detections a forecast issued on d may use."""
        end = self.issue_time(d) - timedelta(hours=self.fire_lag_hours)
        return end - timedelta(hours=self.firms_window_hours), end

    def check_model_cycle(self, d: date, cycle: int, posted_lag_hours: float) -> bool:
        """True if a model run of day d / cycle was public before issue time."""
        validate_cycle_hour(cycle)
        _validate_hours("posted_lag_hours", posted_lag_hours)
        posted = datetime(d.year, d.month, d.day, cycle) + timedelta(hours=posted_lag_hours)
        return posted <= self.issue_time(d)


# Measured AWS posting lags (hours after cycle time), 2026-11-01. See configs/.
HRRR_POSTED_LAG_H = 2.0   # 12z f48 LastModified 13:55Z
AQM_POSTED_LAG_H = 6.1    # 12z hourly PM2.5 LastModified ~18:03Z
