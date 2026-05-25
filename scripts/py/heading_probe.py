"""Phase 6: Heading-style discovery probe.

Create a battery of test notes via set_body, each with a different candidate
HTML form for Title/Heading/Subheading. The user visually inspects each in
Notes.app and reports which (if any) produces a proper paragraph style:

  - Title: theme-sized large bold text (NOT explicit 24px)
  - Heading: bold + collapse arrow ">" beside the text
  - Subheading: theme-sized smaller bold text

For each test note we also save the get_body OUTPUT to a file so we can later
diff against the GUI native output of T03-headings to see if any input form
produces a matching serialization (which would suggest the internal style was
properly created).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT = REPO_ROOT / "data" / "heading_probe"


# Each entry: (note name prefix, label, body HTML).
# The note title (first text in body) must contain the prefix so the user
# can identify it in Notes.app. We use the suffix as a visible label too.
CASES: list[tuple[str, str, str]] = [
    # --- Heading-tag variations ---
    ("H01-h1-bare",
     "Bare <h1>, no <div> wrapper",
     "<h1>H01 — Title test (h1 bare)</h1><div>body line</div>"),

    ("H02-h2-bare",
     "Bare <h2>, no <div> wrapper",
     "<h2>H02 — Heading test (h2 bare)</h2><div>body line</div>"),

    ("H03-h3-bare",
     "Bare <h3>, no <div> wrapper",
     "<h3>H03 — Subheading test (h3 bare)</h3><div>body line</div>"),

    ("H04-h1-then-body",
     "Bare <h1> then body content",
     "<h1>H04 — Title</h1><div>regular body paragraph here</div>"),

    # --- Tags that group headings ---
    ("H05-header-tag",
     "<header><h1>...</h1></header>",
     "<header><h1>H05 — header wrapping h1</h1></header><div>body</div>"),

    ("H06-hgroup",
     "<hgroup><h1>...</h1></hgroup>",
     "<hgroup><h1>H06 — hgroup wrapping h1</h1></hgroup><div>body</div>"),

    # --- Candidate Apple-specific class names on <div> ---
    ("H07-div-class-title",
     'div class="title"',
     '<div class="title">H07 — div.title</div><div>body</div>'),

    ("H08-div-class-Apple-title",
     'div class="Apple-title"',
     '<div class="Apple-title">H08 — div.Apple-title</div><div>body</div>'),

    ("H09-div-class-AppleTitleStyle",
     'div class="AppleTitleStyle"',
     '<div class="AppleTitleStyle">H09 — div.AppleTitleStyle</div><div>body</div>'),

    ("H10-h1-class-Apple-style",
     'h1 class="Apple-paragraph-title"',
     '<div><h1 class="Apple-paragraph-title">H10 — h1.Apple-paragraph-title</h1></div><div>body</div>'),

    # --- Data attributes ---
    ("H11-data-paragraph-style",
     'div data-paragraph-style="title"',
     '<div data-paragraph-style="title">H11 — data-paragraph-style</div><div>body</div>'),

    ("H12-data-apple-style",
     'div data-apple-paragraph-style="title"',
     '<div data-apple-paragraph-style="title">H12 — data-apple-paragraph-style</div><div>body</div>'),

    # --- HTML document envelope ---
    ("H13-doctype-html-body",
     "Full HTML document with <!DOCTYPE>",
     "<!DOCTYPE html><html><body><h1>H13 — full doc with doctype</h1><div>body</div></body></html>"),

    ("H14-meta-charset",
     "With <meta charset> first",
     '<meta charset="utf-8"><h1>H14 — meta charset first</h1><div>body</div>'),

    # --- Title HTML element (head element) ---
    ("H15-title-element",
     "<title>...</title>",
     "<title>H15 — title element</title><div>H15 — title element body</div>"),

    # --- Inline style that matches a likely Title spec ---
    ("H16-inline-style-title-like",
     "div with inline style mimicking Title theme",
     '<div style="font-family: -apple-system, \'Helvetica Neue\'; font-size: 28px; font-weight: bold">H16 — inline 28px bold</div><div>body</div>'),

    # --- Setting body to GUI-native form of T03 exactly (as control) ---
    ("H17-mimic-T03-gui-native",
     "Exact replay of T03-headings GUI-native HTML",
     "<div><h1>H17 — Title (T03 mimic)</h1></div>\n<div><h2>H17 — Heading (T03 mimic)</h2></div>\n<div><h3>H17 — Subheading (T03 mimic)</h3></div>\n<div>Body paragraph.</div>"),

    # --- h1 inside <article> ---
    ("H18-article-h1",
     "<article><h1>...</h1></article>",
     "<article><h1>H18 — article h1</h1></article><div>body</div>"),

    # --- h1 with role attribute ---
    ("H19-h1-role-heading",
     'h1 role="heading"',
     '<h1 role="heading">H19 — h1 role heading</h1><div>body</div>'),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # Clean up any existing H- probe notes from previous runs
    existing = [n.name for n in notes.list_notes() if n.name.startswith("H") and "—" in n.name]
    for name in existing:
        try:
            notes.delete_note(name)
        except notes.NotesError:
            pass
    if existing:
        print(f"Deleted {len(existing)} previous probe notes")
        time.sleep(1.5)

    for prefix, label, html in CASES:
        try:
            notes.create_note(html)
            time.sleep(0.4)
        except notes.NotesError as e:
            print(f"FAIL {prefix}: {e}")
            continue

    time.sleep(1.5)

    # Save the get_body output for each
    summary = []
    for prefix, label, html in CASES:
        # Find note by prefix
        all_notes = notes.list_notes()
        matches = [n for n in all_notes if n.name.startswith(prefix)]
        if not matches:
            print(f"NOT FOUND in HTMLTest: {prefix}")
            summary.append(f"{prefix}\tNOT FOUND")
            continue
        name = matches[0].name
        try:
            body = notes.get_body(name)
        except notes.NotesError as e:
            print(f"get_body failed {name}: {e}")
            continue
        (OUT / f"{prefix}.input.html").write_text(html, encoding="utf-8")
        (OUT / f"{prefix}.actual-name.txt").write_text(name, encoding="utf-8")
        (OUT / f"{prefix}.body.html").write_text(body, encoding="utf-8")
        summary.append(f"{prefix}\t{name}\t{label}")

    print("\n=== Created notes ===")
    for line in summary:
        print(line)
    print(f"\nOutputs saved to: {OUT}")
    print("\nNow open each in Notes.app and check:")
    print("  - Does the title-line render as a proper Title paragraph?")
    print("    (theme-sized large bold, like in T01-plain originally)")
    print("  - For H02 / H08 etc: does it show as Heading with `>` collapse arrow?")
    return 0


if __name__ == "__main__":
    sys.exit(main())
