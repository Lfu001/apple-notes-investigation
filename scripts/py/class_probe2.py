"""Phase 6 round 3: deeper class-name probe.

User confirmed that <ul class="Apple-dash-list"> actually triggers the
internal "Dashed List" paragraph style — not just preserves the class string,
but creates the real paragraph type in Notes' model. So the precedent is:
  Apple-* class on a specific element name triggers a specific paragraph
  style. We need to discover the others.

This probe:
  1. Tries NSTextList-marker-derived variants on <ul> and <ol>
  2. Tries com.apple.*, IC*, NS* prefixes
  3. Tries <h1>/<p>/<header> with paragraph-style class candidates
  4. Records WHICH inputs result in a class attribute surviving round-trip
     (= a recognized class)

Class survival in get_body output is the indicator. The user can then
visually confirm whether the surviving class actually creates a real
paragraph style or just decorative bold-body output.
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT = REPO_ROOT / "data" / "class_probe"


# NSTextList markers — formats Cocoa supports for ordered/unordered lists
# https://developer.apple.com/documentation/uikit/nstextlist
LIST_MARKER_NAMES = [
    "box", "check", "circle", "diamond", "disc", "hyphen", "square",
    "lower-alpha", "lower-roman", "upper-alpha", "upper-roman",
    "decimal", "octal", "lowercase-hexadecimal", "uppercase-hexadecimal",
]

# Try Apple-X-list and a few other formats for list types
LIST_CANDIDATES: list[tuple[str, str]] = []
for marker in LIST_MARKER_NAMES:
    LIST_CANDIDATES.append((f"Apple-{marker}-list", "ul"))
    LIST_CANDIDATES.append((f"Apple-{marker}-list", "ol"))


# Title/Heading/Subheading/Body candidates — try many element/class combos
PARAGRAPH_CANDIDATES: list[tuple[str, str]] = []  # (class, element)

# Apple-paragraph-X
for kind in ["title", "Title", "heading", "Heading", "subheading", "Subheading",
             "body", "Body", "monostyled", "Monostyled", "block-quote", "BlockQuote"]:
    for elem in ["div", "p", "h1", "header"]:
        PARAGRAPH_CANDIDATES.append((f"Apple-paragraph-{kind}", elem))

# Apple-style-X
for kind in ["title", "heading", "subheading", "body", "monostyled", "block-quote"]:
    for elem in ["div", "p", "h1"]:
        PARAGRAPH_CANDIDATES.append((f"Apple-style-{kind}", elem))

# Apple-X
for kind in ["title", "heading", "subheading", "body", "monostyled", "block-quote",
             "blockquote", "quote"]:
    for elem in ["div", "p", "h1", "blockquote"]:
        PARAGRAPH_CANDIDATES.append((f"Apple-{kind}", elem))

# IC-prefix (Notes' internal class prefix as seen in ICScriptingNote etc.)
for kind in ["Title", "Heading", "Subheading", "Body", "Monostyled", "BlockQuote",
             "title", "heading", "subheading"]:
    for elem in ["div", "p"]:
        PARAGRAPH_CANDIDATES.append((f"IC-{kind}", elem))
        PARAGRAPH_CANDIDATES.append((f"IC{kind}", elem))
        PARAGRAPH_CANDIDATES.append((f"ic-{kind.lower()}", elem))

# com.apple.* identifier-style
for kind in ["title", "heading", "subheading", "monostyled", "block-quote"]:
    PARAGRAPH_CANDIDATES.append((f"com.apple.notes.{kind}", "div"))
    PARAGRAPH_CANDIDATES.append((f"com-apple-notes-{kind}", "div"))

# Reverse-DNS-as-class with periods replaced by dashes
for kind in ["title", "heading"]:
    PARAGRAPH_CANDIDATES.append((f"com-apple-paragraphstyle-{kind}", "div"))

# x-apple-* prefix (sometimes used in Cocoa CSS)
for kind in ["title", "heading", "subheading", "monostyled"]:
    PARAGRAPH_CANDIDATES.append((f"x-apple-{kind}", "div"))
    PARAGRAPH_CANDIDATES.append((f"x-apple-paragraph-{kind}", "div"))

# Apple-text-style-* (CSS -apple-text-style-name precedent)
for kind in ["title-1", "title-2", "title-3", "title", "headline", "subheadline",
             "body", "callout", "footnote", "caption", "caption-1"]:
    PARAGRAPH_CANDIDATES.append((f"Apple-text-style-{kind}", "div"))
    # Also as font-style on h1
    PARAGRAPH_CANDIDATES.append((f"Apple-text-style-{kind}", "h1"))


def probe_one(class_name: str, element: str) -> tuple[bool, str]:
    """Return (class_preserved_in_get_body, body_html)."""
    label = f"prb-{element}-{abs(hash((class_name, element))) % 100000}"
    if element == "ul" or element == "ol":
        html = f'<{element} class="{class_name}"><li>{label}</li></{element}><div>body</div>'
    else:
        html = f'<{element} class="{class_name}">{label}</{element}><div>body</div>'
    try:
        notes.delete_note(label)
    except notes.NotesError:
        pass
    res = notes.create_note(html)
    time.sleep(0.2)
    body = notes.get_body(res["name"])
    preserved = f'class="{class_name}"' in body
    return preserved, body


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    candidates = LIST_CANDIDATES + PARAGRAPH_CANDIDATES
    print(f"Probing {len(candidates)} class/element combinations…\n")

    preserved_results = []
    for i, (cls, elem) in enumerate(candidates):
        try:
            pres, body = probe_one(cls, elem)
        except Exception as e:
            print(f"  [{i:3d}] ERROR  {cls} on {elem}: {e}")
            continue
        if pres:
            preserved_results.append({"class": cls, "elem": elem, "body": body})
            compact = body.replace("\n", " ").strip()
            if len(compact) > 110:
                compact = compact[:110] + "…"
            print(f"  ★ [{i:3d}] PRESERVED  class={cls!r} elem={elem}")
            print(f"           body: {compact}")

    print(f"\n=== Found {len(preserved_results)} preserved class/element combos ===")
    (OUT / "deep_results.json").write_text(
        json.dumps(preserved_results, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
