"""Backtest: train -> calibrate -> score, with the same rows for every model.

Two modes
  dev   (default)  score on half of the calibration season. Use this while building.
  final (--final)  score on the TEST seasons. Do this ONCE (see BACKTEST_PROTOCOL.md);
                   a lock file records when it was run and on which code version.

Splitting the calibration season by ISO week:
  even weeks -> early stopping;  odd weeks -> conformal calibration (final) / scoring (dev)
"""

from __future__ import annotations

import json
import subprocess
import warnings
from datetime import datetime

import numpy as np
import pandas as pd

from serein.aqi import pm25_to_category
from serein.config import REPO_ROOT, Study
from serein.data.airnow import load_forecasts, load_observed_area_aqi
from serein.data.points import load_points
from serein.eval.metrics import (
    bootstrap_rmse_diff,
    crps_from_quantiles,
    interval_metrics,
    point_metrics,
)
from serein.features.graph import build_knn_graph, idw_neighbor_mean
from serein.features.prepare import (
    Prep,
    history_from,
    is_sensor_feature,
    leads_of,
    neighbor_base,
    to_graph_data,
)
from serein.features.table import processed_dir
from serein.models.baselines import baselines
from serein.models.conformal import CQR, calibrate_quantiles
from serein.models.gbm import GBM_QUANTILES, QuantileGBM
from serein.models.gnn import QUANTILES
from serein.models.train import TrainConfig, Trainer


def _load(study: Study, name: str) -> pd.DataFrame:
    p = processed_dir(study) / f"table_{name}.parquet"
    if not p.exists():
        raise FileNotFoundError(f"{p} missing. Run `serein build-table --split {name}`.")
    df = pd.read_parquet(p)
    return df[df["kind"] == "epa"].reset_index(drop=True)


def _week_parity(df):
    return pd.to_datetime(df["issue_date"]).dt.isocalendar().week.to_numpy() % 2


def _git(*cmd) -> str:
    return subprocess.check_output(["git", *cmd], cwd=REPO_ROOT, text=True,
                                   stderr=subprocess.DEVNULL).strip()


def _code_is_dirty() -> bool:
    """True if tracked code or configs differ from the last commit."""
    try:
        return bool(_git("status", "--porcelain", "--untracked-files=no", "--",
                         "src", "configs", "scripts", "pyproject.toml", "uv.lock"))
    except Exception:  # noqa: BLE001
        return True


def _git_rev() -> str:
    try:
        rev = _git("rev-parse", "--short", "HEAD")
    except Exception:  # noqa: BLE001
        return "unknown"
    return rev + (" + uncommitted changes" if _code_is_dirty() else "")


def _rows_from_graph(q_tn: np.ndarray, gd, n_rows: int) -> np.ndarray:
    """[T,N,L,Q] -> [rows,L,Q] aligned with the source table."""
    out = np.full((n_rows,) + q_tn.shape[2:], np.nan, np.float32)
    t, n = np.where(gd.row_index >= 0)
    out[gd.row_index[t, n]] = q_tn[t, n]
    return out


def _gbm_features(df, X, g, node_ids):
    """Add IDW neighbor means of recent observations to the flat feature matrix."""
    days = sorted(df["issue_date"].unique())
    extra = []
    for col in ["obs_last3", "obs_last24", "obs_prevday"]:
        # pivot drops all-NaN days, so reindex to every day explicitly
        wide = df.pivot_table(index="issue_date", columns="point_id", values=col,
                              dropna=False).reindex(index=days, columns=node_ids)
        nb = idw_neighbor_mean(np.log1p(wide.clip(lower=0).to_numpy()), g)
        long = pd.DataFrame(nb, index=days, columns=node_ids).stack(future_stack=True)
        long.index.names = ["issue_date", "point_id"]
        keys = pd.MultiIndex.from_arrays([df["issue_date"], df["point_id"]])
        v = long.reindex(keys).to_numpy(dtype=np.float32, na_value=np.nan)
        extra += [np.nan_to_num(v), (~np.isfinite(v)).astype(np.float32)]
    return np.concatenate([X, np.stack(extra, 1)], 1)


def prob_exceed(q_log: np.ndarray, levels, thr: float = 35.5) -> np.ndarray:
    """P(daily PM2.5 >= thr) from predicted quantiles [rows, Q] (log1p space).

    Linear interpolation of the CDF between quantiles; beyond the outer
    quantiles we use half the tail mass (e.g. 2.5% beyond the 5% quantile).
    """
    t = np.log1p(thr)
    lv = np.asarray(levels, float)
    q = np.asarray(q_log, float)
    out = np.full(len(q), np.nan)
    ok = np.all(np.isfinite(q), axis=1)
    if not ok.any():
        return out
    q = q[ok]
    # Same as np.interp(t, q_row, lv, left=..., right=...) for every row at once.
    k = np.clip((q <= t).sum(1), 1, q.shape[1] - 1)   # q[k-1] <= t < q[k]
    r = np.arange(len(q))
    x0, x1 = q[r, k - 1], q[r, k]
    with np.errstate(divide="ignore", invalid="ignore"):
        frac = np.where(x1 > x0, (t - x0) / (x1 - x0), 1.0)
    cdf = lv[k - 1] + np.clip(frac, 0, 1) * (lv[k] - lv[k - 1])
    cdf = np.where(t < q[:, 0], lv[0] / 2, cdf)
    cdf = np.where(t > q[:, -1], 1 - (1 - lv[-1]) / 2, cdf)
    out[ok] = 1 - cdf
    return out


def tune_warning_threshold(p_exceed: np.ndarray, obs: np.ndarray, thr: float = 35.5) -> float:
    """Pick the probability cut-off that maximizes CSI on calibration data."""
    ok = np.isfinite(p_exceed) & np.isfinite(obs)
    p, o = p_exceed[ok], obs[ok] >= thr
    best, best_csi = 0.5, -1.0
    for c in np.arange(0.05, 0.81, 0.025):
        w = p >= c
        hit, miss, fa = np.sum(w & o), np.sum(~w & o), np.sum(w & ~o)
        csi = hit / (hit + miss + fa) if hit + miss + fa else 0
        if csi > best_csi:
            best, best_csi = float(c), csi
    return best


def warning_scores(warn: np.ndarray, obs: np.ndarray, thr: float = 35.5) -> dict:
    ok = np.isfinite(obs) & np.isfinite(warn.astype(float))
    w, o = warn[ok].astype(bool), obs[ok] >= thr
    hit, miss, fa = np.sum(w & o), np.sum(~w & o), np.sum(w & ~o)
    return {"usg_events": int(hit + miss),
            "usg_pod": hit / (hit + miss) if hit + miss else np.nan,
            "usg_far": fa / (hit + fa) if hit + fa else np.nan,
            "usg_csi": hit / (hit + miss + fa) if hit + miss + fa else np.nan}


def run_backtest(study: Study, args) -> dict:
    final = bool(getattr(args, "final", False))
    tag = args.tag or ("final" if final else "dev")
    out_dir = REPO_ROOT / "outputs" / "backtest" / f"{study.name}_{tag}"
    out_dir.mkdir(parents=True, exist_ok=True)
    log_lines = []

    def log(s=""):
        print(s)
        log_lines.append(s)

    train = _load(study, args.train)
    cal = _load(study, args.calibrate)
    # Ablations (B-10): remove whole input groups by column prefix, e.g. "aqm_,hrrr_".
    drop = [p for p in (getattr(args, "drop", "") or "").split(",") if p]
    # (Inputs are hidden from the model via Prep(exclude=...); the table keeps every
    # column so baselines, smoke-day subsets and scoring are unchanged.)
    par = _week_parity(cal)
    val = cal[par == 0].reset_index(drop=True)
    conf = cal[par == 1].reset_index(drop=True)
    if final:
        test = _load(study, args.test)
        lock = out_dir / "FINAL_RUN_LOCK.json"
        if lock.exists() and not getattr(args, "force", False):
            raise SystemExit(f"Final test already run ({lock}). Re-running needs --force and "
                             "a note in docs/BACKTEST_PROTOCOL.md explaining why.")
        if _code_is_dirty():
            # The commit is the proof of what was run: no final test on unsaved code.
            raise SystemExit("Commit (and push) the code before the final test: src/, configs/, "
                             "scripts/ or the lock files have uncommitted changes.")
    else:
        test = conf  # dev mode: score on odd weeks of the calibration season
        conf = val   # ...and calibrate intervals on the even weeks

    leads = leads_of(train)
    log(f"# Serein backtest ({'FINAL' if final else 'dev'}) - {datetime.now():%Y-%m-%d %H:%M}")
    log(f"code version: {_git_rev()}")
    log(f"rows: train {len(train)}, val {len(val)}, conf {len(conf)}, test {len(test)}; leads {leads}")

    pts = load_points(study.name).set_index("point_id")
    node_ids = sorted(set(train["point_id"]) | set(val["point_id"]) | set(test["point_id"])
                      | set(conf["point_id"]))
    node_ids = [n for n in node_ids if n in pts.index]
    g = build_knn_graph(pts.loc[node_ids, "lat"], pts.loc[node_ids, "lon"],
                        k=study.raw["graph"]["k_neighbors"], max_km=study.raw["graph"]["max_km"])
    log(f"graph: {len(node_ids)} nodes, {g.n_edges} edges")

    prep = Prep(exclude=tuple(drop),
                use_obs_base=not any(p.startswith("obs_") for p in drop)).fit(train)
    gds = {k: to_graph_data(v, prep, node_ids)
           for k, v in {"train": train, "val": val, "conf": conf, "test": test}.items()}
    F = gds["train"].X.shape[2]
    log(f"features: {F}")
    if drop:
        log(f"ablation: dropped input groups {drop}")
    if getattr(args, "no_wind", False):
        for gd in gds.values():
            gd.wind[:] = 0.0  # message passing loses its wind-direction information
        log("ablation: wind removed from graph edges")

    # Leave-sites-out (B-7b): hide some monitors completely. Their targets are removed
    # from training and their readings/history are hidden everywhere, so the model must
    # forecast them from neighbors and NOAA inputs alone, like a neighborhood without
    # a sensor.
    holdout = np.zeros(len(node_ids), bool)
    frac = float(getattr(args, "holdout_sites", 0.0) or 0.0)
    names = gds["train"].feat_names
    val_cols = [i for i, n in enumerate(names) if is_sensor_feature(n) and not n.endswith("__missing")]
    flag_cols = [i for i, n in enumerate(names) if is_sensor_feature(n) and n.endswith("__missing")]

    def hide_holdout(X):
        sub = X[:, holdout]
        sub[..., val_cols] = 0.0
        sub[..., flag_cols] = 1.0
        X[:, holdout] = sub

    if frac > 0:
        rng = np.random.default_rng(1234)
        holdout[rng.choice(len(node_ids), round(frac * len(node_ids)), replace=False)] = True
        for gd in gds.values():
            hide_holdout(gd.X)
        gds["train"].Y[:, holdout] = np.nan
        log(f"leave-sites-out: {holdout.sum()} of {len(node_ids)} monitors hidden")

    # Memory of past days (B-18): each day also gets the inputs of the K-1 days before
    # it, taken from all seasons loaded (inputs only, never targets).
    history = int(getattr(args, "history", 1) or 1)
    if history > 1:
        parts = [train, cal] + ([test] if final else [])
        full = to_graph_data(pd.concat(parts, ignore_index=True), prep, node_ids)
        if holdout.any():
            hide_holdout(full.X)
        for gd in gds.values():
            gd.hist = history_from(full, gd.days, history)
        del full
        log(f"history: each sensor reads its last {history} days of inputs")

    # Base forecast without a node's own readings (neighbors' readings instead): used
    # for sensors hidden by node masking in training and for hidden monitors.
    # Hidden monitors never share readings with neighbors (sources=~holdout).
    srcs = {"train": train, "val": val, "conf": conf, "test": test}
    for k, gd in gds.items():
        gd.base_nbr = neighbor_base(gd, srcs[k], prep, g, sources=~holdout)
        if holdout.any():
            gd.base[:, holdout] = gd.base_nbr[:, holdout]

    preds_q: dict[str, np.ndarray] = {}   # model -> [rows, L, Q] log1p
    levels: dict[str, tuple] = {}

    # ---- SmokeCast GNN (+ no-graph ablation) ---------------------------------
    variants = [("smokecast", True)]
    if not getattr(args, "no_ablation", False):
        variants.append(("smokecast_nograph", False))
    cqr_store = {}
    for name, use_graph in variants:
        # Both variants get the same ensemble size for a fair graph ablation.
        n_seeds = max(1, int(getattr(args, "seeds", 1)))
        qc_list, qt_list, states, first_cfg = [], [], [], None
        for k in range(n_seeds):
            cfg = TrainConfig(epochs=args.epochs, seed=args.seed + k, use_graph=use_graph,
                              node_mask_frac=getattr(args, "node_mask", 0.15),
                              hidden=getattr(args, "hidden", 96),
                              layers=getattr(args, "layers", 3),
                              dropout=getattr(args, "dropout", 0.1),
                              weight_decay=getattr(args, "weight_decay", 1e-4),
                              lr=getattr(args, "lr", 2e-3),
                              smoke_weight=getattr(args, "smoke_weight", 1.0),
                              history=history)
            log(f"\n## training {name} (seed {args.seed + k})")
            tr = Trainer(F, len(leads), g, gds["train"].feat_names, cfg)
            tr.fit(gds["train"], gds["val"], log=log)
            qc_list.append(_rows_from_graph(tr.predict(gds["conf"]), gds["conf"], len(conf)))
            qt_list.append(_rows_from_graph(tr.predict(gds["test"]), gds["test"], len(test)))
            if name == "smokecast":
                states.append({key: value.detach().cpu().clone()
                               for key, value in tr.model.state_dict().items()})
            first_cfg = first_cfg or cfg
        # Ensemble = average of each quantile across seeds (log space), then calibrate.
        q_conf, q_test = np.mean(qc_list, 0), np.mean(qt_list, 0)
        cfg = first_cfg
        y_conf = prep.targets(conf)
        cqr = CQR(alpha=0.10).fit(q_conf[..., 0], q_conf[..., -1], q_conf[..., 2], y_conf)
        q_test = calibrate_quantiles(q_test, cqr, QUANTILES)
        if name == "smokecast":
            q_conf_cal = calibrate_quantiles(q_conf, cqr, QUANTILES)
        preds_q[name], levels[name] = q_test, QUANTILES
        cqr_store[name] = {f"{k[0]}_{k[1]}": v for k, v in cqr.qhat.items()}
        if name == "smokecast":
            from serein.models.infer import save_artifacts
            save_artifacts(out_dir, prep, node_ids, F, leads, cfg, cqr, states,
                           seeds=[args.seed + k for k in range(n_seeds)])

    # ---- Gradient boosting (no graph learning) ------------------------------
    if holdout.any() and not getattr(args, "no_gbm", False):
        log("(gbm skipped in leave-sites-out mode: its neighbor features would see hidden sites)")
    if not getattr(args, "no_gbm", False) and not holdout.any():
        log("\n## training gbm")
        Xtr, _ = prep.transform(train)
        Xte, _ = prep.transform(test)
        Xcf, _ = prep.transform(conf)
        Xtr, Xte, Xcf = (_gbm_features(d, x, g, node_ids)
                         for d, x in ((train, Xtr), (test, Xte), (conf, Xcf)))
        btr, bte, bcf = prep.base(train, leads), prep.base(test, leads), prep.base(conf, leads)
        gbm = QuantileGBM(seed=args.seed).fit(Xtr, prep.targets(train) - btr)
        q_cf = gbm.predict(Xcf, len(leads)) + bcf[..., None]
        q_te = gbm.predict(Xte, len(leads)) + bte[..., None]
        cqr = CQR(alpha=0.10).fit(q_cf[..., 0], q_cf[..., -1], q_cf[..., 1], prep.targets(conf))
        q_te = calibrate_quantiles(q_te, cqr, GBM_QUANTILES)
        preds_q["gbm"], levels["gbm"] = q_te, GBM_QUANTILES

    # ---- Score ---------------------------------------------------------------
    obs = test[[f"y_L{lead}" for lead in leads]].to_numpy(dtype=float)
    dates = test["issue_date"].to_numpy()
    base_preds = baselines(test, prep, leads)
    point_preds = {k: np.expm1(v[..., list(levels[k]).index(0.5)]) for k, v in preds_q.items()}
    allp = {**point_preds, **base_preds}

    subsets = {
        "all": np.ones(len(test), bool),
        "smoke_yesterday": (test["hms_prev"].fillna(0) >= 1).to_numpy(),
        "heavy_smoke_yesterday": (test["hms_prev"].fillna(0) >= 3).to_numpy(),
        **({"unseen_sites": test["point_id"].isin(np.array(node_ids)[holdout]).to_numpy()}
           if holdout.any() else {}),
    }
    rows = []
    for li, lead in enumerate(leads):
        valid_dates = np.array([d + pd.Timedelta(days=lead) for d in pd.to_datetime(dates)])
        valid_dates = np.array([d.date() for d in valid_dates])
        for sname, smask in subsets.items():
            for m, p in allp.items():
                pm = point_metrics(p[smask, li], obs[smask, li], valid_dates[smask])
                rec = {"lead": lead, "subset": sname, "model": m, **pm}
                if m in preds_q:
                    qs = np.expm1(preds_q[m][smask, li])
                    ok = np.isfinite(obs[smask, li])
                    rec["crps"] = float(crps_from_quantiles(qs[ok], levels[m], obs[smask, li][ok]).mean())
                    rec.update(interval_metrics(qs[:, 0], qs[:, -1], obs[smask, li]))
                else:
                    ok = np.isfinite(p[smask, li]) & np.isfinite(obs[smask, li])
                    rec["crps"] = float(np.abs(p[smask, li][ok] - obs[smask, li][ok]).mean()) if ok.any() else np.nan
                rows.append(rec)
    # Warning rule: warn when P(>= 35.5) exceeds a cut-off tuned on calibration days.
    obs_conf = conf[[f"y_L{lead}" for lead in leads]].to_numpy(dtype=float)
    warn_test = np.zeros_like(obs, dtype=bool)
    cutoffs = {}
    for li, lead in enumerate(leads):
        pc = prob_exceed(q_conf_cal[:, li], QUANTILES)
        cut = tune_warning_threshold(pc, obs_conf[:, li])
        cutoffs[lead] = cut
        pt = prob_exceed(preds_q["smokecast"][:, li], QUANTILES)
        warn_test[:, li] = pt >= cut
        for sname, smask in subsets.items():
            rows.append({"lead": lead, "subset": sname, "model": "smokecast_warnrule",
                         **warning_scores(warn_test[smask, li], obs[smask, li])})
    met = pd.DataFrame(rows)
    met.to_csv(out_dir / "metrics.csv", index=False)
    log(f"warning cut-offs P(>=35.5) tuned on calibration: {cutoffs}")
    (out_dir / "warn_cutoffs.json").write_text(json.dumps({str(k): v for k, v in cutoffs.items()}))

    # Head-to-head on IDENTICAL rows, with day-block bootstrap CIs.
    h2h = []
    for li, lead in enumerate(leads):
        for b in ["noaa_best", "aqm_bc", "hrrr_smoke", "persistence", "gbm", "smokecast_nograph"]:
            if b not in allp:
                continue
            ci = bootstrap_rmse_diff(allp["smokecast"][:, li], allp[b][:, li], obs[:, li], dates)
            if not ci:
                continue
            ok = np.isfinite(allp[b][:, li]) & np.isfinite(obs[:, li])
            r_s = point_metrics(allp["smokecast"][ok, li], obs[ok, li])["rmse"]
            r_b = point_metrics(allp[b][ok, li], obs[ok, li])["rmse"]
            h2h.append({"lead": lead, "vs": b, "n": int(ok.sum()), "rmse_smokecast": r_s,
                        "rmse_baseline": r_b, "skill": 1 - r_s / r_b, **ci})
    h2h = pd.DataFrame(h2h)
    h2h.to_csv(out_dir / "head_to_head.csv", index=False)

    epa = compare_with_epa(study, test, allp["smokecast"], leads, pts, warn_test)
    if len(epa):
        epa.to_csv(out_dir / "vs_epa_forecast.csv", index=False)

    # Predictions for figures / case studies.
    keep = test[["issue_date", "point_id", "hms_prev"] + [f"y_L{lead}" for lead in leads]].copy()
    for m, p in allp.items():
        for li, lead in enumerate(leads):
            keep[f"{m}_L{lead}"] = p[:, li]
    for li, lead in enumerate(leads):
        keep[f"smokecast_lo_L{lead}"] = np.expm1(preds_q["smokecast"][:, li, 0])
        keep[f"smokecast_hi_L{lead}"] = np.expm1(preds_q["smokecast"][:, li, -1])
    keep.to_parquet(out_dir / "predictions.parquet", index=False)

    # Report
    log("\n## Results: all site-days")
    show = met[(met.subset == "all")].pivot_table(index="model", columns="lead", values="rmse")
    log("RMSE (µg/m³, lower is better)\n" + show.round(2).to_string())
    show = met[(met.subset == "smoke_yesterday")].pivot_table(index="model", columns="lead", values="rmse")
    log("\nRMSE on smoke-affected days (HMS plume overhead yesterday)\n" + show.round(2).to_string())
    if holdout.any():
        show = met[(met.subset == "unseen_sites")].pivot_table(index="model", columns="lead", values="rmse")
        log("\nRMSE at HIDDEN monitors (no readings; persistence/climatology use data a "
            "real unmonitored place would not have)\n" + show.round(2).to_string())
    show = met[(met.subset == "all")].pivot_table(index="model", columns="lead", values="usg_csi")
    log("\nUSG+ critical success index (higher is better)\n" + show.round(3).to_string())
    cov = met[(met.subset == "all") & met["coverage90"].notna()].pivot_table(
        index="model", columns="lead", values="coverage90")
    log("\n90% interval coverage (target 0.90)\n" + cov.round(3).to_string())
    if len(h2h):
        log("\nHead-to-head (same rows; skill = 1 - RMSE_smokecast/RMSE_baseline; CI = 95% day-bootstrap of RMSE diff)")
        log(h2h[["lead", "vs", "n", "rmse_smokecast", "rmse_baseline", "skill", "ci_lo", "ci_hi"]]
            .round(3).to_string(index=False))
    if len(epa):
        log("\nvs. official EPA AQI forecast (reporting areas, category scores)")
        log(epa.round(3).to_string(index=False))
    (out_dir / "report.md").write_text("\n".join(log_lines), encoding="utf-8")
    (out_dir / "conformal.json").write_text(json.dumps(cqr_store, indent=1))
    if final:
        (out_dir / "FINAL_RUN_LOCK.json").write_text(json.dumps(
            {"run_at": datetime.now().isoformat(), "code_version": _git_rev(),
             "test_split": study.raw["split"]["test"]}, indent=1))
    log(f"\nwrote {out_dir}")
    return {"metrics": met, "h2h": h2h, "epa": epa}


def compare_with_epa(study, test, smokecast_pm, leads, pts, warn=None) -> pd.DataFrame:
    """Category forecasts per reporting area: SmokeCast vs. EPA's official forecast.

    SmokeCast area forecast = highest site forecast among sites in the area (the
    AQI for an area is driven by its worst monitor). Truth = EPA's own observed
    daily area AQI ("Y" rows). EPA forecasts are issued late morning/afternoon
    local time, i.e. AFTER our issue time, so this comparison favors EPA.
    """
    days = sorted(test["issue_date"].unique())
    fc = load_forecasts(days)
    if fc.empty:
        return pd.DataFrame()
    # Area names are not unique across states (e.g. "Concord", "Dayton"): keep only
    # areas inside the study region, and match observations on (area, state).
    fc = fc[study.region.contains(fc["lat"], fc["lon"])].copy()
    if fc.empty:
        return pd.DataFrame()
    obs_days = sorted({d + pd.Timedelta(days=lead).to_pytimedelta() for d in days for lead in leads})
    ob = load_observed_area_aqi(obs_days).copy()
    if ob.empty:
        return pd.DataFrame()
    # Use the same text keys for monitor, forecast, and observed-area metadata.
    # Preserve state as part of every join: area names alone are not identifiers.
    def key(value):
        return "" if pd.isna(value) else " ".join(str(value).split()).casefold()

    def normalized_areas(frame):
        frame = frame.copy()
        for column in ("reporting_area", "state"):
            frame[column] = frame[column].map(key)
        return frame[(frame["reporting_area"] != "") & (frame["state"] != "")]

    fc, ob = normalized_areas(fc), normalized_areas(ob)
    if "issue_date" in fc:
        fc = fc.sort_values("issue_date", kind="stable")
    fc = fc.drop_duplicates(["as_of", "valid_date", "lead", "reporting_area", "state"],
                            keep="last")
    ob = ob.drop_duplicates(["valid_date", "reporting_area", "state"], keep="last")
    if fc.empty or ob.empty:
        return pd.DataFrame()
    ra = pts["reporting_area"].fillna("") if "reporting_area" in pts else None
    if ra is None:
        return pd.DataFrame()
    known_states = fc.groupby("reporting_area")["state"].unique()
    site_area, skipped = [], 0
    for pid, areas in ra.items():
        state = key(pts.loc[pid, "state"]) if "state" in pts else ""
        for a in str(areas).split("|"):
            area = key(a)
            if not area:
                continue
            # Older registries omitted state entirely. Infer only an unambiguous
            # area-to-state mapping, never a state from a monitor's coordinates.
            area_states = known_states.get(area, [])
            match_state = state or (area_states[0] if len(area_states) == 1 else "")
            if not match_state:
                skipped += 1
                continue
            site_area.append((pid, area, match_state))
    if skipped:
        warnings.warn(f"Skipped {skipped} EPA monitor/reporting-area mappings without an "
                      "unambiguous state. Run `serein build-points` to rebuild the points "
                      "registry with state metadata before comparing these areas.",
                      UserWarning, stacklevel=2)
    sa = pd.DataFrame(site_area, columns=["point_id", "reporting_area", "state"]).drop_duplicates()
    if sa.empty:
        return pd.DataFrame()
    rows = []
    for li, lead in enumerate(leads):
        t = test[["issue_date", "point_id"]].copy()
        t["pm"] = smokecast_pm[:, li]
        t["warn"] = warn[:, li] if warn is not None else smokecast_pm[:, li] >= 35.5
        t = t.merge(sa, on="point_id")
        area = t.groupby(["issue_date", "reporting_area", "state"]).agg(
            pm=("pm", "max"), warn=("warn", "max")).reset_index()
        f = fc[fc["lead"] == lead][["as_of", "valid_date", "reporting_area", "state", "category_idx"]]
        f = f.rename(columns={"as_of": "issue_date", "category_idx": "epa_cat"})
        m = area.merge(f, on=["issue_date", "reporting_area", "state"])
        m = m.merge(ob.rename(columns={"category_idx": "obs_cat"})[
                        ["valid_date", "reporting_area", "state", "obs_cat"]],
                    on=["valid_date", "reporting_area", "state"])
        m = m.dropna(subset=["epa_cat", "obs_cat", "pm"])
        if m.empty:
            continue
        m["sc_cat"] = [float(pm25_to_category(np.array([p]), vd)[0])
                       for p, vd in zip(m["pm"], m["valid_date"])]
        m["sc_warn"] = m["warn"].astype(bool) | (m["sc_cat"] >= 2)
        m["epa_warn"] = m["epa_cat"] >= 2
        for who, col, wcol in [("smokecast", "sc_cat", "sc_warn"),
                               ("epa_forecast", "epa_cat", "epa_warn")]:
            hit = (m[wcol] & (m["obs_cat"] >= 2)).sum()
            miss = (~m[wcol] & (m["obs_cat"] >= 2)).sum()
            fa = (m[wcol] & (m["obs_cat"] < 2)).sum()
            rows.append({"lead": lead, "who": who, "n_area_days": len(m),
                         "cat_acc": float((m[col] == m["obs_cat"]).mean()),
                         "usg_events": int(hit + miss),
                         "usg_pod": hit / (hit + miss) if hit + miss else np.nan,
                         "usg_far": fa / (hit + fa) if hit + fa else np.nan,
                         "usg_csi": hit / (hit + miss + fa) if hit + miss + fa else np.nan})
    return pd.DataFrame(rows)
