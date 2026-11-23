"""Outdoor-crew smoke outlook: Serein's forecast turned into a shift plan.

California's wildfire smoke rule (Title 8, section 5141.1) applies when the *current*
AQI for PM2.5 is 151 or more, and tells employers to check AQI forecasts and the
current AQI at the start of each shift. Serein forecasts the *daily average*, which is
lower than the worst hours, so this outlook is for planning days ahead. It never
replaces the current-AQI check the rule requires.

Rule text used here (dir.ca.gov/title8/5141_1.html, read 2026-11-23):
- AQI 151 and above: engineering controls where feasible; if not enough, relocate work,
  change schedules, reduce intensity or add rest; give N95s for voluntary use.
- AQI above 500: respirator use is required.

Spanish text is a draft and needs native-speaker review before anyone relies on it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from serein.aqi import CATEGORIES, pm25_to_aqi
from serein.models.gnn import QUANTILES

UNHEALTHY_SENSITIVE = 35.5  # daily PM2.5 at AQI 101
RULE_LEVEL = 55.5  # daily PM2.5 at AQI 151 (2024 scale), the rule's trigger level
QUANTILE_COLUMNS = ("q05", "q25", "q50", "q75", "q95")

TEXT = {
    "en": {
        "check": "Check the current AQI at the start of each shift (AirNow or your air district), as the rule requires.",
        "clear": "No smoke action expected. Keep checking the current AQI.",
        "watch": "Smoke possible. Have N95s on site and a plan to move work or change hours.",
        "plan": "Plan for smoke: schedule heavy work early, add rest breaks, have N95s ready for every worker.",
        "severe": "Very heavy smoke possible. Plan indoor or filtered work; respirators are required if the current AQI tops 500.",
        "low_confidence": "Low confidence: this forecast is less certain than usual. Check again tomorrow.",
    },
    "es": {
        "check": "Revise el AQI actual al inicio de cada turno (AirNow o su distrito del aire), como exige la norma.",
        "clear": "No se espera tomar medidas por humo. Siga revisando el AQI actual.",
        "watch": "Posible humo. Tenga mascarillas N95 en el sitio y un plan para mover el trabajo o cambiar el horario.",
        "plan": "Prepárese para el humo: programe el trabajo pesado temprano, agregue descansos y tenga N95 para cada trabajador.",
        "severe": "Posible humo muy denso. Planee trabajo bajo techo o con aire filtrado; si el AQI actual pasa de 500, el respirador es obligatorio.",
        "low_confidence": "Confianza baja: este pronóstico es menos seguro de lo normal. Vuelva a revisar mañana.",
    },
}
SPANISH_IS_DRAFT = True


@dataclass
class Outlook:
    lead: int
    median: float
    low: float
    high: float
    category: str
    p_unhealthy_sensitive: float
    p_rule_level: float
    low_confidence: bool
    action: str
    notes: list[str] = field(default_factory=list)


def chance_above(quantiles: np.ndarray, threshold: float) -> float:
    """P(daily PM2.5 >= threshold) from the 5 forecast quantiles (µg/m³), same rule as the backtest."""
    from serein.eval.backtest import prob_exceed

    q = np.log1p(np.clip(np.asarray(quantiles, float), 0, None))[None, :]
    return float(prob_exceed(q, QUANTILES, thr=threshold)[0])


def recalibrate(p: float, recal: dict | None, lead: int) -> float:
    """Apply the calibration-row isotonic map saved with the run (prob_recal.json)."""
    if not recal or str(lead) not in recal or not np.isfinite(p):
        return p
    m = recal[str(lead)]
    return float(np.interp(p, m["x"], m["y"]))


def outlook(
    quantiles,
    lead: int,
    recal: dict | None = None,
    flag_width: dict | None = None,
    lang: str = "en",
) -> Outlook:
    q = np.clip(np.asarray(quantiles, float), 0, None)
    text = TEXT[lang]
    p_usg = recalibrate(chance_above(q, UNHEALTHY_SENSITIVE), recal, lead)
    # The recalibration map was fit for the 35.5 event only. A daily average at the rule
    # level (55.5) is also above 35.5, so its chance can never be higher.
    p_rule = min(chance_above(q, RULE_LEVEL), p_usg)
    width = np.log1p(q[-1]) - np.log1p(q[0])
    limit = (flag_width or {}).get("log_width", {}).get(str(lead))
    low_conf = bool(limit is not None and width >= limit)
    aqi = float(pm25_to_aqi(q[2]))
    category = CATEGORIES[min(int(np.searchsorted([51, 101, 151, 201, 301], aqi, side="right")), 5)]
    if q[4] >= 325.5:
        action = text["severe"]
    elif p_rule >= 0.3 or q[2] >= RULE_LEVEL:
        action = text["plan"]
    elif p_usg >= 0.3 or q[4] >= RULE_LEVEL:
        action = text["watch"]
    else:
        action = text["clear"]
    notes = [text["check"]]
    if low_conf:
        notes.insert(0, text["low_confidence"])
    return Outlook(
        lead=lead,
        median=float(q[2]),
        low=float(q[0]),
        high=float(q[4]),
        category=category,
        p_unhealthy_sensitive=p_usg,
        p_rule_level=p_rule,
        low_confidence=low_conf,
        action=action,
        notes=notes,
    )
