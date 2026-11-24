from serein.data import cams


def test_request_covers_the_study_box_and_four_days_ahead():
    assert cams.AREA == [49, -125, 32, -114]
    assert cams.LEADS[0] == "0" and cams.LEADS[-1] == "96" and len(cams.LEADS) == 33


def test_monthly_files_are_named_by_year_and_month():
    assert cams.month_path(2023, 8).name == "cams_pm25_202308.nc"
