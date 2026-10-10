"""
A3 - Extract the BLS ISCO-08 <-> 2010 SOC crosswalk (sheet "ISCO-08 to 2010
SOC") into a clean CSV, with verification.

Key facts established during planning, encoded here rather than re-derived:
- The '*' in the 'part' column means "this ISCO code matched more than one
  SOC code" (one-to-many), per BLS's own isco_soc_crosswalk_process.pdf --
  NOT a match-quality flag. Do not filter rows on this.
- BLS's process document separately calls out 14 explicit (SOC, ISCO) pairs
  as genuinely weak matches (its Table 1). That's the real quality flag,
  hardcoded below, used for the sensitivity-test column only.
- SOC codes in the raw file carry trailing spaces (observed directly,
  e.g. '55-1011 ') -- stripped here before they can silently break any
  future join.
"""
import csv

import xlrd

SRC = "crosswalk.xls"
OUT = "output/isco_soc_crosswalk.csv"
HEADER_ROW = 6  # 0-indexed row containing "ISCO-08 Code" etc.

# BLS process doc (Table 1: "Weak matches SOC-ISCO"), (soc_code, isco_code)
WEAK_MATCH_PAIRS = {
    ("13-1131", "4214"),
    ("13-2071", "3312"),
    ("15-1111", "2511"),
    ("19-1012", "2131"),
    ("19-3022", "2120"),
    ("21-1091", "2263"),
    ("39-3021", "9629"),
    ("39-6012", "4224"),
    ("43-2099", "4229"),
    ("45-2099", "9211"),
    ("45-2099", "9212"),
    ("45-2099", "9213"),
    ("49-2097", "7422"),
    ("53-6051", "3257"),
}


def main():
    wb = xlrd.open_workbook(SRC)
    sh = wb.sheet_by_name("ISCO-08 to 2010 SOC")

    header = [sh.cell_value(HEADER_ROW, c) for c in range(sh.ncols)]
    print(f"[A3] Header row: {header}")
    assert header[:6] == [
        "ISCO-08 Code",
        "ISCO-08 Title EN",
        "part",
        "2010 SOC Code",
        "2010 SOC Title",
        "Comment 8/17/11",
    ], "Crosswalk header layout has changed -- update column indices"

    rows = []
    for r in range(HEADER_ROW + 1, sh.nrows):
        isco_code = str(sh.cell_value(r, 0)).strip()
        if not isco_code:
            continue
        isco_title = str(sh.cell_value(r, 1)).strip()
        part_flag = str(sh.cell_value(r, 2)).strip()
        soc_code = str(sh.cell_value(r, 3)).strip()  # strips the trailing-space gotcha
        soc_title = str(sh.cell_value(r, 4)).strip()
        comment = str(sh.cell_value(r, 5)).strip()

        is_one_to_many = part_flag == "*"
        is_weak_match = (soc_code, isco_code) in WEAK_MATCH_PAIRS

        rows.append(
            {
                "isco_code": isco_code,
                "isco_title": isco_title,
                "is_one_to_many": is_one_to_many,
                "soc_code": soc_code,
                "soc_title": soc_title,
                "is_weak_match": is_weak_match,
                "comment": comment,
            }
        )

    print(f"[A3] Total data rows: {len(rows)}")
    assert len(rows) == 1125, f"Expected 1125 rows, got {len(rows)}"

    unique_isco = {r["isco_code"] for r in rows}
    unique_soc = {r["soc_code"] for r in rows}
    print(f"[A3] Unique ISCO-08 codes: {len(unique_isco)}")
    print(f"[A3] Unique SOC codes: {len(unique_soc)}")
    assert len(unique_isco) == 438, f"Expected 438 unique ISCO codes, got {len(unique_isco)}"
    assert len(unique_soc) == 840, f"Expected 840 unique SOC codes, got {len(unique_soc)}"

    n_starred = sum(1 for r in rows if r["is_one_to_many"])
    pct_starred = round(100 * n_starred / len(rows), 1)
    print(f"[A3] one-to-many (asterisk) rows: {n_starred} ({pct_starred}%)")
    assert n_starred == 970, f"Expected 970 starred rows, got {n_starred}"

    n_weak = sum(1 for r in rows if r["is_weak_match"])
    print(f"[A3] weak-match rows flagged: {n_weak} (expect 14, from BLS Table 1)")
    assert n_weak == 14, f"Expected 14 weak-match rows to be findable in the crosswalk, found {n_weak}"

    # Confirm no residual trailing/leading whitespace made it into the
    # cleaned output -- would silently break the Frey-Osborne join later.
    dirty = [r for r in rows if r["soc_code"] != r["soc_code"].strip()]
    assert not dirty, "Trailing/leading whitespace survived cleaning in soc_code"

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "isco_code", "isco_title", "is_one_to_many",
                "soc_code", "soc_title", "is_weak_match", "comment",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[A3] Wrote {len(rows)} rows to {OUT}")
    print("[A3] ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
