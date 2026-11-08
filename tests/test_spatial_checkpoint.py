import hashlib
import json
from pathlib import Path

import numpy as np
import pytest
import torch

from serein.eval.spatial_checkpoint import MemberCache
from serein.eval.spatial_experiment import main


def cache(tmp_path):
    return MemberCache(tmp_path, {"inputs": {"train": "abc"}})


def test_cache_round_trip_preserves_weights_arrays_and_history(tmp_path):
    store = cache(tmp_path)
    state = {"weight": torch.tensor([[1., 2.]])}
    cal = np.arange(20, dtype=np.float32).reshape(2, 2, 5)
    prediction = cal + 1
    history = {"best_val": .1, "history": [[0, .2, .1]]}
    store.save("smokecast", 4, state, cal, prediction, history)
    saved = store.load("smokecast", 4, calibration_shape=cal.shape, prediction_shape=prediction.shape)
    assert saved is not None
    weights, got_cal, got_pred, got_history = saved
    torch.testing.assert_close(weights["weight"], state["weight"], rtol=0, atol=0)
    np.testing.assert_array_equal(got_cal, cal)
    np.testing.assert_array_equal(got_pred, prediction)
    assert got_history == history and store.reused == 1


def test_interrupted_attempt_is_kept_and_does_not_hide_a_new_completed_attempt(tmp_path):
    store = cache(tmp_path)
    partial = tmp_path / "members/smokecast_0/interrupted"
    partial.mkdir(parents=True)
    (partial / "state.pt").write_bytes(b"partial")
    (partial / "member.json.tmp").write_bytes(b"partial marker")
    assert store.load("smokecast", 0, calibration_shape=(1, 1, 5), prediction_shape=(1, 1, 5)) is None
    values = np.zeros((1, 1, 5), dtype=np.float32)
    store.save("smokecast", 0, {"weight": torch.ones(1)}, values, values, {"best_val": 0.})
    assert (partial / "state.pt").read_bytes() == b"partial"
    assert (partial / "member.json.tmp").read_bytes() == b"partial marker"
    assert store.load("smokecast", 0, calibration_shape=values.shape, prediction_shape=values.shape) is not None


@pytest.mark.parametrize("file", ["state.pt", "predictions.npz"])
def test_corrupt_completed_checkpoint_is_rejected_without_overwriting(tmp_path, file):
    store = cache(tmp_path)
    values = np.zeros((1, 1, 5), dtype=np.float32)
    store.save("smokecast", 0, {"weight": torch.ones(1)}, values, values, {"best_val": 0.})
    path = next((tmp_path / "members").glob(f"*/*/{file}"))
    path.write_bytes(b"corrupt")
    with pytest.raises(ValueError, match="checksum"):
        store.load("smokecast", 0, calibration_shape=values.shape, prediction_shape=values.shape)
    assert path.read_bytes() == b"corrupt"


def test_incompatible_checkpoint_shapes_are_rejected(tmp_path):
    store = cache(tmp_path)
    values = np.zeros((1, 1, 5), dtype=np.float32)
    store.save("smokecast", 0, {"weight": torch.ones(1)}, values, values, {"best_val": 0.})
    with pytest.raises(ValueError, match="shape"):
        store.load("smokecast", 0, calibration_shape=(2, 1, 5), prediction_shape=values.shape)


@pytest.mark.parametrize("condition", ["plan_changed", "complete"])
def test_resume_requires_identical_incomplete_plan(tmp_path, condition):
    cache(tmp_path)
    plan = {"inputs": {"train": "abc"}}
    if condition == "plan_changed":
        plan["inputs"]["train"] = "different"
    else:
        (tmp_path / "manifest.json").write_text("{}")
    before = (tmp_path / "run_plan.json").read_bytes()
    with pytest.raises(ValueError):
        MemberCache(tmp_path, plan, resume=True)
    assert (tmp_path / "run_plan.json").read_bytes() == before


def test_real_interrupted_run_resumes_only_missing_members_and_matches_fresh_fit(tmp_path, monkeypatch):
    import runpy

    from serein.models.train import Trainer

    fixture = runpy.run_path(str(Path(__file__).with_name("test_spatial_experiment.py")))
    interrupted = tmp_path / "interrupted"
    interrupted.mkdir()
    argv, _ = fixture["write_inputs"](interrupted)
    original_fit = Trainer.fit
    calls = []

    def interrupt(trainer, *args, **kwargs):
        calls.append((trainer.cfg.use_graph, trainer.cfg.seed))
        if len(calls) == 2:
            raise RuntimeError("controlled interruption after one completed member")
        return original_fit(trainer, *args, **kwargs)

    monkeypatch.setattr(Trainer, "fit", interrupt)
    with pytest.raises(RuntimeError, match="controlled interruption"):
        main(argv)
    output = interrupted / "experiment"
    assert not (output / "manifest.json").exists()
    markers = list((output / "members").glob("*/*/member.json"))
    assert len(markers) == 1
    original_marker = hashlib.sha256(markers[0].read_bytes()).hexdigest()
    calls.clear()

    def record(trainer, *args, **kwargs):
        calls.append((trainer.cfg.use_graph, trainer.cfg.seed))
        return original_fit(trainer, *args, **kwargs)

    monkeypatch.setattr(Trainer, "fit", record)
    assert main([*argv, "--resume"]) == 0
    assert calls == [(True, 1), (False, 0), (False, 1)]
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["resumed"] and manifest["reused_members"] == 1
    assert hashlib.sha256(markers[0].read_bytes()).hexdigest() == original_marker
    fresh = tmp_path / "fresh"
    fresh.mkdir()
    fresh_argv, _ = fixture["write_inputs"](fresh)
    assert main(fresh_argv) == 0
    import pandas as pd

    pd.testing.assert_frame_equal(pd.read_parquet(output / "predictions.parquet"),
                                  pd.read_parquet(fresh / "experiment/predictions.parquet"))


def test_cli_resume_refuses_changed_inputs_before_fitting(tmp_path, monkeypatch):
    import runpy

    from serein.models.train import Trainer

    fixture = runpy.run_path(str(Path(__file__).with_name("test_spatial_experiment.py")))
    argv, paths = fixture["write_inputs"](tmp_path)
    def interrupt(*args, **kwargs):
        raise RuntimeError("controlled interruption")
    monkeypatch.setattr(Trainer, "fit", interrupt)
    with pytest.raises(RuntimeError, match="controlled interruption"):
        main(argv)
    path = tmp_path / "experiment/run_plan.json"
    before = path.read_bytes()
    paths["partition"].write_text(paths["partition"].read_text() + "\n")
    with pytest.raises(SystemExit) as exc:
        main([*argv, "--resume"])
    assert exc.value.code == 2
    assert path.read_bytes() == before
