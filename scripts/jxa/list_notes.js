#!/usr/bin/env osascript -l JavaScript
// List notes in the HTMLTest folder.
// Env: ACCOUNT (default iCloud), FOLDER (default HTMLTest)
// Output: JSON array of { name, id } sorted by name.

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;

  const accounts = Notes.accounts.whose({ name: accountName });
  if (!accounts.length) throw new Error(`Account not found: ${accountName}`);
  const account = accounts[0];

  const folders = account.folders.whose({ name: folderName });
  if (!folders.length) throw new Error(`Folder not found: ${folderName}`);
  const folder = folders[0];

  const notes = folder.notes();
  const out = [];
  for (const n of notes) {
    out.push({ name: n.name(), id: n.id() });
  }
  out.sort((a, b) => a.name.localeCompare(b.name));
  return JSON.stringify(out, null, 2);
}
