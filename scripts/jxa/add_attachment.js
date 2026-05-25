#!/usr/bin/env osascript -l JavaScript
// Add a single attachment to a note. Production version of attempt D.
// Env: NOTE_NAME, FILE_PATH, ACCOUNT (iCloud), FOLDER (HTMLTest)

ObjC.import('Foundation');

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';
  const noteName = ObjC.unwrap(env.objectForKey('NOTE_NAME'));
  const filePath = ObjC.unwrap(env.objectForKey('FILE_PATH'));
  if (!noteName) throw new Error('NOTE_NAME required');
  if (!filePath) throw new Error('FILE_PATH required');

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;

  const folder = Notes.accounts.whose({ name: accountName })[0]
                 .folders.whose({ name: folderName })[0];
  // Manual iteration — whose() unreliable for large folders
  let note = null;
  for (const n of folder.notes()) {
    if (n.name() === noteName) { note = n; break; }
  }
  if (!note) throw new Error(`Note not found: ${noteName}`);

  const att = Notes.make({
    new: 'attachment',
    at: note,
    withData: Path(filePath),
  });

  return JSON.stringify({
    status: 'ok',
    id: String(att.id()),
    name: String(att.name()),
    cid: String(att.contentIdentifier()),
  });
}
