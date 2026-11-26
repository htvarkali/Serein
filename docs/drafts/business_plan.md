# Business plan draft (task E-6)

Draft of 2026-11-25, for team review. It turns Brief sections 6 to 10 into one plan a
judge or a partner can read from start to finish. Nothing in it has been agreed with a
customer. The rules of the other drafts apply: no number without a source, scenarios are
labeled as scenarios, and every `[TEAM: ...]` slot needs a real fact from us.

Where the numbers come from:

- Prices and counts: [BUSINESS_NUMBERS_2026-11-07.md](../BUSINESS_NUMBERS_2026-11-07.md)
  and [BUSINESS_MODEL_EVIDENCE.md](../BUSINESS_MODEL_EVIDENCE.md).
- Arithmetic: `src/serein/business.py`, checked by `tests/test_business.py`. Rerun the
  scenario table with `uv run python -m serein.business --out docs/drafts/business_scenarios.csv`.
- New sources in this draft (rules for outdoor work, the school bidding threshold,
  Conrad dates, trademark records) are listed at the end with the date they were read.

## 1. The plan in one paragraph

Families never pay. Serein sells a yearly subscription to organizations that already
have to act on smoke days: a neighborhood smoke forecast one to three days ahead, a
warning when a day is likely to be unhealthy for sensitive groups, and a free personal
plan for each family that signs up. The first customer we want is one school district
in a smoke-affected part of California, Oregon or Washington, served free for the 2027
fire season as a pilot. The pilot answers the two questions this plan cannot: whether a
district changes what it does when it gets an earlier warning, and whether families keep
logging. Paid subscriptions start the year after, only if the pilot shows both.

## 2. Who uses it and who pays

The child and the parent benefit. Someone else pays. Each buyer below is a separate
sale with a separate reason to buy, and we have evidence of spending for each, but no
buyer has been interviewed yet (task E-1).

| Buyer | What they already do or spend | What they would buy from us | Evidence we still need |
|---|---|---|---|
| School districts (935 in California, 197 in Oregon, 295 in Washington) | Decide on recess, sports and closures on smoke days; buy safety and messaging tools ($2,095 per building a year for one emergency system; one $69,913 messaging contract) | Morning forecast by school, a day-ahead warning, a sign-up link for families | Who makes the smoke-day call, and whether a day of notice changes it |
| Medicaid plans and children's hospitals | Medi-Cal pays $26.66 per 30 minutes of asthma education; UW Medicine texted smoke guidance to 64,000 patients in 2025-26 and renewed | The personal plan for enrolled children with asthma | A pilot that measures visits; we have no evidence yet that Serein avoids any |
| Air districts and health departments | The Bay Area district budgets $1.95 million a year for Spare the Air outreach | A license to put the forecast in alerts they already send | Whether they would publish a forecast that differs from EPA's |
| Employers with outdoor crews | Must act under state smoke rules (below) | The crew outlook: a planning forecast for the next three days, in English and a draft Spanish | Any conversation with a farm, a contractor or a labor contractor |

### Outdoor work: a buyer the Brief does not mention yet

The crew outlook was built on 2026-11-23 (`src/serein/crew.py`, the app's crew tab). All
three West Coast states have a workplace wildfire smoke rule that tells employers to
watch air quality; California's and Oregon's say at the start of each shift.

| State | Rule | Applies from | What the employer must check |
|---|---|---|---|
| California | Title 8, section 5141.1 | Current AQI for PM2.5 of 151 or more | Exposure "at the start of each shift and periodically thereafter"; two of the three allowed methods are checking "AQI forecasts and the current AQI" from listed government sources |
| Oregon | OAR 437-002-1081 (in effect since July 1, 2022) | PM2.5 of 35.5 µg/m³ (AQI 101) | Monitoring "at the start of each shift, and as needed"; one allowed method is the current and forecasted AQI from Oregon DEQ, AirNow, the interagency smoke program "or equivalent source" |
| Washington | Chapter 296-820 WAC | Planning duties at every level; notices from 20.5 µg/m³, controls from 35.5 | "Watch the PM2.5 conditions and forecasts"; the state says employers may use smoke forecasts to plan ahead |

Two things follow, and both limit what we can claim.

1. Oregon's rule and Washington's exposure controls start at 35.5 µg/m³, the same level
   SmokeCast's warning is scored on. California's starts higher, at AQI 151 (55.5 µg/m³ as a daily
   average), which the crew outlook reports as a separate chance.
2. The rules name government sources for the required check, and California's is about
   the current AQI. Serein forecasts the daily average a day or more ahead. So the crew
   outlook is for planning (ordering N95s, moving heavy work, rescheduling a crew). It
   does not replace the check the rule requires, and every outlook says so.

Size, as far as public numbers go: California's agricultural employment averaged 407,700
in 2023 (California EDD). We did not find comparable counts for Oregon and Washington, or
for construction and utility crews, so we do not total this market. [TEAM: decide whether
this buyer goes into Brief Q6. It costs words there, and we have talked to no employer.]

## 3. Product and price

Prices are set against what these buyers already pay, as in Brief Q9.

| Buyer | Price | Anchor |
|---|---|---|
| School district | $0.50 to $1.50 per student a year, $1,500 minimum (a 10,000-student district pays $5,000 to $15,000) | A quarter to half of one Raptor building license; 7% to 21% of one observed ParentSquare contract |
| Health plan or hospital | $10 to $20 per enrolled child with asthma a year | Less than one Medi-Cal asthma-education unit ($26.66) |
| Air district or health department | Yearly license, price not set | None found; no public contract for smoke alerts alone |
| Outdoor employer | Not set | None found |

For a health plan, one avoided hospital stay ($7,464 mean hospital cost in 2022) equals
373 child-years of Serein at $20 and 746 at $10. That is a comparison of prices. It is
not a claim that Serein avoids stays.

## 4. What it costs us

All forecast inputs are free public data. Running the trained model takes 0.016 seconds
per forecast day on a desktop CPU (median of 20 runs, 2026-11-23), so one small web host
($7 to $25 a month) covers the whole western U.S. however many customers there are.

Messaging is the cost that grows with use. In a heavy season of 60 alerts, one family
costs about $1.13 by SMS (1.5 message parts at $0.0125 each) or $0.20 by WhatsApp.

| | SMS cost as a share of the yearly fee (60 alerts) |
|---|---|
| District at $0.50 per student, every child with asthma enrolled | 15% |
| District at $1.00 per student, every child enrolled | 8% |
| District at $1.50 per student, every child enrolled | 5% |
| Health plan at $10 per child | 11% |
| Health plan at $20 per child | 6% |

"Every child with asthma" means 6.7% of students, the national rate (CDC, 2023), so 670
families in a 10,000-student district. At the lowest district price, SMS stays at or under
10% of the fee as long as no more than two thirds of those families enroll; by WhatsApp
it is under 3% in every row. The Brief's earlier sentence, that compute and messaging
stay under 10% of revenue at our prices, was too broad and is corrected in Q9.

What the cost side leaves out, because we have no sourced number for it: our own time
(nobody on the team is paid), customer support, insurance, forming a legal entity, and
the carrier registration fees for bulk texting. Insurance, a legal entity and carrier
registration have to be priced before the first paid year.

## 5. Three-year scenarios

These are assumptions about how many districts sign, chosen to bracket the outcome.
They are not forecasts. Each district has 10,000 students, pays $5,000 (the low end of
the range), and 30% of its children with asthma enroll. "Net before pay" is revenue
minus messaging, hosting and translation review, before paying any person.

| Scenario | School year | Paying districts | Free pilots | Families | Revenue | Costs | Net before pay |
|---|---|---|---|---|---|---|---|
| Low | 2027-28 | 0 | 1 | 201 | $0 | $1,026 | -$1,026 |
| Low | 2028-29 | 1 | 1 | 402 | $5,000 | $1,252 | $3,748 |
| Low | 2029-30 | 3 | 0 | 603 | $15,000 | $1,478 | $13,522 |
| Base | 2027-28 | 0 | 1 | 201 | $0 | $1,026 | -$1,026 |
| Base | 2028-29 | 3 | 1 | 804 | $15,000 | $2,204 | $12,796 |
| Base | 2029-30 | 10 | 0 | 2,010 | $50,000 | $3,561 | $46,439 |
| High | 2027-28 | 1 | 1 | 402 | $5,000 | $1,252 | $3,748 |
| High | 2028-29 | 15 | 0 | 3,015 | $75,000 | $4,692 | $70,308 |
| High | 2029-30 | 70 | 0 | 14,070 | $350,000 | $17,629 | $332,371 |

How to read it:

- The high case ends at the 70 districts in Brief Q6 (5% of the 1,427 in the three
  states). For five students with no sales history that is a ceiling. The base case is
  the one to say out loud.
- Costs are small in every row because the data is free and the model is cheap to run.
  The limit is people: the table has no salaries, and ten districts need someone
  to answer the phone during fire season.
- In the low and base cases the first year costs about $1,000 and brings in nothing.
  Brief Q10's request covers that, the one-time costs below, and travel.

## 6. How we reach the first customer

1. **Now to January:** five parent interviews, two school nurses and one clinician
   (E-1, C-8). The interview guide is in `docs/interviews/` and the clinician request is in this
   folder. The
   question for a nurse or district is the one in section 2: who decides, and would a
   day of notice change the decision.
2. **January to April:** ask one district or school-nurse group for a free pilot, using
   [pilot_partner_email.md](pilot_partner_email.md) and the pilot protocol in
   `docs/pilot/`. A clinician reviews every message before a family sees one.
3. **Fire season 2027:** run the pilot. Report two numbers: smoke days warned a day
   ahead, and families still logging after 30 days.
4. **After the season:** a paid renewal with that district, and two more districts.

Why a district can say yes quickly: in California, formal competitive bidding is
required for a district's purchases of services above $119,100 (the 2026 threshold,
Public Contract Code 20111). A $5,000 to $15,000 subscription is far below it. A
district's own purchasing policy still applies and may require quotes or board
approval at lower amounts. [TEAM: ask the first district what its own limit is.]
California districts adopt their budgets by July 1 (Education Code 42127), so a renewal
has to be asked for in spring, before the season it pays for.

## 7. Money we need and where it could come from

One-time, before the Summit: the $499 Conrad fee, $65 for the provisional patent the
rules require of U.S. finalists (micro entity), and $350 for one class of trademark
application if we keep the name, $914 in all. A pilot season adds about $1,026 (first
row of the table). With travel, the Brief's $3,000 to $5,000 still holds.

| Source | Amount | Status on 2026-11-25 |
|---|---|---|
| Conrad financial aid for the $499 fee | Not stated on the page | **Applications close December 3, 2026.** One form per team; there is also a group or school discount. [TEAM: decide this week] |
| Davidson Fellows Scholarship | $25,000 to $100,000 | Open to individuals or teams of two, age 18 or under, so not to all five of us together; deadline February 17, 2027; outline in [davidson_fellows_outline.md](davidson_fellows_outline.md) |
| The Pollination Project seed grant | Up to about $1,000 | Rolling; amount not confirmed |
| In-kind sensor data from PurpleAir or an air district | Data, not cash | Request drafted, not sent (D-3) |
| First paying district | $5,000 or more | After the pilot |

Removed from the Brief: the line that Conrad's prize partners give $1,000 and AWS
credits. Conrad's 2026 awards page names no 1517 Fund or AWS prize, and the 2024-25 list we
first read them on is no longer online, so we cannot cite it.

## 8. Risks, and what would change this plan

| Risk | What we know | What we would do |
|---|---|---|
| A district does not act differently with a day of notice | Not tested | The pilot's first number. If the answer is no, the district sale is wrong and the health-plan sale becomes the plan |
| Families stop logging | Not tested | The pilot's second number. The forecast and warning still work without the check-in |
| A free product is good enough | AirNow and its Flag Program are free; Google forecasts 96 hours at 500 m | We publish our accuracy against the official forecast and did not find the same from the free products; that only matters if a buyer cares, which the interviews will show |
| A child is harmed after following a plan | A plan can only be stricter than EPA guidance and always points to the child's own doctor | Clinician review before any family sees a message; no real families before consent and review (docs/ETHICS.md). [TEAM: ask an adult advisor about insurance before a pilot] |
| Children's health data | The check-in holds a child's symptoms | No real entries today. [TEAM: ask an advisor which privacy laws apply before the pilot; we have not checked] |
| The final test comes out worse | 2024-25 has not been scored | We report it either way and re-price nothing until it is in |
| The name | See the [IP memo](ip_decision_memo.md): a USPTO word search on 2026-11-26 found no live mark containing "serein" in the software or health classes; live SEREIN registrations elsewhere include e-cigarettes and children's car seats | Decide whether to keep the name before the video is filmed. A live SERENE registration (Polar Electro) covers health-related software and sensors in the same classes, so ask an attorney before paying to register "Serein" |

## 9. Dates

| Date | What |
|---|---|
| December 3, 2026 | Conrad financial aid applications close (11:59 pm; the event page says ET, the calendar says CST, so treat the earlier one as the deadline) |
| December 10, 2026 | Conrad workshop: "Innovation Insight: Communicating your Idea", 4 to 5 pm CST |
| January 1, 2027 | Our own deadline for the Brief, video and website |
| January 7, 2027 | Conrad deadline and $499 payment, 11:59 pm CST |
| February 17, 2027 | Davidson Fellows deadline |
| February 26, 2027 | Conrad finalists announced |
| April 21 to 24, 2027 | Innovation Summit, Space Center Houston |
| Spring 2027 | Ask a district for the pilot, before its July 1 budget |

## 10. Decisions the team has to make

1. Apply for Conrad financial aid by December 3, or pay the fee.
2. Whether outdoor employers go into the Brief as a fourth buyer (section 2).
3. The district price to say out loud: $0.50, $1.00 or $1.50 per student.
4. Whether to keep the name Serein (IP memo) before the video and website are final.
5. Who makes the first three calls for interviews, and by what date.

## Sources added in this draft (read 2026-11-25)

- California Code of Regulations, Title 8, section 5141.1, Protection from Wildfire Smoke. https://www.dir.ca.gov/title8/5141_1.html
- Oregon Administrative Rules 437-002-1081, Protection from Wildfire Smoke. https://www.law.cornell.edu/regulations/oregon/Or-Admin-Code-SS-437-002-1081
- Washington Department of Labor and Industries. Wildfire smoke (chapter 296-820 WAC). https://www.lni.wa.gov/safety-health/safety-topics/topics/wildfire-smoke
- California EDD. California Agricultural Employment, 2023 annual average (state total 407,700). https://labormarketinfo.edd.ca.gov/file/agric/ca-ag-employ-map-2023.pdf
- Lozano Smith. 2025 (December 10). Bid Thresholds Raised For 2026 ($119,100 for K-12 purchases of equipment, materials, supplies and services other than construction). https://lozanosmith.com/news-clientnewsbriefdetail.php?news_id=3451
- California Education Code section 42127 (district budgets adopted on or before July 1). https://california.public.law/codes/education_code_section_42127
- Conrad Challenge. Phase 2: Innovation Stage (dates, fee, financial aid). https://conrad.spacecenter.org/the-challenge/innovation-stage/
- Conrad Challenge. Financial Aid Opens for Phase 2: Innovation Stage. https://conrad.spacecenter.org/calendar/financial-aid-opens-for-phase-2-innovation-stage-2/
- Conrad Challenge. 2026 Conrad Challenge Innovation Summit Awards. https://conrad.spacecenter.org/2026-awards/
- USPTO. Trademark fee information ($350 per class; page updated November 4, 2026). https://www.uspto.gov/trademarks/trademark-fee-information
- USPTO TSDR status records for serial numbers 90636402 and 98444557. https://tsdr.uspto.gov/
