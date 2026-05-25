#!/usr/bin/env osascript -l JavaScript
// Probe Notes.app: list accounts, folders, and whether HTMLTest folder exists.
// Writes a JSON report to stdout for the Python wrapper to consume.

ObjC.import('stdlib');

function run(argv) {
  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;

  const report = { accounts: [] };
  try {
    const accounts = Notes.accounts();
    for (const acc of accounts) {
      const accName = acc.name();
      const folderNames = [];
      try {
        for (const f of acc.folders()) {
          folderNames.push(f.name());
        }
      } catch (e) {
        folderNames.push(`<error: ${e.message}>`);
      }
      report.accounts.push({ name: accName, folders: folderNames });
    }
  } catch (e) {
    report.error = e.message;
  }

  return JSON.stringify(report, null, 2);
}
