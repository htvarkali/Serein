# Judge Q&A preparation (for online judge coaching and the Summit)

Written 2026-11-08. Online judges leave written coaching in February; finalists face 8
minutes on stage plus 20 minutes of questions. Every team member should be able to give
each answer below in their own words without notes. Answers quote only numbers that
exist in `docs/results/` (development, 2023) and must be updated after the final test.

Rule for every answer: say the number, say the limitation, say the next step. Judges
score Practicality on whether we know our own error bars.

## About the forecast

**1. Why not just use Google's air quality forecast? It's 500 m and 96 hours.**
Google's API is good and we say so in the brief. Three things it does not do: publish
how accurate it is against the official forecast on smoke days, give a range instead
of a single number, and tell a family what to do for their specific child. We measured
ours: on held-out 2023 days, one day ahead, our error was 7.9 µg/m³ against 11.0 for
NOAA's bias-corrected model and 13.8 for persistence. We would welcome Google's data
as an input if they offered it.

**2. A 2026 paper found persistence beats every smoke model for day-level decisions.
Why should we believe yours is different?**
We agree with that paper, which is why persistence is one of our scored baselines
rather than something we hide from. One day ahead on 2023 held-out days, our warning
skill for "unhealthy for sensitive groups" was 0.53 against 0.26 for persistence
(critical success index), and our error was 7.9 against 13.8 µg/m³. The difference
comes from using the live monitor readings the models ignore. Our final 2024-25 test,
run once under a frozen protocol, will say whether that holds.

**3. Why a graph neural network? Isn't that overkill?**
We tested that. The same model with the graph turned off is worse at every lead, and
the gap is largest where there is no sensor: 17% lower error today at monitors we hid
from the model. The graph is how a neighborhood without a monitor borrows information
from its neighbors. A simpler gradient-boosting model is also in our baselines and
loses to the graph model at every lead.

**4. What are your false alarm rates?**
One day ahead we had fewer false alarms than EPA's official forecast (81 vs 98) while
warning on more real days (71% vs 46%). Two days ahead we warn on more days (66% vs
37%) but with more false alarms (54 vs 36). We report that as a tradeoff and tune the
warning threshold on calibration weeks, not test weeks.

**5. How do you know you didn't peek at the future?**
The issue time is 11:30 a.m. Pacific. The code only uses data that had actually posted
by then, and we measured the posting times from the archive timestamps. The rule is
enforced in `serein/data/availability.py` and tested. We also note that EPA's own
forecasts are issued after our issue time, which favors EPA in the comparison.

**6. What happens when HRRR-Smoke is retired?**
NOAA's successor, RRFS, was scheduled operational in November 2026 at the same 3 km
with smoke fields to 84 hours. Our model corrects whatever NOAA runs; swapping the
input is a data-loader change, not a redesign. We have not yet verified the RRFS
go-live date.

**7. Where does it work? Only the West?**
Trained and scored on the western US. We built an out-of-region test on the June 2023
Canadian smoke event in the Northeast, trained only on the West, and will report
whatever it shows after the final test.

## About the child model and safety

**8. Who is liable when a parent follows your plan and the child has an attack?**
Serein is not a medical device and does not diagnose or change medication. Two rules
are enforced in code and tested: a plan can only be stricter than EPA's public
guidance, never looser, and every message tells the family to follow their own
clinician's asthma action plan and lists emergency signs. [After C-8: "Our messages
were reviewed by (role, affiliation), who asked us to change X."] Before any real
family uses it we would run an opt-in pilot with a clinician advising and written
parental consent.

**9. Have you tested the personal model on real children?**
No. It is validated on 300 simulated children, where it recovers each child's true
sensitivity and beats a one-size-fits-all model after about two weeks of logs. The
starting assumptions come from published studies (Sugrue 2026, Khetsuriani 2007,
Williams 2011). A real pilot needs consent, a clinician and ethics review; that is our
first step after the Summit, not before.

**10. Why would a parent keep doing a check-in every night?**
We do not know yet; that is the second number our pilot measures (families still
logging at 30 days). The check-in is six taps. [After E-1: "Of N parents we
interviewed, K said they would, and the thing that would make them stop was Y."]

**11. What about kids whose families don't speak English or Spanish?**
Messages are in English and Spanish today; the Spanish is drafted and awaiting a
native-speaker review. More languages come only after a review process exists,
because we will not machine-translate health instructions.

## About the business

**12. Who actually pays, and have you talked to them?**
Families never pay. Districts, health plans and air districts do. [After E-1: name
the interviews.] Evidence they spend money on this already: a district pays about
$2,095 per building per year for emergency software; the Bay Area air district
budgets $1.95 million a year for Spare the Air messaging; UW Medicine ran a smoke
outreach to 64,000 patients in 2025 and renewed it.

**13. What does it cost you to run?**
All input data is free from NOAA, NASA and EPA. [Measured inference: X seconds per
issue day on Y hardware.] A daily western-US forecast costs cents a day on a cloud
GPU; text alerts cost about 1.3 cents per message part. Messaging and compute stay
under 10% of revenue at our prices.

**14. What stops a competitor from copying you? Your code is public.**
The code is deliberately open so health departments can audit a product that advises
parents about children. Our advantages are the validated backtest, which no consumer
product publishes, the partnerships we build with districts and clinicians, and the
check-in data, which is never published. We will file a provisional patent on the
combined system before the Summit as the rules require. [After E-8: brand decision.]

**15. Did students really build this? It's a lot of code.**
Yes, and each of us can walk you through our part. [Each member: one sentence on what
they built and one decision they made and why.] We used AI coding assistants for
boilerplate and documentation, which we cite in the brief; the model design, the
backtest protocol, the decision to report where we lose, and the safety rules are ours.

## Numbers to have memorized (development, 2023; replace after D-5)

| | Serein | Best NOAA | Persistence | EPA official |
|---|---|---|---|---|
| RMSE, 1 day ahead (µg/m³) | 7.9 | 11.0 | 13.8 | n/a |
| RMSE, 3 days ahead | 11.4 | 15.5 | 15.5 | n/a |
| Warned on real USG+ days, 1 day ahead | 71% | | | 46% |
| False alarms, 1 day ahead | 81 | | | 98 |
| CSI (USG+), 1 day ahead | 0.53 | 0.29 | 0.26 | |
| 90% interval coverage | 89-91% | | | |
| Error without live sensors, today | +66% | | | |
| Error at hidden monitors vs NOAA, 1 day | 8.5 vs 11.1 | | | |

Sources: `docs/results/dev_report.md`, `docs/results/vs_epa_forecast.csv`,
`docs/results/head_to_head.csv`.
