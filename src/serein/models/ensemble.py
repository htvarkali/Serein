"""The same log-space quantile average used during SmokeCast evaluation."""

from __future__ import annotations

import torch
from torch import nn

from serein.models.gnn import SmokeCastGNN


class SmokeCastEnsemble(nn.Module):
    """Average member forecasts without detaching them from gradient attribution.

    Attention shown by ``serein explain`` is the mean of the members' last-layer
    attention, for the same edges and heads. Each member still receives the full
    input graph; calibration is applied once, after this quantile average.
    """

    def __init__(self, members: list[SmokeCastGNN]):
        super().__init__()
        if not members:
            raise ValueError("A SmokeCast ensemble needs at least one member")
        first = members[0]
        if any((m.n_leads, m.nq, m.use_graph) != (first.n_leads, first.nq, first.use_graph)
               for m in members):
            raise ValueError("Ensemble members must share leads, quantiles, and graph settings")
        self.members = nn.ModuleList(members)
        self.n_leads, self.nq = first.n_leads, first.nq
        self.use_graph = first.use_graph
        self.last_attention = None

    def forward(self, x, wind, base, src, dst, bearing, static_attr, xh=None):
        forecasts = [member(x, wind, base, src, dst, bearing, static_attr, xh)
                     for member in self.members]
        attention = [member.last_attention for member in self.members]
        self.last_attention = (torch.stack(attention).mean(0)
                               if all(a is not None for a in attention) else None)
        return torch.stack(forecasts).mean(0)
