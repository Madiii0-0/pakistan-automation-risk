"""
A5 - Roll the ISCO->SOC crosswalk up to 2-digit (sub-major group) level,
join to Frey-Osborne probabilities, and compute min/mean/max/SD/range per
2-digit ISCO category.

Rollup rule (per plan, explicitly called out as a "what could go wrong"
item): a 2-digit category inherits the UNION of SOC codes matched to ANY
of its constituent 4-digit codes, not an average or an arbitrary pick.

Unmatched-SOC handling: Frey-Osborne's 702-occupation set excludes ~3% of
US employment ("all other" catch-all SOC titles with no O*NET data). Some
crosswalk SOC codes may fall in that excluded set. Those are dropped from
the matched pool per 2-digit code (with a count kept for transparency),
not silently ignored.

2-digit categories with zero resolvable SOC matches go to
output/unmatched_occupations.csv for manual review, exactly like Track B's
unmatched-occupation handling, just at coarser granularity.
"""
import csv
import statistics as stats
from collections import defaultdict

CROSSWALK = "output/isco_soc_crosswalk.csv"
FREY_OSBORNE = "output/frey_osborne_occupations.csv"
ISCO_STRUCTURE = "output/isco_structure.csv"
OUT_SCORED = "output/track_a_scored.csv"
OUT_UNMATCHED = "output/unmatched_occupations.csv"


def truncate_to_level(code: str, n: int) -> str:
    """Shared rollup helper -- truncates an ISCO/PSCO code's numeric prefix
    to n digits. Used identically by Track A (here, n=2) and Track B
    (n=4, or coarser fallback levels) so granularity is one parameter."""
    return code[:n]


def main():
    # --- load crosswalk ---
    crosswalk_rows = []
    with open(CROSSWALK, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            row["is_one_to_many"] = row["is_one_to_many"] == "True"
            row["is_weak_match"] = row["is_weak_match"] == "True"
            crosswalk_rows.append(row)
    print(f"[A5] Loaded {len(crosswalk_rows)} crosswalk rows")

    # --- load Frey-Osborne scores ---
    fo_by_soc = {}
    with open(FREY_OSBORNE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fo_by_soc[row["soc_code"]] = float(row["probability"])
    print(f"[A5] Loaded {len(fo_by_soc)} Frey-Osborne SOC scores")

    # --- load official 2-digit ISCO categories (so we enumerate every
    # category, including ones the crosswalk happens to miss entirely) ---
    isco_2digit_titles = {}
    with open(ISCO_STRUCTURE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["level"] == "2":
                isco_2digit_titles[row["isco_code"]] = row["title"]
    print(f"[A5] Loaded {len(isco_2digit_titles)} official 2-digit ISCO categories")

    # --- roll crosswalk up to 2-digit: union of SOC matches per 2-digit code ---
    soc_by_2digit = defaultdict(set)
    weak_by_2digit = defaultdict(bool)
    one_to_many_by_2digit = defaultdict(bool)
    for r in crosswalk_rows:
        two = truncate_to_level(r["isco_code"], 2)
        soc_by_2digit[two].add(r["soc_code"])
        if r["is_weak_match"]:
            weak_by_2digit[two] = True
        if r["is_one_to_many"]:
            one_to_many_by_2digit[two] = True

    scored_rows = []
    unmatched_rows = []
    total_missing_from_fo = 0

    for code, title in sorted(isco_2digit_titles.items()):
        all_socs = soc_by_2digit.get(code, set())
        found_probs = []
        missing_socs = []
        for soc in sorted(all_socs):
            if soc in fo_by_soc:
                found_probs.append(fo_by_soc[soc])
            else:
                missing_socs.append(soc)
        total_missing_from_fo += len(missing_socs)

        if not found_probs:
            unmatched_rows.append(
                {
                    "track": "A",
                    "occ_code": code,
                    "title": title,
                    "reason": (
                        "no crosswalk rows for this 2-digit prefix"
                        if not all_socs
                        else f"crosswalk matched {len(all_socs)} SOC code(s), "
                        f"none present in Frey-Osborne's 702-occupation set"
                    ),
                }
            )
            continue

        scored_rows.append(
            {
                "isco_2digit": code,
                "title": title,
                "matched_soc_count": len(found_probs),
                "missing_soc_count": len(missing_socs),
                "min_prob": round(min(found_probs), 4),
                "mean_prob": round(stats.fmean(found_probs), 4),
                "max_prob": round(max(found_probs), 4),
                "sd_prob": round(stats.pstdev(found_probs), 4) if len(found_probs) > 1 else 0.0,
                "range_prob": round(max(found_probs) - min(found_probs), 4),
                "any_weak_match": weak_by_2digit.get(code, False),
                "any_one_to_many": one_to_many_by_2digit.get(code, False),
            }
        )

    print(f"[A5] Scored 2-digit categories: {len(scored_rows)}")
    print(f"[A5] Unmatched 2-digit categories: {len(unmatched_rows)}")
    print(f"[A5] Total SOC matches dropped for having no Frey-Osborne score: {total_missing_from_fo}")

    assert len(scored_rows) + len(unmatched_rows) == len(isco_2digit_titles), (
        "Scored + unmatched should account for every official 2-digit category"
    )

    # sanity: every scored category should have min <= mean <= max
    bad_order = [r for r in scored_rows if not (r["min_prob"] <= r["mean_prob"] <= r["max_prob"])]
    assert not bad_order, f"min/mean/max ordering violated in {len(bad_order)} rows"

    # High-variance categories are exactly the ones the mandatory SD/range
    # diagnostic exists to surface -- print the worst offenders now so
    # they're visible before anything downstream trusts the mean.
    worst_spread = sorted(scored_rows, key=lambda r: -r["range_prob"])[:5]
    print("[A5] Widest min-max spread (top 5, informational -- flags where the")
    print("     2-digit aggregate is hiding the most within-category variance):")
    for r in worst_spread:
        print(
            f"   {r['isco_2digit']} {r['title'][:50]:<50} "
            f"n={r['matched_soc_count']:>3} min={r['min_prob']:.3f} "
            f"mean={r['mean_prob']:.3f} max={r['max_prob']:.3f} range={r['range_prob']:.3f}"
        )

    with open(OUT_SCORED, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "isco_2digit", "title", "matched_soc_count", "missing_soc_count",
                "min_prob", "mean_prob", "max_prob", "sd_prob", "range_prob",
                "any_weak_match", "any_one_to_many",
            ],
        )
        writer.writeheader()
        writer.writerows(scored_rows)
    print(f"[A5] Wrote {len(scored_rows)} rows to {OUT_SCORED}")

    with open(OUT_UNMATCHED, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["track", "occ_code", "title", "reason"])
        writer.writeheader()
        writer.writerows(unmatched_rows)
    print(f"[A5] Wrote {len(unmatched_rows)} rows to {OUT_UNMATCHED}")
    if unmatched_rows:
        print("[A5] Unmatched 2-digit categories (review these -- Track A cannot score them):")
        for r in unmatched_rows:
            print(f"   {r['occ_code']} {r['title']}: {r['reason']}")

    print("[A5] DONE")


if __name__ == "__main__":
    main()
