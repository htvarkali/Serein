from datetime import date, datetime

import numpy as np
import pandas as pd
import pytest

from serein.aqi import aqi_to_category, pm25_to_aqi, pm25_to_category
from serein.data.airnow import parse_hourly_aqobs, parse_reportingarea
from serein.data.availability import Availability
from serein.data.hrrr import parse_idx, smoke_to_ugm3
from serein.data.purpleair import epa_correction, estimate_history_points, qc_ab
from serein.features.daily import model_daily, obs_daily_means

AQOBS = '''"AQSID","SiteName","Status","EPARegion","Latitude","Longitude","Elevation","GMTOffset","CountryCode","StateName","ValidDate","ValidTime","DataSource","ReportingArea_PipeDelimited","OZONE_AQI","PM10_AQI","PM25_AQI","NO2_AQI","OZONE_Measured","PM10_Measured","PM25_Measured","NO2_Measured","NO2","NO2_Unit","CO","CO_Unit","PM25","PM25_Unit","SO2","SO2_Unit","OZONE","OZONE_Unit","PM10","PM10_Unit"
"061010004","Sutter Buttes","Active","R9","39.20556","-121.82046","645.4","-8","US","CA","09/01/2024","12:00","CARB","","84","","","","1","0","0","0","","","","","","","","","","","",""
"420850100","Farrell","Active","R3","41.215","-80.485","0.0","-5","US","PA","09/01/2024","12:00","PA DEP","Mercer County","19","","38","","1","0","1","0","","","","","7.1","UG/M3","","","20.0","PPB","",""
'''

RA = """09/01/24|09/02/24||PDT|1|F|Y|Sacramento|CA|38.5670|-121.4670|PM2.5|105|Unhealthy for Sensitive Groups|No|smoke|SMAQMD
09/01/24|08/31/24||PDT|-1|Y|Y|Sacramento|CA|38.5670|-121.4670|PM2.5|60|Moderate|No||SMAQMD
09/01/24|09/01/24|23:00|PDT|0|O|Y|Sacramento|CA|38.5670|-121.4670|OZONE|40|Good|No||SMAQMD
"""


def test_parse_hourly_aqobs_keeps_only_pm25_rows():
    df = parse_hourly_aqobs(AQOBS)
    assert list(df["site_id"]) == ["420850100"]
    assert df.loc[0, "pm25"] == pytest.approx(7.1)
    assert df.loc[0, "time_utc"] == pd.Timestamp("2024-09-01 12:00")
    assert df.loc[0, "gmt_offset"] == -5


def test_parse_reportingarea_forecast_lead():
    df = parse_reportingarea(RA)
    assert len(df) == 2  # ozone row dropped
    f = df[df["data_type"] == "F"].iloc[0]
    assert f["lead"] == 1 and f["category_idx"] == 2


def test_aqi_2024_breakpoints():
    assert pm25_to_aqi([9.0])[0] == 50
    assert pm25_to_aqi([9.1])[0] == 51
    assert pm25_to_aqi([35.4])[0] == 100
    assert pm25_to_aqi([35.5])[0] == 101
    assert pm25_to_aqi([125.4])[0] == 200
    assert list(pm25_to_category([5, 20, 40, 100, 200, 300])) == [0, 1, 2, 3, 4, 5]


def test_aqi_old_scale_before_may_2024():
    old = date(2023, 8, 1)
    assert pm25_to_category([10.0], old)[0] == 0  # Good under 2012 scale
    assert pm25_to_category([10.0], date(2024, 8, 1))[0] == 1  # Moderate under 2024 scale
    assert pm25_to_category([140.0], old)[0] == 3
    assert pm25_to_category([140.0], date(2024, 8, 1))[0] == 4


def test_aqi_categories_take_a_single_number():
    for pm in [0.0, 9.0, 9.1, 12.0, 12.1, 35.45, 55.5, 140.0, 225.5, 600.0]:
        for on in (None, date(2023, 8, 1)):
            assert float(pm25_to_category(pm, on)) == pm25_to_category([pm], on)[0], (pm, on)
    assert np.isnan(pm25_to_category(np.nan))
    edges = [0, 50, 51, 100, 101, 150, 151, 200, 201, 300, 301, 500]
    assert list(aqi_to_category(edges)) == [0, 0, 1, 1, 2, 2, 3, 3, 4, 4, 5, 5]
    for a in edges:
        assert float(aqi_to_category(a)) == aqi_to_category([a])[0], a
    assert np.isnan(aqi_to_category(np.nan))
    assert float(aqi_to_category(pm25_to_aqi(40.0))) == float(pm25_to_category(40.0)) == 2


def test_purpleair_correction_is_continuous():
    rh = 40.0
    for x in (30, 50, 210, 260):
        lo = epa_correction(np.array([x - 1e-6]), np.array([rh]))[0]
        hi = epa_correction(np.array([x + 1e-6]), np.array([rh]))[0]
        assert lo == pytest.approx(hi, abs=0.05), x
    # Low-cost sensors read high in smoke; the correction should bring them down.
    assert epa_correction(np.array([100.0]), np.array([40.0]))[0] < 100


def test_purpleair_ab_qc():
    mean, keep = qc_ab([10, 10, 100], [11, 40, 120])
    assert list(keep) == [True, False, True]
    assert mean[0] == pytest.approx(10.5)


def test_purpleair_cost_estimate_scales():
    a = estimate_history_points(10, 30)
    b = estimate_history_points(20, 30)
    assert b["points"] > a["points"] and b["rows"] == 2 * a["rows"]


def test_availability_rules():
    av = Availability(issue_hour_utc=18.5, obs_lag_hours=1.5)
    d = date(2024, 9, 1)
    assert av.last_obs_hour_start(d) == datetime(2024, 9, 1, 16)
    assert av.hms_day(d) == date(2024, 8, 31)
    assert av.check_model_cycle(d, 12, 6.1)       # AQM 12z posted ~18:06Z < 18:30Z
    assert not av.check_model_cycle(d, 12, 7.0)   # would be posted 19:00Z: too late


def test_hrrr_idx_and_units():
    idx = "1:0:d=2024090100:REFC:entire atmosphere:6 hour fcst:\n76:500:d=2024090100:MASSDEN:8 m above ground:6 hour fcst:\n77:900:d=x:UGRD:10 m above ground:6 hour fcst:\n"
    rows = parse_idx(idx)
    assert rows[1] == (500, 899, "MASSDEN:8 m above ground")
    assert rows[-1][1] is None
    kg = np.array([0.0, 2e-8, 1e-7], dtype=np.float32)
    assert smoke_to_ugm3(kg)[2] == pytest.approx(100.0, rel=1e-4)
    ug = np.array([0.0, 20.0, 100.0], dtype=np.float32)
    assert smoke_to_ugm3(ug)[2] == pytest.approx(100.0)


def test_local_day_mean_uses_standard_time_and_completeness():
    # Pacific site: local day 2024-09-02 = UTC 09-02 08:00 .. 09-03 07:00
    times = pd.date_range("2024-09-02 08:00", periods=24, freq="h")
    h = pd.DataFrame({"site_id": "A", "time_utc": times, "pm25": np.arange(24, dtype=float)})
    out = obs_daily_means(h, pd.Series({"A": -8}))
    row = out[out["local_date"] == date(2024, 9, 2)].iloc[0]
    assert row["n_hours"] == 24 and row["pm25_daily"] == pytest.approx(11.5)
    out = obs_daily_means(h.iloc[:10], pd.Series({"A": -8}))
    assert np.isnan(out["pm25_daily"].iloc[0])  # < 18 hours -> no daily value


def test_model_daily_leads():
    t = pd.date_range("2024-09-01 12:00", periods=48, freq="h")
    df = pd.DataFrame({"issue_date": date(2024, 9, 1), "point_id": "A", "valid_utc": t, "value": 1.0})
    g = model_daily(df, pd.Series({"A": -8}), min_count=12)
    assert set(g["lead"]) == {0, 1, 2}
    assert np.isnan(g.loc[g["lead"] == 2, "mean"]).all()  # only 4 h on lead 2
    assert g.loc[g["lead"] == 1, "size"].iloc[0] == 24


def test_time_zone_from_nearest_monitor_not_longitude():
    import pandas as pd

    from serein.data.points import nearest_site_offset, standard_offset

    sites = pd.DataFrame({"lat": [43.6, 47.6], "lon": [-116.2, -122.3], "gmt_offset": [-7, -8]})
    assert standard_offset([-116.0])[0] == -8          # longitude alone gets Boise wrong
    assert nearest_site_offset([43.5], [-116.0], sites)[0] == -7
    assert nearest_site_offset([47.0], [-122.0], sites)[0] == -8


def test_smoke_conversion_refuses_physically_impossible_values():
    from serein.data.hrrr import colmd_to_mgm2

    # Real fields convert as before.
    assert smoke_to_ugm3(np.array([0.0, 2e-6, 4e-6]))[2] == pytest.approx(4000.0, rel=1e-4)
    assert colmd_to_mgm2(np.array([0.0, 1e-3]))[1] == pytest.approx(1000.0, rel=1e-4)
    # A µg/m³ field so clean that the magnitude rule takes it for kg/m³ would be
    # scaled a billion times; that must stop, not be written.
    with pytest.raises(ValueError, match="physical ceiling"):
        smoke_to_ugm3(np.array([0.0, 0.2, 0.6]))
    with pytest.raises(ValueError, match="physical ceiling"):
        colmd_to_mgm2(np.array([0.0, 0.5]))
    # Missing values are ignored, and an all-missing field passes through.
    assert np.isnan(smoke_to_ugm3(np.array([np.nan, np.nan]))).all()
