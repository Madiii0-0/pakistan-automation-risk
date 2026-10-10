# Occupational Automation Risk in Pakistan

Code and derived data for *Estimating Occupational Automation Risk in Pakistan: Granularity, Crosswalk Coverage and the Limits of Frey-Osborne Estimates*.

The paper maps Frey and Osborne's (2017) occupation-level computerisation probabilities onto Pakistan's Labour Force Survey 2024-25 microdata at the 4-digit ISCO-08 level, via the US Bureau of Labor Statistics ISCO-to-SOC crosswalk, and compares the result against a 2-digit baseline built from ILOSTAT tabulations.

Its substantive contribution is less the headline number than the demonstration of how much that number depends on choices usually treated as technical: occupational granularity, the high-risk threshold, and the coverage of the crosswalk itself.

## Headline results

| Statistic | Value |
|---|---|
| High-risk employment share (>0.7, mean variant, 19th ICLS) | 58.32% (SE 0.30) |
| Employment-weighted mean probability | 0.623 |
| Scored employment | 75.71M workers across 345 occupations |
| Range compression, 2-digit to 4-digit | 0.668 to 0.255 (−61.8%) |
| Share of scored employment matching only 1-2 US occupations | 71.8% |

Three occupations hold half the high-risk population; two of them are agricultural codes scoring 0.76, so moving the threshold to 0.8 cuts the share to 26.6%. An apparent 17-point gender gap in high-risk share reverses sign at the same threshold, while the threshold-free weighted mean probability differs between women and men by only 0.043 (SE 0.0026).

## Repository layout

```
scripts/     pipeline, in the order described below
output/      all derived data: extracted sources, scored tables,
             results, reference tables, and figures
output/figures/   the four paper figures, PNG (300 dpi) and PDF
```

## Data

### What is in this repository

Everything in `output/` is derived data produced by the scripts: extracted and cleaned versions of the public source classifications, the occupation-level scoring tables, and the result tables behind every number in the paper.

### What is not, and where to get it

**The PBS Labour Force Survey 2024-25 microdata is not redistributed here.** It is the property of the Pakistan Bureau of Statistics and is published by them directly. Download it from:

- Landing page: <https://www.pbs.gov.pk/labour-force-statistics>
- The analysis used the Stata release, `LFS-2024-25-STATA.zip`

Place the unpacked `.dta` file at `microdata/LFS 2024-25.sav web.dta` relative to the repository root. The scripts expect exactly that path. No registration was required at the time of access (September 2025).

The following raw source files are also not redistributed, because they are third-party publications rather than this project's output. Each script that needs one documents where it comes from:

| File | Needed by | Source |
|---|---|---|
| `frey_osborne.pdf` | `a2` | Frey & Osborne (2017), *Technological Forecasting and Social Change* 114, 254-280 |
| `crosswalk.xls` | `a3` | BLS ISCO-08 to 2010 SOC crosswalk (US government, public domain) |
| `isco_structure.xlsx` | `a4` | ILO ISCO-08 structure and definitions |
| `ilostat_pakistan.csv` | `a1` | ILOSTAT indicator `EMP_TEMP_SEX_OC2_NB_A` |
| `psco_codes.pdf` | `b1` | PBS Pakistan Standard Classification of Occupations 2015 |
| `lfs_2024_25.pdf` | reference | PBS Labour Force Survey 2024-25 Annual Report |

### Provenance note on derived files

`output/frey_osborne_occupations.csv` and `output/isco_structure.csv` are extractions from copyrighted third-party publications (Frey & Osborne's appendix and the ILO's ISCO-08 structure file respectively), retained here as the minimum needed for computational reproducibility. Anyone reusing them should cite the original sources rather than this repository.

## Pipeline

The pipeline has two tracks that converge. **Track A** (2-digit, ILOSTAT) is a complete standalone baseline that needs no microdata. **Track B** (4-digit, microdata) is the upgrade that produces the paper's headline results.

### Track A — 2-digit baseline

| Script | Does | Writes |
|---|---|---|
| `a1_filter_ilostat.py` | Filters the multi-country ILOSTAT dump to Pakistan; verifies Male+Female=Total | `ilostat_pakistan_filtered.csv` |
| `a2_extract_frey_osborne.py` | Extracts the 702 scored SOC occupations from the Frey-Osborne appendix PDF | `frey_osborne_occupations.csv` |
| `a3_extract_crosswalk.py` | Extracts the BLS ISCO-SOC crosswalk; flags one-to-many rows and the 14 weak matches | `isco_soc_crosswalk.csv` |
| `a4_extract_isco_structure.py` | Extracts the official ISCO-08 hierarchy (10/43/130/436) | `isco_structure.csv` |
| `a5_score_2digit.py` | Rolls the crosswalk up to 2-digit by **union** of child SOC matches; scores min/mean/max/SD/range | `track_a_scored.csv`, `unmatched_occupations.csv` |
| `a6_headline_stats.py` | Track A headline statistics by sex and variant | `headline_results_track_a.json`, `track_a_top_*.csv` |

`a1`-`a4` are independent and can run in any order. `a5` needs `a2`, `a3`, `a4`. `a6` needs `a1`, `a5`.

### Track B — 4-digit, microdata

| Script | Does | Writes |
|---|---|---|
| `b1_extract_psco.py` | Parses the PSCO-2015 codebook PDF (handles multi-line title wrapping) | `psco_codes.csv`, `psco_structure_all_levels.csv` |
| `b2_psco_isco_identity.py` | Tests PSCO ≡ ISCO-08 at unit-group level against the official structure | `psco_isco_identity_check.csv` |
| `b3_inspect_microdata.py` | Exploratory: variable locations, occupation-code digit depth, weight stats. No assertions by design | console only |
| `b4_reconciliation_gate.py` | **Go/no-go gate.** Reconstructs employment under both ICLS standards and reconciles against published totals | `b4_reconciliation_summary.csv` |
| `b5_tabulate_4digit.py` | Weighted employment by 4-digit occupation and sex, both standards, main job only | `track_b_employment_19th.csv`, `track_b_employment_13th.csv` |
| `b6_score_4digit.py` | Scores each 4-digit occupation; builds the 2-digit vs 4-digit range comparison | `track_b_scored.csv`, `range_comparison_2digit_vs_4digit.csv` |
| `b6b_unmatched_headline_sensitivity.py` | Three-way test of the unmatched-occupation assignment decision | `b6b_unmatched_sensitivity.json` |
| `b7_final_track_b_headline.py` | Final headline statistics, both standards, plus the excluded-occupation appendix | `headline_results_track_b.json`, `unmatched_appendix.csv`, `track_b_top20_*.csv` |

Track B is sequential from `b3` onward. `b4` is the gate: it must reconcile before anything downstream is trusted.

### Shared analysis and robustness

| Script | Does | Writes |
|---|---|---|
| `step10_reconciliation.py` | Four-way employment reconciliation; ISCO-63 vs Q5.10 own-use diagnostic | `step10_reconciliation_table.csv`, `step10_isco63_q510_diagnostic.json`, `reconciliation_report.md` |
| `rebuild_range_comparison_scenario_b.py` | Rebuilds the range comparison under scenario (b) scoring, so figures and headline share one basis | `range_comparison_2digit_vs_4digit_scenario_b.csv` |
| `final_reference_tables.py` | Threshold sensitivity, agricultural exclusion ladder, concentration, female decomposition | `ref_threshold_table.csv`, `ref_agricultural_exclusion_ladder.csv`, `ref_top10_high_risk_concentration.csv`, `ref_female_*` |
| `coverage_and_counts.py` | Crosswalk-coverage tables and unweighted respondent counts per occupation | `ref_match_count_distribution.csv`, `ref_single_match_codes*.csv`, `ref_respondent_counts.csv`, and three more |
| `check3_weak_match_sensitivity.py` | Recomputes the headline with the 14 BLS weak matches removed | console |
| `check_broad_match_decomposition.py` | Decomposes the effect of generic supervisory SOC codes matched across many ISCO codes | `range_comparison_combined_7soc_removal.csv` |
| `variance_estimation.py` | Design-based standard errors (see below) | `variance_estimates.csv` |
| `make_figures.py` | The four paper figures at 300 dpi, PNG and PDF | `output/figures/` |

### Standard errors

`variance_estimation.py` computes design-based standard errors. The released microdata contains no variable named as a stratum, PSU, replicate weight or design effect, but the design is recoverable: `EBCode` is the primary sampling unit, and `PCode` is hierarchically nested geography (digit 1 province, digits 1-2 division, digits 1-3 district) that reproduces the stratification plan documented in the report's section 1.9.

The reconstruction is validated against PBS's own published coefficients of variation (report p. 202): this code returns 0.292% for total persons against PBS's 0.292%, and 0.437% for employed persons against PBS's 0.438%.

Variances use Taylor linearisation with the ultimate-cluster estimator. The gender gap is linearised jointly, not combined from two separate standard errors, because both ratios come from the same sample.

## Reproducing

Requires Python 3.11+.

```bash
pip install -r requirements.txt

# Track A needs no microdata
python scripts/a1_filter_ilostat.py
python scripts/a2_extract_frey_osborne.py
python scripts/a3_extract_crosswalk.py
python scripts/a4_extract_isco_structure.py
python scripts/a5_score_2digit.py
python scripts/a6_headline_stats.py

# Track B needs the PBS microdata in place
python scripts/b1_extract_psco.py
python scripts/b2_psco_isco_identity.py
python scripts/b4_reconciliation_gate.py      # must pass before continuing
python scripts/b5_tabulate_4digit.py
python scripts/b6_score_4digit.py
python scripts/b6b_unmatched_headline_sensitivity.py
python scripts/b7_final_track_b_headline.py

# analysis, robustness, figures
python scripts/step10_reconciliation.py
python scripts/rebuild_range_comparison_scenario_b.py
python scripts/final_reference_tables.py
python scripts/coverage_and_counts.py
python scripts/variance_estimation.py
python scripts/make_figures.py
```

All scripts are run from the repository root and write to `output/`. `b6_score_4digit.py` appends to `unmatched_occupations.csv`, so re-running the full pipeline from a clean `a5` is the safe way to regenerate it.

## Scoring conventions

- **Scenario (b)**, used for all headline results, assigns SOC 45-2090 (0.87) to the three agricultural labourer codes 9211/9212/9213, whose crosswalk matches fall outside the Frey-Osborne scored set. Scenario (a), excluding them, is reported throughout as sensitivity.
- **min / mean / max** are the minimum, mean and maximum across an occupation's matched SOC codes. They are bounds on the one-to-many matching problem, not a confidence interval. Narrow bounds frequently mean *few matches*, not agreement between matches — `ref_match_count_distribution.csv` is the diagnostic for this.
- **19th ICLS** is the headline employment standard; 13th ICLS is carried as robustness. The choice changes total employment by 2.49M but no risk statistic, because the workers the standards disagree about have no occupation code.
- Every manual judgement call in the mapping is logged in `output/appendix_a_mapping_decisions.csv`.

## Known limitations

Documented at length in the paper; the ones that matter most for anyone reusing this code:

- Frey-Osborne scores describe US occupations as assessed in 2013 and predate generative AI.
- Crosswalk coverage is thin and uneven. 71.8% of scored employment rests on one or two matches, and for 12.75M workers the sole match is a generic supervisory or managerial SOC code that scores low by construction.
- 180 of the 345 scored occupations rest on fewer than 30 unweighted respondents, though together these hold only 1.89% of scored employment. `ref_respondent_counts.csv` flags them.
- 25 occupations covering 1.52M workers have no Frey-Osborne match at all and are excluded from every scenario.

## Citing

Cite the paper. Please also cite the original sources for any derived file you reuse: Frey & Osborne (2017) for the probabilities, the BLS for the crosswalk, the ILO for ISCO-08, and the Pakistan Bureau of Statistics for the Labour Force Survey.
