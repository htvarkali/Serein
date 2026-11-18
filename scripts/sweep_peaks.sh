#!/usr/bin/env bash
# B-13: does up-weighting smoke days in training fix under-predicted peaks? Dev weeks only.
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
mkdir -p outputs/logs  # outputs/ is git-ignored, so a fresh clone has no log folder
for w in 1 3 6; do
  log_path="outputs/logs/peaks_w$w.log"
  if uv run serein backtest --no-gbm --no-ablation --seeds 3 --smoke-weight "$w" \
      --tag "peaks_w$w" > "$log_path" 2>&1; then
    echo "done w=$w"
  else
    status=$?
    echo "peaks_w$w FAILED (exit $status): see $log_path" >&2
    exit "$status"
  fi
done
