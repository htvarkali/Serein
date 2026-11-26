// Interaction checks: reduced motion, the phone menu, the map page, 320 px reflow,
// keyboard focus, axe-core rules, and how busy each page stays when nothing is happening.
//
//   node scripts/site_check/serve.js website 8766 &
//   node scripts/site_check/interaction_check.js [base-url] [--shots]
//
// Needs `playwright` and `axe-core` (npm). Prints JSON and writes
// interaction_check.json to the current folder.
const { chromium, devices } = require('playwright');
const fs = require('fs');
const axeSrc = fs.readFileSync(require.resolve('axe-core/axe.min.js'), 'utf8');
const BASE = (process.argv.slice(2).find(a => a.startsWith('http')) || 'http://localhost:8766').replace(/\/$/, '') + '/#';
const SHOTS = process.argv.includes('--shots');
const routes = ['/', '/smokecast', '/world', '/airplan', '/about'];
const out = {};

(async () => {
  const browser = await chromium.launch();

  // A. Reduced motion
  {
    const ctx = await browser.newContext({ ...devices['iPhone 13'], reducedMotion: 'reduce' });
    const page = await ctx.newPage();
    await page.goto(BASE + '/', { waitUntil: 'load' }); await page.waitForTimeout(3000);
    out.reducedMotion = await page.evaluate(() => {
      const mq = document.querySelector('.marquee');
      const v = document.querySelector('video');
      const cs = mq && getComputedStyle(mq);
      const anims = document.getAnimations().filter(a => a.playState === 'running').map(a => (a.animationName || a.constructor.name));
      const count = {}; anims.forEach(n => count[n] = (count[n] || 0) + 1);
      return { matches: matchMedia('(prefers-reduced-motion: reduce)').matches, marqueeAnimation: cs && cs.animationName, marqueeState: cs && cs.animationPlayState,
        videoPaused: v && v.paused, videoAutoplay: v && v.autoplay, lenisClass: document.documentElement.className, runningAnimations: count };
    });
    // does the page move by itself? compare marquee position over a second
    const x1 = await page.evaluate(() => document.querySelector('.marquee').getBoundingClientRect().x);
    await page.waitForTimeout(1000);
    const x2 = await page.evaluate(() => document.querySelector('.marquee').getBoundingClientRect().x);
    out.reducedMotion.marqueeMovedPx = Math.round(Math.abs(x2 - x1));
    const t1 = await page.evaluate(() => document.querySelector('video').currentTime);
    await page.waitForTimeout(1000);
    const t2 = await page.evaluate(() => document.querySelector('video').currentTime);
    out.reducedMotion.videoAdvancedSec = +(t2 - t1).toFixed(2);
    await ctx.close();
  }

  // B. Menu on a phone
  {
    const ctx = await browser.newContext({ ...devices['iPhone 13'] });
    const page = await ctx.newPage();
    await page.goto(BASE + '/', { waitUntil: 'load' }); await page.waitForTimeout(2500);
    const btn = page.locator('header button').first();
    const info = { buttonLabel: await btn.getAttribute('aria-label'), buttonBox: await btn.boundingBox(), expandedBefore: await btn.getAttribute('aria-expanded') };
    await btn.tap(); await page.waitForTimeout(900);
    info.dialog = await page.evaluate(() => {
      const d = document.querySelector('[role=dialog]');
      if (!d) return null;
      const links = [...d.querySelectorAll('a,button')].map(el => { const r = el.getBoundingClientRect(); return (el.getAttribute('aria-label') || el.innerText.trim().replace(/\s+/g, ' ')).slice(0, 40) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height); });
      return { ariaModal: d.getAttribute('aria-modal'), labelled: !!(d.getAttribute('aria-labelledby') || d.getAttribute('aria-label')), focusInside: d.contains(document.activeElement), active: document.activeElement.tagName + ' ' + (document.activeElement.getAttribute('aria-label') || document.activeElement.innerText || '').slice(0, 30), links };
    });
    if (SHOTS) await page.screenshot({ path: 'shot_menu.png' });
    const axeMenu = await (async () => { await page.addScriptTag({ content: axeSrc }); return page.evaluate(async () => { const r = await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa'] }); return r.violations.map(v => ({ id: v.id, impact: v.impact, n: v.nodes.length, ex: v.nodes[0].html.slice(0, 120) })); }); })();
    info.axeMenuOpen = axeMenu;
    await page.keyboard.press('Escape'); await page.waitForTimeout(600);
    info.afterEscape = await page.evaluate(() => ({ dialogGone: !document.querySelector('[role=dialog]'), focus: document.activeElement.tagName + ' ' + (document.activeElement.getAttribute('aria-label') || '') }));
    out.menu = info;
    await ctx.close();
  }

  // C. Map page on a phone
  {
    const ctx = await browser.newContext({ ...devices['iPhone 13'] });
    const page = await ctx.newPage();
    await page.goto(BASE + '/world', { waitUntil: 'load' }); await page.waitForTimeout(5000);
    out.world = await page.evaluate(() => {
      const map = document.querySelector('.maplibregl-map');
      const r = map && map.getBoundingClientRect();
      const coop = [...document.querySelectorAll('.maplibregl-cooperative-gesture-screen, .maplibregl-cooperative-gesture-screen *')].map(e => e.textContent.trim()).filter(Boolean);
      const ranges = [...document.querySelectorAll('input[type=range]')].map(e => { const b = e.getBoundingClientRect(); return (e.getAttribute('aria-label') || e.name || 'range') + ' ' + Math.round(b.width) + 'x' + Math.round(b.height); });
      const buttons = [...document.querySelectorAll('main button, main [role=tab], main select')].map(e => { const b = e.getBoundingClientRect(); return (e.getAttribute('aria-label') || e.innerText || e.tagName).trim().replace(/\s+/g, ' ').slice(0, 30) + ' ' + Math.round(b.width) + 'x' + Math.round(b.height); });
      return { mapBox: r && { w: Math.round(r.width), h: Math.round(r.height), top: Math.round(r.top + scrollY) }, viewportH: innerHeight, cooperativeText: [...new Set(coop)], ranges, buttons, pageH: document.documentElement.scrollHeight };
    });
    const map = page.locator('.maplibregl-map');
    if (await map.count()) { await map.scrollIntoViewIfNeeded(); await page.waitForTimeout(800); if (SHOTS) await page.screenshot({ path: 'shot_world_map.png' }); }
    await page.evaluate(() => window.scrollTo(0, document.documentElement.scrollHeight)); await page.waitForTimeout(600);
    if (SHOTS) await page.screenshot({ path: 'shot_world_bottom.png' });
    await ctx.close();
  }

  // D. Home charts at phone size (the ring chart with very small labels)
  {
    const ctx = await browser.newContext({ ...devices['iPhone 13'] });
    const page = await ctx.newPage();
    await page.goto(BASE + '/', { waitUntil: 'load' }); await page.waitForTimeout(2500);
    const el = page.getByText('FORECAST ERROR BY DAY', { exact: false }).first();
    if (await el.count()) { await el.scrollIntoViewIfNeeded(); await page.waitForTimeout(1500); if (SHOTS) await page.screenshot({ path: 'shot_home_dial.png' }); }
    const up = page.getByText('Update log', { exact: false }).first();
    if (await up.count()) { await up.scrollIntoViewIfNeeded(); await page.waitForTimeout(1200); if (SHOTS) await page.screenshot({ path: 'shot_home_log.png' }); }
    await ctx.close();
  }

  // E. axe on every page at phone size, and reflow at 320 px
  out.axe = {}; out.reflow320 = {};
  for (const route of routes) {
    const ctx = await browser.newContext({ ...devices['iPhone 13'] });
    const page = await ctx.newPage();
    await page.goto(BASE + route, { waitUntil: 'load' }); await page.waitForTimeout(3000);
    // scroll through so reveal-on-scroll content is visible before testing contrast
    await page.evaluate(async () => { const h = document.documentElement.scrollHeight; for (let y = 0; y < h; y += 500) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 120)); } window.scrollTo(0, 0); });
    await page.waitForTimeout(800);
    await page.addScriptTag({ content: axeSrc });
    out.axe[route] = await page.evaluate(async () => {
      const r = await axe.run(document, { runOnly: ['wcag2a', 'wcag2aa', 'wcag21aa', 'wcag22aa', 'best-practice'] });
      return { violations: r.violations.map(v => ({ id: v.id, impact: v.impact, n: v.nodes.length, help: v.help, ex: v.nodes.slice(0, 3).map(n => ({ html: n.html.slice(0, 140), why: (n.any[0] || n.all[0] || n.none[0] || {}).message })) })), incomplete: r.incomplete.map(v => v.id + ':' + v.nodes.length), passes: r.passes.length };
    });
    await ctx.close();
    const c2 = await browser.newContext({ viewport: { width: 320, height: 640 }, isMobile: true, hasTouch: true });
    const p2 = await c2.newPage();
    await p2.goto(BASE + route, { waitUntil: 'load' }); await p2.waitForTimeout(2500);
    out.reflow320[route] = await p2.evaluate(() => ({ vw: document.documentElement.clientWidth, scrollW: document.documentElement.scrollWidth }));
    await c2.close();
  }

  // F. Keyboard focus on desktop: are focus rings visible?
  {
    const ctx = await browser.newContext({ viewport: { width: 1280, height: 900 } });
    const page = await ctx.newPage();
    await page.goto(BASE + '/', { waitUntil: 'load' }); await page.waitForTimeout(2500);
    const stops = [];
    for (let i = 0; i < 10; i++) {
      await page.keyboard.press('Tab');
      stops.push(await page.evaluate(() => { const a = document.activeElement; const s = getComputedStyle(a); const r = a.getBoundingClientRect(); return (a.getAttribute('aria-label') || a.innerText || a.tagName).trim().replace(/\s+/g, ' ').slice(0, 28) + ' | outline ' + s.outlineStyle + ' ' + s.outlineWidth + ' | ring ' + (s.boxShadow === 'none' ? 'none' : 'shadow') + ' | onscreen ' + (r.top >= 0 && r.top < innerHeight); }));
    }
    out.focus = stops;
    await ctx.close();
  }

  // G. Main-thread time used while the page sits idle (no scrolling, nothing playing)
  out.idle = {};
  for (const route of routes) {
    const ctx = await browser.newContext({ ...devices['iPhone 13'] });
    const page = await ctx.newPage();
    const cdp = await ctx.newCDPSession(page);
    await cdp.send('Performance.enable');
    await page.goto(BASE + route, { waitUntil: 'load' }); await page.waitForTimeout(6000);
    const read = async () => Object.fromEntries((await cdp.send('Performance.getMetrics')).metrics.map(m => [m.name, m.value]));
    const a = await read(); await page.waitForTimeout(5000); const b = await read();
    out.idle[route] = { busyPct: Math.round((b.TaskDuration - a.TaskDuration) / 5 * 100), scriptPct: Math.round((b.ScriptDuration - a.ScriptDuration) / 5 * 100), heapMB: Math.round(b.JSHeapUsedSize / 1e6) };
    await ctx.close();
  }

  fs.writeFileSync('interaction_check.json', JSON.stringify(out, null, 1));
  console.log(JSON.stringify(out, null, 1));
  await browser.close();
})();
