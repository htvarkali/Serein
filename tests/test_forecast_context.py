from datetime import date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from serein.data import aqm, grib, hrrr
from serein.data.grib import GribField
from serein.features import context
from serein.models import infer
from serein.personal.action_plan import (
    forecast_confounders,
    forecast_context_values,
    make_plan,
)

DAY = date(2023, 8, 18)


@pytest.fixture
def points():
    return pd.DataFrame({"point_id": ["west", "east"], "lat": [40., 40.],
                         "lon": [-120., -75.], "gmt_offset": [-8, -5], "kind": ["epa", "epa"]})


def hourly(points, ozone=True):
    rows = []
    for p in points.itertuples():
        for step in range(72 if ozone else 49):
            valid = pd.Timestamp(DAY) + pd.Timedelta(hours=12 + step)
            local_hour = (valid + pd.Timedelta(hours=p.gmt_offset)).hour
            rows.append({"point_id": p.point_id, "issue_date": DAY, "valid_utc": valid,
                         "step" if ozone else "fhr": step,
                         "lat": p.lat, "lon": p.lon,
                         "value": float(local_hour if ozone else local_hour + 20)})
    return pd.DataFrame(rows)


def cached_context(monkeypatch, points, ozone=None, temperature=None, issue_hour=18.5):
    ozone = hourly(points) if ozone is None else ozone
    temperature = hourly(points, False) if temperature is None else temperature
    monkeypatch.setattr(aqm, "load_cycles", lambda *args, **kwargs: ozone.copy())
    monkeypatch.setattr(hrrr, "load_temperature_cycles", lambda *args, **kwargs: temperature.copy())
    study = SimpleNamespace(name="context_synthetic", raw={"issue_hour_utc": issue_hour})
    return study, context.forecast_context(study, DAY, points, [0, 1, 2, 3])


@pytest.mark.parametrize("units,value", [("ppb", 40.), ("ppbV", 40.), ("ppm", .04),
                                        ("ppmV", .04), ("mol mol**-1", 40e-9)])
def test_ozone_uses_declared_units(units, value):
    result = aqm.ozone_to_ppb(np.array([value, -value, np.inf, np.nan]), units)
    assert result[0] == pytest.approx(40)
    assert np.isnan(result[1:]).all()


@pytest.mark.parametrize("units,value", [("K", 305.15), ("degC", 32.), ("C", 32.)])
def test_temperature_uses_declared_units(units, value):
    assert hrrr.temperature_to_c(np.array([value]), units)[0] == pytest.approx(32.)


def test_unknown_units_are_not_guessed():
    with pytest.raises(ValueError, match="ozone units"):
        aqm.ozone_to_ppb(np.array([.04]), "kg/m3")
    with pytest.raises(ValueError, match="temperature units"):
        hrrr.temperature_to_c(np.array([90.]), "F")


def test_ozone_extraction_has_separate_ppb_cache(monkeypatch, tmp_path):
    def interim(name):
        path = tmp_path / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    monkeypatch.setattr(aqm, "interim_dir", interim)
    monkeypatch.setattr(grib, "interim_dir", interim)
    requested = []
    response = SimpleNamespace(content=b"ozone", close=lambda: None)
    monkeypatch.setattr(aqm, "get", lambda url, **kwargs: requested.append(url) or response)
    fields = [GribField("ozcon", "sigma:1", step, step + 1,
                        np.array([.04]), "ppm", datetime(2023, 8, 18, 12), "avg")
              for step in range(72)]
    monkeypatch.setattr(aqm, "decode_messages", lambda *args, **kwargs: (fields, ([40.], [-120.])))
    points = pd.DataFrame({"point_id": ["site"], "lat": [40.], "lon": [-120.]})
    result = aqm.extract_cycle(DAY, points, pollutant="o3")
    assert "ave_1hr_o3_bc" in requested[0]
    assert result.value.to_numpy() == pytest.approx(np.full(72, 40.))
    assert result.attrs["ozone_units"] == "ppb"
    assert result.valid_utc.iloc[0] == pd.Timestamp("2023-08-18 12:00")
    assert result[["lat", "lon"]].iloc[0].tolist() == [40., -120.]
    pd.testing.assert_frame_equal(aqm.extract_cycle(DAY, points, pollutant="o3"), result)
    assert len(requested) == 1
    assert aqm.load_cycles([DAY]).empty  # Existing PM cache is untouched.
    assert len(aqm.load_cycles([DAY], pollutant="o3")) == 72


def test_hourly_temperature_is_separate_from_three_hour_weather(monkeypatch, tmp_path):
    def interim(name):
        path = tmp_path / name
        path.mkdir(parents=True, exist_ok=True)
        return path

    monkeypatch.setattr(hrrr, "interim_dir", interim)
    monkeypatch.setattr(grib, "interim_dir", interim)
    requested = []

    def fetch(day, cycle, fhr, wanted):
        requested.append((fhr, wanted))
        return [(hrrr.TEMPERATURE, bytes([fhr]))]

    def decode(blob, **kwargs):
        step = blob[0]
        return [GribField("2t", "heightAboveGround:2", step, step,
                          np.array([300. + step]), "K", datetime(2023, 8, 18, 12), "instant")], (
                              [40.], [-120.])

    monkeypatch.setattr(hrrr, "_fetch_fields", fetch)
    monkeypatch.setattr(hrrr, "decode_messages", decode)
    points = pd.DataFrame({"point_id": ["site"], "lat": [40.], "lon": [-120.]})
    result = hrrr.extract_temperature_cycle(DAY, points, max_fhr=3, workers=1)
    assert requested == [(i, [hrrr.TEMPERATURE]) for i in range(4)]
    assert result.value.tolist() == pytest.approx([26.85, 27.85, 28.85, 29.85])
    assert result.attrs["temperature_units"] == "degC"
    assert len(hrrr.load_temperature_cycles([DAY])) == 4
    assert hrrr.load_cycles([DAY]).empty
    pd.testing.assert_frame_equal(
        hrrr.extract_temperature_cycle(DAY, points, max_fhr=3, workers=1), result)
    assert len(requested) == 4


def test_local_day_coverage_and_forecast_horizon(monkeypatch, points):
    _, result = cached_context(monkeypatch, points)
    tomorrow = result[result.valid_date == DAY + timedelta(days=1)]
    assert tomorrow.ozone_max8h_ppb.tolist() == [19.5, 19.5]  # Mean of hours 16 through 23.
    assert tomorrow.temperature_max_c.tolist() == [43., 43.]
    assert (tomorrow.ozone_hours == 24).all()
    assert (tomorrow.temperature_hours == 24).all()
    today = result[result.valid_date == DAY]
    assert today.ozone_max8h_ppb.isna().all()
    assert today.temperature_max_c.isna().all()
    assert today.temperature_hours.tolist() == [20, 17]
    later = result[result.valid_date >= DAY + timedelta(days=2)]
    assert later.temperature_max_c.isna().all()
    assert set(tomorrow.temperature_statistic) == {"maximum_hourly_forecast"}
    assert set(tomorrow.ozone_statistic) == {"max_8h_within_local_day"}
    assert set(tomorrow.ozone_cycle_utc) == {pd.Timestamp("2023-08-18 12:00")}


def test_three_hour_samples_and_nonfinite_hours_remain_unknown(monkeypatch, points):
    ozone, temperature = hourly(points), hourly(points, False)
    ozone.loc[ozone.step == 20, "value"] = np.inf
    temperature = temperature[temperature.fhr % 3 == 0]
    _, result = cached_context(monkeypatch, points, ozone, temperature)
    tomorrow = result[result.valid_date == DAY + timedelta(days=1)]
    assert tomorrow.ozone_max8h_ppb.isna().all()
    assert tomorrow.ozone_hours.tolist() == [23, 23]
    assert tomorrow.temperature_max_c.isna().all()
    assert tomorrow.temperature_hours.tolist() == [8, 8]


def test_moved_coordinates_do_not_reuse_context(monkeypatch, points):
    ozone, temperature = hourly(points), hourly(points, False)
    moved = points.copy()
    moved.loc[moved.point_id == "west", "lat"] += 1
    _, result = cached_context(monkeypatch, moved, ozone, temperature)
    assert result[result.point_id == "west"].temperature_hours.eq(0).all()
    assert result[result.point_id == "west"].ozone_hours.eq(0).all()
    assert result[result.point_id == "east"].temperature_max_c.notna().any()


def test_ineligible_cycle_is_not_loaded(monkeypatch, points):
    def unexpected(*args, **kwargs):
        pytest.fail("A model cycle posted after issue time must not be used")

    monkeypatch.setattr(aqm, "load_cycles", unexpected)
    monkeypatch.setattr(hrrr, "load_temperature_cycles", unexpected)
    study = SimpleNamespace(name="synthetic", raw={"issue_hour_utc": 13.})
    result = context.forecast_context(study, DAY, points, [0, 1])
    assert result.ozone_hours.eq(0).all() and result.temperature_hours.eq(0).all()


def test_ozone_has_its_own_conservative_posting_allowance(monkeypatch, points):
    def unexpected(*args, **kwargs):
        pytest.fail("Ozone is not assumed available before 18:15 for the 12z cycle")

    monkeypatch.setattr(aqm, "load_cycles", unexpected)
    monkeypatch.setattr(hrrr, "load_temperature_cycles", lambda *args, **kwargs: hourly(points, False))
    study = SimpleNamespace(name="synthetic", raw={"issue_hour_utc": 18.1})
    result = context.forecast_context(study, DAY, points, [1])
    assert result.ozone_hours.eq(0).all()
    assert result.temperature_hours.eq(24).all()


@pytest.mark.parametrize("bad_step", [True, "1", .5, np.nan, np.inf])
def test_bad_forecast_steps_are_rejected(points, bad_step):
    frame = hourly(points)
    frame["step"] = frame.step.astype(object)
    frame.loc[0, "step"] = bad_step
    with pytest.raises(ValueError, match="steps"):
        context._daily_values(frame, points, DAY, 12, True)


def test_wrong_issue_cycle_and_duplicate_samples_rejected(points):
    frame = hourly(points)
    with pytest.raises(ValueError, match="issue cycle"):
        context._daily_values(frame, points, DAY, 6, True)
    with pytest.raises(ValueError, match="duplicate"):
        context._daily_values(pd.concat([frame, frame.iloc[[0]]]), points, DAY, 12, True)


def test_timezone_representation_does_not_change_local_day(points):
    frame = hourly(points)
    expected = context._daily_values(frame, points, DAY, 12, True)
    frame["valid_utc"] = pd.to_datetime(frame.valid_utc, utc=True).dt.tz_convert("US/Eastern")
    pd.testing.assert_frame_equal(context._daily_values(frame, points, DAY, 12, True), expected)


def complete_row(**values):
    return {"ozone_max8h_ppb": 80., "temperature_max_c": 32.,
            "ozone_hours": 24, "temperature_hours": 24,
            "ozone_statistic": "max_8h_within_local_day",
            "temperature_statistic": "maximum_hourly_forecast", **values}


@pytest.mark.parametrize("temperature,expected", [(31.99, 0), (32., 1), (40., 1)])
def test_context_adapter_uses_existing_hot_day_definition(temperature, expected):
    assert forecast_confounders(complete_row(temperature_max_c=temperature)) == {
        "ozone_ppb": 80., "hot_day": expected}


@pytest.mark.parametrize("unknown", [None, np.nan, pd.NA])
def test_adapter_preserves_unknown_for_display_and_defaults_for_model(unknown):
    row = complete_row(ozone_max8h_ppb=unknown, temperature_max_c=unknown)
    assert forecast_context_values(row) == {"ozone_ppb": None, "temperature_max_c": None}
    assert forecast_confounders(row) == {"ozone_ppb": None, "hot_day": 0}
    assert forecast_confounders({}) == {"ozone_ppb": None, "hot_day": 0}


@pytest.mark.parametrize("missing_statistic", [None, pd.NA, np.nan, "sampled_three_hour_max"])
def test_unrecognized_or_missing_statistic_is_unknown(missing_statistic):
    row = complete_row(ozone_statistic=missing_statistic, temperature_statistic=missing_statistic)
    assert forecast_context_values(row) == {"ozone_ppb": None, "temperature_max_c": None}


@pytest.mark.parametrize("invalid", [True, "32", [32], np.inf, -np.inf])
def test_adapter_rejects_invalid_numeric_context(invalid):
    with pytest.raises((TypeError, ValueError), match="numeric scalar"):
        forecast_confounders(complete_row(temperature_max_c=invalid))


def test_partial_day_is_not_displayed_or_passed_to_model():
    row = complete_row(ozone_hours=23, temperature_hours=8)
    assert forecast_context_values(row) == {"ozone_ppb": None, "temperature_max_c": None}
    assert forecast_confounders(row) == {"ozone_ppb": None, "hot_day": 0}


def test_same_context_reaches_smoke_and_clean_air_comparison():
    calls = []

    class Child:
        def risk_under_forecast(self, *args, **kwargs):
            calls.append(kwargs)
            return {"mean": .1, "lo": .05, "hi": .2}

    plan = make_plan(Child(), "Demo", {.05: 5., .5: 5., .95: 5.}, 5., 5.,
                     **forecast_confounders(complete_row()))
    assert calls == [{"ozone_ppb": 80., "hot_day": 1, "high_pollen": 0}] * 2
    assert plan.zone == "green"


def test_forecast_exports_context_without_changing_pm_quantiles(monkeypatch, points):
    study, _ = cached_context(monkeypatch, points)
    q = torch.log1p(torch.tensor([5., 8., 10., 12., 15.])).repeat(1, 2, 2, 1)
    graph = SimpleNamespace(src=np.array([], int), dst=np.array([], int),
                            bearing=np.array([], float), edge_attr=np.zeros((0, 3)))
    inputs = infer.ForecastInputs(
        model=lambda *args: q, prep=None,
        cqr=SimpleNamespace(apply=lambda lo, hi, mid: (lo, hi)), meta={},
        tab=points.copy(), use=points.copy(), leads=[0, 1],
        X=np.zeros((2, 1)), feat_names=["feature"], wind=np.zeros((2, 2)),
        base=np.zeros((2, 2)), graph=graph, nodes=points.point_id.tolist())
    monkeypatch.setattr(infer, "build_inputs", lambda *args: inputs)
    result = infer.forecast_day(study, DAY, None)
    assert result.q50.tolist() == pytest.approx([10.] * 4)
    assert result[result.lead == 1].temperature_max_c.tolist() == [43., 43.]
    assert result[result.lead == 0].ozone_max8h_ppb.isna().all()
    inputs.use = inputs.use.drop(columns="gmt_offset")
    legacy = infer.forecast_day(study, DAY, None)
    assert legacy.temperature_max_c.isna().all()
    np.testing.assert_array_equal(legacy.q50, result.q50)


@pytest.mark.parametrize("attribute,bad", [
    ("short_name", "pm25"), ("level", "surface"), ("step_type", "max"),
    ("reference_time", datetime(2023, 8, 18, 18)), ("units", "unknown"), ("start_step", 72),
])
def test_ozone_rejects_wrong_grib_identity(monkeypatch, tmp_path, attribute, bad):
    monkeypatch.setattr(aqm, "interim_dir", lambda name: tmp_path)
    monkeypatch.setattr(grib, "interim_dir", lambda name: tmp_path)
    monkeypatch.setattr(aqm, "get", lambda *args, **kwargs: SimpleNamespace(
        content=b"field", close=lambda: None))
    field = GribField("ozcon", "sigma:1", 0, 1, np.array([40.]), "ppb",
                      datetime(2023, 8, 18, 12), "avg")
    setattr(field, attribute, bad)
    if attribute == "start_step":
        field.end_step = bad + 1
    monkeypatch.setattr(aqm, "decode_messages", lambda *args, **kwargs: ([field], ([0.], [0.])))
    points = pd.DataFrame({"point_id": ["site"], "lat": [0.], "lon": [0.]})
    with pytest.raises(ValueError, match="ozone"):
        aqm.extract_cycle(DAY, points, pollutant="o3")
    assert not (tmp_path / "20230818_12z.parquet").exists()


@pytest.mark.parametrize("attribute,bad", [
    ("short_name", "skt"), ("level", "surface"), ("step_type", "max"),
    ("reference_time", datetime(2023, 8, 18, 18)), ("end_step", 1),
])
def test_temperature_rejects_wrong_grib_identity(monkeypatch, tmp_path, attribute, bad):
    monkeypatch.setattr(hrrr, "interim_dir", lambda name: tmp_path)
    monkeypatch.setattr(grib, "interim_dir", lambda name: tmp_path)
    monkeypatch.setattr(hrrr, "_fetch_fields", lambda *args: [(hrrr.TEMPERATURE, b"field")])
    field = GribField("2t", "heightAboveGround:2", 0, 0, np.array([300.]), "K",
                      datetime(2023, 8, 18, 12), "instant")
    setattr(field, attribute, bad)
    monkeypatch.setattr(hrrr, "decode_messages", lambda *args, **kwargs: ([field], ([0.], [0.])))
    points = pd.DataFrame({"point_id": ["site"], "lat": [0.], "lon": [0.]})
    with pytest.raises(ValueError, match="temperature"):
        hrrr.extract_temperature_cycle(DAY, points, max_fhr=0, workers=1)


@pytest.mark.parametrize("ozone", [False, True])
def test_relabelled_cache_cannot_change_initialization(monkeypatch, tmp_path, ozone):
    monkeypatch.setattr(aqm, "interim_dir", lambda name: tmp_path)
    monkeypatch.setattr(hrrr, "interim_dir", lambda name: tmp_path)
    frame = pd.DataFrame({"value": [40.]})
    frame.attrs["ozone_units" if ozone else "temperature_units"] = "ppb" if ozone else "degC"
    frame.attrs["context_cycle_utc"] = "2023-08-18T18:00:00"
    frame.to_parquet(tmp_path / "20230818_12z.parquet")
    with pytest.raises(ValueError, match="initialization"):
        if ozone:
            aqm.load_cycles([DAY], pollutant="o3")
        else:
            hrrr.load_temperature_cycles([DAY])


def test_impossible_temperature_does_not_count_toward_complete_day(monkeypatch, points):
    temperature = hourly(points, False)
    temperature.loc[temperature.fhr == 20, "value"] = -300.
    _, result = cached_context(monkeypatch, points, temperature=temperature)
    tomorrow = result[result.valid_date == DAY + timedelta(days=1)]
    assert tomorrow.temperature_hours.tolist() == [23, 23]
    assert tomorrow.temperature_max_c.isna().all()


def test_ozone_cannot_extend_beyond_product_horizon(points):
    frame = hourly(points)
    frame["step"] += 72
    frame["valid_utc"] += pd.Timedelta(hours=72)
    with pytest.raises(ValueError, match="issue cycle"):
        context._daily_values(frame, points, DAY, 12, True)


def test_context_download_route_is_explicit_and_uses_configured_cycles(monkeypatch, points):
    from serein import cli

    study = SimpleNamespace(name="synthetic", raw={
        "availability": {"aqm_cycle": 6, "hrrr_cycle": 12}, "hrrr": {"max_fhr": 48}})
    monkeypatch.setattr(cli, "load_study", lambda config: study)
    monkeypatch.setattr(cli, "_days", lambda args: [DAY])
    monkeypatch.setattr("serein.data.points.load_points", lambda name: points)
    def run(fn, days, *args):
        for day in days:
            fn(day)
        return len(days), 0

    monkeypatch.setattr(cli, "_run_parallel", run)
    calls = []
    monkeypatch.setattr(aqm, "extract_cycle", lambda *args, **kwargs: calls.append(("aqm", kwargs)))
    monkeypatch.setattr(hrrr, "extract_temperature_cycle", lambda *args, **kwargs: calls.append(
        ("hrrr", kwargs)))
    cli.cmd_download(SimpleNamespace(source="context", config="synthetic", workers=4))
    assert calls == [
        ("aqm", {"cycle": 6, "store": "synthetic", "pollutant": "o3"}),
        ("hrrr", {"cycle": 12, "store": "synthetic", "max_fhr": 48}),
    ]


@pytest.mark.parametrize("failure", ["missing", "error"])
def test_context_download_failure_returns_nonzero(monkeypatch, points, failure):
    from serein import cli

    study = SimpleNamespace(name="synthetic", raw={"hrrr": {"max_fhr": 48}})
    monkeypatch.setattr(cli, "load_study", lambda config: study)
    monkeypatch.setattr(cli, "_days", lambda args: [DAY])
    monkeypatch.setattr("serein.data.points.load_points", lambda name: points)

    def unavailable(*args, **kwargs):
        if failure == "error":
            raise ValueError("Unsupported ozone units")

    monkeypatch.setattr(aqm, "extract_cycle", unavailable)
    monkeypatch.setattr(hrrr, "extract_temperature_cycle", lambda *args, **kwargs: points)
    with pytest.raises(SystemExit, match="Context download incomplete"):
        cli.cmd_download(SimpleNamespace(source="context", config="synthetic", workers=1))
