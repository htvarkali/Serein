#!/usr/bin/env bash
# B-17/B-18: does a bigger model, a memory of past days, or more training data help?
# Dev weeks only (2023 odd weeks); never touches the 2024-25 test seasons.
# Every run: same recipe as the ablations (3-seed ensemble, no GBM).
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
mkdir -p outputs/logs
L=outputs/logs
run_logged () {
    local label=$1 log_path=$2 status
    shift 2
    if "$@" > "$log_path" 2>&1; then
        echo "$label done"
    else
        status=$?
        echo "$label FAILED (exit $status): see $log_path" >&2
        return "$status"
    fi
}
run () {
    local cfg=$1 tag=$2
    shift 2
    run_logged "$tag" "$L/$tag.log" uv run serein backtest --config "$cfg" \
        --no-gbm --no-ablation --seeds 3 --tag "$tag" "$@"
}
W=configs/west_us.yaml
C=configs/conus.yaml

# 1. West only: model size and memory.
run $W scale_s                                  # 86k parameters (current)
run $W scale_m  --hidden 128 --layers 3         # 454k
run $W scale_l  --hidden 256 --layers 3         # 1.76M
run $W hist4    --history 4
run $W hist7    --history 7

# 2. All of the US (needs the CONUS AQM + HRRR download: see docs/METHODS.md).
if [ "${SKIP_CONUS:-0}" != 1 ]; then
  # Wait for a download started by outputs/logs/conus_download.sh, if one is running.
  if [ -f "$L/conus_download.log" ]; then
    until grep -q CONUS_DOWNLOAD_DONE "$L/conus_download.log"; do sleep 60; done
  fi
  for s in train calibrate; do
    if [ ! -f "${SEREIN_DATA:-data}/processed/conus/table_$s.parquet" ]; then
      run_logged "conus_table_$s" "$L/conus_table_$s.log" \
          uv run serein build-table --config "$C" --split "$s"
    fi
  done
  run $C conus_s
  run $C conus_m  --hidden 128 --layers 3
  run $C conus_l  --hidden 256 --layers 3
  run $C conus_hist4 --history 4
fi
run_logged compare_runs "$L/compare_runs.log" uv run python scripts/compare_runs.py
echo ALLDONE
