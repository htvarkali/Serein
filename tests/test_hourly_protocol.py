from datetime import date, datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from serein.eval import hourly
from serein.world import HOURS


def test_refuses_a_final_test_run(tmp_path, monkeypatch):
    run_dir = tmp_path / "west_us_test"
    run_dir.mkdir()
    (run_dir / "FINAL_RUN_LOCK.json").write_text("{}")
    monkeypatch.setattr(hourly, "run", lambda *a, **k: pytest.fail("scored a final-test run"))
    with pytest.raises(SystemExit, match="development data only"):
        hourly.main([str(run_dir), "--out", str(tmp_path / "out")])


@pytest.mark.parametrize(
    "name, years", [("west_us_dev", (2021, 2022)), ("west_us_dev_inner", (2021,))]
)
def test_daily_shapes_come_only_from_seasons_before_the_scored_one(
    tmp_path, monkeypatch, name, years
):
    seen = {}

    def fake_run(run_dir, max_days=None, profile_years=()):
        seen["years"] = tuple(profile_years)
        return pd.DataFrame()

    monkeypatch.setattr(hourly, "run", fake_run)
    monkeypatch.setattr(hourly, "summarize", lambda rows: pd.DataFrame({"lead": []}))
    (tmp_path / name).mkdir()
    hourly.main([str(tmp_path / name), "--out", str(tmp_path / "out")])
    assert seen["years"] == years


def test_observed_puts_each_reading_at_its_utc_hour(monkeypatch):
    start = datetime(2023, 8, 18, 19)
    asked = {}

    def fake_load(days):
        asked["days"] = days
        return pd.DataFrame(
            {
                "site_id": ["A", "B", "A", "C", "A", "B"],
                "time_utc": [
                    start,
                    start + timedelta(hours=5),
                    start + timedelta(hours=HOURS - 1),
                    start + timedelta(hours=3),
                    start + timedelta(hours=HOURS),
                    start - timedelta(hours=1),
                ],
                "pm25": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0],
            }
        )

    monkeypatch.setattr(hourly, "load_hourly", fake_load)
    out = hourly.observed(["A", "B"], start)
    assert asked["days"] == [date(2023, 8, 18) + timedelta(days=k) for k in range(4)]
    assert out[0, 0] == 1.0 and out[1, 5] == 2.0 and out[0, HOURS - 1] == 3.0
    assert np.isfinite(out).sum() == 3  # site C and the two hours outside the window are dropped


def test_diurnal_profiles_use_local_hours_in_the_fire_season(monkeypatch):
    rows = []

    def day(site, local_day, offset, value):
        for hour in range(24):
            local = datetime(local_day.year, local_day.month, local_day.day, hour)
            rows.append((site, local - timedelta(hours=offset), value(hour)))

    # Site A at UTC-8. Ratios to each day's mean: 1.5 / 0.5, then 0.5 / 1.5, then 2.0 / 0.67 split at 6 am.
    day("A", date(2021, 8, 1), -8, lambda h: 30.0 if h < 12 else 10.0)
    day("A", date(2021, 8, 2), -8, lambda h: 10.0 if h < 12 else 30.0)
    day("A", date(2021, 8, 3), -8, lambda h: 30.0 if h < 6 else 10.0)
    for d in (5, 6, 7):  # outside June to October: ignored
        day("A", date(2021, 11, d), -8, lambda h: 1.0 if h < 12 else 99.0)
    # Site B at UTC-7 has only 10 local hours, with a strong shape: under 20 hours it stays flat.
    for hour in range(10):
        rows.append(("B", datetime(2021, 8, 1, hour + 7), 10.0 if hour < 5 else 90.0))
    frame = pd.DataFrame(rows, columns=["site_id", "time_utc", "pm25"])
    monkeypatch.setattr(hourly, "load_hourly", lambda days: frame)
    prof = hourly.diurnal_profiles([2021], ["A", "B"], np.array([-8.0, -7.0]))
    median_ratio = np.array([1.5] * 6 + [2 / 3] * 18)  # per local hour, over the three August days
    assert np.allclose(prof[0], median_ratio / median_ratio.mean())
    assert np.allclose(prof[1], 1.0)
