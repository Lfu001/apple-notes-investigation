"""Phase 6 round 3: UI scripting (menu commands / keyboard shortcuts).

Strategy: bypass the body HTML parser entirely. Use AppleScript System Events
to drive Notes.app's UI:
  1. Create a note via set_body with plain content
  2. Open the note (Notes.show)
  3. Select all
  4. Apply Format → Title via Cmd+Shift+T (Heading: Cmd+Shift+H, Subheading: J)

This is slow and brittle but may be the only way to set Notes' internal
paragraph styles when starting from set_body content.
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes


def applescript(src: str) -> str:
    p = subprocess.run(
        ["osascript", "-e", src],
        capture_output=True,
        text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"AppleScript failed: {p.stderr}")
    return p.stdout.strip()


def make_and_apply_title(label: str, html_body: str) -> None:
    """Create a note, then use UI to apply Title to the first line."""
    # Cleanup any prior matching name
    try:
        notes.delete_note(label)
    except notes.NotesError:
        pass

    # Make a fresh note with the given body
    notes.create_note(html_body)
    time.sleep(1.0)

    # Open the note, focus the window, select the first line, apply Title
    # Notes' shortcut: Cmd+Shift+T = Title, Cmd+Shift+H = Heading, J = Subheading,
    # B = Body, M = Monostyled, single quote = Block Quote
    src = f'''
tell application "Notes"
    activate
    set theFolder to folder "HTMLTest" of account "iCloud"
    set matches to (every note of theFolder whose name is "{label}")
    if (count of matches) is 0 then error "note not found: {label}"
    show item 1 of matches
end tell
delay 0.8
tell application "System Events"
    tell process "Notes"
        set frontmost to true
        delay 0.3
        -- Move to start of document
        key code 126 using {{command down}}    -- Cmd+Up = top of note
        delay 0.3
        -- Select to end of line
        key code 124 using {{command down, shift down}}  -- Cmd+Shift+Right = select to line end
        delay 0.3
        -- Apply Title via Cmd+Shift+T
        keystroke "T" using {{command down, shift down}}
        delay 0.5
    end tell
end tell
'''
    applescript(src)
    time.sleep(1.0)


if __name__ == "__main__":
    label = "U01-ui-title-applied"
    body_html = f"<div>{label}</div><div>regular body line</div>"
    try:
        make_and_apply_title(label, body_html)
        print(f"\nCreated {label!r} and applied Cmd+Shift+T via UI scripting")
        print("--- get_body after UI scripting ---")
        print(notes.get_body(label))
    except Exception as e:
        print(f"FAILED: {e}", file=sys.stderr)
        sys.exit(1)
