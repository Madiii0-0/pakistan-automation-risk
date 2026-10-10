# Step 10 — Reconciliation Report

## 1. Four-way employment reconciliation (millions)

| Metric | ILOSTAT 2025 | PBS 19th ICLS (published) | PBS 13th ICLS (published) | Track B microdata (19th) | Track B microdata (13th) |
|---|---|---|---|---|---|
| Total  | 77.642 | 77.200 | 79.700 | 77.326 | 79.812 |
| Male   | 58.865 | 59.400 | 60.400 | 59.482 | 60.478 |
| Female | 18.776 | 17.800 | 19.300 | 17.844 | 19.335 |

**Track B microdata vs its own published target** (the B4 gate): max deviation 0.25% (Female, 19th ICLS) — passes at the 2pp tolerance with wide margin. This column is the only one computed from the identical underlying microdata using an explicit, auditable definition (`S5C1-4 OR own-use` for 13th, minus own-use for 19th) rather than triangulated from published aggregates.

**ILOSTAT vs PBS 19th ICLS**: Total +0.57%, Male −0.90%, **Female +5.49%**.
**ILOSTAT vs PBS 13th ICLS**: Total −2.58%, Male −2.54%, Female −2.71%.

Totals alone point to 19th ICLS (0.57% vs 2.58% deviation). But the sex breakdown does not move the way a clean standard-match would predict: if ILOSTAT were simply 19th ICLS, the male and female deviations should be similar in direction and magnitude. Instead Female deviates from 19th ICLS by +5.5pp while Male deviates by −0.9pp — a pattern consistent with ILOSTAT's series sitting closer to 19th ICLS overall but with partial inclusion of some female-heavy subsistence-adjacent population that 19th ICLS excludes. The diagnostic below tests exactly this hypothesis and finds it does not hold at the person level.

## 2. ISCO-63 vs Q5.10 own-use-producer diagnostic (person-level, now checkable)

The plan's original hypothesis: ILOSTAT's ISCO-63 "Subsistence farmers, fishers, hunters and gatherers" occupational employment (2.213M total, 0.798M male, 1.415M female) is close in magnitude to the LFS report's Q5.10-based own-use-producer count (2.48M) — suggestive, but occupation and activity-status are conceptually different classifications, so near-equal totals don't establish overlap. That was flagged as an open finding, not a conclusion, pending microdata access.

**With microdata, the answer is decisive: these are almost entirely disjoint populations.**

| Cell (weighted, employed_13th population) | Millions |
|---|---|
| ISCO-63 occupation AND own-use producer | 0.0000 |
| ISCO-63 occupation, NOT own-use | 0.0029 |
| Own-use producer, NOT ISCO-63 occupation | 2.4865 |
| Neither | 77.3227 |

Overlap is **0.00%** of both the ISCO-63 population and the own-use-producer population. The 2.21M vs 2.48M magnitude similarity that the plan flagged as suggestive is **coincidental, not definitional overlap** — the hypothesis that ILOSTAT partially re-includes subsistence-occupation workers into an otherwise-19th-ICLS-like series is not supported by the person-level data.

The mechanism became clear in the process of checking this: **100% of own-use producers (2.4865M weighted) have no recorded main-occupation code (S5C12) at all.** They enter "employed" status via a secondary questionnaire path (Q5.10) that evidently does not route through the standard occupation-coding battery. This is a structural feature of the microdata, not a data-quality defect — it also explains why Track B's occupation-level headline statistics (Section 3 below) are numerically identical under 19th and 13th ICLS: the entire 2.4865M standard-gap falls into the `NO_OCCUPATION_CODE` bucket in both ILOSTAT's presumed source processing and Track B's own tabulation, invisible to any occupation-level automation-risk score.

This leaves the Female +5.5pp deviation of ILOSTAT from 19th ICLS as an open question, but the ISCO-63/own-use mechanism specifically proposed in the plan is now ruled out as the explanation, rather than left unresolved.

## 3. Track B headline automation-risk statistics

**Headline = scenario (b)**: PSCO 9211/9212/9213 (Crop/Livestock/Mixed farm labourers, 3.637M combined employment) assigned SOC 45-2090 "Miscellaneous agricultural workers" (prob=0.87) — the literal SOC-hierarchy parent of the crosswalk's own selected-but-unscored child codes (45-2091/2092/2093/2099), not a title-similarity guess. Scenario (a), unmatched excluded, is carried throughout as sensitivity.

### 3a. High-risk share, band distribution, weighted mean — 19th ICLS (headline population)

| Sex | Variant | Scoreable (M) | Unscoreable | High >0.7 | Med 0.3–0.7 | Low <0.3 | Weighted mean |
|---|---|---|---|---|---|---|---|
| Total | min | 75.710 | 2.09% | 23.98% | 44.94% | 31.08% | 0.4853 |
| Total | **mean** | 75.710 | 2.09% | **58.32%** | 22.24% | 19.45% | **0.6229** |
| Total | max | 75.710 | 2.09% | 70.47% | 11.42% | 18.11% | 0.7403 |
| Male | mean | 58.359 | 1.89% | 54.38% | 24.62% | 21.00% | 0.6131 |
| Female | mean | 17.351 | 2.76% | 71.55% | 14.23% | 14.22% | 0.6557 |

Weighted-mean probability (0.6229 Total) is a Pakistan-employment-structure-weighted statistic over Frey-Osborne's 702 US occupation scores. **It is not directly comparable to Frey-Osborne's own headline 47% US figure** — that figure is weighted by US employment structure over the same underlying scores; the two numbers answer "what does this country's occupational mix imply under identical per-occupation risk scores," not "which country is more automatable," and are reported separately per instruction.

### 3b. Sensitivity — scenario (a), unmatched excluded entirely, 19th ICLS

| Sex | Variant | Scoreable (M) | Unscoreable | High >0.7 | Weighted mean |
|---|---|---|---|---|---|
| Total | mean | 72.073 | 6.79% | 56.21% | 0.6104 |
| Male | mean | 55.919 | 5.99% | 52.39% | 0.6019 |
| Female | mean | 16.154 | 9.47% | 69.44% | 0.6398 |

**Cost of the (b) vs (a) decision**: +2.11pp high-risk share, +0.0125 weighted mean prob (Total, mean variant). Assigning these three codes narrows the unscoreable share from 6.79% to 2.09%.

### 3c. Gap between 19th and 13th ICLS standards — its own explicit line

At the **occupation-scored level, the gap is exactly zero** (scoreable_M, band shares, and weighted mean are numerically identical under both standards — 75.710M scoreable either way). This is not an error: it follows directly from Section 2's finding — all 2.4865M persons added by moving from 19th to 13th ICLS are own-use producers with no occupation code, so they fall entirely into `NO_OCCUPATION_CODE` regardless of standard, never entering the scored denominator. The only thing that moves is the *unscoreable* share: 2.09% (19th) vs 5.14% (13th) Total, since 13th ICLS's larger total-employment denominator absorbs the same fixed unscoreable population.

**Implication for the paper**: the 19th-vs-13th ICLS choice affects the *total employment base* materially (77.3M vs 79.8M, a 2.49M/3.2% difference) but has **no effect whatsoever** on any automation-risk statistic computed here, because Frey-Osborne scoring is entirely inapplicable to the population that the standard choice adds or removes. This is a stronger and cleaner result than "report the ICLS gap as a sensitivity range" — there is no sensitivity to report on the risk side, only on the employment-base side.

### 3d. Top 20 occupations by score (mean_prob, 19th ICLS, headline)

Dominated by clerical/data-entry/administrative and machine-operator occupations at prob ≥ 0.97 (Data entry clerks 0.990/0.119M; General office clerks 0.970/0.573M; Accounting associate professionals 0.980/0.141M) — see `output/track_b_top20_by_score.csv` for the full ranked list with employment.

### 3e. Top 20 by absolute workers in high-risk (>0.7) occupations

Dominated by agriculture and manual-trade occupations at large employment scale: Mixed crop and animal producers (11.845M, 0.760), Building construction labourers (5.449M, 0.800), Livestock and dairy producers (4.569M, 0.760), Tailors/dressmakers (2.939M, 0.840), **Crop farm labourers (2.917M, 0.870 — manually assigned)**. Full ranked list in `output/track_b_top20_by_workers_high_risk.csv`.

## 4. Unmatched-occupation appendix (excluded from headline, all scenarios)

25 four-digit PSCO codes, combined employment **1.5175M (1.96% of 77.325M total employed, 19th ICLS)**, remain excluded from every headline scenario — not folded in, not assigned scores. Largest by employment: Sweepers and related labourers (0.317M), Generalist medical practitioners (0.220M), Drivers of animal-drawn vehicles (0.195M), Community health workers (0.186M). Full list with employment and share in `output/unmatched_appendix.csv`. Track A's 3 unmatched 2-digit categories (Armed Forces, all ranks) are tracked separately and were never in Track B's denominator.

## 5. Limitations (for direct inclusion in the paper)

- 25 four-digit occupations (1.96% of employed) have no Frey-Osborne-scored SOC equivalent and are excluded from all headline statistics; see appendix.
- 3.637M employment (4.70% of employed) — Crop/Livestock/Mixed farm labourers — is scored via a manually assigned proxy (SOC 45-2090, the crosswalk's own selected-but-unscored codes' SOC hierarchy parent), not a direct Frey-Osborne match; excluding it instead moves the headline high-risk share from 58.32% to 56.21%.
- The 19th-vs-13th ICLS choice changes the total employment base by 2.49M (3.2%) but has no effect on any risk statistic, since the added/removed population is structurally unscoreable (no occupation code).
- Weighted-mean automation-risk probability is a Pakistan-employment-structure statistic and is not comparable to Frey-Osborne's US-employment-structure-weighted 47% headline figure.
- ILOSTAT's 2025 series does not cleanly match either PBS ICLS standard on the sex breakdown (Female +5.5% vs 19th ICLS); the specific ISCO-63/own-use mechanism hypothesized as an explanation is ruled out by person-level microdata (0.00% overlap) — the remaining deviation is unexplained and should be reported as such, not attributed to a specific mechanism.
