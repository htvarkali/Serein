#!/usr/bin/env bash
# Refresh summary figures in website/assets. The August 2023 case study is a
# separate historical figure with its own caption in website/index.html.
set -euo pipefail
cd "$(dirname "$0")/.."
RUN=${RUN:-outputs/backtest/west_us_dev}
images=(
    "$RUN/fig_rmse_by_lead_all.png"
    "$RUN/fig_improvement_map_L1.png"
    "outputs/maps/map_20230818.png"
    "outputs/airplan/airplan_learning_curve.png"
)
for image in "${images[@]}"; do
    if [[ ! -s "$image" ]]; then
        echo "Missing website image: $image" >&2
        exit 1
    fi
done
mkdir -p website/assets
cp "${images[@]}" website/assets/
python3 scripts/check_website.py
echo "website/assets updated from $RUN"
