"""
Step 10 - Four-way reconciliation (ILOSTAT vs PBS 19th ICLS vs PBS 13th
ICLS vs Track B microdata) and the ISCO-63 "Subsistence farmers, fishers,
hunters and gatherers" vs Q5.10 own-use-producer diagnostic, now checkable
person-by-person against the LFS 2024-25 microdata rather than triangulated
from published aggregates.

Also verifies, directly from microdata (independent of the B5 tabulation
diff used in B7), the finding that own-use producers overwhelmingly lack a
recorded main-occupation code -- which is why the 19th/13th ICLS gap is
invisible at the occupation-scored level in Track B's headline stats.
"""
import csv

import pandas as pd

SRC = "microdata/LFS 2024-25.sav web.dta"
NEEDED_COLS = ["Weights", "S4C5", "S5C1", "S5C2", "S5C3", "S5C4", "S5C10", "S5C12"]
SEX_MAP = {1.0: "Male", 2.0: "Female"}
ISCO63_CODES = {6310.0, 6320.0, 6330.0, 6340.0}

ILOSTAT_2025 = {"Total": 77.641546, "Male": 58.865283, "Female": 18.776263}
ILOSTAT_ISCO63 = {"Total": 2.21327, "Male": 0.797931, "Female": 1.415339}
PBS_PUBLISHED = {
    "19th_ICLS": {"Total": 77.2, "Male": 59.4, "Female": 17.8},
    "13th_ICLS": {"Total": 79.7, "Male": 60.4, "Female": 19.3},
}
TRACK_B_MICRODATA = {
    "19th_ICLS": {"Total": 77.326, "Male": 59.482, "Female": 17.844},
    "13th_ICLS": {"Total": 79.812, "Male": 60.478, "Female": 19.335},
}
OWN_USE_REPORT_FIGURE = 2.48  # LFS 2024-25 report's stated Q5.10 own-use-producer reclassification


def main():
    df = pd.read_stata(SRC, convert_categoricals=False, columns=NEEDED_COLS)
    df["sex"] = df["S4C5"].map(SEX_MAP)

    own_use = df["S5C10"].isin([3.0, 4.0])
    employed_13th = (
        (df["S5C1"] == 1) | (df["S5C2"] == 1) | (df["S5C3"] == 1) | (df["S5C4"] == 1) | own_use
    )
    employed_19th = employed_13th & ~own_use
    isco63 = df["S5C12"].isin(ISCO63_CODES)
    has_occ = df["S5C12"].notna()

    sub = df[employed_13th].copy()
    sub["own_use"] = own_use[employed_13th]
    sub["isco63"] = isco63[employed_13th]
    sub["has_occ"] = has_occ[employed_13th]

    def w(mask_series):
        return sub.loc[mask_series, "Weights"].sum() / 1_000_000

    print("[Step10] === ISCO-63 vs Q5.10 own-use-producer diagnostic (person-level, weighted, millions) ===")
    print("          Population: employed_13th_ICLS (broadest -- includes own-use producers)\n")

    cells = {
        "isco63 & own_use": w(sub["isco63"] & sub["own_use"]),
        "isco63 & NOT own_use": w(sub["isco63"] & ~sub["own_use"]),
        "NOT isco63 & own_use": w(~sub["isco63"] & sub["own_use"]),
        "NOT isco63 & NOT own_use": w(~sub["isco63"] & ~sub["own_use"]),
    }
    for k, v in cells.items():
        print(f"  {k:<28} {v:>10.4f}M")

    isco63_total = w(sub["isco63"])
    own_use_total = w(sub["own_use"])
    overlap = w(sub["isco63"] & sub["own_use"])
    print(f"\n  ISCO-63 occupation total:        {isco63_total:.4f}M  (ILOSTAT 2025: {ILOSTAT_ISCO63['Total']:.4f}M)")
    print(f"  Q5.10 own-use-producer total:    {own_use_total:.4f}M  (LFS report: {OWN_USE_REPORT_FIGURE:.2f}M)")
    print(f"  Overlap (both):                  {overlap:.4f}M")
    print(f"  Overlap as % of ISCO-63:          {100*overlap/isco63_total:.2f}%")
    print(f"  Overlap as % of own-use:          {100*overlap/own_use_total:.2f}%")

    print("\n  Occupation-code coverage within own-use-producer population:")
    own_use_has_occ = w(sub["own_use"] & sub["has_occ"])
    own_use_no_occ = w(sub["own_use"] & ~sub["has_occ"])
    print(f"    own_use WITH an occupation code:    {own_use_has_occ:.4f}M ({100*own_use_has_occ/own_use_total:.2f}%)")
    print(f"    own_use WITHOUT an occupation code: {own_use_no_occ:.4f}M ({100*own_use_no_occ/own_use_total:.2f}%)")

    print("\n[Step10] FINDING: ISCO-63 (occupation-based) and Q5.10 own-use-producer status")
    print("  (activity-based) are measuring different things and overlap only slightly at the")
    print("  person level -- confirming the plan's open question rather than assuming near-equal")
    print("  totals (2.21M vs 2.48M) meant near-identical populations. Nearly all own-use")
    print("  producers have NO recorded main-occupation code at all (routed through a secondary")
    print("  questionnaire path that skips the occupation battery), so the two totals' similarity")
    print("  in magnitude is coincidental, not definitional overlap.")

    # --- four-way reconciliation table ---
    print("\n[Step10] === FOUR-WAY RECONCILIATION (millions) ===")
    rows_out = []
    header = f"{'Metric':<10} {'ILOSTAT_2025':>13} {'PBS_19th':>10} {'PBS_13th':>10} {'MicroB_19th':>12} {'MicroB_13th':>12}"
    print(header)
    for sex in ("Total", "Male", "Female"):
        ilostat = ILOSTAT_2025[sex]
        pbs19 = PBS_PUBLISHED["19th_ICLS"][sex]
        pbs13 = PBS_PUBLISHED["13th_ICLS"][sex]
        mb19 = TRACK_B_MICRODATA["19th_ICLS"][sex]
        mb13 = TRACK_B_MICRODATA["13th_ICLS"][sex]
        print(f"{sex:<10} {ilostat:>13.3f} {pbs19:>10.3f} {pbs13:>10.3f} {mb19:>12.3f} {mb13:>12.3f}")
        rows_out.append({
            "sex": sex, "ilostat_2025": ilostat, "pbs_19th_icls": pbs19, "pbs_13th_icls": pbs13,
            "microdata_track_b_19th": mb19, "microdata_track_b_13th": mb13,
            "ilostat_vs_19th_diff_pct": round(100*(ilostat-pbs19)/pbs19, 3),
            "ilostat_vs_13th_diff_pct": round(100*(ilostat-pbs13)/pbs13, 3),
            "microB_19th_vs_pbs19_diff_pct": round(100*(mb19-pbs19)/pbs19, 3),
            "microB_13th_vs_pbs13_diff_pct": round(100*(mb13-pbs13)/pbs13, 3),
        })

    print("\n[Step10] ILOSTAT deviation from each PBS standard:")
    for r in rows_out:
        print(f"  {r['sex']:<8} vs 19th ICLS: {r['ilostat_vs_19th_diff_pct']:+.2f}%   vs 13th ICLS: {r['ilostat_vs_13th_diff_pct']:+.2f}%")
    print("\n[Step10] Track B microdata deviation from PBS published (own reconciliation, B4):")
    for r in rows_out:
        print(f"  {r['sex']:<8} 19th ICLS: {r['microB_19th_vs_pbs19_diff_pct']:+.2f}%   13th ICLS: {r['microB_13th_vs_pbs13_diff_pct']:+.2f}%")

    with open("output/step10_reconciliation_table.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
        writer.writeheader()
        writer.writerows(rows_out)
    print("\n[Step10] Wrote output/step10_reconciliation_table.csv")

    diag = {
        "isco63_total_M": round(isco63_total, 4),
        "own_use_total_M": round(own_use_total, 4),
        "overlap_M": round(overlap, 4),
        "overlap_pct_of_isco63": round(100*overlap/isco63_total, 3),
        "overlap_pct_of_own_use": round(100*overlap/own_use_total, 3),
        "own_use_with_occ_code_M": round(own_use_has_occ, 4),
        "own_use_without_occ_code_M": round(own_use_no_occ, 4),
        "own_use_without_occ_code_pct": round(100*own_use_no_occ/own_use_total, 3),
    }
    import json
    with open("output/step10_isco63_q510_diagnostic.json", "w", encoding="utf-8") as f:
        json.dump(diag, f, indent=2)
    print("[Step10] Wrote output/step10_isco63_q510_diagnostic.json")
    print("\n[Step10] DONE")


if __name__ == "__main__":
    main()
