"""Training loop for SmokeCast.

Node masking (TODO B-7): on each training step we hide the sensor readings of a
random 15% of sensors, but still ask the model to forecast them. That teaches it
to forecast places with NO sensor, using neighbors, which is what the
neighborhood map needs.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass

import numpy as np
import torch

from serein.features.graph import Graph
from serein.features.prepare import GraphData, is_sensor_feature
from serein.models.gnn import QUANTILES, SmokeCastGNN, pinball_loss


@dataclass
class TrainConfig:
    hidden: int = 64
    layers: int = 2
    heads: int = 4
    dropout: float = 0.3
    lr: float = 2e-3
    weight_decay: float = 1e-3
    epochs: int = 300
    patience: int = 30
    batch_days: int = 8
    node_mask_frac: float = 0.15
    smoke_weight: float = 6.0   # weight for targets >= 35.5 µg/m³ (chosen on dev weeks, B-13)
    seed: int = 0
    use_graph: bool = True
    # Same seed => identical model. The graph step adds messages with GPU atomics,
    # whose order changes run to run; without this, two runs of the same code moved
    # the day-2 warning rate by 7 points. Costs ~1.8x training time.
    deterministic: bool = True
    history: int = 1            # days of inputs each sensor reads (1 = today only)


def _device():
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


class Trainer:
    def __init__(self, n_feat: int, n_leads: int, graph: Graph, feat_names: list[str],
                 cfg: TrainConfig | None = None):
        cfg = cfg or TrainConfig()
        self.cfg, self.dev = cfg, _device()
        torch.use_deterministic_algorithms(cfg.deterministic)
        torch.manual_seed(cfg.seed)
        np.random.seed(cfg.seed)
        self.model = SmokeCastGNN(n_feat, n_leads, cfg.hidden, cfg.layers, cfg.heads,
                                  drop=cfg.dropout, use_graph=cfg.use_graph,
                                  history=cfg.history).to(self.dev)
        self.src = torch.as_tensor(graph.src, device=self.dev)
        self.dst = torch.as_tensor(graph.dst, device=self.dev)
        self.bearing = torch.as_tensor(graph.bearing, dtype=torch.float32, device=self.dev)
        self.eattr = torch.as_tensor(graph.edge_attr, device=self.dev)
        self.q = torch.tensor(QUANTILES, device=self.dev)
        # Columns to hide during node masking: obs values and their missing flags.
        self.obs_val = [i for i, n in enumerate(feat_names)
                        if is_sensor_feature(n) and not n.endswith("__missing")]
        self.obs_flag = [i for i, n in enumerate(feat_names)
                         if is_sensor_feature(n) and n.endswith("__missing")]

    def _tensors(self, gd: GraphData, idx):
        f = lambda a: torch.as_tensor(a[idx], device=self.dev)
        xh = f(gd.hist) if self.cfg.history > 1 else None
        return f(gd.X), f(gd.wind), f(gd.base), f(gd.Y), xh

    def _forward(self, x, w, b, xh=None):
        return self.model(x, w, b, self.src, self.dst, self.bearing, self.eattr, xh)

    def _hide(self, x, m):
        """Zero sensor readings (and set their missing flags) where mask m is True."""
        x = x.clone()
        xv = x[..., self.obs_val]
        xv[m] = 0.0
        x[..., self.obs_val] = xv
        if self.obs_flag:
            xf = x[..., self.obs_flag]
            xf[m] = 1.0
            x[..., self.obs_flag] = xf
        return x

    def _mask_nodes(self, x, b=None, b_nbr=None, xh=None):
        """Hide readings of random sensors; their base forecast switches to the
        neighbor-based one (as for a place with no sensor). Their past days' readings
        are hidden too, or the memory would leak them."""
        if self.cfg.node_mask_frac <= 0 or not self.obs_val:
            return x, b, xh
        B, N, _ = x.shape
        m = torch.rand(B, N, device=x.device) < self.cfg.node_mask_frac
        if b is not None and b_nbr is not None:
            b = torch.where(m.unsqueeze(-1), b_nbr, b)
        x = self._hide(x, m)
        if xh is not None:
            xh = self._hide(xh, m.unsqueeze(-1).expand(-1, -1, xh.shape[2]))
        return x, b, xh

    def _loss(self, q, y):
        w = None
        if self.cfg.smoke_weight != 1.0:
            w = torch.where(torch.nan_to_num(y) > np.log1p(35.5),
                            torch.tensor(self.cfg.smoke_weight, device=y.device),
                            torch.tensor(1.0, device=y.device))
        return pinball_loss(q, y, self.q, w)

    @torch.no_grad()
    def evaluate(self, gd: GraphData) -> float:
        self.model.eval()
        tot, n = 0.0, 0
        for s in range(0, len(gd.days), 16):
            idx = np.arange(s, min(s + 16, len(gd.days)))
            x, w, b, y, xh = self._tensors(gd, idx)
            k = torch.isfinite(y).sum().item()
            tot += self._loss(self._forward(x, w, b, xh), y).item() * k
            n += k
        return tot / max(n, 1)

    def fit(self, train: GraphData, val: GraphData, log=print) -> dict:
        opt = torch.optim.AdamW(self.model.parameters(), lr=self.cfg.lr,
                                weight_decay=self.cfg.weight_decay)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=self.cfg.epochs)
        best, best_state, bad, hist = np.inf, None, 0, []
        T = len(train.days)
        for ep in range(self.cfg.epochs):
            self.model.train()
            perm = np.random.permutation(T)
            tl = []
            for s in range(0, T, self.cfg.batch_days):
                idx = perm[s:s + self.cfg.batch_days]
                x, w, b, y, xh = self._tensors(train, idx)
                b_nbr = (torch.as_tensor(train.base_nbr[idx], device=self.dev)
                         if train.base_nbr is not None else None)
                x, b, xh = self._mask_nodes(x, b, b_nbr, xh)
                loss = self._loss(self._forward(x, w, b, xh), y)
                opt.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), 1.0)
                opt.step()
                tl.append(loss.item())
            sched.step()
            vl = self.evaluate(val)
            hist.append((ep, float(np.mean(tl)), vl))
            if vl < best - 1e-5:
                best, best_state, bad = vl, copy.deepcopy(self.model.state_dict()), 0
            else:
                bad += 1
            if ep % 10 == 0 or bad == 0:
                log(f"  epoch {ep:3d} train {np.mean(tl):.4f} val {vl:.4f}{' *' if bad == 0 else ''}")
            if bad >= self.cfg.patience:
                log(f"  early stop at epoch {ep}; best val {best:.4f}")
                break
        if best_state is not None:
            self.model.load_state_dict(best_state)
        return {"best_val": best, "history": hist}

    @torch.no_grad()
    def predict(self, gd: GraphData) -> np.ndarray:
        """Quantiles [T, N, L, Q] in log1p space."""
        self.model.eval()
        outs = []
        for s in range(0, len(gd.days), 16):
            idx = np.arange(s, min(s + 16, len(gd.days)))
            x, w, b, _, xh = self._tensors(gd, idx)
            outs.append(self._forward(x, w, b, xh).cpu().numpy())
        return np.concatenate(outs, 0)
