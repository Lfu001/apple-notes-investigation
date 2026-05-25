#!/usr/bin/env osascript -l JavaScript
// Duplicate a note from one folder to another (or same).
// Env:
//   SRC_NOTE (required)
//   SRC_FOLDER (required)
//   DST_FOLDER (required)
//   DST_NOTE_NAME (optional) — new name after duplicate; if omitted, leave default
//   ACCOUNT (default iCloud)
//
// Output: JSON describing the new duplicate's id/name and body/plaintext sample.

ObjC.import('Foundation');

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const srcFolderName = ObjC.unwrap(env.objectForKey('SRC_FOLDER'));
  const dstFolderName = ObjC.unwrap(env.objectForKey('DST_FOLDER'));
  const srcNoteName = ObjC.unwrap(env.objectForKey('SRC_NOTE'));
  const dstNoteName = ObjC.unwrap(env.objectForKey('DST_NOTE_NAME'));
  if (!srcFolderName) throw new Error('SRC_FOLDER required');
  if (!dstFolderName) throw new Error('DST_FOLDER required');
  if (!srcNoteName) throw new Error('SRC_NOTE required');

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;

  const accounts = Notes.accounts.whose({ name: accountName });
  if (!accounts.length) throw new Error(`Account not found: ${accountName}`);
  const acc = accounts[0];

  const srcFolders = acc.folders.whose({ name: srcFolderName });
  if (!srcFolders.length) throw new Error(`Src folder not found: ${srcFolderName}`);
  const srcFolder = srcFolders[0];

  const dstFolders = acc.folders.whose({ name: dstFolderName });
  if (!dstFolders.length) throw new Error(`Dst folder not found: ${dstFolderName}`);
  const dstFolder = dstFolders[0];

  const matches = srcFolder.notes.whose({ name: srcNoteName });
  if (!matches.length) throw new Error(`Note not found in ${srcFolderName}: ${srcNoteName}`);
  if (matches.length > 1) throw new Error(`Multiple notes: ${srcNoteName}`);
  const src = matches[0];

  let dup;
  try {
    dup = src.duplicate({ to: dstFolder });
  } catch (e) {
    return JSON.stringify({ ok: false, stage: 'duplicate', error: String(e) });
  }

  let renamed = false;
  if (dstNoteName) {
    try {
      dup.name = dstNoteName;
      renamed = true;
    } catch (e) {
      return JSON.stringify({
        ok: false,
        stage: 'rename',
        error: String(e),
        new_id: String(dup.id()),
      });
    }
  }

  return JSON.stringify({
    ok: true,
    new_id: String(dup.id()),
    new_name: String(dup.name()),
    renamed,
    body_sample: dup.body().slice(0, 2000),
    plaintext_sample: dup.plaintext().slice(0, 500),
    attachment_count: dup.attachments().length,
  }, null, 2);
}
