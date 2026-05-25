#!/usr/bin/env osascript -l JavaScript
// Phase 7 probe: previously-unexplored API surfaces.
//
// 1. note.plaintext  — confirm read access and surface format
// 2. note.attachments — every attachment of a note (URL, cid, dates)
// 3. duplicate — does duplicating a note preserve Title/Heading paragraph styles?
//
// Env:
//   NOTE_NAME (required) — which existing note to probe
//   ACCOUNT (default iCloud), FOLDER (default HTMLTest)
//   DUP_TARGET_NAME (optional) — if set, duplicate the note and try to rename
//
// Output: JSON report to stdout

ObjC.import('Foundation');

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';
  const noteName = ObjC.unwrap(env.objectForKey('NOTE_NAME'));
  const dupTarget = ObjC.unwrap(env.objectForKey('DUP_TARGET_NAME'));
  if (!noteName) throw new Error('NOTE_NAME env var is required');

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;

  const accounts = Notes.accounts.whose({ name: accountName });
  if (!accounts.length) throw new Error(`Account not found: ${accountName}`);
  const folders = accounts[0].folders.whose({ name: folderName });
  if (!folders.length) throw new Error(`Folder not found: ${folderName}`);
  const folder = folders[0];

  const matches = folder.notes.whose({ name: noteName });
  if (!matches.length) throw new Error(`Note not found: ${noteName}`);
  if (matches.length > 1) throw new Error(`Multiple notes: ${noteName}`);
  const note = matches[0];

  const report = { noteName, accountName, folderName };

  // ---------- 1. plaintext access ----------
  try {
    const plaintext = note.plaintext();
    report.plaintext = { ok: true, length: plaintext.length, sample: plaintext.slice(0, 500) };
  } catch (e) {
    report.plaintext = { ok: false, error: String(e) };
  }

  // ---------- 2. attachments enumeration ----------
  try {
    const atts = note.attachments();
    report.attachments = { ok: true, count: atts.length, items: [] };
    for (const a of atts) {
      const item = {};
      for (const key of ['id', 'name', 'creationDate', 'modificationDate',
                         'contentIdentifier', 'URL', 'shared']) {
        try {
          // JXA dynamic property access by name
          const v = a[key]();
          item[key] = v === null || v === undefined ? null : String(v);
        } catch (e) {
          item[key] = `<err: ${String(e).slice(0, 80)}>`;
        }
      }
      report.attachments.items.push(item);
    }
  } catch (e) {
    report.attachments = { ok: false, error: String(e) };
  }

  // ---------- 3. duplicate ----------
  if (dupTarget) {
    try {
      // Clean any existing dup target
      const ex = folder.notes.whose({ name: dupTarget });
      for (const n of ex) { try { n.delete(); } catch (_) {} }

      const dup = note.duplicate({ to: folder });
      // Try to set the duplicate's name so we can find it in get_body later
      try { dup.name = dupTarget; } catch (e) {
        report.duplicate_rename_error = String(e);
      }
      report.duplicate = {
        ok: true,
        new_id: String(dup.id()),
        new_name: String(dup.name()),
        body_after_dup: dup.body().slice(0, 1500),
        plaintext_after_dup: dup.plaintext().slice(0, 500),
      };
    } catch (e) {
      report.duplicate = { ok: false, error: String(e) };
    }
  }

  return JSON.stringify(report, null, 2);
}
