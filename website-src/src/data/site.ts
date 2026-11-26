// Every number on the site lives here, with where it comes from. Development numbers
// (2023 held-out weeks) until the one-time final test on 2024-25 replaces them.

export const asset = (path: string) => `${import.meta.env.BASE_URL}${path}`

export const SOURCE_DEV =
  "Development backtest, 2023 held-out weeks (rerun 2026-11-23). Not the final 2024-25 test."

export const headline = {
  warnedSerein: 72, // % of unhealthy-for-sensitive area-days warned a day ahead
  warnedEpa: 46,
  falseSerein: 92,
  falseEpa: 98,
  rmseSerein: 7.8, // day-1 RMSE, µg/m³
  rmseNoaa: 11.0,
  hiddenSerein: 8.4, // day-1 RMSE at monitors hidden from the model
  hiddenNoaa: 11.1,
  extraDays: 63, // extra smoky area-days warned vs. EPA, day 1
}

export const rmseByLead = [
  { lead: "Today", serein: 4.4, noaa: 10.1 },
  { lead: "Tomorrow", serein: 7.8, noaa: 11.0 },
  { lead: "Day 2", serein: 9.7, noaa: 12.3 },
  { lead: "Day 3", serein: 11.6, noaa: 15.5 },
]

export const warnings = [
  { lead: "1 day ahead", serein: 72, epa: 46, fSerein: 92, fEpa: 98 },
  { lead: "2 days ahead", serein: 62, epa: 37, fSerein: 48, fEpa: 36 },
]

export const hiddenByDistance = [
  { band: "< 15 km", sites: 34, serein: 6.5, noaa: 7.4 },
  { band: "15-30 km", sites: 26, serein: 10.7, noaa: 14.0 },
  { band: "30-60 km", sites: 21, serein: 7.8, noaa: 12.3 },
]

export const equity = [
  { quintile: "Lowest income", far25: 10.8, far50: 3.7 },
  { quintile: "2nd", far25: 6.6, far50: 1.6 },
  { quintile: "Middle", far25: 4.8, far50: 0.7 },
  { quintile: "4th", far25: 2.2, far50: 0.3 },
  { quintile: "Highest income", far25: 0.6, far50: 0.0 },
]

export const team = [
  {
    name: "Aadi Tiwari",
    grade: "11th grade",
    role: "Data pipeline, SmokeCast forecast model, backtest protocol, Smoke World",
  },
  {
    name: "Harshateja Varkali",
    grade: "11th grade",
    role: "Website, sensor quality checks and forecast reliability",
  },
  {
    name: "Abhinav Garg",
    grade: "12th grade",
    role: "Business model, market research and IP",
  },
  {
    name: "Arush Kudaraya",
    grade: "11th grade",
    role: "Forecast context (ozone, heat, pollen) and competitor research",
  },
  {
    name: "Jagath Prabath",
    grade: "11th grade",
    role: "",
  },
]

export const sources = [
  { name: "EPA AirNow", what: "Hourly PM2.5 at air monitors and official AQI forecasts", license: "Public domain" },
  { name: "NOAA HRRR-Smoke", what: "Hourly smoke and weather forecast, 3 km, 48 hours", license: "Public domain" },
  { name: "NOAA AQM (NAQFC)", what: "Hourly PM2.5 forecast, 72 hours", license: "Public domain" },
  { name: "NOAA Hazard Mapping System", what: "Satellite smoke plumes and fire detections", license: "Public domain" },
  { name: "US Census ACS 2019-2023", what: "Population and income by neighborhood", license: "Public domain" },
  { name: "USGS The National Map", what: "Aerial imagery in Smoke World", license: "Public domain" },
  { name: "AWS Terrain Tiles", what: "3D terrain (USGS 3DEP and others)", license: "Open data, credit required" },
  { name: "OpenStreetMap via OpenFreeMap", what: "Places, roads and 3D buildings", license: "ODbL, credit required" },
  { name: "MapLibre GL JS", what: "3D map engine", license: "BSD-3-Clause" },
]

// Update log: real entries from docs/EXPERIMENTS.md and the project history.
// "Failed" means the change did not pass the team's acceptance checks and was not kept.
export const updates = [
  { date: "2026-11-25", kind: "Live", title: "The forecast map now updates each morning", note: "The daily job rebuilds the map data from that morning’s run." },
  { date: "2026-11-25", kind: "Failed", title: "Temporary fire monitors as a new input", note: "Nearby wildfire smoke monitors from the Forest Service archive did not improve days 1–2.", doc: "EXPERIMENTS.md" },
  { date: "2026-11-23", kind: "Evaluation", title: "Hour-by-hour accuracy tested", note: "Repeating the daily estimate across every hour was as accurate or better than the scaled hourly pattern.", doc: "HOURLY_ACCURACY.md" },
  { date: "2026-11-23", kind: "Accepted", title: "Recalibrated warning probabilities", note: "Fitted on calibration data. The point forecast did not change.", doc: "EXPERIMENTS.md" },
  { date: "2026-11-23", kind: "Failed", title: "GOES-West satellite smoke haze as a new input", note: "Did not improve the forecast, so it was not kept.", doc: "EXPERIMENTS.md" },
  { date: "2026-11-23", kind: "Failed", title: "Blending forecasters, second look", note: "Four more blending variants; none was better.", doc: "EXPERIMENTS.md" },
  { date: "2026-11-23", kind: "Failed", title: "2020 as extra training data", note: "Tried for the day 2–3 peaks that are still under-predicted.", doc: "EXPERIMENTS.md" },
  { date: "2026-11-23", kind: "Failed", title: "A fire growth input", note: "Previous-day fire radiative power did not help.", doc: "EXPERIMENTS.md" },
] as const
