"""
Four reference figures at 300 dpi (PNG + PDF), plain academic styling.

Revision notes (final round before submission):
- fig1: now uses scenario (b) scoring for the 4-digit side (see
  rebuild_range_comparison_scenario_b.py) so category 92's employment
  reflects the manually-assigned 9211/9212/9213. Shows all 39 categories
  with scoreable children (was top-20-by-employment, which is why 92
  [rank 25 under the stale pre-scenario-b employment figure] and 14's
  near-zero bar looked like missing data). Category 63 is excluded with
  a stated reason in the caption -- genuinely zero scoreable employment,
  not a plotting artifact. Y-axis now shows code + short title.
- fig2: full 0.50-0.90 step-line sweep at 0.01 resolution, vertical
  reference line at 0.70.
- fig3: top-3 occupations labeled by name at the concentration elbow.
- fig4: x-axis labels now name the excluded occupation(s), not codes.
"""
import csv
import collections
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 9,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.grid": True,
    "axes.axisbelow": True,
    "grid.color": "0.85",
    "grid.linewidth": 0.5,
    "figure.dpi": 300,
    "savefig.dpi": 300,
})

OUT = "output/figures"
os.makedirs(OUT, exist_ok=True)

SHORT_NAMES = {
    "61": "Skilled agricultural", "52": "Sales workers", "93": "Labourers (mfg/constr)",
    "75": "Food/craft trades", "83": "Drivers", "92": "Ag./forestry labourers",
    "23": "Teaching professionals", "51": "Personal services", "71": "Building trades",
    "72": "Metal/machinery trades", "81": "Plant/machine operators", "33": "Business assoc. prof.",
    "91": "Cleaners/helpers", "54": "Protective services", "74": "Electrical trades",
    "41": "Keyboard clerks", "32": "Health assoc. prof.", "14": "Hospitality managers",
    "13": "Production managers", "26": "Legal/social prof.", "73": "Handicraft/printing",
    "31": "Science/eng. assoc.", "96": "Refuse/elementary", "42": "Customer service clerks",
    "95": "Street/service workers", "24": "Business professionals", "34": "Legal/social assoc.",
    "12": "Admin/commercial mgrs", "43": "Recording clerks", "62": "Forestry/fishery skilled",
    "21": "Science/eng. professionals", "22": "Health professionals", "11": "Chief executives",
    "94": "Food prep assistants", "35": "ICT technicians", "25": "ICT professionals",
    "82": "Assemblers", "44": "Clerical support", "53": "Personal care",
    "63": "Subsistence farmers",
}


def save(fig, name):
    fig.savefig(f"{OUT}/{name}.png")
    fig.savefig(f"{OUT}/{name}.pdf")
    plt.close(fig)
    print(f"wrote {name}.png and {name}.pdf")


def fig1_range_comparison():
    rows = list(csv.DictReader(open("output/range_comparison_2digit_vs_4digit_scenario_b.csv", encoding="utf-8")))
    shown = [r for r in rows if r["wmean_range_4digit_track_b"] not in ("", "None")]
    excluded = [r for r in rows if r["wmean_range_4digit_track_b"] in ("", "None")]
    shown.sort(key=lambda r: -float(r["employment_2digit_millions"]))

    labels = [f"{r['isco_2digit']} {SHORT_NAMES.get(r['isco_2digit'], '')}" for r in shown]
    r2d = [float(r["range_2digit_track_a"]) for r in shown]
    r4d = [float(r["wmean_range_4digit_track_b"]) for r in shown]

    y = range(len(shown))
    fig, ax = plt.subplots(figsize=(7.5, 9.5))
    h = 0.35
    ax.barh([i + h/2 for i in y], r2d, height=h, color="0.55", label="2-digit (Track A)")
    ax.barh([i - h/2 for i in y], r4d, height=h, color="0.15", label="4-digit, employment-weighted mean (Track B, scenario b)")
    # annotate near-zero 4-digit bars so they don't read as absent
    for i, v in enumerate(r4d):
        if v < 0.02:
            ax.text(0.012, i - h/2, f"{v:.3f}", va="center", fontsize=6, color="0.15")
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=7.5)
    ax.invert_yaxis()
    ax.set_xlabel("Range (max − min probability)")
    ax.legend(frameon=False, loc="lower right", fontsize=7.5)
    ax.set_xlim(0, 1)

    import textwrap
    excl_desc = ", ".join(f"{r['isco_2digit']} ({SHORT_NAMES.get(r['isco_2digit'],'')})" for r in excluded)
    caption = (
        f"All {len(shown)} ISCO 2-digit categories with at least one scoreable 4-digit child are shown. "
        f"Excluded: {excl_desc} — 0.0029M total employment across its 4-digit children in the LFS "
        f"microdata sample (only 1 of 4 child codes appears at all, and it is itself unmatched to "
        f"Frey-Osborne); not a granularity or plotting artifact."
    )
    wrapped = "\n".join(textwrap.wrap(caption, width=110))
    fig.text(0.5, 0.005, wrapped, ha="center", va="bottom", fontsize=6.5, color="0.35")
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    save(fig, "fig1_range_comparison")


def fig2_threshold_sensitivity():
    emp_f, emp_m, emp_t = collections.defaultdict(float), collections.defaultdict(float), collections.defaultdict(float)
    with open("output/track_b_employment_19th.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["occ_code"] == "NO_OCCUPATION_CODE":
                continue
            e = float(row["weighted_employment_millions"])
            emp_t[row["occ_code"]] += e
            if row["sex"] == "Female":
                emp_f[row["occ_code"]] += e
            elif row["sex"] == "Male":
                emp_m[row["occ_code"]] += e

    scored = {}
    with open("output/track_b_scored.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            scored[row["occ_code"]] = float(row["mean_prob"])
    for code in ("9211", "9212", "9213"):
        scored[code] = 0.87

    thresholds = [round(0.50 + 0.01 * i, 2) for i in range(41)]  # 0.50..0.90

    def series(emp_dict):
        out = []
        for thr in thresholds:
            denom = sum(emp_dict.get(c, 0.0) for c in scored)
            num = sum(emp_dict.get(c, 0.0) for c in scored if scored[c] > thr)
            out.append(100 * num / denom if denom else None)
        return out

    total_s, male_s, female_s = series(emp_t), series(emp_m), series(emp_f)

    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.step(thresholds, total_s, where="post", color="0.15", label="Total", linewidth=1.5)
    ax.step(thresholds, male_s, where="post", color="0.5", label="Male", linewidth=1.3, linestyle="--")
    ax.step(thresholds, female_s, where="post", color="0.5", label="Female", linewidth=1.3, linestyle=":")
    ax.axvline(0.7, color="0.7", linewidth=1.0, linestyle="-", zorder=0)
    ax.text(0.702, ax.get_ylim()[1] if False else 98, "0.70", fontsize=7, color="0.4")
    ax.set_xlim(0.50, 0.90)
    ax.set_ylim(0, 100)
    ax.set_xlabel("High-risk threshold")
    ax.set_ylabel("High-risk employment share (%)")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.legend(frameon=False)
    fig.text(0.5, 0.005, "Mean-probability variant, scenario (b), 19th ICLS. Step function: share at each 0.01 threshold.",
              ha="center", fontsize=7, color="0.4")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save(fig, "fig2_threshold_sensitivity")


def fig3_concentration_curve():
    emp_t = collections.defaultdict(float)
    with open("output/track_b_employment_19th.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["occ_code"] == "NO_OCCUPATION_CODE":
                continue
            emp_t[row["occ_code"]] += float(row["weighted_employment_millions"])

    scored, titles = {}, {}
    with open("output/track_b_scored.csv", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            scored[row["occ_code"]] = float(row["mean_prob"])
            titles[row["occ_code"]] = row["title"]
    manual_titles = {"9211": "Crop farm labourers", "9212": "Livestock farm labourers", "9213": "Mixed crop and livestock farm labourers"}
    for code, t in manual_titles.items():
        scored[code] = 0.87
        titles[code] = t

    high_risk = sorted([(c, emp_t.get(c, 0.0)) for c in scored if scored[c] > 0.7], key=lambda x: -x[1])
    total_hr = sum(e for _, e in high_risk)
    cum = 0.0
    xs, ys = [0], [0]
    for i, (c, e) in enumerate(high_risk, 1):
        cum += 100 * e / total_hr
        xs.append(i)
        ys.append(cum)

    fig, ax = plt.subplots(figsize=(6.5, 4.8))
    ax.plot(xs, ys, color="0.15", linewidth=1.5)
    ax.axhline(50, color="0.8", linewidth=0.7, linestyle="--", zorder=0)

    top3 = high_risk[:3]
    label_texts = [f"{i+1}. {titles[c][:32]} ({c})" for i, (c, e) in enumerate(top3)]
    y_positions = [ys[1], ys[2], ys[3]]
    x_positions = [1, 2, 3]
    text_xy = [(50, 25), (50, 15), (50, 5)]
    for (xp, yp, label, (tx, ty)) in zip(x_positions, y_positions, label_texts, text_xy):
        ax.annotate(label, xy=(xp, yp), xytext=(tx, ty), fontsize=7.5, color="0.2",
                    va="center", arrowprops=dict(arrowstyle="-", color="0.6", linewidth=0.6,
                                                  connectionstyle="arc3,rad=0.15"))
        ax.plot([xp], [yp], marker="o", color="0.15", markersize=3.5, zorder=5)

    ax.set_xlabel("Occupations, ranked by employment (descending)")
    ax.set_ylabel("Cumulative share of high-risk population (%)")
    ax.set_xlim(0, len(high_risk))
    ax.set_ylim(0, 100)
    fig.text(0.5, 0.005, f"{len(high_risk)} occupations in the high-risk (>0.7) population, "
              f"totaling {total_hr:.1f}M. Scenario (b), mean variant, 19th ICLS.",
              ha="center", fontsize=7, color="0.4")
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    save(fig, "fig3_concentration_curve")


def fig4_agricultural_ladder():
    rows = list(csv.DictReader(open("output/ref_agricultural_exclusion_ladder.csv", encoding="utf-8")))
    labels = [
        "Baseline\n(none excluded)",
        "Exclude\nMixed crop &\nanimal producers",
        "Exclude +\nLivestock &\ndairy producers",
        "Exclude all 5\nagricultural\noccupations",
    ]
    total = [float(r["total_high_risk_pct"]) for r in rows]
    male = [float(r["male_high_risk_pct"]) for r in rows]
    female = [float(r["female_high_risk_pct"]) for r in rows]

    x = range(len(rows))
    fig, ax = plt.subplots(figsize=(7, 4.8))
    ax.plot(x, total, marker="o", color="0.15", label="Total", linewidth=1.5)
    ax.plot(x, male, marker="s", color="0.5", label="Male", linewidth=1.5, linestyle="--")
    ax.plot(x, female, marker="^", color="0.5", label="Female", linewidth=1.5, linestyle=":")
    ax.set_xticks(list(x))
    ax.set_xticklabels(labels, fontsize=7.5)
    ax.set_ylabel("High-risk employment share (%)")
    ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.legend(frameon=False)
    import textwrap
    caption = ("Threshold 0.7, mean variant, scenario (b), 19th ICLS. Each step additionally excludes "
               "the named occupation(s); final step also excludes Crop farm labourers, Mobile "
               "farm/forestry plant operators, and Mixed crop and livestock farm labourers.")
    wrapped = "\n".join(textwrap.wrap(caption, width=95))
    fig.text(0.5, 0.005, wrapped, ha="center", va="bottom", fontsize=6.5, color="0.4")
    fig.tight_layout(rect=[0, 0.1, 1, 1])
    save(fig, "fig4_agricultural_ladder")


if __name__ == "__main__":
    fig1_range_comparison()
    fig2_threshold_sensitivity()
    fig3_concentration_curve()
    fig4_agricultural_ladder()
