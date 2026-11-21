"""Memory of past days (B-18), live-forecast helpers (D-11), partial AirNow days."""

import json
from datetime import UTC, date, datetime, timedelta
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest
import torch

from serein.features.graph import build_knn_graph
from serein.features.prepare import GraphData, history_from
from serein.models.conformal import CQR
from serein.models.gnn import SmokeCastGNN
from serein.models.train import TrainConfig, Trainer


def _gd(days, n=3, f=4):
    X = np.arange(len(days) * n * f, dtype=np.float32).reshape(len(days), n, f)
    names = ["obs_last1", "obs_last1__missing", "aqm_mean_L0", "lat"]
    return GraphData(days, [f"s{i}" for i in range(n)], X, np.zeros((len(days), n, 1)),
                     np.zeros((len(days), n, 1)), np.zeros((len(days), n, 2)), names,
                     np.zeros((len(days), n), np.int64))


def test_history_takes_previous_days_oldest_first_and_marks_gaps_missing():
    d0 = date(2023, 6, 1)
    days = [d0 + timedelta(days=k) for k in (0, 1, 2, 4)]  # day 3 is absent
    full = _gd(days)
    h = history_from(full, [days[2], days[3]], k=3)
    assert h.shape == (2, 3, 2, 4)
    np.testing.assert_array_equal(h[0, :, 0], full.X[0])  # 2 days before June 3
    np.testing.assert_array_equal(h[0, :, 1], full.X[1])  # 1 day before
    # June 5: June 3 exists, June 4 does not -> all-missing row (flag 1, values 0).
    np.testing.assert_array_equal(h[1, :, 0], full.X[2])
    np.testing.assert_array_equal(h[1, :, 1], np.tile([0, 1, 0, 0], (3, 1)))


def test_history_model_uses_past_days():
    torch.manual_seed(0)
    m = SmokeCastGNN(n_feat=4, n_leads=2, hidden=16, layers=1, history=3, drop=0.0).eval()
    g = build_knn_graph(np.array([37.0, 37.1, 37.2]), np.array([-122.0, -122.1, -122.2]), k=2)
    a = lambda v: torch.as_tensor(v)
    x, w, b = torch.randn(1, 3, 4), torch.zeros(1, 3, 2), torch.zeros(1, 3, 2)
    xh = torch.randn(1, 3, 2, 4)
    args = (a(g.src), a(g.dst), a(g.bearing).float(), a(g.edge_attr))
    q1 = m(x, w, b, *args, xh)
    q2 = m(x, w, b, *args, xh + 1.0)
    assert q1.shape == (1, 3, 2, 5)
    assert not torch.allclose(q1, q2)  # changing yesterday changes today's forecast


def test_node_masking_also_hides_past_readings():
    g = build_knn_graph(np.array([37.0, 37.1]), np.array([-122.0, -122.1]), k=1)
    names = ["obs_last1", "obs_last1__missing", "aqm_mean_L0"]
    cfg = TrainConfig(node_mask_frac=1.0, history=3, hidden=8, layers=1, deterministic=False)
    tr = Trainer(3, 1, g, names, cfg)
    x = torch.ones(1, 2, 3)
    xh = torch.ones(1, 2, 2, 3)
    x2, _, xh2 = tr._mask_nodes(x, None, None, xh)
    assert torch.all(x2[..., 0] == 0) and torch.all(x2[..., 1] == 1) and torch.all(x2[..., 2] == 1)
    assert torch.all(xh2[..., 0] == 0) and torch.all(xh2[..., 1] == 1) and torch.all(xh2[..., 2] == 1)


def test_warn_cutoffs_read_from_old_report(tmp_path):
    from serein.live import warn_cutoffs

    (tmp_path / "report.md").write_text(
        "x\nwarning cut-offs P(>=35.5) tuned on calibration: {0: 0.575, 1: 0.5250000000000001}\n",
        encoding="utf-8")
    assert warn_cutoffs(tmp_path) == {0: 0.575, 1: 0.5250000000000001}
    (tmp_path / "warn_cutoffs.json").write_text('{"0": 0.3}')
    assert warn_cutoffs(tmp_path) == {0: 0.3}  # the saved file wins


def test_live_scoreboard_counts_hits_and_false_alarms():
    from serein.live import summarize

    s = pd.DataFrame({
        "lead": [1, 1, 1, 1], "issue_date": [date(2026, 11, 3)] * 4,
        "obs": [40.0, 50.0, 10.0, 8.0], "smokecast": [38.0, 20.0, 12.0, 9.0],
        "noaa_best": [20.0, 20.0, 40.0, 9.0], "aqm_bc": [20.0, 20.0, 40.0, 9.0],
        "persistence": [30.0, 30.0, 10.0, 8.0], "warn": [True, False, True, False]})
    r = summarize(s).iloc[0]
    assert (r.usg_days, r.usg_caught, r.false_alarms) == (2, 1, 1)
    assert (r.noaa_caught, r.noaa_false_alarms) == (0, 1)
    assert r.rmse_smokecast < r.rmse_noaa_best and r.skill_vs_noaa > 0


def test_live_scoreboard_compares_with_noaa_on_the_same_monitor_days():
    from serein.live import summarize

    nan = float("nan")
    s = pd.DataFrame({
        "lead": [3, 3, 3, 3], "issue_date": [date(2026, 11, 3)] * 4,
        "obs": [50.0, 40.0, 10.0, 8.0], "smokecast": [40.0, 38.0, 12.0, 9.0],
        "noaa_best": [nan, 36.0, 40.0, 9.0], "aqm_bc": [nan] * 4,
        "persistence": [nan, 36.0, 40.0, 9.0], "warn": [True, True, False, False]})
    r = summarize(s).iloc[0]
    # The first day had no NOAA forecast, so it is left out instead of counted as a NOAA miss.
    assert (r.monitor_days, r.no_noaa_days) == (3, 1)
    assert (r.usg_days, r.usg_caught, r.noaa_caught) == (1, 1, 1)
    assert r.skill_vs_noaa == pytest.approx(1 - r.rmse_smokecast / r.rmse_noaa_best)



def test_live_scoreboard_pairs_aqm_and_persistence_with_smokecast_on_shared_days(
        tmp_path, monkeypatch):
    from serein import live

    nan = float("nan")
    # AQM is missing on the hardest monitor-day and yesterday's value on another.
    s = pd.DataFrame({
        "lead": 1, "issue_date": date(2026, 11, 3), "valid_date": date(2026, 11, 4),
        "obs": [50.0, 40.0, 10.0, 8.0], "smokecast": [30.0, 38.0, 12.0, 9.0],
        "noaa_best": [45.0, 30.0, 14.0, 9.0], "aqm_bc": [nan, 30.0, 14.0, 9.0],
        "persistence": [48.0, nan, 10.0, 8.0], "warn": False})
    r = live.summarize(s).iloc[0]
    # On its own days AQM's RMSE (6.2) is below SmokeCast's over all days (10.1), but on
    # the days AQM forecast, SmokeCast's RMSE is 1.7.
    assert r.monitor_days_vs_aqm_bc == 3
    assert r.rmse_aqm_bc == pytest.approx(np.sqrt(39))
    assert r.rmse_smokecast_vs_aqm_bc == pytest.approx(np.sqrt(3))
    assert r.skill_vs_aqm_bc == pytest.approx(1 - np.sqrt(3) / np.sqrt(39))
    assert r.monitor_days_vs_persistence == 3
    assert r.rmse_persistence == pytest.approx(np.sqrt(4 / 3))
    assert r.rmse_smokecast_vs_persistence == pytest.approx(np.sqrt(135))

    monkeypatch.setattr(live, "LIVE", tmp_path)
    (tmp_path / "test").mkdir()
    live._write_board(SimpleNamespace(name="test"), s, pd.DataFrame(), 1)
    text = (tmp_path / "test" / "SCOREBOARD.md").read_text(encoding="utf-8")
    assert "| 1 | NOAA AQM | 3 | 1.73 | 6.24 | +72% |" in text
    assert "| 1 | yesterday's value | 3 | 11.62 | 1.15 | -906% |" in text
    # The main table no longer puts AQM's own-days RMSE beside SmokeCast's all-days RMSE.
    assert "6.24 | 1.15" not in text and "NOAA AQM | yesterday's value | skill" not in text


def test_live_scoreboard_reports_the_day_bootstrap_interval_vs_noaa():
    from serein.live import summarize

    rng = np.random.default_rng(0)
    days = [date(2026, 11, 3) + timedelta(days=k) for k in range(6)]
    obs = rng.uniform(5, 60, 6 * 4)
    s = pd.DataFrame({
        "lead": 1, "issue_date": np.repeat(days, 4), "obs": obs,
        "smokecast": obs + rng.normal(0, 2, obs.size),
        "noaa_best": obs + rng.normal(0, 10, obs.size), "aqm_bc": np.nan,
        "persistence": np.nan, "warn": False})
    r = summarize(s).iloc[0]
    diff = r.rmse_smokecast - r.rmse_noaa_best
    assert r.ci_lo_vs_noaa <= diff <= r.ci_hi_vs_noaa < 0
    # Fewer than 5 issue days is too few to resample, so no interval is shown.
    r4 = summarize(s[s["issue_date"] < days[4]]).iloc[0]
    assert r4.issue_days == 4 and np.isnan(r4.ci_lo_vs_noaa) and np.isnan(r4.ci_hi_vs_noaa)


def test_live_scoreboard_reports_fire_season_and_off_season_apart(tmp_path, monkeypatch):
    from serein import live

    monkeypatch.setattr(live, "LIVE", tmp_path)
    (tmp_path / "test").mkdir()
    study = SimpleNamespace(name="test")
    s = pd.DataFrame({
        "lead": 1, "issue_date": [date(2027, 7, 1), date(2027, 7, 1), date(2026, 11, 3)],
        "valid_date": [date(2027, 7, 2), date(2027, 7, 2), date(2026, 11, 4)],
        "obs": [40.0, 20.0, 8.0], "smokecast": [38.0, 21.0, 9.0],
        "noaa_best": [30.0, 25.0, 12.0], "aqm_bc": np.nan, "persistence": np.nan,
        "warn": [True, False, False]})
    live._write_board(study, s, pd.DataFrame(), 2)
    board = pd.read_csv(tmp_path / "test" / "scoreboard.csv")
    assert board.columns[0] == "season"
    assert board.set_index("season")["monitor_days"].to_dict() == {"fire": 2, "off": 1}
    text = (tmp_path / "test" / "SCOREBOARD.md").read_text(encoding="utf-8")
    assert text.index("## Fire season") < text.index("## Off-season")

    live._write_board(study, s.iloc[2:], pd.DataFrame(), 1)
    text = (tmp_path / "test" / "SCOREBOARD.md").read_text(encoding="utf-8")
    assert "## Off-season" in text and "## Fire season" not in text


def test_model_fingerprint_changes_when_the_run_is_retrained_in_place(tmp_path):
    from serein.live import model_fingerprint

    for name in ("model.json", "smokecast.pt", "artifacts.pkl"):
        (tmp_path / name).write_bytes(name.encode())
    (tmp_path / "warn_cutoffs.json").write_text('{"0": 0.5}')
    first = model_fingerprint(tmp_path)
    assert model_fingerprint(tmp_path) == first
    (tmp_path / "smokecast.pt").write_bytes(b"retrained weights")
    second = model_fingerprint(tmp_path)
    assert second != first
    (tmp_path / "warn_cutoffs.json").write_text('{"0": 0.6}')
    assert model_fingerprint(tmp_path) not in (first, second)


def test_partial_airnow_day_is_read_but_not_frozen(tmp_path, monkeypatch):
    from serein.data import airnow

    monkeypatch.setenv("SEREIN_DATA", str(tmp_path))
    d = date.today()
    row = pd.DataFrame({"site_id": ["A"], "time_utc": [pd.Timestamp(d)], "pm25": [5.0]})
    hourly = tmp_path / "raw" / "airnow" / "hourly"
    hourly.mkdir(parents=True)
    row.to_parquet(hourly / f"{d:%Y%m%d}.partial.parquet")
    got = airnow.load_hourly([d])
    assert len(got) == 1  # live forecasts see today's hours so far
    assert not (hourly / f"{d:%Y%m%d}.parquet").exists()  # a later run re-downloads


@pytest.mark.parametrize(("start_hour", "made_hour", "force", "on_time"), [
    (18, 18, True, False),
    (19, 20, False, True),
    (19, 25, False, False),
])
def test_live_forecast_exports_calibrated_bounds_and_checks_completion_time(
    tmp_path, monkeypatch, start_hour, made_hour, force, on_time,
):
    from serein import live

    day = date(2026, 11, 3)
    utc_midnight = datetime(2026, 11, 3, tzinfo=UTC)
    made_at = utc_midnight + timedelta(hours=made_hour)
    clock = iter([utc_midnight + timedelta(hours=start_hour), made_at])
    monkeypatch.setattr(live, "datetime", SimpleNamespace(now=lambda tz: next(clock)))
    monkeypatch.setattr(live, "LIVE", tmp_path)
    monkeypatch.setattr(live, "fetch_inputs", lambda *args: {"aqm": True, "hrrr": True})
    monkeypatch.setattr(live, "plot_map", lambda *args, **kwargs: None)
    monkeypatch.setattr(live, "_git_rev", lambda: "test")
    monkeypatch.setattr(live, "warn_cutoffs", lambda run_dir: {0: 0.5})
    monkeypatch.setattr(live, "model_fingerprint", lambda run_dir: "test-model")
    tab = pd.DataFrame({"point_id": ["A", "B"], "lat": [37., 38.], "lon": [-122., -121.],
                        "kind": ["epa", "epa"]})
    # The first forecast's median is negative. The second interval is shrunk past q25/q75.
    quantiles = torch.tensor([[[[-1., -.4, -.1, .1, .5]], [[.1, .2, 1., 1.8, 2.]]]])
    inputs = SimpleNamespace(run=lambda: quantiles, tab=tab, use=tab, leads=[0], prep=None,
                             cqr=CQR(qhat={(0, -1): -0.5}))
    monkeypatch.setattr(live, "build_inputs", lambda *args, **kwargs: inputs)
    monkeypatch.setattr(live, "baselines", lambda *args: {})
    study = SimpleNamespace(name="test", raw={"issue_hour_utc": 18.5})

    forecast = live.make_forecast(study, day, force=force)

    out = tmp_path / "test" / "forecasts" / "20261103.parquet"
    pd.testing.assert_frame_equal(pd.read_parquet(out), forecast)
    values = forecast[["q05", "q25", "q50", "q75", "q95"]].to_numpy()
    assert (values >= 0).all()
    assert (np.diff(values, axis=1) >= 0).all()
    assert forecast["on_time"].tolist() == [on_time, on_time]
    metadata = json.loads(out.with_suffix(".json").read_text())
    assert metadata["made_at_utc"] == made_at.isoformat(timespec="seconds")
    assert metadata["on_time"] is on_time


def test_forced_live_rerun_keeps_the_first_forecast_and_scores_only_it(tmp_path, monkeypatch):
    from serein import live

    day = date(2026, 11, 3)
    clock = [datetime(2026, 11, 3, 19, tzinfo=UTC)]
    monkeypatch.setattr(live, "datetime", SimpleNamespace(now=lambda tz=None: clock[0]))
    monkeypatch.setattr(live, "LIVE", tmp_path)
    monkeypatch.setattr(live, "fetch_inputs", lambda *args: {"aqm": True, "hrrr": True})
    monkeypatch.setattr(live, "plot_map", lambda *args, **kwargs: None)
    monkeypatch.setattr(live, "_git_rev", lambda: "test")
    monkeypatch.setattr(live, "warn_cutoffs", lambda run_dir: {0: 0.5})
    monkeypatch.setattr(live, "model_fingerprint", lambda run_dir: "test-model")
    tab = pd.DataFrame({"point_id": ["A", "B"], "lat": [37., 38.], "lon": [-122., -121.],
                        "kind": ["epa", "epa"]})
    runs = [torch.tensor([[[[1., 2., 3., 4., 5.]], [[1., 2., 3., 4., 5.]]]]),
            torch.tensor([[[[0., .5, 1., 1.5, 2.]], [[0., .5, 1., 1.5, 2.]]]])]

    def inputs(*args, **kwargs):
        q = runs.pop(0)
        return SimpleNamespace(run=lambda: q, tab=tab, use=tab, leads=[0], prep=None,
                               cqr=CQR(qhat={}))

    monkeypatch.setattr(live, "build_inputs", inputs)
    monkeypatch.setattr(live, "baselines", lambda *args: {
        m: np.array([[5.], [6.]]) for m in ("noaa_best", "aqm_bc", "persistence")})
    study = SimpleNamespace(name="test", raw={"issue_hour_utc": 18.5})

    first = live.make_forecast(study, day)
    assert live.make_forecast(study, day) is None
    clock[0] = datetime(2026, 11, 3, 20, tzinfo=UTC)  # still inside the on-time window
    rerun = live.make_forecast(study, day, force=True)

    saved = tmp_path / "test" / "forecasts"
    pd.testing.assert_frame_equal(pd.read_parquet(saved / "20261103.parquet"), first)
    pd.testing.assert_frame_equal(pd.read_parquet(saved / "20261103.v2.parquet"), rerun)
    assert set(first["model_sha256"]) == {"test-model"}
    assert json.loads((saved / "20261103.json").read_text())["model_sha256"] == "test-model"
    assert rerun["on_time"].all() and not rerun["smokecast"].equals(first["smokecast"])
    hashes = (tmp_path / "test" / "forecast_hashes.txt").read_text().splitlines()
    assert [h.split()[-1] for h in hashes] == ["20261103.parquet", "20261103.v2.parquet"]

    monkeypatch.setattr(live, "load_points", lambda name: pd.DataFrame({"point_id": ["A", "B"]}))
    monkeypatch.setattr(live, "_observed", lambda *args: pd.DataFrame(
        {"point_id": ["A", "B"], "valid_date": [day, day], "obs": [10., 20.]}))
    monkeypatch.setattr(live.airnow, "download_reportingarea_day", lambda *args, **kwargs: None)
    monkeypatch.setattr(live, "compare_with_epa", lambda *args: pd.DataFrame())
    clock[0] = datetime(2026, 11, 6, tzinfo=UTC)
    scored = live.score(study)
    assert scored["smokecast"].tolist() == first["smokecast"].tolist()


def test_live_score_compares_with_the_official_epa_forecast(tmp_path, monkeypatch):
    from serein import live
    from serein.config import Region
    from serein.eval import backtest

    issued, valid = date(2026, 11, 3), date(2026, 11, 4)
    areas = {"reporting_area": ["Sacramento", "Eugene"], "state": ["CA", "OR"]}
    monkeypatch.setattr(live, "LIVE", tmp_path)
    monkeypatch.setattr(live, "datetime",
                        SimpleNamespace(now=lambda tz=None: datetime(2026, 11, 7, tzinfo=UTC)))
    saved = tmp_path / "test" / "forecasts"
    saved.mkdir(parents=True)
    pd.DataFrame({
        "issue_date": issued, "valid_date": valid, "lead": 1, "point_id": ["A", "B"],
        "kind": "epa", "on_time": True, "smokecast": [40.0, 6.0], "warn": [True, False],
        "noaa_best": [20.0, 6.0], "aqm_bc": [20.0, 6.0], "persistence": [10.0, 6.0],
    }).to_parquet(saved / "20261103.parquet", index=False)
    monkeypatch.setattr(live, "load_points",
                        lambda name: pd.DataFrame({"point_id": ["A", "B"], **areas}))
    monkeypatch.setattr(live, "_observed", lambda *args: pd.DataFrame(
        {"point_id": ["A", "B"], "valid_date": valid, "obs": [45.0, 5.0]}))
    monkeypatch.setattr(live.airnow, "download_reportingarea_day", lambda *args, **kwargs: None)
    # EPA forecast Moderate for Sacramento, and the observed day was orange (USG).
    monkeypatch.setattr(backtest, "load_forecasts", lambda days: pd.DataFrame({
        "as_of": issued, "valid_date": valid, "lead": 1, "issue_date": issued, **areas,
        "lat": [38.6, 44.1], "lon": [-121.5, -123.1], "category_idx": [1.0, 0.0]}))
    monkeypatch.setattr(backtest, "load_observed_area_aqi", lambda days: pd.DataFrame(
        {"valid_date": valid, **areas, "category_idx": [2.0, 0.0]}))
    real_board, boards = live._write_board, []
    monkeypatch.setattr(live, "_write_board",
                        lambda *args: (boards.append(args[2]), real_board(*args)))
    study = SimpleNamespace(
        name="test", region=Region(lat_min=30, lat_max=50, lon_min=-125, lon_max=-110))
    logs = []

    live.score(study, log=logs.append)

    assert not [line for line in logs if "EPA comparison skipped" in line]
    epa = boards[0].set_index("who")
    assert epa.loc["smokecast", "n_area_days"] == 2
    assert (epa.loc["smokecast", "usg_pod"], epa.loc["epa_forecast", "usg_pod"]) == (1, 0)
    text = (tmp_path / "test" / "SCOREBOARD.md").read_text(encoding="utf-8")
    assert "Official EPA AQI forecasts" in text


def test_live_epa_comparison_is_split_by_the_day_forecast(tmp_path, monkeypatch):
    from serein import live

    # Issued Oct 31: today is fire season, tomorrow (Nov 1) is off-season.
    fc = pd.DataFrame({"issue_date": date(2026, 10, 31), "point_id": ["A", "A", "B", "B"],
                       "lead": [0, 1, 0, 1], "smokecast": [40.0, 41.0, 6.0, 7.0],
                       "warn": [True, True, False, False]})
    wide = fc.pivot_table(index=["issue_date", "point_id"], columns="lead",
                          values=["smokecast", "warn"], aggfunc="first").reset_index()
    calls = {}

    def fake_compare(study, test, pm, leads, pts, warn):
        season = "fire" if np.isfinite(pm[:, 0]).all() else "off"
        calls[season] = (pm, warn)
        return pd.DataFrame({"lead": leads, "who": "smokecast", "n_area_days": 1})

    monkeypatch.setattr(live, "compare_with_epa", fake_compare)
    epa = live._epa_by_season(None, wide, [0, 1], None)

    assert np.isnan(calls["fire"][0][:, 1]).all() and not calls["fire"][1][:, 1].any()
    assert np.isnan(calls["off"][0][:, 0]).all() and np.isfinite(calls["off"][0][:, 1]).all()
    assert calls["off"][1][:, 1].tolist() == [True, False]
    assert sorted(epa["season"].unique()) == ["fire", "off"]

    monkeypatch.setattr(live, "LIVE", tmp_path)
    (tmp_path / "test").mkdir()
    s = pd.DataFrame({
        "lead": [0, 1], "issue_date": date(2026, 10, 31),
        "valid_date": [date(2026, 10, 31), date(2026, 11, 1)], "obs": [40.0, 8.0],
        "smokecast": [38.0, 9.0], "noaa_best": [30.0, 12.0], "aqm_bc": np.nan,
        "persistence": np.nan, "warn": [True, False]})
    live._write_board(SimpleNamespace(name="test"), s, epa, 1)
    text = (tmp_path / "test" / "SCOREBOARD.md").read_text(encoding="utf-8")
    fire, off = text.index("## Fire season"), text.index("## Off-season")
    epa_tables = [i for i in range(len(text)) if text.startswith("Official EPA", i)]
    assert len(epa_tables) == 2 and fire < epa_tables[0] < off < epa_tables[1]
    assert "both seasons together" not in text


def test_live_score_downloads_the_epa_files_each_lead_needs(tmp_path, monkeypatch):
    from serein import live

    # The observed area AQI for day v is in the file for v + 1, so a lead-2 forecast
    # issued Nov 3 needs the Nov 6 file even when no forecast was issued Nov 4 or 5.
    # The Oct 22 file is both an old observation file and an issue-day file.
    rows = [(date(2026, 10, 20), 1), (date(2026, 10, 22), 1), (date(2026, 11, 3), 1),
            (date(2026, 11, 3), 2)]
    fc = pd.DataFrame({
        "issue_date": [d for d, _ in rows], "lead": [lead for _, lead in rows],
        "valid_date": [d + timedelta(days=lead) for d, lead in rows], "point_id": "A",
        "kind": "epa", "on_time": True, "smokecast": 10.0, "warn": False,
        "noaa_best": 10.0, "aqm_bc": 10.0, "persistence": 10.0})
    monkeypatch.setattr(live, "LIVE", tmp_path)
    monkeypatch.setattr(live, "datetime",
                        SimpleNamespace(now=lambda tz=None: datetime(2026, 11, 7, tzinfo=UTC)))
    saved = tmp_path / "test" / "forecasts"
    saved.mkdir(parents=True)
    fc.to_parquet(saved / "20261103.parquet", index=False)
    monkeypatch.setattr(live, "load_points", lambda name: pd.DataFrame({"point_id": ["A"]}))
    # No monitor reading on Nov 4: the EPA comparison still scores that day's area AQI.
    monkeypatch.setattr(live, "_observed", lambda *args: fc[["point_id", "valid_date"]].assign(
        valid_date=lambda f: pd.to_datetime(f["valid_date"]).dt.date, obs=10.0)
        .query("valid_date != @date(2026, 11, 4)"))
    calls = []
    monkeypatch.setattr(live.airnow, "download_reportingarea_day",
                        lambda d, overwrite=False: calls.append((d, overwrite)))
    monkeypatch.setattr(live, "compare_with_epa", lambda *args: pd.DataFrame())

    live.score(SimpleNamespace(name="test"), log=lambda *args: None)

    # Issue-day files are refreshed; observation files only within 4 days of the newest day.
    assert calls == [(date(2026, 10, 20), True), (date(2026, 10, 22), True),
                     (date(2026, 10, 24), False), (date(2026, 11, 3), True),
                     (date(2026, 11, 5), True),
                     (date(2026, 11, 6), True)]


def test_live_score_writes_the_board_when_an_epa_download_fails(tmp_path, monkeypatch):
    import requests

    from serein import live

    fc = pd.DataFrame({
        "issue_date": [date(2026, 11, 3)], "lead": [1], "valid_date": [date(2026, 11, 4)],
        "point_id": "A", "kind": "epa", "on_time": True, "smokecast": 10.0, "warn": False,
        "noaa_best": 10.0, "aqm_bc": 10.0, "persistence": 10.0})
    monkeypatch.setattr(live, "LIVE", tmp_path)
    monkeypatch.setattr(live, "datetime",
                        SimpleNamespace(now=lambda tz=None: datetime(2026, 11, 7, tzinfo=UTC)))
    saved = tmp_path / "test" / "forecasts"
    saved.mkdir(parents=True)
    fc.to_parquet(saved / "20261103.parquet", index=False)
    monkeypatch.setattr(live, "load_points", lambda name: pd.DataFrame({"point_id": ["A"]}))
    monkeypatch.setattr(live, "_observed", lambda *args: pd.DataFrame(
        {"point_id": ["A"], "valid_date": [date(2026, 11, 4)], "obs": [12.0]}))

    def unavailable(d, overwrite=False):
        raise requests.HTTPError("503 Server Error")
    monkeypatch.setattr(live.airnow, "download_reportingarea_day", unavailable)
    lines = []

    scored = live.score(SimpleNamespace(name="test"), log=lambda *args: lines.append(" ".join(map(str, args))))

    # The EPA comparison is optional, so a failed AirNow download only skips it.
    assert len(scored) == 1
    assert (tmp_path / "test" / "SCOREBOARD.md").exists()
    assert any(line.startswith("EPA comparison skipped") for line in lines)
