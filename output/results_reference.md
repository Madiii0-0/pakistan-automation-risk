# Results Reference — Pakistan Automation-Risk Pipeline

Structured reference for every figure quoted in the results discussion. All Track B figures use **scenario (b)** (9211/9212/9213 assigned SOC 45-2090, prob=0.87, point estimate) and **19th ICLS** employment unless a column says otherwise. Source files are relative to `output/`.

**Verification note**: every number below was re-pulled directly from its source file for this document. No discrepancies were found between file values and figures quoted earlier in conversation — all matches are exact to the rounding precision used in discussion (e.g. 5.485% in-file vs "+5.49%" quoted is a rounding-boundary match, not an error). Where a number had only ever been computed inline and not saved, it has been re-computed here and written to a new file (`ref_*.csv` / `ref_*.json`) so every figure below is now file-backed.

---

## 1. Range comparison: 2-digit (Track A) vs 4-digit (Track B)

**File**: `range_comparison_2digit_vs_4digit.csv` (40 rows, one per ISCO 2-digit category; 1 excluded — code 63, zero 4-digit children scored)

| Figure | Value | Represents |
|---|---|---|
| Employment-weighted mean range, 2-digit (Track A) | **0.6962** | Across 39 valid categories, weighted by 2-digit employment |
| Employment-weighted mean range, 4-digit (Track B) | **0.2679** | Employment-weighted mean of each category's 4-digit children's mean range |
| Overall compression | **−61.51%** | (0.2679 − 0.6962) / 0.6962 |

### Watchlist categories (52, 75, 93, 83, 71)

| Code | Title | Employment (M) | 2-digit range | 4-digit w-mean range | Change |
|---|---|---|---|---|---|
| 52 | Sales Workers | 9.9619 | 0.961 | 0.0257 | −0.9353 |
| 75 | Food Processing/Woodworking/Garment/Craft | 4.9855 | 0.9851 | 0.1162 | −0.8689 |
| 93 | Labourers (Mining/Construction/Mfg/Transport) | 7.3124 | 0.874 | 0.361 | −0.5130 |
| 83 | Drivers and Mobile Plant Operators | 4.3200 | 0.951 | 0.8201 | −0.1309 |
| 71 | Building and Related Trades (excl. Electricians) | 1.9622 | 0.937 | 0.1006 | −0.8364 |

83 (Drivers) is the outlier — 4-digit granularity barely compresses its range, unlike the other four watchlist categories, which compress sharply.

---

## 2. Headline high-risk share and weighted mean — scenario (b), 19th ICLS

**File**: `headline_results_track_b.json` → `headline_scenario_b.19th_ICLS`

| Sex | Variant | Scoreable (M) | Unscoreable % | High >0.7 % | Medium 0.3–0.7 % | Low <0.3 % | Weighted mean prob |
|---|---|---|---|---|---|---|---|
| Total | min | 75.710 | 2.088 | 23.982 | 44.940 | 31.079 | 0.4853 |
| Total | mean | 75.710 | 2.088 | **58.316** | 22.240 | 19.445 | **0.6229** |
| Total | max | 75.710 | 2.088 | 70.471 | 11.422 | 18.107 | 0.7403 |
| Male | min | 58.359 | 1.888 | 25.564 | 38.862 | 35.575 | 0.4695 |
| Male | mean | 58.359 | 1.888 | 54.382 | 24.620 | 20.999 | 0.6131 |
| Male | max | 58.359 | 1.888 | 69.594 | 11.069 | 19.337 | 0.7317 |
| Female | min | 17.351 | 2.756 | 18.660 | 65.382 | 15.957 | 0.5383 |
| Female | mean | 17.351 | 2.756 | 71.547 | 14.234 | 14.219 | 0.6557 |
| Female | max | 17.351 | 2.756 | 73.421 | 12.610 | 13.969 | 0.7695 |

**Do not** compare weighted mean prob against Frey-Osborne's US headline 47% — different employment-structure weighting, not a like-for-like statistic (flagged in `headline_results_track_b.json` → `note`).

**Employment-weighted mean range, all scored codes, scenario (b)**: **0.2551** across 345 codes (342 crosswalk-matched + 3 manually assigned at range=0), total employment 75.7098M — `ref_weighted_mean_range_scenario_b.json`.

---

## 3. Sensitivity — scenario (a), unmatched excluded entirely, 19th ICLS

**File**: `headline_results_track_b.json` → `sensitivity_scenario_a.19th_ICLS`

| Sex | Variant | Scoreable (M) | Unscoreable % | High >0.7 % | Weighted mean prob |
|---|---|---|---|---|---|
| Total | min | 72.073 | 6.792 | 20.146 | 0.4659 |
| Total | mean | 72.073 | 6.792 | 56.212 | 0.6104 |
| Total | max | 72.073 | 6.792 | 68.981 | 0.7338 |
| Male | mean | 55.919 | 5.989 | 52.392 | 0.6019 |
| Female | mean | 16.154 | 9.469 | 69.437 | 0.6398 |

**Cost of (b) vs (a)**, Total mean variant: **+2.10pp** high-risk share (56.212% → 58.316%), **+0.0125** weighted mean prob.

---

## 4. Threshold table (0.6 / 0.7 / 0.8), Total/Male/Female, mean variant

**File**: `ref_threshold_table.csv`

| Threshold | Total % | Male % | Female % | Male − Female gap |
|---|---|---|---|---|
| 0.6 | 63.183 | 59.499 | 75.559 | −16.060pp |
| 0.7 | 58.316 | 54.382 | 71.547 | −17.165pp |
| 0.8 | 26.627 | 27.918 | 22.298 | +5.620pp |

Gap sign flips between 0.7 and 0.8 — see fig2. Not robust to threshold choice.

---

## 5. Agricultural exclusion ladder

**File**: `ref_agricultural_exclusion_ladder.csv` (threshold 0.7, mean variant)

| Scenario | Total % | Male % | Female % | Employment excluded (Total M) |
|---|---|---|---|---|
| Baseline (none excluded) | 58.316 | 54.382 | 71.547 | 0.000 |
| Exclude 6130 | 50.583 | 48.297 | 60.100 | 11.845 |
| Exclude 6130 + 6121 | 46.783 | 47.089 | 45.029 | 16.414 |
| Exclude all 5 ag. codes (6130, 6121, 9211, 8341, 9213) | 43.253 | 44.309 | 36.766 | 20.101 |

6130 alone (11.845M, mean=0.76) accounts for a 7.7pp drop in the Total headline. Female share crosses below Male share once both 6130 and 6121 are removed.

---

## 6. Top 10 high-risk occupations, share of high-risk population

**File**: `ref_top10_high_risk_concentration.csv`. Total high-risk population: **44.1506M** (141 occupations, threshold >0.7, mean variant).

| Rank | Code | Title | Employment (M) | Share of HR pop % | Cumulative % |
|---|---|---|---|---|---|
| 1 | 6130 | Mixed crop and animal producers | 11.845 | 26.831 | 26.831 |
| 2 | 9313 | Building construction labourers | 5.449 | 12.344 | 39.175 |
| 3 | 6121 | Livestock and dairy producers | 4.569 | 10.350 | 49.525 |
| 4 | 7531 | Tailors, dressmakers, furriers and hatters | 2.939 | 6.658 | 56.183 |
| 5 | 9211 | Crop farm labourers *(manually assigned)* | 2.917 | 6.608 | 62.791 |
| 6 | 5223 | Shop sales assistants | 1.468 | 3.325 | 66.116 |
| 7 | 9329 | Manufacturing labourers n.e.c. | 1.247 | 2.825 | 68.941 |
| 8 | 7112 | Bricklayers and related workers | 1.083 | 2.453 | 71.394 |
| 9 | 5212 | Street food salespersons | 0.790 | 1.789 | 73.183 |
| 10 | 7533 | Sewing, embroidery and related workers | 0.779 | 1.764 | 74.947 |

Top 3 = 49.5% of the high-risk population.

---

## 7. Female min→mean decomposition — 6130 and 6121

**Files**: `ref_female_swing_summary.json`, `ref_female_decomposition.csv` (35 flipping codes)

| Figure | Value |
|---|---|
| Total scoreable female employment | 17.3513M |
| Female high-risk share at min | 18.660% |
| Female high-risk share at mean | 71.547% |
| Swing | 52.887pp |
| Codes flipping not-high(min)→high(mean) | 35 |
| Employment in flipping codes | 9.1765M (52.86% of scoreable female employment) |
| **6130 contribution to swing** | **28.681pp** |
| **6121 contribution to swing** | **19.559pp** |
| **6130 + 6121 combined** | **48.240pp of the 52.887pp swing (91.2% of the swing)** |

---

## 8. ICLS reconciliation and ISCO-63 / Q5.10 diagnostic

**Files**: `step10_reconciliation_table.csv`, `step10_isco63_q510_diagnostic.json`, `b4_reconciliation_summary.csv`

### Four-way employment reconciliation (millions)

| Sex | ILOSTAT 2025 | PBS 19th (published) | PBS 13th (published) | Microdata 19th (Track B) | Microdata 13th (Track B) |
|---|---|---|---|---|---|
| Total | 77.641546 | 77.2 | 79.7 | 77.326 | 79.812 |
| Male | 58.865283 | 59.4 | 60.4 | 59.482 | 60.478 |
| Female | 18.776263 | 17.8 | 19.3 | 17.844 | 19.335 |

| Comparison | Total | Male | Female |
|---|---|---|---|
| ILOSTAT vs 19th ICLS | +0.572% | −0.900% | +5.485% |
| ILOSTAT vs 13th ICLS | −2.583% | −2.541% | −2.714% |
| Microdata 19th vs PBS published (B4 gate) | +0.163% | +0.138% | +0.246% |
| Microdata 13th vs PBS published (B4 gate) | +0.141% | +0.129% | +0.179% |

Max absolute B4 gate deviation across all 6 cells: **0.246%** (Female, 19th ICLS) — well within the 2pp tolerance.

### ISCO-63 vs Q5.10 own-use-producer diagnostic (person-level, weighted, millions)

| Cell | Value |
|---|---|
| ISCO-63 occupation total | 0.0029M |
| Q5.10 own-use-producer total | 2.4865M |
| **Overlap (both)** | **0.0000M (0.00%)** |
| Own-use producers WITH an occupation code | 0.0000M (0.00%) |
| Own-use producers WITHOUT an occupation code | 2.4865M (**100.00%**) |

**Finding**: the 2.21M (ILOSTAT ISCO-63) vs 2.48M (LFS report own-use) magnitude similarity flagged in the plan as suggestive is coincidental, not overlap — confirmed at 0.00% person-level overlap. Mechanism: own-use producers are routed through a questionnaire path that skips the occupation-coding battery entirely.

### 19th vs 13th ICLS gap in Track B risk statistics

At the occupation-scored level the gap is **exactly zero** — scoreable_M, band shares, and weighted mean prob are numerically identical under both standards (75.710M either way), because all 2.4865M persons 13th ICLS adds over 19th are the same own-use producers with no occupation code (100% overlap with the "no code" population, confirmed above). Only the *unscoreable* share moves: 2.088% (19th) vs 5.139% (13th), Total.

---

## 9. Unmatched-occupation exclusions

**Files**: `unmatched_appendix.csv` (25 codes), `unmatched_occupations.csv` (28 Track B + 3 Track A)

| Figure | Value |
|---|---|
| 25 remaining unmatched 4-digit codes — combined employment | **1.5175M** |
| — share of total employed (77.325M, 19th ICLS) | **1.9625%** |
| 3 codes resolved this round (9211/9212/9213) — combined employment | 3.637M (excluded from the 25-code appendix; scored via manual assignment in headline scenario b) |
| Track A unmatched (Armed Forces, 3 codes, 2-digit) | Not in Track B's denominator; tracked separately |

Largest 5 in the appendix: 9613 Sweepers (0.3169M), 2211 Generalist medical practitioners (0.2197M), 9332 Drivers of animal-drawn vehicles (0.1954M), 3253 Community health workers (0.1861M), 8159 Textile/fur/leather machine operators (0.1139M).

---

## 10. Employment totals under both ICLS standards

**Files**: `b4_reconciliation_summary.csv`, `track_b_employment_19th.csv`, `track_b_employment_13th.csv`

| Standard | Total (M) | Male (M) | Female (M) | Published (Total/M/F) |
|---|---|---|---|---|
| 19th ICLS (microdata) | 77.326 | 59.482 | 17.844 | 77.2 / 59.4 / 17.8 |
| 13th ICLS (microdata) | 79.812 | 60.478 | 19.335 | 79.7 / 60.4 / 19.3 |
| Gap (13th − 19th) | **2.486** | 0.996 | 1.491 | own-use producers, 100% with no occupation code |

---

## Figures

| File | Content |
|---|---|
| `figures/fig1_range_comparison.png` | 2-digit vs 4-digit range, top 20 categories by employment, watchlist marked in caption |
| `figures/fig2_threshold_sensitivity.png` | Total/Male/Female high-risk share at 0.6/0.7/0.8 |
| `figures/fig3_concentration_curve.png` | Cumulative share of high-risk population by occupation, ranked by employment |
| `figures/fig4_agricultural_ladder.png` | High-risk share across the 4-step agricultural exclusion sequence |

All at 300 dpi, serif/grayscale, no color decoration.
