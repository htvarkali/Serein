# Innovation Brief draft (UNSENT, team edits welcome)

Status: first draft, 2026-11-01; development numbers updated 2026-11-23 to the rerun on the current pipeline; Smoke World, equity, recalibration and hourly results added 2026-11-23. Sections 4 (IP, prior work), 8, 9 and 10 updated 2026-11-25; what changed and a shorter section 5 are in `docs/drafts/brief_review_2026-11-25.md`. Section 5 is over its 450-word limit before the final numbers and feedback go in: check every section with `python3 scripts/check_brief.py`. Nothing here has been submitted. Every `[TEAM: ...]` slot needs a real fact from us before this goes into the Conrad portal. Word limits are from the 2026-27 Student Guide (see `docs/CONRAD.md`); the count after each heading is the limit, not the current length.

Rules for editing this draft:
- All numbers below are **dev results** (2023 held-out weeks). After the final 2024-25 test runs (README "Finishing the proof"), replace them with the final numbers, even if they are worse.
- Maya is an illustrative child from our simulation, not a real patient. Keep saying so, or replace her with a real (consented, anonymized) story from an interview.
- No em dashes, no hype words. Say what we measured.

---

## 1. Elevator pitch (150 words)

When wildfire smoke rolls in, a parent of a child with asthma gets one piece of advice: the same city-wide air quality forecast everyone else gets. That forecast is often a day late and misses most of the worst smoke days.

Serein gives a smoke forecast for each neighborhood, one to three days ahead, and turns it into a plan for one specific child. Our first model corrects NOAA's smoke forecast using what air monitors are measuring right now. Our second model learns from a short daily check-in how much smoke affects that child, then sends the family a green, yellow or red plan in their own language.

On held-out 2023 fire-season days, Serein warned a day ahead on 72% of the days that reached "Unhealthy for Sensitive Groups". EPA's official forecast warned on 46%, and Serein raised fewer false alarms (92 vs. 98).

## 2. Team (150 words)

- Aadi Tiwari, 11th grade, Foothill High School: data pipeline, the SmokeCast forecast model, the AirPlan personal asthma model, and the backtest protocol
- Harshateja Varkali, 11th grade, Foothill High School: website, sensor quality checks and forecast reliability
- Abhinav Garg, 12th grade, Foothill High School: business model, market research and IP
- Arush Kudaraya, 11th grade, Foothill High School: forecast context for family plans (ozone, heat, pollen) and competitor research
- Jagath Prabath, 11th grade, Foothill High School: [TEAM: his role, written only once he has done the work]

Advisor: [TEAM: name and role, once they have agreed]

[TEAM: one sentence on why us. Example shape: "Three of us live in the Bay Area, where smoke from the 2020 and 2021 fires closed our schools for days" only if it is true.]

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

**What is new.** Each piece has related work; the combination is what we did not find published.
1. A graph network over the U.S. monitor network that corrects NOAA's HRRR-Smoke and AQM forecasts, scored on held-out days against EPA's official AQI forecasts. NOAA has corrected its own PM2.5 forecast with past analogs (Huang et al., 2017) and with machine learning that does not use a graph (Hamer et al., 2023), machine learning without a graph has corrected HRRR-Smoke in Alaska using PurpleAir sensors (Dong et al., 2026), a graph network has corrected the CMAQ model's PM2.5 forecasts in South Korea (Dimri et al., 2024), and another has forecast California PM2.5 without NOAA inputs or an official comparison (Liao et al., 2025).
2. A measured check at places with no monitor. When we hid 20% of monitors from the model, its forecasts there still beat NOAA's (8.5 vs. 11.1 µg/m³ error, one day ahead). Grid forecasts already exist (for example Google's Air Quality API); what we add is evidence of accuracy away from monitors.
3. A per-child smoke sensitivity estimate from a check-in a parent can finish in under a minute. A hierarchical model lets a child with few reports borrow from the group, and the estimate sets that child's green, yellow and red plan. Apps such as AirRater already log symptoms and personal triggers; we add an uncertainty-aware estimate tied to a smoke forecast.
[TEAM: literature search done 2026-11-23 (notes in docs/drafts/novelty_check_2026-11-23.md). Dong et al. 2026 is reference 36, checked against NOAA's publication record on 2026-11-07. Dimri et al. 2024 (reference 52): the abstract was read 2026-11-25 and matches the sentence above (183 Korean monitors, 72 hours, no comparison with an official forecast); the publisher's page would not load for us on 2026-11-26, so someone still has to open the full text in a browser before submitting.]

**Results so far (development mode, 2023 held-out weeks, rerun 2026-11-23 on the current pipeline).** Error is RMSE in µg/m³, which gives larger misses more weight.

| Forecast for | Serein | AQM → HRRR → persistence fallback |
|---|---|---|
| Tomorrow | 7.8 | 11.0 |
| In 2 days | 9.7 | 12.3 |
| In 3 days | 11.6 | 15.5 |

Against EPA's official AQI forecast, one day ahead: Serein had the right AQI category on 88.1% of area-days vs. 82.7% for EPA, and warned on 72% of real "Unhealthy for Sensitive Groups" days vs. 46%, with fewer false alarms (92 vs. 98). Two days ahead it warned on 62% vs. 37%, but with more false alarms (48 vs. 36), which we report as a real tradeoff.

[TEAM: after the final test, replace this table and paragraph with 2024-25 results, and keep the 2023 numbers only as "development".]

**Impact.** In those 2023 test weeks alone, warning a day ahead, Serein caught 63 more smoky area-days than EPA's forecast, days on which a family would have had time to keep a child inside, run an air purifier and keep the inhaler close. In our AirPlan simulation of 300 children, after 100 logged days the personal model predicted symptom days better than the average-child model, most of all for very smoke-sensitive children (10% better Brier score). [TEAM: these are simulated children. Replace or add real-world evidence if a clinician pilot happens.]

**IP protection.** Our code is open source (MIT) so health departments and judges can audit it; for a product that advises parents about children, trust is worth more than secrecy. We will file a U.S. provisional patent application on the combined system (the monitor-corrected neighborhood forecast with calibrated ranges, the rule that only data available at issue time is used, and the per-child sensitivity model whose plan can only be stricter than public guidance) before the Summit, as the rules require of finalists. The parts that are hard to copy are a published head-to-head test against the official forecast, which we found no consumer air-quality product offering, the partnerships a pilot builds, and the check-in data, which is never published. [TEAM: confirm this choice (option A in docs/drafts/ip_decision_memo.md) at the next meeting, and add one line on the name once a full trademark search is done.]

## 5. Validation and progress (450 words)

**What we built.** Smoke World (htvarkali.github.io/Serein), a public 3D map of the western U.S. that updates daily with the next 72 hours of smoke, wind and fires, shows the tested daily forecast and its range for any place clicked, and counts how many people live under unhealthy smoke. Behind it, a pipeline downloads five fire seasons (2021-2025) of free NOAA, NASA and EPA data, then trains, scores and maps SmokeCast. A demo app shows a family's plan and the daily check-in; automated tests run on every change.

**Evaluation plan.** The draft protocol (docs/BACKTEST_PROTOCOL.md) reserves 2024-25 for one final test after the methods are frozen; it has not run. Development trains on 2021-22 and tunes and scores on 2023. Forecasts use only data posted before issue time; the posting lags still need a historical audit. Comparisons pair archived forecasts by place and day.

**What the tests showed (development weeks of 2023).**
- One day ahead, Serein's RMSE was 7.8 µg/m³ vs. 11.0 for the AQM-first fallback and 13.8 for persistence (yesterday's reading carried forward). A 2026 BAMS study found persistence matched or beat operational smoke models for day-level decisions; Serein's warning skill a day ahead was 0.53 vs. 0.26 for persistence (critical success index, USG or worse).
- It warned on 72% of "Unhealthy for Sensitive Groups" days vs. 46% for EPA, with fewer false alarms.
- With 20% of monitors hidden, it beat NOAA at the hidden sites in every distance band (8.5 vs. 11.1 µg/m³ a day ahead), so it can serve neighborhoods with no monitor. In the lowest-income fifth of western neighborhoods, 10.8% of people live 25 km or more from any EPA monitor, vs. 0.6% in the highest-income fifth (Census ACS 2019-2023; docs/EQUITY.md).
- Warning probabilities were recalibrated: a stated 60% chance of an unhealthy day comes true about 60% of the time. A low-confidence flag marks the largest misses.
- Hour by hour, Serein beat NOAA on days 0-2, but neither could tell which hours would be worst and a flat daily value was as accurate, so our advice is per day (docs/HOURLY_ACCURACY.md).
- Twelve model changes failed our fixed acceptance test (more seasons, fire growth, satellite smoke, more ensemble members, a separate network for days 2-3), and five blends did no better (all logged in docs/EXPERIMENTS.md).
- Removing inputs one at a time: without HRRR, tomorrow's error rose 29%; without live monitors, today's rose 66%; wind direction between monitors added nothing; fire detections helped 1-4%.

[TEAM: final test results, 2024-25. Run once as a team. Paste the headline numbers here.]

[TEAM: out-of-region test. The Northeast June 2023 Canadian smoke event, trained only on the West. Report whatever it shows.]

**Expert and user feedback.**
[TEAM: C-8. Name, role and one-sentence takeaway from a pediatric pulmonologist, allergist, school nurse or respiratory therapist who reviewed the action plans. Only after they agree to be named.]
[TEAM: C-7. Native Spanish speaker review of the Spanish messages.]
[TEAM: E-1. Interview count and the one change we made because of what we heard.]

**Next steps before the Summit.** Add PurpleAir sensors in two test metros (Sacramento and Portland) to measure how much denser sensors help, add languages, and run a small opt-in pilot of the check-in with families, with a clinician advising. [TEAM: confirm the pilot plan and ethics review with an adult advisor before writing it here. See docs/ETHICS.md.]

## 6. Market (300 words)

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

## 8. Go-to-market (150 words)

Start with one partner that already acts on smoke days: a school district or school-nurse group in a smoke-affected part of California, Oregon or Washington. Serein sends its nurses a neighborhood forecast by midday each day of fire season and gives families a free sign-up link for AirPlan, alongside the AirNow Flag Program many schools already run. Precedent: UW Medicine texted neighborhood smoke guidance to 64,000 patients in 2025 and renewed for 2026, and Ventura County texts farmworkers smoke alerts in English and Spanish. First-season success is two numbers: how many smoke days the district was warned about a day ahead, and how many families still log after 30 days. A clinician reviews every message before any family sees it. At $5,000 to $15,000 a year, a subscription is far below California's $119,100 threshold for formal bidding on district services (2026), so state law does not require a bid. [TEAM: name any district, nurse, clinic or air district that has agreed to talk; attach letters of support (E-7).]


## 9. Business model (300 words)

Families never pay. Organizations that make decisions on smoke days pay a yearly subscription for the neighborhood forecast, alerts and a dashboard; the personal plan rides along free.

**Pricing, anchored to what buyers already pay.**

- School districts: $500 to $1,000 per school building per year, or about $0.50 to $1.50 per student, with a $1,500 floor. That is a quarter to half of one Raptor emergency-software license ($2,095 per building) and 7% to 21% of one observed ParentSquare contract ($69,913). A 10,000-student district pays $5,000 to $15,000 a year.
- Health plans and children's hospitals: $10 to $20 per enrolled child with asthma per year, less than one Medi-Cal asthma-education unit ($26.66 per 30 minutes). A child asthma hospitalization costs $7,464, so one avoided stay funds 370 to 750 child-years of Serein. We do not yet have evidence that Serein avoids visits; a pilot would measure it.
- Air districts and health departments: a license to embed the forecast in alerts they already send.

**Costs.** All inputs are free public data from NOAA, NASA and EPA. Running the trained model (all 5 ensemble members, 425 western monitors) takes 0.016 seconds per forecast day on a desktop CPU (median of 20 runs, measured 2026-11-23); downloading NOAA's daily files takes longer and was not timed. No GPU is needed to forecast, so a small web host at $7 to $25 a month covers it. Text alerts cost about $0.013 per SMS part and our messages fit in one or two parts, so a heavy season of 60 alerts costs about $1.13 per family ($1,100 for 1,000 families), or $0.20 by WhatsApp. By SMS that is 5% to 15% of a district's fee if every child with asthma enrolls, and 6% to 11% of a health plan's. [TEAM: these shares are computed in `src/serein/business.py` and tested; rerun `python -m serein.business` if a price changes.]


## 10. Fundraising (150 words)

To reach the Summit and run one pilot season we need about $3,000 to $5,000: the $499 Conrad fee (or financial aid), $65 for a provisional patent (micro-entity) and $350 for a trademark application on the name, about $300 for a fire season of hosting, roughly $1,100 of text messages for 1,000 families, $500 for native-speaker and translation review, and travel. Sources: Conrad's financial aid for the fee (applications close December 3, 2026), the Davidson Fellows Scholarship (deadline February 17, 2027), small rolling seed grants such as The Pollination Project, in-kind sensors or data from an air district or PurpleAir, and a crowdfunding page. Federal environmental-justice grants are not realistically available in 2026-27. After the pilot, the first paying district funds the next season. [TEAM: say whether we applied for financial aid. The earlier line about 1517 Fund and AWS prizes was removed: Conrad's 2026 awards page names neither.]


---

## References (attachment)

The full, checked reference list is `docs/drafts/references_DRAFT.md` (draft 3, every entry checked 2026-11-23 against Crossref, PubMed or the source page). Before submitting, keep only the references the final text cites, renumber them in citation order, and recheck the links the day before. Two `[TEAM]` items are left in it: the CDC page that defines "not well controlled", and the list of AI tools we used, which Conrad's rules require us to cite. The Gabbay data source and the Conrad prize line were settled 2026-11-25.

## Optional attachments (up to 2)
1. `docs/results/figures/` rmse-by-lead chart (Serein vs. NOAA vs. EPA).
2. The August 2023 neighborhood forecast map or an app screenshot.
