"""Live forecasts: run SmokeCast every day on today's real data, then score it later.

This is the prospective test. A forecast is saved BEFORE the days it predicts have
happened, with the time it was made. Days later, once the monitors have reported,
``score`` compares it with what really happened, and with NOAA's forecast for the
same places and days.

Example (run at 11:45 AM Pacific on 2026-11-03):
  serein live            -> outputs/live/forecasts/20261103.parquet (+ map)
                            and re-scores every older forecast that can be scored now.

Rules (same as the backtest, see docs/BACKTEST_PROTOCOL.md):
  * inputs obey the issue-time rules in serein.data.availability (issue 18:30 UTC);
  * a forecast file is never edited after it is written; a re-run for the same day
    is refused unless --force, and the scoreboard only counts the first version;
  * every monitor-day that has a forecast is scored, smoke or not.
"""

from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import torch

from serein.aqi import pm25_to_category
from serein.config import REPO_ROOT, Study
from serein.data import airnow, aqm, hms, hrrr
from serein.data.availability import Availability
from serein.data.points import load_points
from serein.eval.backtest import _git_rev, compare_with_epa, prob_exceed
from serein.features.daily import obs_daily_means
from serein.models.baselines import baselines
from serein.models.gnn import QUANTILES
from serein.models.infer import build_inputs, plot_map

# SEREIN_LIVE moves the live folder (tests use a scratch folder, never the real record).
LIVE = Path(os.environ.get("SEREIN_LIVE", REPO_ROOT / "outputs" / "live"))
ON_TIME_HOURS = 6  # a forecast made more than 6 h after issue time is not counted
MODELS = ["smokecast", "noaa_best", "aqm_bc", "persistence"]


def live_dir(study: Study, sub: str):
    p = LIVE / study.name / sub
    p.mkdir(parents=True, exist_ok=True)
    return p


def warn_cutoffs(run_dir) -> dict[int, float]:
    """Warning cut-offs P(PM2.5 >= 35.5) tuned on calibration days in the backtest."""
    j = run_dir / "warn_cutoffs.json"
    if j.exists():
        return {int(k): float(v) for k, v in json.loads(j.read_text()).items()}
    m = re.search(r"cut-offs P\(>=35\.5\) tuned on calibration: (\{.*\})",
                  (run_dir / "report.md").read_text(encoding="utf-8"))
    if not m:
        raise FileNotFoundError(f"No warning cut-offs in {run_dir}")
    return {int(k): float(v) for k, v in re.findall(r"(\d+): ([0-9.]+)", m.group(1))}


# ------------------------------------------------------------------------ inputs
def fetch_inputs(study: Study, d: date, log=print) -> dict:
    """Download everything the issue-time rules allow for issue day d."""
    av = Availability.from_study(study.raw)
    pts = load_points(study.name)
    recent = date.today() - timedelta(days=2)
    for k in range(-4, 1):
        airnow.download_hourly_day(d + timedelta(days=k))
    # EPA's own forecast issued on d (re-fetched at scoring time, when the day is over).
    airnow.download_reportingarea_day(d, overwrite=d >= recent)
    hd = av.hms_day(d)
    hms.download_day(hd, overwrite=hd >= recent)
    for fd in (d - timedelta(days=1), d):
        hms.download_fire_day(fd, overwrite=fd >= recent)
    h = study.raw["hrrr"]
    got_h = hrrr.extract_cycle(d, pts, cycle=av.hrrr_cycle, max_fhr=h["max_fhr"],
                               smoke_every=h["smoke_every"], met_every=h["met_every"],
                               met_vars=h["met_vars"], store=study.name)
    got_a = aqm.extract_cycle(d, pts, cycle=av.aqm_cycle, store=study.name)
    status = {"hrrr": got_h is not None, "aqm": got_a is not None}
    log(f"inputs for {d}: HRRR {'ok' if status['hrrr'] else 'MISSING'}, "
        f"AQM {'ok' if status['aqm'] else 'MISSING'}")
    return status


# ---------------------------------------------------------------------- forecast
def make_forecast(study: Study, d: date, run: str = "west_us_dev", force: bool = False,
                  allow_missing: bool = False, log=print):
    out = live_dir(study, "forecasts") / f"{d:%Y%m%d}.parquet"
    if out.exists() and not force:
        log(f"forecast for {d} already exists ({out}); not overwriting")
        return None
    now = datetime.now(UTC)
    issue = Availability.from_study(study.raw).issue_time(d).replace(tzinfo=UTC)
    if now < issue and not force:
        raise SystemExit(f"Too early: issue time is {issue:%H:%M} UTC on {d} "
                         f"(NOAA's AQM run is posted ~18:05 UTC). Now {now:%H:%M} UTC.")
    status = fetch_inputs(study, d, log)
    if not all(status.values()) and not allow_missing:
        raise SystemExit("A NOAA input is missing; try again later (or --allow-missing).")

    run_dir = REPO_ROOT / "outputs" / "backtest" / run
    inp = build_inputs(study, d, run_dir, with_grid=True)
    with torch.no_grad():
        q = inp.run()[0].numpy()
    lo, hi = inp.cqr.apply(q[..., 0], q[..., -1], q[..., 2])
    q[..., 0], q[..., -1] = np.minimum(lo, q[..., 2]), np.maximum(hi, q[..., 2])
    base = baselines(inp.tab, inp.prep, inp.leads)
    cuts = warn_cutoffs(run_dir)
    kinds = inp.use.set_index("point_id").loc[inp.tab["point_id"], "kind"].to_numpy()
    rows = []
    for li, lead in enumerate(inp.leads):
        valid = d + timedelta(days=lead)
        med = np.expm1(q[:, li, 2])
        pex = prob_exceed(q[:, li], QUANTILES)
        rows.append(pd.DataFrame({
            "point_id": inp.tab["point_id"], "kind": kinds,
            "lat": inp.tab["lat"], "lon": inp.tab["lon"],
            "issue_date": d, "lead": lead, "valid_date": valid,
            **{f"q{int(100 * lv):02d}": np.expm1(q[:, li, j]) for j, lv in enumerate(QUANTILES)},
            "smokecast": med, "p_usg": pex, "warn": pex >= cuts[lead],
            "aqi_cat": pm25_to_category(med, valid),
            **{m: base[m][:, li] for m in MODELS if m in base},
        }))
    fc = pd.concat(rows, ignore_index=True)
    on_time = now <= issue + timedelta(hours=ON_TIME_HOURS)
    fc["on_time"] = on_time
    fc.to_parquet(out, index=False)
    meta = {"issue_date": str(d), "made_at_utc": now.isoformat(timespec="seconds"),
            "issue_time_utc": issue.isoformat(), "model_run": run,
            "code_version": _git_rev(), "inputs": status, "on_time": bool(on_time),
            "n_monitors": int((fc["kind"] == "epa").sum() / len(inp.leads))}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=1))
    # Fingerprint log: once these lines are committed (or posted anywhere public), the
    # commit time proves each forecast existed before its days happened.
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    with open(LIVE / study.name / "forecast_hashes.txt", "a", encoding="utf-8") as fh:
        fh.write(f"{d:%Y-%m-%d}  made {meta['made_at_utc']}  sha256 {digest}  {out.name}\n")
    png = live_dir(study, "maps") / f"map_{d:%Y%m%d}.png"
    plot_map(fc, png, title=f"SmokeCast live forecast issued {d} 18:30 UTC "
                            "(squares = map grid, dots = monitors)")
    log(f"wrote {out} and {png}")
    return fc


# ----------------------------------------------------------------------- scoring
def _observed(study: Study, valid_days: list[date], pts: pd.DataFrame) -> pd.DataFrame:
    """Observed local-day mean PM2.5 per monitor, only for days that are complete."""
    need = sorted({v + timedelta(days=k) for v in valid_days for k in (-1, 0, 1)})
    for v in need:
        if v < date.today():
            airnow.download_hourly_day(v)
    offsets = pts.set_index("point_id")["gmt_offset"]
    hourly = airnow.load_hourly(valid_days)
    if hourly.empty:
        return pd.DataFrame(columns=["point_id", "valid_date", "obs"])
    daily = obs_daily_means(hourly, offsets)
    return daily.rename(columns={"local_date": "valid_date", "pm25_daily": "obs"})[
        ["point_id", "valid_date", "obs"]]


def score(study: Study, log=print) -> pd.DataFrame:
    """Score every saved forecast whose days have been observed. Writes the scoreboard."""
    files = sorted(live_dir(study, "forecasts").glob("*.parquet"))
    if not files:
        log("no live forecasts yet")
        return pd.DataFrame()
    pts = load_points(study.name)
    fc = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)
    late = int((~fc["on_time"]).sum()) if "on_time" in fc else 0
    fc = fc[(fc["kind"] == "epa") & fc.get("on_time", True)]
    if late:
        log(f"({late} rows from late forecasts are not counted)")
    # A local day is complete once the next UTC day has started everywhere (+ slack).
    last_ok = (datetime.now(UTC) - timedelta(hours=14)).date() - timedelta(days=1)
    fc = fc[pd.to_datetime(fc["valid_date"]).dt.date <= last_ok].copy()
    if fc.empty:
        log("no forecast day is complete yet")
        _write_board(study, pd.DataFrame(), pd.DataFrame(), len(files))
        return pd.DataFrame()
    fc["valid_date"] = pd.to_datetime(fc["valid_date"]).dt.date
    fc["issue_date"] = pd.to_datetime(fc["issue_date"]).dt.date
    obs = _observed(study, sorted(fc["valid_date"].unique()), pts)
    s = fc.merge(obs, on=["point_id", "valid_date"], how="inner").dropna(subset=["obs"])
    s.to_parquet(LIVE / study.name / "scored.parquet", index=False)

    # Official EPA category forecasts, on the same reporting areas and days.
    epa = pd.DataFrame()
    days = sorted(s["issue_date"].unique())
    for d in days:
        airnow.download_reportingarea_day(d, overwrite=True)
        airnow.download_reportingarea_day(d + timedelta(days=1), overwrite=d >= last_ok - timedelta(days=4))
    wide = fc.pivot_table(index=["issue_date", "point_id"], columns="lead",
                          values=["smokecast", "warn"], aggfunc="first").reset_index()
    leads = sorted(fc["lead"].unique())
    try:
        epa = compare_with_epa(study, wide[["issue_date", "point_id"]],
                               wide["smokecast"][leads].to_numpy(float),
                               leads, pts.set_index("point_id"),
                               wide["warn"][leads].fillna(False).to_numpy(bool))
    except Exception as e:  # noqa: BLE001 - the scoreboard still works without it
        log(f"EPA comparison skipped: {e}")
    _write_board(study, s, epa, len(files))
    return s


def summarize(s: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for lead, g in s.groupby("lead"):
        rec = {"lead": int(lead), "monitor_days": len(g), "issue_days": g["issue_date"].nunique()}
        for m in MODELS:
            ok = g[m].notna()
            rec[f"rmse_{m}"] = float(np.sqrt(((g.loc[ok, m] - g.loc[ok, "obs"]) ** 2).mean()))
        both = g["noaa_best"].notna()
        e_s = ((g.loc[both, "smokecast"] - g.loc[both, "obs"]) ** 2).mean()
        e_n = ((g.loc[both, "noaa_best"] - g.loc[both, "obs"]) ** 2).mean()
        rec["skill_vs_noaa"] = float(1 - np.sqrt(e_s / e_n)) if e_n > 0 else np.nan
        usg = g["obs"] >= 35.5
        rec["usg_days"] = int(usg.sum())
        rec["usg_caught"] = int((usg & g["warn"]).sum())
        rec["false_alarms"] = int((~usg & g["warn"]).sum())
        rec["noaa_caught"] = int((usg & (g["noaa_best"] >= 35.5)).sum())
        rec["noaa_false_alarms"] = int((~usg & (g["noaa_best"] >= 35.5)).sum())
        rows.append(rec)
    return pd.DataFrame(rows)


def _write_board(study: Study, s: pd.DataFrame, epa: pd.DataFrame, n_files: int) -> None:
    lines = [f"# SmokeCast live scoreboard ({study.name})", "",
             (f"Updated {datetime.now():%Y-%m-%d %H:%M} local. Forecasts saved: {n_files}. "
              "Each forecast is written before the days it predicts and never edited."), ""]
    if s.empty:
        lines.append("Nothing to score yet: the first forecast days have not finished.")
    else:
        t = summarize(s)
        t.to_csv(LIVE / study.name / "scoreboard.csv", index=False)
        lines += ["Error (RMSE, µg/m³, lower is better) on every monitor-day observed so far.",
                  "skill = how much smaller SmokeCast's error is than NOAA's best forecast.", "",
                  "| lead | monitor-days | SmokeCast | NOAA best | NOAA AQM | yesterday's value | skill vs NOAA | unhealthy days | caught (SmokeCast / NOAA) | false alarms (SmokeCast / NOAA) |",
                  "|---|---|---|---|---|---|---|---|---|---|"]
        for r in t.itertuples():
            lines.append(f"| {r.lead} | {r.monitor_days} | {r.rmse_smokecast:.2f} | "
                         f"{r.rmse_noaa_best:.2f} | {r.rmse_aqm_bc:.2f} | {r.rmse_persistence:.2f} | "
                         f"{100 * r.skill_vs_noaa:+.0f}% | {r.usg_days} | "
                         f"{r.usg_caught} / {r.noaa_caught} | {r.false_alarms} / {r.noaa_false_alarms} |")
        if len(epa):
            lines += ["", "Official EPA AQI forecasts, same reporting areas and days:", "",
                      "```", epa.round(3).to_string(index=False), "```"]
        lines += ["", ("Caveat: the model was trained on June-October fire seasons only. "
                       "Winter days (wood smoke, inversions) are outside what it learned.")]
    (LIVE / study.name / "SCOREBOARD.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
