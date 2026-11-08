"""Figures for the Innovation Brief (TODO D-7), from a backtest output folder.

    uv run python -m serein.eval.figures outputs/backtest/west_us_dev

Colors follow a fixed, colorblind-validated categorical order; the same model
always gets the same color in every figure.
"""

from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e4e3df"
COLORS = {  # fixed slots: blue, orange, aqua, yellow
    "smokecast": "#2a78d6", "noaa_best": "#eb6834", "persistence": "#1baf7a", "gbm": "#eda100",
}
LABELS = {"smokecast": "SmokeCast (ours)", "noaa_best": "NOAA/persistence fallback",
          "persistence": "Yesterday's value", "gbm": "Boosted trees (no graph)"}


def _style(ax):
    ax.spines[["top", "right"]].set_visible(False)
    ax.spines[["left", "bottom"]].set_color(MUTED)
    ax.tick_params(colors=MUTED)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)


def skill_by_lead(run: Path, subset: str = "all", out: Path | None = None):
    met = pd.read_csv(run / "metrics.csv")
    m = met[met["subset"] == subset]
    fig, ax = plt.subplots(figsize=(6.8, 4))
    ends = []
    for model, color in COLORS.items():
        d = m[m["model"] == model].sort_values("lead")
        if d.empty:
            continue
        ax.plot(d["lead"], d["rmse"], "-o", color=color, lw=2, ms=8,
                markeredgecolor="white", markeredgewidth=2, label=LABELS[model])
        ends.append([d["rmse"].iloc[-1], model, d["lead"].iloc[-1]])
    # Direct labels at line ends, nudged apart so they never overlap.
    ends.sort(reverse=True)
    lo, hi = ax.get_ylim()
    gap = 0.06 * (hi - lo)
    for i in range(1, len(ends)):
        ends[i][0] = min(ends[i][0], ends[i - 1][0] - gap)
    for y, model, x in ends:
        ax.annotate(LABELS[model], (x, y), xytext=(10, 0), textcoords="offset points",
                    va="center", color=INK, fontsize=9, annotation_clip=False)
    ax.legend(frameon=False, fontsize=8, loc="upper left")
    ax.set_xticks(sorted(m["lead"].unique()))
    ax.set_xticklabels(["today", "+1 day", "+2 days", "+3 days"][: m["lead"].nunique()])
    ax.set_ylabel("error (RMSE, µg/m³), lower is better", color=MUTED)
    title = {"all": "All site-days", "smoke_yesterday": "Smoke-affected days"}.get(subset, subset)
    ax.set_title(f"Forecast error by lead time: {title}", color=INK, loc="left")
    _style(ax)
    ax.set_xlim(right=ax.get_xlim()[1] + 1.1)
    fig.tight_layout()
    fig.savefig(out or run / f"fig_rmse_by_lead_{subset}.png", dpi=170)
    plt.close(fig)


def warnings_vs_epa(run: Path, out: Path | None = None):
    p = run / "vs_epa_forecast.csv"
    if not p.exists():
        return
    e = pd.read_csv(p)
    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6), sharey=False)
    for ax, metric, label in [(axes[0], "usg_csi", "Warning skill (CSI), higher is better"),
                              (axes[1], "usg_far", "False alarms (FAR), lower is better")]:
        leads = sorted(e["lead"].unique())
        x = np.arange(len(leads))
        for j, (who, color, name) in enumerate([("smokecast", COLORS["smokecast"], "SmokeCast"),
                                                ("epa_forecast", COLORS["noaa_best"], "EPA forecast")]):
            v = [e[(e["lead"] == lead) & (e["who"] == who)][metric].mean() for lead in leads]
            ax.bar(x + (j - 0.5) * 0.38, v, width=0.36, color=color, label=name,
                   edgecolor="white", linewidth=2)
        ax.set_xticks(x)
        ax.set_xticklabels(["today", "+1", "+2", "+3"][: len(leads)])
        ax.set_title(label, color=INK, loc="left", fontsize=10)
        _style(ax)
    axes[0].legend(frameon=False)
    fig.suptitle("Orange-or-worse (USG+) warnings by reporting area vs. EPA's official forecast",
                 color=INK, fontsize=11)
    fig.tight_layout()
    fig.savefig(out or run / "fig_warnings_vs_epa.png", dpi=170)
    plt.close(fig)


def case_study(run: Path, point_id: str, lead: int = 1, out: Path | None = None):
    pr = pd.read_parquet(run / "predictions.parquet")
    d = pr[pr["point_id"] == point_id].sort_values("issue_date")
    if d.empty:
        return
    t = pd.to_datetime(d["issue_date"]) + pd.Timedelta(days=lead)
    fig, ax = plt.subplots(figsize=(9, 3.8))
    ax.fill_between(t, d[f"smokecast_lo_L{lead}"], d[f"smokecast_hi_L{lead}"],
                    color=COLORS["smokecast"], alpha=0.18, lw=0, label="SmokeCast 90% range")
    ax.plot(t, d[f"smokecast_L{lead}"], color=COLORS["smokecast"], lw=2, label=LABELS["smokecast"])
    if f"noaa_best_L{lead}" in d:
        ax.plot(t, d[f"noaa_best_L{lead}"], color=COLORS["noaa_best"], lw=2, label=LABELS["noaa_best"])
    ax.plot(t, d[f"y_L{lead}"], "o", color=INK, ms=4, label="Observed")
    ax.axhline(35.5, color=MUTED, lw=0.8, ls="--")
    ax.annotate("Unhealthy for Sensitive Groups", (t.iloc[0], 35.5), xytext=(0, 3),
                textcoords="offset points", color=MUTED, fontsize=8)
    ax.set_ylabel("daily PM2.5 (µg/m³)", color=MUTED)
    ax.set_title(f"Site {point_id}: forecasts made {lead} day(s) ahead", color=INK, loc="left")
    ax.legend(frameon=False, ncol=4, fontsize=8, loc="upper left")
    _style(ax)
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(out or run / f"fig_case_{point_id}_L{lead}.png", dpi=170)
    plt.close(fig)


def make_all(run: Path):
    skill_by_lead(run, "all")
    skill_by_lead(run, "smoke_yesterday")
    warnings_vs_epa(run)
    pr = pd.read_parquet(run / "predictions.parquet")
    # Case study: the site with the highest observed day in the scored period.
    top = pr.loc[pr["y_L1"].idxmax(), "point_id"] if pr["y_L1"].notna().any() else None
    if top is not None:
        case_study(run, top, lead=1)
    calibration_by_level(run)
    improvement_map(run, lead=1)
    peak_report(run).to_csv(run / "peak_report.csv", index=False)




# ----------------------------------------------------------------- diagnostics
def peak_report(run: Path, thr: float = 35.5) -> pd.DataFrame:
    """How well are smoky days (observed >= thr) captured? Outcome-based diagnostic."""
    pr = pd.read_parquet(run / "predictions.parquet")
    rows = []
    for lead in range(4):
        y = pr.get(f"y_L{lead}")
        if y is None:
            continue
        m = np.isfinite(y) & (y >= thr)
        if m.sum() == 0:
            continue
        rec = {"lead": lead, "n_smoky_site_days": int(m.sum())}
        for model in ["smokecast", "noaa_best", "persistence"]:
            c = f"{model}_L{lead}"
            if c in pr:
                ok = m & np.isfinite(pr[c])
                rec[f"{model}_n"] = int(ok.sum())
                rec[f"{model}_median_ratio"] = (float(np.median(pr.loc[ok, c] / y[ok]))
                                                if ok.any() else np.nan)
        lo, hi = pr[f"smokecast_lo_L{lead}"], pr[f"smokecast_hi_L{lead}"]
        paired = m & np.isfinite(lo) & np.isfinite(hi)
        if (lo[paired] > hi[paired]).any():
            raise ValueError("interval lower bounds must not exceed upper bounds")
        rec["smokecast_n_intervals"] = int(paired.sum())
        rec["smokecast_in_90pct_range"] = (float(((y >= lo) & (y <= hi))[paired].mean())
                                           if paired.any() else np.nan)
        rows.append(rec)
    return pd.DataFrame(rows)


def calibration_by_level(run: Path, out: Path | None = None):
    """Coverage of the 90% range, split by how smoky the forecast was (D-7b)."""
    pr = pd.read_parquet(run / "predictions.parquet")
    bins = [-np.inf, 12, 35.5, np.inf]
    names = ["clean (<12)", "moderate (12-<35.5)", "smoky (>=35.5)"]
    fig, ax = plt.subplots(figsize=(6.4, 3.8))
    width = 0.2
    for lead in range(4):
        if f"y_L{lead}" not in pr:
            continue
        y, med = pr[f"y_L{lead}"], pr[f"smokecast_L{lead}"]
        lo, hi = pr[f"smokecast_lo_L{lead}"], pr[f"smokecast_hi_L{lead}"]
        paired = np.isfinite(y) & np.isfinite(med) & np.isfinite(lo) & np.isfinite(hi)
        if (lo[paired] > hi[paired]).any():
            plt.close(fig)
            raise ValueError("interval lower bounds must not exceed upper bounds")
        inside = (y >= lo) & (y <= hi)
        grp = pd.cut(med, bins, labels=names, right=False)
        cov = inside[paired].groupby(grp[paired], observed=False).mean()
        x = np.arange(len(names)) + (lead - 1.5) * width
        ax.bar(x, cov.to_numpy(), width=width * 0.9,
               color=["#2a78d6", "#1baf7a", "#eda100", "#6250d6"][lead],
               label=["today", "+1 day", "+2 days", "+3 days"][lead])
    ax.axhline(0.9, color=INK, lw=1, ls="--")
    ax.annotate("target 90%", (2.45, 0.9), xytext=(0, 3), textcoords="offset points",
                color=INK, fontsize=8, ha="right")
    ax.set_xticks(range(len(names)))
    ax.set_xticklabels(names)
    ax.set_ylim(0, 1.0)
    ax.set_ylabel("share of days inside the 90% range", color=MUTED)
    ax.set_title("Interval coverage by predicted smoke level", color=INK, loc="left")
    ax.legend(frameon=False, ncol=4, fontsize=8, loc="lower left")
    _style(ax)
    fig.tight_layout()
    fig.savefig(out or run / "fig_calibration_by_level.png", dpi=170)
    plt.close(fig)


def improvement_map(run: Path, lead: int = 1, out: Path | None = None):
    """Map: % lower error than the NOAA/persistence fallback, per monitor (D-7b)."""
    from serein.data.points import load_points
    from serein.models.infer import state_boundaries

    pr = pd.read_parquet(run / "predictions.parquet")
    y, s, n = pr[f"y_L{lead}"], pr[f"smokecast_L{lead}"], pr[f"noaa_best_L{lead}"]
    ok = y.notna() & s.notna() & n.notna()
    d = pr[ok].assign(es=(s - y)[ok] ** 2, en=(n - y)[ok] ** 2)
    g = d.groupby("point_id").agg(es=("es", "mean"), en=("en", "mean"), cnt=("es", "size"))
    g = g[g["cnt"] >= 20]
    g["gain"] = 100 * (1 - np.sqrt(g["es"]) / np.sqrt(g["en"]))
    pts = load_points(run.name.split("_")[0] + "_" + run.name.split("_")[1]).set_index("point_id")
    g = g.join(pts[["lat", "lon"]], how="inner")
    fig, ax = plt.subplots(figsize=(5, 7))
    st = state_boundaries()
    if st is not None:
        st.boundary.plot(ax=ax, color=MUTED, linewidth=0.5)
    # Diverging: blue = SmokeCast better, orange = fallback better, gray near 0.
    from matplotlib.colors import LinearSegmentedColormap, TwoSlopeNorm
    cmap = LinearSegmentedColormap.from_list("div", ["#eb6834", "#e9e8e4", "#2a78d6"])
    sc = ax.scatter(g["lon"], g["lat"], c=g["gain"].clip(-50, 80), cmap=cmap,
                    norm=TwoSlopeNorm(vcenter=0, vmin=-50, vmax=80), s=26,
                    edgecolors=INK, linewidths=0.3)
    cb = fig.colorbar(sc, ax=ax, shrink=0.6)
    cb.set_label("% lower error than NOAA/persistence fallback", color=MUTED)
    ax.set_xlim(g["lon"].min() - 0.5, g["lon"].max() + 0.5)
    ax.set_ylim(g["lat"].min() - 0.5, g["lat"].max() + 0.5)
    ax.set_aspect(1 / np.cos(np.radians(g["lat"].mean())))
    ax.set_xticks([])
    ax.set_yticks([])
    ax.set_xlabel("")
    ax.set_ylabel("")
    better = (g["gain"] > 0).mean()
    ax.set_title(f"Where SmokeCast helps (+{lead} day): better at {better:.0%} of monitors",
                 color=INK, loc="left", fontsize=10)
    fig.tight_layout()
    fig.savefig(out or run / f"fig_improvement_map_L{lead}.png", dpi=170)
    plt.close(fig)
    return g


if __name__ == "__main__":
    make_all(Path(sys.argv[1]))
