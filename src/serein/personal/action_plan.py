"""From forecast + personal risk to a family action plan (green / yellow / red).

SAFETY RULE: the personal model may only make advice STRICTER than the public
EPA guidance for children with asthma, never looser. A child who looks
"insensitive" in their log still gets at least the zone the AQI calls for.

Floors from EPA guidance for sensitive groups (children with asthma):
  forecast AQI category >= USG (orange)          -> at least YELLOW
  forecast AQI category >= Very Unhealthy        -> RED

Personal escalation uses the risk CAUSED BY SMOKE: the child's predicted risk
under the forecast vs. the same child, same day, with clean air (5 µg/m³ today
and the two days before). A child whose asthma flares for other reasons (a cold)
should not get a smoke warning on a clean day.
  smoke-attributable: +5 points or 1.3x -> YELLOW;   +15 points or 2x -> RED
These cut-offs are design choices to review with a clinician (TODO C-8).
Serein is not a medical device; every message says to follow the child's own
asthma action plan from their doctor.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from numbers import Real
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from serein.aqi import CATEGORIES, pm25_to_category
from serein.personal.model import HOT_DAY_C

ZONES = ["green", "yellow", "red"]
MSG_DIR = Path(__file__).parent / "messages"


@dataclass
class Plan:
    zone: str
    reason: str
    risk: float
    risk_lo: float
    risk_hi: float
    pm_median: float
    pm_hi: float
    aqi_category: str
    message: str


def _validate_numbers(**values: float) -> None:
    for name, value in values.items():
        if (isinstance(value, (bool, np.bool_))
                or not isinstance(value, (int, float, np.integer, np.floating))
                or not np.isfinite(value)):
            raise ValueError(f"{name} must be a finite numeric scalar")
        if value < 0 or (name in ("risk", "baseline_risk") and value > 1):
            raise ValueError(f"{name} is outside its valid range")
    if "pm_hi" in values and values["pm_hi"] < values["pm_median"]:
        raise ValueError("pm_hi must be at least pm_median")


def choose_zone(risk: float, baseline_risk: float, pm_median: float, pm_hi: float,
                on: date | None = None) -> tuple[str, str]:
    _validate_numbers(risk=risk, baseline_risk=baseline_risk,
                      pm_median=pm_median, pm_hi=pm_hi)
    cat_med = int(pm25_to_category(np.array([pm_median]), on)[0])
    cat_hi = int(pm25_to_category(np.array([pm_hi]), on)[0])
    zone, reason = 0, "personal_low"
    # Public-guidance floor (uses the median forecast; a high upper range nudges up).
    if cat_med >= 2 or cat_hi >= 3:
        zone, reason = 1, "aqi_floor"
    if cat_med >= 4:
        zone, reason = 2, "aqi_floor"
    # Personal escalation on smoke-attributable risk.
    rel = risk / max(baseline_risk, 1e-6)
    excess = risk - baseline_risk
    if (rel >= 1.3 or excess >= 0.05) and zone < 1:
        zone, reason = 1, "personal"
    if (rel >= 2.0 or excess >= 0.15) and zone < 2:
        zone, reason = 2, "personal"
    return ZONES[zone], reason


def load_messages(language: str) -> dict:
    path = MSG_DIR / f"{language}.yaml"
    if not path.exists():
        raise FileNotFoundError(f"No messages for '{language}'. Available: "
                                f"{sorted(p.stem for p in MSG_DIR.glob('*.yaml'))}")
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _category_name(category_idx: int) -> str:
    if (isinstance(category_idx, (bool, np.bool_))
            or not isinstance(category_idx, (int, np.integer))
            or not 0 <= category_idx < len(CATEGORIES)):
        raise ValueError("category_idx must be an integer from 0 to 5")
    return CATEGORIES[category_idx]


def render(zone: str, reason: str, child_name: str, day_label: str, pm_median: float,
           pm_hi: float, risk: float, category_idx: int, language: str = "en",
           style: str = "plain") -> str:
    """Full plan. style="whatsapp" bolds the title with *...* (WhatsApp markup)."""
    _validate_numbers(pm_median=pm_median, pm_hi=pm_hi, risk=risk)
    category = _category_name(category_idx)
    msgs = load_messages(language)
    day_label = msgs.get("day_labels", {}).get(day_label, day_label)
    z = msgs["zones"][zone]
    cat = msgs["categories"][category]
    title = z["title"].format(name=child_name, day=day_label)
    lines = [
        f"*{title}*" if style == "whatsapp" else title,
        msgs["forecast_line"].format(pm=round(pm_median), pm_hi=round(pm_hi), category=cat),
        msgs["risk_line"].format(risk=round(100 * risk), name=child_name, day=day_label),
    ]
    if reason == "personal":
        lines.append(msgs["personal_note"].format(name=child_name))
    lines.append("")
    lines += [f"- {a.format(name=child_name)}" for a in z["actions"]]
    lines += ["", msgs["emergency"].format(name=child_name), msgs["disclaimer"]]
    return "\n".join(lines)


# GSM-7 basic character set (3GPP TS 23.038). Anything else forces UCS-2.
_GSM7 = set("@£$¥èéùìòÇ\nØø\rÅå"
            "Δ_ΦΓΛΩΠΨΣΘΞÆæßÉ"
            " !\"#¤%&'()*+,-./0123456789:;<=>?¡ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            "ÄÖÑÜ§¿abcdefghijklmnopqrstuvwxyzäöñüà")
_GSM7_EXT = set("^{}\\[~]|€")  # each costs 2 characters


def sms_segments(text: str) -> tuple[str, int, int]:
    """(encoding, length in that encoding, number of SMS parts the carrier bills)."""
    if all(c in _GSM7 or c in _GSM7_EXT for c in text):
        encoding, single, capacity = "GSM-7", 160, 153
        widths = [2 if c in _GSM7_EXT else 1 for c in text]
    else:
        encoding, single, capacity = "UCS-2", 70, 67
        widths = [2 if ord(c) > 0xFFFF else 1 for c in text]
    n = sum(widths)
    parts, used = 1, 0
    if n > single:
        # Keep extension escapes and UTF-16 surrogate pairs in the same part.
        for width in widths:
            if used + width > capacity:
                parts += 1
                used = 0
            used += width
    return encoding, n, parts


def render_sms(zone: str, child_name: str, day_label: str, pm_median: float,
               category_idx: int, language: str = "en", link: str = "[link]") -> str:
    """Short text-message version of the plan; the link opens the full plan."""
    _validate_numbers(pm_median=pm_median)
    category = _category_name(category_idx)
    msgs = load_messages(language)
    day_label = msgs.get("day_labels", {}).get(day_label, day_label)
    sms = msgs["sms"]
    cat = msgs["categories"][category]
    parts = [sms[zone].format(name=child_name, day=day_label, pm=round(pm_median),
                              category=cat, link=link)]
    if zone != "green":
        parts.append(sms["emergency"])
    parts.append(sms["opt_out"])
    return " ".join(parts)


def forecast_context_values(row) -> dict:
    """Read complete-day values consistently for display and model use."""
    def complete_value(column, prefix, statistic):
        value = row.get(column)
        if value is None or value is pd.NA:
            return None
        if isinstance(value, (bool, np.bool_)) or not isinstance(value, Real):
            raise TypeError(f"{column} must be a finite numeric scalar or missing")
        if np.isnan(value):
            return None
        if not np.isfinite(value):
            raise ValueError(f"{column} must be a finite numeric scalar or missing")
        hours = row.get(f"{prefix}_hours")
        recorded_statistic = row.get(f"{prefix}_statistic")
        if (isinstance(hours, (bool, np.bool_)) or not isinstance(hours, Real)
                or not np.isfinite(hours) or hours != 24
                or not isinstance(recorded_statistic, str) or recorded_statistic != statistic):
            return None
        return float(value)

    ozone = complete_value("ozone_max8h_ppb", "ozone", "max_8h_within_local_day")
    temperature = complete_value("temperature_max_c", "temperature", "maximum_hourly_forecast")
    if ozone is not None and ozone < 0:
        raise ValueError("ozone_max8h_ppb must be nonnegative")
    if temperature is not None and temperature < -273.15:
        raise ValueError("temperature_max_c is below absolute zero")
    return {"ozone_ppb": ozone, "temperature_max_c": temperature}


def forecast_confounders(row) -> dict:
    """Adapt complete-day context to the existing family model.

    Unknowns remain missing in the exported forecast. At this model boundary they
    use its established defaults: no ozone term and a zero heat term. Hourly
    temperature maxima are a forecast proxy, not a measured daily maximum.
    """
    values = forecast_context_values(row)
    temperature = values["temperature_max_c"]
    return {"ozone_ppb": values["ozone_ppb"],
            "hot_day": int(temperature is not None and temperature >= HOT_DAY_C)}


def make_plan(child_model, child_name: str, pm_quantiles: dict, pm_lag1: float,
              pm_lag2: float, outdoor_frac: float = 0.3, cold: int = 0, missed: int = 0,
              day_label: str = "tomorrow", on: date | None = None,
              language: str = "en", ozone_ppb=None, hot_day: int = 0,
              high_pollen: int = 0) -> Plan:
    other = {"ozone_ppb": ozone_ppb, "hot_day": hot_day, "high_pollen": high_pollen}
    r = child_model.risk_under_forecast(pm_quantiles, pm_lag1, pm_lag2, outdoor_frac, cold,
                                        missed, **other)
    # Same child, same day, clean air (fixed seed => paired Monte Carlo draws). Ozone,
    # heat and pollen stay as forecast: only the smoke changes, so a hot or pollen-heavy
    # day alone never triggers a smoke warning.
    base = child_model.risk_under_forecast({0.05: 5.0, 0.5: 5.0, 0.95: 5.0}, 5.0, 5.0,
                                           outdoor_frac, cold, missed, **other)
    qs = sorted(pm_quantiles)
    med = float(np.interp(0.5, qs, [pm_quantiles[q] for q in qs]))
    hi = float(pm_quantiles[qs[-1]])
    zone, reason = choose_zone(r["mean"], base["mean"], med, hi, on)
    cat = int(pm25_to_category(np.array([med]), on)[0])
    msg = render(zone, reason, child_name, day_label, med, hi, r["mean"], cat, language)
    return Plan(zone, reason, r["mean"], r["lo"], r["hi"], med, hi, CATEGORIES[cat], msg)
