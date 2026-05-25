#!/usr/bin/env osascript -l JavaScript
// Try to attach a file to an existing note via `make new attachment with data`.
// Env:
//   NOTE_NAME (required)
//   FILE_PATH (required)
//   ACCOUNT (default iCloud), FOLDER (default HTMLTest)
// Output: JSON describing the result.

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

  const accounts = Notes.accounts.whose({ name: accountName });
  if (!accounts.length) throw new Error(`Account not found: ${accountName}`);
  const folders = accounts[0].folders.whose({ name: folderName });
  if (!folders.length) throw new Error(`Folder not found: ${folderName}`);
  const folder = folders[0];

  const matches = folder.notes.whose({ name: noteName });
  if (!matches.length) throw new Error(`Note not found: ${noteName}`);
  const note = matches[0];

  const attempts = [];

  // Attempt A: Notes.Attachment().make({new:'attachment', at: note, withData: Path})
  try {
    const att = Notes.Attachment().make({
      new: 'attachment',
      at: note,
      withData: Path(filePath),
    });
    attempts.push({ name: 'A_make_attachment_at_note_withData_Path',
                    ok: true, id: String(att.id()), attName: String(att.name()) });
  } catch (e) {
    attempts.push({ name: 'A_make_attachment_at_note_withData_Path',
                    ok: false, error: String(e).slice(0, 200) });
  }

  // Attempt B: Notes.make({new:'attachment', at: note.attachments, withData: Path})
  try {
    const att = Notes.make({
      new: 'attachment',
      at: note.attachments,
      withData: Path(filePath),
    });
    attempts.push({ name: 'B_make_at_note_attachments_withData_Path',
                    ok: true, id: String(att.id()), attName: String(att.name()) });
  } catch (e) {
    attempts.push({ name: 'B_make_at_note_attachments_withData_Path',
                    ok: false, error: String(e).slice(0, 200) });
  }

  // Attempt C: with `withData` referencing the note (i.e., note as container,
  // file as data, no `at:`)
  try {
    const att = Notes.make({
      new: 'attachment',
      withProperties: { container: note },
      withData: Path(filePath),
    });
    attempts.push({ name: 'C_make_withProperties_container_withData_Path',
                    ok: true, id: String(att.id()), attName: String(att.name()) });
  } catch (e) {
    attempts.push({ name: 'C_make_withProperties_container_withData_Path',
                    ok: false, error: String(e).slice(0, 200) });
  }

  // Attempt D: at: note (without specifying attachments collection)
  try {
    const att = Notes.make({
      new: 'attachment',
      at: note,
      withData: Path(filePath),
    });
    attempts.push({ name: 'D_make_at_note_withData_Path',
                    ok: true, id: String(att.id()), attName: String(att.name()) });
  } catch (e) {
    attempts.push({ name: 'D_make_at_note_withData_Path',
                    ok: false, error: String(e).slice(0, 200) });
  }

  return JSON.stringify({ noteName, filePath, attempts }, null, 2);
}
