"""Exhaustive Apple-* class probe.

For each (element, class_name) candidate, create a fresh note and capture
get_body output. Compare against a baseline (plain <div>X</div>): if the
output differs, the class is recognized by Notes' HTML parser.

The presence/absence of class attribute in get_body reveals which class names
the parser preserves vs strips.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
OUT = REPO_ROOT / "data" / "class_probe"


# Class name candidates — broad coverage of naming conventions and concepts
CLASS_CANDIDATES = [
    # Known precedent
    "Apple-dash-list",
    # Direct variants
    "Apple-bullet-list",
    "Apple-numbered-list",
    "Apple-checklist",
    "Apple-checklist-list",
    "Apple-check-list",
    # Title / heading / subheading
    "Apple-title",
    "Apple-Title",
    "Apple-heading",
    "Apple-Heading",
    "Apple-subheading",
    "Apple-Subheading",
    "Apple-section-title",
    "Apple-section-heading",
    "Apple-paragraph-title",
    "Apple-paragraph-heading",
    "Apple-paragraph-subheading",
    "Apple-title-style",
    "Apple-heading-style",
    "Apple-block-title",
    "Apple-block-heading",
    "Apple-title-block",
    "Apple-style-title",
    "Apple-style-heading",
    "Apple-style-subheading",
    # WebKit / Mail known prefixes
    "Apple-style-span",
    "Apple-converted-space",
    "Apple-interchange-newline",
    "Apple-tab-span",
    # Notes-specific guesses based on `Apple-dash-list` formula (-list suffix)
    "Apple-title-list",
    "Apple-heading-list",
    # Capital variants
    "AppleTitle",
    "AppleHeading",
    "AppleSubheading",
    # MailKit / NSAttributedString-style
    "NSAttributedString-Title",
    "x-apple-title",
    "x-apple-heading",
    # All-lowercase
    "apple-title",
    "apple-heading",
    "apple-subheading",
    "apple-paragraph-title",
    # Block quote / monostyled / body
    "Apple-blockquote",
    "Apple-block-quote",
    "Apple-quote",
    "Apple-monostyled",
    "Apple-monospace",
    "Apple-pre",
    "Apple-body",
    "Apple-paragraph-body",
    "Apple-paragraph-block-quote",
    "Apple-paragraph-monostyled",
]


def probe_class(class_name: str, element: str = "div") -> tuple[str, str, str]:
    """Create a note with <{element} class="{class_name}">X</{element}>.
    Return (note_name_assigned, body_returned, class_preserved_str).
    """
    # Use a short unique label as the visible text (without class name in it,
    # so we can accurately detect whether the class= attribute survived)
    label = f"probe-{element}-{abs(hash(class_name)) % 100000}"
    html = f'<{element} class="{class_name}">{label}</{element}><div>body</div>'
    try:
        notes.delete_note(label)
    except notes.NotesError:
        pass
    res = notes.create_note(html)
    time.sleep(0.25)
    body = notes.get_body(res["name"])
    # Detect actual class attribute preservation
    preserved = f'class="{class_name}"' in body
    return res["name"], body, "YES" if preserved else "no"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)

    print(f"{'class':45s} {'elem':6s} {'preserved':10s} {'body sample'}")
    print("-" * 130)

    results = []
    # Test on <div> first (most common)
    for cls in CLASS_CANDIDATES:
        try:
            name, body, pres = probe_class(cls, "div")
        except Exception as e:
            print(f"{cls:45s} {'div':6s} ERROR  {e}")
            continue
        compact = body.replace("\n", " ").strip()
        if len(compact) > 80:
            compact = compact[:80] + "…"
        marker = "★" if pres == "YES" else " "
        print(f"{marker} {cls:43s} {'div':6s} {pres:10s} {compact}")
        results.append({"cls": cls, "elem": "div", "preserved": pres == "YES", "body": body})

    # Also test on <ul> for list-related classes (mirroring Apple-dash-list precedent)
    print()
    list_cls = [c for c in CLASS_CANDIDATES if "list" in c.lower() or "check" in c.lower()]
    for cls in list_cls:
        try:
            label = f"probe-ul-{abs(hash(cls)) % 100000}"
            html = f'<ul class="{cls}"><li>{label}</li></ul><div>body</div>'
            try: notes.delete_note(label)
            except: pass
            res = notes.create_note(html)
            time.sleep(0.25)
            body = notes.get_body(res["name"])
            pres = f'class="{cls}"' in body
            compact = body.replace("\n", " ").strip()
            if len(compact) > 100:
                compact = compact[:100] + "…"
            marker = "★" if pres else " "
            print(f"{marker} {cls:43s} {'ul':6s} {'YES' if pres else 'no':10s} {compact}")
        except Exception as e:
            print(f"  {cls:43s} {'ul':6s} ERROR  {e}")

    # Write results JSON
    import json
    (OUT / "results.json").write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"\nResults saved: {OUT}/results.json")

    preserved_count = sum(1 for r in results if r["preserved"])
    print(f"\nSummary: {preserved_count}/{len(results)} class names preserved on <div>")
    return 0


if __name__ == "__main__":
    sys.exit(main())
