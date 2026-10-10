"""
A4 - Extract the official ILO ISCO-08 structure/definitions file
(isco_structure.xlsx, sheet "ISCO-08 EN Struct and defin") into a clean CSV
at all 4 levels, with verification.

This is the authority used in A5 for rolling 4-digit ISCO codes up to
2-digit, and later (Track B) for the PSCO<->ISCO identity check -- stronger
than relying on the crosswalk's incidental ISCO code list, which has 438
unique codes against this file's official unit-group count (expected 436).
"""
import csv

import openpyxl

SRC = "isco_structure.xlsx"
OUT = "output/isco_structure.csv"
SHEET = "ISCO-08 EN Struct and defin"


def main():
    wb = openpyxl.load_workbook(SRC, read_only=True)
    ws = wb[SHEET]

    rows_iter = ws.iter_rows(values_only=True)
    header = next(rows_iter)
    print(f"[A4] Header row: {header}")
    expected_header = (
        "Level", "ISCO 08 Code", "Title EN", "Definition",
        "Tasks include", "Included occupations", "Excluded occupations", "Notes",
    )
    assert tuple(header) == expected_header, "isco_structure.xlsx header layout has changed"

    rows = []
    for row in rows_iter:
        if row is None or row[0] is None:
            continue
        level, code, title, definition, tasks, included, excluded, notes = row
        rows.append(
            {
                "level": int(level),
                "isco_code": str(code).strip(),
                "title": str(title).strip() if title else "",
                "definition": (definition or "").strip(),
                "tasks_include": (tasks or "").strip(),
                "included_occupations": (included or "").strip(),
                "excluded_occupations": (excluded or "").strip(),
                "notes": (notes or "").strip(),
            }
        )

    print(f"[A4] Total data rows: {len(rows)}")
    assert len(rows) == 619, f"Expected 619 data rows, got {len(rows)}"

    by_level = {}
    for r in rows:
        by_level.setdefault(r["level"], []).append(r)

    for lvl in sorted(by_level):
        print(f"[A4] Level {lvl}: {len(by_level[lvl])} rows")

    # Official ISCO-08 counts: 10 major groups (level 1, incl. Armed Forces
    # major group 0), 43 sub-major (level 2), 130 minor (level 3),
    # 436 unit groups (level 4).
    assert len(by_level.get(1, [])) == 10, f"Expected 10 level-1 rows, got {len(by_level.get(1, []))}"
    assert len(by_level.get(2, [])) == 43, f"Expected 43 level-2 rows, got {len(by_level.get(2, []))}"
    assert len(by_level.get(3, [])) == 130, f"Expected 130 level-3 rows, got {len(by_level.get(3, []))}"
    assert len(by_level.get(4, [])) == 436, f"Expected 436 level-4 (unit group) rows, got {len(by_level.get(4, []))}"

    # Every level-4 code's 1/2/3-digit prefixes should resolve to a defined
    # parent group at the corresponding level.
    codes_by_level = {lvl: {r["isco_code"] for r in rs} for lvl, rs in by_level.items()}
    bad_parents = []
    for r in by_level[4]:
        code = r["isco_code"]
        if len(code) != 4:
            bad_parents.append(("non-4-char code", code))
            continue
        if code[:3] not in codes_by_level[3]:
            bad_parents.append(("missing level-3 parent", code, code[:3]))
        if code[:2] not in codes_by_level[2]:
            bad_parents.append(("missing level-2 parent", code, code[:2]))
        if code[:1] not in codes_by_level[1]:
            bad_parents.append(("missing level-1 parent", code, code[:1]))
    print(f"[A4] Hierarchy resolution issues: {len(bad_parents)}")
    if bad_parents:
        for b in bad_parents[:15]:
            print("   ", b)
    assert not bad_parents, "Some level-4 codes do not resolve to defined parent groups"

    print(f"[A4] Level-4 (unit group) count vs crosswalk's 438 unique ISCO codes:")
    print(f"     official=436, crosswalk=438, diff={438-436} -- flagged for B2 manual review, not resolved here")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "level", "isco_code", "title", "definition",
                "tasks_include", "included_occupations", "excluded_occupations", "notes",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[A4] Wrote {len(rows)} rows to {OUT}")
    print("[A4] ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
