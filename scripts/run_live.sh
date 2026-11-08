#!/usr/bin/env bash
# Daily live forecast (D-8). Run after 18:30 UTC (10:30 AM PST / 11:30 AM PDT), when
# NOAA's 12z AQM run is posted. Scheduled on Aadi's PC at 11:45 AM local time.
# Retries every 20 min for 3 h if a NOAA file is late. Never commits anything.
set -uo pipefail
cd "$(dirname "$0")/.."
export PYTHONIOENCODING=utf-8
mkdir -p outputs/logs
LOG=outputs/logs/live_$(date +%Y%m%d).log
for try in $(seq 1 10); do
  if uv run serein live >> "$LOG" 2>&1; then echo "live ok (try $try)" >> "$LOG"; exit 0; fi
  echo "live try $try failed; waiting 20 min" >> "$LOG"
  sleep 1200
done
exit 1
