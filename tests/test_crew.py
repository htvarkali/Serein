import numpy as np

from serein import crew


def test_clean_air_needs_no_action_and_always_reminds_to_check_current_aqi():
    o = crew.outlook([3, 4, 5, 6, 8], lead=1)
    assert o.action == crew.TEXT["en"]["clear"]
    assert o.notes[-1] == crew.TEXT["en"]["check"]
    assert o.p_rule_level < 0.05 and o.category == "Good"


def test_smoky_forecast_plans_for_the_rule_level():
    o = crew.outlook([40, 55, 70, 90, 130], lead=1)
    assert o.action == crew.TEXT["en"]["plan"]
    assert o.p_rule_level > 0.5


def test_possible_smoke_only_in_the_upper_range_is_a_watch():
    o = crew.outlook([8, 12, 18, 30, 60], lead=2)
    assert o.action == crew.TEXT["en"]["watch"]


def test_extreme_upper_range_warns_about_required_respirators():
    o = crew.outlook([150, 220, 280, 330, 420], lead=0)
    assert o.action == crew.TEXT["en"]["severe"]


def test_recalibration_and_low_confidence_flag_use_saved_run_files():
    recal = {"1": {"x": [0.0, 1.0], "y": [0.0, 0.5]}}
    raw = crew.outlook([20, 30, 40, 50, 60], lead=1)
    cal = crew.outlook([20, 30, 40, 50, 60], lead=1, recal=recal)
    assert np.isclose(cal.p_unhealthy_sensitive, raw.p_unhealthy_sensitive / 2)
    flag = {"log_width": {"1": 0.5}}
    wide = crew.outlook([5, 20, 40, 80, 160], lead=1, flag_width=flag)
    assert wide.low_confidence and wide.notes[0] == crew.TEXT["en"]["low_confidence"]


def test_spanish_has_every_message():
    assert crew.TEXT["es"].keys() == crew.TEXT["en"].keys()


def test_rule_level_chance_never_exceeds_the_lower_threshold_chance():
    recal = {"1": {"x": [0.0, 1.0], "y": [0.0, 0.0]}}
    o = crew.outlook([3, 4, 5, 6, 8], lead=1, recal=recal)
    assert o.p_rule_level <= o.p_unhealthy_sensitive == 0.0
