/*
 * Resolve advances that a 16 px measurement cannot.
 *
 * `measure_chromium.mjs` measures at 16 px, where this browser rounds every
 * glyph advance to a whole pixel. That is fine for the zero-versus-visible
 * split, but it cannot tell 0 px from 0.25 px — so the 16 px column reports
 * every sub-pixel advance as 0.
 *
 * The fix is not to repeat the glyph (each copy is rounded on its own, so the
 * error does not average out). It is to measure once at a very large font size
 * and divide: at 4000 px the rounding is +-0.5 px, which is +-0.002 px once
 * scaled back to 16 px.
 *
 * Two controls are measured in the same run so the result is auditable:
 * a capital `A` and an ordinary space. Both are stable across 1000 px and
 * 4000 px, which is what says the scaling is sound.
 *
 * Run:  node scripts/measure_resolved_widths.mjs
 *   ->   data/cf-width-resolved.csv
 */
import pw from 'file:///C:/Users/Administrator/.workbuddy-ai/binaries/node/workspace/node_modules/playwright/index.js';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = pw;
const HERE = dirname(fileURLToPath(import.meta.url));
const ROOT = join(HERE, '..');

const SIZE = 4000;
const SCALE = SIZE / 16;

const facts = JSON.parse(readFileSync(join(ROOT, 'data', 'unicode-facts.json'), 'utf8'));
const CPS = facts.characters.map((c) => c.cp_dec);

const browser = await chromium.launch();
const page = await browser.newPage();
await page.setContent('<!doctype html><meta charset="utf-8"><div id="w"></div>');

const res = await page.evaluate(({ CPS, SIZE }) => {
  const mk = (txt) => {
    const el = document.createElement('span');
    el.style.whiteSpace = 'pre';
    el.style.font = SIZE + 'px system-ui';
    el.textContent = txt;
    document.getElementById('w').appendChild(el);
    const w = el.getBoundingClientRect().width;
    el.remove();
    return w;
  };
  const base = mk('||');
  const out = CPS.map((cp) => [cp, mk('|' + String.fromCodePoint(cp) + '|') - base]);
  return { out, ctrl: { A: mk('|A|') - base, SPACE: mk('| |') - base } };
}, { CPS, SIZE });

console.log('chromium', browser.version(), '| ' + SIZE + 'px | ' + CPS.length + ' Cf characters');
console.log('controls at 16 px equivalent:  A = ' + (res.ctrl.A / SCALE).toFixed(4)
  + '   SPACE = ' + (res.ctrl.SPACE / SCALE).toFixed(4));

const widths = res.out.map(([cp, raw]) => [cp, raw / SCALE]);
const zero = widths.filter(([, v]) => v === 0).length;
const sub = widths.filter(([, v]) => v > 0 && v < 1);
const over = widths.filter(([, v]) => v >= 1).length;
console.log('resolved: exactly 0 = ' + zero + '   sub-pixel = ' + sub.length + '   >= 1 px = ' + over);
for (const [cp, v] of sub) {
  console.log('  sub-pixel: U+' + cp.toString(16).toUpperCase().padStart(4, '0') + ' = ' + v.toFixed(4) + ' px');
}

const hex = (n) => 'U+' + n.toString(16).toUpperCase().padStart(4, '0');
const lines = ['codepoint,advance_px_16_resolved'];
for (const [cp, v] of widths) lines.push(hex(cp) + ',' + v.toFixed(4));
writeFileSync(join(ROOT, 'data', 'cf-width-resolved.csv'), lines.join('\n') + '\n');

await browser.close();
