#!/usr/bin/env node
/*
 * Find and optionally remove invisible Unicode characters in text.
 * No dependencies — Node's own RegExp and Intl are enough.
 *
 *   node strip_invisible.mjs report.txt            # report only
 *   node strip_invisible.mjs report.txt --strip    # print the cleaned text
 *   node strip_invisible.mjs --in-place report.txt # rewrite the file
 *   cat report.txt | node strip_invisible.mjs      # from stdin
 *
 * Exit codes: 0 = nothing found (or removed), 1 = found and not removed, 2 = usage.
 *
 * This is the JavaScript twin of tools/strip_invisible.py. The two agree on the
 * default set, but they do NOT agree on whitespace: JavaScript's \s matches
 * U+FEFF and Python's does not. That difference is measured in
 * data/invisible-format-characters.csv rather than hidden.
 */
import { readFileSync, writeFileSync } from 'node:fs';

// Codepoints that carry no visible meaning and are safe to remove by default.
const ALWAYS = new Set([
  0x00ad, 0x034f, 0x061c,
  0x115f, 0x1160, 0x17b4, 0x17b5,
  0x180b, 0x180c, 0x180d, 0x180e, 0x180f,
  0x200b, 0x200c, 0x200d, 0x200e, 0x200f,
  0x202a, 0x202b, 0x202c, 0x202d, 0x202e,
  0x2060, 0x2061, 0x2062, 0x2063, 0x2064,
  0x2066, 0x2067, 0x2068, 0x2069,
  0xfeff,
  0xfff9, 0xfffa, 0xfffb,
]);
for (let cp = 0xe0000; cp <= 0xe007f; cp++) ALWAYS.add(cp);   // tag characters
for (let cp = 0xe0100; cp <= 0xe01ef; cp++) ALWAYS.add(cp);   // variation selectors supplement
for (let cp = 0xfe00; cp <= 0xfe0f; cp++) ALWAYS.add(cp);     // variation selectors

const args = process.argv.slice(2);
const flag = (name) => args.includes(name);
const path = args.find((a) => !a.startsWith('--'));

const strip = flag('--strip');
const inPlace = flag('--in-place');
const asJson = flag('--json');
const quiet = flag('--quiet');

if (flag('--list')) {
  const names = new Intl.DisplayNames(['en'], { type: 'unknown' });
  for (const cp of [...ALWAYS].sort((a, b) => a - b)) {
    const ch = String.fromCodePoint(cp);
    process.stdout.write(
      `U+${cp.toString(16).toUpperCase().padStart(4, '0')}  ${ch.length} units  ${JSON.stringify(ch)}\n`);
  }
  process.stderr.write(`\n${ALWAYS.size} codepoints in the default strip set\n`);
  process.exit(0);
}

let text;
if (path) {
  text = readFileSync(path, 'utf8');
} else {
  if (inPlace) { process.stderr.write('--in-place needs a file path\n'); process.exit(2); }
  text = readFileSync(0, 'utf8');
}

const isInvisible = (ch) => ALWAYS.has(ch.codePointAt(0));

if (strip || inPlace) {
  const cleaned = [...text].filter((ch) => !isInvisible(ch)).join('');
  if (inPlace) {
    writeFileSync(path, cleaned, 'utf8');
    if (!quiet) {
      const removed = [...text].length - [...cleaned].length;
      process.stderr.write(`removed ${removed} character(s) from ${path}\n`);
    }
  } else {
    process.stdout.write(cleaned);
  }
  process.exit(0);
}

// scan
const hits = [];
let line = 1;
let col = 0;
for (const ch of text) {
  if (ch === '\n') { line++; col = 0; continue; }
  col++;
  if (isInvisible(ch)) hits.push({ line, column: col, cp: ch.codePointAt(0) });
}

const counts = new Map();
for (const h of hits) counts.set(h.cp, (counts.get(h.cp) || 0) + 1);

const hex = (cp) => 'U+' + cp.toString(16).toUpperCase().padStart(4, '0');

if (asJson) {
  process.stdout.write(JSON.stringify({
    total: hits.length,
    distinct: counts.size,
    by_codepoint: [...counts.entries()]
      .sort((a, b) => b[1] - a[1])
      .map(([cp, n]) => ({ codepoint: hex(cp), count: n, utf16_units: String.fromCodePoint(cp).length })),
    positions: hits.slice(0, 500).map((h) => ({ line: h.line, column: h.column, codepoint: hex(h.cp) })),
  }, null, 1) + '\n');
  process.exit(hits.length ? 1 : 0);
}

if (quiet) process.exit(hits.length ? 1 : 0);

if (!hits.length) {
  process.stdout.write(`no invisible characters found (${[...text].length} characters scanned)\n`);
  process.exit(0);
}

process.stdout.write(
  `${hits.length} invisible character(s), ${counts.size} distinct codepoint(s), in ${[...text].length} characters\n\n`);
process.stdout.write('codepoint  units  n\n');
for (const [cp, n] of [...counts.entries()].sort((a, b) => b[1] - a[1] || a[0] - b[0])) {
  process.stdout.write(`${hex(cp).padEnd(10)} ${String(String.fromCodePoint(cp).length).padEnd(6)} ${n}\n`);
}
process.stdout.write('\nfirst 20 positions (1-based line:column):\n');
for (const h of hits.slice(0, 20)) {
  process.stdout.write(`  ${h.line}:${h.column}  ${hex(h.cp)}\n`);
}
if (hits.length > 20) process.stdout.write(`  ... and ${hits.length - 20} more\n`);
process.stdout.write('\nre-run with --strip to print the cleaned text, or --in-place to rewrite the file.\n');
process.exit(1);
