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

## To-do list

The task list lives on the README task board, section **W: Smoke World** (W-1 to W-20), in
the same format as every other task: anyone can pick up an **Open** task, set it to **In
progress** with their name and the date, and mark it **Done** when finished. Non-code tasks
that also matter for the 3D world are already on the board: interviews (E-1), Spanish review
(C-7), the video (S-9) and the Brief (S-4 to S-6).

## Timeline

| By | What |
|---|---|
| Nov 30 | W-2 to W-5: fly over the West and play 72 hours of smoke |
| Dec 7 | W-6 to W-9, W-13 (hourly test), W-16 to W-18 |
| Dec 14 | W-10 to W-12, W-14, W-15, website ready |
| Dec 17 | Model freeze and the one-time final test |
| Dec 17 - Jan 1 | Video, Brief, interviews written up |
| Jan 7 | Submit |

## What we will say about it (honest wording)

"Serein's Smoke World shows NOAA's hour-by-hour smoke forecast for the next three days,
corrected by Serein's tested daily forecast, on real terrain. Hourly accuracy: [W-13 result]."
We never call it a physics simulation we built ourselves.
