# Innovation Video: script and storyboard (task S-9)

Revised 2026-11-25: numbers moved to the 2026-11-23 development rerun, Smoke World
added as the main thing on screen, five team members, and the wording about the
check-in brought in line with what the app does today.

Target length 4:20 (limit 3 to 5 minutes). Conrad asks for "a 3-5 minute demonstration
of your innovation." Ours is a working prototype: the live 3D map, the forecast behind
it, and a plan being generated. Upload unlisted to YouTube or Vimeo AND export an MP4
under 800 MB.

Principles
- Lead with the child, not the model. A judge should feel the problem in the first
  30 seconds. The graph network gets 30 seconds, as the answer to "how."
- Every number on screen comes from the README section "Current results (development
  rerun, 2026-11-23)" until the final test runs. Label them "development results, 2023."
  Replace them after D-5, even if they are worse.
- Every team member appears and explains their own part on camera. This is the best
  answer to "did students really build this?"
- Say "development" and "simulated" where true. The rubric's Practicality criterion
  rewards a team that knows its own limits.
- No stock footage of fires. Screen recordings and the team talking are enough.
- Captions on (many judges watch muted). No music under speech.

Scoring lens (Storytelling and Professionalism, 20%): clarity of the opportunity,
investor appeal, and the same name, logo and colors as the website and the Brief.

**Check before recording.** `docs/results/` is still the November 2 snapshot (71%, 81
false alarms). The README and the Brief quote the November 23 rerun (72%, 92 false
alarms). Use the README numbers, and re-export the snapshot and the figures before a
chart goes on screen, so the chart and the voice say the same thing.

---

## One-sentence pitch (use everywhere: video open, website hero, Brief Q1 first line)

> Tomorrow's smoke forecast is for your whole city. Serein tells a parent what it
> means for their neighborhood and their child, a day ahead.

Alternate for a parent audience:

> When wildfire smoke is coming, Serein tells you the day before: how bad it will be
> where you live, and what to do for your kid.

---

## Storyboard

| Time | On screen | Voice (who) | Notes |
|---|---|---|---|
| 0:00-0:25 | Black, then a phone lock screen. A text arrives: the YELLOW message for "Maya" from `docs/mockups/messages.md`. Cut to a team member on camera. | **[A]**: "This is the text we want a parent to get the evening before a smoke day. It says how bad the air will be in their neighborhood tomorrow, and what to do for their daughter, who has asthma. Four point eight million American kids have asthma, and smoke is one of the things that sends them to the ER. We built Serein so that text can exist." | Hook. "4.8 million" is CDC 2023. Caption: "Maya is an example child from our simulation." No logo yet. |
| 0:25-0:45 | Side by side: the AirNow forecast for one metro "reporting area" and Smoke World zoomed into a town in the same area. | **[A]**: "Today a parent gets one forecast for the whole metro area. Smoke doesn't arrive that way, and the advice is the same for every child: 'unhealthy for sensitive groups.' That doesn't tell you whether your kid is fine at 40 micrograms or needs the inhaler at 20." | The gaps, shown and not listed. |
| 0:45-1:05 | Title card: Serein logo and tagline. Then five quick face shots with names and grades. | **[A]**: "We're five students at Foothill High School. Aadi built the data pipeline and both models. Harshateja built the website and the sensor checks. Arush did the ozone, heat and pollen inputs and the competitor research. Abhinav did the business model. [Jagath: his part.]" | Must match Brief Q2 and the website. Each person says their own line if time allows. [TEAM: Jagath's role.] |
| 1:05-1:40 | Screen recording of Smoke World (htvarkali.github.io/Serein): fly over the West, press play, smoke and wind move; click a town to open its forecast and range; switch between NOAA's forecast and Serein's. Caption: "graph neural network". | **[Aadi]**: "This is Smoke World. It updates every day. NOAA already runs a smoke model, and about 400 EPA monitors in the West are measuring smoke right now, but the forecast a family reads doesn't use those live readings. Ours does. Our model treats the monitors as a network: each one learns from its neighbors, NOAA's forecast, the weather and the fires, and corrects NOAA's number one to three days out. Every forecast comes with a range, and the real value lands inside our 90% range about 90% of the time." | The one technical stretch. Say "graph neural network" once at most; the caption carries it. |
| 1:40-2:00 | Stay in Smoke World, slow the playback. Caption: "Tested per day, not per hour." | **[Aadi]**: "One thing we want to be straight about. The hour-by-hour motion you see comes from NOAA. We tested it against real hourly readings, and neither NOAA's forecast nor ours could say which hours of a day would be worst. So Serein gives advice per day." | Source: `docs/HOURLY_ACCURACY.md`. Showing a limit on purpose earns Practicality points. |
| 2:00-2:30 | Chart: warnings a day ahead, Serein and EPA (re-exported `fig_warnings_vs_epa.png`). Then the August 2023 replay on the SmokeCast page. Caption all of it: "Development results, 2023 held-out weeks." | **[Harshateja or Aadi]**: "We tested it the way a scientist would: train on 2021 and 2022, then score on fire-season weeks the model never saw. One day ahead, Serein warned on 72% of the days that really turned unhealthy for sensitive groups. EPA's official forecast warned on 46%, and we raised fewer false alarms, 92 against 98. Two days ahead we still catch more days, 62% against 37%, but with more false alarms than EPA, 48 against 36. We report that too." | **Replace with the 2024-25 numbers after D-5.** |
| 2:30-2:55 | Smoke World people layer: neighborhoods by income, and places more than 25 km from a monitor. | **[Harshateja]**: "It also works where there is no monitor. We hid one monitor in five from the model and it still beat NOAA there. That matters for fairness: in the lowest-income fifth of western neighborhoods, about one person in ten lives more than 25 kilometers from any monitor. In the highest-income fifth it is fewer than one in a hundred." | 10.8% vs. 0.6%, `docs/EQUITY.md`. Hidden monitors: 8.4 vs. 11.1 µg/m³ a day ahead. |
| 2:55-3:35 | Screen recording: the app's family plan tab, then `uv run serein airplan-demo --seed 3 --language es` and the English version. A green plan and a red plan appear. Then the six-tap check-in screen. Caption: "Simulated child." | **[Aadi or Arush]**: "A forecast is only useful if it becomes a decision for one child. The second model is built to learn how much smoke affects that child from a six-tap check-in each evening. Today it runs on simulated children: 300 of them, and after about two weeks of logs the personal model beats the one-size-fits-all one. It turns tomorrow's forecast into a green, yellow or red plan, in English or Spanish. Two rules never bend: a plan can be stricter than EPA's public guidance, never looser, and it always says to follow the child's own doctor's plan." | The check-in form in the app takes fictional entries and does not yet feed the model shown; do not imply real families use it. If a clinician has reviewed by filming day, add "Reviewed by [role, affiliation]." |
| 3:35-4:00 | Simple slide: who pays. Icons for a school district, a health plan, an air district. One line of pricing. | **[Abhinav]**: "Families never pay. School districts already pay about two thousand dollars a building for emergency software; we charge a quarter to half of that. Our data is free from NOAA, NASA and EPA, and the model for the whole West runs in a fraction of a second on an ordinary computer, so the main cost is the text messages: about a dollar a family in a heavy season." | Numbers: `docs/BUSINESS_NUMBERS_2026-11-07.md` and `src/serein/business.py` ($1.13 per family for 60 alerts by SMS). |
| 4:00-4:20 | Team on camera together. End card: name, tagline, website address, "Conrad Challenge 2026-27". | **[A]**: "This spring we want to run Serein with one school district through one fire season, with a clinician reviewing every message, and measure two numbers: how many smoke days we warned about a day ahead, and how many families kept logging after a month. Kids with asthma shouldn't find out about smoke from a cough." | Add the category to the end card once S-1 confirms it. |

Spoken words: about 650, timed at 150 words a minute, which is 4:20 with the title card. If it
runs long, cut the "tested per day, not per hour" row to one sentence before cutting the results.

---

## Shot list and assets

- Phone lock-screen text: send the mockup text to your own phone and film it arriving,
  or screen-record a phone mockup. Use the exact wording from `docs/mockups/messages.md`.
- AirNow reporting-area screenshot: airnow.gov for your metro, forecast tab.
- Smoke World: record at 1920x1080 in a clean browser window with no other tabs. Record
  the August 2023 replay too, so there is smoke on screen even if the West is clear on
  filming day.
- App: `uv run streamlit run app/streamlit_app.py`, same window size.
- Charts: `docs/results/figures/`, re-exported after the snapshot is rebuilt (see the
  check at the top) and again after the final test.
- Plan generation: terminal recording of `airplan-demo` with a large font.
- Diagram, if one is needed: three boxes (NOAA forecast + live monitors, Serein,
  neighborhood forecast), drawn in the website colors. The chart in the README is too
  dense for video.
- Team shots: one location, daylight, phone camera at eye level, a quiet room.

## Editing

- Any editor works (iMovie, DaVinci Resolve free, CapCut desktop). Export H.264 1080p,
  under 800 MB (a 4-minute 1080p export is usually 200 to 400 MB).
- Captions: auto-generate in YouTube, then correct every number by hand.
- Last check before upload: every number on screen matches the README's current
  results (or the final report after D-5); the category matches the portal; the website
  address works in a private window.
- Conrad's workshop "Innovation Insight: Communicating your Idea" is December 10, 2026,
  4 to 5 pm CST. Watch it before filming.

## Website hero (S-8) should match

Hero line: the one-sentence pitch above. Sub-line: "A free neighborhood smoke forecast
and a personal plan for every child with asthma. Built by students, scored against NOAA
and EPA."
