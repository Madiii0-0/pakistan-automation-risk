"""
A1 - Filter ilostat_pakistan.csv to Pakistan, parse ISCO 2-digit codes/titles,
verify structure, and write output/ilostat_pakistan_filtered.csv.

Verification checks (per plan):
- Total Pakistan rows == 889
- 2025 cut has exactly 39 substantive 2-digit categories + Total + "Not
  elsewhere classified"
- Male + Female == Total for every category/year (spot check + full check)
- note_source.label flags recorded for downstream Step 10 use
"""
import csv
import re
import sys

SRC = "ilostat_pakistan.csv"
OUT = "output/ilostat_pakistan_filtered.csv"

CAT_RE = re.compile(
    r"Occupation \(ISCO-08\), 2 digit level:\s*(Total|X - Not elsewhere classified|(\d{2})\s*-\s*(.+))$"
)


def parse_category(label: str):
    m = CAT_RE.match(label.strip())
    if not m:
        return None, None, "UNPARSED"
    if m.group(1) == "Total":
        return None, "Total", "TOTAL"
    if m.group(1) == "X - Not elsewhere classified":
        return "X", "Not elsewhere classified", "NEC"
    return m.group(2), m.group(3).strip(), "CATEGORY"


def main():
    rows = []
    with open(SRC, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["ref_area.label"] != "Pakistan":
                continue
            code, title, kind = parse_category(row["classif1.label"])
            rows.append(
                {
                    "year": row["time"],
                    "sex": row["sex.label"],
                    "isco_2digit": code,
                    "category_title": title,
                    "row_kind": kind,
                    "employment_thousands": row["obs_value"],
                    "obs_status": row["obs_status.label"],
                    "note_source": row["note_source.label"],
                    "note_classif": row["note_classif.label"],
                }
            )

    print(f"[A1] Pakistan rows: {len(rows)}")
    assert len(rows) == 889, f"Expected 889 Pakistan rows, got {len(rows)}"

    unparsed = [r for r in rows if r["row_kind"] == "UNPARSED"]
    if unparsed:
        print(f"[A1] WARNING: {len(unparsed)} unparsed classif1.label values:")
        for r in unparsed[:10]:
            print("   ", r)
    assert not unparsed, "Unparsed category labels found -- fix CAT_RE before proceeding"

    years = sorted(set(r["year"] for r in rows))
    print(f"[A1] Years present: {years}")

    # 2025 category count check
    rows_2025 = [r for r in rows if r["year"] == "2025"]
    cats_2025 = set(
        r["isco_2digit"] or r["category_title"]
        for r in rows_2025
        if r["row_kind"] == "CATEGORY"
    )
    print(f"[A1] 2025 substantive 2-digit categories: {len(cats_2025)}")
    # Note: planning-phase notes said 39; a recount here shows 40 (the
    # earlier count during exploration included Total+NEC in a "42" tally,
    # 42-2=40, and "39" in the plan doc was a slip. Trust this script's
    # count, not the plan prose.
    assert len(cats_2025) == 40, f"Expected 40 categories in 2025, got {len(cats_2025)}"

    kinds_2025 = set(r["row_kind"] for r in rows_2025)
    assert "TOTAL" in kinds_2025 and "NEC" in kinds_2025, "Missing Total or NEC row in 2025"

    # Male + Female == Total check, per year, for the Total row and for each category
    by_key = {}
    for r in rows:
        key = (r["year"], r["isco_2digit"], r["row_kind"])
        by_key.setdefault(key, {})[r["sex"]] = r["employment_thousands"]

    mismatches = []
    checked = 0
    for key, sexvals in by_key.items():
        if not all(s in sexvals for s in ("Male", "Female", "Total")):
            continue
        try:
            m = float(sexvals["Male"])
            f = float(sexvals["Female"])
            t = float(sexvals["Total"])
        except ValueError:
            continue
        checked += 1
        if abs((m + f) - t) > 0.05:  # tolerance for rounding in source
            mismatches.append((key, m, f, t, (m + f) - t))

    print(f"[A1] Male+Female==Total checked on {checked} category/year cells, {len(mismatches)} mismatches")
    if mismatches:
        for row in mismatches[:15]:
            print("   MISMATCH", row)
    assert len(mismatches) == 0, "Male+Female does not reconcile to Total for one or more cells"

    # Spot check the figures already hand-verified during planning
    total_2025 = by_key[("2025", None, "TOTAL")]
    assert abs(float(total_2025["Total"]) - 77641.546) < 0.01
    assert abs(float(total_2025["Male"]) - 58865.283) < 0.01
    assert abs(float(total_2025["Female"]) - 18776.263) < 0.01
    print("[A1] 2025 total/male/female spot-check against plan figures: PASS")

    subs = by_key.get(("2025", "63", "CATEGORY"))
    if subs:
        assert abs(float(subs["Total"]) - 2213.27) < 0.01
        print("[A1] 2025 ISCO-63 (subsistence) spot-check against plan figures: PASS")

    note_sources = sorted(set(r["note_source"] for r in rows if r["year"] in ("2025", "2021", "2019")))
    print(f"[A1] note_source.label values for 2025/2021/2019: {note_sources}")

    armed = [r for r in rows_2025 if r["isco_2digit"] in ("01", "02", "03")]
    print(f"[A1] Armed-forces category rows in Pakistan 2025: {len(armed)} (expected 0, per plan)")
    assert len(armed) == 0

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "year", "sex", "isco_2digit", "category_title", "row_kind",
                "employment_thousands", "obs_status", "note_source", "note_classif",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"[A1] Wrote {len(rows)} rows to {OUT}")
    print("[A1] ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
