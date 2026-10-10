"""
B1 - Extract the PSCO-2015 codebook (psco_codes.pdf) into a clean CSV at
all 4 levels (major/sub-major/minor/unit group), with verification.

Layout: the PDF renders as a 4-column table (Sub-major | Minor | Unit |
Description) but text-extracts as a linear "code  description" sequence
per row, with "Major Group N   Title" section headers. Code string length
(2/3/4 digits) unambiguously identifies the hierarchy level -- no column
position needed. Leading zeros matter (Major Group 0, Armed Forces:
sub-major 01/02/03) so codes are kept as strings throughout, never cast
to int.
"""
import csv
import re

import pdfplumber

SRC = "psco_codes.pdf"
OUT_UNITS = "output/psco_codes.csv"
OUT_ALL_LEVELS = "output/psco_structure_all_levels.csv"

MAJOR_RE = re.compile(r"^Major Group\s+(\d+)\s+(.+)$")
CODE_RE = re.compile(r"^(\d{2,4})\s+(.+?)\s*$")
BARE_DIGIT_RE = re.compile(r"^(\d{1,4})$")

# Page furniture that is neither a major-group header nor a code row, and
# must not be allowed into the orphan-attachment logic (confirmed by
# direct inspection: the repeated table column headers were getting
# silently prefixed onto the first code row's description otherwise).
JUNK_LINES = {
    "PAKISTAN STANDARD CLASSIFICATION OF OCCUPATION-2012",
    "Sub-major Minor Unit",
    "Description",
    "Group Group Group",
}


def classify_lines():
    """Pass 1: walk every page's text in reading order and classify each
    line as ('major', code, title) / ('code', code, desc) /
    ('bare_digit', code, None) / ('orphan', None, text).

    'bare_digit' is its own category, not folded into 'code': a line that
    is ONLY digits with nothing following could be either (a) a wrapped
    minor-group code sitting between the two visual lines of its own
    title (confirmed by direct word-position inspection on page index 7 --
    code '351' sits at y=247.5, between its title's two wrapped lines at
    y=241.7 and y=253.2), or (b) an ordinary page-number footer (this doc
    numbers pages 1-18, and 2-digit page numbers collide with the same
    \\d{2,4} pattern used for sub-major codes). Pass 2 disambiguates using
    orphan-adjacency, since only case (a) sits next to unattached text.
    """
    events = []
    with pdfplumber.open(SRC) as pdf:
        for page in pdf.pages:
            text = page.extract_text(x_tolerance=1) or ""
            for line in text.split("\n"):
                line = line.strip()
                if not line or line in JUNK_LINES:
                    continue
                m_major = MAJOR_RE.match(line)
                if m_major:
                    events.append(("major", m_major.group(1), m_major.group(2).strip()))
                    continue
                if BARE_DIGIT_RE.match(line):
                    events.append(("bare_digit", line, None))
                    continue
                m_code = CODE_RE.match(line)
                if m_code:
                    code, desc = m_code.group(1), m_code.group(2).strip()
                    events.append(("code", code, desc))
                    continue
                events.append(("orphan", None, line))
    return events


def repair_wrapped_titles(events):
    """Pass 2: resolve 'bare_digit' events and attach orphan lines to the
    correct code event.

    - A 'bare_digit' event adjacent (immediately before or after, once
      surrounding orphans are accounted for) to at least one 'orphan'
      event is a wrapped code marker: promoted to a 'code' event whose
      description is assembled from the orphan run(s) around it.
    - A 'bare_digit' event with NO adjacent orphan on either side (i.e.
      sandwiched directly between two ordinary code/major lines) is a
      page-number footer: dropped, not promoted.
    - A run of orphan lines immediately BEFORE a code event (bare-digit-
      promoted or ordinary) is a leading fragment of THAT code's
      description. A run immediately AFTER is a trailing fragment of the
      same code's description (ordinary forward wrap).
    - Any orphan that never gets attached to a code is reported, not
      silently dropped.
    """
    # First pass: resolve bare_digit -> wrapped_code or drop, using local
    # adjacency on the RAW event stream. Promoted codes get their OWN kind
    # ('wrapped_code', distinct from ordinary 'code') so the second pass
    # can give them exclusive rights to consume neighbouring orphans --
    # ordinary single-line code rows must never touch adjacent orphans,
    # or a real orphan sitting between an ordinary code and an upcoming
    # wrapped code gets stolen by the wrong row (the original bug here).
    resolved = []
    n = len(events)
    for idx, (kind, a, b) in enumerate(events):
        if kind != "bare_digit":
            resolved.append((kind, a, b))
            continue
        prev_is_orphan = idx > 0 and events[idx - 1][0] == "orphan"
        next_is_orphan = idx < n - 1 and events[idx + 1][0] == "orphan"
        if prev_is_orphan or next_is_orphan:
            resolved.append(("wrapped_code", a, ""))
        else:
            resolved.append(("dropped_page_number", a, None))

    dropped_page_numbers = [a for k, a, b in resolved if k == "dropped_page_number"]
    events = [(k, a, b) for k, a, b in resolved if k != "dropped_page_number"]
    n = len(events)

    repaired = []
    i = 0
    pending_orphans_before = []
    unused_orphans = []

    while i < n:
        kind, code, text = events[i]

        if kind == "orphan":
            pending_orphans_before.append(text)
            i += 1
            continue

        if kind == "major":
            if pending_orphans_before:
                unused_orphans.extend(pending_orphans_before)
                pending_orphans_before = []
            repaired.append(("major", code, text))
            i += 1
            continue

        if kind == "code":
            # Ordinary row, matched with real inline text. Two sub-cases
            # exist in this document (confirmed by direct inspection):
            #   (a) simple forward wrap -- e.g. code 75's title trails onto
            #       a plain continuation line with no bare-digit involved.
            #       Here the following orphan(s) genuinely belong to THIS
            #       code and should be appended as a suffix.
            #   (b) the orphan(s) immediately following actually belong to
            #       an UPCOMING wrapped_code as its prefix (the '35' /
            #       '351' case). Distinguish by peeking past the orphan
            #       run: if the next non-orphan event is a wrapped_code,
            #       leave the orphans alone for it to claim as prefix.
            j = i + 1
            lookahead_orphans = []
            while j < n and events[j][0] == "orphan":
                lookahead_orphans.append(events[j][2])
                j += 1
            next_is_wrapped = j < n and events[j][0] == "wrapped_code"

            if lookahead_orphans and not next_is_wrapped:
                desc = " ".join([text, *lookahead_orphans]).strip()
                repaired.append(("code", code, desc))
                i = j
            else:
                repaired.append(("code", code, text))
                i += 1
            continue

        # kind == "wrapped_code": consume pending prefix orphans, plus any
        # orphans immediately following, to reconstruct the full title.
        prefix = " ".join(pending_orphans_before)
        pending_orphans_before = []

        j = i + 1
        suffix_parts = []
        while j < n and events[j][0] == "orphan":
            suffix_parts.append(events[j][2])
            j += 1

        parts = [p for p in (prefix, *suffix_parts) if p]
        desc = " ".join(parts).strip()

        repaired.append(("code", code, desc))
        i = j

    if pending_orphans_before:
        unused_orphans.extend(pending_orphans_before)

    return repaired, unused_orphans, dropped_page_numbers


def main():
    raw_events = classify_lines()
    events, unused_orphans, dropped_page_numbers = repair_wrapped_titles(raw_events)

    print(f"[B1] Raw line events: {len(raw_events)} -> repaired events: {len(events)}")
    print(f"[B1] Bare-digit lines dropped as page numbers: {sorted(dropped_page_numbers, key=int)}")
    # This document is 18 pages; every dropped value should plausibly be a
    # page number (<=18) and each value should be page-number-shaped, i.e.
    # short. Anything outside that range is suspicious and worth a look,
    # not an automatic pass.
    suspicious_drops = [p for p in dropped_page_numbers if not (1 <= int(p) <= 18)]
    assert not suspicious_drops, f"Dropped 'page numbers' outside 1-18 -- inspect: {suspicious_drops}"
    print(f"[B1] Unused/unattached orphan lines: {len(unused_orphans)}")
    if unused_orphans:
        for o in unused_orphans:
            print("   ORPHAN:", repr(o))
    assert not unused_orphans, "Some orphan lines never attached to a code -- extraction is losing text"

    major_code = major_title = None
    submajor_code = submajor_title = None
    minor_code = minor_title = None

    all_rows = []  # every level, for hierarchy verification
    unit_rows = []  # 4-digit only, the main output

    for kind, code, desc in events:
        if kind == "major":
            major_code, major_title = code, desc
            continue

        # kind == "code"
        if major_code is None or not desc:
            continue

        level = len(code)
        if level == 2:
            submajor_code, submajor_title = code, desc
            minor_code = minor_title = None
            all_rows.append(("2", code, desc, major_code, major_title, None, None, None, None))
        elif level == 3:
            minor_code, minor_title = code, desc
            all_rows.append(
                ("3", code, desc, major_code, major_title, submajor_code, submajor_title, None, None)
            )
        elif level == 4:
            all_rows.append(
                ("4", code, desc, major_code, major_title, submajor_code, submajor_title, minor_code, minor_title)
            )
            unit_rows.append(
                {
                    "psco_4digit": code,
                    "unit_title": desc,
                    "minor_code": minor_code,
                    "minor_title": minor_title,
                    "submajor_code": submajor_code,
                    "submajor_title": submajor_title,
                    "major_code": major_code,
                    "major_title": major_title,
                }
            )

    print(f"[B1] Level-2 (sub-major) rows: {sum(1 for r in all_rows if r[0]=='2')}")
    print(f"[B1] Level-3 (minor) rows: {sum(1 for r in all_rows if r[0]=='3')}")
    print(f"[B1] Level-4 (unit group) rows: {len(unit_rows)}")

    # Every unit code's prefixes must resolve to a defined parent in the
    # same document (self-consistency check, independent of ISCO-08).
    submajor_set = {r[1] for r in all_rows if r[0] == "2"}
    minor_set = {r[1] for r in all_rows if r[0] == "3"}
    bad = []
    for r in unit_rows:
        code = r["psco_4digit"]
        if code[:3] not in minor_set:
            bad.append(("missing minor parent", code, code[:3]))
        if code[:2] not in submajor_set:
            bad.append(("missing submajor parent", code, code[:2]))
    print(f"[B1] Hierarchy self-consistency issues: {len(bad)}")
    if bad:
        for b in bad[:15]:
            print("   ", b)
    assert not bad, "PSCO codebook hierarchy does not self-resolve -- extraction likely mis-parsed a page"

    # No duplicate unit codes
    codes = [r["psco_4digit"] for r in unit_rows]
    dupes = {c for c in codes if codes.count(c) > 1}
    print(f"[B1] Duplicate unit-group codes: {len(dupes)}")
    assert not dupes, f"Duplicate PSCO unit codes found: {dupes}"

    # Spot checks against values hand-read during exploration
    by_code = {r["psco_4digit"]: r for r in unit_rows}
    spot = {
        "1111": "Legislators",
        "2511": "Systems analysts",
        "9629": "Elementary workers not elsewhere classified",
        "0110": "Commissioned armed forces officers",
        "6310": "Subsistence crop farmers",
    }
    for code, expected_substr in spot.items():
        assert code in by_code, f"Expected PSCO code {code} not found"
        actual = by_code[code]["unit_title"]
        assert expected_substr.lower() in actual.lower(), (
            f"PSCO {code}: got '{actual}', expected to contain '{expected_substr}'"
        )
    print(f"[B1] All {len(spot)} spot checks PASSED")

    with open(OUT_UNITS, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "psco_4digit", "unit_title", "minor_code", "minor_title",
                "submajor_code", "submajor_title", "major_code", "major_title",
            ],
        )
        writer.writeheader()
        writer.writerows(unit_rows)
    print(f"[B1] Wrote {len(unit_rows)} unit-group rows to {OUT_UNITS}")

    with open(OUT_ALL_LEVELS, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["level", "code", "title", "major_code", "major_title",
             "submajor_code", "submajor_title", "minor_code", "minor_title"]
        )
        writer.writerows(all_rows)
    print(f"[B1] Wrote {len(all_rows)} all-level rows to {OUT_ALL_LEVELS}")

    print("[B1] ALL CHECKS PASSED")


if __name__ == "__main__":
    main()
