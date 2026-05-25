"""Thin Python wrapper around JXA scripts that talk to Notes.app.

All operations are scoped to a single (account, folder) pair to prevent
accidental modification of unrelated notes. Defaults to iCloud / HTMLTest.
"""
from __future__ import annotations

import json
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
JXA_DIR = REPO_ROOT / "scripts" / "jxa"

DEFAULT_ACCOUNT = "iCloud"
DEFAULT_FOLDER = "HTMLTest"


class NotesError(RuntimeError):
    pass


def _run_jxa(script: str, env_extra: dict[str, str], stdin_bytes: bytes | None = None) -> str:
    path = JXA_DIR / script
    if not path.exists():
        raise NotesError(f"JXA script not found: {path}")
    env = os.environ.copy()
    env.update(env_extra)
    proc = subprocess.run(
        ["osascript", "-l", "JavaScript", str(path)],
        input=stdin_bytes,
        env=env,
        capture_output=True,
    )
    if proc.returncode != 0:
        stderr = proc.stderr.decode("utf-8", errors="replace")
        raise NotesError(f"{script} failed (rc={proc.returncode}): {stderr.strip()}")
    return proc.stdout.decode("utf-8", errors="replace")


@dataclass
class NoteRef:
    name: str
    id: str


def list_notes(account: str = DEFAULT_ACCOUNT, folder: str = DEFAULT_FOLDER) -> list[NoteRef]:
    out = _run_jxa("list_notes.js", {"ACCOUNT": account, "FOLDER": folder})
    return [NoteRef(name=item["name"], id=item["id"]) for item in json.loads(out)]


def get_body(note_name: str, account: str = DEFAULT_ACCOUNT, folder: str = DEFAULT_FOLDER) -> str:
    return _run_jxa(
        "get_body.js",
        {"ACCOUNT": account, "FOLDER": folder, "NOTE_NAME": note_name},
    ).rstrip("\n")  # JXA `return` adds a trailing newline


def set_body(
    note_name: str,
    html: str,
    account: str = DEFAULT_ACCOUNT,
    folder: str = DEFAULT_FOLDER,
) -> None:
    with tempfile.NamedTemporaryFile(
        mode="w", encoding="utf-8", suffix=".html", delete=False
    ) as tmp:
        tmp.write(html)
        tmp_path = tmp.name
    try:
        _run_jxa(
            "set_body.js",
            {
                "ACCOUNT": account,
                "FOLDER": folder,
                "NOTE_NAME": note_name,
                "HTML_FILE": tmp_path,
            },
        )
    finally:
        os.unlink(tmp_path)


def create_note(
    body: str, account: str = DEFAULT_ACCOUNT, folder: str = DEFAULT_FOLDER
) -> dict:
    out = _run_jxa(
        "create_note.js",
        {"ACCOUNT": account, "FOLDER": folder, "NOTE_BODY": body},
    )
    return json.loads(out)


def delete_note(
    note_name: str, account: str = DEFAULT_ACCOUNT, folder: str = DEFAULT_FOLDER
) -> dict:
    out = _run_jxa(
        "delete_note.js",
        {"ACCOUNT": account, "FOLDER": folder, "NOTE_NAME": note_name},
    )
    return json.loads(out)


@dataclass
class Attachment:
    id: str
    name: str | None
    cid: str
    creation_date: str
    modification_date: str


def list_attachments(
    note_name: str, account: str = DEFAULT_ACCOUNT, folder: str = DEFAULT_FOLDER
) -> list[Attachment]:
    """List attachments of a note via JXA. Note: 1 make-new-attachment call
    currently produces 2 entries here (Notes API quirk — see docs/07 §2.4)."""
    out = _run_jxa(
        "probe_api_surface.js",
        {"ACCOUNT": account, "FOLDER": folder, "NOTE_NAME": note_name},
    )
    data = json.loads(out)
    if not data.get("attachments", {}).get("ok"):
        return []
    seen_ids = set()
    result = []
    for item in data["attachments"]["items"]:
        if item["id"] in seen_ids:
            continue  # dedupe the well-known 1->2 quirk
        seen_ids.add(item["id"])
        result.append(Attachment(
            id=item["id"],
            name=None if item["name"] in ("None", "null") else item["name"],
            cid=item["contentIdentifier"],
            creation_date=item["creationDate"],
            modification_date=item["modificationDate"],
        ))
    return result


def get_plaintext(
    note_name: str, account: str = DEFAULT_ACCOUNT, folder: str = DEFAULT_FOLDER
) -> str:
    """Return note.plaintext (read-only). Attachment positions are marked
    with U+FFFC (\\uFFFC, '￼'). See docs/07 §2.1."""
    out = _run_jxa(
        "probe_api_surface.js",
        {"ACCOUNT": account, "FOLDER": folder, "NOTE_NAME": note_name},
    )
    data = json.loads(out)
    if not data.get("plaintext", {}).get("ok"):
        raise NotesError(f"plaintext read failed: {data}")
    return data["plaintext"]["sample"]


def add_attachment(
    note_name: str,
    file_path: str,
    account: str = DEFAULT_ACCOUNT,
    folder: str = DEFAULT_FOLDER,
) -> dict:
    """Add a single attachment to the end of a note's body.
    Does NOT destroy paragraph styles (Title/Heading preserved).

    ⚠️ Known quirk: 1 call results in 2 <img> tags in body HTML, both pointing
    to the same attachment record. See docs/07 §2.4.
    """
    out = _run_jxa(
        "add_attachment.js",
        {
            "ACCOUNT": account,
            "FOLDER": folder,
            "NOTE_NAME": note_name,
            "FILE_PATH": file_path,
        },
    )
    return json.loads(out)


def rename_note(
    note_name: str,
    new_name: str,
    account: str = DEFAULT_ACCOUNT,
    folder: str = DEFAULT_FOLDER,
) -> dict:
    """Change note.name. Body is left untouched — paragraph styles preserved.

    ⚠️ NOT PERSISTENT: scripting allows the name and the body's first line
    to diverge initially, but a subsequent edit operation (e.g.
    make-new-attachment) causes Notes to recompute name from the body's
    first line, discarding the rename. See docs/07 §2.6.

    For a stable name change, you must change the body's first line, which
    requires set_body and risks paragraph-style destruction. So this function
    is mostly diagnostic — use it to probe behavior, not as a primary edit
    operation.
    """
    out = _run_jxa(
        "probe_name_change.js",
        {
            "ACCOUNT": account,
            "FOLDER": folder,
            "NOTE_NAME": note_name,
            "NEW_NAME": new_name,
        },
    )
    return json.loads(out)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("usage: notes.py {list|get NAME|smoke}", file=sys.stderr)
        sys.exit(2)

    cmd = sys.argv[1]
    if cmd == "list":
        for n in list_notes():
            print(f"{n.name}\t{n.id}")
    elif cmd == "get":
        print(get_body(sys.argv[2]))
    elif cmd == "smoke":
        # Round-trip smoke test
        import time

        name = "_smoke_test"
        try:
            delete_note(name)
        except NotesError:
            pass
        body_html = "<div><h1>_smoke_test</h1></div><div>hello world</div>"
        create_note(body_html)
        time.sleep(1.5)
        try:
            got = get_body(name)
            print("--- get_body returned ---")
            print(got)
        finally:
            delete_note(name)
            print("--- smoke test cleaned up ---")
    else:
        print(f"unknown command: {cmd}", file=sys.stderr)
        sys.exit(2)
