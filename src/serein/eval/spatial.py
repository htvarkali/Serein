"""Measure saved development forecast skill by distance from reference sensors."""

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
from scipy.spatial import cKDTree

from serein.eval.comparison import _nonnegative_integer, _prediction_dates
from serein.eval.episode_inputs import _choices, _load_predictions, _values


def _ids(values, name):
    if (not isinstance(values, list) or not values
            or any(not isinstance(value, str) or not value.strip() for value in values)
            or len(set(values)) != len(values)):
        raise ValueError(f"{name} must be a nonempty list of distinct nonblank strings")
    return values


def spatial_sites(points: pd.DataFrame, partition: dict, *, edges=(0, 25, 50, 100, 200)):
    """Locate evaluation sites relative to a declared, disjoint reference set.

    A declaration is not proof that model fitting or calibration excluded sites.
    Coordinates use a spherical Earth with radius 6371 km, like the sensor graph.
    """
    if not isinstance(partition, dict):
        raise TypeError("partition must be an object")
    reference = _ids(partition.get("reference_ids"), "reference_ids")
    evaluation = _ids(partition.get("evaluation_ids"), "evaluation_ids")
    if set(reference) & set(evaluation):
        raise ValueError("reference and evaluation IDs must be disjoint")
    if not isinstance(partition.get("provenance"), str) or not partition["provenance"].strip():
        raise ValueError("partition requires a nonblank provenance description")
    if not points.columns.is_unique or not {"point_id", "lat", "lon"}.issubset(points):
        raise ValueError("registry requires unique columns including point_id, lat and lon")
    _ids(points.point_id.tolist(), "registry point IDs")
    registry = points.set_index("point_id")
    if not set(reference + evaluation).issubset(registry.index):
        raise ValueError("partition IDs must all exist in the registry")
    selected = registry.loc[reference + evaluation]
    if "kind" in selected and selected.kind.eq("grid").any():
        raise ValueError("partition must contain monitoring sites, not display grid points")
    xy = selected[["lat", "lon"]].to_numpy(dtype=float, na_value=np.nan)
    if (not np.isfinite(xy).all() or (np.abs(xy[:, 0]) > 90).any()
            or (np.abs(xy[:, 1]) > 180).any()):
        raise ValueError("partition coordinates must be finite valid latitude and longitude")
    raw_edges = list(edges)
    if any(isinstance(edge, (bool, np.bool_)) for edge in raw_edges):
        raise ValueError("distance edges must be finite increasing numbers starting at zero")
    edges = np.asarray(raw_edges, dtype=float)
    if (edges.ndim != 1 or not len(edges) or not np.isfinite(edges).all()
            or edges[0] != 0 or np.any(np.diff(edges) <= 0)):
        raise ValueError("distance edges must be finite increasing numbers starting at zero")
    lat, lon = np.radians(xy).T
    xyz = np.column_stack([np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)])
    # Euclidean chord distance on the unit sphere has the same nearest neighbor.
    chord, nearest = cKDTree(xyz[:len(reference)]).query(xyz[len(reference):], k=1)
    distance = 2 * 6371.0 * np.arcsin(np.clip(chord / 2, 0, 1))
    index = np.searchsorted(edges, distance, side="right") - 1
    sites = selected.loc[evaluation, ["lat", "lon"]].reset_index()
    sites["nearest_reference_id"] = np.asarray(reference)[nearest]
    sites["nearest_reference_km"] = distance
    sites["distance_band"] = index
    bands = pd.DataFrame({"distance_band": np.arange(len(edges)), "distance_lo_km": edges,
                          "distance_hi_km": [*edges[1:], np.nan]})
    return sites, bands


def _scores(totals):
    n = totals["n_scored"]
    return {"rmse": float(np.sqrt(totals["squared_error_sum"] / n)) if n else np.nan,
            "mae": float(totals["absolute_error_sum"] / n) if n else np.nan,
            "bias": float(totals["error_sum"] / n) if n else np.nan}


def _difference_bounds(daily, *, block_days, n_boot, seed):
    blocks = (daily.issue_date - pd.Timestamp("1970-01-01")).dt.days // block_days
    totals = daily.groupby(blocks)[["n_scored", "squared_error_sum", "reference_squared_error_sum"]].sum()
    totals = totals.loc[totals.n_scored.gt(0)].to_numpy(dtype=float)
    result = {"n_blocks": len(totals), "bootstrap_status": "insufficient_blocks",
              "rmse_difference_ci_lo": np.nan, "rmse_difference_ci_hi": np.nan}
    if len(totals) < 5:
        return result
    rng = np.random.default_rng(seed)
    samples = np.empty(n_boot)
    for start in range(0, n_boot, 256):
        stop = min(start + 256, n_boot)
        chosen = rng.integers(0, len(totals), size=(stop - start, len(totals)))
        sums = totals[chosen].sum(axis=1)
        samples[start:stop] = np.sqrt(sums[:, 1] / sums[:, 0]) - np.sqrt(sums[:, 2] / sums[:, 0])
    result.update(bootstrap_status="ok", **dict(zip(
        ("rmse_difference_ci_lo", "rmse_difference_ci_hi"),
        map(float, np.percentile(samples, [2.5, 97.5])), strict=True)))
    return result


def analyze_spatial(predictions: pd.DataFrame, points: pd.DataFrame, partition: dict, *,
                    models=("smokecast", "noaa_best"), leads=None,
                    edges=(0, 25, 50, 100, 200), block_days=7, n_boot=1000, seed=0):
    """Return band summaries, daily totals, and per-site scores on common rows.

    The first model is the score reference. All selected models use the same
    observation and complete point predictions at a lead. Reference-site rows
    in the input are excluded; unclassified input sites fail instead of vanishing.
    Empty bands and evaluation sites without exported rows remain visible.
    """
    days = _prediction_dates(predictions)
    if predictions.empty:
        raise ValueError("predictions must not be empty")
    sites, bands = spatial_sites(points, partition, edges=edges)
    declared = set(partition["reference_ids"] + partition["evaluation_ids"])
    if not predictions.point_id.isin(declared).all():
        raise ValueError("all prediction sites must be classified in the partition")
    models = _choices(models, "models")
    leads = _choices(sorted(int(match[1]) for column in predictions
                           if (match := re.fullmatch(r"y_L(0|[1-9]\d*)", str(column))))
                     if leads is None else leads, "leads", integers=True)
    for name, value in (("block_days", block_days), ("n_boot", n_boot), ("seed", seed)):
        _nonnegative_integer(value, name)
        if name != "seed" and value == 0:
            raise ValueError(f"{name} must be positive")
    mask = predictions.point_id.isin(sites.point_id).to_numpy()
    frame = predictions.loc[mask].copy()
    frame["issue_date"] = days[mask]
    summaries, audits, site_scores = [], [], []
    site_index = sites.set_index("point_id")
    band_index = frame.point_id.map(site_index.distance_band).to_numpy()
    for lead in leads:
        required = [f"y_L{lead}"] + [f"{model}_L{lead}" for model in models]
        if not set(required).issubset(predictions):
            raise ValueError(f"missing prediction columns: {', '.join(sorted(set(required) - set(predictions)))}")
        # Validate reference-site values too, even though only evaluation rows score.
        values = {column: _values(predictions, column)[mask] for column in required}
        obs = values[f"y_L{lead}"]
        observed = np.isfinite(obs)
        available = {model: np.isfinite(values[f"{model}_L{lead}"]) for model in models}
        common = observed & np.logical_and.reduce(list(available.values()))
        with np.errstate(over="ignore", invalid="ignore"):
            errors = {model: values[f"{model}_L{lead}"][common] - obs[common] for model in models}
            squares = {model: error ** 2 for model, error in errors.items()}
        if any(not np.isfinite(value).all() for value in [*errors.values(), *squares.values()]):
            raise ValueError("forecast errors overflow; check concentration units")
        for model in models:
            row = pd.DataFrame({"issue_date": frame.issue_date.to_numpy(),
                                "point_id": frame.point_id.to_numpy(), "n_input": 1,
                                "n_observed": observed.astype(int),
                                "n_prediction": available[model].astype(int),
                                "n_pairwise": (observed & available[model]).astype(int),
                                "n_scored": common.astype(int), "error_sum": 0.,
                                "absolute_error_sum": 0., "squared_error_sum": 0.,
                                "reference_squared_error_sum": 0.})
            row.loc[common, "error_sum"] = errors[model]
            row.loc[common, "absolute_error_sum"] = np.abs(errors[model])
            row.loc[common, "squared_error_sum"] = squares[model]
            row.loc[common, "reference_squared_error_sum"] = squares[models[0]]
            numeric = row.columns.difference(["issue_date", "point_id"]).tolist()
            per_site = row.groupby("point_id", sort=True)[numeric].sum()
            per_site["n_days_scored"] = row.loc[common].groupby("point_id").size()
            detail = sites.merge(per_site.reset_index(), how="left", on="point_id", validate="one_to_one")
            detail[numeric + ["n_days_scored"]] = detail[numeric + ["n_days_scored"]].fillna(0)
            for name in ("n_input", "n_observed", "n_prediction", "n_pairwise", "n_scored", "n_days_scored"):
                detail[name] = detail[name].astype("int64")
            detail["model"], detail["lead"] = model, int(lead)
            detail["status"] = np.where(detail.n_scored.gt(0), "ok", "no_scored_rows")
            for metric in ("rmse", "mae", "bias"):
                detail[metric] = [_scores(record)[metric] for record in detail.to_dict("records")]
            site_scores.append(detail)
            for band in [-1, *bands.distance_band.tolist()]:
                selected = np.ones(len(frame), dtype=bool) if band == -1 else band_index == band
                daily = row.loc[selected].groupby("issue_date", sort=True)[numeric].sum().reset_index()
                totals = daily[numeric].sum()
                if not np.isfinite(totals.to_numpy(dtype=float)).all():
                    raise ValueError("forecast error totals overflow; check concentration units")
                counts = {name: int(totals[name]) for name in numeric if name.startswith("n_")}
                evaluated = sites if band == -1 else sites.loc[sites.distance_band.eq(band)]
                n = counts["n_scored"]
                metrics = _scores(totals)
                reference_rmse = float(np.sqrt(totals.reference_squared_error_sum / n)) if n else np.nan
                key = {"model": model, "lead": int(lead), "distance_band": band}
                summary = {**key, **counts, "n_excluded_common": counts["n_pairwise"] - n,
                           "n_sites": len(evaluated),
                           "n_sites_exported": int(evaluated.point_id.isin(frame.point_id).sum()),
                           "n_sites_scored": int(detail.loc[detail.point_id.isin(evaluated.point_id), "n_scored"].gt(0).sum()),
                           "n_days_input": len(daily), "n_days_scored": int(daily.n_scored.gt(0).sum()),
                           "status": "ok" if n else "no_scored_rows", **metrics,
                           "reference_model": models[0], "reference_rmse": reference_rmse,
                           "rmse_difference": metrics["rmse"] - reference_rmse,
                           **_difference_bounds(daily, block_days=block_days, n_boot=n_boot, seed=seed)}
                summaries.append(summary)
                for name, value in key.items():
                    daily[name] = value
                audits.append(daily)
    summary = pd.DataFrame(summaries).merge(bands, how="left", on="distance_band", validate="many_to_one")
    return summary, pd.concat(audits, ignore_index=True), pd.concat(site_scores, ignore_index=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("run", type=Path, help="development run or predictions parquet")
    parser.add_argument("--points", required=True, type=Path, help="point registry parquet")
    parser.add_argument("--partition", required=True, type=Path, help="declared reference/evaluation JSON")
    parser.add_argument("--config", type=Path, default=Path("configs/west_us.yaml"))
    parser.add_argument("--output", required=True, type=Path, help="new report directory")
    parser.add_argument("--model", action="append", dest="models", help="first model is the score reference")
    parser.add_argument("--lead", action="append", type=int, dest="leads")
    parser.add_argument("--edge-km", action="append", type=float, dest="edges")
    parser.add_argument("--block-days", type=int, default=7)
    parser.add_argument("--n-boot", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--plot", action="store_true", help="plot RMSE and paired differences by distance")
    args = parser.parse_args(argv)
    source = args.run / "predictions.parquet" if args.run.is_dir() else args.run
    try:
        if args.output.exists():
            raise FileExistsError(f"output already exists: {args.output}")
        if not args.output.parent.is_dir():
            raise ValueError("output parent must exist")
        if (source.parent / "FINAL_RUN_LOCK.json").exists():
            raise ValueError("spatial reports accept development runs only")
        payloads = {"points": args.points.read_bytes(), "partition": args.partition.read_bytes(),
                    "config": args.config.read_bytes()}
        config = yaml.safe_load(io.BytesIO(payloads["config"]))
        years = _choices(config["split"]["calibrate"], "calibration years", integers=True)
        reserved = _choices(config["split"]["test"], "test years", integers=True)
        if set(years) & set(reserved):
            raise ValueError("calibration and reserved test years must be disjoint")
        predictions, digest = _load_predictions(source)
        days = _prediction_dates(predictions)
        if not days.year.isin(years).all():
            raise ValueError("issue dates must belong to configured calibration years")
        partition = json.loads(payloads["partition"])
        edges = args.edges if args.edges is not None else [0, 25, 50, 100, 200]
        summary, daily, sites = analyze_spatial(
            predictions, pd.read_parquet(io.BytesIO(payloads["points"])), partition,
            models=args.models or ("smokecast", "noaa_best"), leads=args.leads,
            edges=edges, block_days=args.block_days, n_boot=args.n_boot, seed=args.seed)
        for lead in summary.lead.unique():
            if not (days + pd.Timedelta(days=int(lead))).year.isin(years).all():
                raise ValueError("target dates must belong to configured calibration years")
        manifest = {"report_version": 1, "source": str(source.resolve()), "sha256": digest,
                    "inputs": {name: {"path": str(getattr(args, name).resolve()),
                                      "sha256": hashlib.sha256(payload).hexdigest()}
                               for name, payload in payloads.items()},
                    "partition_provenance": partition["provenance"], "development_years": years,
                    "n_input": len(predictions),
                    "n_reference_rows_excluded": int(predictions.point_id.isin(partition["reference_ids"]).sum()),
                    "models": summary.model.drop_duplicates().tolist(),
                    "leads": summary.lead.drop_duplicates().tolist(),
                    "distance_edges_km": edges, "earth_radius_km": 6371.0,
                    "block_days": args.block_days, "block_origin": "1970-01-01",
                    "n_boot": args.n_boot, "seed": args.seed,
                    "plots": [f"spatial_L{lead}.png" for lead in summary.lead.drop_duplicates()]
                    if args.plot else [],
                    "population": "common rows across selected models at each lead",
                    "interpretation": "declared partition, not verified training exclusion; exploratory fixed-site development scores"}
        args.output.mkdir(exist_ok=False)
        summary.to_csv(args.output / "summary.csv", index=False)
        daily.to_parquet(args.output / "daily.parquet", index=False)
        sites.to_csv(args.output / "sites.csv", index=False)
        if args.plot:
            from serein.eval.spatial_plots import plot_spatial_scores

            for lead in summary.lead.drop_duplicates():
                plot_spatial_scores(summary, int(lead), args.output / f"spatial_L{lead}.png")
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, KeyError, OverflowError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    print(f"wrote {args.output}: {len(summary)} spatial summaries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
