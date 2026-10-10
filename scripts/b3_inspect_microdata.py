"""
B3 - Locate and inspect the key LFS 2024-25 microdata variables needed for
Track B, without assuming precision or filters that haven't been checked.

Loads only the needed columns from the 436MB .dta file for memory
efficiency. Reports, for each variable that matters downstream:
- occupation code digit-length distribution (main job AND subsidiary job)
  -- confirms/quantifies the 4-digit claim rather than assuming it
- weight variable basic stats
- Fstatus / PCode distinct values, to determine what filtering (if any)
  is needed to isolate valid/final employed-person records
- sex, province coding
"""
import pandas as pd

SRC = "microdata/LFS 2024-25.sav web.dta"

NEEDED_COLS = [
    "PCode", "Fstatus", "Weights", "Province", "Region", "Quarter",
    "S4C4", "S4C5", "S4C6",
    "S5C1", "S5C2", "S5C3", "S5C4", "S5C8", "S5C9", "S5C10", "S5C11",
    "S5C12", "S5C13",
    "S5C25", "S5C26", "S5C27", "S5C28",
]


def digit_len_distribution(series):
    s = series.dropna()
    s = s[s != 0]
    lengths = s.astype("int64").astype(str).str.len()
    return lengths.value_counts().sort_index()


def main():
    print(f"[B3] Loading columns: {NEEDED_COLS}")
    df = pd.read_stata(SRC, convert_categoricals=False, columns=NEEDED_COLS)
    print(f"[B3] Loaded {len(df):,} rows")

    print("\n[B3] --- PCode (Processing Code) distinct values ---")
    print(df["PCode"].value_counts(dropna=False))

    print("\n[B3] --- Fstatus distinct values ---")
    print(df["Fstatus"].value_counts(dropna=False))

    print("\n[B3] --- S4C4 (Present Status) distinct values ---")
    print(df["S4C4"].value_counts(dropna=False))

    print("\n[B3] --- Weights: basic stats ---")
    print(df["Weights"].describe())
    print("Weights nulls:", df["Weights"].isna().sum())

    print("\n[B3] --- S4C5 (sex) distinct values ---")
    print(df["S4C5"].value_counts(dropna=False))

    print("\n[B3] --- Province distinct values ---")
    print(df["Province"].value_counts(dropna=False))

    print("\n[B3] --- Region distinct values ---")
    print(df["Region"].value_counts(dropna=False))

    print("\n[B3] --- S5C1..S5C4 (employment screening) value counts ---")
    for c in ["S5C1", "S5C2", "S5C3", "S5C4"]:
        print(f"  {c}:")
        print(df[c].value_counts(dropna=False).to_string())

    print("\n[B3] --- S5C10 (products intended for -- own-use producer flag) ---")
    print(df["S5C10"].value_counts(dropna=False))

    print("\n[B3] --- S5C11 (Status of Employment) ---")
    print(df["S5C11"].value_counts(dropna=False))

    print("\n[B3] --- S5C12 (Major Occupation, MAIN job) digit-length distribution ---")
    print(digit_len_distribution(df["S5C12"]))
    n_main_occ_nonnull = df["S5C12"].notna().sum()
    n_main_occ_unique = df["S5C12"].dropna().nunique()
    print(f"  non-null S5C12 records: {n_main_occ_nonnull:,}")
    print(f"  unique S5C12 codes: {n_main_occ_unique}")

    print("\n[B3] --- S5C25 (Any subsidiary work) ---")
    print(df["S5C25"].value_counts(dropna=False))

    print("\n[B3] --- S5C27 (Subsidiary Occupation) digit-length distribution ---")
    print(digit_len_distribution(df["S5C27"]))
    n_sub_occ_nonnull = df["S5C27"].notna().sum()
    print(f"  non-null S5C27 records: {n_sub_occ_nonnull:,}")

    print("\n[B3] DONE -- inspection complete, no assertions in this step by design")
    print("    (this step is exploratory; B4 will assert the reconciliation)")


if __name__ == "__main__":
    main()
