"""Why did SmokeCast forecast this? (TODO B-11)

For one place, day and lead time, two answers:

1. **Neighbors.** Which monitors the graph listened to, with their attention
   weights from the last message-passing layer (averaged over heads). Weights for
   one place add up to 1.
2. **Inputs.** How much each group of inputs (live monitor readings, HRRR smoke,
   HRRR weather, NOAA AQM, fire detections, smoke plumes, place and season) moved
   the median forecast, by integrated gradients (Sundararajan et al., ICML 2017).
   The starting point is an "average day": every input at its training mean, with
   the same missing-data pattern and the same base forecast. Attributions add up to
   the gap between that and the real forecast, so each group gets a share of it.
   They are shown as multipliers on PM2.5, e.g. x1.40 = "raised the forecast 40%".

Inputs at the place itself and at its neighbors are summed, so "live monitor
readings" also covers the readings of nearby monitors that reached it through
the graph.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from pathlib import Path

import numpy as np
import torch

from serein.config import Study

GROUPS = [  # (label, feature-name prefixes); first match wins
    ("live monitor readings", ("obs_", "site_clim", "site_bg")),
    ("HRRR smoke forecast", ("hrrr_smoke", "hrrr_colmd", "hrrr_pm")),
    ("HRRR weather", ("hrrr_", "wind_now")),
    ("NOAA AQM forecast", ("aqm_",)),
    ("satellite fire detections", ("frp", "fire_dist")),
    ("smoke plume maps (HMS)", ("hms_",)),
    ("place and season", ("lat", "lon", "doy")),
]


def feature_group(name: str) -> str:
    base = name.removesuffix("__missing")
    for label, prefixes in GROUPS:
        if base.startswith(prefixes):
            return label
    return "other"


@dataclass
class Explanation:
    point_id: str
    day: date
    lead: int
    pm_median: float          # µg/m³
    pm_base: float            # starting forecast the model corrects (AQM or persistence)
    pm_average_day: float     # forecast with every input at its training mean
    neighbors: list           # [(point_id, km, weight)], largest weight first
    groups: dict              # label -> multiplier on PM2.5 (log-space attribution)

    def text(self) -> str:
        head = (f"{self.point_id}, {self.day:%Y-%m-%d}, {self.lead} day(s) ahead: "
                f"median {self.pm_median:.1f} µg/m³ (starting forecast {self.pm_base:.1f}, "
                f"average-day inputs {self.pm_average_day:.1f})")
        lines = [head, "", "Inputs that moved it (x = multiplier on PM2.5 + 1):"]
        for g, m in sorted(self.groups.items(), key=lambda kv: -abs(np.log(kv[1]))):
            lines.append(f"  {g:28s} x{m:.2f}")
        if self.neighbors:
            lines += ["", "Neighbors the graph listened to (last layer):"]
            lines += [f"  {p:14s} {km:6.1f} km  weight {w:.2f}" for p, km, w in self.neighbors]
        return "\n".join(lines)


def integrated_gradients(f, x: torch.Tensor, x0: torch.Tensor, steps: int = 32) -> torch.Tensor:
    """Riemann (midpoint) integrated gradients of scalar f along x0 -> x."""
    total = torch.zeros_like(x)
    for a in (torch.arange(steps, dtype=x.dtype) + 0.5) / steps:
        xi = (x0 + a * (x - x0)).detach().requires_grad_(True)
        (g,) = torch.autograd.grad(f(xi), xi)
        total += g
    return (x - x0) * total / steps


def explain_point(study: Study, day: date, run_dir: Path, point_id: str, lead: int = 1,
                  steps: int = 32, top_k: int = 5) -> Explanation:
    from serein.models.infer import build_inputs

    inp = build_inputs(study, day, run_dir, with_grid=True)
    if point_id not in inp.nodes:
        raise KeyError(f"{point_id} is not a monitor or grid cell in this run")
    i, li = inp.nodes.index(point_id), inp.leads.index(lead)
    mid = inp.model.nq // 2
    t = lambda a: torch.as_tensor(a).unsqueeze(0)
    g = inp.graph

    # Attributions are for today's inputs; past days (history models) stay as they were.
    def f(x):
        return inp.run(x)[0, i, li, mid]

    x = t(inp.X)
    flags = torch.tensor([n.endswith("__missing") for n in inp.feat_names])
    x0 = torch.where(flags, x, torch.zeros_like(x))   # training mean, same missingness
    with torch.no_grad():
        y, y0 = float(f(x)), float(f(x0))
        f(x)  # leaves the real day's attention in model.last_attention
        att = inp.model.last_attention
    attr = integrated_gradients(f, x, x0, steps)[0].sum(0).numpy()  # per feature
    groups: dict = {}
    for name, a in zip(inp.feat_names, attr, strict=True):
        groups[feature_group(name)] = groups.get(feature_group(name), 0.0) + float(a)
    # IG is exact only in the limit; spread the small leftover proportionally.
    gap, s = y - y0, sum(groups.values())
    if abs(s) > 1e-9:
        groups = {k: v * gap / s for k, v in groups.items()}
    neighbors = []
    if att is not None:
        e = np.where(g.dst == i)[0]
        w = att[0, e].mean(-1).numpy()
        for k in np.argsort(-w)[:top_k]:
            neighbors.append((inp.nodes[g.src[e[k]]], float(g.dist_km[e[k]]), float(w[k])))
    return Explanation(point_id, day, lead, float(np.expm1(y)), float(np.expm1(inp.base[i, li])),
                       float(np.expm1(y0)), neighbors,
                       {k: float(np.exp(v)) for k, v in groups.items() if abs(v) > 1e-4})
