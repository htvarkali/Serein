# Development skill by sensor distance

The spatial report scores an existing development prediction export at an explicit
set of evaluation monitors. It measures great-circle distance to the nearest
declared reference monitor, then reports paired errors by distance band. It does
not fit a model, obtain observations, or run the reserved evaluation.

```powershell
uv run python -m serein.eval.spatial outputs/backtest/west_us_holdout `
  --points data/interim/west_us/points.parquet `
  --partition C:/path/to/partition.json `
  --model smokecast --model smokecast_nograph --model noaa_best `
  --output C:/path/to/new-spatial-report
```

Use a new output directory whose parent exists. An existing output is refused.
The command accepts either a run directory or its `predictions.parquet` file.
It permits only issue and selected target dates in the configuration's calibration
years, rejects calibration/test-year overlap, and refuses runs carrying
`FINAL_RUN_LOCK.json`. This is a development diagnostic, not completion of D-5.

## Declare the population before inspecting scores

The partition JSON supplies disjoint, nonempty ID lists and a description of
where they came from. IDs are exact strings, including any leading zeroes:

```json
{
  "reference_ids": ["reference_monitor"],
  "evaluation_ids": ["evaluation_monitor"],
  "provenance": "Describe the saved experiment and how these roles were established."
}
```

Every exported prediction ID must appear in one list. Reference-site forecast
rows are counted in the manifest and excluded from scoring. Every declared ID
must exist in the point registry. Extra registry rows do not supply reference
sensors. Display grid rows are refused: they have no observed targets with which
to verify skill. Evaluation sites remain in `sites.csv` even when their predictions
are absent. Missing exported dates cannot be inferred from the file.

The command records the declaration, but **does not establish that fitting,
early stopping, calibration or input construction excluded evaluation-site data**.
Check the experiment that produced the predictions. Do not infer an unseen-site
experiment from a model's `node_ids`, because the saved list includes hidden sites.
For legacy runs, reconstruct a partition only from a known run's settings and node
ordering, and describe that reconstruction in `provenance`.

The current `--holdout-sites` backtest hides selected sites' readings and history
and removes their training targets. Their validation and conformal-calibration
targets remain available. The graph also contains their locations. That experiment
is a development test of withholding training targets and readings, not a fully
spatially independent validation or calibration experiment. This report does not
change that design. Preprocessing is fitted before the training-target mask and
uses the full training table, so even the preprocessing is not independently
fitted on reference sites alone. A stronger spatial test needs an agreed protocol
that keeps the evaluation sites out of model selection and calibration as well.
The separate [reference-only development runner](SPATIAL_EXPERIMENT.md) implements
that site exclusion. It retains the ordinary development time split, including
reuse of reference-site even weeks for selection and calibration.

## Distances and score populations

Coordinates are latitude and longitude in degrees. Distances use a spherical
Earth of radius 6371 km, consistent with the sensor graph. The nearest reference
is found in three-dimensional unit-sphere coordinates, so dateline crossings and
polar locations work. Distinct IDs at the same location legitimately have zero
distance. Tied nearest references may have either ID; the distance is unchanged.

The default bands are `[0,25)`, `[25,50)`, `[50,100)`, `[100,200)` and `[200,infinity)`
km. Set lower boundaries with repeated `--edge-km` options, starting at zero.
The last band always has no upper bound. `distance_band=-1` is the pooled
evaluation population; other bands are zero-based. Blank `distance_hi_km` denotes
an unbounded last band, or the pooled row. Empty bands stay in the report.

Distances describe the declared reference set, not the actual graph edges or
availability of readings on a forecast day. They do not prove that a nearby sensor
influenced a forecast. Use the [map support audit](MAP_SUPPORT.md) to inspect map
graph connectivity and supplied reading availability.

For each selected lead, all selected models score on identical rows with finite
observations and point predictions from every model. The default models are
`smokecast` and `noaa_best`. The first `--model` is the score reference. Adding a
model can reduce the scored population, including scores for previously selected
models. Leads can still have different observations and scored populations.
Missing values are retained in the denominator audits. Infinities, duplicate
site-day keys, invalid coordinates and unclassified sites are errors.

## Outputs and reconstruction

- `summary.csv`: pooled and distance-band RMSE, MAE and signed bias per model/lead,
  paired RMSE differences, site/day counts and exploratory bootstrap bounds.
- `daily.parquet`: input, observed, prediction, pairwise and common-row counts,
  plus error, absolute-error, squared-error and reference-squared-error sums.
  Exported dates with no scoreable rows remain present within each band.
- `sites.csv`: distance, nearest reference ID, counts and scores for every
  evaluation site/model/lead, including sites with no exported rows.
- `manifest.json`: exact-byte SHA-256 hashes of the prediction file, registry,
  partition and configuration, with model, lead, distance and bootstrap settings.

All concentration errors use the saved export's micrograms/m3 units. Bias is
prediction minus observation. Scores weight scored site-days equally; sites with
more observations have more weight. Inspect `sites.csv` before interpreting pooled
results. RMSE is `sqrt(sum(squared_error_sum) / sum(n_scored))`, MAE uses
`absolute_error_sum`, and bias uses `error_sum`. Do not average daily RMSE values.

`n_pairwise` counts rows with this model and an observation. `n_scored` further
requires all selected models; `n_excluded_common` is the difference. `n_sites`
includes every declared evaluation site in the band. `n_sites_exported` counts
those present in the predictions, and `n_sites_scored` counts those with at least
one common scored row. Empty populations have blank scores and
`status=no_scored_rows`, not zero error. Pooled and banded rows overlap; do not
add them together. The daily and site tables likewise summarize the same rows.

`--plot` adds one `spatial_L<lead>.png` per lead, recorded in the manifest. The
upper panel shows RMSE dots; the lower shows differences from the first model
with any available paired bootstrap bounds. Bounds need not contain the observed
difference. Empty populations remain labeled with their counts but have no dot.
These plots describe the fixed declared sites, not a spatial confidence region.

## Uncertainty and interpretation limits

`rmse_difference` is this model's RMSE minus the first selected model's RMSE on
the same population. Positive values mean this model has larger error. The
reference model's own difference is zero. The report resamples whole fixed
calendar blocks of issue days and recomputes both RMSE values on each draw.
The default uses seven-day blocks, 1,000 draws and seed zero. Blocks start at
1970-01-01, so seven-day blocks run Thursday through Wednesday. Calendar gaps
stay gaps. Counts are resampled with errors, preserving site-day weighting.

At least five scored blocks are required; otherwise bounds are blank with
`bootstrap_status=insufficient_blocks`. That floor does not establish that an
interval is reliable. Use `--block-days`, `--n-boot` and `--seed` to examine agreed
sensitivity choices, not to select a favorable interval.

The percentile 95% bounds describe day-block variability **conditional on these
fixed monitors and this declared partition**. They do not resample sites or test
generalization to new locations. Dependence across blocks, few sites in a band,
geographic differences and model selection can distort the interpretation.
Bounds have no multiplicity adjustment across bands, models or leads. Sensor
distance is not a randomized treatment, so a distance gradient is not a causal
estimate of the value of adding sensors. These scores do not verify neighborhood
forecast accuracy or interval calibration. See the separate
[interval report](INTERVAL_DIAGNOSTICS.md) for descriptive bounds coverage.

## Legacy development example, November 6, 2026

The archived five-member development holdout export used 85 evaluation monitors
and 340 reference monitors. Its partition was reconstructed from the recorded
0.2 holdout fraction, saved node ordering and NumPy generator seed 1234. The
legacy experiment retains the preprocessing, selection and calibration limits
described above; this is not the reference-only runner's output.

Selecting SmokeCast, no-graph and `noaa_best` at lead 1 produced:

| Nearest reference distance | Declared sites | Scored sites | Common scored site-days |
|---|---|---|---|
| 0 to less than 25 km | 56 | 48 | 3,522 |
| 25 to less than 50 km | 23 | 17 | 1,245 |
| 50 to less than 100 km | 6 | 4 | 274 |
| 100 to less than 200 km | 0 | 0 | 0 |
| 200 km or more | 0 | 0 | 0 |
| Pooled | 85 | 69 | 5,041 |

The last two bands cannot measure distant-site skill, and the 50 to 100 km band
contains only four scored monitors. Day-block bounds do not compensate for that
limited spatial support. This audit does not establish neighborhood-scale skill
or replace the historical results snapshot.

Prediction-file SHA-256:
`d3d6517376a33aa872b4a3ac6d7d86afce8d53dc84f8b699838d38d84a8d698b`.
