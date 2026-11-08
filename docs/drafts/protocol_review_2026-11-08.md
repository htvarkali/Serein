# Pre-freeze review of BACKTEST_PROTOCOL.md (for D-4)

Read 2026-11-08 the way a skeptical judge or reviewer would. The protocol is already
better than most published forecast evaluations: season-level split, enforced issue
time, pre-registered primary metric, fixed seeds, deterministic training, a lock file.
The items below are the questions a judge could still ask, ranked by how much damage
an unanswered one would do. Each has a proposed fix that can be made **before** the
freeze without touching the test seasons. After the freeze, only section 7 applies.

## Must fix before freezing

**1. The change log stops on 2026-11-02, but scoring-relevant code changed through 2026-11-07.**
Q-9 (nonnegative ordered calibration, missing-HMS handling, EPA area matching by state),
B-12b (full-ensemble export), the "historical AQI categories in transfer scoring" fix,
and the observation-aggregation changes all touch numbers that appear in the brief. A
judge who diffs the repo sees unexplained drift between the protocol's dev numbers and
the code. *Fix:* one change-log row per merged PR since Nov 2 that affects data, scoring
or export, in the same style as the existing rows; then rerun the dev suite on the
current code and record the new dev numbers in 6b. The freeze commit should be the
commit right after that rerun.

**2. Dev-week results reuse the weeks that tuned them.**
Section 2 says odd 2023 weeks are used for conformal calibration, and 6b says dev
results are "scored on odd ISO weeks of 2023." The warning cut-offs were also "tuned on
calibration." So the dev-mode 89-91% interval coverage is close to in-sample by
construction, and the dev 71%-vs-46% warning result is optimistic. The protocol's
caveat sentence covers this in general terms; a judge will want it specific. *Fix:* add
to 6b: "Interval coverage and the warning hit rate on dev weeks are partly in-sample
(the same odd weeks set the conformal offsets and warning cut-offs). The 2024-25 test is
the only fully out-of-sample estimate of either." Say the same in Brief Q5.

**3. Two "final" runs are planned but the protocol says "scored once."**
The README's finishing section runs `--final` and then `--final --tag final_holdout
--holdout-sites 0.2 --no-gbm`, plus the transfer test. That is fine, but it must be
written down before the freeze or it reads as a second bite. *Fix:* in section 6,
enumerate the exact commands that constitute the final evaluation (main, hidden-sites,
transfer), state that each runs exactly once, and that the hidden-site run uses seed 1234
chosen in advance.

**4. The Diebold-Mariano test is in the D-5 task but not in the protocol.**
Any test named after the result is known looks post hoc. *Fix:* add to section 6:
"Day-level Diebold-Mariano test of squared errors, SmokeCast vs. each baseline, per lead,
two-sided, with a Newey-West bandwidth of [state it]; reported alongside the bootstrap CI,
not in place of it."

## Should fix before freezing

**5. Historical data-availability times were measured in 2026, not in 2024-25.**
Section 3 posting times come from S3 `LastModified` on 2026-11-01. For 2024-25 files that
may reflect re-uploads. NEXT_STEPS.md already admits "historical availability still needs
an audit." The AQM 12z run (≈18:03 UTC) lands 27 minutes before the 18:30 issue time,
which is the input a judge will probe. *Fix:* (a) state the limitation in section 3;
(b) pre-register a sensitivity row: "If the AQM input had been late, the forecast would
use HRRR+persistence only; we report that scenario using the existing no-AQM ablation."
That ablation exists (AQM removal: +7-14% error) and costs nothing.

**6. `noaa_best` is a composite we built, not a NOAA product.**
A judge may say: you beat a fallback chain of your own design. The per-product rows
(`aqm_bc`, `hrrr_smoke`) already exist. *Fix:* in section 5, state that the primary
comparison is against `noaa_best` because it is the best official number available at
issue time for each lead, and that `aqm_bc` and `hrrr_smoke` are also reported on the rows
where each exists, with row counts per competitor per lead in the final report.

**7. Add a same-day morning persistence baseline for lead 0 (and consider for lead 1).**
Berlinghieri et al. (BAMS 2026) found morning AirNow persistence matched or beat the
operational models for day-level decisions. Our `persistence` is yesterday's daily mean.
For L0 ("the rest of today"), the mean of today's hours up to 16:00 UTC is the stronger
naive forecast and the one that paper implies. Adding it before the freeze is legitimate;
adding it after is not. *Fix:* add `persistence_morning` (today's observed mean of hours
≤ 16:00 UTC, carried forward) as a competitor for L0 and L1. If it is not implemented in
time, write in the protocol that it was considered and why it was omitted.

**8. AQM version change inside the test period.**
DATA.md: AQMv6 to 2024-05-13, v7 after. The test seasons therefore mix two AQM versions,
and the model was trained on v5/v6. *Fix:* state this in section 2 and pre-register a
secondary split of the test results by AQM version (2024 before/after May 13; 2025).
Whatever it shows, it is better to have said so first.

**9. Lead 3 is where the brief says Serein "adds the most," but the primary success
criterion only covers leads 1 and 2.**
That is defensible (no official product at L3 to compare with), but say it. *Fix:* add
one sentence: "Lead 3 has no official competitor; we report it against persistence and
climatology as a secondary result."

**10. Hidden-monitor holdout: hidden from what, exactly?**
State that the 20% held-out sites are excluded from training, early stopping, conformal
calibration and warning-threshold tuning, not only from training. If that is not true
today, fix the code before the freeze or state the limitation.

## Nice to have

**11. Test-season data completeness.** Before freezing, confirm every month of
Jun-Oct 2024 and 2025 has AirNow, HRRR and AQM files, and record the count of missing
days in the protocol. A gap discovered after the run looks like cherry-picking even when
it isn't.

**12. Pre-specify what "we lose" looks like.** One sentence: "If the primary criterion
is not met, we will report that as the headline result and the brief will say so."
Judges remember teams that wrote that down.

**13. Out-of-region test framing.** Section 2 already notes 2023 is a calibration year
for the West. Add that the Northeast test uses the West-calibrated conformal offsets and
warning thresholds unchanged, so its coverage may be off, and that this is expected.

**14. Archive the inputs.** After the final run, hash and archive the test feature
tables and the model export (`CACHE_ARCHIVE_AUDIT.md` seems to cover this); mention it in
section 7 so reproduction is part of the protocol.

## Proposed freeze checklist (D-4), in order

1. Merge every open code PR that touches data, scoring or export; close the rest until after the final run.
2. Add change-log rows for all Nov 3-7 changes (item 1 above).
3. Rebuild train and calibrate tables; rerun `scripts/run_dev_suite.sh`; paste new dev numbers into 6b and the README results table (labelled development).
4. Apply the text fixes above (items 2-10, 12, 13) to the protocol.
5. Confirm test-season file completeness (item 11) and record it.
6. Change the status line to **FROZEN**, commit with message "D-4: freeze backtest protocol", push, and record the hash and time in the change log of the *next* commit.
7. Then, and only then: `serein backtest --final`, the hidden-site run, the transfer run, each once. Report everything.

## Sentences to add to the brief (Q5) after the freeze

> Our evaluation protocol was written and committed before the 2024-25 test seasons
> were scored (commit [hash], [date]). It fixes the data split, the issue time, the
> baselines including persistence, the primary metric and the model settings. Dev-week
> coverage and warning rates are partly in-sample; the test seasons are the only fully
> out-of-sample numbers, and we report them whether or not we win.
