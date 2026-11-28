# Brief review, 2026-11-25 (tasks S-5, S-10, E-6, E-8)

A pass over the pitch material against the repo as it stood on 2026-11-25 (main at
a0f25a1). Update 2026-11-27: `docs/results/` has since been re-exported from the
November 23 rerun, section 5 of the Brief was cut to fit its limit, and the
hidden-monitor numbers were rerun (8.5 vs. 11.1 a day ahead). It records what was changed, what was found, and what only the team can do.
Model code, the website and Smoke World were not touched.

## 1. Things with a date on them

1. **Conrad financial aid closes December 3, 2026, 11:59 pm.** The event page says ET
   and the calendar entry says CST; treat the earlier one as the deadline. One form
   per team, linked from the Innovation Stage page; there is also a group or school
   discount. The page does not say how much of the $499 it covers. If we are not
   applying, say so in Brief section 10.
2. **Conrad's rules require citing AI tools, and nothing we have cites one.** The Rules
   and Regulations say a submission "may not copy or use other materials- including
   artificial intelligence (AI) tools- without properly citing the source", and that it
   "must be entirely the work of the student team members." Judge Q&A answer 22 says we
   cite our tools; that is not true yet. A `[TEAM]` slot is at the end of
   `references_DRAFT.md`. Each member lists what they used for their own part.
3. **Roster and coach.** The same rules say a team is 2 to 5 students, needs one coach
   who is at least 18, and cannot add members after the Activation Stage. Brief section
   2 lists five members and no advisor yet. Check in the portal that all five were on
   the Activation roster and that a coach is named (S-1, S-3).
4. **December 10, 2026, 4 to 5 pm CST:** Conrad workshop "Innovation Insight:
   Communicating your Idea". Worth watching before the video is filmed.

## 2. Numbers that disagree between files

`docs/results/` is still the 2026-11-02 snapshot. The README and the Brief quote the
2026-11-23 rerun. A judge who follows "every number comes from a file" will find two
answers:

| Figure | `docs/results/` (Nov 2) | README and Brief (Nov 23) |
|---|---|---|
| Warned a day ahead, Serein | 71% | 72% |
| False alarms a day ahead, Serein | 81 | 92 |
| Warned two days ahead, Serein | 66% | 62% |
| False alarms two days ahead, Serein | 54 | 48 |
| RMSE one day ahead | 7.9 | 7.8 |
| RMSE three days ahead | 11.4 | 11.6 |
| Hidden monitors, one day ahead | 8.5 | 8.4 |
| Share of the true peak, one day ahead | 80% | 76% |

The video script and the judge Q&A used the old column until today; both now use the
new one. Someone with the data needs to re-export `docs/results/` (report, CSVs and
figures) from the November 23 run before a figure goes into the Brief as an
attachment or onto the screen in the video. The README task B-13 row still says 80%.

Brief section 5 says "Nine ideas to improve accuracy failed" and lists them as of
November 23. Three more failures were logged on November 25. The log now has nine runs
marked `ACCEPTANCE: FAIL`. That is a different tally from the Brief's list, which also
counts the blending studies, and those have no acceptance line. Recount and say which
count is meant.

## 3. Word counts

`python3 scripts/check_brief.py` (new) counts each section without the `[TEAM]` notes:

```
 sec words  limit status       [TEAM] slots
 1   144 / 150  ok           0 open  Elevator pitch
 2    75 / 150  ok           3 open  Team
 3   233 / 300  ok           1 open  Opportunity
 4   748 / 750  ok           4 open  Key metrics: how it works, what's new, impact, IP
 5   517 / 450  OVER by 67   6 open  Validation and progress
 6   291 / 300  ok           1 open  Market
 7   258 / 300  ok           0 open  Competition
 8   147 / 150  ok           1 open  Go-to-market
 9   292 / 300  ok           1 open  Business model
10   124 / 150  ok           1 open  Fundraising
    2829 / 3000 ok
```

- Section 5 is over before the final results and the three feedback slots go in. A
  shorter version is in part 6 below.
- Section 4 is 2 words under its limit and still has the results table to swap for
  the final numbers. Any new sentence there has to replace one.
- Sections 7 and 4 contain tables. If the portal's text box does not keep tables, they
  need to become sentences; check the portal before the last week.

## 4. What changed in this pass

| File | Change |
|---|---|
| `innovation_brief.md` section 4 | IP paragraph written from the IP memo's option A, with a `[TEAM]` note to confirm it. Dong et al. 2026 cited in "What is new" (it was already reference 36); the note about Dimri et al. updated after reading its abstract |
| section 8 | One sentence on California's $119,100 formal-bidding threshold; the precedent sentence shortened to make room |
| section 9 | "Compute and messaging stay under 10% of revenue" replaced with the measured shares: 5% to 15% of a district's fee, 6% to 11% of a health plan's. The old sentence was wrong at the low end of both price ranges |
| section 10 | The 1517 Fund and AWS prize line removed (Conrad's 2026 awards page names neither); financial aid and its deadline added |
| `business_plan.md` (new) | Task E-6: buyers, prices, costs, three-year scenarios, route to the first customer, funding, risks, dates. Adds outdoor employers as a possible fourth buyer, with what each state's smoke rule requires |
| `src/serein/business.py`, `tests/test_business.py` (new) | The arithmetic behind the plan and Brief section 9, with 12 tests |
| `business_scenarios.csv` (new) | Output of `python -m serein.business` |
| `scripts/check_brief.py` (new) | Word counts against the limits |
| `references_DRAFT.md` | Entries 7, 44, 46 and 57 settled; 58 to 66 added; a slot for the AI tools |
| `ip_decision_memo.md` | Trademark status from USPTO: the health-software application is dead; one live registration covers e-cigarettes |
| `video_script.md` | November 23 numbers, Smoke World as the main visual, five members, timed at 150 words a minute |
| `judge_qa_prep.md` | November 23 numbers; eight new questions |
| `innovation_brief_q6-q10_DRAFT.md` | Sections 8 to 10 brought back in line with the Brief |

## 5. Slots only the team can fill

| Where | What is needed | Task |
|---|---|---|
| Section 2 | Jagath's role; the coach or advisor; one true sentence on why us | S-3 |
| Section 3 | Two or three sentences from interviews, with counts | E-1 |
| Section 4 | Confirm IP option A; the line about the name after a full trademark search; read Dimri et al. in full; final results table | E-8, D-5 |
| Section 5 | Final test, out-of-region test, clinician, Spanish review, interviews, pilot plan | D-5, D-6b, C-8, C-7, E-1 |
| Section 6 | Adjust the bottom-up size after interviews; decide on the outdoor-employer buyer | E-4 |
| Section 8 | A named partner or a letter of support | E-7 |
| Section 10 | Whether we applied for financial aid | S-11 |
| References | The CDC page that defines "not well controlled"; the AI tools | S-10 |
| Portal | Lean Canvas submitted, category, roster, coach | S-1 |

## 6. A shorter section 5 (proposal; the section's owner decides)

About 290 words, which leaves about 120 for the final results and the feedback. It
keeps every result now in the section except the single-input details, and it drops
PurpleAir from the next steps because B-8 was closed on November 25. Put that back if
A-14 is still planned.

**What we built.** Smoke World (htvarkali.github.io/Serein), a public 3D map of the western U.S. that updates each day with the next 72 hours of smoke, wind and fires, and shows the tested daily forecast and its range for any place clicked. Behind it are a pipeline that downloads five fire seasons of free public data from NOAA, NASA and EPA, trains SmokeCast, scores it and draws maps; a demo app with the map, a family's plan and the daily check-in; and automated tests that run on every change.

**How we tested.** We wrote the rules before scoring (docs/BACKTEST_PROTOCOL.md): train on 2021-22, tune on 2023, and keep 2024-25 for one final test.

**Development results (held-out weeks of 2023).**
- One day ahead, Serein's RMSE was 7.8 µg/m³ against 11.0 for the AQM-first fallback and 13.8 for persistence; its warning skill was 0.53 against 0.26 for persistence (critical success index).
- It warned on 72% of "Unhealthy for Sensitive Groups" days against 46% for EPA, with fewer false alarms.
- With 20% of monitors hidden, it still beat NOAA at the hidden sites. In the lowest-income fifth of western neighborhoods, 10.8% of people live 25 km or more from an EPA monitor, against 0.6% in the highest (docs/EQUITY.md).
- Hour by hour, neither NOAA's forecast nor ours could tell which hours of a day would be worst, so our advice is per day (docs/HOURLY_ACCURACY.md).
- Without live monitor readings, today's error was 66% worse; without NOAA's HRRR forecasts, tomorrow's was 29% worse.
- Nine attempts to improve accuracy failed our fixed acceptance test. All are logged (docs/EXPERIMENTS.md).

[TEAM: final test results, 2024-25, and the out-of-region test. About 60 words.]

**Expert and user feedback.** [TEAM: C-8 clinician, C-7 Spanish review, E-1 interviews. About 60 words.]

**Next steps before the Summit.** Run a small opt-in pilot of the check-in with one school district, with a clinician advising, and add languages once a review process exists. [TEAM: confirm the pilot plan and ethics review with an adult advisor. See docs/ETHICS.md.]
