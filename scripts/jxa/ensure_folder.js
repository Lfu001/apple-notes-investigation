#!/usr/bin/env osascript -l JavaScript
// Ensure the HTMLTest folder exists under the configured account.
// Reads env var ACCOUNT (default: "iCloud") and FOLDER (default: "HTMLTest").

ObjC.import('stdlib');

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;

  const accounts = Notes.accounts.whose({ name: accountName });
  if (!accounts.length) {
    return JSON.stringify({ status: 'error', message: `Account not found: ${accountName}` });
  }
  const account = accounts[0];

  // Look for existing folder
  for (const f of account.folders()) {
    if (f.name() === folderName) {
      return JSON.stringify({ status: 'exists', account: accountName, folder: folderName });
    }
  }

  // Create it
  const newFolder = Notes.Folder({ name: folderName });
  account.folders.push(newFolder);

  return JSON.stringify({ status: 'created', account: accountName, folder: folderName });
}
