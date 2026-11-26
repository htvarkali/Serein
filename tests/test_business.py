"""The Brief and the business plan quote these figures; keep them tied to the arithmetic."""

import csv

import pytest

from serein import business


def test_brief_worked_example_of_a_season_of_text_alerts():
    # Brief Q9: "60 smoke-day alerts to 1,000 families cost about $1,100 a season."
    assert business.messaging_cost(1000, 60) == pytest.approx(1125.0)


def test_one_family_costs_about_a_dollar_by_sms_and_twenty_cents_by_whatsapp():
    assert business.messaging_cost(1, 60) == pytest.approx(1.125)
    assert business.messaging_cost(1, 60, "whatsapp") == pytest.approx(0.204)


def test_district_fee_uses_the_floor_for_small_districts():
    assert business.district_fee(10_000, 0.50) == 5000.0
    assert business.district_fee(10_000, 1.50) == 15000.0
    assert business.district_fee(1_000, 0.50) == business.DISTRICT_FLOOR_USD


def test_messaging_share_of_a_district_fee_when_every_child_with_asthma_enrolls():
    # 10,000 students x 6.7% = 670 families; 670 x $1.125 = $754.
    assert business.district_messaging_share(10_000, 0.50) == pytest.approx(0.151, abs=0.001)
    assert business.district_messaging_share(10_000, 1.00) == pytest.approx(0.075, abs=0.001)
    assert business.district_messaging_share(10_000, 1.50) == pytest.approx(0.050, abs=0.001)


def test_at_the_lowest_price_two_thirds_enrollment_keeps_sms_at_ten_percent():
    share = business.max_enrolled_share(10_000, 0.50)
    assert share == pytest.approx(0.663, abs=0.001)
    assert business.district_messaging_share(10_000, 0.50, share) == pytest.approx(0.10)
    assert business.max_enrolled_share(10_000, 1.00) == 1.0


def test_messaging_share_of_a_health_plan_fee():
    assert business.health_plan_messaging_share(10.0) == pytest.approx(0.1125)
    assert business.health_plan_messaging_share(20.0) == pytest.approx(0.05625)
    assert business.health_plan_messaging_share(10.0, channel="whatsapp") == pytest.approx(0.0204)


def test_one_avoided_hospital_stay_in_child_years():
    # Brief Q9: "one avoided stay funds 370 to 750 child-years of Serein."
    assert business.child_years_per_avoided_stay(20.0) == pytest.approx(373.2)
    assert business.child_years_per_avoided_stay(10.0) == pytest.approx(746.4)


def test_one_time_costs_before_the_summit():
    assert business.one_time_costs() == 499 + 65 + 350
    assert business.one_time_costs(trademark_classes=2) == 499 + 65 + 700


def test_scenario_rows_add_up_and_the_high_case_ends_at_the_brief_figure():
    rows = business.scenario_rows()
    assert {row["scenario"] for row in rows} == {"low", "base", "high"}
    for row in rows:
        costs = row["messaging_usd"] + row["hosting_usd"] + row["review_usd"]
        assert abs(row["costs_usd"] - costs) <= 1  # each part is rounded to a dollar
        assert abs(row["net_before_pay_usd"] - (row["revenue_usd"] - row["costs_usd"])) <= 1
    last_high = [row for row in rows if row["scenario"] == "high"][-1]
    assert last_high["paying_districts"] == 70
    assert last_high["revenue_usd"] == 350_000  # Brief Q6 bottom-up size


def test_a_free_pilot_year_has_no_revenue():
    first_base = next(row for row in business.scenario_rows() if row["scenario"] == "base")
    assert first_base["revenue_usd"] == 0
    assert first_base["net_before_pay_usd"] < 0


def test_bad_inputs_are_refused():
    with pytest.raises(ValueError):
        business.messaging_cost(-1, 10)
    with pytest.raises(ValueError):
        business.messaging_cost(1, 10, "fax")
    with pytest.raises(ValueError):
        business.district_messaging_share(10_000, 0.50, enrolled_share=1.5)
    with pytest.raises(ValueError):
        business.health_plan_messaging_share(0)


def test_cli_writes_the_table(tmp_path, capsys):
    out = tmp_path / "scenarios.csv"
    business.main(["--out", str(out)])
    with out.open(encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 9
    assert "net_before_pay_usd" in rows[0]
    assert "| scenario |" in capsys.readouterr().out
