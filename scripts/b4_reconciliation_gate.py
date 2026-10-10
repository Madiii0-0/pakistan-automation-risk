"""
B4 - Reconciliation gate. Derive "employed" under both ICLS standards from
the raw LFS 2024-25 microdata screening questions, compute weighted
totals, and compare against PBS's published figures.

Derivation logic (no pre-built "employed" flag exists in the microdata --
this is reconstructed from the raw section-5 screening battery, and was
corrected once during this reconstruction: an initial version using only
S5C1-S5C4 undercounted 13th ICLS employment, especially female, by
missing ~0.94M weighted persons who answered "No" to all four screening
questions yet still have a valid own-use-production response on S5C10 --
i.e. a secondary path into the agricultural/subsistence module that
doesn't strictly require a "Yes" on S5C1-4 first. Confirmed by checking
(own_use & ~employed_13th_v1), which was non-empty and explained the gap
exactly):

  own_use_producer = S5C10 in (3, 4)
      "mainly for family use" / "only for family use" -- S5C10 is
      explicitly the same question the LFS report cites by name ("Q5.10,
      codes 3 and 4") for the 2.48M own-use-producer reclassification.
      Weighted total here: 2.487M, essentially exact vs. the report's
      stated 2.48M -- this flag alone is independently validated.

  employed_13th_ICLS = (S5C1==1) | (S5C2==1) | (S5C3==1) | (S5C4==1) | own_use_producer
      "worked for pay", "ran a business/farm", "helped in family
      farm/business", "has a job but was absent last week", OR is a
      confirmed own-use producer via the secondary path -- matching the
      13th ICLS's broad "any work" definition, own-use production
      included.

  employed_19th_ICLS = employed_13th_ICLS & ~own_use_producer
      Mathematically identical to (S5C1==1)|(S5C2==1)|(S5C3==1)|(S5C4==1)
      minus own_use_producer -- the own_use OR-in and the subsequent
      AND-NOT cancel out, so this fix changes 13th ICLS only, not 19th.

This is a reconstruction, not a copy of PBS's internal derivation code --
that's exactly why this script's job is to check it against published
totals rather than assume it's right.
"""
import pandas as pd

SRC = "microdata/LFS 2024-25.sav web.dta"
OUT_SUMMARY = "output/b4_reconciliation_summary.csv"

NEEDED_COLS = [
    "Weights", "S4C5", "S4C6",
    "S5C1", "S5C2", "S5C3", "S5C4", "S5C10", "S5C12",
]

# Published PBS LFS 2024-25 figures (millions), from lfs_2024_25.pdf
PUBLISHED = {
    "19th_ICLS": {"Total": 77.2, "Male": 59.4, "Female": 17.8},
    "13th_ICLS": {"Total": 79.7, "Male": 60.4, "Female": 19.3},
}
SEX_MAP = {1.0: "Male", 2.0: "Female"}


def main():
    df = pd.read_stata(SRC, convert_categoricals=False, columns=NEEDED_COLS)
    print(f"[B4] Loaded {len(df):,} rows")

    df["sex"] = df["S4C5"].map(SEX_MAP)

    own_use = df["S5C10"].isin([3.0, 4.0])
    employed_13th = (
        (df["S5C1"] == 1) | (df["S5C2"] == 1) | (df["S5C3"] == 1) | (df["S5C4"] == 1) | own_use
    )
    employed_19th = employed_13th & ~own_use

    df["employed_13th"] = employed_13th
    df["employed_19th"] = employed_19th
    df["own_use"] = own_use

    print(f"\n[B4] Unweighted person counts:")
    print(f"  employed_13th_ICLS (any screening Yes): {employed_13th.sum():,}")
    print(f"  own_use_producer (S5C10 in 3,4):         {own_use.sum():,}")
    print(f"  employed_19th_ICLS (13th minus own-use): {employed_19th.sum():,}")
    print(f"  S5C12 (main occupation) non-null:        {df['S5C12'].notna().sum():,}")

    # Data-quality cross-check: does the employed_13th flag line up with
    # who actually has a main-occupation code? A large mismatch either
    # way would mean the screening-question derivation above is wrong.
    occ_but_not_employed = ((df["S5C12"].notna()) & (~employed_13th)).sum()
    employed_but_no_occ = (employed_13th & df["S5C12"].isna()).sum()
    print(f"  Has occupation code but NOT flagged employed_13th: {occ_but_not_employed:,}")
    print(f"  Flagged employed_13th but NO occupation code:      {employed_but_no_occ:,}")

    results = {}
    for icls_label, flag_col in (("19th_ICLS", "employed_19th"), ("13th_ICLS", "employed_13th")):
        sub = df[df[flag_col]]
        total_weighted = sub["Weights"].sum() / 1_000_000  # raw person-count weights -> millions
        by_sex = sub.groupby("sex")["Weights"].sum() / 1_000_000

        results[icls_label] = {
            "Total": total_weighted,
            "Male": by_sex.get("Male", 0.0),
            "Female": by_sex.get("Female", 0.0),
        }

    print("\n[B4] === RECONCILIATION TABLE (millions) ===")
    print(f"{'ICLS':<10} {'Sex':<8} {'Microdata':>12} {'Published':>12} {'Diff':>10} {'Diff %':>8}")
    rows_out = []
    for icls_label in ("19th_ICLS", "13th_ICLS"):
        for sex_key in ("Total", "Male", "Female"):
            micro = results[icls_label][sex_key]
            pub = PUBLISHED[icls_label][sex_key]
            diff = micro - pub
            diff_pct = 100 * diff / pub
            flag = "  <-- >2pp OFF" if abs(diff_pct) > 2 else ("  <-- 1-2pp" if abs(diff_pct) > 1 else "")
            print(f"{icls_label:<10} {sex_key:<8} {micro:>12.2f} {pub:>12.2f} {diff:>+10.2f} {diff_pct:>+7.2f}%{flag}")
            rows_out.append(
                {
                    "icls_standard": icls_label,
                    "sex": sex_key,
                    "microdata_millions": round(micro, 3),
                    "published_millions": pub,
                    "diff_millions": round(diff, 3),
                    "diff_pct": round(diff_pct, 3),
                }
            )

    import csv
    with open(OUT_SUMMARY, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f, fieldnames=["icls_standard", "sex", "microdata_millions", "published_millions", "diff_millions", "diff_pct"]
        )
        writer.writeheader()
        writer.writerows(rows_out)
    print(f"\n[B4] Wrote reconciliation table to {OUT_SUMMARY}")

    max_abs_diff_pct = max(abs(r["diff_pct"]) for r in rows_out)
    print(f"\n[B4] Max absolute diff across all 6 cells: {max_abs_diff_pct:.2f}%")
    print("[B4] Plan tolerance: ~1-2 percentage points.")
    gate_pass = max_abs_diff_pct <= 2.0
    print(f"[B4] GATE {'PASSES' if gate_pass else 'FAILS'} at 2pp tolerance (max diff {max_abs_diff_pct:.2f}%)")

    # Known, quantified completeness gap for B5: some employed_19th persons
    # (via S5C2/S5C3/S5C4 "Yes") have no recorded main-occupation code, so
    # B5's per-occupation tabulation will sum to slightly less than this
    # gate's total employed figure. Surfaced here, not discovered cold in B5.
    has_occ = df["S5C12"].notna()
    employed_no_occ = employed_19th & ~has_occ
    w_gap = df.loc[employed_no_occ, "Weights"].sum() / 1_000_000
    w_19th_total = results["19th_ICLS"]["Total"]
    print(f"\n[B4] Employed (19th ICLS) with NO main-occupation code: {w_gap:.3f}M "
          f"({100*w_gap/w_19th_total:.2f}% of {w_19th_total:.2f}M) -- B5's occupation-level")
    print("     tabulation will be short by this amount; not an error, just item-nonresponse")
    print("     on S5C12 among people otherwise confirmed employed.")


if __name__ == "__main__":
    main()
