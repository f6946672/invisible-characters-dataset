# Invisible Unicode characters — measured dataset

What every Unicode **format character** (`Cf`) actually does when a browser
renders it, what the HTML form APIs say about it, and which ones can carry a
blank message or a blank username.

Most lists of "invisible characters" are copied from one another and say the
same three things. This is a measurement: 170 code points put through a real
browser, with the raw output committed and the scripts that produced it.

## Files

| File | Rows | What it is |
|---|---|---|
| `data/invisible-format-characters.csv` | 170 | One row per `Cf` character: advance width, ink, whitespace behaviour, normalisation, form-API verdicts |
| `data/blank-message-candidates.csv` | 23 | What a single character does inside a chat bubble, and whether it gets past a send button's emptiness check |
| `data/cf-width-resolved.csv` | 170 | The same advances re-measured at 4000 px and scaled to 16 px — this is what resolves values below one pixel |
| `data/character-counting.csv` | 16 | One row per character: bytes, percent-encoded length, and what JavaScript and Python each report for the same string |
| `data/cf-codepoint-ranges.csv` | 21 | The contiguous `Cf` ranges, for writing a regex without listing 170 code points |
| `data/unicode-facts.json` | — | Raw Unicode Character Database output (Python `unicodedata`) |
| `data/render-facts.json` | — | Raw browser output (Chromium via Playwright) |
| `data/blank-message.json` | — | Raw chat-bubble output |

## Headline numbers

All of these come from `data/invisible-format-characters.csv`. None of them are
quoted from anywhere else.

- Unicode 15.1 defines **170** characters in category `Cf` (format), in **21**
  contiguous ranges. 289,394 code points are assigned in total.
- **136** of the 170 report an advance of exactly **0.00 px** at a 16 px font,
  and **34** advance by 1 px or more. Read the first figure with care: at 16 px
  this browser rounds every glyph advance to a whole pixel, so the 16 px column
  cannot separate 0 from a quarter of a pixel.
- The rounding is a property of the 16 px measurement, not a blind spot in the
  instrument. Re-measured at **4000 px** and scaled back down — where the
  rounding is 250x smaller, about +-0.002 px — the split is **135 / 1 / 34**:
  exactly one character has a sub-pixel advance, **U+070F SYRIAC ABBREVIATION
  MARK** at **0.25 px**. The characters usually listed as sub-pixel (U+200C,
  U+200F, U+202B, U+202E, U+2067, U+061C) resolve to exactly **0**. Two controls
  measured in the same run, a capital `A` and an ordinary space, are stable
  across 1000 px and 4000 px, which is what says the scaling holds. See
  `data/cf-width-resolved.csv`.
- **36** of the 170 draw ink on a canvas at 64 px — but only 34 of those advance
  by 1 px or more. Two characters (**U+0605 ARABIC NUMBER MARK ABOVE** and
  **U+070F SYRIAC ABBREVIATION MARK**) paint a visible glyph while reporting a
  **0 px** advance at 16 px. They are invisible in the sense that they take no
  space, and visible in the sense that they draw. Resolved, U+0605 is exactly
  0 px and U+070F is the 0.25 px case above.
- **1** of the 170 is removed by JavaScript's `trim()`, and it is the same one
  matched by `/\s/`: **U+FEFF**. **0** of the 170 are removed by Python's
  `strip()`, and **0** return `True` from `str.isspace()`.
- **0** of the 170 are accepted by a Chromium `<input type="email">` in the
  local part of an address.
- **170** of 170 count as *filled in* in a `required` field. An empty string is
  the only thing that fails that check.
- **0** of the 170 change under NFKC.
- **0** of the 170 match CSS `:empty` — that selector tests for text nodes, not
  for whitespace, so it is false as soon as the box contains anything at all.

## A space is not a message

`data/blank-message-candidates.csv` measures the 23 characters usually handed
out for a blank name, a blank status or a blank message.

Measured chat bubble, 16 px font, 8 px vertical padding:

| In the bubble | Height |
|---|---|
| nothing | 16.00 px |
| one ordinary letter | 38.39 px |
| **one ordinary space** | **16.00 px** |
| any of the 23 candidates | 38.39 px |

So a space is stored and then skipped at layout. The second gate is the string
check behind the send button, and the check most send buttons implement is
`value.trim() !== ''`:

- **16 of 23** candidates pass it. **7 of 23** do not, and they are exactly the
  seven JavaScript's `trim()` removes: U+00A0, U+2028, U+2029, U+202F, U+205F,
  U+3000, U+FEFF. An ordinary space fails too.
- **13 of 23** advance the cursor by 0 px. **10** advance without drawing ink,
  including **U+3164 HANGUL FILLER**, which advances a full em — ten copies make
  a bubble 184 px wide, where ten copies of U+200B make a 24 px one.
- **0 of 23** draw any ink in the font stack measured.
- **U+E0020 TAG SPACE** is two UTF-16 units, so a field counting units reports
  20 after you type 10.

## One character, four different numbers

`data/character-counting.csv` counts the same character four ways, in four
layers that do not agree. The measured string is the five-letter word `golds`
with one character appended, so every figure is the total for a six-character
string: a `6` means "five letters plus one character".

| Character | UTF-8 bytes | Percent-encoded | JS `.length` | Python `len()` |
|---|---|---|---|---|
| U+200B | 3 | `%E2%80%8B` | 6 | 6 |
| U+200C | 3 | `%E2%80%8C` | 6 | 6 |
| U+200D | 3 | `%E2%80%8D` | 6 | 6 |
| U+200E | 3 | `%E2%80%8E` | 6 | 6 |
| U+200F | 3 | `%E2%80%8F` | 6 | 6 |
| U+202A | 3 | `%E2%80%AA` | 6 | 6 |
| U+202C | 3 | `%E2%80%AC` | 6 | 6 |
| U+202D | 3 | `%E2%80%AD` | 6 | 6 |
| U+202E | 3 | `%E2%80%AE` | 6 | 6 |
| U+2060 | 3 | `%E2%81%A0` | 6 | 6 |
| U+FEFF | 3 | `%EF%BB%BF` | 6 | 6 |
| U+00AD | 2 | `%C2%AD` | 6 | 6 |
| U+034F | 2 | `%CD%8F` | 6 | 6 |
| U+3164 | 3 | `%E3%85%A4` | 6 | 6 |
| U+E0001 | 4 | `%F3%A0%80%81` | 7 | 6 |
| U+1D173 | 4 | `%F0%9D%85%B3` | 7 | 6 |

Four layers, four rules:

- **UTF-8 counts bytes.** 12 of these sixteen are three bytes, 2 are two
  (U+00AD, U+034F), and 2 are four (U+E0001, U+1D173).
- **Percent-encoding is three characters per byte** — `%XX` — so its length is
  always three times the byte count: 9, 6 or 12. That is measured, not assumed:
  the two columns agree on all sixteen rows.
- **JavaScript `.length` counts UTF-16 code units.** Every character in the BMP
  is one unit, so fourteen rows report 6. The two characters outside the BMP are
  two units each, so they report **7**.
- **Python `len()` counts code points**, so all sixteen report 6.

The consequence is worth stating plainly: count invisible characters by
`.length` and the two astral characters are counted **twice**. Five letters plus
thirty-nine zero-width spaces is 44 by both counters, but it is 122 bytes on the
wire — 5 + 39 x 3. Four different numbers for one string, and none of them is
wrong.

One column nobody asks for. Under NFKC, **U+3164 HANGUL FILLER** becomes
**U+1160**, a different code point, and it is the only row that changes. A pipeline
that normalises before it compares will be looking at a string nobody sent it.

There is deliberately no raw-character column in the CSV. A file holding sixteen
invisible characters corrupts the first time someone opens it in an editor that
strips them, and a dataset about that failure should not be the example of it.
The bytes are given as hex.

## Reproduce it

```bash
python scripts/measure_unicode.py          # Unicode facts  -> data/unicode-facts.json
node   scripts/measure_chromium.mjs        # browser facts  -> data/render-facts.json
node   scripts/measure_blank_message.mjs   # chat bubble    -> data/blank-message.json
python scripts/build_csv.py                # join them      -> the three CSVs
node   scripts/measure_resolved_widths.mjs # 4000 px sweep  -> data/cf-width-resolved.csv
python scripts/measure_counting.py         # Python side    -> data/counting-py.json
node   scripts/measure_counting.cjs        # JS side        -> data/counting-js.json
python scripts/build_counting_csv.py       # join them      -> data/character-counting.csv
```

One caveat about four rows. The advance of the Arabic combining marks
(U+0600, U+0601, U+0603, U+08E2) depends on which fallback font ends up
drawing them, and the two setups disagree by several pixels: the 16 px column
was measured with the probe element positioned off-screen, the resolved column
with the element in flow. Both are reproducible from the committed scripts;
neither is "the" value for those four.

`measure_chromium.mjs` needs Playwright with a Chromium build. The other two
need nothing outside the standard library.

Two more scripts keep the numbers honest:

```bash
node   scripts/check_width_stability.mjs   # 3 font stacks x 4 sizes x 2 DPRs
python scripts/verify_readme.py            # re-checks every number in this file
```

`verify_readme.py` fails if any figure above stops matching the CSVs.

The stability check is why the headline count is quoted **at a 16 px font**: at
16 px, 136 characters advance 0.00 px, and at 32 px and above the count is 135.
One character has a sub-pixel advance that stays under one pixel until the font
is large enough to round it up. Both numbers are correct; the font size is part
of the measurement, so it is stated rather than dropped. No configuration
produced a sub-pixel advance at 16 px, in any of the three font stacks — but see
the caveat above: this browser quantises glyph advances to whole pixels, so a
sub-pixel advance would be indistinguishable from zero in this measurement. What
the stability check establishes is the zero-versus-visible split, which is what
the tables use, and not the shape of any value below one pixel.

## Tools

Two dependency-free command-line tools that find and optionally remove these
characters. They agree byte-for-byte on their output.

```bash
python tools/strip_invisible.py report.txt              # report only
python tools/strip_invisible.py report.txt --strip      # print the cleaned text
python tools/strip_invisible.py report.txt --in-place   # rewrite the file
python tools/strip_invisible.py --include-spaces        # also treat U+00A0 etc.
python tools/strip_invisible.py --json report.txt       # machine-readable
python tools/strip_invisible.py --list                  # every code point it strips

node tools/strip_invisible.mjs report.txt
```

Exit code is `1` when characters are found and left in place, so it drops into a
pre-commit hook or a CI step without any extra wiring.

The default strip set is the 419 code points that carry no meaning a reader can
see. Control characters and non-ASCII spaces are opt-in, because they sometimes
do carry meaning.

## Limits — what this does not tell you

- **These are measurements of one build on one machine.** The browser numbers
  are Chromium 153.0.8010.12 with the font stack named in the script. A device
  with different font coverage can substitute a glyph, which is where a
  "tofu" box comes from; no measurement here predicts which devices do that.
- **Advance width is a property of the character; the box is a property of the
  device.** Only the first one travels with your text.
- **The Unicode numbers depend on the version.** Python 3.13.14 here carries
  Unicode 15.1.0. A later Unicode adds `Cf` code points, which moves every count
  in this file.
- **No application behaviour is measured.** Nothing here says what any
  particular chat app, form or platform accepts today. What is measured is the
  box: the renderer, the string operations, and the HTML constraint API.
- **The blank-message set is 23 characters, not all 170.** It is the set people
  actually hand out for this, not a canonical list.

## Licence

**CC0-1.0** — public domain, no attribution needed. Code and data alike. The
full text is in `LICENSE`.

The measurements were made for
[Strip Invisible](https://stripinvisible.com/), a browser-based tool that
strips these characters from pasted text.
