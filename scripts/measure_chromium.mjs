/*
 * Measure what Chromium actually does with every Cf (format) character:
 * advance width, whether it draws any ink, and what the HTML form APIs say.
 *
 * Run:  node scripts/measure_chromium.mjs
 * Out:  data/render-facts.json
 *
 * Playwright lives in the managed workspace and is CommonJS, so it has to be
 * imported by absolute file URL — a bare specifier or NODE_PATH will not work.
 */
import pw from 'file:///C:/Users/Administrator/.workbuddy-ai/binaries/node/workspace/node_modules/playwright/index.js';
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = pw;
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, '..', 'data', 'render-facts.json');

const facts = JSON.parse(readFileSync(join(HERE, '..', 'data', 'unicode-facts.json'), 'utf8'));
const CFS = facts.characters.map((c) => c.cp_dec);

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setContent(`<!doctype html><meta charset="utf-8"><style>
  html,body{margin:0;padding:0;background:#fff;color:#111}
  body{font:16px/1.4 system-ui,-apple-system,Segoe UI,sans-serif}
  #probe{position:absolute;left:-9999px;top:0;white-space:pre}
  #bubble{display:inline-block;max-width:60%;padding:8px 12px;border-radius:16px;
          background:#e8e8ee;word-break:break-word}
</style>
<div id="bubble"></div>
<span id="probe"></span>
<canvas id="cv" width="240" height="110"></canvas>`);

console.log('chromium', browser.version(), '| measuring', CFS.length, 'Cf characters');

const bubbleBase = await page.evaluate(() => {
  const b = document.getElementById('bubble');
  b.textContent = '';
  const empty = b.getBoundingClientRect().height;
  b.textContent = 'M';
  const letter = b.getBoundingClientRect().height;
  b.textContent = ' ';
  const space = b.getBoundingClientRect().height;
  return { empty: +empty.toFixed(2), letter: +letter.toFixed(2), space: +space.toFixed(2) };
});
console.log('bubble: empty', bubbleBase.empty, 'px | one letter', bubbleBase.letter,
            'px | one ordinary space', bubbleBase.space, 'px');

const rows = [];
for (const cp of CFS) {
  const r = await page.evaluate((cp) => {
    const ch = String.fromCodePoint(cp);

    // advance width at the 16 px UI font the site uses
    const p = document.getElementById('probe');
    p.textContent = '||';
    const base = p.getBoundingClientRect().width;
    p.textContent = '|' + ch + '|';
    const advance16 = +(p.getBoundingClientRect().width - base).toFixed(2);

    // ink + advance on a canvas at 64 px
    const cv = document.getElementById('cv');
    const ctx = cv.getContext('2d', { willReadFrequently: true });
    ctx.fillStyle = '#ffffff';
    ctx.fillRect(0, 0, cv.width, cv.height);
    ctx.fillStyle = '#000000';
    ctx.font = '64px sans-serif';
    ctx.textBaseline = 'alphabetic';
    ctx.fillText(ch, 20, 90);
    const d = ctx.getImageData(0, 0, cv.width, cv.height).data;
    let ink = 0;
    for (let i = 0; i < d.length; i += 4) {
      if (d[i] < 250 || d[i + 1] < 250 || d[i + 2] < 250) ink++;
    }
    ctx.font = '64px sans-serif';
    const advance64 = +ctx.measureText(ch).width.toFixed(2);

    // what the chat bubble does with it
    const b = document.getElementById('bubble');
    b.textContent = ch;
    const bubbleH = +b.getBoundingClientRect().height.toFixed(2);
    b.textContent = '';

    // string facts
    const trimRemoves = ch.trim() === '';
    const regexWhitespace = /\s/.test(ch);
    const regexNonSpace = /\S/.test(ch);

    // form gates
    const emailInput = document.createElement('input');
    emailInput.type = 'email';
    emailInput.value = 'user' + ch + 'user@example.com';
    const emailAccepts = emailInput.checkValidity();

    const req = document.createElement('input');
    req.required = true;
    req.value = ch;
    const requiredCountsAsFilled = !req.validity.valueMissing;

    const text = document.createElement('input');
    text.value = ch;
    const placeholderShown = text.matches(':placeholder-shown');

    const div = document.createElement('div');
    div.textContent = ch;
    const matchesEmpty = div.matches(':empty');

    return {
      advance16, advance64, ink,
      bubbleHeight: bubbleH,
      js_trim_removes: trimRemoves,
      js_regex_whitespace: regexWhitespace,
      js_regex_nonspace: regexNonSpace,
      email_input_accepts: emailAccepts,
      required_counts_as_filled: requiredCountsAsFilled,
      placeholder_shown: placeholderShown,
      matches_css_empty: matchesEmpty,
      utf16_units: ch.length,
    };
  }, cp);

  rows.push({ cp_dec: cp, ...r });
  if (rows.length % 25 === 0) console.log('  ...', rows.length);
}

const zero = rows.filter((r) => r.advance16 === 0).length;
const sub = rows.filter((r) => r.advance16 > 0 && r.advance16 < 1).length;
const draws = rows.filter((r) => r.advance16 >= 1).length;
console.log('\nadvance 0.00 px     :', zero);
console.log('sub-pixel 0 < w < 1 :', sub);
console.log('advance >= 1 px     :', draws);
console.log('draws ink at 64 px  :', rows.filter((r) => r.ink > 0).length);
console.log('JS trim() removes   :', rows.filter((r) => r.js_trim_removes).length);
console.log('email field accepts :', rows.filter((r) => r.email_input_accepts).length);
console.log('required = filled   :', rows.filter((r) => r.required_counts_as_filled).length);

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify({
  generated_by: 'scripts/measure_chromium.mjs',
  source: 'Chromium ' + browser.version() + ' via Playwright; measured on this machine',
  chromium_version: browser.version(),
  bubble_baseline: bubbleBase,
  characters: rows,
}, null, 1));

await browser.close();
console.log('\nwrote', OUT);
