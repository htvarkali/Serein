"""Explainability helpers (B-11)."""

from datetime import date

import numpy as np
import pytest
import torch

from serein.eval.explain import explain_point, feature_group, integrated_gradients


def test_feature_groups():
    assert feature_group("obs_last24") == "live monitor readings"
    assert feature_group("obs_last24__missing") == "live monitor readings"
    assert feature_group("hrrr_pm_L1") == "HRRR smoke forecast"
    assert feature_group("hrrr_t2m_L1") == "HRRR weather"
    assert feature_group("aqm_mean_L2") == "NOAA AQM forecast"
    assert feature_group("frp_upwind_250") == "satellite fire detections"
    assert feature_group("hms_prev") == "smoke plume maps (HMS)"
    assert feature_group("doy_sin") == "place and season"


def test_integrated_gradients_add_up_to_the_change():
    w = torch.tensor([0.5, -2.0, 1.0])
    f = lambda x: torch.tanh(x @ w) + (x[1] * x[2])   # nonlinear, with an interaction
    x, x0 = torch.tensor([1.0, 0.3, -0.7]), torch.zeros(3)
    a = integrated_gradients(f, x, x0, steps=200)
    assert abs(float(a.sum()) - float(f(x) - f(x0))) < 1e-3


class _Model:
    nq, last_attention = 3, None


class _Inputs:
    # One place: readings raise the forecast (x**3, 0 -> 1), weather lowers it (-0.9 x).
    def __init__(self):
        self.nodes, self.leads, self.graph, self.model = ["A"], [1], None, _Model()
        self.X = np.array([[1.0, 1.0]], np.float32)
        self.feat_names = ["obs_last24", "hrrr_t2m_L1"]
        self.base = np.zeros((1, 1), np.float32)

    def run(self, x):
        v = x[0, 0, 0] ** 3 - 0.9 * x[0, 0, 1]
        return v.reshape(1, 1, 1, 1).repeat(1, 1, 1, 3)


def test_groups_pulling_both_ways_keep_their_direction(monkeypatch):
    from serein.models import infer

    monkeypatch.setattr(infer, "build_inputs", lambda *args, **kwargs: _Inputs())
    for steps in (1, 4):
        ex = explain_point(None, date(2023, 8, 18), None, "A", lead=1, steps=steps)
        readings, weather = ex.groups["live monitor readings"], ex.groups["HRRR weather"]
        assert readings > 1 > weather
        assert np.log(readings) + np.log(weather) == pytest.approx(0.1, abs=1e-5)
    # Few steps leave IG 0.016 short; that leftover must not inflate readings past x e.
    assert readings == pytest.approx(np.e, rel=0.01)
    assert weather == pytest.approx(np.exp(-0.9), rel=0.01)
