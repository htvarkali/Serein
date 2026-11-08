"""Command line: ``uv run serein <command> --help``."""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta

import pandas as pd

from serein.config import REPO_ROOT, load_study

DEFAULT_CONFIG = str(REPO_ROOT / "configs" / "west_us.yaml")


def _days(args) -> list[date]:
    from serein.data.airnow import daterange, parse_date

    study = load_study(args.config)
    if getattr(args, "split", None):
        return study.split_days(args.split)
    if getattr(args, "years", None):
        return study.season_days([int(y) for y in args.years.split(",")])
    if not (args.start and args.end):
        sys.exit("Give --start/--end, --years, or --split")
    return daterange(parse_date(args.start), parse_date(args.end))


def _run_parallel(fn, days, workers, label):
    from tqdm import tqdm

    ok = fail = 0
    with ThreadPoolExecutor(workers) as ex:
        futs = {ex.submit(fn, d): d for d in days}
        for f in tqdm(as_completed(futs), total=len(futs), desc=label):
            try:
                res = f.result()
                ok += res is not None
                fail += res is None
            except Exception as e:  # noqa: BLE001 - keep going; report at the end
                fail += 1
                print(f"  {label} {futs[f]} failed: {e}", file=sys.stderr)
    print(f"{label}: {ok} ok, {fail} missing/failed")


def cmd_download(args):
    from serein.data import airnow, aqm, hms, hrrr
    from serein.data.points import load_points

    study = load_study(args.config)
    days = _days(args)
    src = args.source
    if src in ("airnow", "all"):
        _run_parallel(airnow.download_hourly_day, days, args.workers, "airnow-hourly")
        _run_parallel(airnow.download_reportingarea_day, days, args.workers, "airnow-forecast")
    if src in ("hms", "all"):
        _run_parallel(hms.download_day, days, args.workers, "hms")
        pad = sorted({d - timedelta(days=1) for d in days} | set(days))
        _run_parallel(hms.download_fire_day, pad, args.workers, "hms-fires")
    if src in ("hrrr", "all"):
        pts = load_points(study.name)
        h = study.raw["hrrr"]
        _run_parallel(lambda d: hrrr.extract_cycle(
            d, pts, cycle=study.raw["availability"]["hrrr_cycle"], max_fhr=h["max_fhr"],
            smoke_every=h["smoke_every"], met_every=h["met_every"], met_vars=h["met_vars"],
            store=study.name),
            days, max(1, args.workers // 4), "hrrr")
    if src in ("aqm", "all"):
        pts = load_points(study.name)
        _run_parallel(lambda d: aqm.extract_cycle(
            d, pts, cycle=study.raw["availability"]["aqm_cycle"], store=study.name),
            days, max(1, args.workers // 4), "aqm")
    if src == "firms":
        from serein.data import firms
        # Only the season days (plus the day before each run, for the 24 h window),
        # not every day between the first and last date.
        n = 0
        for start, end in firms.contiguous_runs(days):
            n += len(firms.download_range(start - timedelta(days=1), end, study.region))
        print(f"firms: {n} detections")


def cmd_build_points(args):
    from serein.config import raw_dir
    from serein.data import airnow
    from serein.data.points import build_points, save_points

    study = load_study(args.config)
    days = _days(args)
    hourly = airnow.load_hourly(days)
    if hourly.empty:
        sys.exit("No AirNow data cached; run `serein download airnow` first.")
    sites = airnow.site_table(hourly)
    # Keep sites with enough data to be useful.
    sites = sites[sites["n_hours"] >= args.min_hours]
    pa = None
    pa_path = raw_dir("purpleair") / "sensors.parquet"  # honors SEREIN_DATA
    if pa_path.exists():
        pa = pd.read_parquet(pa_path)
    grid = study.raw.get("grid_step_deg") if not args.no_grid else None
    pts = build_points(sites, study.region, grid, pa)
    pts = pts[study.in_study(pts["lat"], pts["lon"])].reset_index(drop=True)
    save_points(pts, study.name)
    print(pts["kind"].value_counts().to_string())


def cmd_build_table(args):
    from serein.data.points import load_points
    from serein.features.table import build_table, processed_dir

    study = load_study(args.config)
    days = _days(args)
    pts = load_points(study.name)
    pts = pts[pts["kind"].isin(args.kinds.split(","))]
    tab = build_table(study, days, pts, use_firms=not args.no_firms)
    name = args.out or (args.split or f"{days[0]:%Y%m%d}_{days[-1]:%Y%m%d}")
    path = processed_dir(study) / f"table_{name}.parquet"
    tab.to_parquet(path, index=False)
    print(f"wrote {path} rows={len(tab)} cols={tab.shape[1]}")


def cmd_backtest(args):
    from serein.eval.backtest import run_backtest

    run_backtest(load_study(args.config), args)


def cmd_map(args):
    from serein.data.airnow import parse_date
    from serein.models.infer import forecast_day, plot_map

    study = load_study(args.config)
    run = REPO_ROOT / "outputs" / "backtest" / args.run
    day = parse_date(args.date)
    fc = forecast_day(study, day, run, with_grid=not args.no_grid)
    out = REPO_ROOT / "outputs" / "maps"
    out.mkdir(parents=True, exist_ok=True)
    fc.to_parquet(out / f"forecast_{day:%Y%m%d}.parquet", index=False)
    plot_map(fc, out / f"map_{day:%Y%m%d}.png")
    print(f"wrote {out / f'map_{day:%Y%m%d}.png'}")


def cmd_explain(args):
    from serein.data.airnow import parse_date
    from serein.eval.explain import explain_point

    study = load_study(args.config)
    run = REPO_ROOT / "outputs" / "backtest" / args.run
    ex = explain_point(study, parse_date(args.date), run, args.point, lead=args.lead)
    print(ex.text())


def cmd_live(args):
    from serein import live
    from serein.data.airnow import parse_date

    study = load_study(args.config)
    if not args.score_only:
        day = parse_date(args.date) if args.date else date.today()
        live.make_forecast(study, day, run=args.run, force=args.force,
                           allow_missing=args.allow_missing)
    live.score(study)
    print(f"scoreboard: {live.LIVE / study.name / 'SCOREBOARD.md'}")


def cmd_transfer(args):
    from serein.eval.transfer import run_transfer

    run_transfer(load_study(args.config), REPO_ROOT / "outputs" / "backtest" / args.run,
                 split=args.split, tag=args.tag)


def cmd_purpleair(args):
    from serein.data import purpleair

    if args.action == "estimate":
        est = purpleair.estimate_history_points(args.sensors, args.days, args.average)
        for k, v in est.items():
            print(f"{k:>8}: {v:,}")
        print("Prices are placeholders: confirm on the PurpleAir Developer Dashboard.")
    elif args.action == "list":
        df = purpleair.list_outdoor_sensors(load_study(args.config).region)
        print(f"{len(df)} outdoor sensors saved")
    elif args.action == "qc":
        import json
        from pathlib import Path

        from serein.data.purpleair_qc import (
            QCConfig,
            accepted_history,
            quality_control,
            summarize_qc,
        )

        if not args.input or not args.output:
            sys.exit("purpleair qc requires INPUT and --output (CSV or Parquet)")

        def read(path):
            path = Path(path)
            if path.suffix.lower() == ".csv":
                return pd.read_csv(path)
            if path.suffix.lower() == ".parquet":
                return pd.read_parquet(path)
            raise ValueError("QC files must use .csv or .parquet")

        def write(frame, path):
            path = Path(path)
            if path.suffix.lower() not in (".csv", ".parquet"):
                raise ValueError("QC files must use .csv or .parquet")
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix.lower() == ".csv":
                frame.to_csv(path, index=False)
            else:
                frame.to_parquet(path, index=False)

        try:
            inputs = {Path(path).resolve() for path in (args.input, args.sensors_file) if path}
            outputs = [Path(path).resolve() for path in (args.output, args.clean_output) if path]
            if any(path in inputs for path in outputs) or len(set(outputs)) != len(outputs):
                raise ValueError("QC outputs must be distinct from each other and from input files")
            config = QCConfig(
                ab_abs_tol=args.ab_abs_tol, ab_rel_tol=args.ab_rel_tol,
                expected_minutes=args.average, stuck_hours=args.stuck_hours,
                stuck_tolerance=args.stuck_tolerance, neighbor_radius_km=args.neighbor_radius_km,
                min_neighbors=args.min_neighbors, neighbor_abs_tol=args.neighbor_abs_tol,
                neighbor_rel_tol=args.neighbor_rel_tol)
            sensors = read(args.sensors_file) if args.sensors_file else None
            audit = quality_control(read(args.input), sensors, config)
            # Validate every destination before writing either output.
            if any(path.suffix.lower() not in (".csv", ".parquet") for path in outputs):
                raise ValueError("QC files must use .csv or .parquet")
            write(audit, args.output)
            if args.clean_output:
                write(accepted_history(audit), args.clean_output)
            print(json.dumps(summarize_qc(audit), indent=2, sort_keys=True))
        except (TypeError, ValueError, OSError) as exc:
            sys.exit(f"PurpleAir QC: {exc}")


def cmd_airplan_demo(args):
    from serein.personal.simulate import demo

    demo(seed=args.seed, days=args.days, language=args.language)


def main(argv=None):
    # Windows consoles default to cp1252, which can't print µ, ³ or ≈.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    p = argparse.ArgumentParser(prog="serein", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    def common(sp):
        sp.add_argument("--config", default=DEFAULT_CONFIG)
        sp.add_argument("--start")
        sp.add_argument("--end")
        sp.add_argument("--years", help="comma list, uses season months from config")
        sp.add_argument("--split", choices=["train", "calibrate", "test"])

    sp = sub.add_parser("download", help="download + extract one data source")
    sp.add_argument("source", choices=["airnow", "hms", "hrrr", "aqm", "firms", "all"])
    common(sp)
    sp.add_argument("--workers", type=int, default=8)
    sp.set_defaults(fn=cmd_download)

    sp = sub.add_parser("build-points", help="registry of EPA sites (+PurpleAir, +grid)")
    common(sp)
    sp.add_argument("--min-hours", type=int, default=24)
    sp.add_argument("--no-grid", action="store_true")
    sp.set_defaults(fn=cmd_build_points)

    sp = sub.add_parser("build-table", help="feature/target table for a set of days")
    common(sp)
    sp.add_argument("--kinds", default="epa")
    sp.add_argument("--out")
    sp.add_argument("--no-firms", action="store_true")
    sp.set_defaults(fn=cmd_build_table)

    sp = sub.add_parser("backtest", help="train on train split, calibrate, score on test")
    sp.add_argument("--config", default=DEFAULT_CONFIG)
    sp.add_argument("--train", default="train", help="table name for training")
    sp.add_argument("--calibrate", default="calibrate")
    sp.add_argument("--test", default="test")
    sp.add_argument("--epochs", type=int, default=300)
    sp.add_argument("--seed", type=int, default=0)
    sp.add_argument("--seeds", type=int, default=5, help="ensemble size for SmokeCast")
    sp.add_argument("--tag", default="")
    sp.add_argument("--final", action="store_true",
                    help="score on TEST seasons (once! see docs/BACKTEST_PROTOCOL.md)")
    sp.add_argument("--force", action="store_true")
    sp.add_argument("--no-ablation", action="store_true")
    sp.add_argument("--no-gbm", action="store_true")
    sp.add_argument("--node-mask", type=float, default=0.15)
    sp.add_argument("--drop", default="", help="ablation: drop input groups by prefix, e.g. aqm_,hrrr_")
    sp.add_argument("--no-wind", action="store_true", help="ablation: no wind on graph edges")
    sp.add_argument("--holdout-sites", type=float, default=0.0,
                    help="hide this fraction of monitors entirely (leave-sites-out test)")
    sp.add_argument("--hidden", type=int, default=64)
    sp.add_argument("--layers", type=int, default=2)
    sp.add_argument("--dropout", type=float, default=0.3)
    sp.add_argument("--weight-decay", type=float, default=1e-3)
    sp.add_argument("--lr", type=float, default=2e-3)
    sp.add_argument("--history", type=int, default=1,
                    help="days of inputs each sensor reads (1 = today only)")
    sp.add_argument("--smoke-weight", type=float, default=6.0,
                    help="loss weight for days >= 35.5 ug/m3 (1 = none)")
    sp.set_defaults(fn=cmd_backtest)

    sp = sub.add_parser("map", help="forecast map for one day from a trained run")
    sp.add_argument("--config", default=DEFAULT_CONFIG)
    sp.add_argument("--date", required=True)
    sp.add_argument("--run", default="west_us_dev", help="folder in outputs/backtest/")
    sp.add_argument("--no-grid", action="store_true")
    sp.set_defaults(fn=cmd_map)

    sp = sub.add_parser("explain", help="which neighbors and inputs drove one forecast")
    sp.add_argument("--config", default=DEFAULT_CONFIG)
    sp.add_argument("--date", required=True)
    sp.add_argument("--point", required=True, help="monitor ID (AQS) or grid cell ID")
    sp.add_argument("--lead", type=int, default=1, help="days ahead (0-3)")
    sp.add_argument("--run", default="west_us_dev", help="folder in outputs/backtest/")
    sp.set_defaults(fn=cmd_explain)

    sp = sub.add_parser("live", help="today's forecast (after 18:30 UTC) + score older ones")
    sp.add_argument("--config", default=DEFAULT_CONFIG)
    sp.add_argument("--date", help="issue day (default: today)")
    sp.add_argument("--run", default="west_us_dev", help="folder in outputs/backtest/")
    sp.add_argument("--force", action="store_true", help="overwrite / run before issue time")
    sp.add_argument("--allow-missing", action="store_true", help="run even if AQM/HRRR missing")
    sp.add_argument("--score-only", action="store_true")
    sp.set_defaults(fn=cmd_live)

    sp = sub.add_parser("transfer", help="apply a trained run to another region (test!)")
    sp.add_argument("--config", default=str(REPO_ROOT / "configs" / "northeast_2023.yaml"))
    sp.add_argument("--run", required=True, help="folder in outputs/backtest/")
    sp.add_argument("--split", default="test")
    sp.add_argument("--tag", default="")
    sp.set_defaults(fn=cmd_transfer)

    sp = sub.add_parser("purpleair", help="PurpleAir tools")
    sp.add_argument("action", choices=["estimate", "list", "qc"])
    sp.add_argument("input", nargs="?", help="raw history CSV or Parquet for offline QC")
    sp.add_argument("--config", default=DEFAULT_CONFIG)
    sp.add_argument("--sensors", type=int, default=300)
    sp.add_argument("--days", type=int, default=153)
    sp.add_argument("--average", type=int, default=60)
    sp.add_argument("--output", help="QC audit CSV or Parquet (all original rows plus flags)")
    sp.add_argument("--sensors-file", help="sensor metadata CSV or Parquet, keyed by sensor_index")
    sp.add_argument("--clean-output", help="optional accepted time_utc/sensor_index/pm25 output")
    sp.add_argument("--ab-abs-tol", type=float, default=5.0)
    sp.add_argument("--ab-rel-tol", type=float, default=0.7)
    sp.add_argument("--stuck-hours", type=float, default=24.0)
    sp.add_argument("--stuck-tolerance", type=float, default=0.01)
    sp.add_argument("--neighbor-radius-km", type=float, default=25.0)
    sp.add_argument("--min-neighbors", type=int, default=3)
    sp.add_argument("--neighbor-abs-tol", type=float, default=30.0)
    sp.add_argument("--neighbor-rel-tol", type=float, default=2.0)
    sp.set_defaults(fn=cmd_purpleair)

    sp = sub.add_parser("airplan-demo", help="simulate a child and print their plan")
    sp.add_argument("--seed", type=int, default=1)
    sp.add_argument("--days", type=int, default=60)
    sp.add_argument("--language", default="en")
    sp.set_defaults(fn=cmd_airplan_demo)

    args = p.parse_args(argv)
    args.fn(args)


if __name__ == "__main__":
    main()
