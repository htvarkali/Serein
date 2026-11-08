# Reference-only spatial development experiment

The experiment runner withholds a declared set of evaluation monitors from
preprocessing, model fitting, early stopping and conformal calibration. It trains
on reference monitors, then predicts at evaluation locations using reference
readings and public forecast inputs. It reuses the existing SmokeCast trainer,
ensemble serialization, calibration and map-graph code. It does not change the
ordinary backtest or run the reserved evaluation.

This is separate from the existing `backtest --holdout-sites` experiment, which
retains evaluation monitors in preprocessing, early stopping and calibration.
See the [saved spatial audit](SPATIAL_EVALUATION.md) for that distinction and the
partition format.

```powershell
uv run python -m serein.eval.spatial_experiment `
  --train data/processed/west_us/table_train.parquet `
  --calibrate data/processed/west_us/table_calibrate.parquet `
  --points data/interim/west_us/points.parquet `
  --partition C:/path/to/partition.json `
  --output C:/path/to/new-spatial-experiment
```

Choose and record the monitor lists before comparing outcomes. The partition's
`provenance` should describe the selection method. Geographic clusters or buffers
may answer a different question from randomly withholding monitors. The runner
does not choose a favorable split or tune model settings across splits.

The training and calibration tables must contain only their configured years,
including all selected target dates. Training, calibration and reserved test years
must be disjoint. No test table option exists. Source folders carrying
`FINAL_RUN_LOCK.json` are refused. The output must be new, with an existing parent,
except for the explicit resume workflow described below.
Input files and ordinary outputs are never overwritten. Extra table sites are
ignored; declared reference sites must have training and even-week calibration
rows. An evaluation monitor absent from the export remains in the site audit.

## What is isolated

1. Preprocessing fits only reference-site training rows. Evaluation-site target
   histories cannot affect site backgrounds, global fallback values or scaling.
2. Training, early stopping and CQR calibration graphs contain only reference
   sites and their targets. The default is a five-member graph ensemble and a
   matching five-member no-graph ensemble.
3. For prediction, the reference sensor graph stays unchanged. Evaluation sites
   receive reference-to-evaluation edges, with no reverse or evaluation-to-
   evaluation edges. Their sensor-derived feature values are hidden and missing
   flags are set, and their base forecast uses reference neighbors or a
   reference-trained global fallback when AQM is unavailable.
4. Prediction `GraphData` contains no targets. Evaluation observations are kept
   separately and attached only to the exported predictions for scoring.

Only single-day models are supported. The runner uses the existing development
time split: reference-site even ISO weeks of the calibration season supply both
early stopping and CQR calibration; odd weeks supply evaluation forecasts.
Selection and CQR therefore reuse days, and overlapping target windows and
temporal dependence remain. Excluding evaluation monitors does not create a
finite-sample coverage guarantee. Settings were developed using 2023 elsewhere
in the project, so this is still exploratory development work.

The exported `noaa_best` comparator uses the existing AQM, then HRRR plus background
fallback rule, fitted with reference-only preprocessing. It has no evaluation-site
persistence readings or historical background. If both NOAA inputs are unavailable,
its prediction remains missing. It is not the same comparator population as the
ordinary backtest's local-persistence fallback. The graph and no-graph models have
the same reference-neighbor base. Differences therefore assess the extra learned
message-passing path, not removal of all neighboring information.

## Settings and artifacts

Defaults match the main development model's size: 96 hidden units, three layers,
five seeds, a 300-epoch cap, dropout 0.1, weight decay 0.0001 and smoke weight 6.
`--epochs`, `--seeds`, `--seed`, `--hidden` and `--layers` allow a small execution
probe or an explicitly documented experiment. `--threads` defaults to one CPU
thread for predictable CPU work; device selection follows the existing trainer
and installed PyTorch build. A CPU-only PyTorch environment is appropriate when
the local CUDA build is not working. This command does not repair that environment.

The experiment writes:

- `predictions.parquet`, with evaluation-site observations, point predictions and
  calibrated bounds for both ensembles, plus `noaa_best` point predictions.
- `smokecast/` and `smokecast_nograph/`, each containing the full fitted ensemble,
  preprocessing and CQR objects. Their `node_ids` include reference sites only.
- `summary.csv`, `daily.parquet` and `sites.csv`, using the saved spatial audit's
  common-row scores, default distance bands and exploratory seven-day bootstrap.
  These compare the two learned models on common rows, preserving long-lead
  scores when NOAA has no prediction.
- `noaa_summary.csv`, `noaa_daily.parquet` and `noaa_sites.csv`, comparing
  SmokeCast and `noaa_best` on their own common population. An absent NOAA
  prediction remains visible here. Do not compare errors across the two sets
  of tables without checking their scored populations.
- `partition.json`, the exact input declaration, and `training.log`.
- `manifest.json`, written last on completion, with input hashes, package
  source hashes, fitted populations, settings, member training histories and
  runtime versions. A directory without this completion manifest is incomplete.

Add `--plot` for RMSE and paired-difference PNGs for each lead and comparison.
The manifest lists the files. The plots retain empty distance bands and show
scored-site and common-row counts alongside exploratory day-block bounds.

The default spatial summary uses 1,000 draws and seed zero. Run the saved
[spatial audit](SPATIAL_EVALUATION.md) again into another new directory to select
different model populations, bands or bootstrap settings. Use the
[interval report](INTERVAL_DIAGNOSTICS.md) on the experiment directory to inspect
coverage. None of these reports establish performance at neighborhoods lacking
validation monitors, or authorize changing the reserved protocol.

## Interrupted runs

Each completed ensemble member is saved under `members/`, including its weights,
calibration predictions, evaluation predictions and training history. Checksums
and an atomic completion marker protect the saved member. An interruption during
a later member loses that member's unfinished fit, not the completed members.
Incomplete save attempts remain intact and are ignored on resume.

Repeat the original command with the same output and add `--resume`. The runner
requires the exact input bytes, package source, model settings, ensemble size and
numerical runtime recorded in `run_plan.json`. A mismatch fails before fitting or
changing checkpoints. Corrupt completed members are rejected rather than silently
retrained. The training log is appended; completed member files stay unchanged.
The completion manifest records whether the run resumed and how many members it
reused. A completed experiment cannot be resumed into itself.

Checkpoint resume applies only to runs created with this version of the runner.
Older incomplete directories without `run_plan.json` and member checkpoints need
a fresh output directory. This is member-level resume, not optimizer or epoch
resume. Keep the input tables and code unchanged while a run is in progress.

## Methods references

[Roberts et al. (2017), Ecography](https://www.biom.uni-freiburg.de/mitarbeiter/dormann/roberts-et-al-2017-ecography.pdf/at_download/file)
discuss how dependence and the intended interpolation or extrapolation task affect
validation splits. Withholding scattered monitors does not answer every regional
transfer question. This runner accepts a declared split rather than choosing a
geographic design for the team.

[Romano, Patterson and Candes (2019), NeurIPS](https://proceedings.neurips.cc/paper/2019/file/5103c3584b063c431bd1268e9b5e76fb-Paper.pdf)
derive CQR's marginal coverage guarantee under exchangeability, with a model fitted
separately from calibration. This experiment does not establish those assumptions
for spatially and temporally dependent air-quality data, and it reuses selection
and calibration days. Its coverage reports remain descriptive.
