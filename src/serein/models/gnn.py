"""SmokeCast: a wind-aware graph neural network that corrects NOAA's forecast.

Plain-English version
---------------------
1. Every sensor turns its own inputs (recent readings, NOAA forecasts, fires,
   weather) into a short summary vector ("embedding").
2. Message passing, repeated 3 times: every sensor looks at its neighbors'
   summaries. An attention score decides how much to trust each neighbor, using
   distance, direction, and whether the wind blows from the neighbor toward it.
   (Optional, ``history`` > 1: step 1 first reads the last few days of each sensor's
   inputs with a small recurrent network (a GRU), so a sensor can notice things like
   "NOAA has run high here all week". history = 1 is the original model.)
3. A final layer outputs, for each lead day, five quantiles (5%, 25%, 50%, 75%,
   95%) of the CORRECTION to the base forecast (in log space).

The quantiles are built as median ± sums of positive steps, so they can never
cross (the 95% value is always above the 75% value, etc.).
"""

from __future__ import annotations

import os

# cuBLAS needs this before its first use for repeatable matrix products
# (training and inference turn on torch.use_deterministic_algorithms).
os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")

import torch
import torch.nn.functional as F
from torch import nn

QUANTILES = (0.05, 0.25, 0.5, 0.75, 0.95)


def mlp(i, h, o, drop=0.0):
    return nn.Sequential(nn.Linear(i, h), nn.GELU(), nn.Dropout(drop), nn.Linear(h, o))


def scatter_softmax(logits: torch.Tensor, index: torch.Tensor, n: int) -> torch.Tensor:
    """Softmax of logits [B, E, H] grouped by destination index [E] (n groups)."""
    B, E, H = logits.shape
    idx = index.view(1, E, 1).expand(B, E, H)
    mx = torch.full((B, n, H), -1e30, device=logits.device, dtype=logits.dtype)
    mx = mx.scatter_reduce(1, idx, logits, reduce="amax", include_self=True)
    ex = torch.exp(logits - mx.gather(1, idx))
    den = torch.zeros((B, n, H), device=logits.device, dtype=logits.dtype).scatter_add(1, idx, ex)
    return ex / (den.gather(1, idx) + 1e-12)


class WindEdgeAttention(nn.Module):
    """One round of message passing with multi-head edge attention."""

    def __init__(self, hidden: int, edge_dim: int, heads: int = 4, drop: float = 0.1):
        super().__init__()
        self.heads = heads
        self.msg = mlp(2 * hidden + edge_dim, hidden, hidden, drop)
        self.att = mlp(2 * hidden + edge_dim, hidden // 2, heads)
        self.norm1 = nn.LayerNorm(hidden)
        self.ff = mlp(hidden, 2 * hidden, hidden, drop)
        self.norm2 = nn.LayerNorm(hidden)

    def forward(self, h, src, dst, e):
        B, N, H = h.shape
        z = torch.cat([h[:, src], h[:, dst], e], dim=-1)          # [B, E, 2H+De]
        a = scatter_softmax(self.att(z), dst, N)                  # [B, E, heads]
        m = self.msg(z).view(B, -1, self.heads, H // self.heads)  # [B, E, heads, H/heads]
        m = (m * a.unsqueeze(-1)).reshape(B, -1, H)
        agg = torch.zeros_like(h).index_add_(1, dst, m)
        h = self.norm1(h + agg)
        return self.norm2(h + self.ff(h)), a


class SmokeCastGNN(nn.Module):
    def __init__(self, n_feat: int, n_leads: int, hidden: int = 96, layers: int = 3,
                 heads: int = 4, static_edge_dim: int = 4, drop: float = 0.1,
                 quantiles=QUANTILES, use_graph: bool = True, history: int = 1):
        super().__init__()
        self.history = history
        self.q = torch.tensor(quantiles)
        self.n_leads, self.nq = n_leads, len(quantiles)
        self.use_graph = use_graph
        edge_dim = static_edge_dim + 3  # + wind-from-src-toward-dst, |wind| src, same at dst
        self.enc = mlp(n_feat, hidden, hidden, drop)
        if history > 1:
            self.gru = nn.GRU(hidden, hidden, batch_first=True)
        self.layers = nn.ModuleList(
            [WindEdgeAttention(hidden, edge_dim, heads, drop) for _ in range(layers)])
        self.head = mlp(hidden + n_feat, hidden, n_leads * self.nq)
        self.last_attention = None

    def edge_features(self, wind, src, dst, bearing, static_attr):
        # Wind component blowing from src toward dst (m/s / 10).
        # bearing is direction src->dst measured from north; unit vector (sin b, cos b).
        ux, uy = torch.sin(bearing), torch.cos(bearing)
        ws = wind[:, src]  # [B, E, 2]
        wd = wind[:, dst]
        toward_src = (ws[..., 0] * ux + ws[..., 1] * uy) / 10.0
        toward_dst = (wd[..., 0] * ux + wd[..., 1] * uy) / 10.0
        speed = ws.norm(dim=-1) / 10.0
        B = wind.shape[0]
        st = static_attr.unsqueeze(0).expand(B, -1, -1)
        return torch.cat([st, toward_src.unsqueeze(-1), toward_dst.unsqueeze(-1),
                          speed.unsqueeze(-1)], dim=-1)

    def forward(self, x, wind, base, src, dst, bearing, static_attr, xh=None):
        """x [B,N,F], wind [B,N,2], base [B,N,L] -> quantiles [B,N,L,Q] (log1p space).

        xh [B,N,K-1,F]: inputs of the previous K-1 days, oldest first (history > 1).
        """
        if self.history > 1:
            if xh is None:
                raise ValueError("this model reads past days: pass xh")
            seq = self.enc(torch.cat([xh, x.unsqueeze(2)], 2))       # [B,N,K,H]
            B, N, K, H = seq.shape
            _, last = self.gru(seq.reshape(B * N, K, H))
            h = last[-1].view(B, N, H)
        else:
            h = self.enc(x)
        if self.use_graph:
            e = self.edge_features(wind, src, dst, bearing, static_attr)
            for layer in self.layers:
                h, a = layer(h, src, dst, e)
            self.last_attention = a.detach()
        out = self.head(torch.cat([h, x], -1)).view(*x.shape[:2], self.n_leads, self.nq)
        mid = self.nq // 2
        median = out[..., mid]
        up = F.softplus(out[..., mid + 1:]).cumsum(-1)
        down = F.softplus(out[..., :mid].flip(-1)).cumsum(-1).flip(-1)
        q = torch.cat([median.unsqueeze(-1) - down, median.unsqueeze(-1),
                       median.unsqueeze(-1) + up], dim=-1)
        return q + base.unsqueeze(-1)


def pinball_loss(q_pred: torch.Tensor, y: torch.Tensor, quantiles: torch.Tensor,
                 weight: torch.Tensor | None = None) -> torch.Tensor:
    """Quantile ("pinball") loss, ignoring NaN targets. q_pred [...,Q], y [...]."""
    ok = torch.isfinite(y)
    yy = torch.where(ok, y, torch.zeros_like(y)).unsqueeze(-1)
    diff = yy - q_pred
    qs = quantiles.to(q_pred.device)
    loss = torch.maximum(qs * diff, (qs - 1) * diff).mean(-1)
    if weight is not None:
        loss = loss * weight
    loss = torch.where(ok, loss, torch.zeros_like(loss))
    return loss.sum() / ok.sum().clamp(min=1)
