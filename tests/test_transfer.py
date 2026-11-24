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


def test_transfer_head_to_head_uses_identical_rows(monkeypatch, tmp_path):
    # Seven days at one monitor, observed 10 every day. SmokeCast misses day 6 badly and
    # has no forecast on day 7; persistence has no forecast on day 6 and misses day 7.
    # Protocol section 5 compares competitors on identical rows: days 1-5 only.
    days = pd.date_range("2023-06-01", periods=7).strftime("%Y-%m-%d").tolist()
    tab = pd.DataFrame({"point_id": ["site"] * 7, "kind": ["epa"] * 7,
                        "issue_date": days, "y_L1": [10.0] * 7})
    points = pd.DataFrame({"point_id": ["site"], "lat": [40.0], "lon": [-75.0]})
    medians = [12.0] * 5 + [40.0, np.nan]
    q = torch.log1p(torch.tensor([[[[m - 2, m - 1, m, m + 1, m + 2]]] for m in medians]))
    graph_data = SimpleNamespace(
        X=np.zeros((7, 1, 1)), wind=np.zeros((7, 1, 2)), base=np.zeros((7, 1, 1)),
        row_index=np.arange(7).reshape(7, 1),
    )
    calibration = SimpleNamespace(apply=lambda lo, hi, mid: (lo, hi))
    persistence = np.array([[14.0]] * 5 + [[np.nan], [50.0]])
    monkeypatch.setattr(transfer, "load_artifacts", lambda path: (
        lambda *args: q, None, calibration, None))
    monkeypatch.setattr(transfer.pd, "read_parquet", lambda path: tab.copy())
    monkeypatch.setattr(transfer, "load_points", lambda name: points)
    monkeypatch.setattr(transfer, "to_graph_data", lambda *args: graph_data)
    monkeypatch.setattr(transfer, "baselines", lambda *args: {
        "persistence": persistence, "aqm_bc": np.full((7, 1), np.nan)})
    monkeypatch.setattr(transfer, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(transfer, "processed_dir", lambda study: tmp_path)
    study = SimpleNamespace(name="synthetic", raw={"graph": {"k_neighbors": 0, "max_km": 100}})

    result = transfer.run_transfer(study, tmp_path / "run")

    # metrics.csv keeps each model's own rows (6 each here, not the same 6).
    own = result.set_index("model")
    assert own.loc["smokecast", "n"] == 6 and own.loc["persistence", "n"] == 6
    h2h = pd.read_csv(tmp_path / "outputs" / "transfer" / "synthetic_run" / "head_to_head.csv")
    assert h2h[["lead", "vs", "n"]].values.tolist() == [[1, "persistence", 5]]
    row = h2h.iloc[0]
    assert row["rmse_smokecast"] == pytest.approx(2.0, rel=1e-5)
    assert row["rmse_baseline"] == pytest.approx(4.0, rel=1e-5)
    assert row["skill"] == pytest.approx(0.5, rel=1e-5)
    assert row["diff"] == pytest.approx(row["rmse_smokecast"] - row["rmse_baseline"])
    assert row["ci_lo"] == pytest.approx(-2.0, rel=1e-5)
    assert row["ci_hi"] == pytest.approx(-2.0, rel=1e-5)
