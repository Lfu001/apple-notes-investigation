"""Practical edit recipe library.

High-level functions for safely editing GUI-created Notes.app notes.
See docs/02-recipe.md for the usage guide and docs/01-facts.md for the
underlying constraints (what set_body destroys vs preserves).

IMPORTANT: Phase 1 (T-note) testing revealed that set_body destroys some
content (images, attachments, links, highlights, checklist state). Always call
`check_safety` before editing notes that may contain such content.
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes

from bs4 import BeautifulSoup, NavigableString

# Default delay between set_body and the next get_body. The right value depends on
# iCloud sync latency; 1.5s has been reliable in our test environment.
DEFAULT_DELAY = 1.5


@dataclass
class SafetyReport:
    safe: bool
    visible_destroyers: list[str]   # Detected in body HTML (we CAN see these)
    attachment_destroyers: list[str]  # Detected via note.attachments() — Phase 7
    note: str                       # Reminder text about invisible losses

    def __str__(self) -> str:
        all_issues = self.visible_destroyers + self.attachment_destroyers
        if self.safe:
            return f"SAFE (visible body content is editable). NOTE: {self.note}"
        return f"UNSAFE — would destroy: {', '.join(all_issues)}. {self.note}"


_INVISIBLE_LOSS_NOTE = (
    "Links/highlights/checklist-state/block-quote/soft-breaks/font-family/"
    "Title-Heading-Subheading-paragraphs cannot be detected programmatically; "
    "if the note has any of these, they will be lost on set_body. "
    "(Monostyled paragraphs survive set_body — Phase 9.)"
)


def check_safety_html(body: str) -> SafetyReport:
    """Inspect raw body HTML only (no attachment lookup). See check_safety
    for the recommended `note.attachments()`-aware version."""
    soup = BeautifulSoup(body, "html.parser")
    issues = []
    if soup.find("img"):
        issues.append("image(s)")
    for obj in soup.find_all("object"):
        # Tables also use <object> wrapper; only flag if no <table> inside
        if not obj.find("table"):
            issues.append("attachment (object without table)")
    return SafetyReport(
        safe=not issues,
        visible_destroyers=issues,
        attachment_destroyers=[],
        note=_INVISIBLE_LOSS_NOTE,
    )


_IMAGE_EXTS = (".jpeg", ".jpg", ".png", ".gif", ".heic", ".heif", ".bmp", ".tiff", ".webp")


def check_safety(note_name: str) -> SafetyReport:
    """Inspect the note for content that `set_body` would destroy.

    Phase 7 enhancement: uses `note.attachments()` for reliable detection
    instead of relying on body HTML alone. Attachment-bearing elements
    (images, PDFs) appear in the attachments collection regardless of body
    HTML serialization.

    DETECTABLE destroyers (returned in the report):
      - body HTML <img> — image
      - body HTML <object> without <table> — non-table attachment
      - attachments with image extensions (.jpeg/.png/etc.) — image
      - attachments with .pdf extension — PDF
      - attachments with name=None — table (NOT destructive, body has <object><table>)
      - attachments with other extensions — unknown attachment kind

    UNDETECTABLE losses (mentioned in `note`, cannot be guarded against):
      - Hyperlinks (URL info missing from body and attachments)
      - Highlights / background colors
      - Checklist checkbox states (rendered as plain <ul>)
      - Block Quote paragraphs (rendered as plain <div>)
      - Soft breaks (rendered as spaces)
      - Custom font family (face attr will be dropped, size preserved;
        exception: `-apple-system*` font tokens are preserved as face — Phase 9)
      - Title / Heading / Subheading paragraph styles

    SAFE (Phase 9 reclassification — these used to be in the destructive list):
      - Monostyled paragraphs (`<tt>`/`<pre>`/`<code>`/`<kbd>`/`<samp>` →
        all create real Monostyled paragraph style in GUI, and existing
        Monostyled paragraphs survive set_body)

    NOTE: Once you've called set_body on a note, destructive content is already
    gone. Call this on a fresh (un-set) note body.
    """
    body = notes.get_body(note_name)
    base = check_safety_html(body)

    # Phase 7: also consult note.attachments() for reliable detection
    attachment_issues = []
    try:
        for a in notes.list_attachments(note_name):
            name = a.name or ""
            lower = name.lower()
            if lower.endswith(_IMAGE_EXTS):
                attachment_issues.append(f"image: {name}")
            elif lower.endswith(".pdf"):
                attachment_issues.append(f"PDF: {name}")
            elif a.name is None:
                # Tables are attachments with name=None; body HTML has <object><table>,
                # which set_body preserves. Not destructive.
                pass
            else:
                attachment_issues.append(f"attachment: {name}")
    except notes.NotesError:
        # If JXA probe fails, fall back silently to HTML-only check
        pass

    return SafetyReport(
        safe=not (base.visible_destroyers or attachment_issues),
        visible_destroyers=base.visible_destroyers,
        attachment_destroyers=attachment_issues,
        note=_INVISIBLE_LOSS_NOTE,
    )


def normalize(note_name: str, delay: float = DEFAULT_DELAY, max_rounds: int = 5) -> str:
    """Return a fixed-point body for the note (research / convergence tool).

    NOTE: Each round invokes set_body which permanently degrades any
    Title/Heading/Subheading paragraph styles (see docs/01-facts.md §3.1).
    Use this only when the note has no paragraph-style content to preserve.
    """
    prev = notes.get_body(note_name)
    for _ in range(max_rounds):
        notes.set_body(note_name, prev)
        time.sleep(delay)
        cur = notes.get_body(note_name)
        if cur == prev:
            return cur
        prev = cur
    raise RuntimeError(f"Note did not converge in {max_rounds} rounds: {note_name}")


def replace_unique_text(note_name: str, needle: str, replacement: str,
                        delay: float = DEFAULT_DELAY) -> None:
    """Replace a unique substring in the note's text content.

    The substring must occur in exactly one NavigableString in the document.
    """
    body = normalize(note_name, delay)
    soup = BeautifulSoup(body, "html.parser")
    matches = [s for s in soup.find_all(string=True)
               if isinstance(s, NavigableString) and needle in str(s)]
    if not matches:
        raise ValueError(f"text not found: {needle!r}")
    if len(matches) > 1:
        raise ValueError(f"text is ambiguous ({len(matches)} matches): {needle!r}")
    target = matches[0]
    new_text = str(target).replace(needle, replacement)
    target.replace_with(NavigableString(new_text))
    notes.set_body(note_name, str(soup))


def append_paragraph(note_name: str, text: str, delay: float = DEFAULT_DELAY) -> None:
    """Append a new plain-text paragraph to the end of the note."""
    body = normalize(note_name, delay)
    soup = BeautifulSoup(body, "html.parser")
    new_div = soup.new_tag("div")
    new_div.string = text
    soup.append(new_div)
    notes.set_body(note_name, str(soup))


def append_list_item(note_name: str, text: str, delay: float = DEFAULT_DELAY) -> None:
    """Append a new <li> to the first <ul> or <ol> in the note."""
    body = normalize(note_name, delay)
    soup = BeautifulSoup(body, "html.parser")
    container = soup.find(["ul", "ol"])
    if container is None:
        raise ValueError("no <ul> or <ol> found in note")
    new_li = soup.new_tag("li")
    new_li.string = text
    container.append(new_li)
    notes.set_body(note_name, str(soup))


def remove_list_item(note_name: str, marker: str, delay: float = DEFAULT_DELAY) -> None:
    """Remove the first <li> whose text contains `marker`."""
    body = normalize(note_name, delay)
    soup = BeautifulSoup(body, "html.parser")
    targets = [li for li in soup.find_all("li") if marker in li.get_text()]
    if not targets:
        raise ValueError(f"no <li> matching: {marker!r}")
    targets[0].decompose()
    notes.set_body(note_name, str(soup))


def append_link(note_name: str, text: str, url: str,
                delay: float = DEFAULT_DELAY) -> None:
    """Append a paragraph containing a hyperlink to the end of the note.

    Phase 9 finding: `<a href="X">text</a>` via set_body creates a working
    hyperlink in the GUI (URL stored internally). The link is functional
    when clicked, but the URL is NOT visible in subsequent get_body output
    (only `<u>text</u>` shows). This means the link will be DESTROYED if you
    call set_body again on the same note.

    Practical use: write-once append for new links. Do NOT use on notes
    whose existing links you want to preserve through editing — those links
    are already invisible to get_body and will be lost on any set_body call.
    """
    body = normalize(note_name, delay)
    soup = BeautifulSoup(body, "html.parser")
    new_div = soup.new_tag("div")
    anchor = soup.new_tag("a", href=url)
    anchor.string = text
    new_div.append(anchor)
    soup.append(new_div)
    notes.set_body(note_name, str(soup))


def color_text(note_name: str, needle: str, hex_color: str,
               delay: float = DEFAULT_DELAY) -> None:
    """Wrap a unique substring in <font color="#XXXXXX"> to give it a color.

    `hex_color` may be 6-hex (e.g. "#FF0000") or 3-hex (e.g. "#F00").
    Notes normalizes this to 6-hex on round-trip.
    """
    if not hex_color.startswith("#"):
        hex_color = "#" + hex_color
    body = normalize(note_name, delay)
    soup = BeautifulSoup(body, "html.parser")
    matches = [s for s in soup.find_all(string=True)
               if isinstance(s, NavigableString) and needle in str(s)]
    if not matches:
        raise ValueError(f"text not found: {needle!r}")
    if len(matches) > 1:
        raise ValueError(f"text is ambiguous: {needle!r}")
    target = matches[0]
    text = str(target)
    idx = text.index(needle)
    head, tail = text[:idx], text[idx + len(needle):]
    parent = target.parent
    target.replace_with(NavigableString(head))
    # Locate the newly inserted head node
    head_node = None
    for c in parent.contents:
        if isinstance(c, NavigableString) and str(c) == head:
            head_node = c
            break
    if head_node is None:
        raise RuntimeError("internal: failed to locate head node")
    font_tag = soup.new_tag("font", color=hex_color)
    font_tag.string = needle
    head_node.insert_after(font_tag)
    font_tag.insert_after(NavigableString(tail))
    notes.set_body(note_name, str(soup))


# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Mini CLI for ad-hoc edits.
    import argparse

    p = argparse.ArgumentParser(description="Safe Notes.app editing recipes")
    sub = p.add_subparsers(dest="cmd", required=True)

    sc = sub.add_parser("safety", help="Check whether a note is safe to edit")
    sc.add_argument("note")

    rp = sub.add_parser("replace", help="Replace a unique substring")
    rp.add_argument("note")
    rp.add_argument("needle")
    rp.add_argument("replacement")

    ap = sub.add_parser("append-para", help="Append plain paragraph")
    ap.add_argument("note")
    ap.add_argument("text")

    li = sub.add_parser("append-li", help="Append a list item")
    li.add_argument("note")
    li.add_argument("text")

    rl = sub.add_parser("remove-li", help="Remove an <li> by text marker")
    rl.add_argument("note")
    rl.add_argument("marker")

    cl = sub.add_parser("color", help="Color a unique substring")
    cl.add_argument("note")
    cl.add_argument("needle")
    cl.add_argument("hex")

    lk = sub.add_parser("append-link", help="Append a new hyperlink paragraph (write-once)")
    lk.add_argument("note")
    lk.add_argument("text")
    lk.add_argument("url")

    args = p.parse_args()
    if args.cmd == "safety":
        report = check_safety(args.note)
        print(report)
        sys.exit(0 if report.safe else 1)
    elif args.cmd == "replace":
        replace_unique_text(args.note, args.needle, args.replacement)
    elif args.cmd == "append-para":
        append_paragraph(args.note, args.text)
    elif args.cmd == "append-li":
        append_list_item(args.note, args.text)
    elif args.cmd == "remove-li":
        remove_list_item(args.note, args.marker)
    elif args.cmd == "color":
        color_text(args.note, args.needle, args.hex)
    elif args.cmd == "append-link":
        append_link(args.note, args.text, args.url)
    print(f"OK: {args.cmd}")
