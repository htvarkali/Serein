"""Optional pollen answers stay distinct through check-in, CSV and model preparation."""

import csv
from datetime import date, timedelta

import numpy as np
import pandas as pd
import pytest

from serein.personal.log import CheckIn, model_rows, save_local, to_frame
from serein.personal.model import FEATURES, design_row


@pytest.mark.parametrize("legacy_numeric", [False, True])
def test_pollen_csv_round_trip_preserves_answers_and_confounders(tmp_path, legacy_numeric):
    start = date(2023, 7, 3)
    entries = [
        CheckIn(start + timedelta(days=i), 0, 0, False, 1, False, False, answer)
        for i, answer in enumerate((True, False, None))
    ]
    log = to_frame(entries)
    if legacy_numeric:
        log["high_pollen"] = [1.0, 0.0, np.nan]
    log["ozone_ppb"], log["hot_day"] = 80.0, 1
    original = log.copy(deep=True)
    path = tmp_path / "log.csv"
    save_local(log, path)
    with path.open(newline="") as stream:
        stored = [row["high_pollen"] for row in csv.DictReader(stream)]
    assert stored == (["1.0", "0.0", ""] if legacy_numeric else ["True", "False", ""])
    loaded = pd.read_csv(path)
    assert loaded.high_pollen.iloc[:2].tolist() == [True, False]
    assert pd.isna(loaded.high_pollen.iloc[2])

    pm = {start + timedelta(days=i): 10.0 for i in range(-2, 3)}
    expected = np.array([
        design_row(10, 10, 10, 0.3, 0, 0, ozone_ppb=80, hot_day=1, high_pollen=pollen)
        for pollen in (1, 0, 0)
    ])
    for frame in (log, loaded):
        before = frame.copy(deep=True)
        X, y = model_rows(frame, pm)
        np.testing.assert_array_equal(X, expected)
        np.testing.assert_array_equal(y, [0, 0, 0])
        pd.testing.assert_frame_equal(frame, before)
    pd.testing.assert_frame_equal(log, original)


@pytest.mark.parametrize("unknown", [None, np.nan, pd.NA])
def test_unknown_pollen_matches_old_logs_without_losing_the_unknown(unknown):
    day = date(2023, 7, 3)
    # Existing callers can still construct a check-in with the original seven fields.
    log = to_frame([CheckIn(day, 1, 0, False, 1, False, False)])
    assert log.high_pollen.iloc[0] is None
    log["high_pollen"] = pd.Series([unknown], dtype=object)
    pm = {day - timedelta(days=i): 10.0 for i in range(3)}
    expected = model_rows(log.drop(columns="high_pollen"), pm)
    actual = model_rows(log, pm)
    for before, after in zip(expected, actual, strict=True):
        np.testing.assert_array_equal(before, after)
    assert pd.isna(log.high_pollen.iloc[0])


@pytest.mark.parametrize("invalid", ["False", "True", "", 0, 1, np.nan, pd.NA])
def test_checkin_pollen_rejects_ambiguous_answers(invalid):
    with pytest.raises(ValueError, match="high_pollen"):
        CheckIn(date(2023, 7, 3), 0, 0, False, 1, False, False, invalid)


@pytest.mark.parametrize("answer", [np.bool_(True), np.bool_(False)])
def test_checkin_accepts_numpy_boolean_pollen(answer):
    checkin = CheckIn(date(2023, 7, 3), 0, 0, False, 1, False, False, answer)
    assert checkin.high_pollen == answer


def test_empty_log_has_pollen_column_and_valid_empty_model_rows():
    log = to_frame([])
    assert "high_pollen" in log.columns
    X, y = model_rows(log, {})
    assert X.shape == (0, len(FEATURES)) and y.shape == (0,)


def test_pollen_ui_saves_distinct_answers_and_defaults_to_unknown(tmp_path, monkeypatch):
    pytest.importorskip("streamlit")
    pytest.importorskip("streamlit_folium")
    from pathlib import Path

    from streamlit.testing.v1 import AppTest

    from serein import config

    monkeypatch.setattr(config, "REPO_ROOT", tmp_path)
    maps = tmp_path / "outputs/maps"
    maps.mkdir(parents=True)
    pd.DataFrame([{
        "lead": 0, "valid_date": date(2023, 8, 18), "point_id": "fictional", "kind": "epa",
        "lat": 38.58, "lon": -121.49, "q05": 5., "q25": 10., "q50": 20.,
        "q75": 30., "q95": 40., "aqi_cat": 1, "obs": 18.,
    }]).to_parquet(maps / "forecast_20230818.parquet", index=False)
    app = AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app/streamlit_app.py"),
        default_timeout=30,
    ).run()
    assert not app.exception
    assert app.radio(key="checkin_pollen").value == "Not sure"
    for offset, (choice, expected) in enumerate((("Not sure", None), ("Yes", True), ("No", False))):
        app.date_input[0].set_value(date(2023, 7, 3) + timedelta(days=offset))
        app.radio(key="checkin_pollen").set_value(choice)
        next(button for button in app.button if button.label == "Save today").click().run()
        assert not app.exception
        assert app.session_state["log"][-1].high_pollen is expected
    saved = app.dataframe[0].value
    assert pd.isna(saved.high_pollen.iloc[0])
    assert saved.high_pollen.iloc[1:].tolist() == [True, False]
    assert any(item.proto.label == "Download my log (CSV)" for item in app.get("download_button"))
