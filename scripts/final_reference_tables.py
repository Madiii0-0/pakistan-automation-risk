"""
Final reference tables - consolidates every ad-hoc inline computation from
the results-discussion phase (threshold sensitivity, agricultural exclusion
ladder, top-10 high-risk concentration, female min-to-mean decomposition)
into saved output files, so the results reference document can cite a file
for every number rather than "computed inline."

All figures use scenario (b) (9211/9212/9213 assigned SOC 45-2090, 0.87
point estimate) and 19th ICLS employment unless stated otherwise.
"""
import csv
import json
from collections import defaultdict

EMP_19TH = "output/track_b_employment_19th.csv"
SCORED = "output/track_b_scored.csv"
MANUAL = {
    "9211": ("Crop farm labourers", 0.87),
    "9212": ("Livestock farm labourers", 0.87),
    "9213": ("Mixed crop and livestock farm labourers", 0.87),
}
AG5 = ["6130", "6121", "9211", "8341", "9213"]


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


def load_scored():
    scored, titles = {}, {}
    with open(SCORED, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            scored[row["occ_code"]] = {
                "min": float(row["min_prob"]), "mean": float(row["mean_prob"]), "max": float(row["max_prob"]),
            }
            titles[row["occ_code"]] = row["title"]
    for code, (t, p) in MANUAL.items():
        scored[code] = {"min": p, "mean": p, "max": p}
        titles[code] = t
    return scored, titles


def hr_share(emp_dict, scored, exclude, thr, variant):
    denom = sum(emp_dict.get(c, 0.0) for c in scored if c not in exclude)
    num = sum(emp_dict.get(c, 0.0) for c in scored if c not in exclude and scored[c][variant] > thr)
    return (100 * num / denom if denom else None), denom


def main():
    emp_f, emp_m, emp_t = load_employment()
    scored, titles = load_scored()

    # --- threshold table: Total/Male/Female x 0.6/0.7/0.8, mean variant ---
    threshold_rows = []
    for thr in (0.6, 0.7, 0.8):
        row = {"threshold": thr}
        shares = {}
        for sexname, d in (("Total", emp_t), ("Male", emp_m), ("Female", emp_f)):
            share, denom = hr_share(d, scored, set(), thr, "mean")
            row[f"{sexname.lower()}_high_risk_pct"] = round(share, 3)
            row[f"{sexname.lower()}_scoreable_M"] = round(denom, 4)
            shares[sexname] = share
        row["male_minus_female_gap_pp"] = round(shares["Male"] - shares["Female"], 3)
        threshold_rows.append(row)
    with open("output/ref_threshold_table.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(threshold_rows[0].keys()))
        writer.writeheader()
        writer.writerows(threshold_rows)
    print("[final_ref] Wrote output/ref_threshold_table.csv")

    # --- agricultural exclusion ladder ---
    ladder_rows = []
    for label, excl in [
        ("baseline", set()),
        ("exclude_6130", {"6130"}),
        ("exclude_6130_6121", {"6130", "6121"}),
        ("exclude_all_5_ag_codes", set(AG5)),
    ]:
        row = {"scenario": label, "excluded_codes": ",".join(sorted(excl)) if excl else ""}
        for sexname, d in (("Total", emp_t), ("Male", emp_m), ("Female", emp_f)):
            share, denom = hr_share(d, scored, excl, 0.7, "mean")
            excl_emp = sum(d.get(c, 0.0) for c in excl)
            row[f"{sexname.lower()}_high_risk_pct"] = round(share, 3)
            row[f"{sexname.lower()}_denom_M"] = round(denom, 4)
            row[f"{sexname.lower()}_excluded_emp_M"] = round(excl_emp, 4)
        ladder_rows.append(row)
    with open("output/ref_agricultural_exclusion_ladder.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(ladder_rows[0].keys()))
        writer.writeheader()
        writer.writerows(ladder_rows)
    print("[final_ref] Wrote output/ref_agricultural_exclusion_ladder.csv")

    # --- top 10 high-risk occupations, share of high-risk population ---
    high_risk_rows = [(c, titles[c], emp_t.get(c, 0.0)) for c in scored if scored[c]["mean"] > 0.7]
    total_hr_emp = sum(e for _, _, e in high_risk_rows)
    high_risk_rows.sort(key=lambda r: -r[2])
    top10 = []
    cum = 0.0
    for i, (c, t, e) in enumerate(high_risk_rows[:10], 1):
        share = 100 * e / total_hr_emp
        cum += share
        top10.append({
            "rank": i, "occ_code": c, "title": t, "employment_millions": round(e, 4),
            "share_of_high_risk_pop_pct": round(share, 3), "cumulative_pct": round(cum, 3),
        })
    with open("output/ref_top10_high_risk_concentration.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(top10[0].keys()))
        writer.writeheader()
        writer.writerows(top10)
    print(f"[final_ref] Wrote output/ref_top10_high_risk_concentration.csv (total high-risk pop = {total_hr_emp:.4f}M)")

    # --- female min-to-mean decomposition ---
    total_f = sum(emp_f.get(c, 0.0) for c in scored)
    high_min_f = sum(emp_f.get(c, 0.0) for c in scored if scored[c]["min"] > 0.7)
    high_mean_f = sum(emp_f.get(c, 0.0) for c in scored if scored[c]["mean"] > 0.7)
    flips = [(c, emp_f.get(c, 0.0)) for c in scored if scored[c]["min"] <= 0.7 < scored[c]["mean"]]
    flips.sort(key=lambda x: -x[1])
    flip_rows = []
    for c, e in flips:
        flip_rows.append({
            "occ_code": c, "title": titles[c], "female_employment_M": round(e, 4),
            "min_prob": scored[c]["min"], "mean_prob": scored[c]["mean"],
            "contribution_to_swing_pp": round(100 * e / total_f, 4),
        })
    with open("output/ref_female_decomposition.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(flip_rows[0].keys()))
        writer.writeheader()
        writer.writerows(flip_rows)

    swing_summary = {
        "total_scoreable_female_M": round(total_f, 4),
        "high_risk_share_min_pct": round(100 * high_min_f / total_f, 3),
        "high_risk_share_mean_pct": round(100 * high_mean_f / total_f, 3),
        "swing_pp": round(100 * (high_mean_f - high_min_f) / total_f, 3),
        "n_flipping_codes": len(flips),
        "flipping_codes_employment_M": round(sum(e for _, e in flips), 4),
        "6130_contribution_pp": round(100 * emp_f.get("6130", 0.0) / total_f, 3),
        "6121_contribution_pp": round(100 * emp_f.get("6121", 0.0) / total_f, 3),
        "6130_plus_6121_contribution_pp": round(100 * (emp_f.get("6130", 0.0) + emp_f.get("6121", 0.0)) / total_f, 3),
    }
    with open("output/ref_female_swing_summary.json", "w", encoding="utf-8") as f:
        json.dump(swing_summary, f, indent=2)
    print("[final_ref] Wrote output/ref_female_decomposition.csv and output/ref_female_swing_summary.json")
    print(json.dumps(swing_summary, indent=2))


if __name__ == "__main__":
    main()
