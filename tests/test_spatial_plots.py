import numpy as np
import pandas as pd
import pytest
from PIL import Image

from serein.eval.spatial import analyze_spatial
from serein.eval.spatial_plots import plot_spatial_scores


def summary():
    frame = pd.DataFrame({"issue_date": pd.date_range("2023-06-01", periods=42),
                          "point_id": "E", "y_L1": 10., "smokecast_L1": 11., "other_L1": 12.})
    points = pd.DataFrame({"point_id": ["R", "E"], "lat": [38., 38.1], "lon": [-121., -121.1]})
    partition = {"reference_ids": ["R"], "evaluation_ids": ["E"], "provenance": "synthetic"}
    result, _, _ = analyze_spatial(frame, points, partition, models=["smokecast", "other"], n_boot=10)
    return result


@pytest.mark.parametrize("condition", ["ordinary", "no_scored_rows", "no_bounds", "point_outside_bounds", "single_model"])
def test_spatial_png_handles_empty_populations_and_exploratory_bounds(tmp_path, condition):
    frame = summary()
    if condition == "no_scored_rows":
        frame["n_scored"] = frame["n_sites_scored"] = 0
        frame["rmse"] = frame["rmse_difference"] = np.nan
        frame["rmse_difference_ci_lo"] = frame["rmse_difference_ci_hi"] = np.nan
    elif condition == "no_bounds":
        frame["rmse_difference_ci_lo"] = frame["rmse_difference_ci_hi"] = np.nan
    elif condition == "point_outside_bounds":
        frame["rmse_difference_ci_lo"] = 3.
        frame["rmse_difference_ci_hi"] = 4.
    elif condition == "single_model":
        frame = frame.loc[frame.model.eq("smokecast")]
    before = frame.copy(deep=True)
    target = tmp_path / "spatial.png"
    plot_spatial_scores(frame, 1, target)
    with Image.open(target) as image:
        assert image.format == "PNG"
        assert image.width > 1000 and image.height > 500
        assert np.asarray(image).std() > 0
    pd.testing.assert_frame_equal(frame, before)


@pytest.mark.parametrize("problem", ["missing_lead", "duplicate", "missing_reference", "mixed_references"])
def test_spatial_plot_rejects_ambiguous_summaries(tmp_path, problem):
    frame = summary()
    lead = 1
    if problem == "missing_lead":
        lead = 2
    elif problem == "duplicate":
        frame = pd.concat([frame, frame.iloc[:1]])
    elif problem == "missing_reference":
        frame = frame.loc[frame.model.eq("other")]
    else:
        frame.loc[frame.index[-1], "reference_model"] = "other"
    with pytest.raises(ValueError):
        plot_spatial_scores(frame, lead, tmp_path / "invalid.png")
    assert not (tmp_path / "invalid.png").exists()
