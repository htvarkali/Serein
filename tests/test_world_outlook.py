"""The map file's daily outlook: calibrated chance, warning and low-confidence flag.

These must match what the crew outlook and the backtest compute for the same forecast,
and must be left out entirely when the trained run's settings are missing, so the site
never shows a raw chance.
"""

import json
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from serein import crew, world

SAMPLE = Path(__file__).resolve().parents[1] / "app" / "sample" / "forecast_20230818.parquet"

# A recalibration map that pulls chances down in the middle, like the real one does.
RECAL = {str(L): {"x": [0.0, 0.4, 0.8, 1.0], "y": [0.0, 0.3, 0.7, 1.0]} for L in range(4)}
CUTOFFS = {str(L): 0.45 for L in range(4)}
FLAG = {"quantile": 0.9, "log_width": {str(L): 1.5 for L in range(4)}}


def _forecast():
    # Point A: clean air. B: likely smoky. C: wide range. D: missing quantiles.
    rows = []
    quantiles = {
        "A": (4, 6, 8, 10, 14),
        "B": (25, 34, 42, 52, 70),
        "C": (5, 15, 30, 60, 120),
        "D": (np.nan,) * 5,
    }
    for lead in range(2):
        for pid, q in quantiles.items():
            rows.append({"point_id": pid, "lead": lead, "issue_date": "2023-08-18",
                         "valid_date": pd.Timestamp("2023-08-18") + pd.Timedelta(days=lead),
                         **dict(zip(world.QUANTILE_COLUMNS, q, strict=True))})
    return pd.DataFrame(rows), list(quantiles)


def _settings(tmp_path, recal=RECAL, cutoffs=CUTOFFS, flag=FLAG):
    for name, value in (("prob_recal.json", recal), ("warn_cutoffs.json", cutoffs),
                        ("flag_width.json", flag)):
        if value is not None:
            (tmp_path / name).write_text(json.dumps(value))
    return world.run_settings(tmp_path)


def test_without_settings_only_the_median_and_range_are_written():
    fc, ids = _forecast()
    days = world.daily_outlooks(fc, ids, {})
    assert [d["lead"] for d in days] == [0, 1]
    assert days[1]["date"] == "2023-08-19"
    assert set(days[0]) == {"lead", "date", "q05", "q50", "q95"}
    assert days[0]["q50"][:3] == [8, 42, 30] and days[0]["q50"][3] is None


def test_chance_matches_the_crew_outlook_and_flags_match_the_backtest_rules(tmp_path):
    fc, ids = _forecast()
    days = world.daily_outlooks(fc, ids, _settings(tmp_path))
    for lead, day in enumerate(days):
        for i, pid in enumerate(ids[:3]):
            row = fc[(fc.point_id == pid) & (fc.lead == lead)]
            q = row[list(world.QUANTILE_COLUMNS)].to_numpy()[0]
            expected = crew.outlook(q, lead, recal=RECAL, flag_width=FLAG)
            assert day["p_usg"][i] == round(100 * expected.p_unhealthy_sensitive)
            assert day["low_conf"][i] == int(expected.low_confidence)
            raw = crew.chance_above(q, crew.UNHEALTHY_SENSITIVE)
            assert day["warn"][i] == int(raw >= CUTOFFS[str(lead)])
    # Clean air: a small chance (the rule puts 2.5% of the mass beyond the top of the
    # range) and no warning. Smoky: warned. Wide range: low confidence.
    assert days[1]["p_usg"][0] < 5 and days[1]["warn"][0] == 0
    assert days[1]["warn"][1] == 1 and days[1]["p_usg"][1] > 50
    assert days[1]["low_conf"][2] == 1 and days[1]["low_conf"][0] == 0


def test_missing_quantiles_give_no_chance_and_no_flags(tmp_path):
    fc, ids = _forecast()
    day = world.daily_outlooks(fc, ids, _settings(tmp_path))[0]
    assert day["p_usg"][3] is None and day["warn"][3] == 0 and day["low_conf"][3] == 0


def test_a_missing_settings_file_leaves_out_only_its_value(tmp_path):
    fc, ids = _forecast()
    days = world.daily_outlooks(fc, ids, _settings(tmp_path, recal=None))
    assert "p_usg" not in days[0]
    assert "warn" in days[0] and "low_conf" in days[0]
    assert world.run_settings(None) == {}
    assert world.run_settings(tmp_path / "nowhere") == {}


def test_daily_only_refreshes_an_existing_file_from_the_sample_forecast(tmp_path):
    fc = pd.read_parquet(SAMPLE)
    n = fc["point_id"].nunique()
    out = tmp_path / "aug2023.json"
    old = {"issue_date": "2023-08-18", "hours": 72, "points": [[0, 0, 0]] * n,
           "wind_hours": [], "fires": [], "daily": [], "noaa": [1, 2]}
    out.write_text(json.dumps(old))
    _settings(tmp_path)
    world.main(["--daily-only", "--forecast", str(SAMPLE), "--out", str(out),
                "--run-dir", str(tmp_path)])
    data = json.loads(out.read_text())
    assert data["noaa"] == [1, 2]  # everything else is kept
    assert [d["lead"] for d in data["daily"]] == [0, 1, 2, 3]
    for day in data["daily"]:
        assert len(day["p_usg"]) == len(day["warn"]) == len(day["low_conf"]) == n
        assert all(p is None or 0 <= p <= 100 for p in day["p_usg"])
    # The August 18, 2023 run had real smoke, so some places carry a warning.
    assert sum(data["daily"][1]["warn"]) > 0


def test_daily_only_refuses_a_different_forecast_run(tmp_path):
    out = tmp_path / "live.json"
    out.write_text(json.dumps({"issue_date": "2026-11-26", "points": [], "daily": []}))
    with pytest.raises(SystemExit, match="issued 2023-08-18"):
        world.main(["--daily-only", "--forecast", str(SAMPLE), "--out", str(out),
                    "--run-dir", str(tmp_path)])


def test_settings_come_from_the_run_named_in_the_forecast_record(tmp_path, monkeypatch):
    monkeypatch.setenv("SEREIN_LIVE_RUN", "west_us_dev")
    forecast = tmp_path / "20261127.parquet"
    # No record: the environment decides, as in scripts/run_live.sh.
    assert world.default_run_dir(forecast).name == "west_us_dev"
    # The record written by serein.live names the run that made the forecast.
    forecast.with_suffix(".json").write_text(json.dumps({"model_run": "west_us_live_v1"}))
    assert world.default_run_dir(forecast).name == "west_us_live_v1"
    # A broken or odd record falls back to the environment.
    for bad in ("not json", json.dumps({"model_run": "../elsewhere"}), json.dumps([1])):
        forecast.with_suffix(".json").write_text(bad)
        assert world.default_run_dir(forecast).name == "west_us_dev"
    monkeypatch.delenv("SEREIN_LIVE_RUN")
    assert world.default_run_dir(None).name == "west_us_dev"

