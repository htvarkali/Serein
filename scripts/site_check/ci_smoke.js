// Browser smoke test of a built site, run in CI on every push (job "website").
// Each page, at phone and laptop size: no uncaught script errors, no missing files of
// our own, no sideways scrolling, one h1, and no "serious" or "critical" axe-core
// accessibility issues. Map tiles and other outside hosts are blocked, so the result
// does not depend on someone else's server.
//
//   node scripts/site_check/serve.js website 8766 &
//   node scripts/site_check/ci_smoke.js [base-url]
//
// Needs `playwright` and `axe-core` (npm). Exits 1 if any check fails.
const { chromium } = require('playwright');

const BASE = (process.argv[2] || 'http://localhost:8766').replace(/\/$/, '');
const ROUTES = ['/', '/smokecast', '/world', '/airplan', '/about'];
const SIZES = [
  { name: 'phone 360', viewport: { width: 360, height: 740 }, isMobile: true, hasTouch: true },
  { name: 'laptop 1280', viewport: { width: 1280, height: 800 } },
];

(async () => {
  const browser = await chromium.launch();
  const problems = [];
  for (const size of SIZES) {
    const { name, ...opts } = size;
    // Reduced motion: reveal animations finish at once, so axe sees final colors.
    const ctx = await browser.newContext({ ...opts, reducedMotion: 'reduce' });
    await ctx.route('**/*', r => (r.request().url().startsWith(BASE) ? r.continue() : r.abort()));
    for (const route of ROUTES) {
      const where = `${name} ${route}`;
      const page = await ctx.newPage();
      const errors = [];
      page.on('pageerror', e => errors.push(String(e).slice(0, 200)));
      page.on('response', r => { if (r.url().startsWith(BASE) && r.status() >= 400) errors.push(`${r.status()} ${r.url().slice(BASE.length)}`); });
      await page.goto(`${BASE}/#${route}`, { waitUntil: 'load' });
      await page.waitForTimeout(2000);
      await page.evaluate(() => document.querySelectorAll('[data-reveal]').forEach(el => el.classList.add('is-in')));

      const m = await page.evaluate(() => ({
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
        h1: document.querySelectorAll('h1').length,
      }));
      if (m.overflow > 1) problems.push(`${where}: page scrolls sideways by ${m.overflow}px`);
      if (m.h1 !== 1) problems.push(`${where}: ${m.h1} h1 headings (expected 1)`);
      for (const e of errors) problems.push(`${where}: ${e}`);

      await page.addScriptTag({ path: require.resolve('axe-core') });
      const issues = await page.evaluate(async () => {
        const r = await window.axe.run(document, { resultTypes: ['violations'] });
        return r.violations.filter(v => v.impact === 'serious' || v.impact === 'critical')
          .map(v => `${v.impact} ${v.id} (${v.nodes.length}): ${v.nodes[0].target.join(' ')}`);
      });
      for (const i of issues) problems.push(`${where}: axe ${i}`);
      console.log(`${errors.length || m.overflow > 1 || m.h1 !== 1 || issues.length ? 'FAIL' : 'ok  '} ${where}`);
      await page.close();
    }
    await ctx.close();
  }
  await browser.close();
  if (problems.length) {
    console.log(`\n${problems.length} problem(s):\n` + problems.map(p => '  ' + p).join('\n'));
    process.exit(1);
  }
  console.log('\nAll pages passed.');
})().catch(e => { console.error(e); process.exit(1); });
