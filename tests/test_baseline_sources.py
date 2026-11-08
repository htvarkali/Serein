import hashlib
import json

import numpy as np
import pandas as pd
import pytest
import yaml

from serein.eval.baseline_sources import COUNTS, SOURCES, SUMS, analyze_sources, main


def forecasts():
    return pd.DataFrame({
        "issue_date": pd.to_datetime(["2023-06-01"] * 4 + ["2023-06-03"] * 4),
        "point_id": ["A", "B", "C", "D"] * 2,
        "y_L1": [10., 30., 50., 70., 10., 30., 50., 70.],
        "smokecast_L1": [11., 31., 52., 72., 11., 31., 52., 72.],
        "aqm_bc_L1": [12., np.nan, np.nan, np.nan] * 2,
        "hrrr_smoke_L1": [99., 34., np.nan, np.nan] * 2,
        "persistence_L1": [88., 88., 56., np.nan] * 2,
        "noaa_best_L1": [12., 34., 56., np.nan] * 2,
    })


def test_source_priority_paired_errors_and_counts():
    frame = forecasts()
    summary, daily = analyze_sources(frame)
    result = summary.set_index("source")
    assert result.index.tolist() == ["all", "noaa_only", *SOURCES]
    assert result.loc["all", "n_input"] == len(frame)
    assert result.loc["all", "n_scored"] == 6
    assert result.loc["all", "model_rmse"] == pytest.approx(np.sqrt(np.mean([1., 1., 4.])))
    assert result.loc["all", "baseline_rmse"] == pytest.approx(np.sqrt(np.mean([4., 16., 36.])))
    assert result.loc["noaa_only", "baseline_rmse"] == pytest.approx(np.sqrt(np.mean([4., 16.])))
    assert result.loc["persistence", "model_mae"] == 2
    assert result.loc["persistence", "baseline_bias"] == 6
    assert result.loc["persistence", "skill"] == pytest.approx(1 - 2 / 6)
    assert result.loc["unavailable", "n_input"] == 2
    assert result.loc["unavailable", "n_scored"] == 0
    assert result.loc["unavailable", "status"] == "no_scored_rows"
    assert pd.isna(result.loc["unavailable", "skill"])
    assert daily.issue_date.nunique() == 2
    totals = daily.groupby("source")[list(COUNTS)].sum()
    pd.testing.assert_frame_equal(totals, result[list(COUNTS)].sort_index(), check_dtype=False)
    disjoint = daily.loc[daily.source.isin(SOURCES)].groupby("issue_date")[list(SUMS)].sum()
    pooled = daily.loc[daily.source.eq("all")].set_index("issue_date")[list(SUMS)]
    pd.testing.assert_frame_equal(disjoint, pooled)


def test_source_selection_precedes_target_and_model_availability():
    frame = forecasts()
    frame.loc[0, "y_L1"] = np.nan
    frame.loc[1, "smokecast_L1"] = np.nan
    summary, daily = analyze_sources(frame)
    rows = summary.set_index("source")
    assert rows.loc["aqm_bc", "n_input"] == rows.loc["hrrr_smoke", "n_input"] == 2
    assert rows.loc["aqm_bc", "n_observed"] == 1
    assert rows.loc["hrrr_smoke", "n_model"] == 1
    assert rows.loc["all", "n_pairwise"] == 4
    assert rows.loc["all", "n_excluded"] == 4
    assert daily.loc[daily.n_scored.eq(0), list(SUMS)].eq(0).all().all()


def test_common_population_excludes_missing_other_model_only_when_requested():
    frame = forecasts()
    frame["other_L1"] = frame.smokecast_L1
    frame.loc[0, "other_L1"] = np.nan
    models = ["smokecast", "other"]
    separate, _ = analyze_sources(frame, models=models)
    common, _ = analyze_sources(frame, models=models, common_rows=True)
    assert separate.loc[separate.source.eq("all"), "n_scored"].tolist() == [6, 5]
    assert common.loc[common.source.eq("all"), "n_scored"].tolist() == [5, 5]
    assert common.loc[common.source.eq("all"), "n_pairwise"].tolist() == [6, 5]
    assert common.loc[common.source.eq("all"), "n_excluded_common"].tolist() == [1, 0]
    assert common.population.eq("common_rows").all()


def test_perfect_baseline_has_undefined_relative_skill():
    frame = forecasts()
    frame["y_L1"] = frame.noaa_best_L1
    rows = analyze_sources(frame)[0]
    assert rows.skill.isna().all()
    assert rows.loc[rows.status.eq("ok"), "baseline_rmse"].eq(0).all()


@pytest.mark.parametrize("change", ["wrong value", "unexpected missing", "unexpected finite",
                                    "wrong priority", "no target"])
def test_inconsistent_fallback_chain_fails_even_on_unscored_rows(change):
    frame = forecasts()
    if change in {"wrong value", "no target"}:
        frame.loc[0, "noaa_best_L1"] = 13.
        if change == "no target":
            frame.loc[0, "y_L1"] = np.nan
    elif change == "unexpected missing":
        frame.loc[0, "noaa_best_L1"] = np.nan
    elif change == "unexpected finite":
        frame.loc[3, "noaa_best_L1"] = 0.
    else:
        frame.loc[0, "noaa_best_L1"] = frame.loc[0, "hrrr_smoke_L1"]
    with pytest.raises(ValueError, match="disagrees.*1 rows"):
        analyze_sources(frame)


def test_serialization_rounding_is_tolerated_but_not_used_for_source_selection():
    frame = forecasts()
    frame.loc[0, "noaa_best_L1"] += 1e-6
    summary, _ = analyze_sources(frame)
    assert summary.set_index("source").loc["aqm_bc", "n_input"] == 2


def test_missing_source_groups_are_explicit_and_input_is_unchanged():
    frame = forecasts().iloc[[0, 4]].copy()
    before = frame.copy(deep=True)
    summary, daily = analyze_sources(frame)
    empty = summary.loc[summary.source.isin(["hrrr_smoke", "persistence", "unavailable"])]
    assert empty.n_input.eq(0).all() and empty.n_days_input.eq(0).all()
    assert empty.status.eq("no_scored_rows").all()
    assert not daily.source.isin(empty.source).any()
    pd.testing.assert_frame_equal(frame, before)


def test_selected_models_and_leads():
    frame = forecasts().rename(columns=lambda c: c.replace("_L1", "_L2"))
    frame = frame.rename(columns={"smokecast_L2": "other_L2"})
    summary, _ = analyze_sources(frame, models=["other"], leads=[2])
    assert summary.model.eq("other").all() and summary.lead.eq(2).all()


@pytest.mark.parametrize("column", ["y", "smokecast", "aqm_bc", "hrrr_smoke", "persistence", "noaa_best"])
def test_incomplete_export_cannot_claim_source_provenance(column):
    with pytest.raises(ValueError, match="missing forecast columns"):
        analyze_sources(forecasts().drop(columns=f"{column}_L1"), leads=[1])


@pytest.mark.parametrize("column", ["y", "smokecast", "aqm_bc", "hrrr_smoke", "persistence", "noaa_best"])
@pytest.mark.parametrize("value", [np.inf, -np.inf])
def test_infinite_forecasts_fail_even_when_the_source_is_not_selected(column, value):
    frame = forecasts()
    frame.loc[0, f"{column}_L1"] = value
    with pytest.raises(ValueError, match="finite"):
        analyze_sources(frame)


@pytest.mark.parametrize("options", [{"models": []}, {"models": ["a", "a"]},
    {"models": ["has space"]}, {"leads": []}, {"leads": [True]}, {"leads": [1, 1]},
    {"leads": [-1]}, {"leads": [1.5]}, {"common_rows": 1}])
def test_invalid_options(options):
    with pytest.raises((ValueError, TypeError)):
        analyze_sources(forecasts(), **options)


@pytest.mark.parametrize("change", ["empty", "duplicate rows", "duplicate columns", "missing id",
                                    "blank id", "timestamp", "timezone", "missing date"])
def test_invalid_keys(change):
    frame = forecasts()
    if change == "empty":
        frame = frame.iloc[:0]
    elif change == "duplicate rows":
        frame = pd.concat([frame, frame.iloc[:1]])
    elif change == "duplicate columns":
        frame = pd.concat([frame, frame[["y_L1"]]], axis=1)
    elif change == "missing id":
        frame.loc[0, "point_id"] = None
    elif change == "blank id":
        frame.loc[0, "point_id"] = " "
    elif change == "timestamp":
        frame["issue_date"] += pd.Timedelta(hours=1)
    elif change == "timezone":
        frame["issue_date"] = frame.issue_date.dt.tz_localize("UTC")
    else:
        frame.loc[0, "issue_date"] = pd.NaT
    with pytest.raises(ValueError):
        analyze_sources(frame)


def test_error_overflow_is_rejected():
    frame = forecasts()
    frame.loc[0, "smokecast_L1"] = np.finfo(float).max
    with pytest.raises(ValueError, match="overflow"):
        analyze_sources(frame)


@pytest.fixture
def cli_files(tmp_path):
    source, config, output = (tmp_path / name for name in ("predictions.parquet", "study.yaml", "report"))
    forecasts().to_parquet(source, index=False)
    config.write_text(yaml.safe_dump({"split": {"calibrate": [2023], "test": [2024, 2025]}}))
    return source, config, output


def test_cli_hashes_source_and_config_and_writes_reproducible_scores(cli_files):
    source, config, output = cli_files
    before = source.read_bytes()
    assert main([str(source.parent), "--config", str(config), "--output", str(output)]) == 0
    summary, daily = analyze_sources(forecasts())
    pd.testing.assert_frame_equal(pd.read_csv(output / "summary.csv"), summary, check_dtype=False)
    pd.testing.assert_frame_equal(pd.read_parquet(output / "daily.parquet"), daily)
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["sha256"] == hashlib.sha256(before).hexdigest()
    assert manifest["config_sha256"] == hashlib.sha256(config.read_bytes()).hexdigest()
    assert manifest["priority"] == list(SOURCES)
    assert manifest["models"] == ["smokecast"] and manifest["leads"] == [1]
    assert source.read_bytes() == before


@pytest.mark.parametrize("failure", ["existing output", "missing parent", "final lock", "test dates",
    "target in test", "missing config", "bad yaml", "bad config", "overlapping years", "bad chain"])
def test_cli_rejects_invalid_inputs_before_writing(cli_files, failure):
    source, config, output = cli_files
    if failure == "existing output":
        output.mkdir()
        (output / "sentinel").write_text("keep")
    elif failure == "missing parent":
        output = output / "nested"
    elif failure == "final lock":
        (source.parent / "FINAL_RUN_LOCK.json").write_text("{}")
    elif failure in {"test dates", "target in test", "bad chain"}:
        frame = forecasts()
        if failure == "bad chain":
            frame.loc[0, "noaa_best_L1"] = 0.
        else:
            frame["issue_date"] = pd.Timestamp("2024-06-01" if failure == "test dates" else "2023-12-31")
            frame["point_id"] = [str(i) for i in range(len(frame))]
        frame.to_parquet(source, index=False)
    elif failure == "missing config":
        config = config.with_name("absent.yaml")
    elif failure == "bad yaml":
        config.write_text("split: [unterminated")
    elif failure == "overlapping years":
        config.write_text("split: {calibrate: [2023], test: [2023]}")
    else:
        config.write_text("split: {}")
    with pytest.raises(SystemExit) as error:
        main([str(source), "--config", str(config), "--output", str(output)])
    assert error.value.code == 2
    if failure == "existing output":
        assert (output / "sentinel").read_text() == "keep"
        assert len(list(output.iterdir())) == 1
    else:
        assert not output.exists()
