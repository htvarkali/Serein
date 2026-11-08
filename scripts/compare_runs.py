"""Compare dev runs on IDENTICAL West monitor-days (B-17/B-18).

Runs trained on all of the US are scored on every US monitor; here we keep only the
West monitor-days that every run forecast, so each row of the table is a fair
comparison. CI = 95% day-block bootstrap of the RMSE difference vs. the baseline run
(negative = better than the baseline).

Usage: uv run python scripts/compare_runs.py [baseline_tag tag2 tag3 ...]
"""

from __future__ import annotations

import sys

import numpy as np
import pandas as pd

from serein.config import REPO_ROOT
from serein.eval.metrics import bootstrap_rmse_diff

OUT = REPO_ROOT / "outputs" / "backtest"
DEFAULT = ["west_us_scale_s", "west_us_scale_m", "west_us_scale_l", "west_us_hist4",
           "west_us_hist7", "conus_conus_s", "conus_conus_m", "conus_conus_l",
           "conus_conus_hist4"]
LEADS = [0, 1, 2, 3]


def main(tags: list[str]) -> None:
    west = pd.read_parquet(REPO_ROOT / "data" / "interim" / "west_us" / "points.parquet")
    west_ids = set(west.loc[west["kind"] == "epa", "point_id"])
    runs = {}
    for t in tags:
        p = OUT / t / "predictions.parquet"
        if p.exists():
            d = pd.read_parquet(p)
            runs[t] = d[d["point_id"].isin(west_ids)].set_index(["issue_date", "point_id"])
        else:
            print(f"(skipping {t}: no predictions)")
    if len(runs) < 2:
        sys.exit("need at least two finished runs")
    keys = None
    for d in runs.values():
        keys = d.index if keys is None else keys.intersection(d.index)
    base_tag = next(iter(runs))
    ref = runs[base_tag].loc[keys]
    rows = []
    for lead in LEADS:
        obs = ref[f"y_L{lead}"].to_numpy(float)
        smoke = (ref["hms_prev"].fillna(0) >= 1).to_numpy()
        dates = ref.index.get_level_values(0).to_numpy()
        b = ref[f"smokecast_L{lead}"].to_numpy(float)
        for t, d in runs.items():
            p = d.loc[keys, f"smokecast_L{lead}"].to_numpy(float)
            ok = np.isfinite(p) & np.isfinite(obs) & np.isfinite(b)
            rmse = float(np.sqrt(np.mean((p[ok] - obs[ok]) ** 2)))
            sm = ok & smoke
            rmse_s = float(np.sqrt(np.mean((p[sm] - obs[sm]) ** 2)))
            ci = bootstrap_rmse_diff(p[ok], b[ok], obs[ok], dates[ok]) if t != base_tag else {}
            rows.append({"lead": lead, "run": t, "n": int(ok.sum()), "rmse": rmse,
                         "rmse_smoke_days": rmse_s, "ci_lo": ci.get("ci_lo"), "ci_hi": ci.get("ci_hi")})
        noaa = ref[f"noaa_best_L{lead}"].to_numpy(float)
        ok = np.isfinite(noaa) & np.isfinite(obs) & np.isfinite(b)
        rows.append({"lead": lead, "run": "noaa_best", "n": int(ok.sum()),
                     "rmse": float(np.sqrt(np.mean((noaa[ok] - obs[ok]) ** 2))),
                     "rmse_smoke_days": float(np.sqrt(np.mean((noaa[ok & smoke] - obs[ok & smoke]) ** 2)))})
    res = pd.DataFrame(rows)
    out = REPO_ROOT / "outputs" / "backtest" / "compare_runs.csv"
    res.to_csv(out, index=False)
    print(f"{len(keys)} West monitor-days forecast by every run; baseline = {base_tag}\n")
    print("RMSE, all days (µg/m³)")
    print(res.pivot_table(index="run", columns="lead", values="rmse", sort=False).round(2).to_string())
    print("\nRMSE, smoke days (HMS plume overhead yesterday)")
    print(res.pivot_table(index="run", columns="lead", values="rmse_smoke_days", sort=False).round(2).to_string())
    ci = res.dropna(subset=["ci_lo"])
    if len(ci):
        print(f"\n95% CI of RMSE difference vs {base_tag} (both ends < 0 = clearly better)")
        print(ci.pivot_table(index="run", columns="lead", values=["ci_lo", "ci_hi"], sort=False)
              .round(2).to_string())
    print(f"\nwrote {out}")


if __name__ == "__main__":
    main(sys.argv[1:] or DEFAULT)
