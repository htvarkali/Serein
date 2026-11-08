"""Turn the raw table into model-ready numbers.

* Concentrations are skewed (most days 5 µg/m³, smoke days 300), so we work with
  log1p(x) = log(1 + x). Example: 5 -> 1.79, 35 -> 3.58, 300 -> 5.71.
* Every feature is standardized with TRAIN-season statistics only.
* Missing values become 0, and a 0/1 "missing" flag is added, so the model knows.
* The model predicts a correction to a "base" forecast:
      base_L = AQM (if available) -> yesterday's observed mean -> site climatology.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

ID_COLS = ["issue_date", "point_id", "kind"]
LOG_PREFIXES = ("obs_last", "obs_max", "obs_prev", "hrrr_smoke_", "aqm_", "frp_",
                "hrrr_colmd", "hrrr_pbl")
OBS_PREFIX = "obs_"  # columns hidden during node masking
SITE_HISTORY = ("site_clim", "site_bg")  # also unknown at places with no sensor
# Derived from site_bg (the site's own clean-air history), so it leaks that history
# unless it is hidden wherever site_bg is hidden.
SITE_DERIVED_PREFIX = "hrrr_pm_L"


def is_sensor_feature(name: str) -> bool:
    """Features that only exist where there is a sensor (hidden by node masking)."""
    base = name.removesuffix("__missing")
    return base.startswith((OBS_PREFIX, SITE_DERIVED_PREFIX)) or base in SITE_HISTORY


def target_cols(df: pd.DataFrame) -> list[str]:
    return sorted([c for c in df.columns if c.startswith("y_L")], key=lambda c: int(c[3:]))


def leads_of(df: pd.DataFrame) -> list[int]:
    return [int(c[3:]) for c in target_cols(df)]


def _transform(col: str, x: pd.Series) -> pd.Series:
    x = x.astype(float)
    if col.startswith(LOG_PREFIXES):
        return np.log1p(x.clip(lower=0))
    if col == "obs_n24":
        return x / 24.0
    if col == "fire_dist_km":
        return np.log1p(x)
    return x


@dataclass
class Prep:
    feature_cols: list[str] = field(default_factory=list)
    mean: dict = field(default_factory=dict)
    std: dict = field(default_factory=dict)
    mask_cols: list[str] = field(default_factory=list)
    site_clim: dict = field(default_factory=dict)
    site_bg: dict = field(default_factory=dict)
    global_clim: float = 1.8
    exclude: tuple = ()          # ablations: input prefixes the model may not see
    use_obs_base: bool = True    # False = base forecast may not use sensor readings

    # ------------------------------------------------------------------ fit
    def fit(self, train: pd.DataFrame) -> Prep:
        t = train.copy()
        y0 = np.log1p(t["y_L0"].clip(lower=0))
        self.site_clim = y0.groupby(t["point_id"]).median().dropna().to_dict()
        # A missing map is unknown, not a confirmed clean-air day.
        clean = t["hms_prev"].eq(0) if "hms_prev" in t else pd.Series(False, index=t.index)
        self.site_bg = y0[clean].groupby(t.loc[clean, "point_id"]).median().dropna().to_dict()
        self.global_clim = float(np.nanmedian(y0))
        t = self._add_derived(t)
        skip = set(ID_COLS) | set(target_cols(t))
        self.feature_cols = [c for c in t.columns if c not in skip
                             and pd.api.types.is_numeric_dtype(t[c])
                             and not (self.exclude and c.startswith(tuple(self.exclude)))]
        if self.exclude and any(e.startswith("obs_") for e in self.exclude):
            # "No sensors": hide readings AND the site history learned from them.
            self.feature_cols = [c for c in self.feature_cols if c not in SITE_HISTORY
                                 and not c.startswith(SITE_DERIVED_PREFIX)]
        self.mask_cols = []
        for c in self.feature_cols:
            v = _transform(c, t[c])
            mu, sd = ((float(np.nanmean(v)), float(np.nanstd(v)))
                      if v.notna().any() else (0.0, 1.0))
            self.mean[c], self.std[c] = mu, (sd if sd > 1e-6 else 1.0)
            if is_sensor_feature(c) or v.isna().any():
                self.mask_cols.append(c)
        return self

    def _add_derived(self, df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df["site_clim"] = df["point_id"].map(self.site_clim)
        df["site_bg"] = df["point_id"].map(self.site_bg)
        # HRRR smoke + clean-air background: a fair "raw HRRR" PM2.5 forecast.
        for lead in range(4):
            c = f"hrrr_smoke_mean_L{lead}"
            if c in df:
                bg = np.expm1(df["site_bg"].fillna(self.global_clim))
                df[f"hrrr_pm_L{lead}"] = df[c] + bg
        return df

    # ------------------------------------------------------------ transform
    def transform(self, df: pd.DataFrame) -> tuple[np.ndarray, list[str]]:
        df = self._add_derived(df)
        cols, out = [], []
        for c in self.feature_cols:
            v = _transform(c, df[c]) if c in df else pd.Series(np.nan, index=df.index)
            z = ((v - self.mean[c]) / self.std[c]).to_numpy(dtype=np.float32)
            miss = ~np.isfinite(z)
            z[miss] = 0.0
            out.append(z)
            cols.append(c)
            if c in self.mask_cols:
                out.append(miss.astype(np.float32))
                cols.append(f"{c}__missing")
        return np.stack(out, axis=1), cols

    def base(self, df: pd.DataFrame, leads: list[int]) -> np.ndarray:
        """Base forecast in log1p space, shape [rows, n_leads]."""
        clim = df["point_id"].map(self.site_clim).fillna(self.global_clim).to_numpy()
        persist = np.log1p(df["obs_prevday"].clip(lower=0)).to_numpy()
        recent = np.log1p(df["obs_last24"].clip(lower=0)).to_numpy()
        if not self.use_obs_base:
            persist = recent = np.full(len(df), np.nan)
            clim = np.full(len(df), self.global_clim)
        fallback = np.where(np.isfinite(persist), persist, np.where(np.isfinite(recent), recent, clim))
        out = []
        no_aqm = any(e.startswith("aqm_") for e in self.exclude)
        for lead in leads:
            c = f"aqm_mean_L{lead}"
            a = (np.log1p(df[c].clip(lower=0)).to_numpy() if c in df and not no_aqm
                 else np.full(len(df), np.nan))
            out.append(np.where(np.isfinite(a), a, fallback))
        return np.stack(out, axis=1).astype(np.float32)

    def targets(self, df: pd.DataFrame) -> np.ndarray:
        return np.log1p(df[target_cols(df)].clip(lower=0)).to_numpy(dtype=np.float32)


@dataclass
class GraphData:
    """Dense day x node arrays for the GNN."""
    days: list
    nodes: list
    X: np.ndarray       # [T, N, F]
    Y: np.ndarray       # [T, N, L]   log1p target (NaN = no obs)
    base: np.ndarray    # [T, N, L]
    wind: np.ndarray    # [T, N, 2]   u, v (m/s), 0 if missing
    feat_names: list
    row_index: np.ndarray  # [T, N] index into the source table (-1 = absent)
    base_nbr: np.ndarray | None = None  # [T, N, L] base without the node's own readings
    hist: np.ndarray | None = None      # [T, N, K-1, F] inputs of the K-1 previous days


def _day(d):
    return pd.Timestamp(d).date()


def history_from(full: GraphData, days: list, k: int) -> np.ndarray:
    """Inputs of the k-1 days before each of ``days``, oldest first: [T, N, k-1, F].

    ``full`` must hold every day that may be needed (all splits together): the day
    before a validation day can belong to another split, and its inputs were public
    at issue time either way. Days with no data look like absent rows (all missing).
    """
    di = {_day(d): i for i, d in enumerate(full.days)}
    T, (N, F) = len(days), full.X.shape[1:]
    absent = np.array([n.endswith("__missing") for n in full.feat_names], np.float32)
    out = np.broadcast_to(absent, (T, N, k - 1, F)).copy()
    for t, d in enumerate(days):
        for j, back in enumerate(range(k - 1, 0, -1)):
            i = di.get(_day(d) - pd.Timedelta(days=back).to_pytimedelta())
            if i is not None:
                out[t, :, j] = full.X[i]
    return out


def to_graph_data(df: pd.DataFrame, prep: Prep, nodes: list[str]) -> GraphData:
    df = df.reset_index(drop=True)
    leads = leads_of(df)
    X, names = prep.transform(df)
    Y = prep.targets(df)
    B = prep.base(df, leads)
    u = df.get("hrrr_u10_L0", pd.Series(np.nan, index=df.index)).to_numpy(dtype=np.float32)
    v = df.get("hrrr_v10_L0", pd.Series(np.nan, index=df.index)).to_numpy(dtype=np.float32)
    W = np.nan_to_num(np.stack([u, v], 1))

    days = sorted(df["issue_date"].unique())
    di = {d: i for i, d in enumerate(days)}
    ni = {n: i for i, n in enumerate(nodes)}
    T, N, F, L = len(days), len(nodes), X.shape[1], len(leads)
    Xa = np.zeros((T, N, F), np.float32)
    # Rows that are absent entirely: mark every maskable feature as missing.
    miss_cols = [i for i, n in enumerate(names) if n.endswith("__missing")]
    Xa[:, :, miss_cols] = 1.0
    Ya = np.full((T, N, L), np.nan, np.float32)
    Ba = np.full((T, N, L), prep.global_clim, np.float32)
    Wa = np.zeros((T, N, 2), np.float32)
    R = np.full((T, N), -1, np.int64)
    keep = df["point_id"].isin(ni).to_numpy()
    t_idx = df.loc[keep, "issue_date"].map(di).to_numpy()
    n_idx = df.loc[keep, "point_id"].map(ni).to_numpy()
    rows = np.where(keep)[0]
    Xa[t_idx, n_idx] = X[rows]
    Ya[t_idx, n_idx] = Y[rows]
    Ba[t_idx, n_idx] = B[rows]
    Wa[t_idx, n_idx] = W[rows]
    R[t_idx, n_idx] = rows
    return GraphData(days, nodes, Xa, Ya, Ba, Wa, names, R)


def neighbor_base(gd: GraphData, df: pd.DataFrame, prep: Prep, graph, sources=None) -> np.ndarray:
    """Base forecast for a place WITHOUT its own sensor: [T, N, L] (log1p).

    Same rule as Prep.base, but "yesterday's reading here" is replaced by the
    distance-weighted mean of yesterday's readings at graph neighbors (or their
    last-24 h mean). Used for map grid points, hidden monitors, and for sensors
    hidden by node masking during training, so the model practices this case.

    sources: optional bool mask [N] of nodes allowed to share readings
    (e.g. exclude hidden monitors in the leave-sites-out test).
    """
    from serein.features.graph import idw_neighbor_mean

    T, N, L = gd.base.shape
    df = df.reset_index(drop=True)

    def wide(col):
        a = np.full((T, N), np.nan, np.float32)
        t, n = np.where(gd.row_index >= 0)
        a[t, n] = np.log1p(df[col].clip(lower=0).to_numpy()[gd.row_index[t, n]])
        if sources is not None:
            a[:, ~sources] = np.nan
        return a

    if not prep.use_obs_base:
        return gd.base.copy()
    prev = idw_neighbor_mean(wide("obs_prevday"), graph)
    recent = idw_neighbor_mean(wide("obs_last24"), graph)
    fallback = np.where(np.isfinite(prev), prev, np.where(np.isfinite(recent), recent, prep.global_clim))
    leads = leads_of(df)
    out = np.empty((T, N, L), np.float32)
    for li, lead in enumerate(leads):
        a = np.full((T, N), np.nan, np.float32)
        c = f"aqm_mean_L{lead}"
        if c in df and not any(e.startswith("aqm_") for e in prep.exclude):
            t, n = np.where(gd.row_index >= 0)
            a[t, n] = np.log1p(df[c].clip(lower=0).to_numpy()[gd.row_index[t, n]])
        out[..., li] = np.where(np.isfinite(a), a, fallback)
    return out
