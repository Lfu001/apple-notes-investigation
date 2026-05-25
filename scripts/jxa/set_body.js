#!/usr/bin/env osascript -l JavaScript
// Set the body (HTML) of a note in the HTMLTest folder.
// Env: NOTE_NAME (required), HTML_FILE (required - path to file containing the HTML),
//      ACCOUNT (default iCloud), FOLDER (default HTMLTest)
// We use a file rather than stdin/env to avoid any shell escaping issues with large HTML.

ObjC.import('Foundation');

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';
  const noteName = ObjC.unwrap(env.objectForKey('NOTE_NAME'));
  const htmlFile = ObjC.unwrap(env.objectForKey('HTML_FILE'));
  if (!noteName) throw new Error('NOTE_NAME env var is required');
  if (!htmlFile) throw new Error('HTML_FILE env var is required');

  // Read file as UTF-8
  const errRef = Ref();
  const nsHtml = $.NSString.stringWithContentsOfFileEncodingError(
    htmlFile, $.NSUTF8StringEncoding, errRef
  );
  if (!nsHtml || nsHtml.isNil()) {
    const err = errRef[0];
    throw new Error(`Failed to read ${htmlFile}: ${err ? ObjC.unwrap(err.localizedDescription) : 'unknown'}`);
  }
  const html = ObjC.unwrap(nsHtml);

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

  matches[0].body = html;
  return JSON.stringify({ status: 'ok', name: noteName, bytes: html.length });
}
