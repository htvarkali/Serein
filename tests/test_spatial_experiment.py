import hashlib
import json
from dataclasses import replace

import numpy as np
import pandas as pd
import pytest
import torch
import yaml

from serein.eval.spatial_experiment import fit_experiment, main, prepare_experiment
from serein.features.prepare import is_sensor_feature
from serein.models.conformal import calibrate_quantiles
from serein.models.gnn import QUANTILES
from serein.models.infer import load_artifacts
from serein.models.train import TrainConfig


def points():
    return pd.DataFrame({"point_id": ["A", "B", "C", "D"], "kind": "epa",
                         "lat": [38., 38.1, 38.2, 38.3], "lon": [-121., -121.1, -121.2, -121.3]})


def partition():
    return {"reference_ids": ["B", "A"], "evaluation_ids": ["D", "C"], "provenance": "synthetic split"}


def table(year, n_days=21):
    rows = []
    for day in pd.date_range(f"{year}-07-01", periods=n_days):
        for i, row in points().iterrows():
            value = 10. + i + day.day % 3
            rows.append({"point_id": row.point_id, "issue_date": day, "kind": "epa",
                         "lat": row.lat, "lon": row.lon, "hms_prev": float(day.day % 4),
                         "obs_last24": value, "obs_prevday": value + 1, "obs_n24": 24.,
                         "hrrr_u10_L0": 1., "hrrr_v10_L0": 0.,
                         "hrrr_smoke_mean_L0": 2., "hrrr_smoke_mean_L1": 3.,
                         "aqm_mean_L0": value + 5, "aqm_mean_L1": value + 6,
                         "y_L0": value, "y_L1": value + 2})
    return pd.DataFrame(rows)


def prepared(train=None, calibrate=None, **kwargs):
    return prepare_experiment(table(2021) if train is None else train,
                              table(2023) if calibrate is None else calibrate,
                              points(), partition(), k=2, **kwargs)


def cfg():
    return TrainConfig(epochs=2, hidden=8, layers=1, heads=4, dropout=0., smoke_weight=1., seed=5)


def test_preprocessing_graphs_and_all_target_arrays_exclude_evaluation_data():
    experiment = prepared()
    assert set(experiment.prep.site_clim) == set(experiment.prep.site_bg) == {"A", "B"}
    for gd in (experiment.train, experiment.validation, experiment.calibration):
        assert gd.nodes == ["B", "A"]
        assert gd.X.shape[1] == gd.Y.shape[1] == 2
    assert np.isfinite(experiment.train.Y).all()
    assert np.isnan(experiment.prediction.Y).all()
    graph = experiment.prediction_graph
    assert (graph.src < 2).all()
    reference_edges = graph.dst < 2
    for name in ("src", "dst", "dist_km", "bearing", "edge_attr"):
        np.testing.assert_array_equal(getattr(graph, name)[reference_edges],
                                      getattr(experiment.reference_graph, name))
    for i, name in enumerate(experiment.prediction.feat_names):
        if is_sensor_feature(name):
            assert np.all(experiment.prediction.X[:, 2:, i] == float(name.endswith("__missing")))
    assert experiment.prediction_rows.loc[experiment.prediction_rows.point_id.isin(["C", "D"]), "obs_prevday"].isna().all()
    assert np.isfinite(experiment.observations.y_L1).all()


def test_evaluation_training_values_and_prediction_sensor_values_cannot_change_any_inputs():
    train, calibrate = table(2021), table(2023)
    expected = prepared(train, calibrate)
    original_train, original_cal = train.copy(deep=True), calibrate.copy(deep=True)
    for frame in (train, calibrate):
        hidden = frame.point_id.isin(["C", "D"])
        for column in frame:
            if column.startswith(("obs_", "y_L")):
                frame.loc[hidden, column] = 100000.
    actual = prepared(train, calibrate)
    assert expected.prep == actual.prep
    for name in ("train", "validation", "calibration", "prediction"):
        a, b = getattr(expected, name), getattr(actual, name)
        for field in ("X", "Y", "base", "wind", "row_index"):
            np.testing.assert_array_equal(getattr(a, field), getattr(b, field))
    # Preparing the original inputs does not mutate them.
    experiment = prepared(original_train, original_cal)
    pd.testing.assert_frame_equal(original_train, table(2021))
    pd.testing.assert_frame_equal(original_cal, table(2023))
    assert experiment.observations.y_L1.max() < actual.observations.y_L1.min()


def test_even_reference_weeks_and_odd_evaluation_weeks_are_explicit():
    experiment = prepared()
    assert (pd.DatetimeIndex(experiment.validation.days).isocalendar().week % 2 == 0).all()
    assert (pd.DatetimeIndex(experiment.prediction.days).isocalendar().week % 2 == 1).all()
    assert set(experiment.validation.days).isdisjoint(experiment.prediction.days)
    assert experiment.validation is experiment.calibration


def test_unused_evaluation_values_cannot_change_fit_feature_dtypes():
    expected = prepared()
    train, calibrate = table(2021), table(2023)
    for frame in (train, calibrate):
        for column in [name for name in frame if name.startswith("obs_")]:
            frame[column] = frame[column].astype(object)
            frame.loc[frame.point_id.isin(["C", "D"]), column] = "unavailable"
    actual = prepared(train, calibrate)
    assert expected.prep == actual.prep
    for name in ("train", "validation", "prediction"):
        for field in ("X", "Y", "base", "wind"):
            np.testing.assert_array_equal(getattr(getattr(expected, name), field),
                                          getattr(getattr(actual, name), field))


def test_noaa_fallback_uses_reference_background_and_no_evaluation_persistence():
    calibrate = table(2023)
    hidden = calibrate.point_id.isin(["C", "D"])
    calibrate.loc[hidden, ["aqm_mean_L0", "aqm_mean_L1"]] = np.nan
    calibrate.loc[hidden, ["obs_prevday", "obs_last24"]] = 99999.
    experiment = prepared(calibrate=calibrate)
    predictions, _ = fit_experiment(experiment, cfg(), seeds=1, log=lambda message: None)
    assert predictions.noaa_best_L0.eq(2. + np.expm1(experiment.prep.global_clim)).all()
    assert predictions.noaa_best_L1.eq(3. + np.expm1(experiment.prep.global_clim)).all()


def test_real_fits_are_identical_after_changing_evaluation_observations_and_histories():
    before = prepared()
    train, calibrate = table(2021), table(2023)
    for frame in (train, calibrate):
        for column in frame:
            if column.startswith(("obs_", "y_L")):
                frame.loc[frame.point_id.isin(["C", "D"]), column] += 10000.
    after = prepared(train, calibrate)
    pred_before, fitted_before = fit_experiment(before, cfg(), seeds=2, log=lambda message: None)
    pred_after, fitted_after = fit_experiment(after, cfg(), seeds=2, log=lambda message: None)
    columns = [column for column in pred_before if not column.startswith("y_L")]
    pd.testing.assert_frame_equal(pred_before[columns], pred_after[columns])
    for model in fitted_before:
        a, b = fitted_before[model], fitted_after[model]
        assert a["history"] == b["history"]
        assert a["cqr"] == b["cqr"]
        for original, changed in zip(a["states"], b["states"], strict=True):
            for name in original:
                torch.testing.assert_close(original[name], changed[name], atol=0, rtol=0)


@pytest.mark.parametrize("problem", ["no_reference_training", "no_reference_calibration", "no_eval_rows",
    "no_even_weeks", "missing_obs", "lead_mismatch", "no_targets", "duplicate", "invalid_date"])
def test_invalid_experiments_fail_before_training(problem):
    train, calibrate = table(2021), table(2023)
    if problem == "no_reference_training":
        train = train.loc[train.point_id.ne("A")]
    elif problem == "no_reference_calibration":
        calibrate = calibrate.loc[calibrate.point_id.ne("A")]
    elif problem == "no_eval_rows":
        calibrate = calibrate.loc[calibrate.point_id.isin(["A", "B"])]
    elif problem == "no_even_weeks":
        calibrate = calibrate.loc[calibrate.issue_date.dt.isocalendar().week % 2 == 1]
    elif problem == "missing_obs":
        train = train.drop(columns="obs_last24")
    elif problem == "lead_mismatch":
        calibrate = calibrate.drop(columns="y_L1")
    elif problem == "no_targets":
        train.loc[train.point_id.isin(["A", "B"]), "y_L1"] = np.nan
    elif problem == "duplicate":
        train = pd.concat([train, train.iloc[:1]])
    else:
        calibrate.loc[0, "issue_date"] = pd.NaT
    with pytest.raises((ValueError, TypeError)):
        prepared(train, calibrate)


def write_inputs(tmp_path):
    paths = {}
    for name, frame in (("train", table(2021)), ("calibrate", table(2023)), ("points", points())):
        path = tmp_path / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        paths[name] = path
    paths["partition"] = tmp_path / "partition.json"
    paths["partition"].write_text(json.dumps(partition()), encoding="utf-8")
    paths["config"] = tmp_path / "config.yaml"
    paths["config"].write_text(yaml.safe_dump({"split": {"train": [2021, 2022], "calibrate": [2023], "test": [2024, 2025]},
                                             "graph": {"k_neighbors": 2, "max_km": 300}}), encoding="utf-8")
    argv = [item for name, path in paths.items() for item in (f"--{name}", str(path))]
    argv += ["--output", str(tmp_path / "experiment"), "--epochs", "2", "--seeds", "2", "--hidden", "8", "--layers", "1"]
    return argv, paths


def test_cli_real_ensemble_reload_forecast_parity_and_source_hashes(tmp_path):
    argv, paths = write_inputs(tmp_path)
    before = {name: path.read_bytes() for name, path in paths.items()}
    assert main(argv) == 0
    output = tmp_path / "experiment"
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["status"] == "complete" and manifest["development_only"]
    assert manifest["reference_ids"] == ["B", "A"]
    assert manifest["evaluation_ids"] == ["D", "C"]
    for name, path in paths.items():
        assert path.read_bytes() == before[name]
        assert manifest["inputs"][name]["sha256"] == hashlib.sha256(before[name]).hexdigest()
    saved = pd.read_parquet(output / "predictions.parquet")
    assert set(saved.point_id) == {"C", "D"}
    prepared_data = prepared()
    for name in ("smokecast", "smokecast_nograph"):
        model, prep, cqr, metadata = load_artifacts(output / name)
        assert prep == prepared_data.prep
        assert metadata["node_ids"] == ["B", "A"] and metadata["seeds"] == [0, 1]
        gd, graph = prepared_data.prediction, prepared_data.prediction_graph
        with torch.no_grad():
            predicted = model(torch.as_tensor(gd.X), torch.as_tensor(gd.wind), torch.as_tensor(gd.base),
                              torch.as_tensor(graph.src), torch.as_tensor(graph.dst),
                              torch.as_tensor(graph.bearing, dtype=torch.float32), torch.as_tensor(graph.edge_attr)).numpy()
        predicted = calibrate_quantiles(predicted.reshape(-1, 2, 5), cqr, QUANTILES).reshape(predicted.shape)
        for row in saved.itertuples():
            day = list(gd.days).index(row.issue_date)
            node = gd.nodes.index(row.point_id)
            for i, lead in enumerate((0, 1)):
                for suffix, qi in (("", 2), ("_lo", 0), ("_hi", -1)):
                    assert getattr(row, f"{name}{suffix}_L{lead}") == pytest.approx(np.expm1(predicted[day, node, i, qi]), rel=2e-5, abs=1e-5)
    assert not (output / "FINAL_RUN_LOCK.json").exists()
    assert (output / "training.log").stat().st_size > 0
    assert len(pd.read_csv(output / "summary.csv")) == 24
    assert len(pd.read_csv(output / "noaa_summary.csv")) == 24
    assert manifest["report_models"] == {"primary": ["smokecast", "smokecast_nograph"],
                                          "noaa_": ["smokecast", "noaa_best"]}


def test_missing_noaa_does_not_remove_learned_model_scores(tmp_path):
    argv, paths = write_inputs(tmp_path)
    calibrate = pd.read_parquet(paths["calibrate"])
    missing = calibrate.point_id.isin(["C", "D"])
    calibrate.loc[missing, ["aqm_mean_L0", "aqm_mean_L1", "hrrr_smoke_mean_L0", "hrrr_smoke_mean_L1"]] = np.nan
    calibrate.to_parquet(paths["calibrate"], index=False)
    assert main(argv) == 0
    output = tmp_path / "experiment"
    learned = pd.read_csv(output / "summary.csv")
    noaa = pd.read_csv(output / "noaa_summary.csv")
    assert learned.loc[learned.distance_band.eq(-1), "n_scored"].gt(0).all()
    assert noaa.n_scored.eq(0).all() and noaa.rmse.isna().all()


@pytest.mark.parametrize("problem", ["train_test_year", "calibrate_test_year", "target_cross_year",
    "overlapping_years", "existing_output", "bad_hidden", "zero_epochs", "negative_seed", "locked_inputs"])
def test_cli_invalid_inputs_fail_without_fitting(tmp_path, monkeypatch, problem):
    argv, paths = write_inputs(tmp_path)
    if problem in {"train_test_year", "calibrate_test_year", "target_cross_year"}:
        name = "train" if problem == "train_test_year" else "calibrate"
        frame = table(2024)
        if problem == "target_cross_year":
            frame["issue_date"] = pd.Timestamp("2023-12-31") + pd.to_timedelta(np.arange(len(frame)) // 4, unit="s")
            frame = frame.iloc[:4]
        frame.to_parquet(paths[name], index=False)
    elif problem == "overlapping_years":
        config = yaml.safe_load(paths["config"].read_text())
        config["split"]["train"] = [2023]
        paths["config"].write_text(yaml.safe_dump(config))
    elif problem == "existing_output":
        (tmp_path / "experiment").mkdir()
    elif problem == "locked_inputs":
        (tmp_path / "FINAL_RUN_LOCK.json").write_text("{}")
    else:
        option, value = {"bad_hidden": ("--hidden", "7"), "zero_epochs": ("--epochs", "0"),
                         "negative_seed": ("--seed", "-1")}[problem]
        argv += [option, value]
    def unexpected_fit(*args, **kwargs):
        pytest.fail("invalid inputs reached model fitting")
    monkeypatch.setattr("serein.eval.spatial_experiment.fit_experiment", unexpected_fit)
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == 2
    if problem != "existing_output":
        assert not (tmp_path / "experiment").exists()


def test_history_models_are_explicitly_unsupported():
    base = cfg()
    if not hasattr(base, "history"):
        return
    with pytest.raises(ValueError, match="single-day"):
        fit_experiment(prepared(), replace(base, history=2), seeds=1)
