"""Phase 3: minimal edit test.

For each target note:
  1. Start from a normalized HTML body (get_body once -> if not fixed-point, set+get once more).
  2. Parse with BeautifulSoup.
  3. Modify ONE text node (NavigableString) by string substitution.
  4. set_body with the modified HTML.
  5. get_body.
  6. Compare against the expected (normalized HTML with the text substitution).

The diff in step 6 should be EMPTY if the edit is preserved cleanly,
or limited to differences caused by bs4 vs Notes serialization style.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes
from compare import is_fixed_point, sha256, unified_diff

from bs4 import BeautifulSoup, NavigableString

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA = REPO_ROOT / "data"
EDIT_DIR = DATA / "edit"
RUNS = DATA / "runs"


@dataclass
class EditCase:
    note_name: str
    needle: str             # exact substring expected somewhere in the normalized HTML
    replacement: str        # what to replace it with
    description: str        # human-readable description


# Edit cases targeting our synthetic notes. The 'needle' must exist in the
# normalized body of the note. We use distinctive substrings to avoid ambiguity.
EDIT_CASES = [
    EditCase("S01-plain", "First paragraph.", "FIRST PARAGRAPH (edited).",
             "Replace first body paragraph text"),
    EditCase("S05-inline-decor", "Normal ", "Plain ",
             "Replace text adjacent to a <b>bold</b> span"),
    EditCase("S06-bullet", "item two", "ITEM TWO",
             "Replace text inside a <li>"),
    EditCase("S07-numbered", "second", "TWO",
             "Replace text inside a numbered <li>"),
    EditCase("S03-headings", "Heading level 2", "Replaced Heading",
             "Replace text inside a Heading <span>"),
]


def normalize(note_name: str, delay: float) -> str:
    """Return a 'fixed-point' version of the note body.

    Strategy: round-trip up to 3 times; stop when consecutive results match.
    """
    prev = notes.get_body(note_name)
    for i in range(3):
        notes.set_body(note_name, prev)
        time.sleep(delay)
        cur = notes.get_body(note_name)
        if cur == prev:
            return cur
        prev = cur
    raise RuntimeError(f"Note {note_name} did not converge after 3 rounds")


def edit_via_bs4(html: str, needle: str, replacement: str) -> str:
    """Replace `needle` with `replacement` inside ONE NavigableString.

    Returns the modified HTML serialized by bs4. Raises if needle is ambiguous or missing.
    """
    soup = BeautifulSoup(html, "html.parser")
    matches: list[NavigableString] = []
    for s in soup.find_all(string=True):
        if isinstance(s, NavigableString) and needle in str(s):
            matches.append(s)
    if not matches:
        raise ValueError(f"Needle not found: {needle!r}")
    if len(matches) > 1:
        raise ValueError(f"Needle is ambiguous ({len(matches)} matches): {needle!r}")
    target = matches[0]
    new_text = str(target).replace(needle, replacement)
    target.replace_with(NavigableString(new_text))
    return str(soup)


def run(delay: float) -> int:
    EDIT_DIR.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)

    results = []
    for case in EDIT_CASES:
        print(f"\n[{case.note_name}] {case.description}")
        try:
            normalized = normalize(case.note_name, delay)
        except Exception as e:
            print(f"  normalize ERROR: {e}", file=sys.stderr)
            results.append({"case": case.__dict__, "status": "normalize_error", "error": str(e)})
            continue

        (EDIT_DIR / f"{case.note_name}.normalized.html").write_text(normalized, encoding="utf-8")

        # Compute the "expected" body: the normalized HTML with just the substitution
        expected = normalized.replace(case.needle, case.replacement, 1)
        (EDIT_DIR / f"{case.note_name}.expected.html").write_text(expected, encoding="utf-8")

        # Edit via bs4
        try:
            edited_via_bs4 = edit_via_bs4(normalized, case.needle, case.replacement)
        except Exception as e:
            print(f"  edit ERROR: {e}", file=sys.stderr)
            results.append({"case": case.__dict__, "status": "edit_error", "error": str(e)})
            continue
        (EDIT_DIR / f"{case.note_name}.bs4-out.html").write_text(edited_via_bs4, encoding="utf-8")

        # Compare bs4 output to expected (pure string substitution).
        # If they match, bs4 serializer is "transparent" for this case.
        bs4_vs_expected_diff = unified_diff(expected, edited_via_bs4, case.note_name + ".bs4-vs-expected")
        if bs4_vs_expected_diff:
            print("  WARN: bs4 serializer changed something beyond the substitution")
            (EDIT_DIR / f"{case.note_name}.bs4-vs-expected.diff").write_text(bs4_vs_expected_diff, encoding="utf-8")

        # Set body to bs4 output, then get
        try:
            notes.set_body(case.note_name, edited_via_bs4)
            time.sleep(delay)
            actual = notes.get_body(case.note_name)
        except notes.NotesError as e:
            print(f"  set/get ERROR: {e}", file=sys.stderr)
            results.append({"case": case.__dict__, "status": "set_get_error", "error": str(e)})
            continue

        (EDIT_DIR / f"{case.note_name}.actual.html").write_text(actual, encoding="utf-8")

        # The ultimate question: does actual == expected ?
        # We also try one more round-trip to see if there's a 1-round normalization.
        actual_vs_expected = unified_diff(expected, actual, case.note_name + ".actual-vs-expected")
        if actual_vs_expected:
            (EDIT_DIR / f"{case.note_name}.actual-vs-expected.diff").write_text(actual_vs_expected, encoding="utf-8")

        # And see if it converged
        notes.set_body(case.note_name, actual)
        time.sleep(delay)
        actual2 = notes.get_body(case.note_name)
        converged = (actual == actual2)
        (EDIT_DIR / f"{case.note_name}.actual2.html").write_text(actual2, encoding="utf-8")

        actual_vs_actual2_diff = unified_diff(actual, actual2, case.note_name + ".actual-vs-actual2")
        if actual_vs_actual2_diff:
            (EDIT_DIR / f"{case.note_name}.round2.diff").write_text(actual_vs_actual2_diff, encoding="utf-8")

        clean_edit = (actual == expected)
        result = {
            "case": case.__dict__,
            "status": "ok",
            "normalized_sha256": sha256(normalized),
            "expected_sha256": sha256(expected),
            "bs4_output_sha256": sha256(edited_via_bs4),
            "actual_sha256": sha256(actual),
            "actual2_sha256": sha256(actual2),
            "bs4_serializer_transparent": (not bs4_vs_expected_diff),
            "clean_edit": clean_edit,  # exact text substitution and nothing else
            "converged_after_one_round": converged,
        }
        results.append(result)
        print(f"  bs4 transparent: {result['bs4_serializer_transparent']}")
        print(f"  clean_edit (actual == expected): {result['clean_edit']}")
        print(f"  converged after 1 round: {result['converged_after_one_round']}")

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RUNS / f"edit-{ts}.json"
    out.write_text(json.dumps({"timestamp": ts, "delay": delay, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote: {out}")

    clean = sum(1 for r in results if r.get("clean_edit"))
    transp = sum(1 for r in results if r.get("bs4_serializer_transparent"))
    print(f"\nSummary: {clean}/{len(results)} clean edits, {transp}/{len(results)} bs4 transparent")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 3: minimal edit test")
    p.add_argument("--delay", type=float, default=1.5)
    args = p.parse_args()
    return run(args.delay)


if __name__ == "__main__":
    sys.exit(main())
