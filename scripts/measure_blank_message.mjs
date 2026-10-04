/*
 * The "blank message" measurement set: what a single character does inside a
 * chat bubble, and which characters get past the emptiness check a send button
 * normally implements (refuse the message if value.trim() is empty).
 *
 * Run:  node scripts/measure_blank_message.mjs
 * Out:  data/blank-message.json
 */
import pw from 'file:///C:/Users/Administrator/.workbuddy-ai/binaries/node/workspace/node_modules/playwright/index.js';
import { writeFileSync, mkdirSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = pw;
const HERE = dirname(fileURLToPath(import.meta.url));
const OUT = join(HERE, '..', 'data', 'blank-message.json');

// The 23 characters the site measures: every character commonly handed out for
// a blank name, a blank message or a blank status, plus the two Hangul fillers
// and the tag characters.
const CANDIDATES = [
  ['U+00A0', 0x00A0, 'NO-BREAK SPACE'],
  ['U+00AD', 0x00AD, 'SOFT HYPHEN'],
  ['U+034F', 0x034F, 'COMBINING GRAPHEME JOINER'],
  ['U+061C', 0x061C, 'ARABIC LETTER MARK'],
  ['U+115F', 0x115F, 'HANGUL CHOSEONG FILLER'],
  ['U+1160', 0x1160, 'HANGUL JUNGSEONG FILLER'],
  ['U+180E', 0x180E, 'MONGOLIAN VOWEL SEPARATOR'],
  ['U+200B', 0x200B, 'ZERO WIDTH SPACE'],
  ['U+200C', 0x200C, 'ZERO WIDTH NON-JOINER'],
  ['U+200D', 0x200D, 'ZERO WIDTH JOINER'],
  ['U+200E', 0x200E, 'LEFT-TO-RIGHT MARK'],
  ['U+200F', 0x200F, 'RIGHT-TO-LEFT MARK'],
  ['U+2028', 0x2028, 'LINE SEPARATOR'],
  ['U+2029', 0x2029, 'PARAGRAPH SEPARATOR'],
  ['U+202F', 0x202F, 'NARROW NO-BREAK SPACE'],
  ['U+205F', 0x205F, 'MEDIUM MATHEMATICAL SPACE'],
  ['U+2060', 0x2060, 'WORD JOINER'],
  ['U+3000', 0x3000, 'IDEOGRAPHIC SPACE'],
  ['U+3164', 0x3164, 'HANGUL FILLER'],
  ['U+FEFF', 0xFEFF, 'ZERO WIDTH NO-BREAK SPACE'],
  ['U+FFA0', 0xFFA0, 'HALFWIDTH HANGUL FILLER'],
  ['U+E0001', 0xE0001, 'LANGUAGE TAG'],
  ['U+E0020', 0xE0020, 'TAG SPACE'],
];

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setContent(`<!doctype html><meta charset="utf-8"><style>
  html,body{margin:0;padding:0;background:#fff;color:#111}
  body{font:16px/1.4 system-ui,-apple-system,Segoe UI,sans-serif}
  #row{display:flex;align-items:flex-start}
  #bubble{display:inline-block;max-width:60%;padding:8px 12px;border-radius:16px;
          background:#e8e8ee;word-break:break-word}
  #probe{position:absolute;left:-9999px;top:0;white-space:pre}
  canvas{position:absolute;left:-9999px;top:0}
</style>
<div id="row"><div id="bubble"></div></div>
<span id="probe"></span>
<input id="msg" type="text" placeholder="Type a message">
<canvas id="cv" width="240" height="110"></canvas>`);

const baseline = await page.evaluate(() => {
  const b = document.getElementById('bubble');
  b.textContent = '';
  const empty = b.getBoundingClientRect().height;
  b.textContent = 'M';
  const letter = b.getBoundingClientRect().height;
  b.textContent = ' ';
  const space = b.getBoundingClientRect().height;
  b.textContent = '';
  return { empty_px: +empty.toFixed(2), one_letter_px: +letter.toFixed(2),
           one_space_px: +space.toFixed(2) };
});
console.log('bubble baseline:', JSON.stringify(baseline));

const rows = [];
for (const [label, cp, name] of CANDIDATES) {
  const r = await page.evaluate(({ cp }) => {
    const ch = String.fromCodePoint(cp);

    const p = document.getElementById('probe');
    p.textContent = '||';
    const base = p.getBoundingClientRect().width;
    p.textContent = '|' + ch + '|';
    const advance16 = +(p.getBoundingClientRect().width - base).toFixed(2);

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
    const advance64 = +ctx.measureText(ch).width.toFixed(2);

    const b = document.getElementById('bubble');
    b.textContent = ch;
    const bubbleH = +b.getBoundingClientRect().height.toFixed(2);
    const oneW = +b.getBoundingClientRect().width.toFixed(2);
    b.textContent = ch.repeat(10);
    const tenW = +b.getBoundingClientRect().width.toFixed(2);
    b.textContent = '';

    const i = document.getElementById('msg');
    i.value = ch;
    const trimEmpty = i.value.trim() === '';
    const placeholderShown = i.matches(':placeholder-shown');
    i.required = true;
    const requiredFilled = !i.validity.valueMissing;
    i.required = false;

    const div = document.createElement('div');
    div.textContent = ch;
    const cssEmpty = div.matches(':empty');

    return {
      advance_px_16: advance16,
      advance_px_64: advance64,
      ink_pixels_64px: ink,
      bubble_height_px: bubbleH,
      bubble_width_1_copy_px: oneW,
      bubble_width_10_copies_px: tenW,
      utf16_units: ch.length,
      js_trim_removes: trimEmpty,
      enables_send_under_trim_gate: !trimEmpty,
      placeholder_shown: placeholderShown,
      required_counts_as_filled: requiredFilled,
      matches_css_empty: cssEmpty,
    };
  }, { cp });

  rows.push({ codepoint: label, cp_dec: cp, name, ...r });
  console.log(`${label.padEnd(10)} adv16=${String(r.advance_px_16).padEnd(6)} ink=${String(r.ink_pixels_64px).padEnd(5)} `
    + `bubble=${String(r.bubble_height_px).padEnd(6)} trimGate=${r.enables_send_under_trim_gate ? 'PASS' : 'REFUSED'}`);
}

const pass = rows.filter((r) => r.enables_send_under_trim_gate).length;
console.log(`\npass a trim() emptiness gate: ${pass} of ${rows.length}`);
console.log(`refused                     : ${rows.length - pass} of ${rows.length}`);
console.log(`draw any ink at 64 px       : ${rows.filter((r) => r.ink_pixels_64px > 0).length}`);
console.log(`advance 0 px                : ${rows.filter((r) => r.advance_px_16 === 0).length}`);

mkdirSync(dirname(OUT), { recursive: true });
writeFileSync(OUT, JSON.stringify({
  generated_by: 'scripts/measure_blank_message.mjs',
  source: 'Chromium ' + browser.version() + ' via Playwright; measured on this machine',
  chromium_version: browser.version(),
  bubble_baseline: baseline,
  send_gate_rule: "value.trim() !== '' — the emptiness check a send button normally implements",
  candidates: rows,
}, null, 1));

await browser.close();
console.log('\nwrote', OUT);
