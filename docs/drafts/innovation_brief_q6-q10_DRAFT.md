# Innovation Brief, questions 6 to 10: sourced draft (UNSENT, team review needed)

Status: draft, 2026-11-07, written from `docs/BUSINESS_NUMBERS_2026-11-07.md` and
`docs/COMPETITOR_VERIFICATION_2026-11-07.md`. Every number has a source in those two
files. Word counts are within the Student Guide limits (counted with the script at
the bottom). `[TEAM: ...]` slots still need a real fact from us. No em dashes, no hype
words, say what we measured.

Replaces the placeholder text for sections 6 to 10 in `innovation_brief.md`. Sections
1 to 5 are unchanged.

---

## 6. Market (300 words) [draft: 298 words]

**Who benefits.** About 4.8 million US children under 18 have current asthma (CDC, 2023 NHIS), including an estimated 548,709 in California, 26,594 in Oregon and 83,411 in Washington (CDC, 2023 NSCH); across the western states, roughly 0.9 to 1.1 million. Each year US children make about 374,000 asthma emergency visits and 61,000 hospital stays (CDC, 2023), at a mean hospital cost of $7,464 per stay (Gabbay et al., 2025). Smoke makes this worse: in San Diego, each 10 µg/m³ of wildfire PM2.5 raised pediatric respiratory emergency and urgent-care visits about 30% (Aguilera et al., 2021); in Washington, asthma emergency visits rose 4% to 12% on smoke days (WA OFM); in Oregon they rose about 25% during the 2020 Labor Day fires (OHA, 2025).

**Who pays.** Three buyer groups already spend money acting on smoke days.

1. School districts: 935 in California, 197 in Oregon, 295 in Washington (1,427; state education agencies, 2026), 13,303 nationally (NCES, 2023-24). Districts already buy safety and messaging tools: one district's ParentSquare contract was $69,913 for 2024-25; Raptor emergency software runs about $2,095 per school building per year.
2. Medicaid managed care plans and children's hospitals: 4.4 million California, 463,000 Oregon and 810,000 Washington children are enrolled in Medicaid or CHIP (KFF, July 2026). Medi-Cal reimburses asthma self-management education at $26.66 per 30-minute unit. In 2025-26 UW Medicine texted smoke guidance to 64,000 asthma and COPD patients using neighborhood-level pollution data; 14% engaged.
3. Air districts and health departments: the Bay Area district alone budgets $1.95 million a year for Spare the Air advertising and alerts.

**Bottom-up size.** At $5,000 per district per year, the 1,427 districts in our three states are a $7.1 million annual market; 70 districts (5%) within three years is $350,000 a year. [TEAM: adjust once the first interviews tell us which districts actually make smoke-day decisions.]

## 7. Competition (300 words)

Existing services cover substantial parts of our idea. Sources were checked
November 7, 2026; the [verification record](../COMPETITOR_VERIFICATION_2026-11-07.md)
distinguishes advertised features from tested performance.

| Alternative | Documented offering or status |
|---|---|
| EPA AirNow | Reporting-area AQI forecasts, one to six days where available; Fire and Smoke Map adds monitors, corrected sensors and local smoke outlooks. |
| NOAA HRRR-Smoke / AQM | Selected HRRR cycles reach 48 hours; AQM reaches 72 hours and includes monitor-informed bias correction. |
| PurpleAir / ExactAQ | Sensor observations also feed ExactAQ's 48-hour forecasts, including estimates between monitors. |
| IQAir AirVisual | Advertises seven-day forecasts, alerts and exposure advice. |
| Google / Apple | Google's API documents 500 m, 96-hour forecasts and sensitive-group advice. Apple names BreezoMeter for US air quality; its AQI horizon is not established by that source. |
| AirRater | Australian environmental forecasts, symptom-trigger learning and alerts; its developer explicitly includes caregivers of children. |
| Propeller Health / EPA Smoke Sense | Historical inhaler tracking and citizen-science symptom research, respectively. Resmed says Propeller ceased operations; EPA retains an app-unavailability notice for Smoke Sense. |
| Research | Liao et al. (2025) forecast PM2.5 with a graph network; Wang et al. (2020 preprint) combine sparse observations and smoke-model forecasts for dense predictions. AGATNet already applies graph attention to forecast correction. |

**Our proposed emphasis** is reproducible daily smoke-forecast evaluation,
uncertainty ranges, and a caregiver check-in linked to a family plan. These are
design choices to test, not a claim that the combination is unique. Our current
family demonstration uses simulated children. Accuracy, interval coverage and
usefulness require their own evaluation; competitor features and research results
do not validate Serein. Pilot workflow and distribution remain team decisions.

## 8. Go-to-market (150 words) [draft: 124 words]

Start with one partner that already acts on smoke days: a school district or school-nurse group in a smoke-affected part of California, Oregon or Washington. Serein sends its nurses a neighborhood forecast each morning of fire season and gives families a free sign-up link for AirPlan, alongside the AirNow Flag Program many schools already run. Precedent that organizations will do this: UW Medicine reached 64,000 patients with neighborhood smoke guidance in 2025 and renewed for 2026, and Ventura County already texts farmworkers smoke alerts in English and Spanish. First-season success is two numbers: how many smoke days the district was warned about a day ahead, and how many families still log after 30 days. A clinician reviews every message before any family sees it. [TEAM: name any district, nurse, clinic or air district that has agreed to talk; attach letters of support (E-7).]

## 9. Business model (300 words) [draft: 270 words]

Families never pay. Organizations that make decisions on smoke days pay a yearly subscription for the neighborhood forecast, alerts and a dashboard; the personal plan rides along free.

**Pricing, anchored to what buyers already pay.**

- School districts: $500 to $1,000 per school building per year, or about $0.50 to $1.50 per student, with a $1,500 floor. That is a quarter to half of one Raptor emergency-software license ($2,095 per building) and 7% to 21% of one observed ParentSquare contract ($69,913). A 10,000-student district pays $5,000 to $15,000 a year.
- Health plans and children's hospitals: $10 to $20 per enrolled child with asthma per year, less than one Medi-Cal asthma-education unit ($26.66 per 30 minutes). A child asthma hospitalization costs $7,464, so one avoided stay funds 370 to 750 child-years of Serein. We do not yet have evidence that Serein avoids visits; a pilot would measure it.
- Air districts and health departments: a license to embed the forecast in alerts they already send.

**Costs.** All inputs are free public data from NOAA, NASA and EPA. [TEAM: paste the measured median seconds per issue day and the hardware from `outputs/timing/`.] A T4 GPU costs $0.53 an hour on demand, so a daily forecast for the western US costs cents a day, and a small web host is $7 to $25 a month. Text alerts cost about $0.013 per SMS part; our messages fit in one or two parts, so 60 smoke-day alerts to 1,000 families cost about $1,100 a season. WhatsApp utility messages cost $0.0034 each. PurpleAir sensor history, if added, costs about $1 to $5 per sensor-year. At the prices above, compute and messaging together stay under 10% of revenue.

## 10. Fundraising (150 words) [draft: 131 words]

To reach the Summit and run one pilot season we need about $3,000 to $5,000: the $499 Conrad fee (or financial aid), $65 for a provisional patent (micro-entity) and $350 for a trademark application on the name, about $300 for a fire season of hosting, roughly $1,100 of text messages for 1,000 families, $500 for native-speaker and translation review, and travel. Sources: Conrad's prize partners (1517 Fund has given Scholar teams $1,000 plus $10,000 in AWS credits), the Davidson Fellows Scholarship (deadline February 17, 2027), small rolling seed grants such as The Pollination Project, in-kind sensors or data from an air district or PurpleAir, and a crowdfunding page. Federal environmental-justice grants are not realistically available in 2026-27. After the pilot, the first paying district funds the next season. [TEAM: confirm 1517 Fund and AWS are still 2026-27 prize partners.]

---

## Competition claims to carry into later revisions

The [E-5 source check](../COMPETITOR_VERIFICATION_2026-11-07.md) supersedes the
previous “first/only” wording and missing-feature table. Neither a narrower
first-in-the-US claim nor “no product combines these layers” is established.
AirRater includes caregiver use; ExactAQ uses PurpleAir for forecasts; AQM has
monitor-informed bias correction. The cited forecast evaluation supports reporting
multiple decision metrics and persistence, not “persistence beats every model.”
Use dated availability notices for Propeller and Smoke Sense; do not assume a
scheduled NOAA rollout has occurred. Other sections' market, pricing, clinical
and delivery claims remain outside this Q7 check and need separate review.

## Word-count script

```bash
python3 - <<'EOF'
import re
t=open('docs/drafts/innovation_brief_q6-q10_DRAFT.md').read()
for n,h in [(6,'## 6.'),(7,'## 7.'),(8,'## 8.'),(9,'## 9.'),(10,'## 10.')]:
    s=t.index(h); e=t.index('\n## ',s+1) if n<10 else t.index('\n---',s)
    body=t[s:e].split('\n',1)[1]
    body=re.sub(r'\[TEAM:.*?\]','',body,flags=re.S)       # TEAM notes are not submitted
    body=re.sub(r'^\|[-| ]+\|$','',body,flags=re.M)         # table rule lines
    words=re.findall(r"[A-Za-z0-9$%µ³/.,'-]+",body.replace('|',' '))
    print(n,len(words))
EOF
```
