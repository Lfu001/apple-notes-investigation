#!/usr/bin/env osascript -l JavaScript
// Probe whether attachment binary contents are retrievable.
//
// Try multiple paths:
//   1. att.contents() — hidden file property
//   2. AppleScript "save" command on attachment
//   3. read by content identifier (cid) from body's data URL
//   4. NSData via private NSAttributedString attachment
//
// Env: NOTE_NAME (required), ACCOUNT, FOLDER
ObjC.import('Foundation');
ObjC.import('AppKit');

function safe(fn) {
  try { return { ok: true, value: fn() }; }
  catch (e) { return { ok: false, error: String(e).slice(0, 200) }; }
}

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';
  const noteName = ObjC.unwrap(env.objectForKey('NOTE_NAME'));
  if (!noteName) throw new Error('NOTE_NAME required');

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = true;

  const accounts = Notes.accounts.whose({ name: accountName });
  const folder = accounts[0].folders.whose({ name: folderName })[0];
  const note = folder.notes.whose({ name: noteName })[0];

  const atts = note.attachments();
  if (atts.length === 0) {
    return JSON.stringify({ noteName, error: 'no attachments' });
  }
  const att = atts[0];

  const report = {
    noteName,
    attId: String(att.id()),
    attName: String(att.name()),
    cid: String(att.contentIdentifier()),
  };

  // 1. contents() — hidden file property
  report.contents_call = safe(() => {
    const c = att.contents();
    return { type: typeof c, str: String(c).slice(0, 200) };
  });

  // 2. AppleScript "save" command on attachment
  const tmpDir = $.NSTemporaryDirectory();
  const tmpPath = ObjC.unwrap(tmpDir) + 'att-save-' + Math.floor(Math.random()*1e6);
  report.save_attempt = safe(() => {
    att.save({ in: Path(tmpPath) });
    // Check if file appeared
    const fm = $.NSFileManager.defaultManager;
    const exists = fm.fileExistsAtPath(tmpPath);
    let size = -1;
    if (exists) {
      const errRef = Ref();
      const attrs = fm.attributesOfItemAtPathError(tmpPath, errRef);
      if (attrs && !attrs.isNil()) {
        const sizeNum = attrs.objectForKey('NSFileSize');
        if (sizeNum) size = Number(ObjC.unwrap(sizeNum));
      }
    }
    return { saved_to: tmpPath, exists: !!exists, size };
  });

  // Try save without `in:` — should fail, but exposes error
  report.save_no_target = safe(() => {
    att.save();
    return 'no error (unexpected)';
  });

  // Try save with as: parameter
  const tmpPath2 = ObjC.unwrap(tmpDir) + 'att-save2-' + Math.floor(Math.random()*1e6) + '.png';
  report.save_in_path = safe(() => {
    att.save({ in: Path(tmpPath2), as: 'native format' });
    const fm = $.NSFileManager.defaultManager;
    const exists = fm.fileExistsAtPath(tmpPath2);
    return { path: tmpPath2, exists: !!exists };
  });

  return JSON.stringify(report, null, 2);
}
