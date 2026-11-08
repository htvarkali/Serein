"""The daily check-in (TODO C-9): a 10-second log that teaches AirPlan about one child.

Design rules
------------
* Six required answers and optional pollen context, no typing. Parents of sick kids are tired.
* Ask about TODAY only (memory of past days is unreliable).
* The demo holds fictional check-ins in server memory for the current session.
  A hosted app receives entries on that server; CSV export is an explicit download.

Questions -> fields
  1. Any asthma symptoms today? none / mild / moderate / severe     -> symptoms 0-3
  2. Rescue (quick-relief) inhaler puffs today, NOT counting before
     exercise? 0 / 1-2 / 3-4 / 5+                                    -> puffs_bucket 0-3
  3. Woke up at night because of asthma? yes / no                    -> night_wake
  4. Time outdoors today? little (<1 h) / some (1-3 h) / a lot (3h+) -> outdoor 0.1/0.3/0.6
  5. Has a cold or is sick? yes / no                                 -> cold
  6. Took daily controller medicine? yes / no / doesn't have one     -> missed_controller
  7. High pollen on this day? yes / no / not sure (optional)         -> high_pollen

"Symptom day" (the model's outcome) = symptoms >= 1 OR any rescue puffs OR night waking.
This mirrors how asthma control is judged clinically (daytime symptoms, reliever
use, night waking) and should be confirmed with a clinician (TODO C-8).
"""

from __future__ import annotations

import os
import tempfile
from dataclasses import asdict, dataclass, fields
from datetime import date, datetime
from numbers import Integral, Real
from pathlib import Path

import numpy as np
import pandas as pd

from serein.personal.model import FEATURES, ChildModel, design_row

OUTDOOR_FRAC = {0: 0.1, 1: 0.3, 2: 0.6}


def _loaded_day(value) -> date:
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError as exc:
            raise ValueError("check-in day must be a calendar date or ISO date string") from exc
    if not isinstance(value, date) or isinstance(value, datetime):
        raise TypeError("check-in day must be a calendar date or ISO date string")
    return value


@dataclass
class CheckIn:
    day: date
    symptoms: int            # 0 none, 1 mild, 2 moderate, 3 severe
    puffs_bucket: int        # 0: 0, 1: 1-2, 2: 3-4, 3: 5+
    night_wake: bool
    outdoor: int             # 0 little, 1 some, 2 a lot
    cold: bool
    missed_controller: bool  # False if took it OR has no controller
    high_pollen: bool | None = None  # None preserves an unknown or skipped answer

    def __post_init__(self):
        if self.high_pollen is not None and not isinstance(self.high_pollen, (bool, np.bool_)):
            raise ValueError("check-in high_pollen answer must be boolean or None")
        if not isinstance(self.day, date) or isinstance(self.day, datetime):
            raise TypeError("check-in day must be a calendar date")
        if not all(isinstance(value, (bool, np.bool_)) for value in
                   (self.night_wake, self.cold, self.missed_controller)):
            raise ValueError("check-in yes/no answers must be boolean")
        if (any(isinstance(value, (bool, np.bool_)) or not isinstance(value, Integral)
                for value in (self.symptoms, self.puffs_bucket, self.outdoor))
                or self.symptoms not in range(4) or self.puffs_bucket not in range(4)
                or self.outdoor not in OUTDOOR_FRAC):
            raise ValueError("check-in answer out of range")

    @property
    def symptom_day(self) -> int:
        return int(self.symptoms >= 1 or self.puffs_bucket >= 1 or self.night_wake)

    @property
    def needs_doctor_flag(self) -> bool:
        """Severe symptoms or 5+ puffs: the app shows 'call your doctor', not a forecast."""
        return self.symptoms >= 3 or self.puffs_bucket >= 3


def to_frame(entries: list[CheckIn]) -> pd.DataFrame:
    df = pd.DataFrame([asdict(e) for e in entries], columns=[f.name for f in fields(CheckIn)])
    if df.empty:
        df["symptom_day"] = pd.Series(dtype=int)
        return df
    df["day"] = pd.to_datetime(df["day"]).dt.date
    df["symptom_day"] = [e.symptom_day for e in entries]
    return df.drop_duplicates("day", keep="last").sort_values("day").reset_index(drop=True)


def model_rows(log: pd.DataFrame, pm_by_day: dict) -> tuple[np.ndarray, np.ndarray]:
    """Join the log with OBSERVED daily PM2.5 near home -> (X, y) for ChildModel.fit.

    Log days may be calendar dates or ISO date strings from save_local CSV files.
    The last entry for each day wins, matching to_frame when a check-in is edited.
    pm_by_day: {date: µg/m³}. Missing or nonfinite PM on today or either prior day
    excludes the row. Available readings must be nonnegative real numbers.
    Optional ozone_ppb, hot_day and high_pollen columns supply model confounders.
    Missing ozone is unknown; absent heat and pollen columns default to zero.
    Unknown pollen is preserved in the log and exported as a blank CSV field.
    For fitting, unknown pollen contributes zero, an explicit neutral assumption.
    """
    required = ("day", "cold", "missed_controller", "outdoor", "symptom_day")
    missing = [column for column in required if column not in log.columns]
    if missing:
        raise ValueError(f"check-in table missing required columns: {', '.join(missing)}")
    optional = ("ozone_ppb", "hot_day", "high_pollen")
    duplicates = [column for column in required + optional if (log.columns == column).sum() > 1]
    if duplicates:
        raise ValueError(f"check-in table has duplicate model columns: {', '.join(duplicates)}")
    if any(not isinstance(day, date) or isinstance(day, datetime) for day in pm_by_day):
        raise TypeError("PM history keys must be calendar dates")
    X, y = [], []
    if not log.empty:
        log = log.copy()
        log["day"] = log["day"].map(_loaded_day)
        log = log.drop_duplicates("day", keep="last")
        for column in ("cold", "missed_controller"):
            if not log[column].map(lambda value: isinstance(value, (bool, np.bool_))).all():
                raise ValueError(f"check-in {column} answers must be boolean")
        for column, allowed in (("outdoor", OUTDOOR_FRAC), ("symptom_day", (0, 1))):
            if not log[column].map(
                lambda value, allowed=allowed: isinstance(value, Integral)
                and not isinstance(value, (bool, np.bool_)) and value in allowed
            ).all():
                raise ValueError(f"check-in {column} answers must be integer categories")
        for column in ("hot_day", "high_pollen"):
            if column not in log:
                continue
            values = log[column].dropna() if column == "high_pollen" else log[column]
            if not values.map(
                lambda value: isinstance(value, (Real, np.bool_))
                and np.isfinite(value) and value in (0, 1)
            ).all():
                raise ValueError(f"check-in {column} answers must be binary")
        if "ozone_ppb" in log and not log["ozone_ppb"].map(
            lambda value: value is None or value is pd.NA
            or (isinstance(value, Real) and not isinstance(value, (bool, np.bool_))
                and (np.isnan(value) or (np.isfinite(value) and value >= 0)))
        ).all():
            raise ValueError("check-in ozone_ppb must be nonnegative finite numbers or missing")
    for r in log.itertuples():
        d = r.day
        pm0 = pm_by_day.get(d)
        pm1 = pm_by_day.get(d - pd.Timedelta(days=1).to_pytimedelta())
        pm2 = pm_by_day.get(d - pd.Timedelta(days=2).to_pytimedelta())
        for pm in (pm0, pm1, pm2):
            if pm is None or pm is pd.NA:
                continue
            if (isinstance(pm, (bool, np.bool_)) or not isinstance(pm, Real)
                    or (np.isfinite(pm) and pm < 0)):
                raise ValueError("PM readings must be nonnegative real numbers")
        if any(pd.isna(pm) or not np.isfinite(pm) for pm in (pm0, pm1, pm2)):
            continue
        ozone = getattr(r, "ozone_ppb", None)
        pollen = getattr(r, "high_pollen", None)
        X.append(design_row(pm0, pm1, pm2, OUTDOOR_FRAC[r.outdoor], int(r.cold),
                            int(r.missed_controller),
                            ozone_ppb=ozone if pd.notna(ozone) else None,
                            hot_day=getattr(r, "hot_day", 0),
                            high_pollen=pollen if pd.notna(pollen) else 0))
        y.append(r.symptom_day)
    if not X:
        return np.zeros((0, len(FEATURES))), np.zeros(0)
    return np.array(X), np.array(y, float)


def fit_child(log: pd.DataFrame, pm_by_day: dict) -> ChildModel:
    X, y = model_rows(log, pm_by_day)
    m = ChildModel()
    return m.fit(X, y) if len(y) else m


def save_local(log: pd.DataFrame, path: Path) -> None:
    """Save on THIS device only. Never commit or upload real logs."""
    path.parent.mkdir(parents=True, exist_ok=True)
    # A sibling file keeps replacement atomic on the destination filesystem.
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f"{path.name}.",
                                     suffix=".tmp", delete=False) as stream:
        temporary = Path(stream.name)
    try:
        log.to_csv(temporary, index=False)
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)
