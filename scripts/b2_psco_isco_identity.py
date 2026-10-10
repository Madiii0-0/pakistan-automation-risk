"""
B2 - Verify the PSCO(=ISCO) identity hypothesis: compare PSCO-2015's 436
unit-group codes+titles (output/psco_codes.csv, from B1) against the
official ISCO-08 structure's 436 unit-group codes+titles
(output/isco_structure.csv level 4, from A4).

If this holds, the PSCO->ISCO step in the pipeline is an identity mapping
and no separate crosswalk needs to be built -- PSCO code can be joined
directly to the BLS ISCO-08<->SOC crosswalk.
"""
import csv
import re

PSCO = "output/psco_codes.csv"
ISCO = "output/isco_structure.csv"
OUT = "output/psco_isco_identity_check.csv"


def normalize(title: str) -> str:
    """Lowercase, strip punctuation/whitespace variation, so a match isn't
    defeated by e.g. a trailing period, an extra space, or a hyphen vs
    space -- while still catching any REAL wording difference."""
    t = title.lower().strip()
    t = re.sub(r"[^\w\s]", " ", t)
    t = re.sub(r"\s+", " ", t)
    return t.strip()


def main():
    psco = {}
    with open(PSCO, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            psco[row["psco_4digit"]] = row["unit_title"]

    isco = {}
    with open(ISCO, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row["level"] == "4":
                isco[row["isco_code"]] = row["title"]

    print(f"[B2] PSCO unit codes: {len(psco)}")
    print(f"[B2] Official ISCO-08 unit codes: {len(isco)}")

    all_codes = sorted(set(psco) | set(isco))
    rows = []
    counts = {"exact_match": 0, "normalized_match": 0, "title_mismatch": 0,
              "psco_only": 0, "isco_only": 0}

    for code in all_codes:
        p_title = psco.get(code)
        i_title = isco.get(code)

        if p_title is None:
            status = "isco_only"
        elif i_title is None:
            status = "psco_only"
        elif p_title == i_title:
            status = "exact_match"
        elif normalize(p_title) == normalize(i_title):
            status = "normalized_match"
        else:
            status = "title_mismatch"

        counts[status] += 1
        rows.append(
            {
                "psco_4digit": code,
                "psco_title": p_title or "",
                "isco_title": i_title or "",
                "match_status": status,
            }
        )

    print(f"[B2] Match status breakdown: {counts}")

    total_codes_present_both_sides = counts["exact_match"] + counts["normalized_match"] + counts["title_mismatch"]
    identity_rate = (counts["exact_match"] + counts["normalized_match"]) / total_codes_present_both_sides if total_codes_present_both_sides else 0
    print(f"[B2] Identity rate (exact+normalized / codes present in both): {identity_rate:.4%}")

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["psco_4digit", "psco_title", "isco_title", "match_status"])
        writer.writeheader()
        writer.writerows(rows)
    print(f"[B2] Wrote {len(rows)} rows to {OUT}")

    non_identity = [r for r in rows if r["match_status"] != "exact_match" and r["match_status"] != "normalized_match"]
    print(f"[B2] Non-identity rows requiring manual review: {len(non_identity)}")
    for r in non_identity:
        print(f"   {r['match_status']:<15} {r['psco_4digit']}  PSCO='{r['psco_title']}'  ISCO='{r['isco_title']}'")

    print("[B2] DONE (informational -- see printed breakdown for the identity-hypothesis verdict)")


if __name__ == "__main__":
    main()
