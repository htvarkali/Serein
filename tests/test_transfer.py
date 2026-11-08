from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from serein.eval import transfer


@pytest.mark.parametrize("missing", [False, True])
def test_transfer_coverage_excludes_missing_intervals(monkeypatch, tmp_path, missing):
    tab = pd.DataFrame({
        "point_id": ["site", "site"], "kind": ["epa", "epa"],
        "issue_date": ["2023-06-01", "2023-06-02"], "y_L1": [10.0, 10.0],
    })
    points = pd.DataFrame({"point_id": ["site"], "lat": [40.0], "lon": [-75.0]})
    q = torch.log1p(torch.tensor([[[[5., 8., 10., 12., 15.]]],
                                [[[5., 8., 10., 12., 15.]]]]))
    q[1 if not missing else 0:] = torch.nan
    graph_data = SimpleNamespace(
        X=np.zeros((2, 1, 1)), wind=np.zeros((2, 1, 2)), base=np.zeros((2, 1, 1)),
        row_index=np.array([[0], [1]]),
    )
    calibration = SimpleNamespace(apply=lambda lo, hi, mid: (lo, hi))
    monkeypatch.setattr(transfer, "load_artifacts", lambda path: (
        lambda *args: q, None, calibration, None))
    monkeypatch.setattr(transfer.pd, "read_parquet", lambda path: tab.copy())
    monkeypatch.setattr(transfer, "load_points", lambda name: points)
    monkeypatch.setattr(transfer, "to_graph_data", lambda *args: graph_data)
    monkeypatch.setattr(transfer, "baselines", lambda *args: {})
    monkeypatch.setattr(transfer, "REPO_ROOT", tmp_path)
    study = SimpleNamespace(name="synthetic", raw={"graph": {"k_neighbors": 0, "max_km": 100}})
    monkeypatch.setattr(transfer, "processed_dir", lambda study: tmp_path)

    result = transfer.run_transfer(study, tmp_path / "run")

    if missing:
        assert "coverage90" not in result
    else:
        assert result.loc[0, "n"] == 1
        assert result.loc[0, "coverage90"] == pytest.approx(1.0)
        assert result.loc[0, "width90"] == pytest.approx(10.0)


@pytest.mark.parametrize(("issue_date", "expected_accuracy"), [
    ("2023-06-01", [1.0, 1.0, 1.0]),
    ("2024-05-04", [1.0, 1.0, 0.0]),
    ("2024-05-05", [1.0, 0.0, 0.0]),
])
def test_transfer_aqi_scale_uses_each_leads_valid_date(
    monkeypatch, tmp_path, issue_date, expected_accuracy,
):
    # 8 and 10 are both Good before May 6, 2024; afterward 10 is Moderate.
    tab = pd.DataFrame({
        "point_id": ["site"], "kind": ["epa"], "issue_date": [issue_date],
        "y_L0": [8.0], "y_L1": [8.0], "y_L2": [8.0],
    })
    points = pd.DataFrame({"point_id": ["site"], "lat": [40.0], "lon": [-75.0]})
    q = torch.log1p(torch.tensor([5., 8., 10., 12., 15.])).repeat(1, 1, 3, 1)
    graph_data = SimpleNamespace(
        X=np.zeros((1, 1, 1)), wind=np.zeros((1, 1, 2)), base=np.zeros((1, 1, 3)),
        row_index=np.array([[0]]),
    )
    calibration = SimpleNamespace(apply=lambda lo, hi, mid: (lo, hi))
    monkeypatch.setattr(transfer, "load_artifacts", lambda path: (
        lambda *args: q, None, calibration, None))
    monkeypatch.setattr(transfer.pd, "read_parquet", lambda path: tab.copy())
    monkeypatch.setattr(transfer, "load_points", lambda name: points)
    monkeypatch.setattr(transfer, "to_graph_data", lambda *args: graph_data)
    monkeypatch.setattr(transfer, "baselines", lambda *args: {"persistence": np.full((1, 3), 10.)})
    monkeypatch.setattr(transfer, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(transfer, "processed_dir", lambda study: tmp_path)
    study = SimpleNamespace(name="synthetic", raw={"graph": {"k_neighbors": 0, "max_km": 100}})

    result = transfer.run_transfer(study, tmp_path / "run")

    for model in ("smokecast", "persistence"):
        scores = result[result["model"] == model].sort_values("lead")
        assert scores["cat_acc"].tolist() == expected_accuracy
        assert scores["rmse"].tolist() == pytest.approx([2., 2., 2.])
