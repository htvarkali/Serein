"""Schools and hospitals for the Smoke World map counts (task W-17).

Writes the small file the site reads to count, for the hour on screen, how many schools
and hospitals sit where the map is at or above 35.5 µg/m³ (website/data/places.json).
Only coordinates are kept, rounded to about 100 m; no names.

Inputs (free public downloads, saved anywhere):
- NCES EDGE public school locations, school year 2023-24 (CSV inside the zip):
  https://nces.ed.gov/programs/edge/Geographic/SchoolLocations
- HIFLD hospitals (CSV export): https://hifld-geoplatform.hub.arcgis.com/ , "Hospitals".
  Rows whose STATUS is not OPEN are dropped when that column exists.

    uv run python -m serein.places --schools EDGE_GEOCODE_PUBLICSCH_2324.csv \\
        --hospitals Hospitals.csv --out website-src/public/data/places.json

Then rebuild the site (website-src: npx vite build). Until this runs, the shipped file
has empty lists and the map shows no counts.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

from serein.config import load_study

LAT_COLUMNS = ("LAT", "LATITUDE", "Y")
LON_COLUMNS = ("LON", "LONGITUDE", "X")


def _column(df: pd.DataFrame, names: tuple[str, ...], what: str) -> str:
    upper = {c.upper(): c for c in df.columns}
    for name in names:
        if name in upper:
            return upper[name]
    raise ValueError(f"no {what} column; looked for {', '.join(names)} in {list(df.columns)[:12]}")


def points(df: pd.DataFrame, region: dict) -> list[list[float]]:
    """[lat, lon] pairs inside the study box, rounded to 3 decimals, duplicates removed."""
    status = {c.upper(): c for c in df.columns}.get("STATUS")
    if status is not None:
        df = df[df[status].astype(str).str.upper().eq("OPEN")]
    lat = pd.to_numeric(df[_column(df, LAT_COLUMNS, "latitude")], errors="coerce").to_numpy(float)
    lon = pd.to_numeric(df[_column(df, LON_COLUMNS, "longitude")], errors="coerce").to_numpy(float)
    ok = (np.isfinite(lat) & np.isfinite(lon)
          & (lat >= region["lat_min"]) & (lat <= region["lat_max"])
          & (lon >= region["lon_min"]) & (lon <= region["lon_max"]))
    pairs = np.unique(np.round(np.column_stack([lat[ok], lon[ok]]), 3), axis=0)
    return pairs.tolist()


def build(schools: pd.DataFrame, hospitals: pd.DataFrame, region: dict) -> dict:
    s, h = points(schools, region), points(hospitals, region)
    return {
        "source": ("Public schools: NCES EDGE school locations, 2023-24. Hospitals: HIFLD, "
                   "open hospitals. Locations rounded to about 100 m."),
        "schools": s,
        "hospitals": h,
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Schools and hospitals for the Smoke World counts")
    ap.add_argument("--schools", type=Path, required=True)
    ap.add_argument("--hospitals", type=Path, required=True)
    ap.add_argument("--config", default="configs/west_us.yaml")
    ap.add_argument("--out", type=Path, default=Path("website-src/public/data/places.json"))
    args = ap.parse_args(argv)
    region = load_study(args.config).raw["region"]
    read = lambda p: pd.read_csv(p, dtype=str, encoding_errors="replace")
    data = build(read(args.schools), read(args.hospitals), region)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(data, separators=(",", ":")))
    print(f"{len(data['schools'])} schools, {len(data['hospitals'])} hospitals -> {args.out}")


if __name__ == "__main__":
    main()
