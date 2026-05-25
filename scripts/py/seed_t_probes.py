"""Seed Phase-9 probe notes (T18-T23) via create_note.

These probes test specific question-shaped hypotheses about what the Notes
HTML parser will or won't translate to a paragraph style / character
attribute. Each probe is a single note whose body interleaves label divs
with variant divs, so the get_body output is self-documenting (you can read
which variant produced which output by reading the dump).

CAVEAT — reconstructed inputs:
    The original input HTML for these probes was not preserved when they
    were first created. The constants below were reconstructed by reading
    each probe's get_body output (in data/probes/HTMLTest/) and inferring
    the input HTML from the variant labels and surviving structure.

    For variants where the parser strips everything, the reconstruction is a
    best-guess at what was tested; the testing *intent* (recorded in the
    label divs) is exact, but the exact input string is not authoritative.

Run:
    uv run python scripts/py/seed_t_probes.py             # seed all T18-T23
    uv run python scripts/py/seed_t_probes.py --filter T20
    uv run python scripts/py/seed_t_probes.py --folder HTMLTest

Re-running deletes the existing probe with the same name first, so it is
idempotent.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes


# Each probe is (note_name, [(variant_label, variant_html), ...]).
# The note body is assembled by interleaving <div>label:</div> with the
# variant HTML, so the dump remains self-documenting.

T18_MONO_PROBE = (
    "T18-mono-probe",
    [
        ("Variant A (bare tt)", "<div><tt>tt only sample</tt></div>"),
        ("Variant B (Courier face + tt)",
         '<div><font face="Courier"><tt>face Courier + tt sample</tt></font></div>'),
        ("Variant C (pre)", "<div><pre>pre sample</pre></div>"),
        ("Variant D (plain body for control)", "<div>plain body sample</div>"),
    ],
)

T19_PROBE = (
    "T19-probe",
    [
        ("Variant A (bare blockquote)", "<blockquote>bare blockquote</blockquote>"),
        ("Variant B (div-wrapped blockquote)",
         "<div><blockquote>div-wrapped blockquote</blockquote></div>"),
        ("Variant C (blockquote class=Apple-blockquote)",
         '<blockquote class="Apple-blockquote">classed blockquote</blockquote>'),
        ("Variant D (plain body control)", "<div>plain body sample</div>"),
        ("Variant E (bare h1)", "<h1>bare h1</h1>"),
        ("Variant F (div-wrapped h1)", "<div><h1>div-wrapped h1</h1></div>"),
    ],
)

T20_TAG_PROBE = (
    "T20-tag-probe",
    [
        ("Variant A code", "<div><code>code sample</code></div>"),
        ("Variant B kbd", "<div><kbd>kbd sample</kbd></div>"),
        ("Variant C samp", "<div><samp>samp sample</samp></div>"),
        ("Variant D var", "<div><var>var sample</var></div>"),
        ("Variant E cite", "<div><cite>cite sample</cite></div>"),
        ("Variant F q", "<div><q>q sample</q></div>"),
        ("Variant G mark", "<mark>mark sample</mark>"),
        ("Variant H small", "<div><small>small sample</small></div>"),
        ("Variant I ins", "<div><ins>ins sample</ins></div>"),
        ("Variant J del", "<div><del>del sample</del></div>"),
        ("Variant K dfn", "<div><dfn>dfn sample</dfn></div>"),
        ("Variant L abbr", "<abbr>abbr sample</abbr>"),
        ("Variant M figure", "<div><figure>figure sample</figure></div>"),
        ("Variant N figcaption", "<div><figcaption>figcaption sample</figcaption></div>"),
        # NOTE (O ruby+rt): original probe's output had a trailing <br> we
        # could not reproduce from the reconstructed input. The substantive
        # observation (ruby info lost, kanji+yomi concatenated as plain text)
        # is identical with or without that <br>.
        ("Variant O ruby+rt", "<ruby>漢字<rt>かんじ</rt></ruby>"),
        ("Variant Z control", "<div>plain body sample</div>"),
    ],
)

T21_HIGHLIGHT_PROBE = (
    "T21-highlight-probe",
    [
        # NOTE: variants that ended up stripped to plain text were written
        # at top level (no <div> wrap) — wrapping in <div> causes Notes to
        # emit a trailing <br>, which is cosmetic but breaks byte equality.
        ("Variant A span bg-color yellow",
         '<span style="background-color: yellow">A span bg yellow</span>'),
        ("Variant B span bg-color hex",
         '<span style="background-color: #FFFF00">B span bg #FFFF00</span>'),
        ("Variant C span background shorthand",
         '<span style="background: yellow">C span background yellow</span>'),
        ("Variant D font with style bg",
         '<font style="background-color: yellow">D font style bg yellow</font>'),
        ("Variant E font background attr",
         '<div><font background="yellow">E font background attr</font></div>'),
        ("Variant F mark with style bg",
         '<mark style="background-color: yellow">F mark + style bg</mark>'),
        ("Variant G apple-highlight property",
         '<div><span style="-apple-highlight: yellow">G -apple-highlight prop</span></div>'),
        ("Variant H bg + fg color",
         '<span style="background-color: yellow; color: black">H bg yellow + color black</span>'),
        ("Variant I webkit text-fill-color",
         '<div><span style="-webkit-text-fill-color: yellow">I webkit text-fill</span></div>'),
        ("Variant Z control", "<div>Z plain body</div>"),
    ],
)

T22_CHECKLIST_LINK_PROBE_VARIANTS = [
    ("Variant A ul+li+checkbox checked",
     '<ul><li><input type="checkbox" checked>A done task</li></ul>'),
    ("Variant B ul+li+checkbox unchecked",
     '<ul><li><input type="checkbox">B pending task</li></ul>'),
    ("Variant C ul.Apple-checklist",
     '<ul class="Apple-checklist"><li>C via class</li></ul>'),
    ("Variant D standalone checkbox",
     '<div><input type="checkbox" checked>D standalone checked</div>'),
    ("Variant E basic a-href",
     '<div><a href="https://example.com">E basic link</a></div>'),
    ("Variant F a-href + Apple-link class",
     '<div><a href="https://example.com" class="Apple-link">F classed link</a></div>'),
    ("Variant G a-href + rel attr",
     '<div><a href="https://example.com" rel="noopener">G rel attr</a></div>'),
    ("Variant H a-name anchor",
     '<div><a name="anchor">H named anchor</a></div>'),
    ("Variant I a-href wrapping bold",
     '<div><a href="https://example.com"><b>I bold inside a</b></a></div>'),
    ("Variant Z control", "<div>Z plain body</div>"),
]

T22_CHECKLIST_LINK_PROBE = ("T22-checklist-link-probe", T22_CHECKLIST_LINK_PROBE_VARIANTS)
T22B_CHECKLIST_LINK_PROBE = ("T22b-checklist-link-probe", T22_CHECKLIST_LINK_PROBE_VARIANTS)

T23_HEADING_COMBO = (
    "T23-heading-combo",
    [
        ("Variant A all-attrs h1",
         '<h1 class="Apple-title" data-paragraph-style="title" role="heading" aria-level="1">A combo h1</h1>'),
        ("Variant B section h1", "<section><h1>B section h1</h1></section>"),
        ("Variant C article header h1",
         "<article><header><h1>C article header h1</h1></header></article>"),
        ("Variant D h1 apple-system font",
         '<h1 style="font: -apple-system-headline">D apple-system-headline</h1>'),
        ("Variant E h1 -webkit-text-style-name",
         '<h1 style="-webkit-text-style-name: title">E -webkit-text-style-name</h1>'),
        ("Variant F h1 -apple-text-style",
         '<h1 style="-apple-text-style: title">F -apple-text-style</h1>'),
        ("Variant G p role=heading",
         '<p role="heading" aria-level="1">G p role=heading aria-level=1</p>'),
        ("Variant H full doc wrapper",
         "<!DOCTYPE html><html><body><h1>H full doc h1</h1></body></html>"),
        ("Variant I h1 Apple-title-list",
         '<h1 class="Apple-title">I Apple-title class</h1>'),
        ("Variant J div role heading",
         '<div role="heading" aria-level="1" style="font-weight: bold; font-size: 24px">J div role heading + bold style</div>'),
        ("Variant K generator meta hint",
         '<meta name="generator" content="Cocoa HTML Writer"><h1>K Cocoa HTML Writer hint</h1>'),
        ("Variant L h1 display+font-feature",
         '<h1 style="font-family: -apple-system; font-weight: bold; font-size: 28px">L stack</h1>'),
        ("Variant M strong bold large",
         '<strong style="display: block; font-size: 24px">M strong block-display</strong>'),
        ("Variant N div+h1 explicit class",
         '<div class="Apple-title"><h1 class="Apple-title">N div+h1 both classed</h1></div>'),
        ("Variant O h1 ApplePragraphStyleType",
         '<h1 class="ApplePragraphStyleType">O ApplePragraphStyleType class</h1>'),
        ("Variant Z control plain body", "<div>Z plain body</div>"),
    ],
)


# label_format is a Python format string with one positional placeholder
# (the variant label). T18-T22 use "{}:" style, T23 uses "--- {} ---" style.
PROBES: list[tuple[str, list[tuple[str, str]], str]] = [
    (*T18_MONO_PROBE, "{}:"),
    (*T19_PROBE, "{}:"),
    (*T20_TAG_PROBE, "{}:"),
    (*T21_HIGHLIGHT_PROBE, "{}:"),
    (*T22_CHECKLIST_LINK_PROBE, "{}:"),
    (*T22B_CHECKLIST_LINK_PROBE, "{}:"),
    (*T23_HEADING_COMBO, "--- {} ---"),
]


def assemble_body(name: str, variants: list[tuple[str, str]],
                  label_format: str = "{}:") -> str:
    """Build a note body that interleaves label divs with variant HTML.

    The title row is `<h1>{name}</h1>` so the note's name matches `name`.
    Each variant becomes:
        <div>{label}</div>
        {variant_html}
    where `{label}` is `label_format.format(variant_label)`.
    """
    parts = [f"<div><h1>{name}</h1></div>"]
    for label, html in variants:
        parts.append(f"<div>{label_format.format(label)}</div>")
        parts.append(html)
    return "".join(parts)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--filter",
        help="Only seed probes whose name contains this substring (e.g. T20)",
    )
    parser.add_argument(
        "--folder",
        default=notes.DEFAULT_FOLDER,
        help=f"Target folder (default: {notes.DEFAULT_FOLDER})",
    )
    parser.add_argument(
        "--account",
        default=notes.DEFAULT_ACCOUNT,
        help=f"Target account (default: {notes.DEFAULT_ACCOUNT})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print bodies that would be created, don't talk to Notes",
    )
    args = parser.parse_args()

    targets = [p for p in PROBES if not args.filter or args.filter in p[0]]
    if not targets:
        print(f"No probes matched --filter={args.filter!r}", file=sys.stderr)
        return 2

    if args.dry_run:
        for name, variants, label_format in targets:
            print(f"--- {name} ---")
            print(assemble_body(name, variants, label_format))
            print()
        return 0

    # Delete existing same-named notes so we can re-seed idempotently
    existing = {n.name for n in notes.list_notes(account=args.account, folder=args.folder)}
    to_delete = [name for name, _, _ in targets if name in existing]
    for name in to_delete:
        print(f"Deleting existing: {name}")
        try:
            notes.delete_note(name, account=args.account, folder=args.folder)
        except notes.NotesError as e:
            print(f"  WARN: {e}", file=sys.stderr)
    if to_delete:
        time.sleep(1.5)

    for name, variants, label_format in targets:
        body = assemble_body(name, variants, label_format)
        print(f"Creating: {name}  ({len(variants)} variants, {len(body)} bytes)")
        try:
            notes.create_note(body, account=args.account, folder=args.folder)
        except notes.NotesError as e:
            print(f"  ERROR: {e}", file=sys.stderr)
            return 1

    # T22b is meant to be T22 after one extra set_body roundtrip
    # (so we can compare URL retention before/after a second pass).
    if any(name == "T22b-checklist-link-probe" for name, *_ in targets):
        time.sleep(1.5)
        print("Roundtripping T22b once via get_body -> set_body...")
        body = notes.get_body("T22b-checklist-link-probe",
                              account=args.account, folder=args.folder)
        notes.set_body("T22b-checklist-link-probe", body,
                       account=args.account, folder=args.folder)

    time.sleep(1.5)
    print("\nSeeded notes in", args.folder, ":")
    for n in notes.list_notes(account=args.account, folder=args.folder):
        if any(n.name == name for name, *_ in targets):
            print(f"  - {n.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
