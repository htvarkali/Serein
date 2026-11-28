import json

import pandas as pd
import pytest

from serein import places

REGION = {"lat_min": 32.0, "lat_max": 49.0, "lon_min": -125.0, "lon_max": -114.0}


def test_points_keep_the_study_box_round_and_deduplicate():
    df = pd.DataFrame({"NAME": list("abcde"),
                       "LAT": ["37.12345", "37.12349", "40.0", "51.0", "bad"],
                       "LON": ["-122.0", "-122.0", "-110.0", "-120.0", "-120.0"]})
    assert places.points(df, REGION) == [[37.123, -122.0]]


def test_hospital_columns_and_closed_rows():
    df = pd.DataFrame({"X": ["-121.5", "-121.6"], "Y": ["38.5", "38.6"],
                       "STATUS": ["OPEN", "CLOSED"]})
    assert places.points(df, REGION) == [[38.5, -121.5]]


def test_missing_coordinates_say_what_was_looked_for():
    with pytest.raises(ValueError, match="latitude"):
        places.points(pd.DataFrame({"NAME": ["x"]}), REGION)


def test_main_writes_the_file_the_site_reads(tmp_path):
    s, h, out = tmp_path / "s.csv", tmp_path / "h.csv", tmp_path / "places.json"
    pd.DataFrame({"LAT": [45.5], "LON": [-122.7]}).to_csv(s, index=False)
    pd.DataFrame({"LATITUDE": [47.6], "LONGITUDE": [-122.3], "STATUS": ["OPEN"]}).to_csv(h, index=False)
    places.main(["--schools", str(s), "--hospitals", str(h), "--out", str(out)])
    data = json.loads(out.read_text())
    assert data["schools"] == [[45.5, -122.7]] and data["hospitals"] == [[47.6, -122.3]]
    assert "source" in data
