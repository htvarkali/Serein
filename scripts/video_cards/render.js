// Render each section of cards.html to docs/video/<id>.png at 1920x1080 (task S-9).
//   node scripts/video_cards/render.js
// Needs `playwright` (npm) and the website fonts (cd website-src && npm ci).
// Captions (ids starting with "caption_") are saved with a transparent background,
// so they can be laid over a screen recording in any editor.
const { chromium } = require('playwright');
const path = require('path');
const fs = require('fs');

const root = path.resolve(__dirname, '..', '..');
const out = path.join(root, 'docs', 'video');

(async () => {
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1920, height: 1080 } });
  await page.goto('file://' + path.join(__dirname, 'cards.html'));
  await page.evaluate(() => document.fonts.ready);
  const ids = await page.$$eval('section[id]', s => s.map(x => x.id));
  for (const id of ids) {
    // Captions: no page background, so the PNG keeps its transparency.
    if (id.startsWith('caption_')) await page.evaluate(() => { document.body.style.background = 'transparent' })
    const el = await page.$('#' + id);
    await el.screenshot({ path: path.join(out, id + '.png'), omitBackground: id.startsWith('caption_') });
    console.log('docs/video/' + id + '.png');
  }
  await browser.close();
})();
