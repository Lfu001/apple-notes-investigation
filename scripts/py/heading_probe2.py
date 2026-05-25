"""Phase 6 round 2: try non-HTML representations and exotic CSS.

After confirming standard HTML cannot create Title/Heading paragraph styles,
try:
  - RTF (\\rtf1) input via body property
  - Plain text input
  - Setting name only with empty body
  - Custom -apple-* CSS properties via <style> tag
  - HTML5 details/summary (folding-like semantics)
  - Pre/blockquote variations
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT = REPO_ROOT / "data" / "heading_probe"


# (label, description, html-or-body)
CASES: list[tuple[str, str, str]] = [
    # RTF in body
    ("R01-rtf-bold",
     "RTF with bold (\\b ... \\b0)",
     r"{\rtf1\ansi\ansicpg1252\cocoartf2761 \fonttbl\f0\fswiss\fcharset0 Helvetica;}"
     r"{\colortbl;\red255\green255\blue255;} \pard \f0\fs48 \b R01-rtf-bold\b0\par "
     r"\fs26 body paragraph in RTF\par}"),

    ("R02-rtf-section-style",
     "RTF with custom paragraph style \\s1",
     r"{\rtf1\ansi {\stylesheet{\s1\fs48\b Title;}{\s2\fs36\b Heading;}}"
     r"\pard\plain\s1 R02-rtf-section-style\par "
     r"\pard\plain body line\par}"),

    ("R03-rtf-outline-level",
     "RTF with \\outlinelevel0 (heading level)",
     r"{\rtf1\ansi \pard\plain\f0\fs48\b\outlinelevel0 R03-rtf-outline-level\b0\par "
     r"\pard\plain\fs26 body line\par}"),

    # Plain text
    ("P01-plain-multiline",
     "Plain text, no tags",
     "P01-plain-multiline\nfirst body line\nsecond body line"),

    ("P02-plain-with-blank",
     "Plain text with blank line between title and body",
     "P02-plain-with-blank\n\nfirst body line"),

    # Custom CSS attempts
    ("S01-css-apple-paragraph-style",
     "<style> with -apple-paragraph-style",
     "<style>h1{-apple-paragraph-style:title}</style>"
     "<div><h1>S01-css-apple-paragraph-style</h1></div><div>body</div>"),

    ("S02-css-inline-webkit-text-style",
     "Inline -webkit-text-style-name",
     '<div><h1 style="-webkit-text-style-name: title">S02-css-inline-webkit-text-style</h1></div><div>body</div>'),

    ("S03-h1-with-class-and-data",
     "h1 with potentially-magic class and data attr",
     '<div><h1 class="apple-title" data-paragraph-style="title">S03-h1-with-class-and-data</h1></div><div>body</div>'),

    # HTML5 details/summary
    ("D01-details-summary",
     "<details><summary>...</summary> for folding-like markup",
     "<details><summary>D01-details-summary</summary><div>body line inside details</div></details><div>plain body</div>"),

    # Other HTML structure with built-in semantics
    ("M01-pre-tag",
     "<pre> for preformatted (already Monostyled?)",
     "<pre>M01-pre-tag</pre><div>body</div>"),

    ("M02-blockquote",
     "<blockquote> for Block Quote style?",
     "<blockquote>M02-blockquote</blockquote><div>body</div>"),

    # h1 with style mimicking Notes' theme exactly (could match internal heuristic)
    ("C01-h1-with-padding-margin",
     "h1 with various typographic CSS",
     '<div><h1 style="margin:0;padding:0;font-family:Helvetica;font-size:24px;font-weight:700">C01-h1-with-padding-margin</h1></div><div>body</div>'),

    # Apple-specific class extracted from actual Notes class names (Apple-dash-list precedent)
    ("C02-class-Apple-paragraph-title",
     'div class="Apple-paragraph-title"',
     '<div class="Apple-paragraph-title">C02-class-Apple-paragraph-title</div><div>body</div>'),

    ("C03-class-Apple-heading",
     'div class="Apple-heading"',
     '<div class="Apple-heading">C03-class-Apple-heading</div><div>body</div>'),

    ("C04-class-Apple-subheading",
     'div class="Apple-subheading"',
     '<div class="Apple-subheading">C04-class-Apple-subheading</div><div>body</div>'),
]


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    # Cleanup prior R/P/S/D/M/C probe notes
    prefixes = ("R0", "P0", "S0", "D0", "M0", "C0")
    existing = [n.name for n in notes.list_notes()
                if any(n.name.startswith(p) for p in prefixes)]
    for name in existing:
        try:
            notes.delete_note(name)
        except notes.NotesError:
            pass
    if existing:
        print(f"Deleted {len(existing)} previous probe notes")
        time.sleep(1.5)

    for label, desc, html in CASES:
        try:
            notes.create_note(html)
            time.sleep(0.4)
        except notes.NotesError as e:
            print(f"FAIL {label}: {e}")
            continue

    time.sleep(1.5)

    print("\n=== Created notes and their get_body output ===\n")
    all_n = notes.list_notes()
    for label, desc, html in CASES:
        # Find a note whose name starts with `label`
        match = next((n for n in all_n if n.name.startswith(label)), None)
        if not match:
            print(f"NOT FOUND: {label}")
            continue
        body = notes.get_body(match.name)
        (OUT / f"{label}.input.html").write_text(html, encoding="utf-8")
        (OUT / f"{label}.body.html").write_text(body, encoding="utf-8")
        # Compact body for printing
        compact = body.replace("\n", " ").strip()
        if len(compact) > 200:
            compact = compact[:200] + "..."
        print(f"{label:40s} | name={match.name!r}")
        print(f"  desc: {desc}")
        print(f"  body: {compact}")
        print()

    print(f"\nSaved to: {OUT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
