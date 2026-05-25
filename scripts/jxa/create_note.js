#!/usr/bin/env osascript -l JavaScript
// Create a new note in the HTMLTest folder with given body.
// Env: NOTE_BODY (raw HTML or text, can include first-line as title),
//      ACCOUNT (default iCloud), FOLDER (default HTMLTest)

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';
  const body = ObjC.unwrap(env.objectForKey('NOTE_BODY'));
  if (!body) throw new Error('NOTE_BODY env var is required');

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;

  const accounts = Notes.accounts.whose({ name: accountName });
  if (!accounts.length) throw new Error(`Account not found: ${accountName}`);
  const folders = accounts[0].folders.whose({ name: folderName });
  if (!folders.length) throw new Error(`Folder not found: ${folderName}`);
  const folder = folders[0];

  const note = Notes.Note({ body: body });
  folder.notes.push(note);
  return JSON.stringify({ status: 'ok', name: note.name(), id: note.id() });
}
