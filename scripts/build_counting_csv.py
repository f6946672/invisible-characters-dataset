# -*- coding: utf-8 -*-
"""Join data/counting-py.json + data/counting-js.json into the published CSV.

Nothing in the output is typed by hand: every column is read from one of the two
measurement files, and the script asserts the two runs agree on which code
points were measured, in which order.

    python scripts/measure_counting.py      # -> data/counting-py.json
    node   scripts/measure_counting.cjs     # -> data/counting-js.json
    python scripts/build_counting_csv.py    # -> data/character-counting.csv
"""
import csv, io, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


def load(name):
    with io.open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


py = load("counting-py.json")
js = load("counting-js.json")
py = {r["codepoint"]: r for r in py}
js = {r["codepoint"]: r for r in js}

if list(py) != list(js):
    sys.exit("row order differs between the Python and JavaScript runs: %s vs %s"
             % (list(py), list(js)))

COLS = ["codepoint", "name", "category",
        "utf8_bytes", "utf8_hex",
        "percent_encoded", "percent_encoded_length",
        "js_length", "py_len",
        "js_trim_removes_it", "py_nfkc"]

rows = []
for cp in py:
    p, j = py[cp], js[cp]
    if p["utf8_bytes"] != len(p["utf8_hex"].split()):
        sys.exit("%s: utf8_bytes does not match the hex dump" % cp)
    if p["percent_encoded_length"] != p["utf8_bytes"] * 3:
        sys.exit("%s: percent-encoding is not 3 chars per byte" % cp)
    rows.append({
        "codepoint": cp,
        "name": p["name"],
        "category": p["category"],
        "utf8_bytes": p["utf8_bytes"],
        "utf8_hex": p["utf8_hex"],
        "percent_encoded": p["percent_encoded"],
        "percent_encoded_length": p["percent_encoded_length"],
        "js_length": j["js_length_of_6_char_string"],
        "py_len": p["py_len_of_6_char_string"],
        "js_trim_removes_it": "yes" if j["js_trim_removes_it"] else "no",
        "py_nfkc": p["py_nfkc"],
    })

csv_path = os.path.join(DATA, "character-counting.csv")
with io.open(csv_path, "w", encoding="utf-8", newline="") as f:
    w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
    w.writeheader()
    w.writerows(rows)

json_path = os.path.join(DATA, "character-counting.json")
with io.open(json_path, "w", encoding="utf-8", newline="\n") as f:
    json.dump({
        "measured_string": "golds + one character (5 ASCII letters, 6 characters total)",
        "note": "js_length and py_len are totals for the whole 6-character string, "
                "not for the character on its own. The raw character is deliberately "
                "not stored in the CSV: a file holding 16 invisible characters breaks "
                "the moment it is opened in an editor that strips them.",
        "python": py[list(py)[0]].get("python"),
        "unicode_version": py[list(py)[0]].get("unicode_version"),
        "node": js[list(js)[0]].get("node"),
        "rows": rows,
    }, f, ensure_ascii=False, indent=2)

print("wrote", os.path.normpath(csv_path), "and", os.path.normpath(json_path), "rows:", len(rows))
