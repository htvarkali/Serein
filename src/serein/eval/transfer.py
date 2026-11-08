"""Out-of-region transfer test (TODO D-6): West-trained SmokeCast, applied unchanged
to another region (default: Northeast US, June 2023 Canadian smoke).

Nothing is re-fitted: the scaler, conformal calibration and network weights all
come from the West run. Northeast monitors have no West history, so their site
climatology is "missing", exactly like an unseen site during training (node masking).

    uv run serein build-table --config configs/northeast_2023.yaml --split test
    uv run serein transfer --run west_us_final --config configs/northeast_2023.yaml

This is a TEST. Run it once, after the final West run, and report it as is.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import torch

from serein.config import REPO_ROOT, Study
from serein.data.points import load_points
from serein.eval.metrics import bootstrap_rmse_diff, interval_metrics, point_metrics
from serein.features.graph import build_knn_graph
from serein.features.prepare import leads_of, to_graph_data
from serein.features.table import processed_dir
from serein.models.baselines import baselines
from serein.models.conformal import calibrate_quantiles
from serein.models.gnn import QUANTILES
from serein.models.infer import load_artifacts


def run_transfer(study: Study, run_dir: Path, split: str = "test", tag: str = "") -> pd.DataFrame:
    model, prep, cqr, _meta = load_artifacts(run_dir)
    tab = pd.read_parquet(processed_dir(study) / f"table_{split}.parquet")
    tab = tab[tab["kind"] == "epa"].reset_index(drop=True)
    leads = leads_of(tab)
    pts = load_points(study.name).set_index("point_id")
    nodes = sorted(n for n in tab["point_id"].unique() if n in pts.index)
    g = build_knn_graph(pts.loc[nodes, "lat"], pts.loc[nodes, "lon"],
                        k=study.raw["graph"]["k_neighbors"], max_km=study.raw["graph"]["max_km"])
    gd = to_graph_data(tab, prep, nodes)
    with torch.no_grad():
        q = model(torch.as_tensor(gd.X), torch.as_tensor(gd.wind), torch.as_tensor(gd.base),
                  torch.as_tensor(g.src), torch.as_tensor(g.dst),
                  torch.as_tensor(g.bearing, dtype=torch.float32),
                  torch.as_tensor(g.edge_attr)).numpy()
    rows_q = np.full((len(tab),) + q.shape[2:], np.nan, np.float32)
    t, n = np.where(gd.row_index >= 0)
    rows_q[gd.row_index[t, n]] = q[t, n]
    rows_q = calibrate_quantiles(rows_q, cqr, QUANTILES)
    pred = {"smokecast": np.expm1(rows_q[..., 2]), **baselines(tab, prep, leads)}
    obs = tab[[f"y_L{lead}" for lead in leads]].to_numpy(float)
    dates = tab["issue_date"].to_numpy()
    out = []
    for li, lead in enumerate(leads):
        valid_dates = pd.to_datetime(dates) + pd.Timedelta(days=lead)
        intervals = interval_metrics(np.expm1(rows_q[:, li, 0]),
                                     np.expm1(rows_q[:, li, -1]), obs[:, li])
        for m, p in pred.items():
            rec = {"lead": lead, "model": m, **point_metrics(p[:, li], obs[:, li], valid_dates)}
            if m == "smokecast":
                rec.update(intervals)
            elif np.isfinite(p[:, li]).any():
                rec.update({f"vs_smokecast_{k}": v for k, v in bootstrap_rmse_diff(
                    pred["smokecast"][:, li], p[:, li], obs[:, li], dates).items()})
            out.append(rec)
    res = pd.DataFrame(out)
    out_dir = REPO_ROOT / "outputs" / "transfer" / f"{study.name}_{tag or run_dir.name}"
    out_dir.mkdir(parents=True, exist_ok=True)
    res.to_csv(out_dir / "metrics.csv", index=False)
    keep = tab[["issue_date", "point_id"] + [f"y_L{lead}" for lead in leads]].copy()
    for m, p in pred.items():
        for li, lead in enumerate(leads):
            keep[f"{m}_L{lead}"] = p[:, li]
    keep.to_parquet(out_dir / "predictions.parquet", index=False)
    if "rmse" in res:
        print(res.pivot_table(index="model", columns="lead", values="rmse").round(2).to_string())
    else:
        print("No paired predictions and observations to score.")
    print(f"wrote {out_dir}")
    return res
