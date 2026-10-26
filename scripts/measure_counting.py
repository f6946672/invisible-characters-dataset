# -*- coding: utf-8 -*-
"""Python side of data/character-counting.csv.

For each of the 16 code points used in the counting table, measures the same
string -- five ASCII letters plus the character -- with Python's own rules.

Writes data/counting-py.json. Standard library only. No network.

    python scripts/measure_counting.py
"""
import io, json, os, sys, unicodedata, urllib.parse

CPS = [0x200B, 0x200C, 0x200D, 0x200E, 0x200F,
       0x202A, 0x202C, 0x202D, 0x202E,
       0x2060, 0xFEFF, 0x00AD, 0x034F, 0x3164,
       0xE0001, 0x1D173]

BASE = "golds"
assert len(BASE) == 5, "the base string must be 5 characters"

rows = []
for cp in CPS:
    ch = chr(cp)
    raw = ch.encode("utf-8")
    s = BASE + ch
    nfkc = unicodedata.normalize("NFKC", ch)
    rows.append({
        "codepoint": "U+%04X" % cp,
        "name": unicodedata.name(ch, "UNKNOWN"),
        "category": unicodedata.category(ch),
        "utf8_hex": " ".join("%02X" % b for b in raw),
        "utf8_bytes": len(raw),
        "percent_encoded": urllib.parse.quote(ch, safe=""),
        "percent_encoded_length": len(urllib.parse.quote(ch, safe="")),
        "py_len_of_6_char_string": len(s),
        "py_utf8_bytes_of_6_char_string": len(s.encode("utf-8")),
        "py_len_of_char_alone": len(ch),
        "py_strip_removes_it": s.strip() == BASE,
        "py_isspace": ch.isspace(),
        "py_nfkc": ("U+%04X" % ord(nfkc)) if len(nfkc) == 1 else "EXPANDS",
        "python": sys.version.split()[0],
        "unicode_version": unicodedata.unidata_version,
    })

out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data", "counting-py.json")
with io.open(out, "w", encoding="utf-8", newline="\n") as f:
    json.dump(rows, f, ensure_ascii=False, indent=2)
print("wrote", os.path.normpath(out), "rows:", len(rows))
