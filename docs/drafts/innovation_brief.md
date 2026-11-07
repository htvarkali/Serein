# Innovation Brief draft (UNSENT, team edits welcome)

Status: first draft, 2026-11-01. Nothing here has been submitted. Every `[TEAM: ...]` slot needs a real fact from us before this goes into the Conrad portal. Word limits are from the 2026-27 Student Guide (see `docs/CONRAD.md`); the count after each heading is the limit, not the current length.

Rules for editing this draft:
- All numbers below are **dev results** (2023 held-out weeks). After the final 2024-25 test runs (README "Finishing the proof"), replace them with the final numbers, even if they are worse.
- Maya is an illustrative child from our simulation, not a real patient. Keep saying so, or replace her with a real (consented, anonymized) story from an interview.
- No em dashes, no hype words. Say what we measured.

---

## 1. Elevator pitch (150 words)

When wildfire smoke rolls in, a parent of a child with asthma gets one piece of advice: the same city-wide air quality forecast everyone else gets. That forecast is often a day late and misses most of the worst smoke days.

Serein gives a smoke forecast for each neighborhood, one to three days ahead, and turns it into a plan for one specific child. Our first model corrects NOAA's smoke forecast using what air monitors are measuring right now. Our second model learns from a short daily check-in how much smoke affects that child, then sends the family a green, yellow or red plan in their own language.

On held-out 2023 fire-season days, Serein warned a day ahead on 71% of the days that reached "Unhealthy for Sensitive Groups". EPA's official forecast warned on 46%, and Serein raised fewer false alarms (81 vs. 98).

## 2. Team (150 words)

[TEAM: one line per person: name, grade, school, what they own. Suggested split by task area (README task board A to E):]

- [Name], [grade]: data pipeline (fire, smoke, weather and air monitor data from NASA, NOAA and EPA)
- [Name], [grade]: SmokeCast, the neighborhood forecast model and the backtest
- [Name], [grade]: AirPlan, the personal asthma model and action plans
- [Name], [grade]: science and validation, the backtest protocol and expert reviews
- [Name], [grade]: product and pitch, interviews, business plan and video

[TEAM: one sentence on why us. Example shape: "Three of us live in the Bay Area, where smoke from the 2020 and 2021 fires closed our schools for days" only if it is true. Add any mentor or advisor by name and role once they have agreed.]

## 3. Opportunity (300 words)

About 4.8 million U.S. children have asthma (CDC, 2023). Smoke is a known asthma trigger: in a 2026 study of children in Alameda and Contra Costa counties, each +10 µg/m³ of wildfire smoke PM2.5 raised the risk of an asthma hospital visit that day by about 4% (Sugrue et al., 2026, GeoHealth), and attacks can start a day or two after exposure.

Families already get air quality forecasts, but they have three problems.

First, they are coarse. EPA's AQI forecast covers a whole metro "reporting area", and smoke arrival can be difficult to forecast. In our saved 2023 development evaluation, an AQM-first fallback had next-day RMSE of 11.0 µg/m³. This fallback uses HRRR or persistence when AQM is unavailable.

Second, they ignore what monitors measure right now. The monitors see smoke arrive hours before the next model run, but the forecast a family reads does not use those readings.

Third, the advice is the same for every child. "Unhealthy for sensitive groups" does not tell a parent whether their child is fine at 40 µg/m³ or needs the inhaler at 20. Some children react strongly to smoke and some barely react.

[TEAM: E-1 interviews. Add 2 to 3 sentences with what school nurses and parents actually told us, with counts, e.g. "Of the 6 parents we interviewed, 4 said..." Do not invent quotes.]

The people who act on smoke days are parents, school nurses deciding on recess, and coaches deciding on practice. Each of them needs a forecast for their neighborhood and enough lead time to plan, which is what Serein is built to give.

## 4. Key metrics: how it works, what's new, impact, IP (750 words)

**How it works.** Serein has two models.

SmokeCast forecasts the daily average smoke level (PM2.5) at every air monitor and on a grid covering the western U.S., for today and the next three days. Each morning it reads NOAA's own smoke and air quality forecasts, the weather forecast, satellite smoke plume maps, fire detections and yesterday's readings from about 400 EPA monitors. The model treats the monitors as a network: each monitor's forecast is adjusted using what nearby monitors are seeing. It does not replace NOAA's forecast. It learns how NOAA's forecast tends to be wrong and corrects it. Every forecast comes with a range (for example "about 75, could reach 140"), and we checked that the true value lands inside the 90% range about 90% of the time.

AirPlan prototypes a personal risk estimate using a population prior and per-child symptom history. The app demonstrates it with a synthetic child; its separate six-question check-in form accepts fictional entries and does not yet update that demonstration model. Connecting real histories requires observed exposure data, consent and clinical review. English and Spanish draft messages can be generated, with a public-guidance floor and reminders to follow the child's own clinician-approved asthma plan. Clinical and native-speaker reviews remain open tasks.

**What is new.**
1. Correcting NOAA's smoke forecast with live monitor readings, and checking the result against NOAA and EPA on days the model never saw.
2. Forecasts for places with no monitor. When we hid 20% of monitors from the model, its forecasts at those hidden sites still beat NOAA's (8.5 vs. 11.1 µg/m³ error, one day ahead).
3. A per-child smoke sensitivity estimate from a check-in a parent can finish in under a minute.
[TEAM: verify with a literature search (D-6) that no published tool does all three before keeping "new" claims.]

**Results so far (historical dev mode, 2023 held-out weeks).** Error is RMSE in µg/m³, which gives larger misses more weight. These numbers predate the latest pipeline fixes and require a development rerun before representing the revised system.

| Forecast for | Serein | AQM → HRRR → persistence fallback |
|---|---|---|
| Tomorrow | 7.9 | 11.0 |
| In 2 days | 9.7 | 12.3 |
| In 3 days | 11.4 | 15.5 |

Against EPA's official AQI forecast, one day ahead: Serein had the right AQI category on 87.9% of area-days vs. 82.7% for EPA, and warned on 71% of real "Unhealthy for Sensitive Groups" days vs. 46%, with fewer false alarms (81 vs. 98). Two days ahead it warned on 66% vs. 37%, but with more false alarms (54 vs. 36), which we report as a real tradeoff.

[TEAM: after the final test, replace this table and paragraph with 2024-25 results, and keep the 2023 numbers only as "development".]

**Impact.** In those 2023 test weeks alone, warning a day ahead, Serein caught 61 more smoky area-days than EPA's forecast, days on which a family would have had time to keep a child inside, run an air purifier and keep the inhaler close. In our AirPlan simulation of 300 children, after 100 logged days the personal model predicted symptom days better than the average-child model, most of all for very smoke-sensitive children (10% better Brier score). [TEAM: these are simulated children. Replace or add real-world evidence if a clinician pilot happens.]

**IP protection.** [TEAM decision needed. Facts: our code is public on GitHub. Options to discuss: (a) keep the forecasting code open so health departments can trust and audit it, and protect the name and brand (trademark search on "Serein"); (b) move the trained models and the AirPlan service to a private repository; (c) talk to a mentor about whether a provisional patent on the per-child method is worth it. Our main advantage beyond code is the validated backtest and partnerships with school districts.]

## 5. Validation and progress (450 words)

**What we built.** A working pipeline that downloads five fire seasons (2021 to 2025) of free public data from NOAA, NASA and EPA, trains SmokeCast, scores it, and draws forecast maps. A demo app shows the neighborhood map, a family's plan and the daily check-in. The project has automated tests that run on every change.

**Evaluation plan.** The draft protocol (docs/BACKTEST_PROTOCOL.md) reserves 2024-25 for a final test after the team freezes the methods. That final test has not run. Development trains on 2021-22 and uses 2023 for tuning and scoring. Availability cutoffs are enforced using documented posting-lag assumptions; historical availability still needs an audit. Comparisons use archived forecasts for paired places and days.

**What the tests showed (development weeks of 2023).**
- One day ahead, Serein's RMSE was 7.9 µg/m³ vs. 11.0 for the AQM-first fallback.
- It warned on 71% of "Unhealthy for Sensitive Groups" days vs. 46% for EPA, with fewer false alarms.
- With 20% of monitors hidden, it still beat NOAA at the hidden sites, so it can forecast for neighborhoods with no monitor.
- We removed one input at a time to see what matters. Without NOAA's HRRR smoke and weather forecasts, tomorrow's error got 29% worse. Without live monitor readings, today's error got 66% worse. Wind direction between monitors, which we expected to help, made no difference, and satellite fire detections helped only a little (1-4%). We report both.

[TEAM: final test results, 2024-25. Run once as a team. Paste the headline numbers here.]

[TEAM: out-of-region test. The Northeast June 2023 Canadian smoke event, trained only on the West. Report whatever it shows.]

**Expert and user feedback.**
[TEAM: C-8. Name, role and one-sentence takeaway from a pediatric pulmonologist, allergist, school nurse or respiratory therapist who reviewed the action plans. Only after they agree to be named.]
[TEAM: C-7. Native Spanish speaker review of the Spanish messages.]
[TEAM: E-1. Interview count and the one change we made because of what we heard.]

**Next steps before the Summit.** Add PurpleAir's low-cost sensors in two test metros (Sacramento and Portland) to see how much denser sensors help, add more languages, and run a small opt-in pilot of the check-in with families, with a clinician advising. [TEAM: confirm the pilot plan and ethics review with an adult advisor before writing it here. See docs/ETHICS.md.]

## 6. Market (300 words)

[TEAM: E-4. Fill each with a sourced number. Suggested sources in brackets.]

Who benefits: families of children with asthma in smoke-affected states (about 4.8 million U.S. children with asthma, CDC 2023; [TEAM: share living in western states, CDC state asthma data]).

Who pays, in order of how likely we think they are:
1. School districts, which decide on recess, sports and closures on smoke days. [TEAM: number of districts in CA, OR, WA; NCES]
2. Medicaid managed care plans and children's hospitals with asthma programs, which pay for emergency visits we aim to prevent. [TEAM: average cost of a pediatric asthma ED visit, with source]
3. Local air districts and health departments that already send smoke advisories. [TEAM: count of air districts, e.g. 35 in California per CARB]

[TEAM: one sentence on market size, computed bottom-up: number of districts times our price, not a "billion-dollar market" headline.]

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

## 8. Go-to-market (150 words)

[TEAM: E-4 and E-7.] Start with one partner that already acts on smoke days: a school district or school nurse group in a smoke-affected area. Serein sends their nurses a neighborhood forecast each morning in fire season and gives families a free sign-up link for AirPlan. Success in the first season is measured in two numbers: how many smoke days the district got warned on in advance, and how many families kept logging after 30 days.

[TEAM: name any district, nurse, air district or clinic that has agreed to talk, and attach letters of support if we get them (E-7).]

## 9. Business model (300 words)

[TEAM: E-4. Draft shape below; replace bracketed numbers with researched ones.]

Families never pay. Organizations that make decisions on smoke days pay a yearly subscription for the neighborhood forecast, alerts and a dashboard.

- School districts: [TEAM: price per district per year, and why that price; compare with what districts pay for other safety tools].
- Health plans and children's hospitals: per-enrolled-child pricing for AirPlan, justified by avoided emergency visits. [TEAM: show the break-even: how many avoided ED visits per 1,000 children pay for the service.]
- Air districts and health departments: a license to embed the forecast in their existing alerts.

Costs: all input data is free public data from NOAA, NASA and EPA. Running the daily forecast for the whole western U.S. takes [TEAM: measure: minutes of compute per day on one cloud GPU or CPU, times cloud price] plus hosting and text-message costs for families. [TEAM: add PurpleAir data fees if we use their sensors commercially.]

## 10. Fundraising (150 words)

[TEAM: E-4.] What we need to reach the Summit and a first pilot: [TEAM: list items with dollar amounts: Conrad fee ($499, or financial aid), cloud hosting for one fire season, text-message costs, PurpleAir data access, translation review.] Where it comes from: [TEAM: sponsors, school or district grants, science fair prizes, a crowdfunding page]. After the pilot, the first paying customer funds the next season.

---

## References (attachment)

[TEAM: copy the full citations from docs/METHODS.md (priors table) and docs/DATA.md (data sources). At minimum:]
- CDC (2023). Most recent national asthma data, children under 18.
- Sugrue et al. (2026). GeoHealth 10(2):e2025GH001530. Wildfire PM2.5 and pediatric asthma hospital encounters.
- Khetsuriani et al. (2007). Viral infections and asthma exacerbations in children.
- Williams et al. (2011). J Allergy Clin Immunol 128:1185. Inhaled corticosteroid adherence and asthma exacerbations.
- Barkjohn, Gantt and Clements (2021). U.S.-wide correction for PurpleAir PM2.5 sensors.
- U.S. EPA (2024). Updated AQI breakpoints for PM2.5.
- NOAA: HRRR-Smoke, AQM (NAQFC) and Hazard Mapping System smoke product documentation.

## Optional attachments (up to 2)
1. `docs/results/figures/` rmse-by-lead chart (Serein vs. NOAA vs. EPA).
2. The August 2023 neighborhood forecast map or an app screenshot.
