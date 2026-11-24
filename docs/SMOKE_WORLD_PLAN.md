# Serein Smoke World: plan and to-do list

Written 2026-11-23 for the whole team. Plain language first; details under each task.

## What we are building

An interactive 3D world of the western US (WA, OR, CA, NV, ID, western AZ) that anyone can
open in a web browser. You fly over real terrain, zoom into any town, and press play to
watch the smoke forecast move **hour by hour for the next 3 days**: where the smoke goes,
how thick it gets, which way the wind blows, where the fires are, and who is under it.
Click any place to see its hourly smoke and what to do about it.

It has two modes:
- **Live:** today's forecast plus the next 3 days, updated every day.
- **Replay:** a past smoke event (August 2023), where you can switch between the forecast
  and what really happened.

## The one rule

Everything you see must come from real data or a real, named model. We do **not** invent
smoke physics. The smoke movement comes from NOAA's own models; Serein corrects how much
smoke there is. If something is an estimate, the screen says so.

## Is the data free?

Yes. Every layer below is free public data, and none needs a paid account.

| Layer | What it shows | Source | Cost |
|---|---|---|---|
| Terrain | Mountains, valleys, coast in 3D | AWS Terrain Tiles (from USGS 3DEP), streamed as you zoom | Free, no key |
| Ground imagery | What the land looks like from above | Sentinel-2 cloudless by EOX | Free for non-commercial use, with credit |
| Buildings (close-up) | 3D building shapes in towns | OpenStreetMap / Microsoft US Building Footprints | Free (ODbL), with credit |
| Smoke, hour by hour | Smoke moving for 72 hours | NOAA AQM (hourly, 72 h) and HRRR-Smoke (hourly, 48 h) | Free |
| Serein correction | Better daily smoke level per place | Our own model | Ours |
| Wind | Which way smoke is blowing | NOAA HRRR 10 m wind | Free |
| Fires | Active fires seen by satellite | NOAA HMS fire points | Free |
| Air monitors | Real measured readings | EPA AirNow | Free |
| People | Who lives under the smoke | US Census (ACS) by neighborhood | Free |
| Land use | Farms, forests, towns | USGS National Land Cover Database | Free |
| Schools, hospitals | Places that need warnings | OpenStreetMap | Free |

Things we will **not** use: Google Photorealistic 3D Tiles and Cesium ion terrain (need billing or
accounts), PurpleAir history (paid). The team agreed: no money spent except the $499 Conrad fee.

## Already done (2026-11-23)

- [x] Hour-by-hour smoke data for every point in the West, 72 hours ahead, both NOAA's raw
      version and the Serein-corrected version (`serein.world`).
- [x] Wind every 3 hours (to 48 h) and live fire points in the same file.
- [x] A 2D replay page for August 2023 (on the website branch).

## To-do list

Owner suggestions are just suggestions. Claim a task by writing your name next to it.
"Done means" is how we know a task is finished.

### A. The 3D engine (code)

- [ ] **A1. 3D globe with streaming terrain.** Open the world in the browser, fly anywhere in
  the West, terrain gets sharper as you zoom. *Done means:* Mount Rainier and the Central
  Valley look right up close, and it runs smoothly on a normal laptop. *(Aadi)*
- [ ] **A2. Ground imagery and labels.** Satellite imagery on the terrain, state lines, city
  names. *Done means:* you can recognize Seattle, Portland, Sacramento from above. *(Aadi)*
- [ ] **A3. Smoke layer, hour by hour.** The smoke as a colored haze over the land, by AQI
  color, changing each hour. *Done means:* press play and watch 72 hours of smoke move. *(Aadi)*
- [ ] **A4. Time controls.** Play, pause, speed, a slider for hour 0-72, and the local time and
  date always on screen. *(Aadi or Harshateja)*
- [ ] **A5. Wind.** Moving arrows or streaks that show wind direction and speed, and that stop
  after hour 48 where NOAA's wind forecast ends (with a note). *(Aadi)*
- [ ] **A6. Fires.** Glowing points where satellites see fire, sized by fire strength. *(Aadi)*
- [ ] **A7. Click anywhere.** A panel with that place's 72-hour smoke curve, the chance of
  unhealthy air, the confidence flag, and the advice for workers and families. *(Aadi)*
- [ ] **A8. NOAA vs. Serein switch.** One button to compare NOAA's raw forecast with Serein's
  corrected one. *(Aadi)*
- [ ] **A9. 3D buildings up close.** Building shapes appear when you zoom into a town.
  *Done means:* downtown Sacramento shows buildings without slowing the page. *(Aadi)*
- [ ] **A10. Daily live update.** The scheduled job rebuilds the live data every morning after
  the forecast, so the website always shows today. *(Aadi)*
- [ ] **A11. Works on phones and slow computers.** A lighter version (fewer details) loads on
  phones. *(Harshateja)*

### B. Proof (so judges trust it)

- [ ] **B1. Hourly accuracy test.** On real 2023 days, compare Serein's corrected hourly smoke
  and NOAA's raw hourly smoke against real hourly monitor readings. Report whichever is better,
  honestly. *(Aadi)*
- [ ] **B2. Replay mode.** August 2023 in the 3D world, with a switch to show what really
  happened. *(Aadi)*
- [ ] **B3. "Where the data comes from" panel.** One click shows every source and what is
  measured vs. forecast vs. estimated. *(Arush)*

### C. People layer (the story)

- [ ] **C1. Neighborhood population and income.** Color neighborhoods by income and show how
  many people are under the smoke each hour. Data is already downloaded. *(Arush)*
- [ ] **C2. Places that matter.** Schools, hospitals, farms and work sites from OpenStreetMap
  and land-cover data, with a count of how many are under unhealthy smoke each hour. *(Arush)*
- [ ] **C3. Areas with no monitor.** Highlight places more than 25 km from any air monitor
  (from `docs/EQUITY.md`). *(Arush)*

### D. Not code (anyone can do these)

- [ ] **D1. Interviews.** Talk to 5+ outdoor workers or farm managers and 2+ school nurses or
  health staff: would a 3-day smoke world help them, and what would they click first? Notes go
  in `docs/interviews/` (no names). *(Jagath)*
- [ ] **D2. Test it on real people.** Watch 5 people use the 3D world for the first time and
  write down where they get stuck. *(Jagath)*
- [ ] **D3. Spanish check.** A native Spanish speaker reads every Spanish message. *(anyone who
  speaks Spanish natively)*
- [ ] **D4. Video.** Record the 3D world for the 3-5 minute Conrad video. *(Abhinav)*
- [ ] **D5. Brief.** Describe the 3D world in Brief questions 4 and 5, with the hourly test
  numbers from B1. *(Abhinav, with Aadi for the numbers)*
- [ ] **D6. Credits.** Make sure every data source is credited on the website (several licenses
  require it). *(Harshateja)*

## Timeline

| By | What |
|---|---|
| Nov 30 | A1-A4: fly over the West and play 72 hours of smoke |
| Dec 7 | A5-A8, B1 (hourly test), C1-C3 |
| Dec 14 | A9-A11, B2-B3, website ready |
| Dec 17 | Model freeze and the one-time final test |
| Dec 17 - Jan 1 | Video, Brief, interviews written up |
| Jan 7 | Submit |

## What we will say about it (honest wording)

"Serein's Smoke World shows NOAA's hour-by-hour smoke forecast for the next three days,
corrected by Serein's tested daily forecast, on real terrain. Hourly accuracy: [B1 result]."
We never call it a physics simulation we built ourselves.
