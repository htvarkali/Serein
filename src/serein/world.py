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

    SEREIN_DATA=C:/Users/.../Serein/data uv run python -m serein.world \\
        --forecast outputs/live/west_us/forecasts/20261123.parquet --out website/assets/world/live.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

from serein.config import interim_dir, raw_dir

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


def build(forecast: Path, store: str = "west_us") -> dict:
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
    # The tested forecast: SmokeCast's daily median and 90% range per point and local day.
    by_lead = {int(L): g.set_index("point_id").reindex(ids) for L, g in fc.groupby("lead")}
    days = [
        {
            "lead": L,
            "date": str(pd.Timestamp(g["valid_date"].dropna().iloc[0]).date()) if "valid_date" in g and g["valid_date"].notna().any() else None,
            "q05": ints(g["q05"].to_numpy(float)),
            "q50": ints(g["q50"].to_numpy(float)),
            "q95": ints(g["q95"].to_numpy(float)),
        }
        for L, g in sorted(by_lead.items())
    ]

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
    args = ap.parse_args(argv)
    data = build(args.forecast, args.store)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    n = len(data["points"])
    print(
        f"{n} points x {data['hours']} h, {len(data['wind_hours'])} wind hours, "
        f"{len(data['fires'])} fires -> {args.out} ({args.out.stat().st_size / 1e6:.1f} MB)"
    )


if __name__ == "__main__":
    main()
