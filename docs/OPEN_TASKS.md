# Open tasks: who does what next (2026-11-27)

Every row still Open, In progress or Blocked on the README task board, with what is
stopping it and the next step. The README board stays the official record; this page is
for planning the next five weeks. Dates: financial aid **Dec 3**, protocol freeze
**Dec 17**, team target **Jan 1**, Innovation Stage due **Jan 7, 2027**.

Who can do it: **Team** = a decision or fact only the team has; **Data PC** = needs the
machine with the 150 GB of data and the trained models (Aadi's); **Anyone** = can be
done from a laptop with the repo.

## By deadline

| When | Task | What is left | Who | Next step |
|---|---|---|---|---|
| **Dec 3** | S-11 | Financial aid form (one per team, Microsoft Form linked from Conrad's "Financial aid closes" page; results by Dec 17). Page 2 asks: contact (a team member, not a coach), city, state, country, school, category, team name, **Team ID**, number of members, whether we competed before | Team | Pick the contact, copy the Team ID from the portal, agree the need statement, submit by 8:59 pm Pacific |
| **Now** | S-1 | Confirm the Lean Canvas was submitted on Oct 29, and the category | Team | Log in to the Award Force portal; screenshot it. Needed for the aid form's "Category" too |
| **Nov 30** | E-1 | Interviews: nobody contacted yet | Team | Monday send list in [OUTREACH_TARGETS.md](interviews/OUTREACH_TARGETS.md); needs a coach copied first |
| **Dec 17** | D-4 ⭐ | Freeze the protocol. First decide code review item 1 (fire timing) | Team, then Data PC if option B | [Freeze checklist](drafts/freeze_checklist.md) |
| after D-4 | D-5 ⭐ | Final test, once | Data PC | The five steps in protocol section 6 |
| after D-5 | D-6b ⭐ | Transfer test, once | Data PC | `uv run serein transfer --run west_us_final` |
| after D-5 | S-6 | Brief Q4 and Q5 final numbers | Anyone | Paste from `final_report`; rerun `python3 scripts/check_brief.py` |
| **Jan 1** | S-9 | 3-5 minute video | Team | [Script and shot list](drafts/video_script.md); title card, end card, slides, phone text and captions are ready in [`video/`](video/README.md). Record Smoke World, the app and the team at 1920x1080 |
| **Jan 1** | S-3 | Jagath's role, advisor, "why us" sentence | Team | Fill the three `[TEAM]` lines in Brief section 2 |
| **Jan 1** | S-4 | Interview and clinician findings in Brief Q3 and Q5 | Team | Needs E-1 and C-8 |
| **Jan 1** | S-5 | Brief `[TEAM]` slots in Q6, Q8, Q10 | Team | Each needs interviews or the pilot plan; the rest of Q6-Q10 is done |
| **Jan 1** | S-10 | AI-tool list; the 2 attachments | Team | [Fill-in template](drafts/references_DRAFT.md) at the end; attachments after D-5. The CDC "not well controlled" item was settled 2026-11-27 (entry A6a) |
| **Jan 1** | S-8 | Website: team section and contact line | Team | Needs a team email address (no task tracks it yet). The AirPlan naming issue (H1) was fixed 2026-11-27 |
| **Jan 7** | S-11 | Submit Brief, video, website link and fee in the portal | Team | |

## Outside reviewers and partners

| Task | What is left | Who | Next step |
|---|---|---|---|
| C-8 | A clinician reviews the action-plan wording and the priors | Team | [Review request](drafts/clinician_review_request.md) with the ready packet [`review/clinician_packet.pdf`](review/clinician_packet.pdf); start with a team parent's pediatrician |
| C-7 | Native Spanish speaker reviews `messages/es.yaml` | Team | Send [`review/spanish_review.pdf`](review/spanish_review.pdf) (or the `.csv`) to a Spanish teacher or a native-speaker parent; copy their changes into `es.yaml` |
| C-11, E-3b | More languages, a third mockup language | Anyone, after C-7 | Wait for C-7 to set the review process |
| E-7 | Letters of support | Team | [Letter template](drafts/letter_of_support_template.md) and [district one-pager](drafts/district_one_pager.md); ask after an interview goes well |
| E-2b | Polish the app from interview feedback | Anyone, after E-1 | |
| W-19 | Watch 5 people use Smoke World for the first time | Team | [Script and sheet](SMOKE_WORLD_FIRST_USE_TEST.md); classmates count |

## Business and IP

| Task | What is left | Who | Next step |
|---|---|---|---|
| E-4 | Price confirmation | Team, after E-1 | Ask every district or nurse interviewee the price question in the interview guide |
| E-6 | Merge the Lean Canvas text and interview findings into the business plan | Team | Needs the Lean Canvas text from the portal (S-1) |
| E-8 | IP decision (keep code open and protect the name, or move models private) | Team | [Memo](drafts/ip_decision_memo.md) has the trademark search; decide before the Brief's IP paragraph is final |

## Data and models (Data PC)

| Task | What is left | Next step |
|---|---|---|
| A-14 | PurpleAir history, after the cost estimate is approved | Choose the channel first: [correction check](PURPLEAIR_CORRECTION_CHECK.md) |
| D-3 | Decide whether to send the PurpleAir research-access request | Team decision; [draft](drafts/purpleair_data_request.md) |
| B-15 | Peaks under-predicted at days 2-3; four ideas failed | Only before the freeze, and only under the acceptance rule in `docs/EXPERIMENTS.md` |
| B-16 | Smoke-transport features | Same |
| W-8 | The live map should show each day's chance, warning and low-confidence flag. The live file of Nov 27 has none of them, so the daily job did not find `prob_recal.json`, `warn_cutoffs.json` and `flag_width.json` in `outputs/backtest/west_us_live_v1/` (those files were added to the backtest on 2026-11-23; the live model was trained on 2026-11-22) | Look for the line "note: ... not found" in the daily job's log. If the files are missing, the live model needs them from its own calibration rows, which means rerunning its backtest; do not copy them from another run |
| W-11 | Daily live update | Working: the job pushed new forecasts on Nov 25, 26 and 27 |
| W-17 | Schools and hospitals under unhealthy smoke | Counting code done 2026-11-27 (`serein.places`, shown on the map with the population overlay). One step left: download the two public files named in `src/serein/places.py`, run it, rebuild the site |
| W-10 | 3D buildings: photorealistic cities not checked | Low priority; check once on a desktop browser |
| W-12 | Lighter site for phones: check on real phones | Anyone with a phone: open each page on cellular data, note anything slow or broken |

## Done on 2026-11-27 from this list

- Financial aid form read (page 1 and 2 questions above); draft answers kept out of the
  public repo.
- S-10: CDC "not well controlled" source found and cited (A6a), METHODS.md and the model
  comment corrected.
- D-4: freeze checklist with ready text for both fire-timing options; code changes of
  the day logged in the protocol change log.
- S-8 / H1: AirPlan page section on the per-child plan, labelled as tested on simulated
  children, with a demo screenshot.
- W-17: school and hospital counts built and tested, waiting for the data file.
- W-11: confirmed working.
- Later the same day: video graphics (`docs/video/`), the clinician and Spanish review
  packets (`docs/review/`), and a number check across the README, Brief, website,
  judge Q&A, pitch, one-pager and video script (two stale numbers fixed).
