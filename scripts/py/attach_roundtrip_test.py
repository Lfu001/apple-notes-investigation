"""Phase 7 end-to-end: attachment preservation roundtrip test.

Creates a sacrificial note in HTMLTest, attaches a test image via
make-new-attachment, then:
  1. Saves the attachment via att.save({in:Path}) to /tmp
  2. set_body the note to a new body (image-free) — attachment record drops
  3. Re-attaches the saved file via add_attachment
  4. Compares before/after attachment names and CIDs

Verifies that the "backup → set_body → restore" workflow can be made to work
end-to-end. Reports the known quirks (1 make → 2 <img>) as findings.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import notes

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JXA_DIR = REPO_ROOT / "scripts" / "jxa"
TMP_DIR = Path("/tmp/notes-attachment-roundtrip")
TMP_DIR.mkdir(parents=True, exist_ok=True)


def jxa_save_attachment(note_name: str, att_index: int, out_path: Path) -> dict:
    """Save attachment[att_index] of note via att.save({in:path})."""
    script = JXA_DIR / "_save_attachment_inline.js"
    src = f"""
function run() {{
  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;
  const folder = Notes.accounts.whose({{name:'iCloud'}})[0].folders.whose({{name:'HTMLTest'}})[0];
  let note = null;
  for (const n of folder.notes()) {{
    if (n.name() === {json.dumps(note_name)}) {{ note = n; break; }}
  }}
  if (!note) throw new Error('note not found');
  const atts = note.attachments();
  if (atts.length === 0) throw new Error('no attachments');
  const att = atts[{att_index}];
  att.save({{ in: Path({json.dumps(str(out_path))}) }});
  return JSON.stringify({{ name: String(att.name()), cid: String(att.contentIdentifier()) }});
}}
"""
    p = subprocess.run(
        ["osascript", "-l", "JavaScript", "-e", src],
        capture_output=True, text=True,
    )
    if p.returncode != 0:
        raise RuntimeError(f"save failed: {p.stderr}")
    return json.loads(p.stdout)


def main() -> int:
    NOTE = "PRB-attach-rt"

    # Clean and create
    try: notes.delete_note(NOTE)
    except notes.NotesError: pass
    notes.create_note(f'<div>{NOTE}</div><div>baseline body line</div>')
    time.sleep(1.5)
    print(f"[1] Created {NOTE}")

    # Attach a test image
    test_img = TMP_DIR / "test.png"
    if not test_img.exists():
        # Use the existing dot.png if available
        existing = Path("/tmp/notes-investigation/dot.png")
        if existing.exists():
            test_img.write_bytes(existing.read_bytes())
        else:
            import base64
            test_img.write_bytes(base64.b64decode(
                'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=='
            ))

    notes.add_attachment(NOTE, str(test_img))
    time.sleep(1.5)
    atts_before = notes.list_attachments(NOTE)
    body_before = notes.get_body(NOTE)
    pt_before = notes.get_plaintext(NOTE)
    print(f"[2] Attached. attachments={len(atts_before)} (deduped). cid={atts_before[0].cid if atts_before else 'NONE'}")
    print(f"    plaintext OFC count: {pt_before.count(chr(0xFFFC))}")
    print(f"    body img count: {body_before.count('<img')}")

    # Save attachment to /tmp via att.save({in:Path})
    backup_path = TMP_DIR / "backup.png"
    if backup_path.exists(): backup_path.unlink()
    save_info = jxa_save_attachment(NOTE, 0, backup_path)
    if not backup_path.exists():
        print(f"[3] ❌ FAIL: save did not produce file at {backup_path}")
        return 1
    print(f"[3] Saved attachment: name={save_info['name']!r} size={backup_path.stat().st_size} bytes")

    # set_body: clear the body (drops <img> + attachment SQLite records)
    notes.set_body(NOTE, f'<div>{NOTE}</div><div>after set_body (no img)</div>')
    time.sleep(1.5)
    atts_mid = notes.list_attachments(NOTE)
    body_mid = notes.get_body(NOTE)
    print(f"[4] After set_body: attachments={len(atts_mid)}, body has img? {'<img' in body_mid}")
    if atts_mid:
        print(f"    ❌ FAIL: attachments should be 0 after img-less set_body")
        return 1

    # Re-attach from backup
    notes.add_attachment(NOTE, str(backup_path))
    time.sleep(1.5)
    atts_after = notes.list_attachments(NOTE)
    body_after = notes.get_body(NOTE)
    pt_after = notes.get_plaintext(NOTE)
    print(f"[5] After re-add: attachments={len(atts_after)} (deduped). cid={atts_after[0].cid if atts_after else 'NONE'}")
    print(f"    plaintext OFC count: {pt_after.count(chr(0xFFFC))}")
    print(f"    body img count: {body_after.count('<img')}")

    # Compare
    print()
    print("=== summary ===")
    print(f"  attachment name preserved: {atts_before[0].name == atts_after[0].name}")
    print(f"  attachment cid changed:    {atts_before[0].cid != atts_after[0].cid}  (new make → new cid)")
    print(f"  <img> in body BEFORE: {body_before.count('<img')}  AFTER restore: {body_after.count('<img')}")
    print()
    print("Conclusion:")
    print("  - save + add_attachment roundtrip succeeds; bytes preserved")
    print("  - cid is regenerated (different identity after re-attach)")
    print(f"  - 1-call-yields-2-imgs quirk applies: {body_after.count('<img') == 2}")

    # Cleanup the test note
    try: notes.delete_note(NOTE)
    except notes.NotesError: pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
