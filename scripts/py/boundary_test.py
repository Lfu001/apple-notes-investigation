"""Phase 4: edit boundary mapping.

Each test:
  1. Re-seed (or normalize) the target note.
  2. Apply a specific structural mutation via bs4.
  3. set_body -> get_body -> compare to expected.
  4. Run one more round-trip and report if converged.

Outputs per-case files to data/boundary/ and a summary JSON to data/runs/.
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

sys.path.insert(0, str(Path(__file__).parent))
import notes
from compare import sha256, unified_diff

from bs4 import BeautifulSoup, NavigableString

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DATA = REPO_ROOT / "data"
BOUNDARY = DATA / "boundary"
RUNS = DATA / "runs"


def normalize(note_name: str, delay: float) -> str:
    prev = notes.get_body(note_name)
    for _ in range(3):
        notes.set_body(note_name, prev)
        time.sleep(delay)
        cur = notes.get_body(note_name)
        if cur == prev:
            return cur
        prev = cur
    raise RuntimeError(f"Did not converge: {note_name}")


# --- Mutation functions ------------------------------------------------------
# Each returns the modified HTML (and may use the input note name for context).

def mut_append_paragraph(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    new = soup.new_tag("div")
    new.string = "APPENDED PARAGRAPH"
    # Append at end of document; bs4's soup is the document
    soup.append(new)
    return str(soup)


def mut_append_li(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Find the outermost <ul> or <ol>
    container = soup.find(["ul", "ol"])
    if container is None:
        raise RuntimeError("no <ul>/<ol> found")
    new_li = soup.new_tag("li")
    new_li.string = "APPENDED ITEM"
    container.append(new_li)
    return str(soup)


def mut_delete_li(html: str, text_marker: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    targets = [li for li in soup.find_all("li") if text_marker in li.get_text()]
    if not targets:
        raise RuntimeError(f"no <li> matching {text_marker!r}")
    targets[0].decompose()
    return str(soup)


def mut_insert_new_span(html: str, before_text: str, new_html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Find a NavigableString that contains before_text. Insert new_html before it.
    target = None
    for s in soup.find_all(string=True):
        if isinstance(s, NavigableString) and before_text in str(s):
            target = s
            break
    if target is None:
        raise RuntimeError(f"text not found: {before_text!r}")
    text = str(target)
    idx = text.index(before_text)
    head = text[:idx]
    tail = text[idx:]
    new_fragment = BeautifulSoup(new_html, "html.parser")
    # Replace the text node with [head, ...new_fragment.children, tail]
    parent = target.parent
    target.replace_with(NavigableString(head))
    # After replace_with, the head node is now in place. Insert the new fragment after it.
    head_node = next(c for c in parent.contents if isinstance(c, NavigableString) and str(c) == head)
    # Insert each top-level child of new_fragment after head_node, in order
    insert_after = head_node
    for child in list(new_fragment.contents):
        insert_after.insert_after(child)
        insert_after = child
    # Finally insert the tail text after the last inserted node
    tail_node = NavigableString(tail)
    insert_after.insert_after(tail_node)
    return str(soup)


def mut_add_style_attribute(html: str, marker_text: str, style: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Find the closest tag wrapping the marker text
    for s in soup.find_all(string=True):
        if isinstance(s, NavigableString) and marker_text in str(s):
            tag = s.parent
            tag["style"] = style
            return str(soup)
    raise RuntimeError(f"text not found: {marker_text!r}")


def mut_split_paragraph(html: str, paragraph_text: str, insert: str) -> str:
    """Insert text mid-paragraph by splitting a NavigableString."""
    soup = BeautifulSoup(html, "html.parser")
    for s in soup.find_all(string=True):
        if isinstance(s, NavigableString) and paragraph_text in str(s):
            text = str(s)
            idx = text.index(paragraph_text)
            new_text = text[: idx + len(paragraph_text) // 2] + insert + text[idx + len(paragraph_text) // 2:]
            s.replace_with(NavigableString(new_text))
            return str(soup)
    raise RuntimeError(f"text not found: {paragraph_text!r}")


def mut_remove_paragraph(html: str, marker_text: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    # Find the top-level <div> that contains the marker text and remove it
    for div in soup.find_all("div", recursive=False):
        if marker_text in div.get_text():
            div.decompose()
            return str(soup)
    raise RuntimeError(f"no top-level <div> contains {marker_text!r}")


def mut_wrap_in_b(html: str, target_text: str) -> str:
    """Wrap the target_text substring (inside a NavigableString) with <b>...</b>."""
    soup = BeautifulSoup(html, "html.parser")
    for s in soup.find_all(string=True):
        if isinstance(s, NavigableString) and target_text in str(s):
            text = str(s)
            idx = text.index(target_text)
            head = text[:idx]
            tail = text[idx + len(target_text):]
            parent = s.parent
            s.replace_with(NavigableString(head))
            # Find the head node we just created
            head_node = None
            for c in parent.contents:
                if isinstance(c, NavigableString) and str(c) == head:
                    head_node = c
                    break
            new_b = soup.new_tag("b")
            new_b.string = target_text
            head_node.insert_after(new_b)
            new_b.insert_after(NavigableString(tail))
            return str(soup)
    raise RuntimeError(f"text not found: {target_text!r}")


# --- Test cases --------------------------------------------------------------

@dataclass
class BoundaryCase:
    id: str
    note_name: str
    description: str
    mutate: Callable[[str], str]


CASES: list[BoundaryCase] = [
    BoundaryCase(
        "B01-append-paragraph",
        "S01-plain",
        "Append new <div>APPENDED PARAGRAPH</div> at end",
        mut_append_paragraph,
    ),
    BoundaryCase(
        "B02-append-li",
        "S06-bullet",
        "Append <li>APPENDED ITEM</li> to existing <ul>",
        mut_append_li,
    ),
    BoundaryCase(
        "B03-delete-li",
        "S06-bullet",
        "Delete the <li>item three</li>",
        lambda html: mut_delete_li(html, "item three"),
    ),
    BoundaryCase(
        "B04-insert-new-span",
        "S05-inline-decor",
        "Insert <b>injected</b> before 'back to normal'",
        lambda html: mut_insert_new_span(html, "back to normal.", "<b>injected </b>"),
    ),
    BoundaryCase(
        "B05-add-style-color",
        "S05-inline-decor",
        'Add style="color: red" to the <b>bold</b> tag',
        lambda html: mut_add_style_attribute(html, "bold", "color: red"),
    ),
    BoundaryCase(
        "B06-split-paragraph",
        "S01-plain",
        "Insert ' [INJECTED] ' mid-way in the first paragraph",
        lambda html: mut_split_paragraph(html, "First paragraph.", " [INJECTED] "),
    ),
    BoundaryCase(
        "B07-remove-paragraph",
        "S01-plain",
        "Remove the top-level <div> containing 'Second paragraph.'",
        lambda html: mut_remove_paragraph(html, "Second paragraph."),
    ),
    BoundaryCase(
        "B08-wrap-in-b",
        "S01-plain",
        "Wrap 'paragraph' in the first body line with <b>",
        lambda html: mut_wrap_in_b(html, "paragraph"),
    ),
]


def run_case(case: BoundaryCase, delay: float) -> dict:
    print(f"\n[{case.id}] ({case.note_name}) {case.description}")

    # Reset by re-seeding via roundtrip script's normalize (no destructive reset here;
    # boundary tests may leave the note in a different state, that's fine).
    try:
        normalized = normalize(case.note_name, delay)
    except Exception as e:
        return {"id": case.id, "status": "normalize_error", "error": str(e)}

    (BOUNDARY / f"{case.id}.before.html").write_text(normalized, encoding="utf-8")

    try:
        mutated = case.mutate(normalized)
    except Exception as e:
        return {"id": case.id, "status": "mutate_error", "error": str(e)}

    (BOUNDARY / f"{case.id}.mutated.html").write_text(mutated, encoding="utf-8")

    try:
        notes.set_body(case.note_name, mutated)
        time.sleep(delay)
        actual = notes.get_body(case.note_name)
    except notes.NotesError as e:
        return {"id": case.id, "status": "set_get_error", "error": str(e)}

    (BOUNDARY / f"{case.id}.actual.html").write_text(actual, encoding="utf-8")

    # Round 2 — does it converge?
    notes.set_body(case.note_name, actual)
    time.sleep(delay)
    actual2 = notes.get_body(case.note_name)
    converged = (actual == actual2)
    if not converged:
        diff = unified_diff(actual, actual2, case.id)
        (BOUNDARY / f"{case.id}.round2.diff").write_text(diff, encoding="utf-8")

    # Diff mutated (what we sent) vs actual (what came back)
    mutated_vs_actual = unified_diff(mutated, actual, case.id + ".mutated-vs-actual")
    if mutated_vs_actual:
        (BOUNDARY / f"{case.id}.mutated-vs-actual.diff").write_text(mutated_vs_actual, encoding="utf-8")

    # Heuristic outcome classification
    print(f"  converged: {converged}")
    print(f"  mutated==actual: {not bool(mutated_vs_actual)}")

    return {
        "id": case.id,
        "note": case.note_name,
        "description": case.description,
        "status": "ok",
        "normalized_sha256": sha256(normalized),
        "mutated_sha256": sha256(mutated),
        "actual_sha256": sha256(actual),
        "actual2_sha256": sha256(actual2),
        "converged": converged,
        "mutated_equals_actual": not bool(mutated_vs_actual),
    }


def run(delay: float, only: str | None) -> int:
    BOUNDARY.mkdir(parents=True, exist_ok=True)
    RUNS.mkdir(parents=True, exist_ok=True)

    results = []
    for case in CASES:
        if only and case.id != only:
            continue
        try:
            results.append(run_case(case, delay))
        except Exception as e:
            print(f"  EXCEPTION: {e}", file=sys.stderr)
            results.append({"id": case.id, "status": "exception", "error": str(e)})

    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = RUNS / f"boundary-{ts}.json"
    out.write_text(json.dumps({"timestamp": ts, "delay": delay, "results": results}, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nWrote: {out}")

    converged = sum(1 for r in results if r.get("converged"))
    ok = sum(1 for r in results if r.get("status") == "ok")
    print(f"\nSummary: {ok}/{len(results)} executed without error, {converged}/{ok} converged on round 2")
    return 0


def main() -> int:
    p = argparse.ArgumentParser(description="Phase 4: boundary mapping")
    p.add_argument("--delay", type=float, default=1.5)
    p.add_argument("--only", help="Run only the named case (e.g. B01-append-paragraph)")
    args = p.parse_args()
    return run(args.delay, args.only)


if __name__ == "__main__":
    sys.exit(main())
