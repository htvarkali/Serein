"""Hour-by-hour smoke field for the 3D smoke world (website), from one day's forecast.

For every forecast point (EPA monitors and the 0.25 degree map grid) and every hour of
the next 72 hours:

- ``noaa``: NOAA's bias-corrected AQM hourly PM2.5 (the 12z run of the issue day, out to
  72 hours). This is the hour-by-hour shape: NOAA's physics model moves the smoke.
- ``serein``: the same hourly shape scaled, separately for each local day, so that the
  day's average equals Serein's daily forecast (median) at that point. Serein has been
  tested on daily averages; whether this hourly version beats NOAA hour by hour is a
  separate test (``serein.eval.hourly``).

Wind comes from HRRR's 10 m wind (every 3 hours, to 48 hours; none after that), and fire
points from the latest HMS fire detections. Nothing here is a new physics model.

For each forecast day the file also carries what the site shows for a place (``daily``):
the median and 90% range, and, when the trained run's calibration settings are found
(``outputs/backtest/<run>/``), the chance of an "Unhealthy for Sensitive Groups" day, the
warning the backtest scored, and the low-confidence flag. These use the same rules as the
crew outlook (``serein.crew``) and the backtest, so the site never shows a raw,
uncalibrated chance.

    SEREIN_DATA=C:/Users/.../Serein/data uv run python -m serein.world \\
        --forecast outputs/live/west_us/forecasts/20261123.parquet --out website/data/live.json

To add or refresh only the daily part of an existing file (no NOAA caches needed):

    uv run python -m serein.world --daily-only \\
        --forecast app/sample/forecast_20230818.parquet --out website/data/aug2023.json
"""

from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from serein.config import REPO_ROOT, interim_dir, raw_dir

HOURS = 72
SCALE_BOUNDS = (0.25, 4.0)  # a day's shape is never stretched more than this


def _cache(store: str, folder: str, d) -> pd.DataFrame:
    p = interim_dir(f"{store}/{folder}") / f"{d:%Y%m%d}_12z.parquet"
    return pd.read_parquet(p) if p.exists() else pd.DataFrame()


def hourly_noaa(aqm: pd.DataFrame, ids: list[str], start: datetime) -> np.ndarray:
    """[points, HOURS] AQM PM2.5 for valid hours start .. start+71 h (NaN where missing)."""
    out = np.full((len(ids), HOURS), np.nan)
    if aqm.empty:
        return out
    pos = {k: i for i, k in enumerate(ids)}
    t = pd.to_datetime(aqm["valid_utc"]).dt.tz_localize(None)
    h = ((t - pd.Timestamp(start)) / pd.Timedelta(hours=1)).round().astype(int).to_numpy()
    i = aqm["point_id"].map(pos).to_numpy()
    ok = (h >= 0) & (h < HOURS) & pd.notna(i)
    out[i[ok].astype(int), h[ok]] = aqm["value"].to_numpy(float)[ok]
    return out


def scale_to_daily(
    noaa: np.ndarray,
    start: datetime,
    offsets: np.ndarray,
    issue: datetime,
    daily: dict[int, np.ndarray],
) -> np.ndarray:
    """Scale each point's hourly values per local day so the day's mean equals ``daily[lead]``."""
    out = noaa.copy()
    hours_utc = np.array([start + timedelta(hours=k) for k in range(HOURS)])
    for p in range(noaa.shape[0]):
        local = [(hu + timedelta(hours=float(offsets[p]))).date() for hu in hours_utc]
        lead = np.array([(d - issue.date()).days for d in local])
        for L, target in daily.items():
            m = lead == L
            vals = noaa[p, m]
            good = np.isfinite(vals)
            if good.sum() < 6 or not np.isfinite(target[p]):
                continue
            mean = vals[good].mean()
            f = np.clip(target[p] / mean, *SCALE_BOUNDS) if mean > 0.5 else 1.0
            out[p, m] = vals * f
    return out


def wind(
    hrrr: pd.DataFrame, ids: list[str], start: datetime
) -> tuple[list, np.ndarray, np.ndarray]:
    """HRRR 10 m wind at the hours where it exists (every 3 h to 48 h)."""
    if hrrr.empty:
        return [], np.zeros((len(ids), 0)), np.zeros((len(ids), 0))
    w = hrrr[hrrr["var"].isin(["u10", "v10"])].copy()
    w["h"] = (
        (
            (pd.to_datetime(w["valid_utc"]).dt.tz_localize(None) - pd.Timestamp(start))
            / pd.Timedelta(hours=1)
        )
        .round()
        .astype(int)
    )
    w = w[(w["h"] >= 0) & (w["h"] < HOURS)]
    hours = sorted(w["h"].unique().tolist())
    pos = {k: i for i, k in enumerate(ids)}
    u, v = np.full((len(ids), len(hours)), np.nan), np.full((len(ids), len(hours)), np.nan)
    hpos = {h: j for j, h in enumerate(hours)}
    for var, arr in (("u10", u), ("v10", v)):
        s = w[w["var"] == var]
        i = s["point_id"].map(pos)
        ok = i.notna()
        arr[i[ok].astype(int).to_numpy(), s.loc[ok, "h"].map(hpos).to_numpy()] = s.loc[
            ok, "value"
        ].to_numpy(float)
    return hours, u, v


def fires(d) -> list[list[float]]:
    for back in (0, 1, 2):
        p = raw_dir("hms_fire") / f"{(d - timedelta(days=back)):%Y%m%d}.parquet"
        if p.exists():
            f = pd.read_parquet(p)
            f = f[f["method"].isin(["VIIRS", "MODIS"])] if "method" in f else f
            return [
                [round(float(a), 3), round(float(b), 3), round(float(c), 1)]
                for a, b, c in f[["latitude", "longitude", "frp"]].fillna(0).itertuples(index=False)
            ]
    return []


def ints(a) -> list:
    return [None if not np.isfinite(x) else round(x) for x in np.asarray(a, float).ravel()]


QUANTILE_COLUMNS = ("q05", "q25", "q50", "q75", "q95")
QUANTILE_LEVELS = (0.05, 0.25, 0.5, 0.75, 0.95)  # serein.models.gnn.QUANTILES
UNHEALTHY_SENSITIVE = 35.5  # daily PM2.5 at AQI 101, the level warnings are scored on


def default_run_dir(forecast: Path | None = None) -> Path:
    """The trained run whose settings belong with this forecast.

    A live forecast saves a record next to itself (``<date>.json``) naming the run that
    made it (``model_run``); that run is used, so the chance and flags always come from
    the same model as the forecast. Without a record, ``$SEREIN_LIVE_RUN`` is used, as in
    ``scripts/run_live.sh``, and then ``west_us_dev``."""
    if forecast is not None:
        try:
            info = json.loads(Path(forecast).with_suffix(".json").read_text(encoding="utf-8"))
        except (OSError, ValueError):
            info = None
        run = info.get("model_run") if isinstance(info, dict) else None
        if isinstance(run, str) and run.strip() and "/" not in run and "\\" not in run:
            return REPO_ROOT / "outputs" / "backtest" / run.strip()
    return REPO_ROOT / "outputs" / "backtest" / os.environ.get("SEREIN_LIVE_RUN", "west_us_dev")


def run_settings(run_dir: Path | None) -> dict:
    """Calibration-row settings saved with the trained model by the backtest:
    ``recal`` (prob_recal.json), ``cutoffs`` (warn_cutoffs.json), ``flag`` (flag_width.json).
    Files that are missing are left out."""
    if run_dir is None:
        return {}
    files = {"recal": "prob_recal.json", "cutoffs": "warn_cutoffs.json", "flag": "flag_width.json"}
    out = {}
    for key, name in files.items():
        path = Path(run_dir) / name
        if path.exists():
            out[key] = json.loads(path.read_text(encoding="utf-8"))
    return out


def percents(a) -> list:
    return [None if not np.isfinite(x) else round(100 * float(x)) for x in np.ravel(a)]


def flags(a) -> list:
    return [1 if x else 0 for x in np.ravel(a)]


def daily_outlooks(fc: pd.DataFrame, ids: list, settings: dict | None = None) -> list[dict]:
    """One entry per forecast day: median and 90% range for every point, plus, when the
    run's settings are given, ``p_usg`` (calibrated chance of a day at or above 35.5, in
    percent), ``warn`` (the backtest's warning rule, 0 or 1) and ``low_conf`` (the 10%
    widest intervals on calibration rows, 0 or 1)."""
    settings = settings or {}
    by_lead = {int(L): g.set_index("point_id").reindex(ids) for L, g in fc.groupby("lead")}
    has_all = all(c in fc.columns for c in QUANTILE_COLUMNS)
    days = []
    for L, g in sorted(by_lead.items()):
        dated = "valid_date" in g and g["valid_date"].notna().any()
        day = {
            "lead": L,
            "date": str(pd.Timestamp(g["valid_date"].dropna().iloc[0]).date()) if dated else None,
            "q05": ints(g["q05"].to_numpy(float)),
            "q50": ints(g["q50"].to_numpy(float)),
            "q95": ints(g["q95"].to_numpy(float)),
        }
        if has_all and settings:
            from serein.eval.backtest import prob_exceed

            q_log = np.log1p(np.clip(g[list(QUANTILE_COLUMNS)].to_numpy(float), 0, None))
            raw = prob_exceed(q_log, QUANTILE_LEVELS, thr=UNHEALTHY_SENSITIVE)
            known = np.isfinite(raw)
            recal = settings.get("recal", {}).get(str(L))
            if recal:
                p = np.full(len(raw), np.nan)
                p[known] = np.interp(raw[known], recal["x"], recal["y"])
                day["p_usg"] = percents(p)
            cut = settings.get("cutoffs", {}).get(str(L))
            if cut is not None:
                day["warn"] = flags(known & (np.nan_to_num(raw) >= float(cut)))
            limit = settings.get("flag", {}).get("log_width", {}).get(str(L))
            if limit is not None:
                width = q_log[:, -1] - q_log[:, 0]
                day["low_conf"] = flags(np.isfinite(width) & (np.nan_to_num(width) >= float(limit)))
        days.append(day)
    return days


def build(forecast: Path, store: str = "west_us", run_dir: Path | None = None) -> dict:
    fc = pd.read_parquet(forecast)
    issue = pd.Timestamp(fc["issue_date"].iloc[0]).to_pydatetime()
    start = datetime(
        issue.year, issue.month, issue.day, 19
    )  # first full hour after 18:30 UTC issue
    pts = fc.drop_duplicates("point_id").set_index("point_id")
    ids = pts.index.tolist()
    from serein.data.points import load_points

    reg = load_points(store).set_index("point_id")
    offsets = reg.reindex(ids)["gmt_offset"].fillna(-8).to_numpy(float)
    daily = {
        int(L): g.set_index("point_id").reindex(ids)["q50"].to_numpy(float)
        for L, g in fc.groupby("lead")
    }
    noaa = hourly_noaa(_cache(store, "aqm_bc", issue), ids, start)
    serein = scale_to_daily(noaa, start, offsets, issue, daily)
    w_hours, u, v = wind(_cache(store, "hrrr", issue), ids, start)
    # The tested forecast: SmokeCast's daily median and 90% range per point and local day,
    # with the calibrated chance and flags when the run's settings are available.
    days = daily_outlooks(fc, ids, run_settings(run_dir))

    def wind_ints(a):
        return [None if not np.isfinite(x) else round(float(x), 1) for x in a.ravel()]

    return {
        "issue_date": f"{issue:%Y-%m-%d}",
        "start_utc": start.isoformat() + "Z",
        "hours": HOURS,
        "source": (
            "Hourly shape: NOAA AQM bias-corrected PM2.5, 12z run of the issue day. Serein: same "
            "shape scaled per local day to Serein's daily median forecast. Wind: HRRR 10 m. "
            "Fires: NOAA HMS satellite fire detections."
        ),
        "points": [
            [
                round(float(pts.loc[k, "lat"]), 3),
                round(float(pts.loc[k, "lon"]), 3),
                1 if pts.loc[k, "kind"] == "epa" else 0,
            ]
            for k in ids
        ],
        "noaa": ints(noaa),
        "serein": ints(serein),
        "daily": days,
        "wind_hours": w_hours,
        "u": wind_ints(u),
        "v": wind_ints(v),
        "fires": fires(issue.date()),
    }


def main(argv=None):
    ap = argparse.ArgumentParser(
        description="Export the hour-by-hour smoke field for the 3D smoke world"
    )
    ap.add_argument(
        "--forecast", type=Path, required=True, help="daily forecast parquet (live or map)"
    )
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--store", default="west_us")
    ap.add_argument(
        "--run-dir", type=Path, default=None,
        help="trained run with prob_recal.json, warn_cutoffs.json and flag_width.json "
        "(default: the run named in the forecast's .json record, else "
        "outputs/backtest/$SEREIN_LIVE_RUN, else west_us_dev)",
    )
    ap.add_argument(
        "--daily-only", action="store_true",
        help="only replace the daily outlook in an existing --out file (same forecast run)",
    )
    args = ap.parse_args(argv)
    run_dir = args.run_dir or default_run_dir(args.forecast)
    print(f"calibration settings from {run_dir}")
    settings = run_settings(run_dir)
    missing = {"recal", "cutoffs", "flag"} - settings.keys()
    if missing:
        print(f"note: {', '.join(sorted(missing))} not found in {run_dir}; "
              "the matching daily values are left out")
    if args.daily_only:
        data = json.loads(args.out.read_text(encoding="utf-8"))
        fc = pd.read_parquet(args.forecast)
        issue = f"{pd.Timestamp(fc['issue_date'].iloc[0]):%Y-%m-%d}"
        if issue != data.get("issue_date"):
            raise SystemExit(
                f"{args.forecast} was issued {issue}; {args.out} is for {data.get('issue_date')}"
            )
        ids = fc.drop_duplicates("point_id")["point_id"].tolist()
        if len(ids) != len(data["points"]):
            raise SystemExit(f"{len(ids)} forecast points but {len(data['points'])} in {args.out}")
        data["daily"] = daily_outlooks(fc, ids, settings)
    else:
        data = build(args.forecast, args.store, run_dir)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    n = len(data["points"])
    extra = sorted({k for day in data["daily"] for k in day} & {"p_usg", "warn", "low_conf"})
    print(
        f"{n} points x {data['hours']} h, {len(data['wind_hours'])} wind hours, "
        f"{len(data['fires'])} fires, daily extras {extra or 'none'} -> {args.out} "
        f"({args.out.stat().st_size / 1e6:.1f} MB)"
    )


if __name__ == "__main__":
    main()
