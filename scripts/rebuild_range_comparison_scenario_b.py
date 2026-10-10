"""
Rebuilds the 2-digit vs 4-digit range comparison using scenario (b) scoring
(9211/9212/9213 assigned SOC 45-2090, prob=0.87) instead of the original
crosswalk-only scoring used in B6.

Reason this matters: B6's original comparison was built before the
scenario (b) manual assignment existed. Category 92 "Agricultural,
Forestry and Fishery Labourers" has 6 four-digit children; three of them
(9211/9212/9213 = 3.637M of 3.933M total category employment, 92.5%) were
entirely unmatched at B6 time, so the original comparison only reflects
the remaining 0.296M (9214/9215/9216) -- making category 92 look far
smaller and lower-ranked by employment than it actually is. This rebuild
uses the same scenario (b) scores as the final headline analysis, so
figures and headline numbers are drawn from a consistent scoring basis.

Category 63 "Subsistence Farmers, Fishers, Hunters and Gatherers" is
unaffected by this change and remains at zero scored employment: only one
of its four children (6320) appears in the LFS microdata's main-occupation
variable at all (0.0029M, itself unmatched); the other three (6310, 6330,
6340) have zero recorded weighted employment in the entire sample.
"""
import csv
import statistics as stats
from collections import defaultdict

CROSSWALK = "output/isco_soc_crosswalk.csv"
FREY_OSBORNE = "output/frey_osborne_occupations.csv"
EMP_19TH = "output/track_b_employment_19th.csv"
TRACK_A_SCORED = "output/track_a_scored.csv"
NO_OCC_CODE = "NO_OCCUPATION_CODE"

MANUAL_ASSIGN = {"9211": 0.87, "9212": 0.87, "9213": 0.87}

OUT = "output/range_comparison_2digit_vs_4digit_scenario_b.csv"


def main():
    df_emp = defaultdict(float)
    with open(EMP_19TH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["occ_code"] != NO_OCC_CODE:
                df_emp[row["occ_code"]] += float(row["weighted_employment_millions"])

    soc_by_isco = defaultdict(set)
    with open(CROSSWALK, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            soc_by_isco[row["isco_code"]].add(row["soc_code"])

    fo_by_soc = {}
    with open(FREY_OSBORNE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fo_by_soc[row["soc_code"]] = float(row["probability"])

    scored_rows = []
    for code, emp in sorted(df_emp.items()):
        if code in MANUAL_ASSIGN:
            p = MANUAL_ASSIGN[code]
            scored_rows.append({"occ_code": code, "employment_millions": emp,
                                 "min_prob": p, "mean_prob": p, "max_prob": p, "range_prob": 0.0})
            continue
        all_socs = soc_by_isco.get(code, set())
        found_probs = [fo_by_soc[s] for s in all_socs if s in fo_by_soc]
        if not found_probs:
            continue
        scored_rows.append({
            "occ_code": code, "employment_millions": emp,
            "min_prob": min(found_probs), "mean_prob": stats.fmean(found_probs),
            "max_prob": max(found_probs), "range_prob": max(found_probs) - min(found_probs),
        })

    track_a = {}
    with open(TRACK_A_SCORED, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            track_a[row["isco_2digit"]] = {
                "title": row["title"], "range_2digit": float(row["range_prob"]),
                "min_2digit": float(row["min_prob"]), "max_2digit": float(row["max_prob"]),
            }

    children_by_2digit = defaultdict(list)
    for r in scored_rows:
        children_by_2digit[r["occ_code"][:2]].append(r)

    comparison_rows = []
    for two, a in track_a.items():
        children = children_by_2digit.get(two, [])
        child_emp_total = sum(c["employment_millions"] for c in children)
        if child_emp_total > 0:
            wmean_range = sum(c["range_prob"] * c["employment_millions"] for c in children) / child_emp_total
        else:
            wmean_range = None
        comparison_rows.append({
            "isco_2digit": two, "title": a["title"],
            "employment_2digit_millions": round(child_emp_total, 4),
            "n_4digit_children_scored": len(children),
            "range_2digit_track_a": a["range_2digit"],
            "wmean_range_4digit_track_b": round(wmean_range, 4) if wmean_range is not None else None,
            "change": round(wmean_range - a["range_2digit"], 4) if wmean_range is not None else None,
        })

    comparison_rows.sort(key=lambda r: -r["employment_2digit_millions"])
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(comparison_rows[0].keys()))
        writer.writeheader()
        writer.writerows(comparison_rows)
    print(f"Wrote {len(comparison_rows)} rows to {OUT}")
    for r in comparison_rows:
        if r["isco_2digit"] in ("63", "92", "14"):
            print(" ", r)


if __name__ == "__main__":
    main()
