"""Build the training/evaluation table: one row per (issue_date, point_id).

Every column obeys the "no peeking" rules in ``serein.data.availability``.

Column groups
  y_L{l}               target: observed local-day mean PM2.5 at lead l (µg/m³)
  obs_*                sensor readings available at issue time
  hrrr_smoke_*_L{l}    HRRR-Smoke near-surface smoke, local-day mean/max (µg/m³)
  hrrr_{u10,v10,pbl,t2m,rh2m}_L{l}  HRRR weather, local-day mean
  aqm_*_L{l}           NOAA AQM bias-corrected PM2.5, local-day mean/max
  hms_prev             yesterday's HMS smoke density at the point (0..3)
  frp_*                nearby fire radiative power in the last 24 h (FIRMS)
  cams_*_L{l}          ECMWF CAMS 00 UTC PM2.5 forecast, local-day mean/max (optional)
  lat, lon, doy_sin, doy_cos
"""

from __future__ import annotations

from datetime import date, timedelta

import numpy as np
import pandas as pd
from tqdm import tqdm

from serein.config import Study, data_dir
from serein.data import airnow, aqm, firms, hms, hrrr
from serein.data.availability import AQM_POSTED_LAG_H, HRRR_POSTED_LAG_H, Availability
from serein.features.daily import model_daily, obs_daily_means

MET_VARS = ["u10", "v10", "pbl", "t2m", "rh2m", "colmd"]
# CAMS is 3-hourly and ends at 96 h: day 3 has 6 of its 8 steps, so 6 is the minimum.
CAMS_MIN_STEPS = 6


def processed_dir(study: Study):
    p = data_dir() / "processed" / study.name
    p.mkdir(parents=True, exist_ok=True)
    return p


def _obs_features(hourly: pd.DataFrame, daily: pd.DataFrame, points: pd.DataFrame,
                  days: list[date], av: Availability, leads: list[int]) -> pd.DataFrame:
    for name, frame, column in (("hourly observations", hourly, "site_id"),
                                ("daily observations", daily, "point_id"),
                                ("points", points, "point_id")):
        if frame[column].isna().any():
            raise ValueError(f"{name} contain missing point identifiers")
    if points["point_id"].duplicated().any():
        raise ValueError("points contain duplicate point identifiers")
    local_dates = [pd.to_datetime(value, format="mixed") for value in daily["local_date"]]
    daily = daily.assign(local_date=[pd.NaT if pd.isna(value) else value.date()
                                     for value in local_dates])
    if daily["local_date"].isna().any():
        raise ValueError("daily observations contain missing dates")
    if daily.duplicated(["local_date", "point_id"]).any():
        raise ValueError("duplicate point/date pairs in daily observations")
    if not daily.empty:
        daily["pm25_daily"] = daily["pm25_daily"].where(np.isfinite(daily["pm25_daily"]))
    ids = points["point_id"].tolist()
    h = hourly.rename(columns={"site_id": "point_id"})
    h["time_utc"] = pd.to_datetime(h["time_utc"], utc=True, format="mixed").dt.tz_localize(None)
    if h["time_utc"].isna().any():
        raise ValueError("hourly observations contain missing timestamps")
    h["pm25"] = h["pm25"].where(np.isfinite(h["pm25"]))
    wide = h[h["point_id"].isin(ids)].pivot_table(
        index="time_utc", columns="point_id", values="pm25", aggfunc="mean")
    wide = wide.reindex(columns=ids)
    dwide = daily.pivot_table(index="local_date", columns="point_id",
                              values="pm25_daily").reindex(columns=ids)

    rows = []
    for d in days:
        t = pd.Timestamp(av.last_obs_hour_start(d))
        w24 = wide.loc[t - pd.Timedelta(hours=23): t]
        # Apply the availability cutoff before combining subhourly readings.
        w24 = w24.groupby(w24.index.floor("h")).mean()
        w3 = w24.loc[t - pd.Timedelta(hours=2): t]
        w6 = w24.loc[t - pd.Timedelta(hours=5): t]

        def dget(day):
            return dwide.loc[day].to_numpy() if day in dwide.index else np.full(len(ids), np.nan)

        f = pd.DataFrame({
            "issue_date": d, "point_id": ids,
            "obs_last1": wide.loc[t].to_numpy() if t in wide.index else np.nan,
            "obs_last3": w3.mean().to_numpy(),
            "obs_last6": w6.mean().to_numpy(),
            "obs_last24": w24.mean().to_numpy(),
            "obs_max24": w24.max().to_numpy(),
            "obs_n24": w24.notna().sum().to_numpy(),
            "obs_prevday": dget(d - timedelta(days=1)),
            "obs_prev2day": dget(d - timedelta(days=2)),
        })
        for lead in leads:
            f[f"y_L{lead}"] = dget(d + timedelta(days=lead))
        rows.append(f)
    return pd.concat(rows, ignore_index=True)


def _model_features(days, points, offsets, store: str, av: Availability) -> pd.DataFrame:
    # No peeking: the configured model runs must have been public by issue time.
    for name, cycle, lag in (("HRRR", av.hrrr_cycle, HRRR_POSTED_LAG_H),
                             ("AQM", av.aqm_cycle, AQM_POSTED_LAG_H)):
        if days and not av.check_model_cycle(days[0], cycle, lag):
            raise ValueError(f"{name} {cycle:02d}z run is posted after issue time; "
                             "pick an earlier cycle in the config")
    out = []
    hr = hrrr.load_cycles(days, cycle=av.hrrr_cycle, store=store)
    if len(hr):
        hr = hr[hr["point_id"].isin(offsets.index)]
        smoke = hr[hr["var"] == "smoke"]
        g = model_daily(smoke, offsets, min_count=12)
        g = g[g["lead"].between(0, 3)]
        p = g.pivot_table(index=["issue_date", "point_id"], columns="lead", values=["mean", "max"])
        p.columns = [f"hrrr_smoke_{stat}_L{lead}" for stat, lead in p.columns]
        out.append(p)
        met = hr[hr["var"].isin(MET_VARS)].copy()
        met["var"] = met["var"].astype(str)
        g = model_daily(met, offsets, min_count=4, group_extra=("var",))
        g = g[g["lead"].between(0, 3)]
        p = g.pivot_table(index=["issue_date", "point_id"], columns=["var", "lead"], values="mean")
        p.columns = [f"hrrr_{v}_L{lead}" for v, lead in p.columns]
        out.append(p)
        # Wind at about issue time (last forecast hour before it) for upwind fire features.
        now_fhr = int(av.issue_hour_utc - av.hrrr_cycle)
        now = hr[(hr["fhr"] == now_fhr) & hr["var"].isin(["u10", "v10"])].copy()
        now["var"] = now["var"].astype(str)
        p = now.pivot_table(index=["issue_date", "point_id"], columns="var", values="value")
        p.columns = [f"wind_now_{c}" for c in p.columns]
        out.append(p)
    aq = aqm.load_cycles(days, cycle=av.aqm_cycle, store=store)
    if len(aq):
        aq = aq[aq["point_id"].isin(offsets.index)]
        g = model_daily(aq, offsets, min_count=12)
        g = g[g["lead"].between(0, 3)]
        p = g.pivot_table(index=["issue_date", "point_id"], columns="lead", values=["mean", "max"])
        p.columns = [f"aqm_{stat}_L{lead}" for stat, lead in p.columns]
        out.append(p)
    if not out:
        return pd.DataFrame(columns=["issue_date", "point_id"])
    return pd.concat(out, axis=1).reset_index()


def _cams_features(days, points, offsets) -> pd.DataFrame:
    # The 00 UTC run is published hours before the 18:30 UTC issue time.
    from serein.data import cams as cams_data

    cf = cams_data.point_forecasts(days, points)
    if cf.empty:
        raise RuntimeError("No CAMS files for these days. Download them first (serein.data.cams).")
    g = model_daily(cf, offsets, min_count=CAMS_MIN_STEPS)
    g = g[g["lead"].between(0, 3)]
    p = g.pivot_table(index=["issue_date", "point_id"], columns="lead", values=["mean", "max"])
    p.columns = [f"cams_{stat}_L{lead}" for stat, lead in p.columns]
    return p.reset_index()


def build_table(study: Study, days: list[date], points: pd.DataFrame,
                use_firms: bool = True, progress: bool = True,
                cams: bool = False) -> pd.DataFrame:
    if not days:
        raise ValueError("feature table requires at least one issue date")
    # Issue days are calendar labels, so UTC conversion could change the day.
    normalized = [pd.to_datetime(d, format="mixed") for d in days]
    if any(pd.isna(d) for d in normalized):
        raise ValueError("feature table contains missing issue dates")
    days = [d.date() for d in normalized]
    if len(set(days)) != len(days):
        raise ValueError("feature table contains duplicate issue dates")
    if points.empty:
        raise ValueError("feature table requires at least one point")
    if points["point_id"].isna().any():
        raise ValueError("points contain missing point identifiers")
    if points["point_id"].duplicated().any():
        raise ValueError("points contain duplicate point identifiers")
    av = Availability.from_study(study.raw)
    leads = study.leads
    offsets = points.set_index("point_id")["gmt_offset"]
    if not np.isfinite(offsets).all():
        raise ValueError("Each point must have a finite standard-time offset")

    pad = sorted({d + timedelta(days=k) for d in days for k in range(-3, max(leads) + 2)})
    hourly = airnow.load_hourly(pad)
    if hourly.empty:
        raise RuntimeError("No AirNow data cached for these days. Run `serein download airnow`.")
    daily = obs_daily_means(hourly, offsets)

    tab = _obs_features(hourly, daily, points, days, av, leads)
    mod = _model_features(days, points, offsets, study.name, av)
    if len(mod):
        tab = tab.merge(mod, on=["issue_date", "point_id"], how="left")
    if cams:
        tab = tab.merge(_cams_features(days, points, offsets), on=["issue_date", "point_id"],
                        how="left")

    # HMS (yesterday) and fires.
    fires = pd.DataFrame()
    if use_firms:
        # NASA FIRMS if a key was used to download it; otherwise NOAA HMS fire points
        # (no key). Only polar-orbiter passes (VIIRS/MODIS): geostationary (GOES)
        # detections repeat every few minutes and would inflate 24 h FRP sums.
        fires = firms.load_cached()
        if len(fires):
            # The FIRMS cache may hold other seasons only; use it just for these days.
            t0 = pd.Timestamp(min(days)) - pd.Timedelta(days=2)
            t1 = pd.Timestamp(max(days)) + pd.Timedelta(days=1)
            fires = fires[fires["time_utc"].between(t0, t1)]
        if fires.empty:
            fires = hms.load_fires(days)
            if len(fires):
                fires = fires[fires["method"].isin(["VIIRS", "MODIS"])]
    pts = points.set_index("point_id").loc[tab["point_id"].unique()].reset_index()
    hms_cols, fire_parts = [], []
    it = tqdm(days, desc="hms/fires", disable=not progress)
    for d in it:
        sub = pts
        dens = hms.density_at_points(av.hms_day(d), sub)
        hms_cols.append(pd.DataFrame({"issue_date": d, "point_id": sub["point_id"], "hms_prev": dens}))
        if len(fires):
            wind = tab[tab["issue_date"] == d].set_index("point_id").reindex(sub["point_id"])
            u = wind.get("wind_now_u10", pd.Series(np.nan, index=wind.index)).to_numpy()
            v = wind.get("wind_now_v10", pd.Series(np.nan, index=wind.index)).to_numpy()
            ff = firms.fire_features(fires, sub, av.issue_time(d), av.firms_window_hours, u, v)
            ff["issue_date"], ff["point_id"] = d, sub["point_id"].to_numpy()
            fire_parts.append(ff)
    tab = tab.merge(pd.concat(hms_cols), on=["issue_date", "point_id"], how="left")
    if fire_parts:
        tab = tab.merge(pd.concat(fire_parts), on=["issue_date", "point_id"], how="left")

    tab = tab.merge(points[["point_id", "lat", "lon", "kind"]], on="point_id", how="left")
    doy = pd.to_datetime(tab["issue_date"]).dt.day_of_year
    tab["doy_sin"] = np.sin(2 * np.pi * doy / 365.25)
    tab["doy_cos"] = np.cos(2 * np.pi * doy / 365.25)
    return tab
