import hashlib
import json
from datetime import date, datetime

import numpy as np
import pandas as pd
import pytest
import yaml

from serein.data.hrrr import DEFAULT_MET, SHORT
from serein.eval.forecast_schedule import main, scheduled_inputs
from serein.features.daily import model_daily
from serein.features.table import MET_VARS

DAY = date(2023, 8, 18)


def points(offsets=(-8., -7., -5.)):
    return pd.DataFrame({"point_id": [f"p{i}" for i in range(len(offsets))], "gmt_offset": offsets})


def test_western_12z_horizons_explain_absent_long_lead_inputs():
    registry = points([-8.])
    aqm = scheduled_inputs(registry, DAY, [0, 1, 2, 3], source="aqm", cycle=12)
    assert aqm.n_scheduled.tolist() == [20, 24, 24, 4]
    assert aqm.schedule_status.tolist() == ["meets_feature_threshold"] * 3 + ["below_feature_threshold"]
    assert aqm.first_valid_utc.iloc[0] == pd.Timestamp("2023-08-18 12:00")
    assert aqm.last_valid_utc.iloc[-1] == pd.Timestamp("2023-08-21 11:00")
    hrrr = scheduled_inputs(registry, DAY, [0, 1, 2, 3], source="hrrr", cycle=12)
    smoke = hrrr.loc[hrrr.variable.eq("smoke")]
    assert smoke.n_scheduled.tolist() == [20, 24, 5, 0]
    assert smoke.schedule_status.tolist() == ["meets_feature_threshold"] * 2 + [
        "below_feature_threshold", "no_scheduled_samples"]
    assert pd.isna(smoke.first_valid_utc.iloc[-1])
    assert pd.isna(smoke.last_valid_utc.iloc[-1])
    met = hrrr.loc[hrrr.variable.eq("t2m")]
    assert met.n_scheduled.tolist() == [7, 8, 2, 0]
    assert hrrr.cycle_available_assumed.all() and aqm.cycle_available_assumed.all()


@pytest.mark.parametrize("source", ["aqm", "hrrr"])
@pytest.mark.parametrize("offset", [-24., -8., -7., -5., 0., 5.5, 5.75, 14., 24.])
@pytest.mark.parametrize("cycle", [0, 6, 12, 23])
def test_analytic_counts_match_explicit_timestamp_enumeration(source, offset, cycle):
    registry = points([offset])
    report = scheduled_inputs(registry, DAY, [0, 1, 2, 3, 4], source=source, cycle=cycle,
                              smoke_every=2, met_every=5)
    for row in report.itertuples(index=False):
        cadence = 1 if source == "aqm" else 2 if row.variable == "smoke" else 5
        hours = list(range(72)) if source == "aqm" else list(range(0, 49, cadence))
        if row.aggregation == "issue_wind":
            hours = [hour for hour in hours if hour == int(18.5 - cycle)]
        else:
            hours = [hour for hour in hours if 24 * row.lead <= cycle + offset + hour < 24 * (row.lead + 1)]
        assert row.n_scheduled == len(hours)
        if hours:
            assert row.first_valid_utc == pd.Timestamp(DAY) + pd.Timedelta(hours=cycle + min(hours))
            assert row.last_valid_utc == pd.Timestamp(DAY) + pd.Timedelta(hours=cycle + max(hours))
        else:
            assert pd.isna(row.first_valid_utc) and pd.isna(row.last_valid_utc)


@pytest.mark.parametrize("source,day", [("hrrr", DAY), ("aqm", DAY), ("aqm", date(2021, 7, 19))])
def test_schedule_counts_and_thresholds_match_real_daily_aggregation(source, day):
    registry = points([-8., -5., 5.5])
    rows = []
    fields = ["smoke", *MET_VARS] if source == "hrrr" else ["pm25"]
    for point in registry.point_id:
        for variable in fields:
            hours = (range(0, 49, 1 if variable == "smoke" else 3) if source == "hrrr"
                     else range(48 if day < date(2021, 7, 20) else 72))
            rows.extend({"point_id": point, "var": variable, "issue_date": day,
                         "valid_utc": pd.Timestamp(day) + pd.Timedelta(hours=12 + hour), "value": 10.}
                        for hour in hours)
    raw = pd.DataFrame(rows)
    schedule = scheduled_inputs(registry, day, [0, 1, 2, 3], source=source, cycle=12)
    schedule = schedule.loc[schedule.aggregation.eq("local_day")]
    offsets = registry.set_index("point_id").gmt_offset
    parts = []
    for variable, values in raw.groupby("var"):
        daily = model_daily(values, offsets, min_count=12 if variable in {"smoke", "pm25"} else 4)
        parts.append(daily.assign(variable=variable))
    actual = pd.concat(parts, ignore_index=True)
    merged = schedule.merge(actual, on=["point_id", "variable", "lead"], how="left", validate="one_to_one")
    assert merged.n_scheduled.eq(merged["size"].fillna(0)).all()
    assert merged.schedule_status.eq("meets_feature_threshold").eq(merged["mean"].notna()).all()


def test_aqm_historical_transition_uses_48_then_72_hour_starts():
    old = scheduled_inputs(points([-8.]), date(2021, 7, 19), [0, 1, 2, 3], source="aqm", cycle=12)
    new = scheduled_inputs(points([-8.]), date(2021, 7, 20), [0, 1, 2, 3], source="aqm", cycle=12)
    assert old.n_scheduled.tolist() == [20, 24, 4, 0]
    assert new.n_scheduled.tolist() == [20, 24, 24, 4]


def test_disabled_weather_fields_and_unsampled_issue_wind_are_explicit():
    report = scheduled_inputs(points(), DAY, [0, 1], source="hrrr", cycle=12,
                              met_vars=["TMP:2 m above ground"], met_every=5)
    disabled = report.loc[report.variable.isin(["u10", "v10", "pbl", "rh2m", "colmd"])]
    assert disabled.n_scheduled.eq(0).all()
    assert disabled.schedule_status.eq("no_scheduled_samples").all()
    assert report.loc[report.variable.eq("t2m"), "n_scheduled"].gt(0).all()
    assert report.loc[report.variable.eq("smoke"), "n_scheduled"].gt(0).all()
    enabled = scheduled_inputs(points(), DAY, [0], source="hrrr", cycle=12, met_every=5)
    assert enabled.loc[enabled.aggregation.eq("issue_wind"), "n_scheduled"].eq(0).all()


def test_issue_wind_matches_current_integer_forecast_hour_selection():
    report = scheduled_inputs(points(), DAY, [0], source="hrrr", cycle=12)
    wind = report.loc[report.aggregation.eq("issue_wind")]
    assert wind.n_scheduled.eq(1).all()
    assert wind.first_valid_utc.eq(pd.Timestamp("2023-08-18 18:00")).all()


def test_schedules_keep_unposted_cycles_but_flag_the_posting_assumption():
    for source in ("hrrr", "aqm"):
        report = scheduled_inputs(points(), DAY, [0], source=source, cycle=23)
        assert not report.cycle_available_assumed.any()
        assert report.n_scheduled.gt(0).any()


def test_sample_threshold_does_not_claim_full_local_day_coverage():
    report = scheduled_inputs(points([-8.]), DAY, [0], source="aqm", cycle=12)
    assert report.schedule_status.iloc[0] == "meets_feature_threshold"
    assert report.n_scheduled.iloc[0] < 24


def test_input_order_index_and_registry_are_preserved():
    registry = points([-8., -5.]).iloc[::-1]
    before = registry.copy(deep=True)
    first = scheduled_inputs(registry, DAY, [1, 0], source="aqm", cycle=12)
    second = scheduled_inputs(registry.reset_index(drop=True), DAY, [1, 0], source="aqm", cycle=12)
    pd.testing.assert_frame_equal(first, second)
    pd.testing.assert_frame_equal(registry, before)
    assert first.point_id.tolist() == ["p1", "p1", "p0", "p0"]


@pytest.mark.parametrize("options", [
    {"source": "bad"}, {"cycle": -1}, {"cycle": True}, {"cycle": 24},
    {"max_fhr": -1}, {"max_fhr": 1.5}, {"max_fhr": True},
    {"smoke_every": 0}, {"met_every": 0}, {"met_every": False},
    {"met_vars": ["bad"]}, {"met_vars": DEFAULT_MET * 2},
    {"issue_hour_utc": np.nan}, {"issue_hour_utc": 24}, {"issue_hour_utc": True},
    {"day": datetime(2023, 8, 18)}, {"leads": []}, {"leads": [-1]}, {"leads": [True]},
    {"leads": [1, 1]},
])
def test_invalid_options(options):
    kwargs = {"source": "hrrr", "cycle": 12, "day": DAY, "leads": [0, 1]}
    kwargs.update(options)
    with pytest.raises((TypeError, ValueError)):
        scheduled_inputs(points(), **kwargs)


@pytest.mark.parametrize("change", ["empty", "duplicate ids", "blank id", "missing id",
                                    "duplicate columns", "nan offset", "large offset"])
def test_invalid_registry(change):
    registry = points()
    if change == "empty":
        registry = registry.iloc[:0]
    elif change == "duplicate ids":
        registry.loc[1, "point_id"] = registry.loc[0, "point_id"]
    elif change == "blank id":
        registry.loc[0, "point_id"] = " "
    elif change == "missing id":
        registry.loc[0, "point_id"] = None
    elif change == "duplicate columns":
        registry = pd.concat([registry, registry[["gmt_offset"]]], axis=1)
    else:
        registry.loc[0, "gmt_offset"] = np.nan if change == "nan offset" else 25
    with pytest.raises(ValueError):
        scheduled_inputs(registry, DAY, [0], source="hrrr", cycle=12)


@pytest.fixture
def cli_files(tmp_path):
    config, registry, output = (tmp_path / name for name in ("study.yaml", "points.parquet", "report"))
    config.write_text(yaml.safe_dump({"split": {"train": [2021, 2022], "calibrate": [2023],
        "test": [2024, 2025]}, "season_months": [6, 7, 8, 9, 10], "leads": [0, 1, 2, 3]}))
    points().to_parquet(registry, index=False)
    return config, registry, output


def test_cli_emits_hashes_counts_and_explicit_assumptions(cli_files):
    config, registry, output = cli_files
    before = registry.read_bytes()
    assert main(["--config", str(config), "--points", str(registry), "--date", str(DAY),
                 "--output", str(output)]) == 0
    report = pd.read_parquet(output / "schedule.parquet")
    summary = pd.read_csv(output / "summary.csv")
    manifest = json.loads((output / "manifest.json").read_text())
    assert manifest["config_sha256"] == hashlib.sha256(config.read_bytes()).hexdigest()
    assert manifest["points_sha256"] == hashlib.sha256(before).hexdigest()
    assert summary.n_points.sum() == len(report)
    assert report.source.unique().tolist() == ["hrrr", "aqm"]
    assert manifest["sources"] == ["hrrr", "aqm"]
    assert registry.read_bytes() == before
    assert set(report.variable) == {*SHORT.values(), "pm25"}


@pytest.mark.parametrize("failure", ["existing output", "missing parent", "reserved date", "out of season",
                                    "overlapping years", "bad yaml", "missing registry", "duplicate source"])
def test_cli_rejects_invalid_requests_without_output(cli_files, failure):
    config, registry, output = cli_files
    day, extra = str(DAY), []
    if failure == "existing output":
        output.mkdir()
        (output / "sentinel").write_text("keep")
    elif failure == "missing parent":
        output = output / "nested"
    elif failure == "reserved date":
        day = "2024-08-18"
    elif failure == "out of season":
        day = "2023-01-01"
    elif failure == "overlapping years":
        text = yaml.safe_load(config.read_text())
        text["split"]["test"].append(2023)
        config.write_text(yaml.safe_dump(text))
    elif failure == "bad yaml":
        config.write_text("split: [unterminated")
    elif failure == "missing registry":
        registry = registry.with_name("absent.parquet")
    else:
        extra = ["--source", "hrrr", "--source", "hrrr"]
    with pytest.raises(SystemExit) as error:
        main(["--config", str(config), "--points", str(registry), "--date", day,
              "--output", str(output), *extra])
    assert error.value.code == 2
    if failure == "existing output":
        assert (output / "sentinel").read_text() == "keep"
    else:
        assert not output.exists()
