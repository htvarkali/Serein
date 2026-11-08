"""Use a trained SmokeCast model: forecasts for any day, at sensors AND at map grid points.

Grid points are "virtual sensors": they have NOAA forecasts, weather, fires and
smoke plumes, but no readings. Each grid point receives messages from its k
nearest real sensors (never from other grid points), the same way a sensor
with hidden readings did during training (node masking).
"""

from __future__ import annotations

import json
import pickle
import warnings
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import date
from numbers import Integral
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.spatial import cKDTree

from serein.aqi import pm25_to_category
from serein.config import Study
from serein.data.firms import bearing_rad, haversine_km
from serein.data.points import load_points
from serein.features.context import forecast_context, unavailable_context
from serein.features.graph import Graph, build_knn_graph
from serein.features.prepare import leads_of, neighbor_base, to_graph_data
from serein.features.table import build_table
from serein.models.conformal import calibrate_quantiles
from serein.models.ensemble import SmokeCastEnsemble
from serein.models.gnn import QUANTILES, SmokeCastGNN

AQI_COLORS = ["#00e400", "#ffff00", "#ff7e00", "#ff0000", "#8f3f97", "#7e0023"]


def _validate_metadata(meta: dict) -> None:
    """Fail clearly before constructing a network from an incompatible artifact."""
    if not isinstance(meta, dict):
        raise TypeError("Model metadata must be an object")
    version = meta.get("format_version", 1)
    if isinstance(version, bool) or not isinstance(version, Integral) or version not in (1, 2):
        raise ValueError(f"Unsupported SmokeCast artifact format: {version}")
    for key in ("n_feat", "hidden", "layers", "heads", "n_members"):
        default = 1 if key == "n_members" and version == 1 else None
        value = meta.get(key, default)
        if isinstance(value, bool) or not isinstance(value, Integral) or value < 1:
            raise ValueError(f"Model metadata {key} must be a positive integer")
    if meta["hidden"] % meta["heads"] or meta["hidden"] < 2:
        raise ValueError("Model hidden size must be >= 2 and divisible by attention heads")
    leads = meta.get("leads")
    if (not isinstance(leads, list) or not leads
            or any(isinstance(x, bool) or not isinstance(x, Integral) or x < 0 for x in leads)
            or len(set(leads)) != len(leads)):
        raise ValueError("Model metadata leads must be distinct nonnegative integers")
    nodes = meta.get("node_ids")
    if (not isinstance(nodes, list) or not nodes
            or any(not isinstance(x, str) or not x.strip() for x in nodes)
            or len(set(nodes)) != len(nodes)):
        raise ValueError("Model metadata node_ids must be distinct nonempty strings")
    if not isinstance(meta.get("use_graph", True), bool):
        raise TypeError("Model metadata use_graph must be boolean")
    if version == 2:
        if meta.get("aggregation") != "mean_log1p_quantiles":
            raise ValueError("Unsupported ensemble aggregation in model metadata")
        seeds = meta.get("seeds")
        if (not isinstance(seeds, list) or len(seeds) != meta["n_members"]
                or any(s is not None and (isinstance(s, bool) or not isinstance(s, Integral))
                       for s in seeds)):
            raise ValueError("Model metadata seeds must match the ensemble member count")


def save_artifacts(out_dir: Path, prep, node_ids, n_feat, leads, cfg, cqr, state_dict,
                   *, seeds=None):
    """Export every evaluated member and its shared preprocessing/calibration.

    ``state_dict`` also accepts a single mapping for existing callers. All new
    exports use the versioned bundle, including single-member runs.
    """
    states = [state_dict] if isinstance(state_dict, Mapping) else state_dict
    if not isinstance(states, (list, tuple)) or not states:
        raise ValueError("Export needs one or more model state dictionaries")
    if any(not isinstance(state, Mapping) or not state
           or any(not isinstance(k, str) or not isinstance(v, torch.Tensor)
                  for k, v in state.items()) for state in states):
        raise ValueError("Each model state dictionary must contain named tensors")
    # Copy while this member is still alive; later training must not mutate its weights.
    states = [{k: v.detach().cpu().clone() for k, v in state.items()} for state in states]
    if seeds is None:
        seeds = [int(getattr(cfg, "seed", 0))] if len(states) == 1 else [None] * len(states)
    meta = {
        "node_ids": list(node_ids), "n_feat": int(n_feat), "leads": list(leads),
        "hidden": cfg.hidden, "layers": cfg.layers, "heads": cfg.heads,
        "use_graph": getattr(cfg, "use_graph", True), "format_version": 2,
        "history": int(getattr(cfg, "history", 1)),
        "n_members": len(states),
        "seeds": list(seeds), "aggregation": "mean_log1p_quantiles",
    }
    _validate_metadata(meta)
    out_dir.mkdir(parents=True, exist_ok=True)
    torch.save({"format_version": 2, "members": states}, out_dir / "smokecast.pt")
    with open(out_dir / "artifacts.pkl", "wb") as f:
        pickle.dump({"prep": prep, "cqr": cqr}, f)
    (out_dir / "model.json").write_text(json.dumps(meta, indent=1))


def load_artifacts(run_dir: Path):
    meta = json.loads((run_dir / "model.json").read_text())
    _validate_metadata(meta)
    weights = torch.load(run_dir / "smokecast.pt", map_location="cpu", weights_only=True)
    if meta.get("format_version", 1) == 2:
        if (not isinstance(weights, dict) or weights.get("format_version") != 2
                or not isinstance(weights.get("members"), list)
                or len(weights["members"]) != meta["n_members"]):
            raise ValueError("Model checkpoint member count or format does not match metadata")
        states = weights["members"]
    else:
        if meta.get("n_members", 1) != 1:
            raise ValueError("Legacy checkpoint cannot contain multiple ensemble members")
        warnings.warn("Loading a legacy single-model artifact. Its original ensemble cannot "
                      "be recovered; rerun the development backtest to export all members.",
                      UserWarning, stacklevel=2)
        states = [weights]
    with open(run_dir / "artifacts.pkl", "rb") as f:
        art = pickle.load(f)
    torch.use_deterministic_algorithms(True)
    members = []
    for state in states:
        member = SmokeCastGNN(meta["n_feat"], len(meta["leads"]), meta["hidden"], meta["layers"],
                             meta["heads"], drop=0.0, use_graph=meta.get("use_graph", True),
                             history=meta.get("history", 1))
        try:
            member.load_state_dict(state)
        except (RuntimeError, TypeError) as exc:
            raise ValueError("Model checkpoint is incompatible with its metadata") from exc
        members.append(member)
    model = SmokeCastEnsemble(members)
    model.eval()
    meta.setdefault("n_members", len(members))
    return model, art["prep"], art["cqr"], meta


def sensor_plus_grid_graph(sensor_xy, grid_xy, k: int, max_km: float) -> Graph:
    """Sensors keep their sensor-only kNN graph; each grid point listens to k sensors."""
    sensor_xy, grid_xy = np.asarray(sensor_xy, float), np.asarray(grid_xy, float)
    for coordinates in (sensor_xy, grid_xy):
        if (coordinates.ndim != 2 or coordinates.shape[1] != 2
                or not np.isfinite(coordinates).all()
                or (np.abs(coordinates[:, 0]) > 90).any()
                or (np.abs(coordinates[:, 1]) > 180).any()):
            raise ValueError("Map graph coordinates must have [points, 2] shape with valid "
                             "finite latitude and longitude")
    gs = build_knn_graph(sensor_xy[:, 0], sensor_xy[:, 1], k=k, max_km=max_km)
    ns = len(sensor_xy)
    if not ns or not len(grid_xy) or not k:
        return gs

    def xyz(a):
        la, lo = np.radians(a[:, 0]), np.radians(a[:, 1])
        return np.stack([np.cos(la) * np.cos(lo), np.cos(la) * np.sin(lo), np.sin(la)], 1)

    # cKDTree emits out-of-bounds sentinel indices when k exceeds the sensor count.
    neighbors = min(k, ns)
    _, nbr = cKDTree(xyz(sensor_xy)).query(xyz(grid_xy), k=neighbors)
    src = nbr.reshape(-1)
    dst = np.repeat(np.arange(len(grid_xy)), neighbors) + ns
    d = haversine_km(sensor_xy[src, 0], sensor_xy[src, 1], grid_xy[dst - ns, 0], grid_xy[dst - ns, 1])
    keep = d <= max_km
    src, dst, d = src[keep], dst[keep], d[keep]
    b = bearing_rad(sensor_xy[src, 0], sensor_xy[src, 1], grid_xy[dst - ns, 0], grid_xy[dst - ns, 1])
    attr = np.stack([d / max_km, np.log1p(d) / np.log1p(max_km), np.sin(b), np.cos(b)], 1)
    return Graph(np.r_[gs.src, src], np.r_[gs.dst, dst], np.r_[gs.dist_km, d],
                 np.r_[gs.bearing, b], np.r_[gs.edge_attr, attr].astype(np.float32))


@dataclass
class ForecastInputs:
    """Everything the model sees for one issue day (shared by forecasts and explain)."""
    model: SmokeCastEnsemble
    prep: object
    cqr: object
    meta: dict
    tab: pd.DataFrame
    use: pd.DataFrame
    X: np.ndarray
    feat_names: list
    wind: np.ndarray
    base: np.ndarray
    graph: Graph
    leads: list
    nodes: list
    xh: np.ndarray | None = None  # [N, K-1, F] past days' inputs (history models)

    def run(self, x=None, xh=None):
        """Model output [1, N, L, Q] (log1p), optionally with replaced inputs."""
        t = lambda a: a if torch.is_tensor(a) else torch.as_tensor(a).unsqueeze(0)
        g = self.graph
        xh = xh if xh is not None else (None if self.xh is None else t(self.xh))
        return self.model(t(self.X if x is None else x), t(self.wind), t(self.base),
                          torch.as_tensor(g.src), torch.as_tensor(g.dst),
                          torch.as_tensor(g.bearing, dtype=torch.float32),
                          torch.as_tensor(g.edge_attr), xh)


def build_inputs(study: Study, day: date, run_dir: Path, with_grid: bool = True) -> ForecastInputs:
    model, prep, cqr, meta = load_artifacts(run_dir)
    pts = load_points(study.name).set_index("point_id")
    sensors = [n for n in meta["node_ids"] if n in pts.index]
    grid = pts.index[pts["kind"] == "grid"].tolist() if with_grid else []
    use = pts.loc[sensors + grid].reset_index()
    tab = build_table(study, [day], use, progress=False)
    tab = tab.set_index("point_id").reindex(sensors + grid).reset_index()
    tab["issue_date"] = day
    for c in [c for c in tab.columns if c.startswith("y_L")]:
        tab[c] = tab[c].astype(float)
    X, names = prep.transform(tab)
    leads = leads_of(tab)
    base = prep.base(tab, leads)
    wind = np.nan_to_num(tab[["hrrr_u10_L0", "hrrr_v10_L0"]].to_numpy(np.float32)) \
        if "hrrr_u10_L0" in tab else np.zeros((len(tab), 2), np.float32)
    sxy = pts.loc[sensors, ["lat", "lon"]].to_numpy(float)
    gxy = pts.loc[grid, ["lat", "lon"]].to_numpy(float) if grid else np.zeros((0, 2))
    k, mk = study.raw["graph"]["k_neighbors"], study.raw["graph"]["max_km"]
    g = sensor_plus_grid_graph(sxy, gxy, k, mk) if grid else build_knn_graph(sxy[:, 0], sxy[:, 1], k, mk)
    if grid:
        # Grid points have no readings: their base comes from nearby sensors' readings.
        gd = to_graph_data(tab, prep, sensors + grid)
        is_sensor = np.r_[np.ones(len(sensors), bool), np.zeros(len(grid), bool)]
        b_nbr = neighbor_base(gd, tab, prep, g, sources=is_sensor)[0]
        base = np.where(is_sensor[:, None], base, b_nbr).astype(np.float32)
    xh = None
    k = int(meta.get("history", 1))
    if k > 1:
        # Past days' inputs, built exactly like today's (same issue-time rules).
        days = [day - pd.Timedelta(days=b).to_pytimedelta() for b in range(k - 1, 0, -1)]
        past = build_table(study, days, use, progress=False)
        Xp, _ = prep.transform(past)
        absent = np.array([n.endswith("__missing") for n in names], np.float32)
        xh = np.broadcast_to(absent, (len(tab), k - 1, X.shape[1])).copy()
        pos = {n: i for i, n in enumerate(sensors + grid)}
        for j, d in enumerate(days):
            sel = (past["issue_date"] == d).to_numpy()
            idx = past.loc[sel, "point_id"].map(pos)
            ok = idx.notna().to_numpy()
            xh[idx[ok].astype(int).to_numpy(), j] = Xp[np.where(sel)[0][ok]]
    return ForecastInputs(model, prep, cqr, meta, tab, use, X, names, wind, base, g, leads,
                          sensors + grid, xh)


def forecast_day(study: Study, day: date, run_dir: Path, with_grid: bool = True) -> pd.DataFrame:
    inp = build_inputs(study, day, run_dir, with_grid)
    cqr, tab, use, leads = inp.cqr, inp.tab, inp.use, inp.leads
    with torch.no_grad():
        q = inp.run()[0].numpy()
    q = calibrate_quantiles(q, cqr, QUANTILES)
    rows = []
    for li, lead in enumerate(leads):
        valid = day + pd.Timedelta(days=lead).to_pytimedelta()
        med = np.expm1(q[:, li, 2])
        rows.append(pd.DataFrame({
            "point_id": tab["point_id"], "kind": use.set_index("point_id").loc[tab["point_id"], "kind"].to_numpy(),
            "lat": tab["lat"], "lon": tab["lon"], "issue_date": day, "lead": lead, "valid_date": valid,
            **{f"q{int(100 * lv):02d}": np.expm1(q[:, li, j]) for j, lv in enumerate(QUANTILES)},
            "aqi_cat": pm25_to_category(med, valid), "obs": tab.get(f"y_L{lead}"),
        }))
    forecasts = pd.concat(rows, ignore_index=True)
    try:
        context = forecast_context(study, day, use, leads)
    except (ValueError, OSError, KeyError) as exc:
        warnings.warn(f"Optional forecast context unavailable: {exc}", RuntimeWarning, stacklevel=2)
        context = unavailable_context(day, use, leads)
    return forecasts.merge(context, on=["point_id", "valid_date"], how="left",
                            validate="one_to_one")


STATES_URL = "https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_us_state_20m.zip"


def state_boundaries():
    """US state outlines (Census cartographic boundary file, free), cached."""
    import geopandas as gpd

    from serein.config import raw_dir
    from serein.http import get

    path = raw_dir("boundaries") / "cb_2023_us_state_20m.zip"
    if not path.exists():
        try:
            path.write_bytes(get(STATES_URL).content)
        except Exception:  # noqa: BLE001 - maps still work without outlines
            return None
    return gpd.read_file(f"zip://{path}").to_crs(4326)


def plot_map(fc: pd.DataFrame, out_png: Path, title: str = "") -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import BoundaryNorm, ListedColormap

    leads = sorted(fc["lead"].unique())
    fig, axes = plt.subplots(1, len(leads), figsize=(4.2 * len(leads), 6), squeeze=False)
    cmap = ListedColormap(AQI_COLORS)
    norm = BoundaryNorm(np.arange(-0.5, 6.5), cmap.N)
    states = state_boundaries()
    land = None
    if states is not None:
        import geopandas as gpd
        g0 = fc[(fc["kind"] == "grid") & (fc["lead"] == leads[0])]
        pts = gpd.GeoDataFrame(geometry=gpd.points_from_xy(g0["lon"], g0["lat"]), crs=4326)
        inside = gpd.sjoin(pts, states[["geometry"]], predicate="within", how="inner").index
        land = set(g0["point_id"].iloc[np.unique(inside)])
    for ax, lead in zip(axes[0], leads):
        d = fc[fc["lead"] == lead]
        gr, se = d[d["kind"] == "grid"], d[d["kind"] != "grid"]
        if land is not None:
            gr = gr[gr["point_id"].isin(land)]
        if len(gr):
            # Draw grid cells as an image so they tile without gaps.
            lats, lons = np.sort(gr["lat"].unique()), np.sort(gr["lon"].unique())
            img = np.full((len(lats), len(lons)), np.nan)
            img[np.searchsorted(lats, gr["lat"]), np.searchsorted(lons, gr["lon"])] = gr["aqi_cat"]
            step = lats[1] - lats[0] if len(lats) > 1 else 0.25
            ax.imshow(img, origin="lower", cmap=cmap, norm=norm, alpha=0.75, interpolation="nearest",
                      extent=(lons[0] - step / 2, lons[-1] + step / 2, lats[0] - step / 2, lats[-1] + step / 2))
        if states is not None:
            states.boundary.plot(ax=ax, color="k", linewidth=0.5)
        ax.scatter(se["lon"], se["lat"], c=se["aqi_cat"], cmap=cmap, norm=norm, s=14,
                   edgecolors="k", linewidths=0.4)
        ax.set_xlim(d["lon"].min() - 0.3, d["lon"].max() + 0.3)
        ax.set_ylim(d["lat"].min() - 0.3, d["lat"].max() + 0.3)
        ax.set_title(f"{d['valid_date'].iloc[0]} (day +{lead})")
        ax.set_aspect(1 / np.cos(np.radians(d["lat"].mean())))
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_xlabel("")
        ax.set_ylabel("")
    fig.suptitle(title or "SmokeCast forecast: daily PM2.5 AQI category (squares = map grid, dots = sensors)")
    fig.tight_layout()
    fig.savefig(out_png, dpi=140)
    plt.close(fig)
