"""EPA AirNow: hourly PM2.5 observations and archived official AQI forecasts.

Free, no key. Files live at https://files.airnowtech.org/airnow/YYYY/YYYYMMDD/

* ``HourlyAQObs_YYYYMMDDHH.dat`` (since 2019-05-28): one hour, all sites, with
  coordinates. Times are UTC and mark the START of the hour.
* ``reportingarea.dat``: the last file of each day. Holds forecasts issued that
  day (data type F), yesterday's observed daily AQI (Y), and hourly obs (O).
  Agencies issue forecasts late morning to early afternoon local time, all by
  22:00 UTC (AirNow Reporting Area fact sheet, Aug 2025).
"""

from __future__ import annotations

import io
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timedelta

import pandas as pd

from serein.aqi import category_from_name
from serein.config import raw_dir
from serein.http import get

BASE = "https://files.airnowtech.org/airnow"

HOURLY_COLS = ["AQSID", "SiteName", "Latitude", "Longitude", "Elevation", "GMTOffset",
               "CountryCode", "StateName", "ValidDate", "ValidTime", "DataSource",
               "ReportingArea_PipeDelimited", "PM25", "PM25_Unit"]

RA_COLS = ["issue_date", "valid_date", "valid_time", "time_zone", "record_sequence",
           "data_type", "primary", "reporting_area", "state", "lat", "lon", "pollutant",
           "aqi", "category", "action_day", "discussion", "source"]


def _day_url(d: date, name: str) -> str:
    return f"{BASE}/{d:%Y}/{d:%Y%m%d}/{name}"


def parse_hourly_aqobs(text: str) -> pd.DataFrame:
    """Parse one HourlyAQObs file into tidy PM2.5 rows."""
    df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    missing = [c for c in HOURLY_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"HourlyAQObs missing columns: {missing}")
    df = df[HOURLY_COLS]
    df = df[(df["PM25"] != "") & (df["PM25_Unit"].str.upper() == "UG/M3")]
    out = pd.DataFrame({
        "site_id": df["AQSID"].str.strip(),
        "name": df["SiteName"],
        "lat": pd.to_numeric(df["Latitude"], errors="coerce"),
        "lon": pd.to_numeric(df["Longitude"], errors="coerce"),
        "elev": pd.to_numeric(df["Elevation"], errors="coerce"),
        "gmt_offset": pd.to_numeric(df["GMTOffset"], errors="coerce"),
        "country": df["CountryCode"],
        "state": df["StateName"],
        "reporting_area": df["ReportingArea_PipeDelimited"],
        "time_utc": pd.to_datetime(df["ValidDate"] + " " + df["ValidTime"],
                                   format="mixed", dayfirst=False),
        "pm25": pd.to_numeric(df["PM25"], errors="coerce"),
    })
    # AirNow keeps small negatives for averaging; drop instrument junk.
    out = out[(out["pm25"] > -5) & (out["pm25"] < 2000)]
    return out.dropna(subset=["lat", "lon", "pm25"]).reset_index(drop=True)


def download_hourly_day(d: date, overwrite: bool = False) -> pd.DataFrame | None:
    """Download the 24 hourly files whose UTC hour falls on day d; cache as parquet."""
    path = raw_dir("airnow") / "hourly" / f"{d:%Y%m%d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return pd.read_parquet(path)

    def one(h: int):
        r = get(_day_url(d, f"HourlyAQObs_{d:%Y%m%d}{h:02d}.dat"), allow_404=True)
        if r is None or not r.text.strip():
            return None
        return parse_hourly_aqobs(r.text)

    with ThreadPoolExecutor(8) as ex:
        parts = [p for p in ex.map(one, range(24)) if p is not None]
    if not parts:
        return None
    df = pd.concat(parts, ignore_index=True)
    df = df.drop_duplicates(subset=["site_id", "time_utc"], keep="last")
    # A recent day with missing hours may still be filling in: don't freeze it in the
    # cache, or later runs would skip it forever. Old gaps are permanent, so cache those.
    # The partial copy is kept beside it (live forecasts read it) and replaced later.
    partial = _partial_path(path)
    if len(parts) < 24 and d >= date.today() - timedelta(days=2):
        df.to_parquet(partial, index=False)
        return df
    df.to_parquet(path, index=False)
    partial.unlink(missing_ok=True)
    return df


def _partial_path(path):
    return path.with_name(path.stem + ".partial.parquet")


def parse_reportingarea(text: str) -> pd.DataFrame:
    rows = [line.split("|") for line in text.splitlines() if line.strip()]
    rows = [r[:17] + [""] * (17 - len(r)) for r in rows]
    df = pd.DataFrame(rows, columns=RA_COLS)
    df = df[df["pollutant"].str.upper().isin(["PM2.5", "PM25"])]
    df["issue_date"] = pd.to_datetime(df["issue_date"], format="%m/%d/%y").dt.date
    df["valid_date"] = pd.to_datetime(df["valid_date"], format="%m/%d/%y").dt.date
    df["record_sequence"] = pd.to_numeric(df["record_sequence"], errors="coerce")
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df["aqi"] = pd.to_numeric(df["aqi"], errors="coerce")
    df["category_idx"] = df["category"].map(category_from_name)
    df["lead"] = [(v - i).days for v, i in zip(df["valid_date"], df["issue_date"])]
    return df.drop(columns=["discussion"]).reset_index(drop=True)


def download_reportingarea_day(d: date, overwrite: bool = False) -> pd.DataFrame | None:
    path = raw_dir("airnow") / "reportingarea" / f"{d:%Y%m%d}.parquet"
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not overwrite:
        return pd.read_parquet(path)
    r = get(_day_url(d, "reportingarea.dat"), allow_404=True)
    if r is None:
        return None
    df = parse_reportingarea(r.text)
    df.to_parquet(path, index=False)
    return df


def load_hourly(days: list[date]) -> pd.DataFrame:
    """Load cached hourly obs for days (plus one day each side for local-time edges)."""
    want = set()
    for d in days:
        for k in (-1, 0, 1):
            want.add(d + timedelta(days=k))
    parts = []
    for d in sorted(want):
        p = raw_dir("airnow") / "hourly" / f"{d:%Y%m%d}.parquet"
        if not p.exists():
            p = _partial_path(p)  # today's hours so far (live forecasts)
        if p.exists():
            parts.append(pd.read_parquet(p))
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True).drop_duplicates(["site_id", "time_utc"])


def load_forecasts(days: list[date]) -> pd.DataFrame:
    """The EPA PM2.5 forecast in force on each day, per reporting area.

    The last reportingarea.dat of day D holds every forecast still current on D,
    some issued days earlier. For (D, valid_date) we keep the newest forecast
    with issue_date <= D, and re-express lead relative to D. Returns columns
    as_of (= D), valid_date, lead, reporting_area, state, aqi, category_idx, issue_date.
    """
    parts = []
    for d in days:
        p = raw_dir("airnow") / "reportingarea" / f"{d:%Y%m%d}.parquet"
        if not p.exists():
            continue
        df = pd.read_parquet(p)
        df = df[(df["data_type"] == "F") & (df["issue_date"] <= d) & (df["valid_date"] >= d)]
        df = df.sort_values("issue_date").drop_duplicates(
            ["reporting_area", "state", "valid_date"], keep="last").copy()
        df["as_of"] = d
        df["lead"] = [(v - d).days for v in df["valid_date"]]
        parts.append(df)
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True)


def load_observed_area_aqi(days: list[date]) -> pd.DataFrame:
    """Official observed daily PM2.5 AQI per reporting area (type Y rows).

    The file of day D+1 carries "yesterday's AQI" for day D.
    """
    parts = []
    for d in days:
        p = raw_dir("airnow") / "reportingarea" / f"{d + timedelta(days=1):%Y%m%d}.parquet"
        if p.exists():
            df = pd.read_parquet(p)
            df = df[(df["data_type"] == "Y") & (df["valid_date"] == d)]
            parts.append(df[["valid_date", "reporting_area", "state", "aqi", "category_idx"]])
    if not parts:
        return pd.DataFrame()
    return pd.concat(parts, ignore_index=True).drop_duplicates(
        ["reporting_area", "state", "valid_date"])


def site_table(hourly: pd.DataFrame) -> pd.DataFrame:
    """One row per site with its most common coordinates and metadata."""
    g = hourly.groupby("site_id")
    meta = g.agg(name=("name", "last"), lat=("lat", "median"), lon=("lon", "median"),
                 elev=("elev", "median"), gmt_offset=("gmt_offset", "median"),
                 state=("state", "last"), reporting_area=("reporting_area", "last"),
                 n_hours=("pm25", "size"))
    meta["gmt_offset"] = meta["gmt_offset"].round().astype(int)
    return meta.reset_index()


def daterange(start: date, end: date) -> list[date]:
    n = (end - start).days
    return [start + timedelta(days=i) for i in range(n + 1)]


def parse_date(s: str) -> date:
    return datetime.strptime(s, "%Y-%m-%d").date()


__all__ = [
    "daterange",
    "download_hourly_day",
    "download_reportingarea_day",
    "load_forecasts",
    "load_hourly",
    "load_observed_area_aqi",
    "parse_date",
    "parse_hourly_aqobs",
    "parse_reportingarea",
    "site_table",
]
