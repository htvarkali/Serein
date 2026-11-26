# Website check, 2026-11-26 (groundwork for W-12)

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
