# Protocol freeze checklist (task D-4, by Dec 17, 2026)

Written 2026-11-27. The freeze is one commit that changes the status line at the top of
`docs/BACKTEST_PROTOCOL.md` to "FROZEN" and is pushed before anyone runs
`serein backtest --final`. Its hash and time are our proof that the rules came first.
After that, section 7 of the protocol says what may still change.

## 1. Decide the fire-detection item (code review item 1)

Pick one, as a team, and write down who decided and when.

**Option A: describe what the code does.** No rerun. Replace the FIRMS bullet in
protocol section 3 with:

> - Fire detections in the 24 h before issue time: NOAA HMS fire points (VIIRS and
>   MODIS) from the archived daily file, or NASA FIRMS where a FIRMS cache exists. No
>   posting delay is modeled: the backtest may see detections and analyst removals
>   that a live forecast at 18:30 UTC would not yet have. Removing all fire inputs
>   changed development RMSE by 1-4% (`docs/METHODS.md`), the upper bound on this
>   effect. The live test (section 7b) uses only what had posted.

Change-log row:

> | [date] | Section 3: fire-detection source and timing stated as the code runs them (no model settings changed) | Code review 2026-11-27, item 1. The section said FIRMS; the default is HMS fire points. No posting delay is modeled; the fire ablation bounds the effect |

**Option B: add a 3-hour posting delay.** Needs a rebuild and a development rerun
before the freeze (about a day of computer time on the data machine).

1. In `configs/west_us.yaml` set `fire_lag_hours: 3`.
2. Rebuild the tables (`uv run serein build-table --split train` and `--split calibrate`).
3. Rerun the development backtest the same way as the 2026-11-23 rerun.
4. Record the development numbers before and after. This is a "no peeking" fix, not a
   model improvement, so it is kept even if the scores get slightly worse; the
   acceptance rule in `docs/EXPERIMENTS.md` is for model changes.
5. Section 3 bullet:

> - Fire detections from 27 h to 3 h before issue time (NOAA HMS fire points, or NASA
>   FIRMS where cached), so detections posted late are not used (`fire_lag_hours: 3`).

6. Change-log row with the before and after development numbers, then update the README
   results, `docs/results/` and the judge Q&A numbers.

Either way, update answer 23 in `docs/drafts/judge_qa_prep.md` to match.

## 2. Other items to close before freezing

- [ ] Code review item 2 (HRRR units): run the 10-line check in
      `docs/CODE_REVIEW_2026-11-27.md` on the data machine; expect 0 files.
- [ ] Code review item 3 (development coverage): the README and Brief describe the
      89-91% coverage as development-only (they do; recheck after any rerun).
- [ ] Item 5 (equity edge): run `uv run python -m serein.eval.equity` and read
      `edge_check.csv`; if the lowest-income fifth's share would change, update
      `docs/EQUITY.md` and judge Q&A answer 11.
- [ ] Section 6b lists the settings the final run uses, and `configs/west_us.yaml` on
      main matches it (with `fire_lag_hours` set as decided above).
- [ ] The test feature table has not been built (`data/processed/west_us/table_test.parquet`
      does not exist on any machine), and no `outputs/backtest/west_us_final*` folder
      exists.
- [ ] The full test suite passes on main (CI green).

## 3. The freeze commit

1. Everyone has read the protocol once more (D-4 says "read and freeze").
2. Change the status block at the top to:

> **Status: FROZEN on [date] at commit [this commit].** Nothing in sections 1-6b changes
> after this line except as section 7 allows.

3. Add a change-log row: `| [date] | FROZEN | Before any test-season table was built or scored |`.
4. Commit with a message such as `D-4: freeze the backtest protocol`, push, and copy the
   commit hash and time into the README row for D-4 (mark it Done) and into Brief
   section 5.
5. Only then run the final evaluation (D-5), exactly the steps in protocol section 6,
   then the transfer test (D-6b).
