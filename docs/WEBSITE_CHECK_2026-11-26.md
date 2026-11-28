# Website check, 2026-11-26 (groundwork for W-12)

**Update, same day:** most findings below are now fixed in the site code. What changed
and the before-and-after numbers are in "Fixes made" at the end. Still open: H1 (a team
decision), M7, L4, L8 and L9.

What this is: a read of the built site in `website/` at commit `7a0c967`, at phone
size, with nothing in `website-src/` changed. It covers three things: whether the
site's words agree with the Brief and the README, how the five pages behave on a
phone, and what would make the site lighter. Each finding names the source file so
whoever owns the page can decide what to do with it.

How it was measured, and the limits of that:

- Chromium driven by Playwright, emulating an iPhone 13 (390 px wide) and a 360 px
  Android phone, plus a 320 px pass. The site was served from a local server that
  compresses text files, as GitHub Pages does. Scripts: `scripts/site_check/`.
- Lighthouse 12.6.1 in its default phone mode (slow 4G, CPU slowed 4 times).
- axe-core 4.10.3 for accessibility rules.
- The test machine was a cloud Linux box with no graphics card. **Treat the timings as
  a way to rank pages against each other, not as what a real phone will show.**
- The three map tile hosts could not be reached from that machine, so the map page
  drew smoke, wind and fires on a blank base. Its download size and drawing cost are
  under-counted here.
- Not done: a real iPhone or Android phone, Safari, a screen reader, and contrast of
  text that sits over photos or video (axe could not judge 77 to 203 text items per
  page for that reason).

To run it again:

```bash
npm install --no-save playwright axe-core lighthouse
node scripts/site_check/serve.js website 8766 &
node scripts/site_check/phone_check.js
node scripts/site_check/interaction_check.js
npx lighthouse "http://localhost:8766/#/" --only-categories=performance,accessibility
```

A shorter version, `scripts/site_check/ci_smoke.js`, now runs in CI on every push (the
`website` job): five pages at 360 px and 1280 px, failing on script errors, missing
files, sideways scrolling, a missing or extra h1, or serious and critical axe issues.

## What already works

- No sideways scrolling on any page at 390, 360 or 320 px.
- One `h1` per page, `lang="en"`, every image has alt text, and layout shift is 0.
- The phone menu button is 70 px, is labelled, moves keyboard focus into the menu and
  returns it on Escape. Keyboard focus outlines are visible.
- No console errors from the site's own code. Every link to a doc in the repo resolves.
- Every number on the site matches the README section "Current results (development
  rerun, 2026-11-23)" (`website-src/src/data/site.ts`).
- The cautions are there: "Not the final 2024-25 test", "Illustrative hourly map",
  "Check current AQI on AirNow", "This site collects no personal health information".
- A forecast older than 36 hours gets a notice and an AirNow link
  (`PlanCards.tsx:98`, `World.tsx:124`).
- The replay week (August 15 to 21, 2023) uses forecasts issued in ISO week 33, an odd
  week, which is a scoring week in development mode (`src/serein/eval/backtest.py`).
  So "tested on held-out 2023 weeks" holds for it.
- The map page uses almost no processor time when paused (1% of the main thread).

## Scores and sizes

| Page | Lighthouse performance | Accessibility | Time until usable | Blocked time | Downloaded |
|---|---|---|---|---|---|
| Home `/` | 42 | 93 | 10.1 s | 2,650 ms | 3,115 KB |
| SmokeCast | 66 | 97 | 4.8 s | 510 ms | 1,860 KB |
| Forecast map `/world` | 48 | 100 | 15.1 s | 8,260 ms | 1,124 KB plus map tiles |
| AirPlan | 67 | 96 | 5.3 s | 400 ms | 1,260 KB |
| Data and methods | 90 | 96 | 2.9 s | 220 ms | 344 KB |

"Downloaded" is from `phone_check.js` and counts the site's own files after
compression. The other columns are Lighthouse.

What the bytes are:

| File | Size sent | Loaded by |
|---|---|---|
| `motion/hero-smoke.mp4` | 2,058 KB | Home |
| `motion/hayes-fire.mp4` | 1,260 KB | SmokeCast |
| `motion/lake.mp4` | 572 KB | AirPlan |
| `data/live.json` | 334 KB (1,786 KB once unpacked) | Home, AirPlan, Forecast map |
| `assets/maplibre-gl-*.js` and its worker | 438 KB | Forecast map |
| `assets/index-*.js` | 164 KB | every page |
| `img/photo-hero.webp`, `img/photo-research.webp` | 257 KB, 190 KB | Home |

## Findings

Severity: **High** means fix before a judge or a nurse opens the site on a phone.
**Medium** means worth an hour. **Low** means when someone is in the file anyway.

### High

**H1. "AirPlan" means one thing in the Brief and another on the site.** In the README
and the Brief, AirPlan is the model that learns one child's sensitivity and gives that
child's family a plan. On the site, AirPlan is a page where anyone picks a place and
"An activity", "A family" or "An outdoor crew". Across all five pages the words
"asthma", "child", "inhaler", "parent", "nurse" and "doctor" appear 0 times. The
README's opening line says Serein gives "a personal risk plan for each child with
asthma", and Brief section 5 gives this site's address. Section 5 does say the family
plan is in a demo app, but a judge who opens the site and taps AirPlan will not find a
child or asthma anywhere. The site is accurate about what exists (the child model is
tested on simulated children only), so this is a decision for the team, not a bug:

- either the site's page gets another name (for example "Smoke planner") and the Brief
  keeps "AirPlan" for the child model in the demo app (`app/streamlit_app.py`);
- or the AirPlan page gets one short section that describes the child plan and labels
  it as tested on simulated children.

Done 2026-11-27 (second option): the AirPlan page now has a section "A plan for one
child with asthma", labelled as tested on simulated children, with a screenshot of the
demo app's family plan.

**H2. The home page never stops drawing.** The dot map redraws on every animation
frame, on screen or off, to make the dots pulse
(`components/site/LiveForecast.tsx:94-132`). With nothing happening, the home page
kept the main thread 30% busy (18% running script). The same measure was 1% on the
map page and 9% to 13% on the others. Home also has the lowest Lighthouse performance
score (42). Suggested: draw once, and run the loop only while the canvas is on screen
(an `IntersectionObserver`) and the reader has not asked for reduced motion.

**H3. The "reduce motion" setting is ignored.** With the setting on, the headline
still moved 56 px a second, the background video kept playing, the glow, spin and
pulse animations kept running, and smooth scrolling stayed on. There is no
`prefers-reduced-motion` rule in `styles.css` or `Motion.tsx`. The looping videos and
the moving headline also have no pause control, which WCAG 2.2.2 (level A) asks for
when movement starts by itself and lasts more than five seconds. Suggested:

```css
@media (prefers-reduced-motion: reduce) {
  .marquee, .spin-slow, .spin-rev, .float, .status-dot, .band-dark::before { animation: none; }
  .js [data-reveal] { opacity: 1; transform: none; filter: none; transition: none; }
}
```

and in `Motion.tsx`, skip Lenis and the parallax tweens, and pause the videos, when
`matchMedia("(prefers-reduced-motion: reduce)").matches`.

### Medium

**M1. "Updates each morning" is not what happens.** The forecast is issued at 11:30
am Pacific and the site's data is pushed after the 11:45 run (README row W-11). The
footer on every page (`SiteLayout.tsx:137`) and the update log (`data/site.ts:90`) say
"each morning" and "that morning's run". Brief section 5 says "every morning".
Suggested wording: "updates each day around midday Pacific".

**M2. Before midday, the cards are a day behind the reader.** At 11:30 am Pacific on
November 26 the first card read "Issue day, Wed, Nov 25" and today was "Day 1 ahead"
(`PlanCards.tsx:54`, `World.tsx:23`). The home button says "See tomorrow's forecast",
so the reader has to work out which card that is. Suggested: label cards "Today" and
"Tomorrow" from the reader's own date, and keep the issue date in small text.

**M3. On a phone, the header button runs under the menu button.** After scrolling,
"See tomorrow's forecast" spans 116 to 343 px and the menu button starts at 302 px, so
the last 41 px sit under it on a 390 px screen (`SiteLayout.tsx:90`). The header has no
background, so the logo also sits directly on page text. Suggested: hide the pill
below the `sm` width, or shorten it to "Forecast".

**M4. On a phone, the main headline is never readable in one look.** The visible
headline is a line scrolling sideways at 72 px type, so a 390 px screen shows about
twelve letters at a time (`Home.tsx:87`). Screen readers get a proper hidden `h1`,
which is good. Suggested: a still, wrapped headline below the `md` width.

**M5. Chart labels are too small on a phone.** The ring chart is an SVG that shrinks
with the screen, so at 390 px its labels come out at 6.5 px ("µg/m³ · LOWER IS
BETTER"), 7.5 px (the day names), 8 px (the scale) and 9.6 px (the legend)
(`ForecastDial.tsx:50-58`). Bar chart labels are 11 px. Suggested: keep the ring, move
its labels into normal text under it on small screens.

**M6. Phones download the background videos.** 2,058 KB on Home, 1,260 KB on
SmokeCast, 572 KB on AirPlan, each with `autoPlay` (`Home.tsx:78`, `Section.tsx:91`).
Each already has a still poster image. Suggested: below 768 px, or with reduced
motion or data saver on, show the poster only. That takes Home from 3,115 KB to about
1,060 KB.

**M7. Three pages fetch the whole forecast file.** `data/live.json` is 334 KB sent
and 1,786 KB once unpacked. Home needs it for four numbers and the dot map, AirPlan
for one location. Suggested: have the daily job also write a small summary file for
Home and AirPlan, and leave the full file to the map page.

### Low

| | Finding | Where | Suggested |
|---|---|---|---|
| L1 | The AirNow link in the footer is told apart from the text around it by color only (white on grey, 2.52 to 1, underlined only on hover). axe rates this serious; it is on four pages | `SiteLayout.tsx:169` | Underline it always |
| L2 | `aria-label` on a plain `<p>`, which is not allowed and may be ignored, leaving a screen reader to read the paragraph word by word | `Section.tsx:77` | Hidden full text plus `aria-hidden` on the animated words, as the headline already does |
| L3 | The logo link is named "Serein home" but shows "Falcon Devs Serein", which trips voice control | `SiteLayout.tsx` `Wordmark` | `aria-label="Falcon Devs Serein, home"` |
| L4 | One page, three names: "Forecast map" in the menu, "Forecast explorer" as the heading, "Smoke World" as the tab title, the home card tag and in the Brief, video script and pitch deck | `main.tsx:21`, `World.tsx:175` | Pick one and use it everywhere |
| L5 | On a phone the map is 356 by 345 px and the credits box opens over about a fifth of it until the map is touched | `ForecastMap.tsx:118` | Start it closed on small screens |
| L6 | Small touch areas: the two exposure sliders are 16 px tall, map zoom buttons 29 px, footer and "Read the ..." links 20 to 21 px. Apple and Google suggest 44 to 48 px | `World.tsx`, `SiteLayout.tsx` | More padding on small screens |
| L7 | The map page has no "Skip to content" link; the other four do | `World.tsx` | Add it |
| L8 | One team member is shown with a name and grade and nothing under them. The Brief has the same open slot | `data/site.ts:71` | Fill both together |
| L9 | Six images in `website/img/` (1,940 KB, of which `world-preview.png` is 1,092 KB) are not used by any page. They do not slow the site, only the repo. `docs/drafts/pitch_deck.md` names `world-preview.png` as the source of a slide picture | `website/img/` | Remove, or move the ones the docs use |

## Order of work, if W-12 is picked up

1. H3 and M6 together: one CSS block and one check in `Motion.tsx` cover reduced
   motion, and the same check can hold back the videos on phones.
2. H2: stop the dot map loop when it is off screen.
3. M1 to M5: wording and small-screen layout.
4. M7, then the low items.
5. Run the scripts again, then check on one real iPhone and one real Android phone,
   since nothing here was measured on real hardware.

H1 is separate. It is a decision about what the Brief and the site say, and it should
be made before the Brief is frozen.

## Fixes made, 2026-11-26

Changed in `website-src/`, then rebuilt into `website/` with `npm run build` and
checked with `python3 scripts/check_website.py`. An unchanged rebuild was compared
with the committed site first: the JavaScript was identical apart from file names, and
the CSS differed only in the sixth decimal place of a few colors, so the rebuild
changes nothing except what is listed here.

| Finding | What changed | Files |
|---|---|---|
| H2 | The dot map draws only while it is on screen, at about 20 frames a second instead of every frame, and once if motion is reduced or paused | `LiveForecast.tsx` |
| H3 | With "reduce motion" on: no looping animations, no slide-in or blur reveals, no smooth scrolling or parallax, no background video. Everyone else gets a pause button in each hero, which stops the video and every looping animation on the page | `Motion.tsx`, `Section.tsx`, `styles.css`, `Home.tsx`, `ForecastDial.tsx` |
| M6 | Phones (under 768 px), data saver and reduced motion get the still poster image; the clip is never downloaded | `Section.tsx` (`BackgroundVideo`) |
| M1 | Footer and update log say the map updates every day around midday Pacific | `SiteLayout.tsx`, `data/site.ts` |
| M2 | Forecast cards say "Today" and "Tomorrow" from the reader's Pacific date, with "Issue day" or "Day 1 ahead" underneath. Archived examples keep plain dates | `lib/world.ts` (`relativeDay`), `PlanCards.tsx`, `World.tsx` |
| M3 | The header pill is hidden under 640 px, and kept out of the tab order while it is invisible | `SiteLayout.tsx` |
| M4 | Under 768 px the headline stands still and wraps; the moving line stays on wider screens | `Section.tsx` (`Marquee`), `Home.tsx` |
| M5 | On phones the ring chart hides its tiny labels and lists the same numbers under it as normal text. Smallest mono labels raised from 9.9 to 11.2 px | `ForecastDial.tsx`, `Home.tsx`, `SiteLayout.tsx`, `Section.tsx`, `LiveForecast.tsx` |
| L1 | Footer AirNow link always underlined | `SiteLayout.tsx` |
| L2 | The word-by-word paragraph gives screen readers the sentence once, in hidden text, instead of an `aria-label` on a `<p>` | `Section.tsx` (`WordReveal`) |
| L3 | The logo link is named by its own text ("Falcon Devs Serein home") | `SiteLayout.tsx` |
| L5 | On a phone the map's credits box starts closed; the (i) button opens it | `ForecastMap.tsx` |
| L6 | Exposure sliders and the home comparison slider 28 px tall; footer, AirPlan and "Read the ..." links get 6 px more touch area above and below | `PersonPanel.tsx`, `LiveForecast.tsx`, `SiteLayout.tsx`, `AirPlan.tsx`, `SmokeCast.tsx` |
| L7 | The map page has a "Skip to content" link | `World.tsx` |

Also: the home hero gets 96 px of space at the top, so on a 320 px screen the status
pill no longer runs under the logo.

### Before and after

Same machine, same scripts, same Lighthouse settings as above.

| Page | Performance | Accessibility | Time until usable | Blocked time | Downloaded (site files) |
|---|---|---|---|---|---|
| Home | 42 → 52 | 93 → 100 | 10.1 s → 5.9 s | 2,650 → 1,040 ms | 3,115 → 1,060 KB |
| SmokeCast | 66 → 72 | 97 → 100 | 4.8 s → 4.8 s | 510 → 310 ms | 1,860 → 601 KB |
| AirPlan | 67 → 71 | 96 → 100 | 5.3 s → 5.3 s | 400 → 270 ms | 1,260 → 692 KB |
| Data and methods | 90 → 89 | 96 → 100 | 2.9 s → 3.0 s | 220 → 190 ms | 344 → 346 KB |
| Forecast map | no change | 100 → 100 | about 15 s | about 7,500 ms | 1,124 → 1,128 KB |

The map page score moved between 25 and 43 from one run to the next. Run side by side,
the old and new builds scored 41 to 43 and 42, so nothing changed there; its slow
start is the map library itself and is the main thing left for W-12.

Other checks after the fixes:

- Main thread busy while the home page sits idle: 30% → 14% (script 18% → 1%).
- With "reduce motion" on, phone and desktop: no running animations, no video, the
  headline does not move, normal scrolling.
- Pause button on a desktop screen: video and headline stop, and start again on a
  second press.
- axe-core: 0 violations on all five pages (was 2 rule types on four pages).
- No sideways scrolling at 390, 360 or 320 px; no console errors from the site's code.
- Remaining small touch targets: the map's own zoom buttons (29 px) and the population
  switch on the map page.

### Still open

- **H1**, the meaning of "AirPlan": a team decision, see above.
- **M7**, a small summary file so Home and AirPlan do not fetch the whole forecast:
  needs a change to `serein.world` and the daily job, which Aadi runs.
- **L4**, one name for the map page: a team decision.
- **L8**, the empty role on the team card: the team.
- **L9**, unused images: left in place because `docs/drafts/pitch_deck.md` points at one.
- A check on a real iPhone and Android phone.

## Map page start-up, 2026-11-26 (later)

A CPU profile at phone speed showed the site's own code using about 1 s; loading the page
with the map library blocked cut the frozen time from about 3.8 s to 0.2 s. So the map
library was nearly all of it. Two changes in `ForecastMap.tsx`, neither changing what the
map shows:

- The map starts only when it is within 200 px of the screen, after the forecast has
  loaded (or 3 s have passed) so the layout has settled. On a phone the forecast card sits
  above the map, so the page is usable before the map starts. On a wide screen the map is
  visible at once and starts as before.
- The map is drawn at no more than 2 times the screen's pixel size. Phones are 3 times,
  so this draws 2.25 times fewer pixels.

| Map page, phone audit (two runs each) | Before | After |
|---|---|---|
| Lighthouse performance | 23 and 42 | 77 and 78 |
| Time until usable | 14.3 to 15.3 s | 5.1 s |
| Blocked time | 7,400 to 8,500 ms | 60 to 70 ms |
| Downloaded at load | 979 KB | 688 KB |

Measured directly at phone speed (two runs each): frozen time in the first 10 s went
from 3.7 to 4.7 s down to 0.15 to 0.23 s. Scrolling to the map then freezes the page for
2.6 to 3.2 s while it starts, less than before because of the pixel cap. On a 1280 px
screen nothing changed (3.6 to 4.3 s both ways), as expected. Picking a place before the
map starts still moves the map there once it loads, and tapping the map still picks a
point. These timings are from a machine with no graphics card, which makes map drawing
slower than on a real phone.

The automatic checks now also build the site (`.github/workflows/ci.yml`, job `website`):
a fresh install, a type check, a build into a temporary folder and
`scripts/check_website.py` on the result. The committed `website/` is not compared,
because builds on different machines differ in the last decimal of a few CSS colors.
