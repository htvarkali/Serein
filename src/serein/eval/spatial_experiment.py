"""Run a reference-only spatial development experiment from saved feature tables."""

from __future__ import annotations

import argparse
import hashlib
import io
import json
import platform
from dataclasses import asdict, dataclass, replace
from importlib.metadata import version
from pathlib import Path

import numpy as np
import pandas as pd
import yaml

from serein.eval.comparison import _nonnegative_integer, _prediction_dates
from serein.eval.episode_inputs import _choices, _values
from serein.eval.spatial import analyze_spatial, spatial_sites


@dataclass
class SpatialExperiment:
    prep: object
    train: object
    validation: object
    calibration: object
    prediction: object
    reference_graph: object
    prediction_graph: object
    observations: pd.DataFrame
    prediction_rows: pd.DataFrame
    reference_ids: list[str]
    evaluation_ids: list[str]
    leads: list[int]


def prepare_experiment(train, calibrate, points, partition, *, k=10, max_km=300):
    """Fit preprocessing on reference rows and build a one-way evaluation graph.

    Evaluation observations are retained separately for scoring. They never
    enter GraphData. Evaluation sensor features cannot send messages to any node.
    Early stopping and calibration reuse reference-site even ISO weeks, matching
    the existing development backtest; odd weeks supply evaluation predictions.
    """
    from serein.features.graph import build_knn_graph
    from serein.features.prepare import (
        Prep,
        is_sensor_feature,
        leads_of,
        neighbor_base,
        to_graph_data,
    )
    from serein.models.infer import sensor_plus_grid_graph

    spatial_sites(points, partition)
    _nonnegative_integer(k, "k")
    if isinstance(max_km, (bool, np.bool_)) or not np.isfinite(max_km) or max_km <= 0:
        raise ValueError("max_km must be finite and positive")
    reference, evaluation = partition["reference_ids"], partition["evaluation_ids"]
    tables = []
    for name, table in (("train", train), ("calibrate", calibrate)):
        days = _prediction_dates(table)
        table = table.copy()
        table["issue_date"] = days
        if not {"obs_prevday", "obs_last24", "y_L0"}.issubset(table):
            raise ValueError(f"{name} requires obs_prevday, obs_last24 and y_L0")
        tables.append(table)
    train, calibrate = tables
    # An unused evaluation value can promote an entire input column to object.
    # Infer fit-column types again using only the permitted reference rows.
    train = train.loc[train.point_id.isin(reference)].reset_index(drop=True).infer_objects()
    if not set(reference).issubset(train.point_id):
        raise ValueError("every reference site needs training rows")
    leads = leads_of(train)
    if leads != leads_of(calibrate):
        raise ValueError("training and calibration observation leads must match")
    even = pd.DatetimeIndex(calibrate.issue_date).isocalendar().week.to_numpy() % 2 == 0
    reference_cal = calibrate.loc[even & calibrate.point_id.isin(reference)].reset_index(drop=True).infer_objects()
    prediction_rows = calibrate.loc[~even & calibrate.point_id.isin(reference + evaluation)].reset_index(drop=True)
    observations = prediction_rows.loc[prediction_rows.point_id.isin(evaluation)].reset_index(drop=True)
    if reference_cal.empty or observations.empty:
        raise ValueError("need reference even-week and evaluation odd-week calibration rows")
    for lead in leads:
        _values(observations, f"y_L{lead}")
    if not set(reference).issubset(reference_cal.point_id):
        raise ValueError("every reference site needs even-week calibration rows")
    # Validate only permitted fit targets; evaluation training values are unused.
    for name, table in (("training", train), ("reference calibration", reference_cal)):
        for lead in leads:
            if not np.isfinite(_values(table, f"y_L{lead}")).any():
                raise ValueError(f"{name} has no observed targets at lead {lead}")
    prep = Prep().fit(train)
    registry = points.set_index("point_id")
    ref_xy = registry.loc[reference, ["lat", "lon"]].to_numpy(float)
    eval_xy = registry.loc[evaluation, ["lat", "lon"]].to_numpy(float)
    reference_graph = build_knn_graph(ref_xy[:, 0], ref_xy[:, 1], k=k, max_km=max_km)
    prediction_graph = sensor_plus_grid_graph(ref_xy, eval_xy, k=k, max_km=max_km)
    gd_train = to_graph_data(train, prep, reference)
    gd_cal = to_graph_data(reference_cal, prep, reference)
    gd_train.base_nbr = neighbor_base(gd_train, train, prep, reference_graph)
    gd_cal.base_nbr = neighbor_base(gd_cal, reference_cal, prep, reference_graph)
    sanitized = prediction_rows.copy()
    evaluation_rows = sanitized.point_id.isin(evaluation)
    for column in sanitized:
        if is_sensor_feature(column):
            sanitized.loc[evaluation_rows, column] = np.nan
        if column.startswith("y_L"):
            sanitized[column] = np.nan
    sanitized = sanitized.infer_objects()
    gd_prediction = to_graph_data(sanitized, prep, reference + evaluation)
    n_ref = len(reference)
    for index, name in enumerate(gd_prediction.feat_names):
        if is_sensor_feature(name):
            gd_prediction.X[:, n_ref:, index] = float(name.endswith("__missing"))
    is_reference = np.arange(len(reference + evaluation)) < n_ref
    neighbor = neighbor_base(gd_prediction, sanitized, prep, prediction_graph, sources=is_reference)
    gd_prediction.base[:, n_ref:] = neighbor[:, n_ref:]
    return SpatialExperiment(prep, gd_train, gd_cal, gd_cal, gd_prediction,
                             reference_graph, prediction_graph, observations, sanitized,
                             reference, evaluation, leads)


def _row_predictions(q, gd, n_rows):
    result = np.full((n_rows, *q.shape[2:]), np.nan, dtype=q.dtype)
    day, node = np.where(gd.row_index >= 0)
    result[gd.row_index[day, node]] = q[day, node]
    return result


def fit_experiment(experiment, cfg, *, seeds=5, log=print, cache=None):
    """Fit graph and no-graph ensembles without evaluation-site targets or inputs."""
    from serein.models.baselines import baselines
    from serein.models.conformal import CQR, calibrate_quantiles
    from serein.models.gnn import QUANTILES
    from serein.models.train import Trainer

    _nonnegative_integer(seeds, "seeds")
    if seeds == 0:
        raise ValueError("seeds must be positive")
    if getattr(cfg, "history", 1) != 1:
        raise ValueError("spatial experiments currently support single-day inputs only")
    output = experiment.observations[["issue_date", "point_id"]
                                     + (["hms_prev"] if "hms_prev" in experiment.observations else [])
                                     + [f"y_L{lead}" for lead in experiment.leads]].copy()
    fitted = {}
    n_features = experiment.train.X.shape[-1]
    for model, use_graph in (("smokecast", True), ("smokecast_nograph", False)):
        calibration, prediction, states, histories = [], [], [], []
        for member in range(seeds):
            member_cfg = replace(cfg, use_graph=use_graph, seed=cfg.seed + member)
            log(f"training {model}, seed {member_cfg.seed}")
            trainer = Trainer(n_features, len(experiment.leads), experiment.reference_graph,
                              experiment.train.feat_names, member_cfg)
            cached = None if cache is None else cache.load(
                model, member_cfg.seed,
                calibration_shape=(*experiment.calibration.Y.shape, len(QUANTILES)),
                prediction_shape=(*experiment.prediction.Y.shape, len(QUANTILES)))
            if cached is not None:
                state, q_cal, q_prediction, history = cached
                trainer.model.load_state_dict(state)
                states.append(state)
                calibration.append(q_cal)
                prediction.append(q_prediction)
                histories.append(history)
                log(f"reused completed {model}, seed {member_cfg.seed}")
                continue
            histories.append(trainer.fit(experiment.train, experiment.validation, log=log))
            calibration.append(trainer.predict(experiment.calibration))
            states.append({key: value.detach().cpu().clone()
                           for key, value in trainer.model.state_dict().items()})
            predictor = Trainer(n_features, len(experiment.leads), experiment.prediction_graph,
                                experiment.train.feat_names, member_cfg)
            predictor.model.load_state_dict(states[-1])
            prediction.append(predictor.predict(experiment.prediction))
            if cache is not None:
                cache.save(model, member_cfg.seed, states[-1], calibration[-1], prediction[-1], histories[-1])
        q_cal, q_test = np.mean(calibration, axis=0), np.mean(prediction, axis=0)
        shape = (-1, len(experiment.leads), len(QUANTILES))
        cal_flat = q_cal.reshape(shape)
        cqr = CQR(alpha=.1).fit(cal_flat[..., 0], cal_flat[..., -1], cal_flat[..., 2],
                              experiment.calibration.Y.reshape(-1, len(experiment.leads)))
        q_test = calibrate_quantiles(q_test.reshape(shape), cqr, QUANTILES).reshape(q_test.shape)
        aligned = _row_predictions(q_test, experiment.prediction, len(experiment.prediction_rows))
        eval_rows = experiment.prediction_rows.point_id.isin(experiment.evaluation_ids).to_numpy()
        aligned = np.expm1(aligned[eval_rows])
        if not np.isfinite(aligned).all() or np.any(np.diff(aligned, axis=-1) < 0) or np.any(aligned < 0):
            raise ValueError("spatial forecasts must be finite, ordered and nonnegative")
        for index, lead in enumerate(experiment.leads):
            output[f"{model}_L{lead}"] = aligned[:, index, 2]
            output[f"{model}_lo_L{lead}"] = aligned[:, index, 0]
            output[f"{model}_hi_L{lead}"] = aligned[:, index, -1]
        fitted[model] = {"states": states, "cqr": cqr, "cfg": replace(cfg, use_graph=use_graph),
                         "history": histories, "device": str(trainer.dev)}
    # At evaluation sites, noaa_best has no local persistence or site background.
    evaluation_rows = experiment.prediction_rows.loc[
        experiment.prediction_rows.point_id.isin(experiment.evaluation_ids)]
    noaa = baselines(evaluation_rows, experiment.prep, experiment.leads)["noaa_best"]
    for index, lead in enumerate(experiment.leads):
        output[f"noaa_best_L{lead}"] = noaa[:, index]
    return output, fitted


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", required=True, type=Path, help="development training table")
    parser.add_argument("--calibrate", required=True, type=Path, help="development calibration table")
    parser.add_argument("--points", required=True, type=Path)
    parser.add_argument("--partition", required=True, type=Path)
    parser.add_argument("--config", type=Path, default=Path("configs/west_us.yaml"))
    parser.add_argument("--output", required=True, type=Path, help="new experiment directory")
    parser.add_argument("--epochs", type=int, default=300)
    parser.add_argument("--seeds", type=int, default=5)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--hidden", type=int, default=96)
    parser.add_argument("--layers", type=int, default=3)
    parser.add_argument("--threads", type=int, default=1)
    parser.add_argument("--plot", action="store_true", help="plot each paired spatial score report")
    parser.add_argument("--resume", action="store_true", help="reuse completed members from this output")
    args = parser.parse_args(argv)
    try:
        if (args.output.exists() and not args.resume) or not args.output.parent.is_dir():
            raise ValueError("output must be new and its parent must exist")
        if args.resume and not args.output.is_dir():
            raise ValueError("resume output must be an existing incomplete experiment")
        for name in ("epochs", "seeds", "hidden", "layers", "threads"):
            _nonnegative_integer(getattr(args, name), name)
            if getattr(args, name) == 0:
                raise ValueError(f"{name} must be positive")
        _nonnegative_integer(args.seed, "seed")
        if args.hidden < 2 or args.hidden % 4:
            raise ValueError("hidden must be at least four and divisible by four attention heads")
        if any((path.parent / "FINAL_RUN_LOCK.json").exists() for path in (args.train, args.calibrate)):
            raise ValueError("spatial experiments accept development inputs only")
        payloads = {name: getattr(args, name).read_bytes()
                    for name in ("train", "calibrate", "points", "partition", "config")}
        config = yaml.safe_load(io.BytesIO(payloads["config"]))
        years = {name: _choices(config["split"][name], f"{name} years", integers=True)
                 for name in ("train", "calibrate", "test")}
        if any(set(years[a]) & set(years[b])
               for a, b in (("train", "calibrate"), ("train", "test"), ("calibrate", "test"))):
            raise ValueError("training, calibration and reserved test years must be disjoint")
        tables = {name: pd.read_parquet(io.BytesIO(payloads[name])) for name in ("train", "calibrate")}
        for name, table in tables.items():
            days = _prediction_dates(table)
            if not days.year.isin(years[name]).all():
                raise ValueError(f"{name} issue dates must belong to configured {name} years")
            for column in table:
                if column.startswith("y_L"):
                    lead = int(column[3:])
                    if lead < 0 or not (days + pd.Timedelta(days=lead)).year.isin(years[name]).all():
                        raise ValueError(f"{name} target dates must belong to configured {name} years")
        points = pd.read_parquet(io.BytesIO(payloads["points"]))
        partition = json.loads(payloads["partition"])
        experiment = prepare_experiment(tables["train"], tables["calibrate"], points, partition,
                                        k=config["graph"]["k_neighbors"], max_km=config["graph"]["max_km"])
        import torch

        from serein.eval import spatial_checkpoint
        from serein.models import train
        from serein.models.infer import save_artifacts
        from serein.models.train import TrainConfig

        torch.set_num_threads(args.threads)
        cfg = TrainConfig(epochs=args.epochs, hidden=args.hidden, layers=args.layers,
                          dropout=.1, weight_decay=1e-4, smoke_weight=6., seed=args.seed)
        package = Path(__file__).resolve().parents[1]
        code_hashes = {path.relative_to(package).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in sorted(package.rglob("*.py"))}
        experiment_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        plan = {"inputs": {name: hashlib.sha256(payload).hexdigest() for name, payload in payloads.items()},
                "code_sha256": code_hashes, "experiment_sha256": experiment_hash,
                "train_config": asdict(cfg), "seeds": args.seeds,
                "torch": torch.__version__, "numpy": np.__version__, "pandas": pd.__version__,
                "python": platform.python_version(), "scipy": version("scipy"),
                "pyarrow": version("pyarrow"),
                "threads": args.threads, "interop_threads": torch.get_num_interop_threads(),
                "device": str(train._device())}
        if not args.resume:
            args.output.mkdir(exist_ok=False)
        cache = spatial_checkpoint.MemberCache(args.output, plan, resume=args.resume)
        with (args.output / "training.log").open("a" if args.resume else "w", encoding="utf-8") as stream:
            def log(message):
                print(message, flush=True)
                stream.write(message + "\n")
                stream.flush()

            predictions, fitted = fit_experiment(experiment, cfg, seeds=args.seeds, log=log, cache=cache)
        predictions.to_parquet(args.output / "predictions.parquet", index=False)
        for name, fit in fitted.items():
            save_artifacts(args.output / name, experiment.prep, experiment.reference_ids,
                           experiment.train.X.shape[-1], experiment.leads, fit["cfg"],
                           fit["cqr"], fit["states"], seeds=[args.seed + i for i in range(args.seeds)])
        report_models = {"": ("smokecast", "smokecast_nograph"), "noaa_": ("smokecast", "noaa_best")}
        for prefix, models in report_models.items():
            summary, daily, sites = analyze_spatial(predictions, points, partition, models=models)
            summary.to_csv(args.output / f"{prefix}summary.csv", index=False)
            daily.to_parquet(args.output / f"{prefix}daily.parquet", index=False)
            sites.to_csv(args.output / f"{prefix}sites.csv", index=False)
            if args.plot:
                from serein.eval.spatial_plots import plot_spatial_scores

                for lead in summary.lead.drop_duplicates():
                    plot_spatial_scores(summary, int(lead), args.output / f"{prefix}spatial_L{lead}.png")
        (args.output / "partition.json").write_bytes(payloads["partition"])
        manifest = {"experiment_version": 1, "status": "complete", "development_only": True,
                    "inputs": {name: {"path": str(getattr(args, name).resolve()),
                                      "sha256": hashlib.sha256(payload).hexdigest()}
                               for name, payload in payloads.items()},
                    "partition_provenance": partition["provenance"], "split_years": years,
                    "reference_ids": experiment.reference_ids, "evaluation_ids": experiment.evaluation_ids,
                    "leads": experiment.leads, "train_config": asdict(cfg),
                    "seeds": [args.seed + i for i in range(args.seeds)],
                    "device": next(iter(fitted.values()))["device"],
                    "torch": torch.__version__, "threads": args.threads,
                    "numpy": np.__version__, "pandas": pd.__version__,
                    "code_sha256": code_hashes, "experiment_sha256": experiment_hash,
                    "resumed": args.resume, "reused_members": cache.reused,
                    "run_plan_sha256": hashlib.sha256((args.output / "run_plan.json").read_bytes()).hexdigest(),
                    "graph": config["graph"],
                    "report_models": {prefix or "primary": list(models) for prefix, models in report_models.items()},
                    "plots": [f"{prefix}spatial_L{lead}.png" for prefix in report_models for lead in experiment.leads]
                    if args.plot else [],
                    "preprocessing_sites": "reference only", "fitting_sites": "reference only",
                    "selection_sites": "reference only", "calibration_sites": "reference only",
                    "prediction_graph": "reference-only core; reference-to-evaluation edges only",
                    "time_split": "even ISO weeks for selection and calibration; odd weeks for evaluation",
                    "n_training_days": len(experiment.train.days),
                    "n_validation_calibration_days": len(experiment.validation.days),
                    "n_prediction_days": len(experiment.prediction.days),
                    "n_evaluation_rows": len(predictions),
                    "n_training_targets": int(np.isfinite(experiment.train.Y).sum()),
                    "n_validation_calibration_targets": int(np.isfinite(experiment.validation.Y).sum()),
                    "training_history": {name: fit["history"] for name, fit in fitted.items()},
                    "interpretation": "exploratory development experiment; fixed sites, not a spatial coverage guarantee"}
        (args.output / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    except (OSError, TypeError, ValueError, KeyError, OverflowError, yaml.YAMLError) as exc:
        parser.error(str(exc))
    print(f"wrote {args.output}: reference-only development experiment")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
