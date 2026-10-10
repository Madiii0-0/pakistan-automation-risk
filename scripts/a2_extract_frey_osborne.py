"""
A2 - Extract the Frey & Osborne (2017) Appendix A table (702 occupations)
from frey_osborne.pdf into a clean CSV, with verification.

Approach: pdfplumber text extraction with x_tolerance=1 (default tolerance
merges words together in this PDF -- confirmed by direct inspection), then
regex over every line for the "rank. probability [label] SOC-code Title"
pattern. Scan all pages rather than hardcoding a page range, since the
table's exact page boundaries in pdfplumber's indexing weren't confirmed
ahead of time.
"""
import csv
import re

SRC = "frey_osborne.pdf"
OUT = "output/frey_osborne_occupations.csv"

# e.g. "1. 0.0028 29-1125 Recreational therapists"
#      "15. 0.0042 0 29-1060 Physicians and surgeons"
#      "262. 0.38 1 17-1022 Surveyors"
LINE_RE = re.compile(
    r"^(\d{1,3})\.\s+([\d.]+)\s+(?:([01])\s+)?(\d{2}-\d{4})\s+(.+?)\s*$"
)

# Known values hand-observed during exploration, used as hard assertions.
SPOT_CHECKS = {
    1: (0.0028, "29-1125", "Recreational therapists"),
    702: (0.99, "41-9041", "Telemarketers"),
    70: (0.015, "11-1011", "Chief executives"),
    589: (0.94, "13-2011", "Accountants and auditors"),
}


def main():
    import pdfplumber

    rows = []
    with pdfplumber.open(SRC) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1) or ""
            for line in text.split("\n"):
                m = LINE_RE.match(line.strip())
                if not m:
                    continue
                rank = int(m.group(1))
                prob = float(m.group(2))
                label = m.group(3) if m.group(3) is not None else ""
                soc = m.group(4)
                title = m.group(5).strip()
                # Guard against accidentally matching stray numbered lines
                # from body text/footnotes (e.g. footnote markers) rather
                # than the appendix table: real rows have prob in [0,1].
                if not (0.0 <= prob <= 1.0):
                    continue
                rows.append(
                    {
                        "rank": rank,
                        "probability": prob,
                        "hand_label": label,
                        "soc_code": soc,
                        "title": title,
                    }
                )

    print(f"[A2] Raw regex matches: {len(rows)}")

    # De-dup by rank in case a rank number happens to reappear from
    # unrelated body text; keep the first occurrence only if it's a clean
    # dup, otherwise surface the conflict loudly.
    by_rank = {}
    conflicts = []
    for r in rows:
        if r["rank"] in by_rank and by_rank[r["rank"]] != r:
            conflicts.append((by_rank[r["rank"]], r))
        by_rank.setdefault(r["rank"], r)

    if conflicts:
        print(f"[A2] WARNING: {len(conflicts)} rank conflicts found:")
        for a, b in conflicts[:10]:
            print("   ", a, "vs", b)

    ranks = sorted(by_rank.keys())
    print(f"[A2] Unique ranks found: {len(ranks)} (min={ranks[0]}, max={ranks[-1]})")
    assert len(ranks) == 702, f"Expected 702 unique ranks, got {len(ranks)}"
    assert ranks == list(range(1, 703)), "Ranks are not a contiguous 1..702 sequence"

    final_rows = [by_rank[r] for r in ranks]

    # probability range check
    bad_probs = [r for r in final_rows if not (0.0 <= r["probability"] <= 1.0)]
    assert not bad_probs, f"{len(bad_probs)} rows have out-of-range probability"

    # no duplicate SOC codes
    soc_codes = [r["soc_code"] for r in final_rows]
    dup_socs = {s for s in soc_codes if soc_codes.count(s) > 1}
    print(f"[A2] Duplicate SOC codes: {len(dup_socs)}")
    if dup_socs:
        for s in list(dup_socs)[:10]:
            dupes = [r for r in final_rows if r["soc_code"] == s]
            print("   DUP", s, dupes)
    assert not dup_socs, "Duplicate SOC codes found in Frey-Osborne extraction"

    # spot checks against hand-observed values from initial exploration
    for rank, (exp_prob, exp_soc, exp_title_substr) in SPOT_CHECKS.items():
        row = by_rank[rank]
        assert abs(row["probability"] - exp_prob) < 1e-6, (
            f"Rank {rank} probability mismatch: got {row['probability']}, expected {exp_prob}"
        )
        assert row["soc_code"] == exp_soc, (
            f"Rank {rank} SOC mismatch: got {row['soc_code']}, expected {exp_soc}"
        )
        assert exp_title_substr.lower() in row["title"].lower(), (
            f"Rank {rank} title mismatch: got '{row['title']}', expected to contain '{exp_title_substr}'"
        )
    print(f"[A2] All {len(SPOT_CHECKS)} spot checks PASSED")

    monotonic_violations = sum(
        1
        for a, b in zip(final_rows, final_rows[1:])
        if b["probability"] < a["probability"] - 1e-9
    )
    print(f"[A2] Rank/probability monotonicity violations: {monotonic_violations} (informational)")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["rank", "probability", "hand_label", "soc_code", "title"])
        writer.writeheader()
        writer.writerows(final_rows)

    print(f"[A2] Wrote {len(final_rows)} rows to {OUT}")
    print("[A2] ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
