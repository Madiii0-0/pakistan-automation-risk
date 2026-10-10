"""
A6 - Compute Track A headline statistics: join track_a_scored.csv (2-digit
Frey-Osborne min/mean/max scores) to ilostat_pakistan_filtered.csv
(weighted employment by 2-digit ISCO, sex, year), for year 2025 (the LFS
2024-25 round). Produces, for each of {min, mean, max} x {Total, Male,
Female}:

- high-risk employment share (score > 0.7)
- band shares (>0.7 / 0.3-0.7 / <0.3)
- employment-weighted mean probability (reported separately, not compared
  to Frey-Osborne's 47% US figure)
- share of employment that couldn't be scored at all (Armed Forces + "Not
  elsewhere classified"), so the denominator is never silently redefined

Also writes the two requested rankings: occupations ranked by score, and
occupations ranked by absolute high-risk (>0.7, mean variant) worker count.
"""
import csv
import json
from collections import defaultdict

SCORED = "output/track_a_scored.csv"
ILOSTAT = "output/ilostat_pakistan_filtered.csv"
YEAR = "2025"

OUT_HEADLINE = "output/headline_results_track_a.json"
OUT_TOP_SCORE = "output/track_a_top_by_score.csv"
OUT_TOP_WORKERS = "output/track_a_top_by_worker_count.csv"


def load_scored():
    rows = {}
    with open(SCORED, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            rows[row["isco_2digit"]] = {
                "title": row["title"],
                "min_prob": float(row["min_prob"]),
                "mean_prob": float(row["mean_prob"]),
                "max_prob": float(row["max_prob"]),
                "sd_prob": float(row["sd_prob"]),
                "range_prob": float(row["range_prob"]),
                "matched_soc_count": int(row["matched_soc_count"]),
            }
    return rows


def load_employment_2025():
    """Return {sex: {isco_2digit: employment_thousands}} for CATEGORY rows
    in 2025, plus separately the Total-row and NEC-row employment for the
    unscoreable-share calculation."""
    by_sex = defaultdict(dict)
    nec_by_sex = {}
    total_by_sex = {}
    suppressed = []
    with open(ILOSTAT, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["year"] != YEAR:
                continue
            raw = row["employment_thousands"]
            if raw == "":
                # ILO suppresses some small/unreliable cells (obs_status
                # "Unreliable") rather than reporting a value. Treated as
                # 0 contribution to that sex/category's employment, but
                # logged -- silently coercing to 0 without saying so would
                # be exactly the kind of quiet data loss the plan warns
                # about, even though the magnitude here is small (4 cells).
                suppressed.append((row["sex"], row["isco_2digit"], row["category_title"]))
                continue
            val = float(raw)
            if row["row_kind"] == "CATEGORY":
                by_sex[row["sex"]][row["isco_2digit"]] = val
            elif row["row_kind"] == "NEC":
                nec_by_sex[row["sex"]] = val
            elif row["row_kind"] == "TOTAL":
                total_by_sex[row["sex"]] = val

    if suppressed:
        print(f"[A6] NOTE: {len(suppressed)} 2025 cells are suppressed (ILO obs_status='Unreliable', ")
        print(f"     blank value) and are EXCLUDED from that sex/category's employment, not treated as 0:")
        for s in suppressed:
            print(f"       sex={s[0]:<6} isco_2digit={s[1]:<3} {s[2]}")
        print(f"     Effect: Male/Female totals for these categories will not sum exactly to the")
        print(f"     category's Total-sex row; the Total-sex row itself is unaffected since it's a")
        print(f"     separate reported cell, not a Male+Female recomputation.")

    return by_sex, nec_by_sex, total_by_sex


def band(prob: float) -> str:
    if prob > 0.7:
        return "high"
    if prob >= 0.3:
        return "medium"
    return "low"


def main():
    scored = load_scored()
    emp_by_sex, nec_by_sex, total_by_sex = load_employment_2025()

    print(f"[A6] Scored 2-digit categories available: {len(scored)}")
    for sex in ("Total", "Male", "Female"):
        print(f"[A6] {sex} 2025: {len(emp_by_sex[sex])} categories, "
              f"total employment {total_by_sex[sex]:.1f}K, NEC {nec_by_sex.get(sex, 0):.1f}K")

    headline = {}
    top_score_rows = []
    top_worker_rows = []

    for sex in ("Total", "Male", "Female"):
        categories = emp_by_sex[sex]
        matched_employment = 0.0
        unscored_employment = 0.0
        unscored_reasons = defaultdict(float)

        for code, emp in categories.items():
            if code in scored:
                matched_employment += emp
            else:
                unscored_employment += emp
                unscored_reasons[code] += emp

        # NEC is employment reported by ILOSTAT under no 2-digit code at
        # all -- definitionally unscoreable, always added to the same pile.
        unscored_employment += nec_by_sex.get(sex, 0.0)

        denom = matched_employment  # risk shares computed over SCORED employment only
        total_all = total_by_sex[sex]

        print(
            f"[A6] {sex}: matched(scoreable)={matched_employment:.1f}K, "
            f"unscoreable={unscored_employment:.1f}K "
            f"({100*unscored_employment/total_all:.3f}% of {total_all:.1f}K total)"
        )
        if unscored_reasons:
            print(f"[A6]   unscoreable breakdown: {dict(unscored_reasons)}")

        for variant in ("min_prob", "mean_prob", "max_prob"):
            band_emp = {"high": 0.0, "medium": 0.0, "low": 0.0}
            weighted_prob_sum = 0.0

            for code, emp in categories.items():
                if code not in scored:
                    continue
                prob = scored[code][variant]
                band_emp[band(prob)] += emp
                weighted_prob_sum += emp * prob

            high_risk_share = 100 * band_emp["high"] / denom if denom else None
            band_shares = {k: (100 * v / denom if denom else None) for k, v in band_emp.items()}
            weighted_mean_prob = weighted_prob_sum / denom if denom else None

            key = f"{sex}|{variant}"
            headline[key] = {
                "sex": sex,
                "variant": variant,
                "year": YEAR,
                "scoreable_employment_thousands": round(denom, 1),
                "unscoreable_employment_thousands": round(unscored_employment, 1),
                "unscoreable_share_pct_of_total": round(100 * unscored_employment / total_all, 4),
                "high_risk_share_pct": round(high_risk_share, 2) if high_risk_share is not None else None,
                "band_shares_pct": {k: round(v, 2) if v is not None else None for k, v in band_shares.items()},
                "employment_weighted_mean_prob": round(weighted_mean_prob, 4) if weighted_mean_prob is not None else None,
            }

        # rankings only need to be produced once per sex (score ranking is
        # independent of variant weighting choice at the "mean" level; use
        # mean_prob as the representative ranking variant, min/max available
        # in the same row for reference)
        if sex == "Total":
            for code, emp in categories.items():
                if code not in scored:
                    continue
                s = scored[code]
                top_score_rows.append(
                    {
                        "isco_2digit": code,
                        "title": s["title"],
                        "employment_2025_total_thousands": emp,
                        "min_prob": s["min_prob"],
                        "mean_prob": s["mean_prob"],
                        "max_prob": s["max_prob"],
                        "sd_prob": s["sd_prob"],
                        "range_prob": s["range_prob"],
                    }
                )
                if s["mean_prob"] > 0.7:
                    top_worker_rows.append(
                        {
                            "isco_2digit": code,
                            "title": s["title"],
                            "employment_2025_total_thousands": emp,
                            "mean_prob": s["mean_prob"],
                        }
                    )

    top_score_rows.sort(key=lambda r: -r["mean_prob"])
    top_worker_rows.sort(key=lambda r: -r["employment_2025_total_thousands"])

    with open(OUT_TOP_SCORE, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["isco_2digit", "title", "employment_2025_total_thousands",
                        "min_prob", "mean_prob", "max_prob", "sd_prob", "range_prob"],
        )
        writer.writeheader()
        writer.writerows(top_score_rows)
    print(f"[A6] Wrote {len(top_score_rows)} rows to {OUT_TOP_SCORE}")

    with open(OUT_TOP_WORKERS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["isco_2digit", "title", "employment_2025_total_thousands", "mean_prob"]
        )
        writer.writeheader()
        writer.writerows(top_worker_rows)
    print(f"[A6] Wrote {len(top_worker_rows)} rows (mean_prob>0.7) to {OUT_TOP_WORKERS}")

    with open(OUT_HEADLINE, "w", encoding="utf-8") as f:
        json.dump(headline, f, indent=2)
    print(f"[A6] Wrote headline results to {OUT_HEADLINE}")

    print("\n[A6] === TRACK A HEADLINE SUMMARY (2025, ISCO 2-digit) ===")
    for sex in ("Total", "Male", "Female"):
        print(f"\n  {sex}:")
        for variant in ("min_prob", "mean_prob", "max_prob"):
            h = headline[f"{sex}|{variant}"]
            print(
                f"    {variant:>9}: high-risk(>0.7) = {h['high_risk_share_pct']}%  "
                f"| bands: high={h['band_shares_pct']['high']}% "
                f"medium={h['band_shares_pct']['medium']}% low={h['band_shares_pct']['low']}%  "
                f"| weighted mean prob = {h['employment_weighted_mean_prob']}  "
                f"| unscoreable = {h['unscoreable_share_pct_of_total']}%"
            )

    print("\n[A6] DONE")


if __name__ == "__main__":
    main()
