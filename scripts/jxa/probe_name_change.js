#!/usr/bin/env osascript -l JavaScript
// Probe: does changing note.name preserve body paragraph styles?
// Env: NOTE_NAME, NEW_NAME, ACCOUNT (iCloud), FOLDER (HTMLTest)
ObjC.import('Foundation');

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';
  const noteName = ObjC.unwrap(env.objectForKey('NOTE_NAME'));
  const newName = ObjC.unwrap(env.objectForKey('NEW_NAME'));
  if (!noteName) throw new Error('NOTE_NAME required');
  if (!newName) throw new Error('NEW_NAME required');

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;
  const folder = Notes.accounts.whose({ name: accountName })[0]
                 .folders.whose({ name: folderName })[0];
  let note = null;
  for (const n of folder.notes()) {
    if (n.name() === noteName) { note = n; break; }
  }
  if (!note) throw new Error(`Note not found: ${noteName}`);

  const before = {
    name: note.name(),
    body: note.body().slice(0, 1000),
    plaintext: note.plaintext().slice(0, 200),
  };

  try {
    note.name = newName;
  } catch (e) {
    return JSON.stringify({ ok: false, error: String(e), before });
  }

  // No delay — read immediately
  const after = {
    name: note.name(),
    body: note.body().slice(0, 1000),
    plaintext: note.plaintext().slice(0, 200),
  };

  return JSON.stringify({ ok: true, before, after }, null, 2);
}
