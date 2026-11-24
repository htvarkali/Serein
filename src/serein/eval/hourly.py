"""Hourly accuracy test for the Smoke World hour-by-hour field (task W-13).

Smoke World shows 72 hourly values per place: NOAA AQM's hourly shape scaled per local
day to SmokeCast's daily forecast (``serein.world``). SmokeCast itself is only tested on
daily means. This scores, against real hourly EPA readings at monitors, three hourly
forecasts made the day before each issue time:

- ``noaa``: NOAA AQM bias-corrected hourly PM2.5 (the raw shape);
- ``serein``: the same shape scaled per local day to SmokeCast's daily median (what the site shows);
- ``flat``: SmokeCast's daily median repeated for every hour of that day (no hourly shape).

The comparison ``serein`` vs. ``flat`` asks whether NOAA's hourly shape adds anything;
``serein`` vs. ``noaa`` asks whether the daily correction helps hour by hour. Development
data only (a run's predictions.parquet on 2023 weeks); never the test seasons.

    uv run python -m serein.eval.hourly outputs/backtest/west_us_dev --out outputs/hourly
"""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from serein.data.airnow import load_hourly
from serein.data.points import load_points
from serein.world import HOURS, _cache, hourly_noaa, scale_to_daily

METHODS = ("noaa", "serein", "flat", "profile")


def flat_daily(
    start: datetime, offsets: np.ndarray, issue: datetime, daily: dict[int, np.ndarray], n: int
) -> np.ndarray:
    out = np.full((n, HOURS), np.nan)
    hours = [start + timedelta(hours=k) for k in range(HOURS)]
    for p in range(n):
        lead = [
            ((h + timedelta(hours=float(offsets[p]))).date() - issue.date()).days for h in hours
        ]
        for k, L in enumerate(lead):
            if L in daily:
                out[p, k] = daily[L][p]
    return out


def observed(ids: list[str], start: datetime) -> np.ndarray:
    days = sorted({(start + timedelta(hours=k)).date() for k in range(HOURS)})
    h = load_hourly(days)
    out = np.full((len(ids), HOURS), np.nan)
    if h.empty:
        return out
    h = h[h["site_id"].isin(ids)]
    t = pd.to_datetime(h["time_utc"]).dt.tz_localize(None)
    k = ((t - pd.Timestamp(start)) / pd.Timedelta(hours=1)).round().astype(int).to_numpy()
    pos = {s: i for i, s in enumerate(ids)}
    i = h["site_id"].map(pos).to_numpy()
    ok = (k >= 0) & (k < HOURS)
    v = h["pm25"].to_numpy(float)
    out[i[ok].astype(int), k[ok]] = v[ok]
    return out


def lead_of_hour(start: datetime, offsets: np.ndarray, issue: datetime) -> np.ndarray:
    hours = [start + timedelta(hours=k) for k in range(HOURS)]
    return np.array(
        [
            [((h + timedelta(hours=float(o))).date() - issue.date()).days for h in hours]
            for o in offsets
        ]
    )


def diurnal_profiles(years: list[int], ids: list[str], offsets: np.ndarray) -> np.ndarray:
    """[points, 24] typical shape of each monitor's day in the fire season: median of
    hourly / local-day mean by local hour, from the given years. Flat (1.0) without history."""
    from datetime import date

    days = [date(y, 6, 1) + timedelta(days=k) for y in years for k in range(153)]
    h = load_hourly(days)
    prof = np.ones((len(ids), 24))
    if h.empty:
        return prof
    off = dict(zip(ids, offsets))
    h = h[h["site_id"].isin(ids) & np.isfinite(h["pm25"])].copy()
    t = pd.to_datetime(h["time_utc"]).dt.tz_localize(None) + pd.to_timedelta(
        h["site_id"].map(off), unit="h"
    )
    h["local_day"], h["local_hour"] = t.dt.date, t.dt.hour
    h = h[pd.to_datetime(h["local_day"]).dt.month.between(6, 10)]
    day_mean = h.groupby(["site_id", "local_day"])["pm25"].transform("mean").clip(lower=1.0)
    h["ratio"] = h["pm25"] / day_mean
    med = h.groupby(["site_id", "local_hour"])["ratio"].median().unstack()
    pos = {s: i for i, s in enumerate(ids)}
    for site, row in med.iterrows():
        v = row.reindex(range(24)).to_numpy(float)
        if np.isfinite(v).sum() >= 20:
            v = np.where(np.isfinite(v), v, np.nanmean(v))
            prof[pos[site]] = v / v.mean()
    return prof


def profile_forecast(
    start: datetime, offsets: np.ndarray, flat: np.ndarray, prof: np.ndarray
) -> np.ndarray:
    """SmokeCast's daily value spread over the hours by each monitor's typical daily shape."""
    out = flat.copy()
    for p in range(flat.shape[0]):
        local_hours = [(start + timedelta(hours=k + float(offsets[p]))).hour for k in range(HOURS)]
        out[p] = flat[p] * prof[p, local_hours]
    return out


def run(
    run_dir: Path,
    store: str = "west_us",
    max_days: int | None = None,
    profile_years: tuple[int, ...] = (2021, 2022),
) -> pd.DataFrame:
    pred = pd.read_parquet(run_dir / "predictions.parquet")
    reg = load_points(store).set_index("point_id")
    all_ids = sorted(pred["point_id"].unique())
    prof_all = diurnal_profiles(
        list(profile_years), all_ids, reg.reindex(all_ids)["gmt_offset"].fillna(-8).to_numpy(float)
    )
    prof_pos = {s: i for i, s in enumerate(all_ids)}
    rows = []
    days = sorted(pd.to_datetime(pred["issue_date"]).dt.date.unique())[:max_days]
    for d in days:
        g = pred[pd.to_datetime(pred["issue_date"]).dt.date == d]
        ids = g["point_id"].tolist()
        issue = datetime(d.year, d.month, d.day)
        start = issue + timedelta(hours=19)
        offsets = reg.reindex(ids)["gmt_offset"].fillna(-8).to_numpy(float)
        daily = {
            L: g[f"smokecast_L{L}"].to_numpy(float) for L in range(4) if f"smokecast_L{L}" in g
        }
        noaa = hourly_noaa(_cache(store, "aqm_bc", issue), ids, start)
        flat = flat_daily(start, offsets, issue, daily, len(ids))
        prof = prof_all[[prof_pos[s] for s in ids]]
        fc = {
            "noaa": noaa,
            "serein": scale_to_daily(noaa, start, offsets, issue, daily),
            "flat": flat,
            "profile": profile_forecast(start, offsets, flat, prof),
        }
        obs = observed(ids, start)
        leads = lead_of_hour(start, offsets, issue)
        # Score only hours where every method and the observation exist (identical rows).
        ok = np.isfinite(obs) & np.all([np.isfinite(f) for f in fc.values()], axis=0)
        for L in range(4):
            m = ok & (leads == L)
            if not m.any():
                continue
            row = {"issue_date": d, "lead": L, "n": int(m.sum())}
            for name, f in fc.items():
                row[f"sse_{name}"] = float(((f[m] - obs[m]) ** 2).sum())
            # Shape skill: within each place-day, does the forecast's hour-to-hour pattern follow the observed one?
            for name in ("noaa", "serein", "profile"):
                fa, oa = (
                    fc[name] - np.nanmean(np.where(m, fc[name], np.nan), axis=1, keepdims=True),
                    obs - np.nanmean(np.where(m, obs, np.nan), axis=1, keepdims=True),
                )
                row[f"shape_num_{name}"] = float(np.nansum(np.where(m, fa * oa, 0)))
                row[f"shape_den_f_{name}"] = float(np.nansum(np.where(m, fa**2, 0)))
            row["shape_den_o"] = float(np.nansum(np.where(m, oa**2, 0)))
            rows.append(row)
    return pd.DataFrame(rows)


def summarize(day_rows: pd.DataFrame, n_boot: int = 1000, seed: int = 0) -> pd.DataFrame:
    """RMSE per lead and method; day-block bootstrap of RMSE differences (resampling issue days)."""
    rng = np.random.default_rng(seed)
    out = []
    for L, g in day_rows.groupby("lead"):
        n = g["n"].to_numpy(float)
        rec = {"lead": int(L), "hours": int(n.sum())}
        sse = {m: g[f"sse_{m}"].to_numpy(float) for m in METHODS}
        for m in METHODS:
            rec[f"rmse_{m}"] = float(np.sqrt(sse[m].sum() / n.sum()))
        for a, b in (("serein", "noaa"), ("serein", "flat"), ("profile", "flat"), ("profile", "noaa")):
            diffs = []
            for _ in range(n_boot):
                k = rng.integers(0, len(g), len(g))
                diffs.append(
                    np.sqrt(sse[a][k].sum() / n[k].sum()) - np.sqrt(sse[b][k].sum() / n[k].sum())
                )
            lo, hi = np.percentile(diffs, [2.5, 97.5])
            rec[f"{a}_minus_{b}"] = rec[f"rmse_{a}"] - rec[f"rmse_{b}"]
            rec[f"{a}_minus_{b}_ci"] = f"({lo:+.2f}, {hi:+.2f})"
        for m in ("noaa", "serein", "profile"):
            den = np.sqrt(g[f"shape_den_f_{m}"].sum() * g["shape_den_o"].sum())
            rec[f"shape_corr_{m}"] = float(g[f"shape_num_{m}"].sum() / den) if den > 0 else np.nan
        out.append(rec)
    return pd.DataFrame(out)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Hourly accuracy of the Smoke World field")
    ap.add_argument("run", type=Path)
    ap.add_argument("--out", type=Path, default=Path("outputs/hourly"))
    ap.add_argument("--max-days", type=int, default=None)
    args = ap.parse_args(argv)
    if (args.run / "FINAL_RUN_LOCK.json").exists():
        raise SystemExit("Refusing a final-test run: this check is for development data only.")
    # Daily shapes only from seasons before the scored one (2021-22 for 2023; 2021 for the 2022 inner fold).
    years = (2021,) if "inner" in args.run.name else (2021, 2022)
    rows = run(args.run, max_days=args.max_days, profile_years=years)
    args.out.mkdir(parents=True, exist_ok=True)
    rows.to_csv(args.out / "by_day.csv", index=False)
    s = summarize(rows)
    s.to_csv(args.out / "summary.csv", index=False)
    print(s.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
