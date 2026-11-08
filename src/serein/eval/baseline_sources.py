"""Separate the saved NOAA fallback baseline into its actual forecast sources."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import re
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from serein.eval.comparison import _prediction_dates
from serein.eval.episode_inputs import _choices, _load_predictions, _values

SOURCES = ("aqm_bc", "hrrr_smoke", "persistence", "unavailable")
SUMS = ("model_squared_error", "baseline_squared_error", "model_absolute_error",
        "baseline_absolute_error", "model_error", "baseline_error")
COUNTS = ("n_input", "n_observed", "n_model", "n_baseline", "n_pairwise", "n_scored")


def _source_chain(frame: pd.DataFrame, lead: int) -> tuple[np.ndarray, np.ndarray]:
    expected = np.full(len(frame), np.nan)
    source = np.full(len(frame), "unavailable", dtype=object)
    for name in SOURCES[:-1]:
        values = _values(frame, f"{name}_L{lead}")
        select = ~np.isfinite(expected) & np.isfinite(values)
        expected[select], source[select] = values[select], name
    actual = _values(frame, f"noaa_best_L{lead}")
    matches = np.isclose(actual, expected, rtol=1e-5, atol=1e-6, equal_nan=True)
    if not matches.all():
        raise ValueError(f"noaa_best_L{lead} disagrees with fallback chain on "
                         f"{int((~matches).sum())} rows")
    return source, actual


def analyze_sources(predictions: pd.DataFrame, *, models=("smokecast",), leads=None,
                    common_rows: bool = False) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Return paired errors by actual baseline source and daily audit totals.

    Source selection uses exported, adjusted component forecasts, including rows
    without observations. It cannot recover the raw provider or extraction history.
    The pooled and NOAA-only groups overlap the disjoint source groups.
    """
    days = _prediction_dates(predictions)
    if predictions.empty:
        raise ValueError("predictions must not be empty")
    models = _choices(models, "models")
    if not isinstance(common_rows, (bool, np.bool_)):
        raise TypeError("common_rows must be boolean")
    leads = _choices(sorted(int(match[1]) for column in predictions
                           if (match := re.fullmatch(r"y_L(0|[1-9]\d*)", str(column))))
                     if leads is None else leads, "leads", integers=True)
    summaries, audits = [], []
    for lead in leads:
        required = ([f"{name}_L{lead}" for name in (*SOURCES[:-1], "noaa_best", "y")]
                    + [f"{name}_L{lead}" for name in models])
        missing = sorted(set(required) - set(predictions))
        if missing:
            raise ValueError(f"missing forecast columns: {', '.join(missing)}")
        source, baseline = _source_chain(predictions, lead)
        obs = _values(predictions, f"y_L{lead}")
        observed, reference = np.isfinite(obs), np.isfinite(baseline)
        forecasts = {name: _values(predictions, f"{name}_L{lead}") for name in models}
        common = observed & reference & np.logical_and.reduce(
            [np.isfinite(values) for values in forecasts.values()])
        masks = [("all", np.ones(len(predictions), dtype=bool)),
                 ("noaa_only", np.isin(source, SOURCES[:2]))]
        masks.extend((name, source == name) for name in SOURCES)
        for model, forecast in forecasts.items():
            available = np.isfinite(forecast)
            paired = observed & reference & available
            scored = common if common_rows else paired
            row = pd.DataFrame({
                "issue_date": days, "n_input": 1, "n_observed": observed.astype(int),
                "n_model": available.astype(int), "n_baseline": reference.astype(int),
                "n_pairwise": paired.astype(int), "n_scored": scored.astype(int),
            })
            with np.errstate(over="ignore", invalid="ignore"):
                model_error = forecast[scored] - obs[scored]
                baseline_error = baseline[scored] - obs[scored]
                errors = (model_error ** 2, baseline_error ** 2, np.abs(model_error),
                          np.abs(baseline_error), model_error, baseline_error)
            for name, values in zip(SUMS, errors, strict=True):
                if not np.isfinite(values).all():
                    raise ValueError("forecast errors overflow; check concentration units")
                row[name] = 0.
                row.loc[scored, name] = values
            for name, mask in masks:
                daily = row.loc[mask].groupby("issue_date", sort=True).sum().reset_index()
                totals = daily[list(SUMS)].sum().to_numpy(dtype=float)
                if not np.isfinite(totals).all():
                    raise ValueError("error totals overflow; check concentration units")
                n = int(daily.n_scored.sum())
                means = totals / n if n else np.full(len(SUMS), np.nan)
                rmse_model, rmse_baseline = np.sqrt(means[:2])
                key = {"model": model, "lead": int(lead), "source": name}
                summary = {**key, "population": "common_rows" if common_rows else "model_rows",
                           **{c: int(daily[c].sum()) for c in COUNTS},
                           "n_days_input": len(daily),
                           "n_days_scored": int(daily.n_scored.gt(0).sum()),
                           "status": "ok" if n else "no_scored_rows",
                           "model_rmse": rmse_model, "baseline_rmse": rmse_baseline,
                           "rmse_diff": rmse_model - rmse_baseline,
                           "skill": 1 - rmse_model / rmse_baseline if rmse_baseline > 0 else np.nan,
                           "model_mae": means[2], "baseline_mae": means[3],
                           "model_bias": means[4], "baseline_bias": means[5]}
                summary["n_excluded"] = summary["n_input"] - n
                summary["n_excluded_common"] = summary["n_pairwise"] - n
                summaries.append(summary)
                for column, value in key.items():
                    daily[column] = value
                audits.append(daily)
    return pd.DataFrame(summaries), pd.concat(audits, ignore_index=True)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="development run directory or predictions parquet")
    parser.add_argument("--config", type=Path, default=Path("configs/west_us.yaml"))
    parser.add_argument("--output", type=Path, required=True, help="new report directory")
    parser.add_argument("--model", action="append", dest="models")
    parser.add_argument("--lead", action="append", type=int, dest="leads")
    parser.add_argument("--common-rows", action="store_true")
    args = parser.parse_args(argv)
    source = args.run / "predictions.parquet" if args.run.is_dir() else args.run
    try:
        if args.output.exists():
            raise FileExistsError(f"output already exists: {args.output}")
        if not args.output.parent.is_dir():
            raise ValueError("output parent must exist")
        if (source.parent / "FINAL_RUN_LOCK.json").exists():
            raise ValueError("source reports accept development runs only")
        predictions, digest = _load_predictions(source)
        config_bytes = args.config.read_bytes()
        config = yaml.safe_load(io.BytesIO(config_bytes))
        years = config["split"]["calibrate"]
        reserved = config["split"].get("test", [])
        if (not isinstance(years, list) or not years
                or any(type(year) is not int or not 1 <= year <= 9999 for year in years)
                or not isinstance(reserved, list) or set(years).intersection(reserved)):
            raise ValueError("calibration years must be nonempty integers disjoint from test years")
        days = _prediction_dates(predictions)
        if not days.year.isin(years).all():
            raise ValueError("issue dates must belong to configured calibration years")
        summary, daily = analyze_sources(predictions, models=args.models or ["smokecast"],
                                         leads=args.leads, common_rows=args.common_rows)
        for lead in summary.lead.unique():
            if not (days + pd.Timedelta(days=int(lead))).year.isin(years).all():
                raise ValueError("target dates must belong to configured calibration years")
        manifest = {"report_version": 1, "source": str(source.resolve()), "sha256": digest,
                    "config": str(args.config.resolve()),
                    "config_sha256": hashlib.sha256(config_bytes).hexdigest(),
                    "development_years": years, "n_input": len(predictions),
                    "models": summary.model.drop_duplicates().tolist(),
                    "leads": summary.lead.drop_duplicates().tolist(),
                    "common_rows": args.common_rows, "priority": list(SOURCES),
                    "chain_rtol": 1e-5, "chain_atol": 1e-6,
                    "interpretation": "descriptive development errors by adjusted fallback source; "
                                      "persistence is not a NOAA forecast"}
        args.output.mkdir(exist_ok=False)
        summary.to_csv(args.output / "summary.csv", index=False)
        daily.to_parquet(args.output / "daily.parquet", index=False)
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n",
                                                   encoding="utf-8")
    except (OSError, TypeError, ValueError, KeyError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    print(f"wrote {args.output}: {len(summary)} source summaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
