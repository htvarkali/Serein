import numpy as np
import pandas as pd
import pytest
from matplotlib.figure import Figure

from serein.eval.figures import calibration_by_level, case_study, peak_report, skill_by_lead


def predictions():
    return pd.DataFrame({
        "point_id": ["A"] * 8, "issue_date": pd.date_range("2023-06-01", periods=8),
        "y_L1": [0., 10., 20., 40., 50., 60., np.nan, np.inf],
        "smokecast_L1": [0., 12., 35.5, 40., 40., 40., 10., 10.],
        "smokecast_lo_L1": [0., 5., 10., 35., np.nan, 45., 5., 5.],
        "smokecast_hi_L1": [1., 15., 30., 45., 55., 50., 15., 15.],
        "noaa_best_L1": [0., 12., 20., 50., np.nan, np.inf, 10., 10.],
        "persistence_L1": [0., 10., 30., 35., 40., 50., 10., 10.],
    })


@pytest.fixture
def saved_run(tmp_path):
    predictions().to_parquet(tmp_path / "predictions.parquet", index=False)
    return tmp_path


def test_peak_report_separates_missing_bounds_and_forecasts_from_misses(saved_run):
    result = peak_report(saved_run).iloc[0]
    assert result.n_smoky_site_days == 3
    assert result.smokecast_n == 3
    assert result.noaa_best_n == 1
    assert result.persistence_n == 3
    assert result.smokecast_n_intervals == 2
    assert result.smokecast_in_90pct_range == pytest.approx(1 / 2)
    assert result.noaa_best_median_ratio == pytest.approx(50 / 40)


def test_peak_report_no_available_predictions_or_intervals_is_undefined(saved_run):
    frame = predictions()
    frame["smokecast_L1"] = frame["smokecast_lo_L1"] = np.nan
    frame.to_parquet(saved_run / "predictions.parquet", index=False)
    result = peak_report(saved_run).iloc[0]
    assert result.smokecast_n == result.smokecast_n_intervals == 0
    assert pd.isna(result.smokecast_median_ratio) and pd.isna(result.smokecast_in_90pct_range)


@pytest.mark.parametrize("renderer", [peak_report, calibration_by_level])
def test_reversed_scored_bounds_fail_instead_of_becoming_noncoverage(saved_run, renderer):
    frame = predictions()
    frame.loc[3, "smokecast_lo_L1"] = 100.
    frame.to_parquet(saved_run / "predictions.parquet", index=False)
    with pytest.raises(ValueError, match="lower bounds"):
        renderer(saved_run)


def test_calibration_chart_uses_finite_paired_bounds_and_exact_bin_boundaries(saved_run, monkeypatch):
    captured = []

    def save(fig, *args, **kwargs):
        ax = fig.axes[0]
        captured.append(([bar.get_height() for bar in ax.patches], ax.get_ylim(),
                         [tick.get_text() for tick in ax.get_xticklabels()]))

    monkeypatch.setattr(Figure, "savefig", save)
    calibration_by_level(saved_run)
    heights, limits, labels = captured[0]
    assert heights == pytest.approx([1., 1., 2 / 3])
    assert limits == (0, 1)
    assert labels == ["clean (<12)", "moderate (12-<35.5)", "smoky (>=35.5)"]


@pytest.mark.parametrize("renderer", ["lead", "case"])
def test_plots_name_the_actual_mixed_baseline(saved_run, monkeypatch, renderer):
    captured = []

    def save(fig, *args, **kwargs):
        captured.extend(fig.axes[0].get_legend_handles_labels()[1])

    monkeypatch.setattr(Figure, "savefig", save)
    if renderer == "lead":
        pd.DataFrame({"subset": ["all"] * 2, "model": ["smokecast", "noaa_best"],
                      "lead": [1, 1], "rmse": [5., 10.]}).to_csv(saved_run / "metrics.csv", index=False)
        skill_by_lead(saved_run)
    else:
        case_study(saved_run, "A")
    assert "NOAA/persistence fallback" in captured
    assert "Best NOAA forecast" not in captured
