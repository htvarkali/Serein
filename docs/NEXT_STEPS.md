# Next steps after the reliability and sensor-QC work

Updated November 4, 2026. This supplements the README task board. Code on a feature
branch remains in progress until reviewed and merged.

## What this increment delivers

- **A-12:** offline PurpleAir screening with row-level rejection reasons, corrected
  accepted readings, a CLI, and tests. It does not spend API points or establish
  that adding sensors improves forecasts.
- **B-12b:** all ensemble members are exported and used by maps, transfer and
  explanations. Graph/no-graph experiments use matching ensemble sizes.
- **Q-8:** automated CPU checks, app tests, a real synthetic training-to-forecast
  integration test, executable shell entry points, and failures propagated from
  the development scripts.
- **Q-9:** shared ordered, nonnegative calibrated forecasts; unavailable smoke maps
  remain missing; map graphs support fewer sensors than the requested neighbors.

## 1. Review, merge and rerun development

After reviewing this increment, install and verify:

```bash
uv sync --all-extras
uv run pytest -q
uv run ruff check .
```

On the machine with the downloaded public environmental data, rebuild training and
calibration features because observation aggregation and missing-HMS handling changed:

```bash
uv run serein build-points
uv run serein build-table --split train
uv run serein build-table --split calibrate
./scripts/run_dev_suite.sh
```

This scores 2023 development weeks. Compare errors, warning tradeoffs, peak capture,
and coverage, including the matched-size graph/no-graph comparison. Regenerate the
map from the new full ensemble. Check `model.json` for `n_members: 5` and its seed list.
Retain the old snapshot as historical evidence until the revised run is reviewed;
do not treat software tests as proof of improved forecasting accuracy.

The rebuilt registry retains each EPA monitor's state so identically named
reporting areas in different states remain separate in the EPA comparison.

The small synthetic test runs locally and in CI without the full data cache. It
verifies that training, calibration, serialization and map inference agree. It
does not replace the development run above.

## 2. Add real low-cost sensors only after access and QC review

Use the [QC guide](PURPLEAIR_QC.md) on a small history file. Inspect rejected rows,
especially localized plumes, flat clean-air periods and sparse neighborhoods.
Tune screening choices on development data and document them. A-14 needs a reviewed
API-point estimate or research access. B-8 then adds the accepted nodes and measures
their benefit on the same development days. Never substitute current sensor
placement metadata for historical availability without documenting the limitation.

## 3. Complete the family experience

C-10b's [forecast-context workflow](FORECAST_CONTEXT.md) exports AQM ozone and the
maximum of complete hourly HRRR temperature forecasts, connects them to the
existing personal-model inputs, and preserves unavailable data. The optional
pollen check-in is included. The current family plan still uses synthetic history; the
check-in demonstration is stored separately. Connecting real check-ins requires
observed exposure history and the consent/review process in [ETHICS.md](ETHICS.md).
C-7/C-8 require native-speaker and clinical review; no such review is claimed here.

## 4. Finish the evidence and competition materials

The team must confirm the Conrad submission state (S-1), provide member/advisor
details (S-3), collect genuine interviews and expert feedback (E-1/C-8), verify the
business and competitor claims (E-4/E-5), and complete the video and contact details.
These require real information; development work cannot establish their completion.

After development methods are agreed, freeze and commit [BACKTEST_PROTOCOL.md](BACKTEST_PROTOCOL.md).
Only then run the reserved 2024–25 evaluation and transfer test with the team, once.
An exploratory [paired forecast comparison](FORECAST_COMPARISON.md) is available
for saved development predictions, with bootstrap RMSE intervals and a day-level
Diebold-Mariano test. Review its estimand, calendar-gap variance, bandwidth, and
multiple-comparison choices before including it in D-5. The final analysis remains
pending team review.
Report all outcomes, including losses, before replacing numbers in the brief and
website. No final or transfer evaluation is performed by this increment.
