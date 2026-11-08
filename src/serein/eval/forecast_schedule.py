"""Check whether a configured NOAA extraction can support each local forecast day."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
from datetime import date, datetime
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from serein.data.availability import (
    AQM_POSTED_LAG_H,
    HRRR_POSTED_LAG_H,
    Availability,
    validate_cycle_hour,
)
from serein.data.hrrr import DEFAULT_MET, SHORT
from serein.eval.episode_inputs import _choices
from serein.features.table import MET_VARS


def scheduled_inputs(points: pd.DataFrame, day: date, leads, *, source: str, cycle: int,
                     max_fhr: int = 48, smoke_every: int = 1, met_every: int = 3,
                     met_vars=None, issue_hour_utc: float = 18.5) -> pd.DataFrame:
    """Count requested timestamps before data loss or out-of-grid sampling.

    AQM counts hour-start labels, matching extract_cycle and model_daily. HRRR
    counts instantaneous requested fields. Counts describe the code's declared
    schedule, not actual product availability or full-day representativeness.
    """
    if not isinstance(day, date) or isinstance(day, datetime):
        raise TypeError("day must be a calendar date")
    validate_cycle_hour(cycle)
    leads = _choices(leads, "leads", integers=True)
    if source not in {"hrrr", "aqm"}:
        raise ValueError("source must be hrrr or aqm")
    av = Availability(issue_hour_utc=issue_hour_utc)
    required = {"point_id", "gmt_offset"}
    if not points.columns.is_unique or not required.issubset(points):
        raise ValueError("points require unique columns including point_id and gmt_offset")
    if (points.empty or points.point_id.duplicated().any()
            or not points.point_id.map(lambda value: isinstance(value, str) and bool(value.strip())).all()):
        raise ValueError("point IDs must be distinct nonempty strings")
    offsets = points.set_index("point_id").gmt_offset.astype(float)
    if not np.isfinite(offsets).all() or offsets.abs().gt(24).any():
        raise ValueError("point offsets must be finite and within 24 hours of UTC")
    for name, value in (("max_fhr", max_fhr), ("smoke_every", smoke_every), ("met_every", met_every)):
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, (int, np.integer)):
            raise TypeError(f"{name} must be an integer")
        if value < (0 if name == "max_fhr" else 1):
            raise ValueError(f"invalid {name}")
    met_vars = list(DEFAULT_MET if met_vars is None else met_vars)
    if len(set(met_vars)) != len(met_vars) or any(name not in DEFAULT_MET for name in met_vars):
        raise ValueError("met_vars must contain unique supported HRRR field names")
    enabled = {SHORT[name] for name in met_vars}
    fields = ["smoke", *MET_VARS] if source == "hrrr" else ["pm25"]
    report = pd.MultiIndex.from_product(
        [points.point_id, fields, leads], names=["point_id", "variable", "lead"]).to_frame(index=False)
    report["aggregation"] = "local_day"
    report["min_count"] = np.where(report.variable.isin(["smoke", "pm25"]), 12, 4)
    if source == "hrrr":
        wind = pd.MultiIndex.from_product(
            [points.point_id, ["u10", "v10"]], names=["point_id", "variable"]).to_frame(index=False)
        wind["lead"], wind["aggregation"], wind["min_count"] = 0, "issue_wind", 1
        report = pd.concat([report, wind], ignore_index=True)
    local_cycle = cycle + report.point_id.map(offsets).to_numpy(dtype=float)
    cadence = (np.where(report.variable.eq("smoke"), smoke_every, met_every)
               if source == "hrrr" else np.ones(len(report), dtype=int))
    last_step = max_fhr if source == "hrrr" else (47 if day < date(2021, 7, 20) else 71)
    lower = np.maximum(0, np.ceil((24 * report.lead.to_numpy() - local_cycle) / cadence))
    upper = np.minimum(last_step // cadence,
                       np.ceil((24 * (report.lead.to_numpy() + 1) - local_cycle) / cadence) - 1)
    count = np.maximum(upper - lower + 1, 0).astype("int64")
    first, last = lower * cadence, upper * cadence
    if source == "hrrr":
        active = report.variable.eq("smoke") | report.variable.isin(enabled)
        count[~active] = 0
        now = report.aggregation.eq("issue_wind").to_numpy()
        now_fhr = int(issue_hour_utc - cycle)
        count[now] = ((0 <= now_fhr <= max_fhr) and now_fhr % met_every == 0)
        count[now & ~active] = 0
        first[now] = last[now] = now_fhr
    report["n_scheduled"] = count
    report["first_valid_utc"] = pd.Timestamp(day) + pd.to_timedelta(cycle + first, unit="h")
    report["last_valid_utc"] = pd.Timestamp(day) + pd.to_timedelta(cycle + last, unit="h")
    report.loc[report.n_scheduled.eq(0), ["first_valid_utc", "last_valid_utc"]] = pd.NaT
    report["schedule_status"] = np.select(
        [report.n_scheduled.eq(0), report.n_scheduled.lt(report.min_count)],
        ["no_scheduled_samples", "below_feature_threshold"], default="meets_feature_threshold")
    lag = HRRR_POSTED_LAG_H if source == "hrrr" else AQM_POSTED_LAG_H
    report["cycle_available_assumed"] = av.check_model_cycle(day, cycle, lag)
    report["source"], report["issue_date"], report["cycle"] = source, day, cycle
    report["valid_date"] = pd.Timestamp(day) + pd.to_timedelta(report.lead, unit="D")
    return report


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=Path("configs/west_us.yaml"))
    parser.add_argument("--points", type=Path, required=True)
    parser.add_argument("--date", type=date.fromisoformat, required=True)
    parser.add_argument("--source", choices=("hrrr", "aqm"), action="append", dest="sources")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.output.exists():
            raise FileExistsError(f"output already exists: {args.output}")
        if not args.output.parent.is_dir():
            raise ValueError("output parent must exist")
        config_bytes, points_bytes = args.config.read_bytes(), args.points.read_bytes()
        config = yaml.safe_load(io.BytesIO(config_bytes))
        from serein.eval.cache_archive import development_days

        if args.date not in development_days(config):
            raise ValueError("schedule date must belong to a configured development season")
        leads = _choices(config["leads"], "leads", integers=True)
        if any((args.date + pd.Timedelta(days=int(lead))).year in config["split"]["test"] for lead in leads):
            raise ValueError("schedule target dates must not enter reserved test years")
        points = pd.read_parquet(io.BytesIO(points_bytes))
        av = Availability.from_study(config)
        sources = _choices(args.sources or ["hrrr", "aqm"], "sources")
        options = config.get("hrrr", {})
        report = pd.concat([
            scheduled_inputs(points, args.date, leads, source=source,
                             cycle=av.hrrr_cycle if source == "hrrr" else av.aqm_cycle,
                             max_fhr=options.get("max_fhr", 48),
                             smoke_every=options.get("smoke_every", 1),
                             met_every=options.get("met_every", 3),
                             met_vars=options.get("met_vars"), issue_hour_utc=av.issue_hour_utc)
            for source in sources], ignore_index=True)
        keys = ["source", "variable", "lead", "aggregation", "n_scheduled", "min_count",
                "schedule_status", "cycle_available_assumed"]
        summary = report.groupby(keys, sort=True, observed=True).size().rename("n_points").reset_index()
        manifest = {"report_version": 1, "issue_date": args.date.isoformat(), "sources": sources,
                    "n_points": len(points), "leads": leads,
                    "config": str(args.config.resolve()),
                    "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
                    "points": str(args.points.resolve()),
                    "points_sha256": hashlib.sha256(points_bytes).hexdigest(),
                    "posting_lag_hours_assumed": {"hrrr": HRRR_POSTED_LAG_H, "aqm": AQM_POSTED_LAG_H},
                    "interpretation": "configured extraction schedule only; no provider availability, "
                                      "actual posting time, full-day coverage or forecast skill verified"}
        args.output.mkdir(exist_ok=False)
        report.to_parquet(args.output / "schedule.parquet", index=False)
        summary.to_csv(args.output / "summary.csv", index=False)
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                                   encoding="utf-8")
    except (OSError, ValueError, TypeError, KeyError, OverflowError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    print(f"wrote {args.output}: {len(report)} scheduled input combinations")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
