#!/usr/bin/env osascript -l JavaScript
// Get the body (HTML) of a note in the HTMLTest folder.
// Env: NOTE_NAME (required), ACCOUNT (default iCloud), FOLDER (default HTMLTest)
// Output: the raw body HTML to stdout.

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';
  const noteName = ObjC.unwrap(env.objectForKey('NOTE_NAME'));
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
  if (matches.length > 1) throw new Error(`Multiple notes with name: ${noteName} (count=${matches.length})`);

  return matches[0].body();
}
