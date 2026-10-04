#!/usr/bin/env python3
"""Generate the Unicode-side facts for every Cf (format) character.

Everything here comes from Python's own unicodedata module, which is the
authoritative Unicode Character Database shipped with the interpreter. No
value in the output is typed by hand or estimated.

Run:  python scripts/measure_unicode.py
Out:  data/unicode-facts.json
"""
import json
import os
import sys
import unicodedata

OUT = os.path.join(os.path.dirname(__file__), "..", "data", "unicode-facts.json")

def esc(s):
    """ASCII-safe rendering of a string: every non-ASCII code point as \\uXXXX."""
    out = []
    for ch in s:
        cp = ord(ch)
        if 0x20 <= cp < 0x7F:
            out.append(ch)
        elif cp <= 0xFFFF:
            out.append("\\u%04x" % cp)
        else:
            out.append("\\U%08x" % cp)
    return "".join(out)

def main():
    version = unicodedata.unidata_version
    rows = []
    category_counts = {}
    assigned = 0

    for cp in range(0x110000):
        ch = chr(cp)
        cat = unicodedata.category(ch)
        category_counts[cat] = category_counts.get(cat, 0) + 1
        if cat != "Cn":
            assigned += 1
        if cat != "Cf":
            continue

        name = unicodedata.name(ch, "")
        nfc = unicodedata.normalize("NFC", ch)
        nfd = unicodedata.normalize("NFD", ch)
        nfkc = unicodedata.normalize("NFKC", ch)
        nfkd = unicodedata.normalize("NFKD", ch)

        def cps(s):
            return " ".join("U+%04X" % ord(c) for c in s)

        rows.append({
            "codepoint": "U+%04X" % cp,
            "cp_dec": cp,
            "char_escaped": esc(ch),
            "name": name,
            "category": cat,
            "utf8_bytes": len(ch.encode("utf-8")),
            "utf16_units": len(ch.encode("utf-16-le")) // 2,
            "py_isspace": ch.isspace(),
            "py_strip_removes": ch.strip() == "",
            "nfc": cps(nfc), "nfc_same": nfc == ch,
            "nfd": cps(nfd), "nfd_same": nfd == ch,
            "nfkc": cps(nfkc), "nfkc_same": nfkc == ch,
            "nfkd": cps(nfkd), "nfkd_same": nfkd == ch,
            "py_isprintable": ch.isprintable(),
        })

    # group the Cf code points into contiguous ranges, which is how the
    # Unicode standard itself describes them
    ranges = []
    start = prev = None
    for r in rows:
        cp = r["cp_dec"]
        if start is None:
            start = prev = cp
        elif cp == prev + 1:
            prev = cp
        else:
            ranges.append((start, prev))
            start = prev = cp
    if start is not None:
        ranges.append((start, prev))

    data = {
        "generated_by": "scripts/measure_unicode.py",
        "source": "Python unicodedata module (Unicode Character Database shipped with CPython)",
        "python_version": sys.version.split()[0],
        "unicodedata_version": version,
        "counts": {
            "total_assigned_code_points": assigned,
            "Cf_format_characters": len(rows),
            "Cc_control": category_counts.get("Cc", 0),
            "Zs_space_separator": category_counts.get("Zs", 0),
            "Zl_line_separator": category_counts.get("Zl", 0),
            "Zp_paragraph_separator": category_counts.get("Zp", 0),
            "Mn_nonspacing_mark": category_counts.get("Mn", 0),
            "Cn_unassigned": category_counts.get("Cn", 0),
        },
        "cf_ranges": [
            {"first": "U+%04X" % a, "last": "U+%04X" % b, "count": b - a + 1}
            for a, b in ranges
        ],
        "characters": rows,
    }

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    print("unicodedata", version, "| python", sys.version.split()[0])
    print("Cf format characters:", len(rows), "in", len(ranges), "ranges")
    print("assigned code points :", assigned)
    print("Cf that Python strip() removes:", sum(1 for r in rows if r["py_strip_removes"]))
    print("Cf changed by NFKC          :", sum(1 for r in rows if not r["nfkc_same"]))
    print("wrote", os.path.normpath(OUT))

if __name__ == "__main__":
    main()
