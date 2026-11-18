#!/usr/bin/env bash
# Dev-mode ablation sweep (B-10): does message passing help, and under which settings?
# Scores ONLY on the 2023 calibration weeks. Never touches the test seasons.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
mkdir -p outputs/logs  # outputs/ is git-ignored, so a fresh clone has no log folder
run () {
    local tag=$1 status log_path
    shift
    log_path="outputs/logs/sweep_$tag.log"
    if uv run serein backtest --no-gbm --tag "sweep_$tag" "$@" > "$log_path" 2>&1; then
        echo "== $tag $*"
        awk '/^RMSE \(|^RMSE at HIDDEN/ { report = 1 } /^$/ { report = 0 }
             report && /RMSE|lead|smokecast|noaa_best/' "$log_path"
    else
        status=$?
        echo "$tag FAILED (exit $status): see $log_path" >&2
        return "$status"
    fi
}
REG="--dropout 0.3 --weight-decay 1e-3"
run mask0_reg   --node-mask 0 $REG
run small_reg   --hidden 64 --layers 2 $REG
run reg_seed1   $REG --seed 1
run holdout_reg $REG --holdout-sites 0.2
run ens5_reg    $REG --seeds 5
