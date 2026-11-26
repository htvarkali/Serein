# One page for a school district or school nurse (DRAFT, unsent)

Written 2026-11-26 for task E-7. Attach it, as a PDF, only after the person has agreed
to talk; the first email stays three sentences (see
`docs/interviews/OUTREACH_TARGETS.md`). The numbers are development results and must be
replaced after the final test. Everything below the line is the page.

---

## Serein: a day's notice before a smoke day

**A free pilot for the 2027 fire season, from five students at Foothill High School,
Pleasanton.**

### What it is

Serein is a wildfire smoke forecast for each neighborhood, one to three days ahead. It
starts from NOAA's smoke forecast and corrects it with what EPA's air monitors are
measuring that morning. Each forecast comes with a range, for example "about 75, could
reach 140."

### What your schools would get

- Each day of fire season, by about noon, the expected air quality at each of your
  schools for today and the next three days.
- A flag when tomorrow is likely to reach "Unhealthy for Sensitive Groups" (AQI 101)
  or worse, so indoor recess, practice changes and inhaler checks can be planned the
  day before.
- If you want it, and only after a clinician and an ethics board have approved it: a
  sign-up link for families of children with asthma, who get a green, yellow or red
  plan for their own child. Every plan tells the family to follow their child's own
  doctor's asthma action plan.

### What we have measured so far

On fire-season weeks of 2023 that the model never saw:

| One day ahead | Serein | EPA's official forecast |
|---|---|---|
| Unhealthy-for-sensitive-groups days warned about | 72% | 46% |
| False alarms | 92 | 98 |

At monitors we hid from the model, to stand in for neighborhoods without one, its
error a day ahead was 8.4 µg/m³ against 11.1 for NOAA's forecast.

These are development results. Our final test, on 2024 and 2025, has not been run yet,
and we will report it whatever it shows. All of it is public: htvarkali.github.io/Serein

### What it is not

- It does not replace your air quality chart, AirNow, or the air district. Those tell
  you about the air now. Serein is for planning the day before.
- It gives a level for each day. We tested hour-by-hour forecasts and they could not
  tell which hours of a day would be worst, so we do not offer that.
- It is not a medical device, and it does not decide whether a school closes.
- It has not yet been used by a school or by real families.

### What we are asking

1. Fifteen minutes, to learn how your district decides what to do on a smoke day.
2. If it seems useful after that, a free pilot for the 2027 fire season with one or
   two schools. We would ask you for two things at the end: how many smoke days you
   had notice of, and whether the notice changed anything.

There is no cost and no contract.

**Contact:** [TEAM: name, role, team email address] · Coach: [TEAM: name]

---

## Notes for the team (not part of the page)

- Sources for every number: README "Current results (development rerun, 2026-11-23)";
  the hourly finding is `docs/HOURLY_ACCURACY.md`.
- "AQI 101" is the level where the San Ramon Valley chart starts to recommend indoor
  recess for students with asthma, and it is the level our warning is scored on.
- The forecast is issued at 11:30 am Pacific, so the page says "by about noon". Brief
  section 8 says "each morning"; make the two agree.
- Do not send this before a coach is named and the team email exists.
- To make the PDF, print this section from GitHub's rendered view, or paste it into a
  document. Keep it to one page.
