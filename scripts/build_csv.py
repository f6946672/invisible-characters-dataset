#!/usr/bin/env python3
"""Join the raw measurement JSON into the CSV files people actually cite.

Inputs (produced by the two measure_* scripts):
    data/unicode-facts.json   <- scripts/measure_unicode.py
    data/render-facts.json    <- scripts/measure_chromium.mjs
    data/blank-message.json   <- scripts/measure_blank_message.mjs

Outputs:
    data/invisible-format-characters.csv   one row per Cf character
    data/blank-message-candidates.csv      one row per candidate for a blank message
    data/cf-codepoint-ranges.csv           the contiguous Cf ranges

Run:  python scripts/build_csv.py
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "..", "data")


def load(name):
    with open(os.path.join(DATA, name), encoding="utf-8") as f:
        return json.load(f)


def main():
    facts = load("unicode-facts.json")
    render = load("render-facts.json")
    blank = load("blank-message.json")

    rmap = {r["cp_dec"]: r for r in render["characters"]}

    # ---- master table ----------------------------------------------------
    cols = [
        "codepoint", "char_escaped", "name", "category",
        "utf8_bytes", "utf16_units",
        "advance_width_px_at_16px", "advance_px_at_64px",
        "draws_ink_at_64px", "ink_pixels_at_64px",
        "js_trim_removes", "js_regex_s_matches",
        "python_isspace", "python_strip_removes",
        "nfkc_changes", "nfkc_result",
        "email_input_accepts", "required_counts_as_filled",
        "css_empty_matches", "bubble_height_px",
    ]
    rows = []
    for c in facts["characters"]:
        r = rmap[c["cp_dec"]]
        rows.append({
            "codepoint": c["codepoint"],
            "char_escaped": c["char_escaped"],
            "name": c["name"],
            "category": c["category"],
            "utf8_bytes": c["utf8_bytes"],
            "utf16_units": c["utf16_units"],
            "advance_width_px_at_16px": r["advance16"],
            "advance_px_at_64px": r["advance64"],
            "draws_ink_at_64px": r["ink"] > 0,
            "ink_pixels_at_64px": r["ink"],
            "js_trim_removes": r["js_trim_removes"],
            "js_regex_s_matches": r["js_regex_whitespace"],
            "python_isspace": c["py_isspace"],
            "python_strip_removes": c["py_strip_removes"],
            "nfkc_changes": not c["nfkc_same"],
            "nfkc_result": c["nfkc"],
            "email_input_accepts": r["email_input_accepts"],
            "required_counts_as_filled": r["required_counts_as_filled"],
            "css_empty_matches": r["matches_css_empty"],
            "bubble_height_px": r["bubbleHeight"],
        })

    out = os.path.join(DATA, "invisible-format-characters.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)
    print("wrote %-42s %d rows" % (os.path.basename(out), len(rows)))

    # ---- blank-message candidates ---------------------------------------
    bcols = [
        "codepoint", "name", "advance_px_16", "advance_px_64",
        "ink_pixels_64px", "bubble_height_px",
        "bubble_width_1_copy_px", "bubble_width_10_copies_px",
        "utf16_units", "js_trim_removes", "enables_send_under_trim_gate",
        "placeholder_shown", "required_counts_as_filled", "matches_css_empty",
    ]
    brows = []
    for r in blank["candidates"]:
        brows.append({k: r[k] for k in bcols})
    out = os.path.join(DATA, "blank-message-candidates.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=bcols)
        w.writeheader()
        w.writerows(brows)
    print("wrote %-42s %d rows" % (os.path.basename(out), len(brows)))

    # ---- contiguous Cf ranges -------------------------------------------
    out = os.path.join(DATA, "cf-codepoint-ranges.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["first", "last", "count"])
        w.writeheader()
        w.writerows(facts["cf_ranges"])
    print("wrote %-42s %d rows" % (os.path.basename(out), len(facts["cf_ranges"])))

    # ---- summary --------------------------------------------------------
    print()
    print("summary of the master table (n=%d):" % len(rows))
    print("  advance width exactly 0.00 px :", sum(1 for r in rows if r["advance_width_px_at_16px"] == 0))
    print("  0 < advance < 1 px            :", sum(1 for r in rows
          if 0 < r["advance_width_px_at_16px"] < 1))
    print("  advance >= 1 px               :", sum(1 for r in rows
          if r["advance_width_px_at_16px"] >= 1))
    print("  draws ink at 64 px            :", sum(1 for r in rows if r["draws_ink_at_64px"]))
    print("  JS trim() removes             :", sum(1 for r in rows if r["js_trim_removes"]))
    print("  JS /\\s/ matches               :", sum(1 for r in rows if r["js_regex_s_matches"]))
    print("  Python isspace() true         :", sum(1 for r in rows if r["python_isspace"]))
    print("  email input accepts           :", sum(1 for r in rows if r["email_input_accepts"]))
    print("  required counts as filled     :", sum(1 for r in rows if r["required_counts_as_filled"]))
    print("  CSS :empty matches            :", sum(1 for r in rows if r["css_empty_matches"]))
    print("  changed by NFKC               :", sum(1 for r in rows if r["nfkc_changes"]))


if __name__ == "__main__":
    sys.exit(main())
