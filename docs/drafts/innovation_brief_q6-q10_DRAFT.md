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

**Bottom-up size.** Public schools in the three states enroll 7.4 million students (fall 2025): $3.7 to $11.1 million a year at $0.50 to $1.50 per student. Seventy 10,000-student districts (5%) at the low price is $350,000 a year. [TEAM: adjust once the first interviews tell us which districts actually make smoke-day decisions.]

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

## 8. Go-to-market (150 words) [draft: 149 words]

Start with one partner that already acts on smoke days: a school district or school-nurse group in a smoke-affected part of California, Oregon or Washington. Serein sends its nurses a neighborhood forecast by midday each day of fire season and gives families a free sign-up link for AirPlan, alongside the AirNow Flag Program many schools already run. Precedent: UW Medicine texted neighborhood smoke guidance to 64,000 patients in 2025 and renewed for 2026, and Ventura County texts farmworkers smoke alerts in English and Spanish. First-season success is two numbers: how many smoke days the district was warned about a day ahead, and how many families still log after 30 days. A clinician reviews every message before any family sees it. At $5,000 to $15,000 a year, a subscription is far below California's $119,100 threshold for formal bidding on district services (2026), so state law does not require a bid. [TEAM: name any district, nurse, clinic or air district that has agreed to talk; attach letters of support (E-7).]

## 9. Business model (300 words) [draft: 292 words]

Families never pay. Organizations that make decisions on smoke days pay a yearly subscription for the neighborhood forecast, alerts and a dashboard; the personal plan rides along free.

**Pricing, anchored to what buyers already pay.**

- School districts: $500 to $1,000 per school building per year, or about $0.50 to $1.50 per student, with a $1,500 floor. That is a quarter to half of one Raptor emergency-software license ($2,095 per building) and 7% to 21% of one observed ParentSquare contract ($69,913). A 10,000-student district pays $5,000 to $15,000 a year.
- Health plans and children's hospitals: $10 to $20 per enrolled child with asthma per year, less than one Medi-Cal asthma-education unit ($26.66 per 30 minutes). A child asthma hospitalization costs $7,464, so one avoided stay funds 370 to 750 child-years of Serein. We do not yet have evidence that Serein avoids visits; a pilot would measure it.
- Air districts and health departments: a license to embed the forecast in alerts they already send.

**Costs.** All inputs are free public data from NOAA, NASA and EPA. Running the trained model (all 5 ensemble members, 425 western monitors) takes 0.016 seconds per forecast day on a desktop CPU (median of 20 runs, measured 2026-11-23); downloading NOAA's daily files takes longer and was not timed. No GPU is needed to forecast, so a small web host at $7 to $25 a month covers it. Text alerts cost about $0.013 per SMS part and our messages fit in one or two parts, so a heavy season of 60 alerts costs about $1.13 per family ($1,100 for 1,000 families), or $0.20 by WhatsApp. By SMS that is 5% to 15% of a district's fee if every child with asthma enrolls, and 6% to 11% of a health plan's. [TEAM: these shares are computed in `src/serein/business.py` and tested; rerun `python -m serein.business` if a price changes.]

## 10. Fundraising (150 words) [draft: 124 words]

To reach the Summit and run one pilot season we need about $3,000 to $5,000: the $499 Conrad fee (or financial aid), $65 for a provisional patent (micro-entity) and $350 for a trademark application on the name, about $300 for a fire season of hosting, roughly $1,100 of text messages for 1,000 families, $500 for native-speaker and translation review, and travel. Sources: Conrad's financial aid for the fee (applications close December 3, 2026), the Davidson Fellows Scholarship (deadline February 17, 2027), small rolling seed grants such as The Pollination Project, in-kind sensors or data from an air district or PurpleAir, and a crowdfunding page. Federal environmental-justice grants are not realistically available in 2026-27. After the pilot, the first paying district funds the next season. [TEAM: say whether we applied for financial aid. The earlier line about 1517 Fund and AWS prizes was removed: Conrad's 2026 awards page names neither.]

---

## Status note (2026-11-08, updated 2026-11-25)

Sections 8, 9 and 10 here were brought back in line with `innovation_brief.md` on
2026-11-25 (bidding threshold in 8, messaging cost shares in 9, financial aid in 10;
see `brief_review_2026-11-25.md`). Count every Brief section with
`python3 scripts/check_brief.py`.

Sections 6, 8, 9 and 10 below were merged into `innovation_brief.md` on 2026-11-08.
Section 7 in the brief is the E-5 rewrite by Kwilier (merged 2026-11-07), which is the
version of record. This file stays as the sourced working copy.

## Alternative closing paragraph for Q7 (team decision)

The Innovation criterion (30%) asks judges "Is it unique?" A closing paragraph that
says we make no uniqueness claim answers that question for them. The version in the
brief is accurate; the version below is equally accurate and answers the rubric. Pick
one at the next meeting. Every statement in it is a report of what the E-5 check found,
not a guarantee.

> **What we found, and what we are testing.** Each layer of Serein exists somewhere:
> Google fuses monitors and smoke models at 500 m; NOAA's AQM bias-corrects with
> monitors; AirRater in Australia learns a user's triggers from check-ins, including
> for caregivers. In our search we did not find a US service that publishes its skill
> against the official forecast and persistence on held-out fire seasons, reports
> calibrated ranges, and turns that forecast into a per-child plan a family can act on
> the night before. That combination is what we built and what we are testing; our
> family model is still evaluated on simulated children, and the competitors' features
> do not validate ours.

(About 120 words; replaces the 75-word "Our proposed emphasis" paragraph, keeping Q7
under 300.)

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
