"""Plot paired spatial-development errors with their scored populations."""

from __future__ import annotations

import numpy as np
import pandas as pd


def plot_spatial_scores(summary: pd.DataFrame, lead: int, output):
    """Show RMSE values and paired RMSE differences, without inventing bounds."""
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    from matplotlib.figure import Figure

    selected = summary.loc[summary.lead.eq(lead)]
    if selected.empty:
        raise ValueError(f"no spatial summaries for lead {lead}")
    models = selected.model.drop_duplicates().tolist()
    if selected.duplicated(["model", "distance_band"]).any():
        raise ValueError("spatial plot requires unique model/distance-band rows")
    reference = selected.reference_model.drop_duplicates().tolist()
    if len(reference) != 1 or reference[0] not in models:
        raise ValueError("spatial plot requires one included reference model")
    bands = selected.loc[selected.model.eq(reference[0])].sort_values("distance_band")
    labels = []
    for row in bands.itertuples():
        if row.distance_band == -1:
            label = "Pooled"
        elif np.isnan(row.distance_hi_km):
            label = f"{row.distance_lo_km:g}+ km"
        else:
            label = f"{row.distance_lo_km:g} to <{row.distance_hi_km:g} km"
        labels.append(f"{label}\n{row.n_sites_scored}/{row.n_sites} sites; {row.n_scored} rows")
    figure = Figure(figsize=(max(10, len(bands) * 1.9), 7), layout="constrained")
    FigureCanvasAgg(figure)
    axes = figure.subplots(2, 1, sharex=True)
    x = np.arange(len(bands))
    width = .75 / len(models)
    for index, model in enumerate(models):
        rows = selected.loc[selected.model.eq(model)].set_index("distance_band").reindex(bands.distance_band)
        positions = x + (index - (len(models) - 1) / 2) * width
        ok = rows.n_scored.gt(0) & np.isfinite(rows.rmse)
        line, = axes[0].plot(positions[ok], rows.loc[ok, "rmse"], "o", label=model)
        if model == reference[0]:
            continue
        axes[1].plot(positions[ok], rows.loc[ok, "rmse_difference"], "o", color=line.get_color(), label=model)
        bounded = ok & np.isfinite(rows.rmse_difference_ci_lo) & np.isfinite(rows.rmse_difference_ci_hi)
        # Percentile bounds need not contain the point estimate.
        axes[1].vlines(positions[bounded], rows.loc[bounded, "rmse_difference_ci_lo"],
                       rows.loc[bounded, "rmse_difference_ci_hi"], color=line.get_color())
    axes[0].set_ylabel("RMSE (micrograms/m3)")
    axes[0].set_ylim(bottom=0)
    axes[0].legend()
    axes[1].axhline(0, color="0.5", linestyle=":", linewidth=1)
    axes[1].set_ylabel(f"RMSE minus {reference[0]}\n(micrograms/m3)")
    axes[1].set_xticks(x, labels, fontsize=8)
    axes[1].set_xlabel("Nearest declared reference sensor; scored/declared sites and common scored rows")
    for axis in axes:
        axis.grid(axis="y", alpha=.2)
    figure.suptitle(f"Lead {lead}: exploratory fixed-site development scores\n"
                    "Bars: paired day-block 95% bounds; no spatial or multiplicity guarantee")
    figure.savefig(output, dpi=150)
