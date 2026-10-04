#!/usr/bin/env python3
"""Find and optionally remove invisible Unicode characters in text.

Standard library only — no dependencies. Reads from a file, from an argument, or
from stdin.

    python strip_invisible.py report.txt              # report only
    python strip_invisible.py report.txt --strip      # print the cleaned text
    python strip_invisible.py --in-place report.txt   # rewrite the file
    cat report.txt | python strip_invisible.py        # from stdin
    python strip_invisible.py --list                  # list every codepoint it knows

Exit codes:  0 = nothing found (or --strip/--in-place used successfully)
             1 = invisible characters found and not removed
             2 = bad usage / unreadable input

Categories covered:
  Cf  format characters        zero-width space, word joiner, BOM, bidi marks,
                               soft hyphen, tag characters, Hangul fillers
  Cc  control characters       (opt-in with --include-control)
  Zs/Zl/Zp  space separators   no-break space, ideographic space, line separator
                               (opt-in with --include-spaces)

The default set is the one that never carries meaning a reader can see. The
opt-in sets are real characters that sometimes do.
"""
from __future__ import annotations

import argparse
import json
import sys
import unicodedata

# Characters that carry no visible meaning in any language and are safe to
# remove by default. This is the set the site's remover strips.
ALWAYS_STRIP = {
    0x00AD,  # SOFT HYPHEN
    0x034F,  # COMBINING GRAPHEME JOINER
    0x061C,  # ARABIC LETTER MARK
    0x115F, 0x1160,  # HANGUL CHOSEONG / JUNGSEONG FILLER
    0x17B4, 0x17B5,  # KHMER VOWEL INHERENT AQ / AA
    0x180B, 0x180C, 0x180D, 0x180E, 0x180F,  # MONGOLIAN FREE VARIATION SELECTORs / VOWEL SEPARATOR
    0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
    0x202A, 0x202B, 0x202C, 0x202D, 0x202E,
    0x2060, 0x2061, 0x2062, 0x2063, 0x2064,
    0x2066, 0x2067, 0x2068, 0x2069,
    0xFE00, 0xFE01, 0xFE02, 0xFE03, 0xFE04, 0xFE05, 0xFE06, 0xFE07, 0xFE08, 0xFE09,
    0xFE0A, 0xFE0B, 0xFE0C, 0xFE0D, 0xFE0E, 0xFE0F,
    0xFEFF,
    0xFFF9, 0xFFFA, 0xFFFB,
}
# every tag character U+E0000..U+E007F
ALWAYS_STRIP |= set(range(0xE0000, 0xE0080))
# variation selectors supplement U+E0100..U+E01EF
ALWAYS_STRIP |= set(range(0xE0100, 0xE01F0))


def is_invisible(ch: str, include_control: bool, include_spaces: bool) -> bool:
    cp = ord(ch)
    if cp in ALWAYS_STRIP:
        return True
    cat = unicodedata.category(ch)
    if cat == "Cf":
        return True
    if include_control and cat == "Cc" and ch not in "\t\n\r":
        return True
    if include_spaces and cat in ("Zs", "Zl", "Zp") and ch != " ":
        return True
    return False


def describe(ch: str) -> dict:
    cp = ord(ch)
    return {
        "codepoint": "U+%04X" % cp,
        "name": unicodedata.name(ch, "<unnamed>"),
        "category": unicodedata.category(ch),
        "utf8_bytes": len(ch.encode("utf-8")),
        "utf16_units": len(ch.encode("utf-16-le")) // 2,
        "escaped": "".join(c if 0x20 <= ord(c) < 0x7F else "\\u%04x" % ord(c) for c in ch),
    }


def scan(text: str, include_control: bool, include_spaces: bool):
    """Yield (index, line, column, char) for every invisible character."""
    line = 1
    col = 0
    for i, ch in enumerate(text):
        if ch == "\n":
            line += 1
            col = 0
            continue
        col += 1
        if is_invisible(ch, include_control, include_spaces):
            yield i, line, col, ch


def main(argv=None) -> int:
    p = argparse.ArgumentParser(
        prog="strip_invisible",
        description="Find and optionally remove invisible Unicode characters.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__.split("Categories covered:")[0].strip(),
    )
    p.add_argument("path", nargs="?", help="file to read; omit to read stdin")
    p.add_argument("--strip", action="store_true",
                   help="print the text with the invisible characters removed")
    p.add_argument("--in-place", action="store_true",
                   help="rewrite the file without the invisible characters")
    p.add_argument("--include-control", action="store_true",
                   help="also treat control characters (Cc) as invisible")
    p.add_argument("--include-spaces", action="store_true",
                   help="also treat non-ASCII spaces (Zs/Zl/Zp) as invisible")
    p.add_argument("--json", action="store_true", help="machine-readable report")
    p.add_argument("--quiet", action="store_true", help="print nothing, only set the exit code")
    p.add_argument("--list", action="store_true", help="list every codepoint in the default set")
    args = p.parse_args(argv)

    if args.list:
        for cp in sorted(ALWAYS_STRIP):
            ch = chr(cp)
            d = describe(ch)
            print("%-9s %-8s %-3s %s" % (d["codepoint"], d["category"], d["utf8_bytes"], d["name"]))
        print("\n%d codepoints in the default strip set" % len(ALWAYS_STRIP), file=sys.stderr)
        return 0

    if args.path:
        try:
            # newline="" disables universal-newline translation. Without it a
            # CRLF file is read back as LF and written out as LF, so the tool
            # would silently rewrite every line ending while reporting only the
            # invisible characters it removed.
            with open(args.path, encoding="utf-8", newline="") as f:
                text = f.read()
        except OSError as e:
            print("cannot read %s: %s" % (args.path, e), file=sys.stderr)
            return 2
    else:
        if args.in_place:
            print("--in-place needs a file path", file=sys.stderr)
            return 2
        text = sys.stdin.read()

    hits = list(scan(text, args.include_control, args.include_spaces))

    # group by codepoint
    counts: dict[int, int] = {}
    for _, _, _, ch in hits:
        counts[ord(ch)] = counts.get(ord(ch), 0) + 1

    if args.strip or args.in_place:
        cleaned = "".join(ch for ch in text
                          if not is_invisible(ch, args.include_control, args.include_spaces))
        if args.in_place:
            try:
                # newline="" here too: writing CRLF text in text mode turns
                # every \n into \r\n, which on an existing CRLF file produces
                # \r\r\n — the file grows while you asked it to shrink.
                with open(args.path, "w", encoding="utf-8", newline="") as f:
                    f.write(cleaned)
            except OSError as e:
                print("cannot write %s: %s" % (args.path, e), file=sys.stderr)
                return 2
            if not args.quiet:
                print("removed %d character(s) from %s" % (len(hits), args.path), file=sys.stderr)
        else:
            # Write bytes straight through: on Windows text mode would turn
            # every \n into \r\n, which silently rewrites the file's line
            # endings while the user asked only for characters to be removed.
            try:
                sys.stdout.reconfigure(newline="")
            except (AttributeError, ValueError):
                pass
            sys.stdout.write(cleaned)
        return 0

    if args.json:
        print(json.dumps({
            "total": len(hits),
            "distinct": len(counts),
            "by_codepoint": [
                {**describe(chr(cp)), "count": n}
                for cp, n in sorted(counts.items(), key=lambda kv: -kv[1])
            ],
            "positions": [
                {"index": i, "line": ln, "column": col, **describe(ch)}
                for i, ln, col, ch in hits[:500]
            ],
        }, ensure_ascii=False, indent=1))
        return 1 if hits else 0

    if args.quiet:
        return 1 if hits else 0

    if not hits:
        print("no invisible characters found (%d characters scanned)" % len(text))
        return 0

    print("%d invisible character(s), %d distinct codepoint(s), in %d characters"
          % (len(hits), len(counts), len(text)))
    print()
    print("%-9s %-4s %-3s %-3s %s" % ("codepoint", "cat", "utf8", "n", "name"))
    for cp, n in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        d = describe(chr(cp))
        print("%-9s %-4s %-3s %-3d %s" % (d["codepoint"], d["category"], d["utf8_bytes"], n, d["name"]))
    print()
    print("first 20 positions (1-based line:column):")
    for i, ln, col, ch in hits[:20]:
        print("  %d:%d  %s  %s" % (ln, col, describe(ch)["codepoint"], describe(ch)["name"]))
    if len(hits) > 20:
        print("  ... and %d more" % (len(hits) - 20))
    print()
    print("re-run with --strip to print the cleaned text, or --in-place to rewrite the file.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
