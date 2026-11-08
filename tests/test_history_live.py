"""Memory of past days (B-18), live-forecast helpers (D-11), partial AirNow days."""

from datetime import date, timedelta

import numpy as np
import pandas as pd
import torch

from serein.features.graph import build_knn_graph
from serein.features.prepare import GraphData, history_from
from serein.models.gnn import SmokeCastGNN
from serein.models.train import TrainConfig, Trainer


def _gd(days, n=3, f=4):
    X = np.arange(len(days) * n * f, dtype=np.float32).reshape(len(days), n, f)
    names = ["obs_last1", "obs_last1__missing", "aqm_mean_L0", "lat"]
    return GraphData(days, [f"s{i}" for i in range(n)], X, np.zeros((len(days), n, 1)),
                     np.zeros((len(days), n, 1)), np.zeros((len(days), n, 2)), names,
                     np.zeros((len(days), n), np.int64))


def test_history_takes_previous_days_oldest_first_and_marks_gaps_missing():
    d0 = date(2023, 6, 1)
    days = [d0 + timedelta(days=k) for k in (0, 1, 2, 4)]  # day 3 is absent
    full = _gd(days)
    h = history_from(full, [days[2], days[3]], k=3)
    assert h.shape == (2, 3, 2, 4)
    np.testing.assert_array_equal(h[0, :, 0], full.X[0])  # 2 days before June 3
    np.testing.assert_array_equal(h[0, :, 1], full.X[1])  # 1 day before
    # June 5: June 3 exists, June 4 does not -> all-missing row (flag 1, values 0).
    np.testing.assert_array_equal(h[1, :, 0], full.X[2])
    np.testing.assert_array_equal(h[1, :, 1], np.tile([0, 1, 0, 0], (3, 1)))


def test_history_model_uses_past_days():
    torch.manual_seed(0)
    m = SmokeCastGNN(n_feat=4, n_leads=2, hidden=16, layers=1, history=3, drop=0.0).eval()
    g = build_knn_graph(np.array([37.0, 37.1, 37.2]), np.array([-122.0, -122.1, -122.2]), k=2)
    a = lambda v: torch.as_tensor(v)
    x, w, b = torch.randn(1, 3, 4), torch.zeros(1, 3, 2), torch.zeros(1, 3, 2)
    xh = torch.randn(1, 3, 2, 4)
    args = (a(g.src), a(g.dst), a(g.bearing).float(), a(g.edge_attr))
    q1 = m(x, w, b, *args, xh)
    q2 = m(x, w, b, *args, xh + 1.0)
    assert q1.shape == (1, 3, 2, 5)
    assert not torch.allclose(q1, q2)  # changing yesterday changes today's forecast


def test_node_masking_also_hides_past_readings():
    g = build_knn_graph(np.array([37.0, 37.1]), np.array([-122.0, -122.1]), k=1)
    names = ["obs_last1", "obs_last1__missing", "aqm_mean_L0"]
    cfg = TrainConfig(node_mask_frac=1.0, history=3, hidden=8, layers=1, deterministic=False)
    tr = Trainer(3, 1, g, names, cfg)
    x = torch.ones(1, 2, 3)
    xh = torch.ones(1, 2, 2, 3)
    x2, _, xh2 = tr._mask_nodes(x, None, None, xh)
    assert torch.all(x2[..., 0] == 0) and torch.all(x2[..., 1] == 1) and torch.all(x2[..., 2] == 1)
    assert torch.all(xh2[..., 0] == 0) and torch.all(xh2[..., 1] == 1) and torch.all(xh2[..., 2] == 1)


def test_warn_cutoffs_read_from_old_report(tmp_path):
    from serein.live import warn_cutoffs

    (tmp_path / "report.md").write_text(
        "x\nwarning cut-offs P(>=35.5) tuned on calibration: {0: 0.575, 1: 0.5250000000000001}\n",
        encoding="utf-8")
    assert warn_cutoffs(tmp_path) == {0: 0.575, 1: 0.5250000000000001}
    (tmp_path / "warn_cutoffs.json").write_text('{"0": 0.3}')
    assert warn_cutoffs(tmp_path) == {0: 0.3}  # the saved file wins


def test_live_scoreboard_counts_hits_and_false_alarms():
    from serein.live import summarize

    s = pd.DataFrame({
        "lead": [1, 1, 1, 1], "issue_date": [date(2026, 11, 3)] * 4,
        "obs": [40.0, 50.0, 10.0, 8.0], "smokecast": [38.0, 20.0, 12.0, 9.0],
        "noaa_best": [20.0, 20.0, 40.0, 9.0], "aqm_bc": [20.0, 20.0, 40.0, 9.0],
        "persistence": [30.0, 30.0, 10.0, 8.0], "warn": [True, False, True, False]})
    r = summarize(s).iloc[0]
    assert (r.usg_days, r.usg_caught, r.false_alarms) == (2, 1, 1)
    assert (r.noaa_caught, r.noaa_false_alarms) == (0, 1)
    assert r.rmse_smokecast < r.rmse_noaa_best and r.skill_vs_noaa > 0


def test_partial_airnow_day_is_read_but_not_frozen(tmp_path, monkeypatch):
    from serein.data import airnow

    monkeypatch.setenv("SEREIN_DATA", str(tmp_path))
    d = date.today()
    row = pd.DataFrame({"site_id": ["A"], "time_utc": [pd.Timestamp(d)], "pm25": [5.0]})
    hourly = tmp_path / "raw" / "airnow" / "hourly"
    hourly.mkdir(parents=True)
    row.to_parquet(hourly / f"{d:%Y%m%d}.partial.parquet")
    got = airnow.load_hourly([d])
    assert len(got) == 1  # live forecasts see today's hours so far
    assert not (hourly / f"{d:%Y%m%d}.parquet").exists()  # a later run re-downloads
