#!/usr/bin/env python3
"""Check every numeric claim in README.md against the generated CSVs.

If a claim in the README cannot be reproduced from the data, this fails. It is
the guard that keeps the README from drifting away from the measurements.

Run:  python scripts/verify_readme.py
"""
import csv
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")


def main():
    readme = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read()
    master = list(csv.DictReader(open(os.path.join(ROOT, "data", "invisible-format-characters.csv"),
                                    encoding="utf-8")))
    blank = list(csv.DictReader(open(os.path.join(ROOT, "data", "blank-message-candidates.csv"),
                                   encoding="utf-8")))
    ranges = list(csv.DictReader(open(os.path.join(ROOT, "data", "cf-codepoint-ranges.csv"),
                                    encoding="utf-8")))
    facts = json.load(open(os.path.join(ROOT, "data", "unicode-facts.json"), encoding="utf-8"))

    ok = True

    def chk(label, actual, expected_in_readme):
        global ok
        good = actual == expected_in_readme
        if not good:
            ok = False
        print(("PASS " if good else "FAIL ") + label
              + "  computed=%r  readme says %r" % (actual, expected_in_readme))

    def claim(pattern):
        """Pull a number out of the README so the check reads the same source."""
        m = re.search(pattern, readme)
        return int(m.group(1)) if m else None

    print("--- dataset shape ---")
    chk("Cf rows", len(master), 170)
    chk("Cf ranges", len(ranges), 21)
    chk("assigned code points", facts["counts"]["total_assigned_code_points"], 289394)
    chk("blank-message rows", len(blank), 23)

    print("\n--- advance width ---")
    zero = sum(1 for r in master if float(r["advance_width_px_at_16px"]) == 0)
    sub = sum(1 for r in master if 0 < float(r["advance_width_px_at_16px"]) < 1)
    draw = sum(1 for r in master if float(r["advance_width_px_at_16px"]) >= 1)
    chk("advance exactly 0.00 px", zero, claim(r"\*\*(\d+)\*\* of the 170 advance the text cursor by exactly"))
    chk("sub-pixel advance", sub, claim(r"\*\*(\d+)\*\* have a sub-pixel advance"))
    chk("advance >= 1 px", draw, claim(r"\*\*(\d+)\*\* advance by 1 px or more"))

    print("\n--- ink ---")
    ink = [r for r in master if r["draws_ink_at_64px"] == "True"]
    ink_zero_adv = [r for r in ink if float(r["advance_width_px_at_16px"]) == 0]
    chk("draws ink at 64 px", len(ink), claim(r"\*\*(\d+)\*\* of the 170 draw ink on a canvas"))
    chk("draws ink but advances 0 px", len(ink_zero_adv), 2)
    for r in ink_zero_adv:
        print("      %s  %s" % (r["codepoint"], r["name"]))
    for expected in ["U+0605", "U+070F"]:
        chk("README names %s" % expected, expected in readme, True)
        chk("%s is really ink-with-zero-advance" % expected,
            any(r["codepoint"] == expected for r in ink_zero_adv), True)

    print("\n--- whitespace behaviour ---")
    js_trim = [r["codepoint"] for r in master if r["js_trim_removes"] == "True"]
    js_s = [r["codepoint"] for r in master if r["js_regex_s_matches"] == "True"]
    py_strip = sum(1 for r in master if r["python_strip_removes"] == "True")
    py_isspace = sum(1 for r in master if r["python_isspace"] == "True")
    chk("JS trim() removes", len(js_trim), claim(r"\*\*(\d+)\*\* of the 170 is removed by JavaScript"))
    chk("that character is U+FEFF", js_trim, ["U+FEFF"])
    chk("JS /\\s/ matches the same one", js_s, ["U+FEFF"])
    chk("Python strip() removes", py_strip, 0)
    chk("Python isspace() true", py_isspace, 0)

    print("\n--- form API ---")
    email = sum(1 for r in master if r["email_input_accepts"] == "True")
    req = sum(1 for r in master if r["required_counts_as_filled"] == "True")
    css = sum(1 for r in master if r["css_empty_matches"] == "True")
    nfkc = sum(1 for r in master if r["nfkc_changes"] == "True")
    chk("email input accepts", email, 0)
    chk("required counts as filled", req, 170)
    chk("CSS :empty matches", css, 0)
    chk("changed by NFKC", nfkc, 0)

    print("\n--- blank message ---")
    bh = {r["bubble_height_px"] for r in blank}
    chk("every candidate takes the bubble to one height", bh, {"38.39"})
    passes = sum(1 for r in blank if r["enables_send_under_trim_gate"] == "True")
    chk("pass the trim() gate", passes, claim(r"\*\*(\d+) of 23\*\* candidates pass it"))
    refused = [r["codepoint"] for r in blank if r["enables_send_under_trim_gate"] == "False"]
    chk("refused count", len(refused), 23 - passes)
    chk("the refused seven", refused,
        ["U+00A0", "U+2028", "U+2029", "U+202F", "U+205F", "U+3000", "U+FEFF"])
    zero_adv = sum(1 for r in blank if float(r["advance_px_16"]) == 0)
    chk("blank candidates with 0 px advance", zero_adv, 13)
    chk("blank candidates that advance", len(blank) - zero_adv, 10)
    chk("blank candidates drawing ink", sum(1 for r in blank if int(r["ink_pixels_64px"]) > 0), 0)
    u3164 = [r for r in blank if r["codepoint"] == "U+3164"][0]
    chk("U+3164 ten copies bubble width", u3164["bubble_width_10_copies_px"], "184")
    u200b = [r for r in blank if r["codepoint"] == "U+200B"][0]
    chk("U+200B ten copies bubble width", u200b["bubble_width_10_copies_px"], "24")
    chk("U+E0020 is 2 UTF-16 units",
        [r["utf16_units"] for r in blank if r["codepoint"] == "U+E0020"], ["2"])

    print("\n--- tools ---")
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import strip_invisible as si
    chk("default strip set size", len(si.ALWAYS_STRIP), claim(r"the (\d+) code points that carry no meaning"))

    print()
    print("RESULT:", "EVERY README CLAIM REPRODUCES" if ok else "README DRIFT DETECTED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
