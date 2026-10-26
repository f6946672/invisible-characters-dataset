// JavaScript side of data/character-counting.csv.
//
// Measures the same string as scripts/measure_counting.py -- five ASCII letters
// plus one character -- with JavaScript's own rules (UTF-16 code units).
//
// Writes data/counting-js.json. Node 18+. No dependencies. No network.
//
//     node scripts/measure_counting.cjs

const fs = require('fs');
const path = require('path');

const CPS = [0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
             0x202A, 0x202C, 0x202D, 0x202E,
             0x2060, 0xFEFF, 0x00AD, 0x034F, 0x3164,
             0xE0001, 0x1D173];

const BASE = 'golds';
if (BASE.length !== 5) throw new Error('the base string must be 5 characters');

const rows = CPS.map((cp) => {
  const ch = String.fromCodePoint(cp);
  const s = BASE + ch;
  return {
    codepoint: 'U+' + cp.toString(16).toUpperCase().padStart(4, '0'),
    js_length_of_6_char_string: s.length,
    js_length_of_char_alone: ch.length,
    js_codepoint_count_of_6_char_string: [...s].length,
    js_trim_removes_it: s.trim() === BASE,
    js_regex_whitespace_removes_it: s.replace(/\s/g, '') === BASE,
    node: process.version,
  };
});

const out = path.join(__dirname, '..', 'data', 'counting-js.json');
fs.writeFileSync(out, JSON.stringify(rows, null, 2) + '\n');
console.log('wrote', out, 'rows:', rows.length);
