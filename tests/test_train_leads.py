import numpy as np
import torch

from serein.features.graph import build_knn_graph
from serein.models.train import TrainConfig, Trainer


def _trainer(train_leads):
    g = build_knn_graph(np.array([45.0, 45.1, 45.2]), np.array([-120.0, -120.1, -120.2]),
                        k=2, max_km=300)
    cfg = TrainConfig(hidden=8, layers=1, heads=2, seed=0, train_leads=train_leads)
    return Trainer(3, 4, g, ["a", "b", "c"], cfg)


def test_train_leads_ignore_the_other_leads():
    q = torch.zeros(1, 3, 4, 5)
    y = torch.zeros(1, 3, 4)
    late = _trainer((2, 3))
    base = late._loss(q, y)
    y_bad = y.clone()
    y_bad[..., :2] = 5.0                       # big errors at leads 0-1 only
    assert torch.equal(late._loss(q, y_bad), base)
    y_bad[..., 2] = 5.0
    assert late._loss(q, y_bad) > base
    assert _trainer(None)._loss(q, y_bad[..., :]) > base
