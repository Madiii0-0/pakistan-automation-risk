"""
Check 3 - Recompute the scenario (b), 19th ICLS, mean-variant headline
with the 14 BLS-flagged weak-match SOC pairs removed from the crosswalk
before scoring, to test whether the headline is sensitive to including
BLS's own explicitly-flagged low-confidence matches.

3 of the 14 pairs are 9211/9212/9213 -> 45-2099 "Agricultural Workers,
All Other" -- that SOC code was never in the Frey-Osborne 702 set anyway,
so removing it has zero numeric effect on those codes (which are scored
via the separate scenario-b manual assignment to 45-2090, unaffected by
this crosswalk edit).
"""
import csv
import statistics as stats
from collections import defaultdict

CROSSWALK = "output/isco_soc_crosswalk.csv"
FREY_OSBORNE = "output/frey_osborne_occupations.csv"
EMP_19TH = "output/track_b_employment_19th.csv"
MANUAL = {"9211": 0.87, "9212": 0.87, "9213": 0.87}


def load_employment():
    emp_f, emp_m, emp_t = defaultdict(float), defaultdict(float), defaultdict(float)
    with open(EMP_19TH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["occ_code"] == "NO_OCCUPATION_CODE":
                continue
            e = float(row["weighted_employment_millions"])
            emp_t[row["occ_code"]] += e
            if row["sex"] == "Female":
                emp_f[row["occ_code"]] += e
            elif row["sex"] == "Male":
                emp_m[row["occ_code"]] += e
    return emp_f, emp_m, emp_t


def score(exclude_weak):
    soc_by_isco = defaultdict(set)
    weak_pairs = set()
    with open(CROSSWALK, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["is_weak_match"] == "True":
                weak_pairs.add((row["isco_code"], row["soc_code"]))
            if exclude_weak and row["is_weak_match"] == "True":
                continue
            soc_by_isco[row["isco_code"]].add(row["soc_code"])

    fo_by_soc = {}
    with open(FREY_OSBORNE, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fo_by_soc[row["soc_code"]] = float(row["probability"])

    scored = {}
    for code, socs in soc_by_isco.items():
        probs = [fo_by_soc[s] for s in socs if s in fo_by_soc]
        if probs:
            scored[code] = {"min": min(probs), "mean": stats.fmean(probs), "max": max(probs)}
    for code, p in MANUAL.items():
        scored[code] = {"min": p, "mean": p, "max": p}
    return scored, weak_pairs


def hr_share_and_wmean(emp_dict, scored, variant="mean", thr=0.7):
    denom = sum(emp_dict.get(c, 0.0) for c in scored)
    num = sum(emp_dict.get(c, 0.0) for c in scored if scored[c][variant] > thr)
    wsum = sum(emp_dict.get(c, 0.0) * scored[c][variant] for c in scored)
    return (100 * num / denom if denom else None), (wsum / denom if denom else None), denom


def main():
    emp_f, emp_m, emp_t = load_employment()
    scored_with, weak_pairs = score(exclude_weak=False)
    scored_without, _ = score(exclude_weak=True)

    print(f"[check3] {len(weak_pairs)} weak-match pairs in crosswalk")

    affected = []
    for code in scored_with:
        if code in MANUAL:
            continue  # unaffected by crosswalk edit
        before = scored_with[code]
        after = scored_without.get(code)
        if after is None or before != after:
            affected.append((code, before, after))

    print(f"\n[check3] Codes whose scenario-b score changes when weak matches are removed: {len(affected)}")
    total_affected_emp = 0.0
    for code, before, after in affected:
        e = emp_t.get(code, 0.0)
        total_affected_emp += e
        after_str = f"min={after['min']:.3f} mean={after['mean']:.3f} max={after['max']:.3f}" if after else "DROPS TO UNMATCHED"
        print(f"  {code}: emp={e:.4f}M  before(min/mean/max)={before['min']:.3f}/{before['mean']:.3f}/{before['max']:.3f}  after: {after_str}")
    print(f"\n[check3] Total employment affected: {total_affected_emp:.4f}M ({100*total_affected_emp/sum(emp_t.get(c,0.0) for c in scored_with):.3f}% of scenario-b scoreable employment)")

    print("\n[check3] === Headline comparison: WITH vs WITHOUT the 14 weak-match pairs (scenario b, 19th ICLS, mean variant) ===")
    print(f"{'Sex':<8} {'HR% (with)':>12} {'HR% (without)':>14} {'Delta pp':>10} {'WMean (with)':>13} {'WMean (without)':>16} {'Delta':>8}")
    for sexname, d in (("Total", emp_t), ("Male", emp_m), ("Female", emp_f)):
        hr_w, wm_w, denom_w = hr_share_and_wmean(d, scored_with)
        hr_wo, wm_wo, denom_wo = hr_share_and_wmean(d, scored_without)
        print(f"{sexname:<8} {hr_w:>11.3f}% {hr_wo:>13.3f}% {hr_wo-hr_w:>+9.3f} {wm_w:>13.4f} {wm_wo:>16.4f} {wm_wo-wm_w:>+8.4f}")
        print(f"         denom_with={denom_w:.3f}M  denom_without={denom_wo:.3f}M  (diff={denom_wo-denom_w:+.4f}M)")


if __name__ == "__main__":
    main()
