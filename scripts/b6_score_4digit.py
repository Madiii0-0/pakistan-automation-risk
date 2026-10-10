"""
B6 - Join 4-digit PSCO employment (B5, 19th ICLS headline) to the ISCO-SOC
crosswalk (PSCO=ISCO identity, confirmed in B2) and Frey-Osborne scores,
compute min/mean/max/SD/range per 4-digit occupation, then produce the
2-digit vs 4-digit range comparison: for each 2-digit category, its
Track A (2-digit) range alongside the employment-weighted mean range
across its 4-digit children, sorted by 2-digit employment descending.
"""
import csv
import statistics as stats
from collections import defaultdict

import pandas as pd

CROSSWALK = "output/isco_soc_crosswalk.csv"
FREY_OSBORNE = "output/frey_osborne_occupations.csv"
EMP_19TH = "output/track_b_employment_19th.csv"
TRACK_A_SCORED = "output/track_a_scored.csv"
NO_OCC_CODE = "NO_OCCUPATION_CODE"

OUT_SCORED = "output/track_b_scored.csv"
OUT_COMPARISON = "output/range_comparison_2digit_vs_4digit.csv"


def load_employment_totals():
    """Return {occ_code: total_employment_millions} across sexes (Total),
    excluding the NO_OCCUPATION_CODE pseudo-row (handled separately)."""
    df = pd.read_csv(EMP_19TH)
    df = df[df["occ_code"] != NO_OCC_CODE]
    totals = df.groupby("occ_code")["weighted_employment_millions"].sum()
    return totals.to_dict()


def main():
    emp_by_code = load_employment_totals()
    total_employed_with_code = sum(emp_by_code.values())
    print(f"[B6] 4-digit codes with employment: {len(emp_by_code)}, "
          f"total = {total_employed_with_code:.3f}M")

    # crosswalk: ISCO code == PSCO code (identity confirmed in B2)
    soc_by_isco = defaultdict(set)
    weak_by_isco = defaultdict(bool)
    with open(CROSSWALK, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            soc_by_isco[row["isco_code"]].add(row["soc_code"])
            if row["is_weak_match"] == "True":
                weak_by_isco[row["isco_code"]] = True

    fo_by_soc = {}
    with open(FREY_OSBORNE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fo_by_soc[row["soc_code"]] = float(row["probability"])

    scored_rows = []
    unmatched_rows = []

    for code, emp in sorted(emp_by_code.items()):
        all_socs = soc_by_isco.get(code, set())
        found_probs = [fo_by_soc[s] for s in all_socs if s in fo_by_soc]
        missing = [s for s in all_socs if s not in fo_by_soc]

        if not found_probs:
            unmatched_rows.append(
                {
                    "track": "B",
                    "occ_code": code,
                    "title": "",  # filled from psco_codes.csv below
                    "reason": (
                        "no crosswalk rows for this 4-digit code"
                        if not all_socs
                        else f"crosswalk matched {len(all_socs)} SOC code(s), none present in Frey-Osborne set"
                    ),
                }
            )
            continue

        scored_rows.append(
            {
                "occ_code": code,
                "employment_millions": round(emp, 4),
                "matched_soc_count": len(found_probs),
                "missing_soc_count": len(missing),
                "min_prob": round(min(found_probs), 4),
                "mean_prob": round(stats.fmean(found_probs), 4),
                "max_prob": round(max(found_probs), 4),
                "sd_prob": round(stats.pstdev(found_probs), 4) if len(found_probs) > 1 else 0.0,
                "range_prob": round(max(found_probs) - min(found_probs), 4),
                "any_weak_match": weak_by_isco.get(code, False),
            }
        )

    # attach titles from PSCO codebook
    titles = {}
    with open("output/psco_codes.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            titles[row["psco_4digit"]] = row["unit_title"]
    for r in scored_rows:
        r["title"] = titles.get(r["occ_code"], "")
    for r in unmatched_rows:
        r["title"] = titles.get(r["occ_code"], "")

    print(f"[B6] Scored 4-digit codes: {len(scored_rows)}")
    print(f"[B6] Unmatched 4-digit codes: {len(unmatched_rows)}")
    unmatched_emp = sum(emp_by_code[r["occ_code"]] for r in unmatched_rows)
    print(f"[B6] Employment in unmatched codes: {unmatched_emp:.4f}M")

    bad_order = [r for r in scored_rows if not (r["min_prob"] <= r["mean_prob"] <= r["max_prob"])]
    assert not bad_order, f"min/mean/max ordering violated in {len(bad_order)} rows"

    with open(OUT_SCORED, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "occ_code", "title", "employment_millions", "matched_soc_count", "missing_soc_count",
                "min_prob", "mean_prob", "max_prob", "sd_prob", "range_prob", "any_weak_match",
            ],
        )
        writer.writeheader()
        writer.writerows(scored_rows)
    print(f"[B6] Wrote {len(scored_rows)} rows to {OUT_SCORED}")

    # append Track B unmatched rows to the shared unmatched_occupations.csv
    with open("output/unmatched_occupations.csv", "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["track", "occ_code", "title", "reason"])
        for r in unmatched_rows:
            writer.writerow({"track": r["track"], "occ_code": r["occ_code"], "title": r["title"], "reason": r["reason"]})
    print(f"[B6] Appended {len(unmatched_rows)} rows to output/unmatched_occupations.csv")
    for r in unmatched_rows:
        print(f"   {r['occ_code']} {r['title']}: emp={emp_by_code[r['occ_code']]:.4f}M -- {r['reason']}")

    # --- 2-digit vs 4-digit range comparison ---
    track_a = {}
    with open(TRACK_A_SCORED, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            track_a[row["isco_2digit"]] = {
                "title": row["title"],
                "range_2digit": float(row["range_prob"]),
                "min_2digit": float(row["min_prob"]),
                "mean_2digit": float(row["mean_prob"]),
                "max_2digit": float(row["max_prob"]),
            }

    children_by_2digit = defaultdict(list)
    for r in scored_rows:
        two = r["occ_code"][:2]
        children_by_2digit[two].append(r)

    comparison_rows = []
    for two, a in track_a.items():
        children = children_by_2digit.get(two, [])
        child_emp_total = sum(c["employment_millions"] for c in children)
        if child_emp_total > 0:
            wmean_range_4digit = sum(c["range_prob"] * c["employment_millions"] for c in children) / child_emp_total
            wmean_min_4digit = sum(c["min_prob"] * c["employment_millions"] for c in children) / child_emp_total
            wmean_max_4digit = sum(c["max_prob"] * c["employment_millions"] for c in children) / child_emp_total
        else:
            wmean_range_4digit = wmean_min_4digit = wmean_max_4digit = None

        comparison_rows.append(
            {
                "isco_2digit": two,
                "title": a["title"],
                "employment_2digit_millions": round(child_emp_total, 4),
                "n_4digit_children_scored": len(children),
                "range_2digit_track_a": a["range_2digit"],
                "wmean_range_4digit_track_b": round(wmean_range_4digit, 4) if wmean_range_4digit is not None else None,
                "change": round(wmean_range_4digit - a["range_2digit"], 4) if wmean_range_4digit is not None else None,
                "min_2digit": a["min_2digit"],
                "wmean_min_4digit": round(wmean_min_4digit, 4) if wmean_min_4digit is not None else None,
                "max_2digit": a["max_2digit"],
                "wmean_max_4digit": round(wmean_max_4digit, 4) if wmean_max_4digit is not None else None,
            }
        )

    comparison_rows.sort(key=lambda r: -r["employment_2digit_millions"])

    with open(OUT_COMPARISON, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "isco_2digit", "title", "employment_2digit_millions", "n_4digit_children_scored",
                "range_2digit_track_a", "wmean_range_4digit_track_b", "change",
                "min_2digit", "wmean_min_4digit", "max_2digit", "wmean_max_4digit",
            ],
        )
        writer.writeheader()
        writer.writerows(comparison_rows)
    print(f"\n[B6] Wrote 2-digit vs 4-digit range comparison to {OUT_COMPARISON}")

    print("\n[B6] === RANGE COMPARISON (sorted by 2-digit employment desc) ===")
    hdr = f"{'code':<4} {'title':<45} {'emp_M':>8} {'n4d':>4} {'2d_range':>9} {'4d_wrange':>10} {'change':>8}"
    print(hdr)
    print("-" * len(hdr))
    for r in comparison_rows:
        wr = r["wmean_range_4digit_track_b"]
        ch = r["change"]
        wr_s = f"{wr:.3f}" if wr is not None else "  n/a"
        ch_s = f"{ch:+.3f}" if ch is not None else "  n/a"
        print(f"{r['isco_2digit']:<4} {r['title'][:45]:<45} {r['employment_2digit_millions']:>8.2f} "
              f"{r['n_4digit_children_scored']:>4} {r['range_2digit_track_a']:>9.3f} {wr_s:>10} {ch_s:>8}")

    print("\n[B6] DONE")


if __name__ == "__main__":
    main()
