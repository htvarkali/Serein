# Judge Q&A preparation (for online judge coaching and the Summit)

Written 2026-11-08; revised 2026-11-25 to the November 23 development rerun, with
new questions on Smoke World, the hourly test, failed experiments and outdoor work.
Online judges leave written coaching in February; finalists face 8 minutes on stage
plus 20 minutes of questions. Every team member should be able to give each answer
below in their own words without notes.

Where the numbers come from: the README section "Current results (development rerun,
2026-11-23)" and the docs named in each answer. `docs/results/` holds the same
November 23 rerun (re-exported 2026-11-27). Everything is replaced after the final
test.

Rule for every answer: say the number, say the limitation, say the next step. Judges
score Practicality on whether we know our own error bars.

## About the forecast

**1. Why not just use Google's air quality forecast? It's 500 m and 96 hours.**
Google's API is good and we say so in the Brief. Three things its overview page does
not do: publish how accurate it is against the official forecast on smoke days, give a
range, and tell a family what to do for their specific child. We measured ours: on
held-out 2023 days, one day ahead, our error was 7.8 µg/m³ against 11.0 for the NOAA
fallback and 13.8 for persistence. We have not tested Google's forecast against ours,
so we do not claim to beat it.

**2. A 2026 paper found persistence is hard to beat for day-level decisions. Why
should we believe yours is different?**
We take that paper seriously, which is why persistence is one of our scored baselines.
One day ahead on 2023 held-out days, our warning skill for "unhealthy for sensitive
groups" was 0.53 against 0.26 for persistence (critical success index), and our error
was 7.8 against 13.8 µg/m³. The difference comes from using the live monitor readings
with NOAA's forecast. Our final 2024-25 test, run once under a frozen protocol, will
say whether that holds.

**3. Why a graph neural network? Isn't that overkill?**
We tested that. The same model with the graph turned off has higher error at every
lead (8.2 against 7.8 one day ahead), and the gap is largest where there is no sensor:
at monitors we hid from the model, the graph cut today's error by 18% and day 3's by
17%. The graph is how a neighborhood without a monitor borrows from its neighbors.

**4. What are your false alarm rates?**
One day ahead we had fewer false alarms than EPA's official forecast (92 against 98)
while warning on more real days (72% against 46%). Two days ahead we warn on more days
(62% against 37%) but with more false alarms (48 against 36). We report that as a
tradeoff, and we tune the warning cut-off on calibration weeks, not test weeks.

**5. Do you under-forecast the worst days?**
Yes, less than NOAA does. On smoky days our day-ahead forecast reaches a median 76% of
the true level; NOAA's reaches 31%. At two and three days we reach 55% and 29%. Two
fixes we tried on November 23 did not help, and both are in the experiment log.

**6. How do you know you didn't peek at the future?**
The issue time is 11:30 a.m. Pacific. The code uses only data that had posted by then,
with posting times we measured from the archive timestamps; the rule is in
`serein/data/availability.py` and is tested. A full audit of historical posting times
is still open. EPA's own forecasts are issued after our issue time, which favors EPA
in the comparison.

**7. What happens when NOAA changes its models?**
NOAA's new RRFS system was scheduled to go live on November 3, 2026 (Service Change
Notice 26-48). That notice retires the NAM, HREF, SREF and HiResW models; it does not
retire HRRR, which still feeds the new ensemble. We have not confirmed the switch
happened on that date, and the notice does not list smoke fields. Our model corrects
whatever NOAA runs, so a new input means a new data loader and a retrain, and we would
rerun the backtest before trusting it.

**8. Where does it work? Only the West?**
Trained and scored on the western U.S. We built an out-of-region test on the June 2023
Canadian smoke event in the Northeast, trained only on the West, and will report
whatever it shows right after the final test.

**9. Your map moves hour by hour. Is the hourly forecast accurate?**
The hour-by-hour motion in Smoke World comes from NOAA's hourly forecast, scaled to our
daily level. We tested it against real hourly monitor readings: our values beat NOAA's
hour by hour on days 0 to 2, but neither could tell which hours of a day would be
worst, and a flat daily value was as accurate. So our advice is per day, not per hour,
and the site says so (`docs/HOURLY_ACCURACY.md`).

**10. What did you try that failed?**
A lot, and we wrote each one down before running it. The experiment log has twelve
runs marked as failing our acceptance rule as of November 27: a different point
forecast, heavier weighting of smoky days, training on the error in µg/m³, a separate
network for days 2-3, fire growth, partial-day inputs, smoke-cover history, an extra
training season, satellite smoke haze, temporary fire monitors twice, and ten ensemble
members in place of five. One change passed: recalibrating the warning probabilities.
We keep the failures because they show the acceptance rule is real
(`docs/EXPERIMENTS.md`).

**11. Does it work where there is no monitor, and who lives there?**
With one monitor in five hidden, our day-ahead error at the hidden sites was 8.5
against NOAA's 11.1, and we were ahead in every distance band, though the farthest
band has only 3 sites. In the lowest-income fifth of western neighborhoods, 10.8% of
people live 25 km or more from an EPA monitor; in the highest-income fifth, 0.6%
(`docs/EQUITY.md`).

## About the child model and safety

**12. Who is liable when a parent follows your plan and the child has an attack?**
Serein is not a medical device and does not diagnose or change medication. Two rules
are enforced in code and tested: a plan can only be stricter than EPA's public
guidance, never looser, and every message tells the family to follow their own
clinician's asthma action plan and lists emergency signs. [After C-8: "Our messages
were reviewed by (role, affiliation), who asked us to change X."] Before any real
family uses it we would run an opt-in pilot with a clinician advising and written
parental consent, and we would ask an adult advisor about insurance first.

**13. Have you tested the personal model on real children?**
No. It is tested on 300 simulated children, where it recovers each child's true
sensitivity and beats a one-size-fits-all model after about two weeks of logs. The
check-in form in the app takes fictional entries and does not yet feed that model
(screenshots of the plan and the check-in: `docs/demo/README.md`). The
starting assumptions come from published studies (Sugrue 2026, Khetsuriani 2007,
Williams 2011). A real pilot needs consent, a clinician and ethics review; that is our
first step after the Summit, not before.

**14. Why would a parent keep doing a check-in every night?**
We do not know yet; that is the second number our pilot measures (families still
logging at 30 days). The check-in is six taps. [After E-1: "Of N parents we
interviewed, K said they would, and the thing that would make them stop was Y."]

**15. What about kids whose families don't speak English or Spanish?**
Messages are in English and Spanish today; the Spanish is drafted and waiting for a
native-speaker review. More languages come only after a review process exists,
because we will not machine-translate health instructions.

## About the business

**16. Who actually pays, and have you talked to them?**
Families never pay. Districts, health plans and air districts do. [After E-1: name
the interviews. Until then the honest answer is "not yet."] Evidence they already
spend on this: a district pays about $2,095 per building a year for emergency
software; the Bay Area air district budgets $1.95 million a year for Spare the Air
outreach; UW Medicine texted smoke guidance to 64,000 patients in 2025 and renewed.

**17. What does it cost you to run?**
All input data is free from NOAA, NASA and EPA. The trained model takes 0.016 seconds
per forecast day on a desktop CPU, so a small web host at $7 to $25 a month is enough.
The cost that grows is text messages: about $1.13 per family in a heavy season of 60
alerts, or $0.20 by WhatsApp. By SMS that is 5% to 15% of a district's fee if every
child with asthma enrolls. What we have not priced is people: none of us is paid.

**18. How many customers do you expect?**
We do not have a forecast, because no district has been asked. Our plan shows three
scenarios for the third year: 3, 10 and 70 paying districts. Seventy is 5% of the
1,427 districts in California, Oregon and Washington and is a ceiling. The first year
is one free pilot (`docs/drafts/business_plan.md`). If every district in the three
states bought, it would be $3.7 to $11.1 million a year: 7.4 million students at $0.50
to $1.50 each. We say that as the size of the market, not as what we expect to win.

**19. Could employers use this? Some states have smoke rules for outdoor work.**
California, Oregon and Washington all have one. California's and Oregon's tell
employers to check air quality at the start of each shift, and Oregon's rule and
Washington's exposure controls start at 35.5 µg/m³, the level our warning is scored on. We built a crew outlook for planning days
ahead, in English and a draft Spanish. It does not replace the check the rule requires, which
is of current conditions from government sources, and we have not spoken to an
employer yet.

**20. What stops a competitor from copying you? Your code is public.**
The code is open on purpose, so health departments can audit a product that advises
parents about children. What is hard to copy is a published head-to-head test against the
official forecast, the partnerships a pilot builds, and the check-in data, which is
never published. We will file a provisional patent on the combined system before the
Summit, as the rules require of finalists. [After E-8: the decision on the name.]

**21. Is the name yours?**
We searched the U.S. trademark records on November 26, 2026. Thirty marks contain
"serein" and 13 are live, none of them in the software or health-service classes; an
earlier application there was abandoned in 2023. Live SEREIN registrations cover
unrelated goods such as e-cigarettes and children's car seats. We also searched the
similar-sounding "serene": one live SERENE registration, owned by a fitness-watch
company, covers health-related software and sensors, so we would ask an attorney
before filing. We have not filed. [Update after the team decides.]

**22. Did students really build this? It's a lot of code.**
Yes, and each of us can walk you through our part. [Each member: one sentence on what
they built and one decision they made and why.] We used AI coding assistants and we
cite them in our reference list; the model design, the backtest protocol, the decision
to report where we lose, and the safety rules are ours. [TEAM: this answer is only
true once the reference list names the tools. Conrad's rules say a submission "may not
copy or use other materials- including artificial intelligence (AI) tools- without
properly citing the source." See the note at the end of `references_DRAFT.md`.]

## Added 2026-11-27 (from the code review and the website check)

**23. Your forecast counts fire detections up to issue time. Would a live forecast
really have all of them?**
Not quite, and we checked. In the backtest the fire points come from NOAA's finished
daily file; a live run at 11:30 a.m. Pacific sees only what had posted by then. Taking
fire inputs out entirely changed error by 1-4% (`docs/METHODS.md`), so this cannot
move our numbers by more than that. The code now has a posting-delay setting
(`fire_lag_hours` in `configs/west_us.yaml`, off by default) so the effect can be
measured. [TEAM: finish this answer with what was decided under D-4: either "we wrote
it into the protocol before freezing" or "we added a 3-hour delay and reran
development before freezing". See item 1 of `docs/CODE_REVIEW_2026-11-27.md`.]

**24. The site says "20% chance". Chance of what, and is that number honest?**
The chance that the day's average reaches 35.5 µg/m³, the start of "Unhealthy for
Sensitive Groups". It comes from our forecast range, then a correction fitted on the
calibration days only (isotonic regression, `fit_probability_recalibration`), so that
"20%" means it happened on about 20% of similar past days. The site never shows the
raw, uncorrected number. What we have not yet shown is how reliable the corrected
chance is on days the correction never saw; the backtest saves it
(`smokecast_probcal_L*` in `predictions.parquet`) and `serein.eval.reliability` scores
it. [TEAM: run that on the development predictions before the Summit, or after D-5 on
the test years, and put the result here.]

**25. I opened your website and it never mentions asthma or children. Why?**
Because the website shows what runs today for anyone: the smoke forecast and an
activity plan for a place. The per-child model is in the demo app
(`app/streamlit_app.py`, screenshots in `docs/demo/`) and has been tested only on
simulated children, so we do not put it in front of the public yet. Real families come
after a clinician reviews the wording (README C-8) and we have parent interviews
(E-1). [TEAM: if the AirPlan page gets a short section on the child plan, or a new
name, change this answer to match. See H1 in `docs/WEBSITE_CHECK_2026-11-26.md`.]

## Numbers to have memorized (development, 2023; replace after D-5)

| | Serein | NOAA fallback | Persistence | EPA official |
|---|---|---|---|---|
| RMSE, 1 day ahead (µg/m³) | 7.8 | 11.0 | 13.8 | n/a |
| RMSE, 3 days ahead | 11.6 | 15.5 | | n/a |
| Warned on real USG+ days, 1 day ahead | 72% | | | 46% |
| False alarms, 1 day ahead | 92 | | | 98 |
| Warned on real USG+ days, 2 days ahead | 62% | | | 37% |
| False alarms, 2 days ahead | 48 | | | 36 |
| CSI (USG+), 1 day ahead | 0.53 | | 0.26 | |
| Share of the true peak forecast, 1 day ahead | 76% | 31% | | |
| 90% interval coverage | 89-91% | | | |
| Error without live sensors, today (ablation of 2026-11-02) | +66% | | | |
| Error at hidden monitors, 1 day ahead | 8.5 | 11.1 | | |

Sources: README "Current results (development rerun, 2026-11-23)"; the persistence and
CSI figures are in Brief section 5; `docs/EQUITY.md`; `docs/HOURLY_ACCURACY.md`.
