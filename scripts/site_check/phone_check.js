// Phone-size check of the built site: overflow, small text, tap targets, alt text,
// headings, console errors and bytes loaded, on five pages at two phone sizes.
//
//   node scripts/site_check/serve.js website 8766 &
//   node scripts/site_check/phone_check.js [base-url] [--shots]
//
// Needs `playwright` (npm). Prints a summary and writes phone_check.json to the
// current folder. With --shots it also saves one screenshot per page.
const { chromium, devices } = require('playwright');
const fs = require('fs');

const BASE = (process.argv.slice(2).find(a => a.startsWith('http')) || 'http://localhost:8766').replace(/\/$/, '');
const SHOTS = process.argv.includes('--shots');

const routes = ['/', '/smokecast', '/world', '/airplan', '/about'];
const profiles = [
  { name: 'iPhone 13', opts: devices['iPhone 13'] },
  { name: 'small Android 360x740', opts: { viewport: { width: 360, height: 740 }, isMobile: true, hasTouch: true, userAgent: devices['Pixel 5'].userAgent } },
];
const EXTERNAL = /openfreemap|nationalmap|amazonaws|googleapis|gstatic/;

(async () => {
  const browser = await chromium.launch();
  const report = [];
  for (const prof of profiles) {
    for (const route of routes) {
      const ctx = await browser.newContext({ ...prof.opts });
      const page = await ctx.newPage();
      const errs = [], failed = [], sizes = {};
      page.on('console', m => { if (m.type() === 'error') errs.push(m.text().slice(0, 160)); });
      page.on('pageerror', e => errs.push('pageerror: ' + String(e).slice(0, 160)));
      page.on('requestfailed', r => failed.push(r.url()));
      page.on('response', async r => {
        try {
          const u = r.url();
          if (!u.startsWith(BASE)) return;
          const len = Number(r.headers()['content-length'] || 0);
          sizes[u.replace(BASE, '')] = len;
        } catch (e) {}
      });
      const t0 = Date.now();
      await page.goto(BASE + '/#' + route, { waitUntil: 'load' });
      await page.waitForTimeout(3500);
      const loadMs = Date.now() - t0 - 3500;
      const m = await page.evaluate(() => {
        const vw = document.documentElement.clientWidth;
        const vis = el => {
          const r = el.getBoundingClientRect();
          const s = getComputedStyle(el);
          return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none' && Number(s.opacity) > 0.01;
        };
        const label = el => (el.getAttribute('aria-label') || el.innerText || el.getAttribute('title') || el.tagName).trim().replace(/\s+/g, ' ').slice(0, 50);
        // Horizontal overflow
        const scrollW = document.documentElement.scrollWidth;
        const wide = [];
        for (const el of document.querySelectorAll('body *')) {
          if (!vis(el)) continue;
          const r = el.getBoundingClientRect();
          if (r.right > vw + 2 && r.width <= vw * 3) {
            // ignore things inside a horizontally scrolling or clipped ancestor
            let a = el.parentElement, clipped = false;
            while (a && a !== document.body) {
              const o = getComputedStyle(a).overflowX;
              if (o === 'hidden' || o === 'auto' || o === 'scroll' || o === 'clip') { clipped = true; break; }
              a = a.parentElement;
            }
            if (!clipped) wide.push(el.tagName + '.' + String(el.className).slice(0, 40) + ' right=' + Math.round(r.right));
          }
        }
        // Small text
        const small = {};
        const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let n, textNodes = 0;
        while ((n = walker.nextNode())) {
          const t = n.textContent.trim();
          if (!t) continue;
          const el = n.parentElement;
          if (!el || !vis(el)) continue;
          textNodes++;
          const fs = parseFloat(getComputedStyle(el).fontSize);
          if (fs < 12) { const k = fs.toFixed(1) + 'px'; (small[k] = small[k] || []).push(t.slice(0, 40)); }
        }
        // Tap targets
        const targets = [...document.querySelectorAll('a[href], button, [role=button], input, select, textarea, [role=tab], summary')].filter(vis);
        const under44 = [], under24 = [];
        for (const el of targets) {
          const r = el.getBoundingClientRect();
          const inline = getComputedStyle(el).display === 'inline';
          const d = label(el) + ' ' + Math.round(r.width) + 'x' + Math.round(r.height) + (inline ? ' (inline link)' : '');
          if (r.width < 24 || r.height < 24) under24.push(d);
          else if (r.width < 44 || r.height < 44) under44.push(d);
        }
        // Names and alt text
        const noAlt = [...document.querySelectorAll('img')].filter(i => !i.hasAttribute('alt')).map(i => i.src.split('/').pop());
        const emptyAlt = [...document.querySelectorAll('img[alt=""]')].length;
        const unnamed = targets.filter(el => !(el.getAttribute('aria-label') || el.innerText.trim() || el.getAttribute('title') || el.getAttribute('aria-labelledby') || (el.id && document.querySelector('label[for="' + el.id + '"]')) || el.closest('label'))).map(el => el.outerHTML.slice(0, 110));
        const heads = [...document.querySelectorAll('h1,h2,h3,h4,h5,h6')].filter(vis).map(h => h.tagName[1]);
        const h1 = heads.filter(x => x === '1').length;
        let skips = 0; for (let i = 1; i < heads.length; i++) if (heads[i] - heads[i - 1] > 1) skips++;
        const videos = [...document.querySelectorAll('video')].map(v => ({ src: (v.currentSrc || '').split('/').pop(), autoplay: v.autoplay, controls: v.controls, loop: v.loop, paused: v.paused, preload: v.preload }));
        const canvases = document.querySelectorAll('canvas').length;
        return { vw, scrollW, wide: wide.slice(0, 8), small, textNodes, targetCount: targets.length, under44, under24, noAlt, emptyAlt, unnamed, h1, headingSkips: skips, headCount: heads.length,
          videos, canvases, lang: document.documentElement.lang, title: document.title, main: document.querySelectorAll('main').length, skipLink: !!document.querySelector('a[href^="#"][class*="skip"], a.skip-link, a[href="#main"], a[href="#content"]'),
          pageHeight: document.documentElement.scrollHeight };
      });
      const local = Object.entries(sizes);
      const bytes = local.reduce((a, [, v]) => a + v, 0);
      const top = local.sort((a, b) => b[1] - a[1]).slice(0, 6).map(([u, v]) => u + ' ' + Math.round(v / 1024) + ' KB');
      const shot = 'shot_' + prof.name.split(' ')[0].toLowerCase() + '_' + (route === '/' ? 'home' : route.slice(1)) + '.png';
      if (SHOTS) await page.screenshot({ path: shot });
      report.push({ profile: prof.name, route, loadMs, requests: local.length, kb: Math.round(bytes / 1024), top, errs: [...new Set(errs)].filter(e => !EXTERNAL.test(e)).slice(0, 6), extErrs: errs.filter(e => EXTERNAL.test(e)).length, failedLocal: failed.filter(u => !EXTERNAL.test(u)), failedExt: [...new Set(failed.filter(u => EXTERNAL.test(u)).map(u => u.split('/')[2]))], ...m, shot });
      await ctx.close();
    }
  }
  fs.writeFileSync('phone_check.json', JSON.stringify(report, null, 1));
  for (const r of report) {
    console.log(`\n## ${r.profile} ${r.route}  vw=${r.vw} scrollW=${r.scrollW} height=${r.pageHeight} req=${r.requests} ${r.kb}KB`);
    console.log(' overflow:', r.wide.length ? r.wide : 'none');
    console.log(' small text:', Object.fromEntries(Object.entries(r.small).map(([k, v]) => [k, v.length + ' e.g. ' + v.slice(0, 3).join(' | ')])), 'of', r.textNodes);
    console.log(' targets:', r.targetCount, 'under24:', r.under24.length, r.under24.slice(0, 6), 'under44:', r.under44.length, r.under44.slice(0, 8));
    console.log(' noAlt:', r.noAlt, 'emptyAlt:', r.emptyAlt, 'unnamed:', r.unnamed.slice(0, 4));
    console.log(' h1:', r.h1, 'heading skips:', r.headingSkips, '/', r.headCount, 'main:', r.main, 'skip:', r.skipLink, 'lang:', r.lang, 'canvases:', r.canvases);
    console.log(' videos:', JSON.stringify(r.videos));
    console.log(' errors:', r.errs, 'ext err count', r.extErrs, 'failed local:', r.failedLocal, 'ext hosts:', r.failedExt);
    console.log(' top:', r.top);
  }
  await browser.close();
})();
