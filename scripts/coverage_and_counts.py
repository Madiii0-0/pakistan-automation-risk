"""
Crosswalk-coverage tables and unweighted respondent counts.

Regenerates the reference tables behind Section 5.5 and Appendix E of the
paper, plus the sample-size diagnostics behind the variance discussion.
These were originally produced ad hoc during analysis; this script exists
so every published output has a script that reproduces it.

Produces:
  ref_match_count_distribution.csv      match-count class for all 345 scored occupations
  ref_single_match_codes.csv            the 138 single-match occupations (Appendix E)
  ref_single_match_codes_with_n.csv     the same, plus unweighted respondent counts
  ref_respondent_counts.csv             unweighted n and PSU count for all scored occupations
  ref_weighted_mean_range_scenario_b.json  employment-weighted mean range, scenario (b)
  unmatched_occupations_ranked.csv      all unmatched codes, both tracks, by employment
  track_a_scored_ranked_by_range.csv    Track A categories sorted by range descending

Requires: b5, b6 (and a2/a3 for the crosswalk), plus the microdata for counts.
"""
import csv
import json
from collections import defaultdict

import pandas as pd

SRC = "microdata/LFS 2024-25.sav web.dta"
MANUAL = {
    "9211": ("Crop farm labourers", 0.87),
    "9212": ("Livestock farm labourers", 0.87),
    "9213": ("Mixed crop and livestock farm labourers", 0.87),
}
GENERIC_MARKERS = ["first-line supervisor", "all other", "not elsewhere classified",
                   "n.e.c", "general and operations manager", "managers, all other"]


def load_employment():
    emp = defaultdict(float)
    with open("output/track_b_employment_19th.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["occ_code"] != "NO_OCCUPATION_CODE":
                emp[row["occ_code"]] += float(row["weighted_employment_millions"])
    return emp


def respondent_counts():
    """Unweighted respondents and distinct PSUs per 4-digit occupation, 19th ICLS."""
    df = pd.read_stata(SRC, convert_categoricals=False,
                       columns=["EBCode", "Weights", "S5C1", "S5C2", "S5C3", "S5C4",
                                "S5C10", "S5C12"])
    own = df["S5C10"].isin([3.0, 4.0])
    e19 = ((df["S5C1"] == 1) | (df["S5C2"] == 1) | (df["S5C3"] == 1) |
           (df["S5C4"] == 1) | own) & ~own
    sub = df[e19].copy()
    sub["occ"] = sub["S5C12"].apply(lambda v: None if pd.isna(v) else str(int(v)))
    g = sub.groupby("occ").agg(n=("Weights", "size"), npsu=("EBCode", "nunique"))
    return {c: (int(r.n), int(r.npsu)) for c, r in g.iterrows()}


def main():
    emp = load_employment()
    counts = respondent_counts()

    scored = {r["occ_code"]: r for r in
              csv.DictReader(open("output/track_b_scored.csv", encoding="utf-8"))}

    soc_by_isco = defaultdict(list)
    with open("output/isco_soc_crosswalk.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            soc_by_isco[row["isco_code"]].append(row["soc_code"])
    fo_titles = {}
    with open("output/frey_osborne_occupations.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fo_titles[row["soc_code"]] = row["title"]

    # ---- all scored occupations: match-count class, employment, counts ----
    all_rows = []
    for code, r in scored.items():
        n, npsu = counts.get(code, (0, 0))
        all_rows.append({
            "occ_code": code, "title": r["title"],
            "matched_soc_count": int(r["matched_soc_count"]),
            "employment_millions": round(emp.get(code, 0.0), 4),
            "mean_prob": float(r["mean_prob"]),
            "n_unweighted": n, "n_psu": npsu,
            "below_30": "YES" if n < 30 else "",
            "manually_assigned": False,
        })
    for code, (title, p) in MANUAL.items():
        n, npsu = counts.get(code, (0, 0))
        all_rows.append({
            "occ_code": code, "title": title, "matched_soc_count": 0,
            "employment_millions": round(emp.get(code, 0.0), 4), "mean_prob": p,
            "n_unweighted": n, "n_psu": npsu,
            "below_30": "YES" if n < 30 else "", "manually_assigned": True,
        })
    all_rows.sort(key=lambda r: -r["employment_millions"])

    write(all_rows, "output/ref_match_count_distribution.csv",
          ["occ_code", "title", "matched_soc_count", "employment_millions",
           "mean_prob", "manually_assigned"])
    write(all_rows, "output/ref_respondent_counts.csv",
          ["occ_code", "title", "employment_millions", "mean_prob",
           "matched_soc_count", "n_unweighted", "n_psu", "below_30"])

    # ---- single-match occupations (Appendix E) ----
    single = []
    for r in all_rows:
        if r["manually_assigned"] or r["matched_soc_count"] != 1:
            continue
        code = r["occ_code"]
        in_fo = [s for s in soc_by_isco.get(code, []) if s in fo_titles]
        soc = in_fo[0] if in_fo else "?"
        title = fo_titles.get(soc, "?")
        single.append({
            "occ_code": code, "title": r["title"],
            "employment_millions": r["employment_millions"],
            "mean_prob": r["mean_prob"], "matched_soc": soc,
            "matched_soc_title": title,
            "flagged_generic": any(m in title.lower() for m in GENERIC_MARKERS),
            "n_unweighted": r["n_unweighted"], "n_psu": r["n_psu"],
            "below_30": r["below_30"],
        })
    single.sort(key=lambda r: -r["employment_millions"])
    write(single, "output/ref_single_match_codes.csv",
          ["occ_code", "title", "employment_millions", "mean_prob",
           "matched_soc", "matched_soc_title", "flagged_generic"])
    write(single, "output/ref_single_match_codes_with_n.csv",
          ["occ_code", "title", "employment_millions", "mean_prob", "matched_soc",
           "matched_soc_title", "flagged_generic", "n_unweighted", "n_psu", "below_30"])

    # ---- employment-weighted mean range, scenario (b) ----
    wsum = esum = 0.0
    n_codes = 0
    for code, r in scored.items():
        e = emp.get(code, 0.0)
        wsum += e * float(r["range_prob"])
        esum += e
        n_codes += 1
    for code in MANUAL:                       # point estimates contribute zero range
        esum += emp.get(code, 0.0)
        n_codes += 1
    with open("output/ref_weighted_mean_range_scenario_b.json", "w", encoding="utf-8") as f:
        json.dump({"n_scored_codes_scenario_b": n_codes,
                   "total_employment_M": round(esum, 4),
                   "employment_weighted_mean_range": round(wsum / esum, 4)}, f, indent=2)

    # ---- unmatched codes, both tracks, ranked ----
    unmatched = list(csv.DictReader(open("output/unmatched_occupations.csv", encoding="utf-8")))
    for r in unmatched:
        r["employment_millions"] = round(emp.get(r["occ_code"], 0.0), 4)
    unmatched.sort(key=lambda r: -r["employment_millions"])
    write(unmatched, "output/unmatched_occupations_ranked.csv",
          ["track", "occ_code", "title", "employment_millions", "reason"])

    # ---- Track A categories by range descending, with ILOSTAT employment ----
    ilo = {}
    with open("output/ilostat_pakistan_filtered.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["year"] == "2025" and row["sex"] == "Total" and row["row_kind"] == "CATEGORY":
                ilo[row["isco_2digit"]] = row["employment_thousands"]
    track_a = []
    with open("output/track_a_scored.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            track_a.append({
                "code": row["isco_2digit"], "title": row["title"],
                "employment_2025_total_K": ilo.get(row["isco_2digit"], ""),
                "min": row["min_prob"], "mean": row["mean_prob"], "max": row["max_prob"],
                "range": row["range_prob"], "sd": row["sd_prob"],
                "n_soc": row["matched_soc_count"],
            })
    track_a.sort(key=lambda r: -float(r["range"]))
    write(track_a, "output/track_a_scored_ranked_by_range.csv",
          ["code", "title", "employment_2025_total_K", "min", "mean", "max",
           "range", "sd", "n_soc"])

    below = [r for r in all_rows if r["n_unweighted"] < 30]
    print(f"[coverage] scored occupations: {len(all_rows)}")
    print(f"[coverage] single-match: {len(single)}  "
          f"({sum(1 for r in single if r['flagged_generic'])} generic)")
    print(f"[coverage] with fewer than 30 respondents: {len(below)} occupations, "
          f"{sum(r['employment_millions'] for r in below):.4f}M employment "
          f"({100*sum(r['employment_millions'] for r in below)/esum:.2f}% of scored)")
    print("[coverage] wrote 7 reference tables to output/")


def write(rows, path, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
