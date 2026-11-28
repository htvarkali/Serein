"""Who lives far from an air monitor? Distance to the nearest EPA monitor by tract income.

Free public inputs, no key (downloaded to data/raw/census/):
- ACS 2019-2023 5-year table-based summary files: B19013 (median household income) and
  B01003 (total population), https://www2.census.gov/programs-surveys/acs/summary_file/2023/
- Census cartographic tract boundaries, 2023, 1:500k:
  https://www2.census.gov/geo/tiger/GENZ2023/shp/cb_2023_<state>_tract_500k.zip
- EPA monitor locations from the study's points registry.

For each tract inside the study box: distance from its representative point to the
nearest monitor. Tracts are grouped into income quintiles (population-weighted
summaries). This describes monitor coverage only; it says nothing about health.

Edge check: the registry only holds monitors inside the study box, so a tract near the
box edge may have a closer monitor just outside it. A monitor outside the box is at
least as far away as the box edge, so a tract's distance can only be overstated when it
lies closer to the edge than to its nearest monitor inside. `edge_check` reports how
many of the far-from-a-monitor people are in that situation (an upper bound: all four
edges count, including the Pacific coast and the borders).

    uv run python -m serein.eval.equity --out outputs/equity
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd

from serein.config import load_study, raw_dir
from serein.data.points import load_points

STATES = {"04": "AZ", "06": "CA", "16": "ID", "32": "NV", "41": "OR", "53": "WA"}
FAR_KM = (25, 50)


def haversine_km(lat1, lon1, lat2, lon2):
    lat1, lon1, lat2, lon2 = map(np.radians, (lat1, lon1, lat2, lon2))
    a = (
        np.sin((lat2 - lat1) / 2) ** 2
        + np.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    return 2 * 6371.0 * np.arcsin(np.sqrt(a))


def read_acs(table: str, column: str) -> pd.Series:
    path = raw_dir("census") / f"acsdt5y2023-{table}.dat"
    df = pd.read_csv(path, sep="|", usecols=["GEO_ID", column], dtype={"GEO_ID": str})
    df = df[df["GEO_ID"].str.startswith("1400000US")]
    return pd.to_numeric(df.set_index("GEO_ID")[column], errors="coerce")


def tracts(region: dict) -> pd.DataFrame:
    import geopandas as gpd

    parts = []
    for fips, abbr in STATES.items():
        g = gpd.read_file(raw_dir("census") / f"cb_2023_{fips}_tract_500k.zip")
        pt = g.geometry.representative_point()
        parts.append(
            pd.DataFrame(
                {
                    "GEO_ID": "1400000US" + g["GEOID"].astype(str),
                    "state": abbr,
                    "lat": pt.y,
                    "lon": pt.x,
                }
            )
        )
    t = pd.concat(parts, ignore_index=True)
    inside = t.lat.between(region["lat_min"], region["lat_max"]) & t.lon.between(
        region["lon_min"], region["lon_max"]
    )
    t = t[inside].copy()
    t["income"] = t["GEO_ID"].map(read_acs("b19013", "B19013_E001"))
    t["population"] = t["GEO_ID"].map(read_acs("b01003", "B01003_E001"))
    # ACS uses large negative codes for "not available"; keep only real values.
    t.loc[t["income"] < 0, "income"] = np.nan
    return t[t["population"] > 0]


def nearest_km(t: pd.DataFrame, monitors: pd.DataFrame) -> np.ndarray:
    out = np.empty(len(t))
    mlat, mlon = monitors["lat"].to_numpy(), monitors["lon"].to_numpy()
    for i, (la, lo) in enumerate(zip(t["lat"].to_numpy(), t["lon"].to_numpy())):
        out[i] = haversine_km(la, lo, mlat, mlon).min()
    return out


def km_to_box_edge(t: pd.DataFrame, region: dict) -> np.ndarray:
    """Distance (km) from each tract point inside the box to the nearest box edge."""
    lat, lon = t["lat"].to_numpy(float), t["lon"].to_numpy(float)
    ns = np.minimum(lat - region["lat_min"], region["lat_max"] - lat) * 111.2
    # East and west edges are meridians: the shortest way there runs along the parallel.
    ew = np.minimum(lon - region["lon_min"], region["lon_max"] - lon)
    ew = ew * 111.2 * np.cos(np.radians(lat))
    return np.maximum(np.minimum(ns, ew), 0.0)


def edge_check(t: pd.DataFrame, far_km: float = FAR_KM[0]) -> pd.DataFrame:
    """Per income quintile: people over far_km from a monitor, and how many of them could
    have a closer monitor outside the box (box edge nearer than the nearest monitor)."""
    t = t.dropna(subset=["income"]).copy()
    t["quintile"] = pd.qcut(t["income"], 5, labels=["1 (lowest)", "2", "3", "4", "5 (highest)"])
    rows = []
    for q, g in t.groupby("quintile", observed=True):
        far = g[g["km"] > far_km]
        maybe = far[far["edge_km"] < far["km"]]
        rows.append({
            "income_quintile": q,
            f"people_over_{far_km:g}km": int(far["population"].sum()),
            "of_them_possibly_closer_outside_box": int(maybe["population"].sum()),
            "share_of_quintile_if_all_removed": float(
                (far["population"].sum() - maybe["population"].sum()) / g["population"].sum()),
        })
    return pd.DataFrame(rows)


def summarize(t: pd.DataFrame) -> pd.DataFrame:
    """Population-weighted coverage by income quintile (quintiles of tracts by income)."""
    t = t.dropna(subset=["income"]).copy()
    t["quintile"] = pd.qcut(t["income"], 5, labels=["1 (lowest)", "2", "3", "4", "5 (highest)"])
    rows = []
    for q, g in t.groupby("quintile", observed=True):
        w = g["population"].to_numpy(float)
        d = g["km"].to_numpy(float)
        order = np.argsort(d)
        cum = np.cumsum(w[order]) / w.sum()
        row = {
            "income_quintile": q,
            "tracts": len(g),
            "people": int(w.sum()),
            "income_range": f"${g['income'].min():,.0f}-${g['income'].max():,.0f}",
            "median_km_to_monitor": float(d[order][np.searchsorted(cum, 0.5)]),
        }
        for km in FAR_KM:
            row[f"share_people_over_{km}km"] = float(w[d > km].sum() / w.sum())
        rows.append(row)
    return pd.DataFrame(rows)


def main(argv=None):
    ap = argparse.ArgumentParser(description="Monitor coverage by tract income")
    ap.add_argument("--config", default="configs/west_us.yaml")
    ap.add_argument("--out", type=Path, default=Path("outputs/equity"))
    args = ap.parse_args(argv)
    study = load_study(args.config)
    monitors = load_points(study.name)
    monitors = monitors[monitors["kind"] == "epa"]
    t = tracts(study.raw["region"])
    t["km"] = nearest_km(t, monitors)
    args.out.mkdir(parents=True, exist_ok=True)
    t.to_csv(args.out / "tracts.csv", index=False)
    s = summarize(t)
    s.to_csv(args.out / "by_income.csv", index=False)
    print(f"{len(t)} tracts, {int(t['population'].sum()):,} people, {len(monitors)} monitors")
    print(s.round(3).to_string(index=False))
    t["edge_km"] = km_to_box_edge(t, study.raw["region"])
    e = edge_check(t)
    e.to_csv(args.out / "edge_check.csv", index=False)
    print("\nEdge check (upper bound on distances overstated by the study box):")
    print(e.round(3).to_string(index=False))


if __name__ == "__main__":
    main()
