# Pitch deck: slide text and speaker notes (task E-6)

Written 2026-11-26 for the eight-minute Summit pitch. Twelve slides. The deck itself is a
slide file kept by Abhinav, who can share it or export it as PowerPoint or PDF; this page
is the text of each slide and what to say, so the team can review it here.

- Every number is a development result from the README section "Current results
  (development rerun, 2026-11-23)" and must be replaced after the final test.
- The picture on slide 5 is `website/img/world-preview.png` (the forecast issued
  August 18, 2023).
- Colors and the typeface (Poppins) follow the website.
- `[Jagath: his part]` on the last slide is still open, as in Brief section 2.

## 1. Serein

On the slide:

- CONRAD CHALLENGE 2026-27
- A day’s notice before a smoke day, for every neighborhood and every child with asthma.
- Falcon Devs · Foothill High School, Pleasanton, California
- Aadi Tiwari · Harshateja Varkali · Abhinav Garg · Arush Kudaraya · Jagath Prabath

Say: 0:00 to 0:20. Say the name the way we pronounce it, then one sentence: tomorrow’s smoke forecast is for your whole city; Serein tells a parent what it means for their neighborhood and their child, a day ahead. Do not explain the model here. Every number in this deck is a development result from 2023 until the final test is run; replace them afterwards.

## 2. One forecast for the whole city, one piece of advice for every child

On the slide:

- THE PROBLEM
- 4.8M
- U.S. children have asthma (CDC, 2023)
- +4%
- higher risk of an asthma hospital visit that day for each extra 10 µg/m³ of wildfire smoke (Sugrue et al., 2026)
- 46%
- of unhealthy smoke days were warned about a day ahead by EPA’s official forecast in our 2023 test weeks

Say: 0:20 to 1:05. Start with one family. Maya is an example child from our simulation, not a real patient; say so. Her parent gets the same metro-wide forecast as everyone else and the same line, “unhealthy for sensitive groups.” Then the three numbers. The 4% is from a 2026 study of children in Alameda and Contra Costa counties, which is where we live. The 46% is EPA’s official forecast on the 2023 weeks we scored: it warned a day ahead on fewer than half of the days that turned unhealthy for sensitive groups.

## 3. Three gaps in the forecast a family reads today

On the slide:

- WHY IT HAPPENS
- 1 · COARSE
- It covers a whole metro area
- EPA’s AQI forecast is issued for a reporting area, not for a neighborhood.
- 2 · BLIND TO LIVE DATA
- It ignores what monitors see
- About 400 EPA monitors in the West measure smoke as it arrives. The forecast does not use them.
- 3 · ONE SIZE
- Same advice for every child
- It does not say whether your child is fine at 40 µg/m³ or needs the inhaler at 20.

Say: 1:05 to 1:45. One sentence per gap. Coarse: a reporting area can be a whole metro region, and smoke reaches one side hours before the other. Live data: the monitors see smoke arrive before the next model run, but the forecast a family reads is not corrected with them. One size: some children react strongly to smoke and some barely react, and the public advice cannot tell them apart. Each gap is one thing Serein does.

## 4. Two models: a forecast, then a plan

On the slide:

- WHAT SEREIN IS
- Public data
- NOAA’s smoke and weather forecasts, fire detections, and live readings from about 400 EPA monitors
- SmokeCast
- A graph network over the monitors corrects NOAA’s forecast, one to three days ahead
- Neighborhood forecast
- A level for each day with a range: “about 75, could reach 140”
- AirPlan
- Turns the forecast into a green, yellow or red plan for one child
- We do not replace NOAA’s forecast. We learn how it tends to be wrong and correct it.
- A plan can be stricter than EPA’s public guidance, never looser, and it always points to the child’s own doctor.

Say: 1:45 to 2:35. Walk left to right. All inputs are free public data. SmokeCast treats the monitors as a network: each monitor’s forecast is adjusted using what its neighbors are seeing, which is also how a place with no monitor gets a forecast. Every forecast has a range, and the real value lands inside the 90% range about 90% of the time. AirPlan is built to learn one child’s sensitivity from a six-tap check-in. Be exact here: today it is tested on 300 simulated children, and the check-in form in the app does not yet feed the model. Say “graph neural network” once.

## 5. A live 3D map anyone can open

On the slide:

- THE PROTOTYPE
- Smoke World updates each day with the next 72 hours of smoke, wind and fires.
- Click any place for its daily forecast and range.
- Switch between NOAA’s forecast and ours.
- Shown: the forecast issued August 18, 2023. The hour-by-hour motion comes from NOAA. Neither forecast could tell which hours of a day would be worst, so our advice is per day.
- [Picture: Smoke World showing the Pacific Northwest on August 19, 2023, with smoke shaded by air quality category over Washington and Oregon, wind lines, fire points and a time slider]

Say: 2:35 to 3:20. If the room has internet, switch to the live site here and fly to a town the judges know; otherwise use this picture. Press play, click a place, show the range, flip between NOAA and Serein. Then say the limit before anyone asks: the motion you see hour by hour is NOAA’s. We tested it against real hourly readings and neither forecast could tell which hours of a day would be worst, so Serein gives a level per day.

## 6. A day ahead, Serein warned on more of the unhealthy days

On the slide:

- PROOF · WARNINGS
- Serein
- 72%
- EPA’s official forecast
- 46%
- Share of the 244 area-days that reached Unhealthy for Sensitive Groups or worse and were warned about one day ahead. Held-out weeks of 2023.
- False alarms a day ahead: 92 for Serein, 98 for EPA.
- Two days ahead we still warn on more days (62% against 37%), with more false alarms (48 against 36).

Say: 3:20 to 4:05. How we tested: train on 2021 and 2022, score on fire-season weeks of 2023 the model never saw, against the forecast EPA actually issued for the same places and days. One day ahead we warned on 72% of the days that turned unhealthy for sensitive groups; EPA’s official forecast warned on 46%, and we raised fewer false alarms, 92 against 98. Then say the tradeoff yourself: two days ahead we catch more days but with more false alarms than EPA. These are development results. The final test on 2024 and 2025 has not been run.

## 7. Lower error at every lead, and where there is no monitor

On the slide:

- PROOF · ACCURACY
- Error (RMSE, µg/m³)
- Tomorrow
- In 2 days
- In 3 days
- Serein
- 7.8
- 9.7
- 11.6
- NOAA fallback
- 11.0
- 12.3
- 15.5
- Serein, at monitors hidden from it
- 8.4
- 9.9
- 11.4
- NOAA, at those same monitors
- 11.1
- 11.9
- 14.1
- In the lowest-income fifth of western neighborhoods, 10.8% of people live 25 km or more from an EPA monitor. In the highest-income fifth, 0.6%.

Say: 4:05 to 4:45. Error is in micrograms per cubic meter; lower is better. The NOAA fallback is the best NOAA forecast available for that day: its air quality model first, then HRRR, then yesterday’s reading. We beat it at every lead. The lower two rows are the test we care most about: we hid one monitor in five from the model, to stand in for a neighborhood with no monitor, and it still beat NOAA there. That matters for fairness, because the people farthest from a monitor are far more often in low-income neighborhoods: about one in ten in the lowest-income fifth, fewer than one in a hundred in the highest.

## 8. Four limits we report ourselves

On the slide:

- WHAT WE DO NOT KNOW YET
- The final test is not run
- Every result here is from 2023. The 2024 and 2025 seasons are kept for one final test.
- Peaks come in low
- A day ahead we forecast a median 76% of a smoky day’s true level. Three days ahead, 29%.
- No real children yet
- The personal model is tested on 300 simulated children. A pilot needs consent, a clinician and an ethics review.
- No customer yet
- No district, health plan or employer has been interviewed. That comes before any sale.
- Nine attempts to improve accuracy failed our acceptance test. All nine are in our public log.

Say: 4:45 to 5:30. This slide is on purpose. Judges score practicality on whether a team knows its own limits. One: the numbers so far are development results; the final test runs once, after the method is frozen, and we will report it whatever it shows. Two: we still forecast big smoke days too low, though less than NOAA, which reaches 31% a day ahead. Three: the child model has never met a real child. Four: nobody has agreed to pay. And we kept every failed experiment: nine runs marked as failing our own acceptance rule, with one change that passed.

## 9. Who pays: families never do

On the slide:

- BUSINESS MODEL
- Buyer
- Our price
- What they already pay
- School districts
- $0.50 to $1.50 per student a year
- $2,095 per building a year for one emergency system
- Health plans and children’s hospitals
- $10 to $20 per child with asthma a year
- $26.66 per 30 minutes of asthma education (Medi-Cal)
- Air districts and health departments
- A yearly license, not priced yet
- $1.95 million a year for Spare the Air outreach (Bay Area)
- Prices are proposals set against public contracts. No buyer has been interviewed yet.

Say: 5:30 to 6:10. Families never pay. The organizations that already have to act on smoke days pay a yearly subscription, and the family plan rides along free. A 10,000-student district would pay $5,000 to $15,000, which is a quarter to half of what one district pays per building for emergency software. A health plan would pay less per child than one asthma-education visit. Be straight: these are our proposals, anchored to contracts we found in public records, and nobody has been asked yet. If a judge asks about employers: California, Oregon and Washington have smoke rules for outdoor work, and we built a planning outlook for crews, but we have not spoken to an employer.

## 10. What it costs to run

On the slide:

- COSTS
- $0
- for data: every input is free and public, from NOAA, NASA and EPA
- 16 ms
- to run the trained model for one forecast day on a desktop computer
- $1.13
- per family in a heavy season of 60 text alerts, or $0.20 by WhatsApp
- Third-year scenarios, not forecasts: 3, 10 or 70 paying districts at $5,000 each.
- What this leaves out: our own time. None of us is paid.

Say: 6:10 to 6:45. Three numbers. The data is free. The model for the whole West runs in 16 thousandths of a second on an ordinary computer, so a small web host at $7 to $25 a month is enough. The cost that grows with use is text messages: about a dollar thirteen per family in a heavy season, which is 5 to 15 percent of a district’s fee if every child with asthma enrolls. Our plan shows three scenarios for year three; seventy districts is 5% of the districts in California, Oregon and Washington and is a ceiling, not a prediction. The first year is one free pilot. What the costs leave out is people.

## 11. One district, one fire season, two numbers

On the slide:

- THE PLAN
- NOW
- Listen first
- Interviews with parents, school nurses and a clinician, before we build further.
- SPRING 2027
- Ask for a pilot
- One district, free. A clinician reviews every message before a family sees it.
- FIRE SEASON 2027
- Measure
- Smoke days warned about a day ahead, and families still logging after 30 days.
- AFTER
- Renew and grow
- A paid renewal with that district, then two more.
- What we need: about $3,000 to $5,000, one district willing to try it, and a clinician to review the plans.

Say: 6:45 to 7:30. The pilot answers the two questions we cannot answer from a desk: does a district do anything differently with a day of notice, and do families keep logging. If the first answer is no, the district is the wrong first customer and we go to health plans. Nothing reaches a real family before a clinician has reviewed the wording and an ethics board has approved the study. The money covers the Conrad fee, the provisional patent finalists must file, hosting, a season of text messages for a pilot, and translation review. [Add here: any district, nurse or clinician who has agreed to talk, once that is true.]

## 12. Kids with asthma shouldn’t find out about smoke from a cough.

On the slide:

- SEREIN
- Falcon Devs · Foothill High School, Pleasanton, California
- htvarkali.github.io/Serein

Say: 7:30 to 8:00. Each of us says in one sentence what we built: Aadi, the data pipeline and both models; Harshateja, the website and the sensor checks; Arush, the ozone, heat and pollen inputs and the competitor research; Abhinav, the business model; [Jagath: his part]. Then the last line on the slide, and stop. For questions, the prepared answers are in docs/drafts/judge_qa_prep.md.

Notes total about 1,130 words, which is close to eight minutes if read in full. They are
prompts, not a script: put them in your own words, and cut enough to leave a minute for
the live demonstration on slide 5.
