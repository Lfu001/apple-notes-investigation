#!/usr/bin/env osascript -l JavaScript
// List all folders under an account.
// Env: ACCOUNT (default iCloud)
ObjC.import('Foundation');

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;
  const accounts = Notes.accounts.whose({ name: accountName });
  if (!accounts.length) throw new Error(`Account not found: ${accountName}`);
  const folders = accounts[0].folders();
  const out = folders.map(f => ({
    name: f.name(),
    id: String(f.id()),
    shared: f.shared(),
    noteCount: f.notes().length,
  }));
  return JSON.stringify(out, null, 2);
}
