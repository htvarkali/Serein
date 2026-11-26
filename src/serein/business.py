"""Cost and revenue arithmetic behind the business plan (task E-6).

Every price below is a public number already recorded, with its source and date, in
docs/BUSINESS_NUMBERS_2026-11-07.md. This module only multiplies them, so the Brief and
the business plan quote figures that a test can check. The scenario table is a set of
labeled assumptions about how many districts sign. It is not a forecast: no district has
been interviewed or has agreed to pay.

    uv run python -m serein.business --out docs/drafts/business_scenarios.csv
"""

from __future__ import annotations

import argparse
import csv
from dataclasses import dataclass
from pathlib import Path

# Public prices (docs/BUSINESS_NUMBERS_2026-11-07.md, section 3).
SMS_PART_USD = 0.0125  # Twilio $0.0083 a segment plus carrier fees of $0.0035 to $0.005
PARTS_PER_ALERT = 1.5  # our messages are 1 or 2 SMS parts (docs/mockups/messages.md)
WHATSAPP_ALERT_USD = 0.0034  # Meta utility message, North America (reseller copy of the card)
HOST_MONTH_USD = 25.0  # Render 1 CPU, 2 GB; the $7 tier also runs the forecast
REVIEW_USD = 500.0  # native-speaker and translation review, per season (Brief Q10)

# One-time costs before the Summit (Brief Q10; USPTO fee page read 2026-11-25).
CONRAD_FEE_USD = 499.0
PROVISIONAL_PATENT_USD = 65.0  # micro entity
TRADEMARK_CLASS_USD = 350.0  # base electronic application, per class

# Prices we propose (Brief Q9).
DISTRICT_PER_STUDENT_USD = (0.50, 1.50)
DISTRICT_FLOOR_USD = 1500.0
HEALTH_PLAN_PER_CHILD_USD = (10.0, 20.0)

# CDC, 2023 National Health Interview Survey: 6.7% of US children have current asthma.
CHILD_ASTHMA_SHARE = 0.067

# Assumption, not a measurement: alerts sent to one family in a heavy smoke season.
# The Brief's worked example uses 60. Twenty and forty are shown next to it.
ALERTS_HEAVY_SEASON = 60


def messaging_cost(families: float, alerts: float, channel: str = "sms") -> float:
    """Cost in dollars of sending `alerts` messages to each of `families` in one season."""
    if families < 0 or alerts < 0:
        raise ValueError("families and alerts cannot be negative")
    if channel == "sms":
        per_alert = PARTS_PER_ALERT * SMS_PART_USD
    elif channel == "whatsapp":
        per_alert = WHATSAPP_ALERT_USD
    else:
        raise ValueError(f"unknown channel {channel!r}")
    return families * alerts * per_alert


def district_fee(students: float, per_student: float) -> float:
    """Yearly fee for a district at a per-student price, never below the floor."""
    if students < 0 or per_student < 0:
        raise ValueError("students and price cannot be negative")
    return max(students * per_student, DISTRICT_FLOOR_USD)


def district_messaging_share(
    students: float,
    per_student: float,
    enrolled_share: float = 1.0,
    alerts: float = ALERTS_HEAVY_SEASON,
    channel: str = "sms",
) -> float:
    """Messaging cost as a share of one district's fee.

    `enrolled_share` is the share of the district's children with asthma whose family
    signs up; 1.0 means every one of them.
    """
    if not 0.0 <= enrolled_share <= 1.0:
        raise ValueError("enrolled_share must be between 0 and 1")
    families = students * CHILD_ASTHMA_SHARE * enrolled_share
    return messaging_cost(families, alerts, channel) / district_fee(students, per_student)


def max_enrolled_share(
    students: float, per_student: float, target: float = 0.10, alerts: float = ALERTS_HEAVY_SEASON
) -> float:
    """Largest enrolled share that keeps SMS cost at or under `target` of the fee (capped at 1)."""
    at_full = district_messaging_share(students, per_student, 1.0, alerts)
    return 1.0 if at_full <= target else target / at_full


def health_plan_messaging_share(
    per_child: float, alerts: float = ALERTS_HEAVY_SEASON, channel: str = "sms"
) -> float:
    """Messaging cost for one enrolled child as a share of the health plan's yearly fee."""
    if per_child <= 0:
        raise ValueError("price per child must be positive")
    return messaging_cost(1, alerts, channel) / per_child


def child_years_per_avoided_stay(per_child: float, stay_cost: float = 7464.0) -> float:
    """Child-years of Serein one avoided hospital stay would pay for (Gabbay et al., 2025)."""
    return stay_cost / per_child


def one_time_costs(trademark_classes: int = 1) -> float:
    return CONRAD_FEE_USD + PROVISIONAL_PATENT_USD + trademark_classes * TRADEMARK_CLASS_USD


@dataclass(frozen=True)
class Year:
    """One year of one scenario. Every field except the prices is an assumption."""

    label: str
    paying_districts: int
    pilot_districts: int = 0  # served free
    students_per_district: int = 10_000
    per_student: float = 0.50
    enrolled_share: float = 0.30
    alerts: float = ALERTS_HEAVY_SEASON
    languages_reviewed: int = 1

    def row(self) -> dict:
        districts = self.paying_districts + self.pilot_districts
        families = districts * self.students_per_district * CHILD_ASTHMA_SHARE * self.enrolled_share
        revenue = self.paying_districts * district_fee(self.students_per_district, self.per_student)
        messaging = messaging_cost(families, self.alerts)
        hosting = 12 * HOST_MONTH_USD
        review = self.languages_reviewed * REVIEW_USD
        costs = messaging + hosting + review
        return {
            "year": self.label,
            "paying_districts": self.paying_districts,
            "pilot_districts": self.pilot_districts,
            "families": round(families),
            "revenue_usd": round(revenue),
            "messaging_usd": round(messaging),
            "hosting_usd": round(hosting),
            "review_usd": round(review),
            "costs_usd": round(costs),
            # Before paying anyone: student time, support and insurance are not priced.
            "net_before_pay_usd": round(revenue - costs),
        }


# Three scenarios for the first three school years. The district counts are assumptions
# chosen to bracket the outcome; the high case ends at the Brief's 70 districts (5% of the
# 1,427 in California, Oregon and Washington). Unpaid student time is not a cost here,
# which is the largest thing this table leaves out.
SCENARIOS: dict[str, tuple[Year, ...]] = {
    "low": (
        Year("2027-28", paying_districts=0, pilot_districts=1),
        Year("2028-29", paying_districts=1, pilot_districts=1),
        Year("2029-30", paying_districts=3),
    ),
    "base": (
        Year("2027-28", paying_districts=0, pilot_districts=1),
        Year("2028-29", paying_districts=3, pilot_districts=1, languages_reviewed=2),
        Year("2029-30", paying_districts=10, languages_reviewed=2),
    ),
    "high": (
        Year("2027-28", paying_districts=1, pilot_districts=1),
        Year("2028-29", paying_districts=15, languages_reviewed=2),
        Year("2029-30", paying_districts=70, languages_reviewed=3),
    ),
}


def scenario_rows() -> list[dict]:
    return [{"scenario": name, **year.row()} for name, years in SCENARIOS.items() for year in years]


def markdown_table(rows: list[dict]) -> str:
    columns = list(rows[0])
    lines = ["| " + " | ".join(columns) + " |", "|" + "---|" * len(columns)]
    for row in rows:
        lines.append("| " + " | ".join(str(row[c]) for c in columns) + " |")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--out", type=Path, help="write the scenario table to this CSV file")
    args = parser.parse_args(argv)
    rows = scenario_rows()
    if args.out:
        with args.out.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(rows[0]), lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
    print(markdown_table(rows))


if __name__ == "__main__":
    main()
