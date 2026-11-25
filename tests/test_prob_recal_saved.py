"""The crew outlook's chances match what the backtest scored for the same forecast."""

import json
from datetime import date, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd

from serein import crew
from serein.config import Study
from serein.eval import backtest
from serein.models import infer


def _smoky_table(start, n_days, points):
    # Swings from about 5 to 51 µg/m³, so calibration and test both have days at 35.5 or more.
    # One monitor also gets smoke the inputs do not show once a week, so the fitted map does
    # not start at exactly 0.
    rows = []
    for offset in range(n_days):
        for site, point in points.iterrows():
            pm = 25 + 20 * np.sin(offset / 2) + site * 3
            surprise = 40.0 if site == 0 and offset % 7 == 3 else 0.0
            rows.append(
                {
                    "issue_date": start + timedelta(days=offset),
                    "point_id": point.point_id,
                    "kind": "epa",
                    "lat": point.lat,
                    "lon": point.lon,
                    "hms_prev": 3.0 if pm > 30 else 0.0,
                    "obs_last3": pm,
                    "obs_last24": pm - 1,
                    "obs_prevday": pm - 2,
                    "hrrr_u10_L0": 2.0,
                    "hrrr_v10_L0": 0.0,
                    **{f"aqm_mean_L{lead}": pm + lead + 4 for lead in (0, 1)},
                    **{f"y_L{lead}": pm + lead + surprise for lead in (0, 1)},
                }
            )
    return pd.DataFrame(rows)


def test_saved_recalibration_and_live_quantiles_give_the_scored_chances(tmp_path, monkeypatch):
    points = pd.DataFrame(
        {
            "point_id": ["A", "B", "C"],
            "kind": "epa",
            "lat": [38.0, 38.1, 38.2],
            "lon": [-121.0, -121.1, -121.2],
        }
    )
    train = _smoky_table(date(2021, 7, 1), 12, points)
    calibrate = _smoky_table(date(2023, 7, 1), 28, points)
    cache = tmp_path / "processed"
    cache.mkdir()
    train.to_parquet(cache / "table_train.parquet", index=False)
    calibrate.to_parquet(cache / "table_calibrate.parquet", index=False)
    monkeypatch.setattr(backtest, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(backtest, "processed_dir", lambda study: cache)
    monkeypatch.setattr(backtest, "load_points", lambda name: points.copy())
    monkeypatch.setattr(backtest, "load_forecasts", lambda days: pd.DataFrame())
    study = Study(
        {"name": "synthetic_recal", "leads": [0, 1], "graph": {"k_neighbors": 2, "max_km": 300}}
    )
    args = SimpleNamespace(
        final=False,
        tag="smoke",
        train="train",
        calibrate="calibrate",
        test="test",
        seed=4,
        seeds=2,
        epochs=3,
        hidden=16,
        layers=1,
        dropout=0.0,
        smoke_weight=1.0,
        no_gbm=True,
        no_ablation=True,
    )

    backtest.run_backtest(study, args)

    run = tmp_path / "outputs" / "backtest" / "synthetic_recal_smoke"
    recal = json.loads((run / "prob_recal.json").read_text())
    assert set(recal) == {"0", "1"}
    scored = pd.read_parquet(run / "predictions.parquet")
    moved = 0.0
    for lead in study.leads:
        raw = scored[f"smokecast_prob_L{lead}"].to_numpy()
        cal = scored[f"smokecast_probcal_L{lead}"].to_numpy()
        ok = np.isfinite(raw)
        assert ok.sum() > 10
        np.testing.assert_array_equal(np.isfinite(cal), ok)
        # What the crew tab does with the saved file equals what the backtest scored.
        again = np.array([crew.recalibrate(p, recal, lead) for p in raw[ok]])
        np.testing.assert_allclose(again, cal[ok], rtol=0, atol=1e-12)
        moved = max(moved, float(np.abs(cal[ok] - raw[ok]).max()))
        # The backtest's map clips outside the range it was fitted on (out_of_bounds="clip").
        x, y = recal[str(lead)]["x"], recal[str(lead)]["y"]
        assert crew.recalibrate(x[0] - 0.01, recal, lead) == y[0]
        assert crew.recalibrate(x[-1] + 0.01, recal, lead) == y[-1]
    assert moved > 0.05, "the fitted maps left every chance unchanged, so nothing was checked"

    # The live forecast file's quantiles give the crew tab the same raw chance the backtest scored.
    test = calibrate[backtest._week_parity(calibrate) == 1].reset_index(drop=True)
    monkeypatch.setattr(infer, "load_points", lambda name: points.copy())
    checked = 0
    for day in sorted(test.issue_date.unique()):
        day_table = test[test.issue_date == day].reset_index(drop=True)
        monkeypatch.setattr(infer, "build_table", lambda *a, table=day_table, **k: table.copy())
        forecast = infer.forecast_day(study, day, run, with_grid=False)
        same_day = scored[scored.issue_date == day].set_index("point_id")
        for _, row in forecast.iterrows():
            q = row[list(crew.QUANTILE_COLUMNS)].to_numpy(dtype=float)
            expected = same_day.loc[row.point_id, f"smokecast_prob_L{row.lead}"]
            assert abs(crew.chance_above(q, crew.UNHEALTHY_SENSITIVE) - expected) < 1e-4
            checked += 1
    assert checked == len(test) * len(study.leads)
