"""
Design-based standard errors for the headline automation-risk statistics.

SAMPLE DESIGN (LFS 2024-25 annual report, sections 1.7-1.10):
  Stratified two-stage design.
  Strata   - Rural: each administrative district is a stratum in KP, Punjab
             and Sindh; each administrative division is a stratum in
             Balochistan. Urban: each administrative division is a stratum.
  PSUs     - Enumeration blocks, selected with PPS (size = households).
  SSUs     - 12 households per urban PSU, 16 per rural PSU, systematic.

RECOVERING THE DESIGN FROM THE RELEASED FILE:
  The release contains no variable named as a stratum, PSU, replicate or
  design-effect indicator. It does contain EBCode ("BLOCK"), which is the
  PSU: it nests perfectly within Province, Region and Quarter, carries
  exactly 16 households per PSU in rural and 12 in urban as the design
  specifies, and the PSU counts per Province x Region reconcile exactly
  with report Table 1.1 net of the dropped blocks in Table 1.2 (3,759).

  PCode is hierarchically nested geography: digit 1 = province, digits 1-2
  = division (31 distinct), digits 1-3 = district (125 distinct), each
  prefix falling wholly inside one province. That allows the documented
  stratification plan to be reconstructed exactly rather than approximated.

ESTIMATOR:
  Every statistic here is a ratio of weighted totals, R = Y/X. Variance is
  obtained by Taylor linearisation: the linearised value for person i is
  u_i = (y_i - R*x_i)/X, and Var(R) is the variance of the weighted total
  of u under the ultimate-cluster (with-replacement) stratified formula:

      Var = sum_h  n_h/(n_h - 1) * sum_c (t_hc - tbar_h)^2

  with t_hc the weighted sum of u over PSU c in stratum h. The with-
  replacement form ignores the finite population correction, which is
  conservative and standard when the PSU sampling fraction is negligible
  (3,759 blocks out of a national frame of hundreds of thousands).

  The gender gap is a difference of two ratios estimated on the same
  sample, so it is linearised jointly (u_i = u_i^female - u_i^male) rather
  than by combining the two standard errors, which would ignore their
  covariance.
"""
import csv
import math
import statistics as stats
from collections import defaultdict

import pandas as pd

SRC = "microdata/LFS 2024-25.sav web.dta"
NEEDED = ["PCode", "EBCode", "Weights", "Province", "Region",
          "S4C5", "S5C1", "S5C2", "S5C3", "S5C4", "S5C10", "S5C12"]
MANUAL = {"9211": 0.87, "9212": 0.87, "9213": 0.87}
BALOCHISTAN = 4.0
RURAL = 1.0


def build_scored():
    """Scenario (b) scoring: crosswalk matches plus the three manual assignments."""
    soc_by_isco = defaultdict(set)
    with open("output/isco_soc_crosswalk.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            code = row["isco_code"]
            if len(code) == 4 and code.isdigit():
                soc_by_isco[code].add(row["soc_code"])
    fo = {}
    with open("output/frey_osborne_occupations.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            fo[row["soc_code"]] = float(row["probability"])
    scored = {}
    for code, socs in soc_by_isco.items():
        probs = [fo[s] for s in socs if s in fo]
        if probs:
            scored[code] = stats.fmean(probs)
    scored.update(MANUAL)
    return scored


def make_strata(df):
    """Reconstruct the documented stratification plan."""
    pc = df["PCode"].astype(str)
    district = pc.str[:3]
    division = pc.str[:2]
    is_rural = df["Region"] == RURAL
    is_baloch = df["Province"] == BALOCHISTAN
    # rural outside Balochistan -> district; rural Balochistan and all urban -> division
    unit = division.where((~is_rural) | is_baloch, district)
    return df["Region"].astype(int).astype(str) + "_" + unit


def ratio_se(df, ynum, xden, strata, psu):
    """Taylor-linearised SE of R = sum(w*ynum)/sum(w*xden)."""
    w = df["Weights"].to_numpy()
    y = (w * ynum.to_numpy()).sum()
    x = (w * xden.to_numpy()).sum()
    R = y / x
    u = (ynum.to_numpy() - R * xden.to_numpy()) / x
    return R, _total_var(w * u, strata, psu)


def diff_ratio_se(df, y1, x1, y2, x2, strata, psu):
    """Taylor-linearised SE of (sum w*y1/sum w*x1) - (sum w*y2/sum w*x2)."""
    w = df["Weights"].to_numpy()
    Y1, X1 = (w * y1.to_numpy()).sum(), (w * x1.to_numpy()).sum()
    Y2, X2 = (w * y2.to_numpy()).sum(), (w * x2.to_numpy()).sum()
    R1, R2 = Y1 / X1, Y2 / X2
    u = (y1.to_numpy() - R1 * x1.to_numpy()) / X1 - (y2.to_numpy() - R2 * x2.to_numpy()) / X2
    return R1 - R2, _total_var(w * u, strata, psu)


def _total_var(wu, strata, psu):
    """Ultimate-cluster variance of a weighted total, returns (se, n_singleton_strata)."""
    by_psu = defaultdict(float)
    psu_stratum = {}
    for val, h, c in zip(wu, strata, psu):
        by_psu[c] += val
        psu_stratum[c] = h
    clusters_by_stratum = defaultdict(list)
    for c, tot in by_psu.items():
        clusters_by_stratum[psu_stratum[c]].append(tot)

    var = 0.0
    singletons = 0
    for h, totals in clusters_by_stratum.items():
        n = len(totals)
        if n < 2:
            singletons += 1          # contributes zero; reported for transparency
            continue
        mean = sum(totals) / n
        ss = sum((t - mean) ** 2 for t in totals)
        var += n / (n - 1) * ss
    return math.sqrt(var), singletons


def main():
    df = pd.read_stata(SRC, convert_categoricals=False, columns=NEEDED)
    scored = build_scored()

    own_use = df["S5C10"].isin([3.0, 4.0])
    employed_19th = ((df["S5C1"] == 1) | (df["S5C2"] == 1) |
                     (df["S5C3"] == 1) | (df["S5C4"] == 1) | own_use) & ~own_use
    occ = df["S5C12"].apply(lambda v: None if pd.isna(v) else str(int(v)))
    prob = occ.map(lambda c: scored.get(c))
    in_scope = employed_19th & prob.notna()

    df = df.assign(_prob=prob, _scope=in_scope,
                   _female=(df["S4C5"] == 2.0), _male=(df["S4C5"] == 1.0))
    strata = make_strata(df).to_numpy()
    psu = df["EBCode"].to_numpy()

    print(f"[design] PSUs: {len(set(psu))}   strata: {len(set(strata))}")
    sc = df[df["_scope"]]
    print(f"[design] scored-employment respondents: {len(sc):,}  "
          f"weighted {sc['Weights'].sum()/1e6:.3f}M")
    print(f"[design] PSUs containing scored employment: {sc['EBCode'].nunique()}")
    print()

    scope = df["_scope"].astype(float)
    hr = (df["_scope"] & (df["_prob"] > 0.7)).astype(float)
    p_scope = (df["_prob"].fillna(0) * df["_scope"]).astype(float)
    f_scope = (df["_scope"] & df["_female"]).astype(float)
    m_scope = (df["_scope"] & df["_male"]).astype(float)
    pf = (df["_prob"].fillna(0) * f_scope).astype(float)
    pm = (df["_prob"].fillna(0) * m_scope).astype(float)

    rows = []

    R, (se, sg) = ratio_se(df, hr, scope, strata, psu)
    rows.append(("High-risk share, total (>0.7, mean variant)", R * 100, se * 100, sg, "%"))

    R, (se, sg) = ratio_se(df, pm, m_scope, strata, psu)
    rows.append(("Weighted mean probability, male", R, se, sg, ""))

    R, (se, sg) = ratio_se(df, pf, f_scope, strata, psu)
    rows.append(("Weighted mean probability, female", R, se, sg, ""))

    D, (se, sg) = diff_ratio_se(df, pf, f_scope, pm, m_scope, strata, psu)
    rows.append(("Gender gap in weighted mean probability", D, se, sg, ""))

    # SRS comparison for design effect, on the same scored-employment base
    n_eff = int(df["_scope"].sum())

    print("=" * 96)
    print(f"{'Statistic':<46}{'Estimate':>11}{'SE':>10}{'95% CI':>24}{'CV %':>7}")
    print("=" * 96)
    out = []
    for name, est, se, sg, unit in rows:
        lo, hi = est - 1.96 * se, est + 1.96 * se
        cv = abs(100 * se / est) if est else float("nan")
        print(f"{name:<46}{est:>11.4f}{se:>10.4f}   [{lo:>8.4f}, {hi:>8.4f}]{cv:>7.2f}")
        out.append({"statistic": name, "estimate": round(est, 5), "se": round(se, 5),
                    "ci_lower": round(lo, 5), "ci_upper": round(hi, 5),
                    "cv_pct": round(cv, 3), "singleton_strata": sg, "unit": unit})
    print("=" * 96)

    # design effect for the headline share
    p = rows[0][1] / 100
    srs_se = math.sqrt(p * (1 - p) / n_eff) * 100
    deff = (rows[0][2] / srs_se) ** 2
    print(f"\n[deff] headline share: design SE {rows[0][2]:.4f} vs naive SRS SE {srs_se:.4f} "
          f"-> design effect {deff:.2f} (n = {n_eff:,} respondents)")
    print(f"[deff] effective sample size {n_eff/deff:,.0f}")

    with open("output/variance_estimates.csv", "w", newline="", encoding="utf-8") as f:
        wri = csv.DictWriter(f, fieldnames=list(out[0].keys()))
        wri.writeheader()
        wri.writerows(out)
    print("\nWrote output/variance_estimates.csv")


if __name__ == "__main__":
    main()
