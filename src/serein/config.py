"""Paths and study configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]


def data_dir() -> Path:
    """Root of the local data cache. Override with SEREIN_DATA=/some/path."""
    p = Path(os.environ.get("SEREIN_DATA", REPO_ROOT / "data"))
    p.mkdir(parents=True, exist_ok=True)
    return p


def raw_dir(source: str) -> Path:
    p = data_dir() / "raw" / source
    p.mkdir(parents=True, exist_ok=True)
    return p


def interim_dir(name: str) -> Path:
    p = data_dir() / "interim" / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_env() -> None:
    """Load KEY=VALUE lines from REPO_ROOT/.env into os.environ (never printed)."""
    env = REPO_ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


@dataclass
class Region:
    lon_min: float
    lon_max: float
    lat_min: float
    lat_max: float

    def contains(self, lat, lon):
        return (
            (lat >= self.lat_min) & (lat <= self.lat_max)
            & (lon >= self.lon_min) & (lon <= self.lon_max)
        )


@dataclass
class Study:
    raw: dict

    @property
    def name(self) -> str:
        return self.raw["name"]

    @property
    def region(self) -> Region:
        return Region(**self.raw["region"])

    @property
    def excluded(self) -> list[Region]:
        """Boxes inside the region that must stay out (e.g. a transfer-test area)."""
        return [Region(**r) for r in self.raw.get("exclude_regions") or []]

    def in_study(self, lat, lon):
        """Inside the region and outside every excluded box."""
        ok = self.region.contains(lat, lon)
        for r in self.excluded:
            ok = ok & ~r.contains(lat, lon)
        return ok

    @property
    def leads(self) -> list[int]:
        return list(self.raw["leads"])

    def season_days(self, years: list[int]) -> list[date]:
        """All days in the configured season months for the given years."""
        import pandas as pd

        out = []
        months = set(self.raw["season_months"])
        for y in years:
            for d in pd.date_range(f"{y}-01-01", f"{y}-12-31", freq="D"):
                if d.month in months:
                    out.append(d.date())
        return out

    def split_days(self, part: str) -> list[date]:
        return self.season_days(self.raw["split"][part])


def load_study(path: str | Path) -> Study:
    with open(path) as f:
        return Study(yaml.safe_load(f))
