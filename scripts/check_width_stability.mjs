/*
 * Is the zero-width count stable, or is it an artifact of one font and one size?
 *
 * Re-measures all Cf characters across three font stacks, four font sizes and
 * two device scale factors, and prints how many advance exactly 0.00 px in each
 * configuration. A number that only holds in one configuration is not a fact
 * about the characters, it is a fact about that configuration.
 *
 * Run:  node scripts/check_width_stability.mjs
 */
import pw from 'file:///C:/Users/Administrator/.workbuddy-ai/binaries/node/workspace/node_modules/playwright/index.js';
import { readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const { chromium } = pw;
const HERE = dirname(fileURLToPath(import.meta.url));
const facts = JSON.parse(readFileSync(join(HERE, '..', 'data', 'unicode-facts.json'), 'utf8'));
const CFS = facts.characters.map((c) => c.cp_dec);

const browser = await chromium.launch();
console.log('chromium', browser.version(), '|', CFS.length, 'Cf characters');

for (const dsf of [1, 2]) {
  const page = await browser.newPage({ deviceScaleFactor: dsf });
  await page.setContent('<!doctype html><meta charset="utf-8"><div id="wrap"></div>');
  for (const stack of ['system-ui', 'Arial', 'Times New Roman']) {
    for (const size of [16, 32, 64, 100]) {
      const res = await page.evaluate(({ CFS, size, stack }) => {
        const el = document.createElement('span');
        el.style.whiteSpace = 'pre';
        el.style.font = size + 'px ' + stack;
        document.getElementById('wrap').appendChild(el);
        el.textContent = '||';
        const base = el.getBoundingClientRect().width;
        let zero = 0, sub = 0, draw = 0;
        for (const cp of CFS) {
          el.textContent = '|' + String.fromCodePoint(cp) + '|';
          const w = el.getBoundingClientRect().width - base;
          if (w === 0) zero++; else if (w < 1) sub++; else draw++;
        }
        el.remove();
        return { zero, sub, draw };
      }, { CFS, size, stack });
      console.log(`dsf=${dsf}  ${stack.padEnd(16)} ${String(size).padStart(3)}px  ->  `
        + `0.00 px: ${String(res.zero).padStart(3)}   sub-pixel: ${String(res.sub).padStart(2)}   `
        + `>= 1px: ${String(res.draw).padStart(3)}`);
    }
  }
  await page.close();
}

await browser.close();
