"""
B6b - Three-way headline statistics showing the cost of the unmatched-
occupation assignment decision for 9211/9212/9213 (Crop/Livestock/Mixed
farm labourers), per explicit instruction:

(a) EXCLUDED    -- unmatched codes stay out, denominator = scored employment only
(b) ASSIGNED    -- 9211/9212/9213 assigned the primary candidate (SOC 45-2090,
                   prob=0.87) as a point estimate (min=mean=max=0.87)
(c) FLAGGED     -- 9211/9212/9213 assigned using BOTH proposed candidates as a
                   min/max band (0.85-0.87) rather than a point, explicitly
                   tagged manually_assigned=True in the output so this
                   assignment's contribution to any headline number can be
                   isolated for a sensitivity footnote

The other 25 unmatched codes (1.52M employment) are NOT addressed this
round and remain excluded in all three scenarios -- stated explicitly,
not silently folded in.
"""
import csv
import statistics as stats
from collections import defaultdict

SCORED = "output/track_b_scored.csv"
EMP_19TH = "output/track_b_employment_19th.csv"
NO_OCC_CODE = "NO_OCCUPATION_CODE"

MANUAL = {
    "9211": {"title": "Crop farm labourers", "candidates": [0.87, 0.85]},
    "9212": {"title": "Livestock farm labourers", "candidates": [0.87, 0.85]},
    "9213": {"title": "Mixed crop and livestock farm labourers", "candidates": [0.87, 0.85]},
}


def load_scored():
    scored = {}
    with open(SCORED, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            scored[row["occ_code"]] = {
                "min_prob": float(row["min_prob"]),
                "mean_prob": float(row["mean_prob"]),
                "max_prob": float(row["max_prob"]),
            }
    return scored


def load_employment_by_sex():
    by_sex = defaultdict(dict)  # sex -> {code: emp_millions}
    total_by_sex = defaultdict(float)
    with open(EMP_19TH, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            sex = row["sex"]
            emp = float(row["weighted_employment_millions"])
            total_by_sex[sex] += emp  # includes NO_OCCUPATION_CODE in the true total
            if row["occ_code"] != NO_OCC_CODE:
                by_sex[sex][row["occ_code"]] = by_sex[sex].get(row["occ_code"], 0.0) + emp
    return by_sex, total_by_sex


def band(prob):
    if prob > 0.7:
        return "high"
    if prob >= 0.3:
        return "medium"
    return "low"


def compute_headline(scored, emp_by_sex, total_by_sex, label):
    print(f"\n[B6b] === SCENARIO: {label} ===")
    result = {}
    for sex in ("Male", "Female"):
        categories = emp_by_sex[sex]
        matched_employment = sum(v for k, v in categories.items() if k in scored)
        unscoreable = total_by_sex[sex] - matched_employment
        print(f"  {sex}: scoreable={matched_employment:.3f}M, "
              f"unscoreable(excluded/no-code)={unscoreable:.3f}M "
              f"({100*unscoreable/total_by_sex[sex]:.2f}% of {total_by_sex[sex]:.3f}M)")

        for variant in ("min_prob", "mean_prob", "max_prob"):
            band_emp = {"high": 0.0, "medium": 0.0, "low": 0.0}
            wsum = 0.0
            for code, emp in categories.items():
                if code not in scored:
                    continue
                p = scored[code][variant]
                band_emp[band(p)] += emp
                wsum += emp * p
            hr = 100 * band_emp["high"] / matched_employment if matched_employment else None
            wmean = wsum / matched_employment if matched_employment else None
            result[f"{sex}|{variant}"] = {
                "scoreable_M": round(matched_employment, 3),
                "unscoreable_M": round(unscoreable, 3),
                "unscoreable_pct": round(100 * unscoreable / total_by_sex[sex], 3),
                "high_risk_pct": round(hr, 2) if hr is not None else None,
                "weighted_mean_prob": round(wmean, 4) if wmean is not None else None,
            }

    # Total (Male+Female combined)
    categories_total = defaultdict(float)
    for sex in ("Male", "Female"):
        for code, emp in emp_by_sex[sex].items():
            categories_total[code] += emp
    total_all = total_by_sex["Male"] + total_by_sex["Female"]
    matched_employment = sum(v for k, v in categories_total.items() if k in scored)
    unscoreable = total_all - matched_employment
    print(f"  Total: scoreable={matched_employment:.3f}M, "
          f"unscoreable(excluded/no-code)={unscoreable:.3f}M "
          f"({100*unscoreable/total_all:.2f}% of {total_all:.3f}M)")

    for variant in ("min_prob", "mean_prob", "max_prob"):
        band_emp = {"high": 0.0, "medium": 0.0, "low": 0.0}
        wsum = 0.0
        for code, emp in categories_total.items():
            if code not in scored:
                continue
            p = scored[code][variant]
            band_emp[band(p)] += emp
            wsum += emp * p
        hr = 100 * band_emp["high"] / matched_employment if matched_employment else None
        wmean = wsum / matched_employment if matched_employment else None
        result[f"Total|{variant}"] = {
            "scoreable_M": round(matched_employment, 3),
            "unscoreable_M": round(unscoreable, 3),
            "unscoreable_pct": round(100 * unscoreable / total_all, 3),
            "high_risk_pct": round(hr, 2) if hr is not None else None,
            "weighted_mean_prob": round(wmean, 4) if wmean is not None else None,
        }
        r = result[f"Total|{variant}"]
        print(f"    {variant:>9}: high-risk(>0.7)={r['high_risk_pct']}%  "
              f"weighted_mean_prob={r['weighted_mean_prob']}  "
              f"unscoreable={r['unscoreable_pct']}%")

    return result


def main():
    scored_base = load_scored()
    emp_by_sex, total_by_sex = load_employment_by_sex()

    # --- (a) EXCLUDED ---
    result_a = compute_headline(scored_base, emp_by_sex, total_by_sex,
                                 "(a) EXCLUDED -- unmatched stays out entirely")

    # --- (b) ASSIGNED (point estimate: primary candidate 0.87) ---
    scored_b = dict(scored_base)
    for code, info in MANUAL.items():
        p = info["candidates"][0]  # primary candidate, 0.87
        scored_b[code] = {"min_prob": p, "mean_prob": p, "max_prob": p}
    result_b = compute_headline(scored_b, emp_by_sex, total_by_sex,
                                 "(b) ASSIGNED -- 9211/9212/9213 = 0.87 (point estimate, primary candidate)")

    # --- (c) FLAGGED (band across both candidates, manually_assigned tagged) ---
    scored_c = dict(scored_base)
    for code, info in MANUAL.items():
        lo, hi = min(info["candidates"]), max(info["candidates"])
        mean = stats.fmean(info["candidates"])
        scored_c[code] = {"min_prob": lo, "mean_prob": round(mean, 4), "max_prob": hi}
    result_c = compute_headline(scored_c, emp_by_sex, total_by_sex,
                                 "(c) FLAGGED -- 9211/9212/9213 = 0.85-0.87 band, manually_assigned=True")

    # --- summary table: cost of the decision ---
    print("\n[B6b] === COST OF THE ASSIGNMENT DECISION (Total, mean_prob variant) ===")
    print(f"{'Scenario':<10} {'Scoreable_M':>12} {'Unscoreable%':>13} {'HighRisk%':>10} {'WeightedMean':>13}")
    for label, res in (("(a) excl", result_a), ("(b) point", result_b), ("(c) band", result_c)):
        r = res["Total|mean_prob"]
        print(f"{label:<10} {r['scoreable_M']:>12.3f} {r['unscoreable_pct']:>12.3f}% "
              f"{r['high_risk_pct']:>9.2f}% {r['weighted_mean_prob']:>13}")

    delta_share = result_b["Total|mean_prob"]["high_risk_pct"] - result_a["Total|mean_prob"]["high_risk_pct"]
    delta_wmean = result_b["Total|mean_prob"]["weighted_mean_prob"] - result_a["Total|mean_prob"]["weighted_mean_prob"]
    print(f"\n[B6b] Effect of assigning 9211/9212/9213 (b vs a): "
          f"high-risk share {delta_share:+.3f}pp, weighted mean prob {delta_wmean:+.4f}")
    print("[B6b] NOTE: 25 other unmatched codes (1.52M employment) remain excluded in ALL")
    print("      three scenarios -- not addressed this round, per explicit scope.")

    import json
    with open("output/b6b_unmatched_sensitivity.json", "w", encoding="utf-8") as f:
        json.dump({"a_excluded": result_a, "b_assigned_point": result_b, "c_assigned_flagged": result_c}, f, indent=2)
    print("\n[B6b] Wrote full breakdown to output/b6b_unmatched_sensitivity.json")


if __name__ == "__main__":
    main()
