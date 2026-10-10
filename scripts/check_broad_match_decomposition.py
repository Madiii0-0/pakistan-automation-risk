"""
Decomposition of generic/supervisory broad-match SOC codes' effect on
Track A (2-digit) and Track B (4-digit) automation-risk scores, following
up on the 53-1031/category-83 finding. Runs the same before/after removal
analysis for each named SOC (or SOC group), plus a combined 7-code removal,
plus the fully recomputed 2-digit vs 4-digit range comparison under that
combined removal.
"""
import csv
import statistics as stats
from collections import defaultdict

CROSSWALK = "output/isco_soc_crosswalk.csv"
FREY_OSBORNE = "output/frey_osborne_occupations.csv"
EMP_19TH = "output/track_b_employment_19th.csv"
ISCO_STRUCTURE = "output/isco_structure.csv"
PSCO_TITLES = "output/psco_codes.csv"

MANUAL = {"9211": 0.87, "9212": 0.87, "9213": 0.87}

SOC_NAMES = {
    "53-1031": "First-line supervisors of transportation",
    "45-1011": "First-line supervisors of farming, fishing, forestry",
    "49-1011": "First-line supervisors of mechanics, installers, repairers",
    "39-1021": "First-line supervisors of personal service workers",
    "41-1012": "First-line supervisors of non-retail sales workers",
    "11-1021": "General and operations managers",
    "11-9199": "Managers, all other",
}
ALL_SEVEN = set(SOC_NAMES.keys())

# --- load static data once ---
crosswalk_rows = []
with open(CROSSWALK, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        crosswalk_rows.append(row)

fo_by_soc = {}
with open(FREY_OSBORNE, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        fo_by_soc[row["soc_code"]] = float(row["probability"])

isco_2digit_titles = {}
with open(ISCO_STRUCTURE, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        if row["level"] == "2":
            isco_2digit_titles[row["isco_code"]] = row["title"]

titles_4d = {}
with open(PSCO_TITLES, encoding="utf-8") as f:
    for row in csv.DictReader(f):
        titles_4d[row["psco_4digit"]] = row["unit_title"]

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


def build_4digit(excluded_socs):
    isco_by_soc_map = defaultdict(set)
    for r in crosswalk_rows:
        code = r["isco_code"]
        if len(code) == 4 and code.isdigit() and r["soc_code"] not in excluded_socs:
            isco_by_soc_map[code].add(r["soc_code"])
    scored = {}
    for code, socs in isco_by_soc_map.items():
        probs = [fo_by_soc[s] for s in socs if s in fo_by_soc]
        if probs:
            scored[code] = {"min": min(probs), "mean": stats.fmean(probs), "max": max(probs)}
    for c, p in MANUAL.items():
        scored[c] = {"min": p, "mean": p, "max": p}
    return scored


def build_2digit(excluded_socs):
    soc_by_2digit = defaultdict(set)
    for r in crosswalk_rows:
        if r["soc_code"] in excluded_socs:
            continue
        two = r["isco_code"][:2]
        soc_by_2digit[two].add(r["soc_code"])
    scored = {}
    for code, title in isco_2digit_titles.items():
        probs = [fo_by_soc[s] for s in soc_by_2digit.get(code, set()) if s in fo_by_soc]
        if probs:
            scored[code] = {"min": min(probs), "mean": stats.fmean(probs), "max": max(probs)}
    return scored


def touched_codes(soc_set):
    codes = set()
    for r in crosswalk_rows:
        if r["soc_code"] in soc_set and len(r["isco_code"]) == 4 and r["isco_code"].isdigit():
            codes.add(r["isco_code"])
    return codes


def hr_wmean(emp_dict, scored, variant, thr=0.7):
    denom = sum(emp_dict.get(c, 0.0) for c in scored)
    num = sum(emp_dict.get(c, 0.0) for c in scored if scored[c][variant] > thr)
    wsum = sum(emp_dict.get(c, 0.0) * scored[c][variant] for c in scored)
    return (100 * num / denom if denom else None), (wsum / denom if denom else None), denom


def report_removal(label, soc_set):
    print(f"\n{'='*100}")
    print(f"REMOVAL: {label}  -> SOCs: {sorted(soc_set)}")
    print("=" * 100)

    scored_base = build_4digit(set())
    scored_after = build_4digit(soc_set)
    codes = sorted(touched_codes(soc_set))

    print(f"\n-- Per-code min/mean/max, before -> after ({len(codes)} codes touched) --")
    cat_emp_before = defaultdict(float)
    cat_wsum_before = defaultdict(float)
    cat_emp_after = defaultdict(float)
    cat_wsum_after = defaultdict(float)
    for c in codes:
        e = emp_t.get(c, 0.0)
        b = scored_base.get(c)
        a = scored_after.get(c)
        two = c[:2]
        title = titles_4d.get(c, "")
        if b:
            cat_emp_before[two] += e
            cat_wsum_before[two] += (b["max"] - b["min"]) * e
        if a:
            cat_emp_after[two] += e
            cat_wsum_after[two] += (a["max"] - a["min"]) * e
        b_str = f"{b['min']:.3f}/{b['mean']:.3f}/{b['max']:.3f} (r={b['max']-b['min']:.3f})" if b else "UNMATCHED"
        a_str = f"{a['min']:.3f}/{a['mean']:.3f}/{a['max']:.3f} (r={a['max']-a['min']:.3f})" if a else "DROPS TO UNMATCHED"
        print(f"  {c} {title[:38]:<38} emp={e:.4f}M  before={b_str:<32} after={a_str}")

    print(f"\n-- Category employment-weighted mean range, before -> after --")
    for two in sorted(set(list(cat_emp_before.keys()) + list(cat_emp_after.keys()))):
        wb = cat_wsum_before[two] / cat_emp_before[two] if cat_emp_before[two] else None
        wa = cat_wsum_after[two] / cat_emp_after[two] if cat_emp_after[two] else None
        title = isco_2digit_titles.get(two, "")
        wb_s = f"{wb:.4f}" if wb is not None else "n/a"
        wa_s = f"{wa:.4f}" if wa is not None else "n/a"
        delta = f"{wa-wb:+.4f}" if (wb is not None and wa is not None) else "n/a"
        print(f"  {two} {title[:40]:<40} before={wb_s}  after={wa_s}  delta={delta}")

    print(f"\n-- Headline effect (scenario b, 19th ICLS): baseline -> after removal --")
    print(f"{'Variant':<8}{'Sex':<8}{'HR% before':>12}{'HR% after':>12}{'d HR pp':>10}{'WM before':>11}{'WM after':>11}{'d WM':>9}")
    for variant in ("min", "mean", "max"):
        for sexname, d in (("Total", emp_t), ("Male", emp_m), ("Female", emp_f)):
            hr_b, wm_b, _ = hr_wmean(d, scored_base, variant)
            hr_a, wm_a, _ = hr_wmean(d, scored_after, variant)
            print(f"{variant:<8}{sexname:<8}{hr_b:>11.3f}%{hr_a:>11.3f}%{hr_a-hr_b:>+10.3f}{wm_b:>11.4f}{wm_a:>11.4f}{wm_a-wm_b:>+9.4f}")

    return scored_after


# --- individual / grouped removals ---
report_removal("45-1011 (First-line supervisors of farming/fishing/forestry) on category 61", {"45-1011"})
report_removal("49-1011 (First-line supervisors of mechanics/installers/repairers)", {"49-1011"})
report_removal("39-1021 + 41-1012 + 11-1021 + 11-9199 (combined generic supervisory/catch-all)",
                {"39-1021", "41-1012", "11-1021", "11-9199"})

# --- combined 7-code removal ---
scored_4d_combined = report_removal("ALL SEVEN combined (53-1031, 45-1011, 49-1011, 39-1021, 41-1012, 11-1021, 11-9199)", ALL_SEVEN)

# --- full 2-digit vs 4-digit comparison under combined removal ---
print(f"\n{'='*100}")
print("FULL 2-DIGIT VS 4-DIGIT RANGE COMPARISON UNDER COMBINED 7-SOC REMOVAL")
print("=" * 100)

scored_2d_combined = build_2digit(ALL_SEVEN)
scored_4d_base = build_4digit(set())
scored_2d_base = build_2digit(set())

children_by_2digit = defaultdict(list)
for c, s in scored_4d_combined.items():
    children_by_2digit[c[:2]].append((c, s))

rows_out = []
for two, title in sorted(isco_2digit_titles.items()):
    a_before = scored_2d_base.get(two)
    a_after = scored_2d_combined.get(two)
    children = children_by_2digit.get(two, [])
    child_emp_total = sum(emp_t.get(c, 0.0) for c, s in children)
    wmean_range_4d = (sum((s["max"] - s["min"]) * emp_t.get(c, 0.0) for c, s in children) / child_emp_total
                       if child_emp_total > 0 else None)
    rows_out.append({
        "isco_2digit": two, "title": title,
        "employment_millions": round(child_emp_total, 4),
        "range_2digit_before": round(a_before["max"] - a_before["min"], 4) if a_before else None,
        "range_2digit_after": round(a_after["max"] - a_after["min"], 4) if a_after else None,
        "wmean_range_4digit_after": round(wmean_range_4d, 4) if wmean_range_4d is not None else None,
    })

with open("output/range_comparison_combined_7soc_removal.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows_out[0].keys()))
    writer.writeheader()
    writer.writerows(rows_out)
print("Wrote output/range_comparison_combined_7soc_removal.csv")

valid = [r for r in rows_out if r["wmean_range_4digit_after"] is not None and r["range_2digit_after"] is not None]
emp_total = sum(r["employment_millions"] for r in valid)
w2d = sum(r["range_2digit_after"] * r["employment_millions"] for r in valid) / emp_total
w4d = sum(r["wmean_range_4digit_after"] * r["employment_millions"] for r in valid) / emp_total
pct = 100 * (w4d - w2d) / w2d
print(f"\nValid categories (both sides scoreable after removal): {len(valid)} of {len(rows_out)}")
print(f"Total employment: {emp_total:.4f}M")
print(f"Employment-weighted mean range, 2-digit (SOCs removed): {w2d:.4f}")
print(f"Employment-weighted mean range, 4-digit (SOCs removed): {w4d:.4f}")
print(f"Percent compression: {pct:.2f}%")
print(f"\nCompare to scenario (b) baseline (SOCs NOT removed): 0.6685 / 0.2551 / -61.85%")
