# Results snapshot (2026-11-23, dev mode)

A copy of the key outputs so anyone can read the results **without** re-downloading
~150 GB of data. Everything here is **development** scoring: trained on 2021-22,
scored on held-out (odd ISO) weeks of 2023. The 2024-25 test seasons have NOT been
scored yet (see "Finishing the proof" in the main README).

These are the numbers the Brief, pitch and website quote (for example, warned a day
ahead on 72% of "Unhealthy for Sensitive Groups" days against 46% for EPA, with 92
false alarms against 98). The November 2 snapshot that used to be here (71%, 81 false
alarms) is in git history.

## Where the files come from

| Files | Run | Code |
|---|---|---|
| `dev_report.md`, `dev_summary.md`, `metrics.csv`, `head_to_head.csv`, `vs_epa_forecast.csv`, `peak_report.csv`, `impact.txt`, `figures/fig_*.png` | `west_us_dev`, 2026-11-23, 5-member ensemble | 9f01f4d |
| `dev_holdout_report.md` | `west_us_dev_holdout`, 2026-11-23 | 7334216 |
| `figures/map_20230818.png`, `figures/airplan_learning_curve.png`, `airplan_simulation_summary.csv`, `logs/` | older runs (Nov 1-2) | see below |

Between 7334216 and 9f01f4d only warning-probability outputs and the final-test
summary were added; the trained model is the same (identical `smokecast.pt` hash).
The figures were regenerated from the 9f01f4d predictions and came out byte-identical.
Both report headers say "+ uncommitted changes": the run did not record which local
edits those were, so treat this snapshot as reproducible to the commit, not to the byte.

## Files

| File | What it is |
|---|---|
| `dev_summary.md` | One-page summary: the pre-registered primary criterion (PASS on dev), RMSE vs NOAA's best forecast with 95% day-bootstrap intervals |
| `dev_report.md` | Full dev backtest report: RMSE by lead, smoke-day RMSE, warning scores, interval coverage, head-to-head with 95% CIs, comparison with EPA forecasts |
| `dev_holdout_report.md` | Same, with 20% of monitors hidden from the model (forecasting places with no sensor) |
| `metrics.csv` | Every metric for every model, lead and subset |
| `head_to_head.csv` | SmokeCast vs. each baseline on identical rows, with day-bootstrap CIs |
| `vs_epa_forecast.csv` | Category accuracy + warnings vs. EPA's official AQI forecast |
| `peak_report.csv` | How much of each real smoke peak was forecast (median forecast / observed on site-days at or above 35.5 µg/m³: 91%, 76%, 55%, 29% at leads 0-3; see B-15) |
| `impact.txt` | Plain-English impact numbers (warned smoky days, false alarms) |
| `airplan_simulation_summary.csv` | AirPlan synthetic-children study (Brier gain by days logged), 2026-11-01 |
| `figures/` | Charts for the brief, video and website. `map_20230818.png` is still the 2026-11-02 single-model map; regenerate it with `uv run serein map --date 2023-08-18 --run west_us_dev` |
| `logs/abl_*.log` | Historical input ablations, rerun 2026-11-02. Summary table in `docs/METHODS.md` |
| `logs/peaks_w*.log` | Smoke-day loss-weight experiment (B-13), code before the 2026-11-01 review fixes |
| `logs/sweep_*_reg*.log` | Settings sweep, code before smoke weighting and the neighbor-based base |

Later experiments are in [EXPERIMENTS.md](../EXPERIMENTS.md). The ones scored so far
(B-15, B-16, GOES AOD, fire monitors as inputs and as graph nodes, 10 seeds) did not
pass the acceptance rule, and the CAMS test has not been scored yet, so the model
behind this snapshot is still the current one.

To regenerate everything: `./scripts/run_dev_suite.sh` (after downloading data).
