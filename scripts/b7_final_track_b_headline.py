"""
B7 - Final Track B headline statistics.

Headline = scenario (b): 9211/9212/9213 assigned the primary candidate
score (SOC 45-2090 "Miscellaneous agricultural workers", prob=0.87) as a
point estimate. Scenario (a) -- unmatched excluded entirely -- is carried
as an explicit sensitivity comparison, not silently dropped.

The other 25 unmatched 4-digit codes are documented as an explicit
appendix exclusion (code, title, employment, share of total employed),
not folded into any headline number.

Computed under BOTH 19th and 13th ICLS employment, by sex, for
min/mean/max variants: high-risk share (>0.7), band distribution
(>0.7 / 0.3-0.7 / <0.3), employment-weighted mean probability (reported
alone, never set against the US 47% figure -- different country, different
labour-market structure, not a like-for-like benchmark), top 20 by score,
top 20 by absolute workers in high-risk occupations.
"""
import csv
import json
from collections import defaultdict

SCORED = "output/track_b_scored.csv"
EMP_19TH = "output/track_b_employment_19th.csv"
EMP_13TH = "output/track_b_employment_13th.csv"
NO_OCC_CODE = "NO_OCCUPATION_CODE"

MANUAL_ASSIGN = {"9211": 0.87, "9212": 0.87, "9213": 0.87}
MANUAL_TITLES = {
    "9211": "Crop farm labourers",
    "9212": "Livestock farm labourers",
    "9213": "Mixed crop and livestock farm labourers",
}


def load_scored(assign_manual):
    scored = {}
    titles = {}
    with open(SCORED, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            scored[row["occ_code"]] = {
                "min_prob": float(row["min_prob"]),
                "mean_prob": float(row["mean_prob"]),
                "max_prob": float(row["max_prob"]),
            }
            titles[row["occ_code"]] = row["title"]
    if assign_manual:
        for code, p in MANUAL_ASSIGN.items():
            scored[code] = {"min_prob": p, "mean_prob": p, "max_prob": p}
            titles[code] = MANUAL_TITLES[code]
    return scored, titles


def load_employment(path):
    by_sex = defaultdict(dict)
    total_by_sex = defaultdict(float)
    with open(path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sex = row["sex"]
            emp = float(row["weighted_employment_millions"])
            total_by_sex[sex] += emp
            if row["occ_code"] != NO_OCC_CODE:
                by_sex[sex][row["occ_code"]] = by_sex[sex].get(row["occ_code"], 0.0) + emp
    return by_sex, total_by_sex


def band(prob):
    if prob > 0.7:
        return "high"
    if prob >= 0.3:
        return "medium"
    return "low"


def combine_total(emp_by_sex):
    total = defaultdict(float)
    for sex in ("Male", "Female"):
        for code, emp in emp_by_sex[sex].items():
            total[code] += emp
    return total


def compute_stats(scored, emp_by_sex, total_by_sex):
    out = {}
    categories_total = combine_total(emp_by_sex)
    total_all = total_by_sex["Male"] + total_by_sex["Female"]
    groups = {"Male": emp_by_sex["Male"], "Female": emp_by_sex["Female"], "Total": categories_total}
    grand_totals = {"Male": total_by_sex["Male"], "Female": total_by_sex["Female"], "Total": total_all}

    for sex, categories in groups.items():
        matched_employment = sum(v for k, v in categories.items() if k in scored)
        unscoreable = grand_totals[sex] - matched_employment
        for variant in ("min_prob", "mean_prob", "max_prob"):
            band_emp = {"high": 0.0, "medium": 0.0, "low": 0.0}
            wsum = 0.0
            for code, emp in categories.items():
                if code not in scored:
                    continue
                p = scored[code][variant]
                band_emp[band(p)] += emp
                wsum += emp * p
            wmean = wsum / matched_employment if matched_employment else None
            out[f"{sex}|{variant}"] = {
                "scoreable_M": round(matched_employment, 3),
                "unscoreable_M": round(unscoreable, 3),
                "unscoreable_pct": round(100 * unscoreable / grand_totals[sex], 3) if grand_totals[sex] else None,
                "high_risk_pct": round(100 * band_emp["high"] / matched_employment, 3) if matched_employment else None,
                "medium_risk_pct": round(100 * band_emp["medium"] / matched_employment, 3) if matched_employment else None,
                "low_risk_pct": round(100 * band_emp["low"] / matched_employment, 3) if matched_employment else None,
                "weighted_mean_prob": round(wmean, 4) if wmean is not None else None,
            }
    return out


def top_by_score(scored, titles, categories_total, n=20):
    rows = []
    for code, emp in categories_total.items():
        if code not in scored:
            continue
        rows.append({
            "occ_code": code,
            "title": titles.get(code, ""),
            "employment_millions": round(emp, 4),
            "mean_prob": scored[code]["mean_prob"],
            "min_prob": scored[code]["min_prob"],
            "max_prob": scored[code]["max_prob"],
            "manually_assigned": code in MANUAL_ASSIGN,
        })
    rows.sort(key=lambda r: (-r["mean_prob"], -r["employment_millions"]))
    return rows[:n]


def top_by_workers_high_risk(scored, titles, categories_total, n=20):
    rows = []
    for code, emp in categories_total.items():
        if code not in scored:
            continue
        if scored[code]["mean_prob"] <= 0.7:
            continue
        rows.append({
            "occ_code": code,
            "title": titles.get(code, ""),
            "employment_millions": round(emp, 4),
            "mean_prob": scored[code]["mean_prob"],
            "manually_assigned": code in MANUAL_ASSIGN,
        })
    rows.sort(key=lambda r: -r["employment_millions"])
    return rows[:n]


def print_stats_table(stats_dict, label):
    print(f"\n[B7] --- {label} ---")
    hdr = f"{'sex':<7} {'variant':<10} {'scoreable_M':>12} {'unscoreable%':>13} {'high%':>7} {'med%':>7} {'low%':>7} {'wmean':>7}"
    print(hdr)
    print("-" * len(hdr))
    for sex in ("Total", "Male", "Female"):
        for variant in ("min_prob", "mean_prob", "max_prob"):
            r = stats_dict[f"{sex}|{variant}"]
            print(f"{sex:<7} {variant:<10} {r['scoreable_M']:>12.3f} {r['unscoreable_pct']:>12.3f}% "
                  f"{r['high_risk_pct']:>6.2f}% {r['medium_risk_pct']:>6.2f}% {r['low_risk_pct']:>6.2f}% "
                  f"{r['weighted_mean_prob']:>7.4f}")


def build_appendix(unmatched_path, emp_19th_by_code, total_employed):
    excluded_codes = set()
    rows = []
    with open(unmatched_path, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["track"] != "B":
                continue
            if row["occ_code"] in MANUAL_ASSIGN:
                continue  # resolved this round, not part of the 25-code appendix
            emp = emp_19th_by_code.get(row["occ_code"], 0.0)
            rows.append({
                "occ_code": row["occ_code"],
                "title": row["title"],
                "employment_millions": round(emp, 4),
                "share_pct_of_total_employed": round(100 * emp / total_employed, 4) if total_employed else None,
                "reason": row["reason"],
            })
            excluded_codes.add(row["occ_code"])
    rows.sort(key=lambda r: -r["employment_millions"])
    return rows


def main():
    scored_a, titles_a = load_scored(assign_manual=False)
    scored_b, titles_b = load_scored(assign_manual=True)

    emp19_by_sex, emp19_total_by_sex = load_employment(EMP_19TH)
    emp13_by_sex, emp13_total_by_sex = load_employment(EMP_13TH)

    # --- headline: scenario (b), both ICLS standards ---
    stats_19_b = compute_stats(scored_b, emp19_by_sex, emp19_total_by_sex)
    stats_13_b = compute_stats(scored_b, emp13_by_sex, emp13_total_by_sex)
    print_stats_table(stats_19_b, "HEADLINE (b) assigned, 19th ICLS")
    print_stats_table(stats_13_b, "HEADLINE (b) assigned, 13th ICLS")

    # --- sensitivity: scenario (a), both ICLS standards ---
    stats_19_a = compute_stats(scored_a, emp19_by_sex, emp19_total_by_sex)
    stats_13_a = compute_stats(scored_a, emp13_by_sex, emp13_total_by_sex)
    print_stats_table(stats_19_a, "SENSITIVITY (a) excluded, 19th ICLS")
    print_stats_table(stats_13_a, "SENSITIVITY (a) excluded, 13th ICLS")

    # --- gap between ICLS standards, headline (b), mean_prob variant ---
    print("\n[B7] === 19th vs 13th ICLS gap (scenario b, mean_prob variant) ===")
    for sex in ("Total", "Male", "Female"):
        r19 = stats_19_b[f"{sex}|mean_prob"]
        r13 = stats_13_b[f"{sex}|mean_prob"]
        d_hr = r13["high_risk_pct"] - r19["high_risk_pct"]
        d_wm = r13["weighted_mean_prob"] - r19["weighted_mean_prob"]
        d_emp = r13["scoreable_M"] - r19["scoreable_M"]
        print(f"  {sex:<7} scoreable_M: 19th={r19['scoreable_M']:.3f}  13th={r13['scoreable_M']:.3f}  "
              f"gap={d_emp:+.3f}M | high-risk%: 19th={r19['high_risk_pct']:.2f}  13th={r13['high_risk_pct']:.2f}  "
              f"gap={d_hr:+.3f}pp | wmean: 19th={r19['weighted_mean_prob']:.4f}  13th={r13['weighted_mean_prob']:.4f}  "
              f"gap={d_wm:+.4f}")

    # --- top 20 by score / top 20 by workers in high-risk (headline scenario b, 19th ICLS Total) ---
    cat_total_19 = combine_total(emp19_by_sex)
    top20_score = top_by_score(scored_b, titles_b, cat_total_19, n=20)
    top20_workers = top_by_workers_high_risk(scored_b, titles_b, cat_total_19, n=20)

    print("\n[B7] === TOP 20 BY SCORE (mean_prob, headline scenario b, 19th ICLS Total) ===")
    for i, r in enumerate(top20_score, 1):
        flag = " [manually assigned]" if r["manually_assigned"] else ""
        print(f"  {i:>2}. {r['occ_code']} {r['title'][:45]:<45} prob={r['mean_prob']:.3f} "
              f"emp={r['employment_millions']:.3f}M{flag}")

    print("\n[B7] === TOP 20 BY ABSOLUTE WORKERS IN HIGH-RISK (>0.7) OCCUPATIONS ===")
    for i, r in enumerate(top20_workers, 1):
        flag = " [manually assigned]" if r["manually_assigned"] else ""
        print(f"  {i:>2}. {r['occ_code']} {r['title'][:45]:<45} emp={r['employment_millions']:.3f}M "
              f"prob={r['mean_prob']:.3f}{flag}")

    # --- appendix: 25 remaining unmatched codes ---
    emp19_code_total = cat_total_19
    total_employed_19 = emp19_total_by_sex["Male"] + emp19_total_by_sex["Female"]
    appendix = build_appendix("output/unmatched_occupations.csv", emp19_code_total, total_employed_19)
    appendix_total_emp = sum(r["employment_millions"] for r in appendix)
    appendix_total_share = 100 * appendix_total_emp / total_employed_19

    print(f"\n[B7] === APPENDIX: {len(appendix)} REMAINING UNMATCHED 4-DIGIT CODES (excluded from headline) ===")
    print(f"     Combined employment: {appendix_total_emp:.4f}M ({appendix_total_share:.3f}% of {total_employed_19:.3f}M total employed, 19th ICLS)")
    for r in appendix:
        print(f"  {r['occ_code']} {r['title'][:50]:<50} emp={r['employment_millions']:.4f}M "
              f"({r['share_pct_of_total_employed']:.4f}%)")

    with open("output/unmatched_appendix.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["occ_code", "title", "employment_millions", "share_pct_of_total_employed", "reason"])
        writer.writeheader()
        writer.writerows(appendix)
    print(f"\n[B7] Wrote appendix table to output/unmatched_appendix.csv")

    with open("output/track_b_top20_by_score.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["occ_code", "title", "employment_millions", "mean_prob", "min_prob", "max_prob", "manually_assigned"])
        writer.writeheader()
        writer.writerows(top20_score)

    with open("output/track_b_top20_by_workers_high_risk.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["occ_code", "title", "employment_millions", "mean_prob", "manually_assigned"])
        writer.writeheader()
        writer.writerows(top20_workers)

    all_out = {
        "headline_scenario_b": {"19th_ICLS": stats_19_b, "13th_ICLS": stats_13_b},
        "sensitivity_scenario_a": {"19th_ICLS": stats_19_a, "13th_ICLS": stats_13_a},
        "appendix_unmatched_total_employment_M": round(appendix_total_emp, 4),
        "appendix_unmatched_share_pct": round(appendix_total_share, 4),
        "note": "weighted_mean_prob is an internal Pakistan-occupation-structure statistic; "
                "not to be set against Frey-Osborne's headline 47% US figure, which is a "
                "differently-weighted (US employment structure) statistic over the same "
                "underlying 702 occupation scores.",
    }
    with open("output/headline_results_track_b.json", "w", encoding="utf-8") as f:
        json.dump(all_out, f, indent=2)
    print("\n[B7] Wrote output/headline_results_track_b.json")
    print("\n[B7] DONE")


if __name__ == "__main__":
    main()
