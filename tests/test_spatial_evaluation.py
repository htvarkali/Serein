import hashlib
import json
import math

import numpy as np
import pandas as pd
import pytest
import yaml

from serein.eval.spatial import analyze_spatial, main, spatial_sites


def registry():
    return pd.DataFrame({"point_id": ["R", "A", "B", "C"], "kind": ["epa"] * 4,
                         "lat": [0., 0., 0., 0.], "lon": [0., .1, 1., 3.]})


def partition():
    return {"reference_ids": ["R"], "evaluation_ids": ["A", "B", "C"],
            "provenance": "Synthetic declared split, not a training-exclusion check."}


def forecasts(n_days=42):
    return pd.DataFrame({"issue_date": np.repeat(pd.date_range("2023-06-01", periods=n_days), 3),
                         "point_id": ["R", "A", "B"] * n_days,
                         "y_L1": [900., 10., 20.] * n_days,
                         "smokecast_L1": [0., 13., 16.] * n_days,
                         "noaa_best_L1": [0., 15., 32.] * n_days})


def analyze(frame=None, **kwargs):
    return analyze_spatial(forecasts() if frame is None else frame, registry(), partition(),
                           n_boot=30, **kwargs)


def test_nearest_reference_and_distances_on_equator():
    sites, bands = spatial_sites(registry(), partition())
    assert sites.point_id.tolist() == ["A", "B", "C"]
    np.testing.assert_allclose(sites.nearest_reference_km, np.deg2rad([.1, 1, 3]) * 6371.)
    assert sites.nearest_reference_id.tolist() == ["R"] * 3
    assert sites.distance_band.tolist() == [0, 3, 4]
    assert bands.distance_lo_km.tolist() == [0, 25, 50, 100, 200]
    assert np.isnan(bands.distance_hi_km.iloc[-1])


def test_spherical_nearest_matches_independent_dense_oracle():
    rng = np.random.default_rng(3)
    xy = np.column_stack([rng.uniform(-90, 90, 120), rng.uniform(-180, 180, 120)])
    points = pd.DataFrame({"point_id": [f"p{i}" for i in range(len(xy))],
                           "lat": xy[:, 0], "lon": xy[:, 1]})
    split = {"reference_ids": points.point_id[:70].tolist(),
             "evaluation_ids": points.point_id[70:].tolist(), "provenance": "synthetic"}
    sites, _ = spatial_sites(points, split)
    expected = []
    for lat, lon in xy[70:]:
        distances = []
        for rlat, rlon in xy[:70]:
            phi, rphi = math.radians(lat), math.radians(rlat)
            cosine = (math.sin(phi) * math.sin(rphi)
                      + math.cos(phi) * math.cos(rphi) * math.cos(math.radians(lon - rlon)))
            distances.append(6371. * math.acos(max(-1., min(1., cosine))))
        expected.append(distances)
    expected = np.asarray(expected)
    np.testing.assert_allclose(sites.nearest_reference_km, expected.min(axis=1), atol=1e-8)
    assert sites.nearest_reference_id.tolist() == points.point_id[np.argmin(expected, axis=1)].tolist()


def test_dateline_poles_colocation_and_antipodes():
    points = pd.DataFrame({"point_id": ["r", "date", "same", "anti"],
                           "lat": [0., 0., 0., 0.], "lon": [179., -179., 179., -1.]})
    split = {"reference_ids": ["r"], "evaluation_ids": ["date", "same", "anti"],
             "provenance": "synthetic"}
    sites, _ = spatial_sites(points, split)
    np.testing.assert_allclose(sites.nearest_reference_km, [6371. * math.radians(2), 0, 6371. * math.pi])
    points.loc[:, "lat"] = [90., 90., -90., 0.]
    sites, _ = spatial_sites(points, split)
    np.testing.assert_allclose(sites.nearest_reference_km,
                               [0., 6371. * math.pi, 6371. * math.pi / 2], atol=1e-9)


def test_distance_edges_are_left_closed_and_final_band_is_open_ended():
    sites, _ = spatial_sites(registry(), partition(), edges=[0])
    boundary = sites.nearest_reference_km.iloc[0]
    sites, _ = spatial_sites(registry(), partition(), edges=[0, boundary])
    assert sites.distance_band.tolist() == [1, 1, 1]


def test_point_scores_common_population_and_daily_reconstruction():
    summary, daily, sites = analyze()
    pooled = summary.loc[summary.distance_band.eq(-1)].set_index("model")
    sc = pooled.loc["smokecast"]
    assert sc.rmse == pytest.approx(np.sqrt((3 ** 2 + 4 ** 2) / 2))
    assert sc.mae == pytest.approx(3.5)
    assert sc.bias == pytest.approx(-.5)
    assert sc.n_input == sc.n_scored == 84
    assert sc.n_sites == 3 and sc.n_sites_exported == sc.n_sites_scored == 2
    assert sc.reference_rmse == sc.rmse
    assert sc.rmse_difference == sc.rmse_difference_ci_lo == sc.rmse_difference_ci_hi == 0
    baseline = pooled.loc["noaa_best"]
    assert baseline.rmse == pytest.approx(np.sqrt((5 ** 2 + 12 ** 2) / 2))
    assert baseline.rmse_difference == pytest.approx(baseline.rmse - sc.rmse)
    assert baseline.rmse_difference_ci_lo == pytest.approx(baseline.rmse_difference)
    for model, group in daily.loc[daily.distance_band.eq(-1)].groupby("model"):
        assert np.sqrt(group.squared_error_sum.sum() / group.n_scored.sum()) == pytest.approx(pooled.loc[model].rmse)
    assert sites.loc[sites.point_id.eq("C"), "n_input"].eq(0).all()
    assert sites.loc[sites.point_id.eq("C"), "status"].eq("no_scored_rows").all()
    assert sites.loc[sites.point_id.eq("C"), "rmse"].isna().all()
    banded = summary.loc[summary.distance_band.ge(0)].groupby("model").n_scored.sum()
    pd.testing.assert_series_equal(banded, pooled.n_scored.sort_index(), check_names=False)


def test_missing_observations_and_models_are_audited_on_common_rows():
    frame = forecasts(3)
    frame.loc[1, "smokecast_L1"] = np.nan
    frame.loc[2, "noaa_best_L1"] = np.nan
    frame.loc[4, "y_L1"] = np.nan
    summary, daily, sites = analyze(frame)
    pooled = summary.loc[summary.distance_band.eq(-1)].set_index("model")
    assert pooled.n_input.eq(6).all() and pooled.n_observed.eq(5).all()
    assert pooled.n_prediction.eq(5).all() and pooled.n_pairwise.eq(4).all()
    assert pooled.n_scored.eq(3).all() and pooled.n_excluded_common.eq(1).all()
    assert daily.loc[daily.distance_band.eq(-1)].groupby("model").size().eq(3).all()
    sc = pooled.loc["smokecast"]
    assert sc.rmse == pytest.approx(np.sqrt((16 + 9 + 16) / 3))
    assert sites.loc[sites.point_id.eq("A"), "n_scored"].eq(1).all()


@pytest.mark.parametrize("empty", ["observations", "forecasts", "evaluation_rows"])
def test_no_scored_population_and_empty_bands_remain_visible(empty):
    frame = forecasts(3)
    if empty == "observations":
        frame["y_L1"] = np.nan
    elif empty == "forecasts":
        frame["noaa_best_L1"] = np.nan
    else:
        frame = frame.loc[frame.point_id.eq("R")]
    summary, daily, sites = analyze(frame)
    assert len(summary) == 12
    assert summary.n_scored.eq(0).all() and summary.rmse.isna().all()
    assert summary.bootstrap_status.eq("insufficient_blocks").all()
    assert sites.n_scored.eq(0).all() and len(sites) == 6
    assert summary.status.eq("no_scored_rows").all()
    assert daily.n_scored.eq(0).all()


def test_leads_use_separate_common_populations_and_site_counts():
    frame = forecasts()
    frame["y_L2"] = 50.
    frame["smokecast_L2"] = 51.
    frame["noaa_best_L2"] = 49.
    frame.loc[frame.point_id.eq("A"), "noaa_best_L2"] = np.nan
    summary, _, sites = analyze(frame)
    pooled = summary.loc[summary.distance_band.eq(-1)]
    assert pooled.loc[pooled.lead.eq(1), "n_sites_scored"].eq(2).all()
    assert pooled.loc[pooled.lead.eq(2), "n_sites_scored"].eq(1).all()
    assert pooled.loc[pooled.lead.eq(2), "rmse"].eq(1).all()
    assert sites.loc[sites.point_id.eq("A") & sites.lead.eq(2), "n_scored"].eq(0).all()


def test_reordering_and_indexes_do_not_change_scores():
    frame = forecasts()
    frame.loc[1, "noaa_best_L1"] = np.nan
    expected = analyze(frame)
    actual = analyze(frame.sample(frac=1, random_state=8).set_axis([17] * len(frame)))
    for left, right in zip(expected, actual, strict=True):
        pd.testing.assert_frame_equal(left, right)


def test_bootstrap_uses_calendar_blocks_not_observed_row_order():
    frame = forecasts(8)
    frame["issue_date"] = np.repeat(pd.to_datetime(["2023-01-01", "2023-01-02", "2023-02-01", "2023-03-01",
                                                  "2023-04-01", "2023-05-01", "2023-06-01", "2023-07-01"]), 3)
    summary, _, _ = analyze(frame)
    assert summary.loc[summary.distance_band.eq(-1), "n_blocks"].eq(7).all()
    assert summary.loc[summary.distance_band.eq(-1), "bootstrap_status"].eq("ok").all()
    frame["issue_date"] = np.repeat(pd.date_range("2023-06-01", periods=8), 3)
    summary, _, _ = analyze(frame)
    assert summary.loc[summary.distance_band.eq(-1), "bootstrap_status"].eq("insufficient_blocks").all()


def test_bootstrap_matches_scalar_resampling_with_unequal_counts():
    frame = forecasts(42)
    frame["noaa_best_L1"] += np.repeat(np.arange(42), 3)
    frame.loc[frame.index[2::6], "smokecast_L1"] = np.nan
    summary, daily, _ = analyze(frame, block_days=7, seed=4)
    selected = daily.loc[daily.distance_band.eq(-1) & daily.model.eq("noaa_best")]
    blocks = (selected.issue_date - pd.Timestamp("1970-01-01")).dt.days // 7
    totals = selected.groupby(blocks)[["n_scored", "squared_error_sum", "reference_squared_error_sum"]].sum()
    rng = np.random.default_rng(4)
    values = []
    for _ in range(30):
        sampled = totals.iloc[rng.integers(0, len(totals), len(totals))].sum()
        values.append(math.sqrt(sampled.squared_error_sum / sampled.n_scored)
                      - math.sqrt(sampled.reference_squared_error_sum / sampled.n_scored))
    row = summary.loc[summary.distance_band.eq(-1) & summary.model.eq("noaa_best")].iloc[0]
    np.testing.assert_allclose([row.rmse_difference_ci_lo, row.rmse_difference_ci_hi],
                               np.percentile(values, [2.5, 97.5]))


@pytest.mark.parametrize("field,value", [("reference_ids", []), ("evaluation_ids", []),
    ("reference_ids", ["R", "R"]), ("reference_ids", [" "]), ("reference_ids", [1]),
    ("reference_ids", "R"), ("reference_ids", [["R"]]), ("reference_ids", ["unknown"]),
    ("evaluation_ids", ["R"]), ("provenance", ""), ("provenance", None)])
def test_invalid_partitions_fail(field, value):
    split = partition()
    split[field] = value
    with pytest.raises((ValueError, TypeError)):
        spatial_sites(registry(), split)


@pytest.mark.parametrize("edges", [[], [1], [0, 0], [0, -1], [0, np.inf], [0, np.nan], [False, 25]])
def test_invalid_distance_edges_fail(edges):
    with pytest.raises(ValueError, match="distance edges"):
        spatial_sites(registry(), partition(), edges=edges)


@pytest.mark.parametrize("column,value", [("lat", 91), ("lat", np.nan), ("lon", 181),
                                          ("lon", np.inf), ("kind", "grid")])
def test_invalid_selected_registry_rows_fail(column, value):
    points = registry()
    points.loc[0, column] = value
    with pytest.raises(ValueError):
        spatial_sites(points, partition())


def test_duplicate_or_missing_registry_ids_fail_and_unused_rows_do_not_supply_support():
    points = registry()
    with pytest.raises(ValueError):
        spatial_sites(pd.concat([points, points.iloc[:1]]), partition())
    with pytest.raises(ValueError):
        spatial_sites(points.drop(columns="lon"), partition())
    points.loc[len(points)] = ["unused", "grid", np.nan, np.nan]
    sites, _ = spatial_sites(points, partition())
    assert sites.nearest_reference_id.eq("R").all()


@pytest.mark.parametrize("column", ["y_L1", "smokecast_L1", "noaa_best_L1"])
@pytest.mark.parametrize("value", [np.inf, -np.inf, "bad"])
def test_invalid_values_fail_even_on_excluded_reference_rows(column, value):
    frame = forecasts(1)
    frame[column] = frame[column].astype(object)
    frame.loc[0, column] = value
    with pytest.raises((TypeError, ValueError)):
        analyze(frame)


@pytest.mark.parametrize("change", ["unknown_site", "duplicate", "missing_date", "time", "timezone",
                                    "numeric_date", "no_leads", "missing_model", "duplicate_column", "empty"])
def test_invalid_prediction_tables_fail(change):
    frame = forecasts(2)
    if change == "unknown_site":
        frame.loc[0, "point_id"] = "unclassified"
    elif change == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]])
    elif change == "missing_date":
        frame.loc[0, "issue_date"] = pd.NaT
    elif change == "time":
        frame["issue_date"] += pd.Timedelta(hours=1)
    elif change == "timezone":
        frame["issue_date"] = frame.issue_date.dt.tz_localize("UTC")
    elif change == "numeric_date":
        frame["issue_date"] = 20230601
    elif change == "no_leads":
        frame = frame.drop(columns="y_L1")
    elif change == "missing_model":
        frame = frame.drop(columns="noaa_best_L1")
    elif change == "duplicate_column":
        frame = pd.concat([frame, frame[["y_L1"]]], axis=1)
    else:
        frame = frame.iloc[:0]
    with pytest.raises((TypeError, ValueError)):
        analyze(frame)


@pytest.mark.parametrize("options", [{"models": []}, {"models": ["x", "x"]}, {"models": ["../x"]},
    {"leads": []}, {"leads": [True]}, {"leads": [-1]}, {"leads": [1, 1]},
    {"block_days": 0}, {"block_days": 1.5}, {"seed": -1}, {"seed": True}])
def test_invalid_analysis_options_fail(options):
    with pytest.raises((ValueError, TypeError)):
        analyze(**options)


def test_error_overflow_fails():
    frame = forecasts(1)
    frame.loc[1, "smokecast_L1"] = 1e308
    with pytest.raises(ValueError, match="overflow"):
        analyze(frame)


def inputs(tmp_path):
    run = tmp_path / "run"
    run.mkdir()
    forecasts().to_parquet(run / "predictions.parquet", index=False)
    registry().to_parquet(tmp_path / "points.parquet", index=False)
    (tmp_path / "partition.json").write_text(json.dumps(partition()), encoding="utf-8")
    (tmp_path / "config.yaml").write_text(yaml.safe_dump({"split": {"calibrate": [2023], "test": [2024, 2025]}}), encoding="utf-8")
    return [str(run), "--points", str(tmp_path / "points.parquet"),
            "--partition", str(tmp_path / "partition.json"), "--config", str(tmp_path / "config.yaml"),
            "--output", str(tmp_path / "report"), "--n-boot", "20"]


def test_cli_writes_reconstructable_tables_and_exact_source_hashes(tmp_path):
    argv = inputs(tmp_path)
    before = {path: path.read_bytes() for path in [tmp_path / "run" / "predictions.parquet",
              tmp_path / "points.parquet", tmp_path / "partition.json", tmp_path / "config.yaml"]}
    assert main(argv) == 0
    result = tmp_path / "report"
    manifest = json.loads((result / "manifest.json").read_text())
    assert manifest["sha256"] == hashlib.sha256(before[tmp_path / "run" / "predictions.parquet"]).hexdigest()
    for name, suffix in [("points", "parquet"), ("partition", "json"), ("config", "yaml")]:
        assert manifest["inputs"][name]["sha256"] == hashlib.sha256(before[tmp_path / f"{name}.{suffix}"]).hexdigest()
    assert manifest["n_reference_rows_excluded"] == 42
    assert manifest["models"] == ["smokecast", "noaa_best"]
    assert manifest["partition_provenance"] == partition()["provenance"]
    assert {path.name for path in result.iterdir()} == {"manifest.json", "summary.csv", "daily.parquet", "sites.csv"}
    assert len(pd.read_csv(result / "summary.csv")) == 12
    assert len(pd.read_csv(result / "sites.csv")) == 6
    for path, payload in before.items():
        assert path.read_bytes() == payload


@pytest.mark.parametrize("problem", ["lock", "issue_year", "target_year", "overlap", "existing_output",
                                    "bad_partition", "invalid_edges", "missing_parent"])
def test_cli_rejects_unsafe_or_invalid_reports_before_creating_output(tmp_path, problem):
    argv = inputs(tmp_path)
    if problem == "lock":
        (tmp_path / "run" / "FINAL_RUN_LOCK.json").write_text("{}")
    elif problem in {"issue_year", "target_year"}:
        frame = forecasts(1)
        frame["issue_date"] = pd.Timestamp("2024-06-01" if problem == "issue_year" else "2023-12-31")
        frame.to_parquet(tmp_path / "run" / "predictions.parquet", index=False)
    elif problem == "overlap":
        (tmp_path / "config.yaml").write_text(yaml.safe_dump({"split": {"calibrate": [2023, 2024], "test": [2024]}}))
    elif problem == "existing_output":
        (tmp_path / "report").mkdir()
        (tmp_path / "report" / "keep").write_text("original")
    elif problem == "bad_partition":
        (tmp_path / "partition.json").write_text("null")
    elif problem == "invalid_edges":
        argv += ["--edge-km", "25"]
    else:
        argv[argv.index("--output") + 1] = str(tmp_path / "absent" / "report")
    with pytest.raises(SystemExit) as exc:
        main(argv)
    assert exc.value.code == 2
    if problem == "existing_output":
        assert (tmp_path / "report" / "keep").read_text() == "original"
    else:
        assert not (tmp_path / "report").exists()


def test_cli_accepts_prediction_file_and_explicit_model_lead_edges(tmp_path):
    argv = inputs(tmp_path)
    argv[0] = str(tmp_path / "run" / "predictions.parquet")
    argv += ["--model", "noaa_best", "--lead", "1", "--edge-km", "0", "--edge-km", "100"]
    assert main(argv) == 0
    summary = pd.read_csv(tmp_path / "report" / "summary.csv")
    assert len(summary) == 3 and summary.model.eq("noaa_best").all()
    assert summary.rmse_difference.dropna().eq(0).all()


def test_cli_plot_option_writes_and_records_figure(tmp_path):
    argv = inputs(tmp_path)
    assert main([*argv, "--plot"]) == 0
    result = tmp_path / "report"
    manifest = json.loads((result / "manifest.json").read_text())
    assert manifest["plots"] == ["spatial_L1.png"]
    assert (result / "spatial_L1.png").read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
