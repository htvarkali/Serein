#!/usr/bin/env bash
# Rebuild the public site (website/) from the React app in website-src/.
# Optional inputs are refreshed first when they exist:
#   - summary figures from a backtest run (RUN, default outputs/backtest/west_us_dev)
#   - the live Smoke World data from the latest live forecast (serein.world)
set -euo pipefail
cd "$(dirname "$0")/.."
RUN=${RUN:-outputs/backtest/west_us_dev}
mkdir -p website-src/public/img website-src/public/data
for image in "$RUN/fig_rmse_by_lead_all.png" "$RUN/fig_improvement_map_L1.png"; do
    [[ -s "$image" ]] && cp "$image" website-src/public/img/
done
latest=$(ls outputs/live/west_us/forecasts/*.parquet 2>/dev/null | sort | tail -1 || true)
if [[ -n "$latest" ]]; then
    uv run python -m serein.world --forecast "$latest" --out website-src/public/data/live.json
fi
(cd website-src && npm ci --silent && npm run build)
python3 scripts/check_website.py
echo "website/ rebuilt"
