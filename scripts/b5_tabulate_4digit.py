"""
B5 - Tabulate weighted employment by 4-digit PSCO occupation code (main
job only -- S5C12, not the subsidiary-job S5C27, per the plan's explicit
double-counting warning), by sex, under both ICLS standards, using the
employment derivation finalized and validated in B4.

The 0.097M (19th ICLS) / equivalent 13th-ICLS-scope employed persons with
no recorded main-occupation code are carried through as their own
explicit "NO_OCCUPATION_CODE" row in the output, per instruction -- not
dropped silently.
"""
import csv

import pandas as pd

SRC = "microdata/LFS 2024-25.sav web.dta"
NEEDED_COLS = ["Weights", "S4C5", "S5C1", "S5C2", "S5C3", "S5C4", "S5C10", "S5C12"]
SEX_MAP = {1.0: "Male", 2.0: "Female"}
NO_OCC_CODE = "NO_OCCUPATION_CODE"


def tabulate(df, employed_flag, label):
    sub = df[employed_flag].copy()
    sub["occ_code"] = sub["S5C12"].apply(
        lambda v: NO_OCC_CODE if pd.isna(v) else str(int(v))
    )

    grouped = sub.groupby(["occ_code", "sex"], dropna=False)["Weights"].sum().reset_index()
    grouped["weighted_employment_millions"] = grouped["Weights"] / 1_000_000

    total_by_sex = sub.groupby("sex")["Weights"].sum() / 1_000_000
    total_overall = sub["Weights"].sum() / 1_000_000

    rows = []
    for _, r in grouped.iterrows():
        rows.append(
            {
                "occ_code": r["occ_code"],
                "sex": r["sex"],
                "weighted_employment_millions": round(r["weighted_employment_millions"], 4),
                "share_pct_of_sex_total": round(
                    100 * r["weighted_employment_millions"] / total_by_sex[r["sex"]], 4
                ),
            }
        )

    n_codes = sub.loc[sub["occ_code"] != NO_OCC_CODE, "occ_code"].nunique()
    no_occ_total = grouped.loc[grouped["occ_code"] == NO_OCC_CODE, "weighted_employment_millions"].sum()
    print(f"[B5] {label}: total employed = {total_overall:.3f}M across {n_codes} occupation codes "
          f"+ {no_occ_total:.4f}M ({100*no_occ_total/total_overall:.3f}%) with no occupation code")
    print(f"[B5] {label} by sex: " + ", ".join(f"{s}={v:.3f}M" for s, v in total_by_sex.items()))

    return rows, total_overall, total_by_sex


def main():
    df = pd.read_stata(SRC, convert_categoricals=False, columns=NEEDED_COLS)
    df["sex"] = df["S4C5"].map(SEX_MAP)

    own_use = df["S5C10"].isin([3.0, 4.0])
    employed_13th = (
        (df["S5C1"] == 1) | (df["S5C2"] == 1) | (df["S5C3"] == 1) | (df["S5C4"] == 1) | own_use
    )
    employed_19th = employed_13th & ~own_use

    for flag, label, outpath in (
        (employed_19th, "19th ICLS", "output/track_b_employment_19th.csv"),
        (employed_13th, "13th ICLS", "output/track_b_employment_13th.csv"),
    ):
        rows, total, by_sex = tabulate(df, flag, label)
        with open(outpath, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(
                f, fieldnames=["occ_code", "sex", "weighted_employment_millions", "share_pct_of_sex_total"]
            )
            writer.writeheader()
            writer.writerows(rows)
        print(f"[B5] Wrote {len(rows)} rows to {outpath}\n")

    print("[B5] DONE")


if __name__ == "__main__":
    main()
