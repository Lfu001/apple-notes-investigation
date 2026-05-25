"""Seed synthetic test notes via create_note (S-prefix).

These cover formats that Notes can be coerced into via input HTML (no GUI manipulation needed).
Formats requiring GUI (custom font/color/table/attachment) are NOT covered here — see docs/01.

Run idempotently: deletes existing S-notes first.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes

# (name, html) pairs. Each HTML's first line becomes the note title.
SYNTHETIC: list[tuple[str, str]] = [
    (
        "S01-plain",
        "<div><h1>S01-plain</h1></div>"
        "<div>First paragraph.</div>"
        "<div><br></div>"
        "<div>Second paragraph.</div>"
        "<div><br></div>"
        "<div>Third paragraph.</div>",
    ),
    (
        "S02-softbreak",
        "<div><h1>S02-softbreak</h1></div>"
        "<div>line 1<br>line 2<br>line 3</div>",
    ),
    (
        "S03-headings",
        "<div><h1>S03-headings</h1></div>"
        "<h2>Heading level 2</h2>"
        "<h3>Subheading level 3</h3>"
        "<div>Body paragraph.</div>",
    ),
    (
        "S05-inline-decor",
        "<div><h1>S05-inline-decor</h1></div>"
        "<div>Normal "
        "<b>bold</b> "
        "<i>italic</i> "
        "<u>underline</u> "
        "<s>strike</s> "
        "<b><i>bold-italic</i></b> "
        "back to normal.</div>",
    ),
    (
        "S06-bullet",
        "<div><h1>S06-bullet</h1></div>"
        "<ul>"
        "<li>item one</li>"
        "<li>item two"
        "<ul><li>nested item</li></ul>"
        "</li>"
        "<li>item three</li>"
        "</ul>",
    ),
    (
        "S07-numbered",
        "<div><h1>S07-numbered</h1></div>"
        "<ol>"
        "<li>first</li>"
        "<li>second"
        "<ol><li>nested</li></ol>"
        "</li>"
        "<li>third</li>"
        "</ol>",
    ),
    (
        "S10-link",
        "<div><h1>S10-link</h1></div>"
        '<div>Visit <a href="https://example.com">example</a> for details.</div>'
        '<div>Bare URL: https://www.apple.com</div>',
    ),
]


def main() -> int:
    # Cleanup any pre-existing S-notes
    existing = [n.name for n in notes.list_notes() if n.name.startswith("S")]
    for name in existing:
        print(f"Deleting existing: {name}")
        try:
            notes.delete_note(name)
        except notes.NotesError as e:
            print(f"  WARN: {e}", file=sys.stderr)

    # Wait a moment for deletions to settle
    if existing:
        time.sleep(1.5)

    for name, html in SYNTHETIC:
        print(f"Creating: {name}")
        try:
            notes.create_note(html)
        except notes.NotesError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            return 1

    time.sleep(1.5)
    print("\nFinal listing in HTMLTest:")
    for n in notes.list_notes():
        print(f"  - {n.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
