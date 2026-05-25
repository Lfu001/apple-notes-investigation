#!/usr/bin/env osascript -l JavaScript
// Phase 7 advanced API surface probe:
//   1. make new attachment with data <file>
//   2. paragraph/text suite access on note.body
//   3. body property type coercion (NSAttributedString, NSData)
//   4. paste/keystroke event availability
//
// Env:
//   NOTE_NAME (required) — target note in HTMLTest
//   ACCOUNT (default iCloud), FOLDER (default HTMLTest)
//   IMAGE_FILE (optional) — path to image for make-new-attachment test
//
// Output: JSON report.

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
  const imageFile = ObjC.unwrap(env.objectForKey('IMAGE_FILE'));
  if (!noteName) throw new Error('NOTE_NAME required');

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

  const report = { noteName, folderName };

  // ---------- 2. text suite on body ----------
  // Try paragraph / text / characters / words access on the body string.
  report.text_suite = {};
  report.text_suite.paragraphs_of_body = safe(() => {
    const ps = note.body.paragraphs();
    return { count: ps.length, sample: ps.slice(0, 3).map(p => String(p).slice(0, 80)) };
  });
  report.text_suite.text_of_body = safe(() => {
    const t = note.body.text();
    return String(t).slice(0, 200);
  });
  report.text_suite.characters_of_body = safe(() => {
    const c = note.body.characters();
    return { count: c.length };
  });
  report.text_suite.paragraph_1_of_note = safe(() => {
    const p = note.paragraphs[0]();
    return String(p).slice(0, 200);
  });

  // ---------- 1. make new attachment ----------
  if (imageFile) {
    report.make_attachment = safe(() => {
      const url = $.NSURL.fileURLWithPath(imageFile);
      // Try the JXA AppleScript-style API: make new attachment at note with data file
      // First attempt: pass a Path object.
      const path = Path(imageFile);
      const att = Notes.Attachment().make({
        new: 'attachment',
        at: note,
        withData: path,
      });
      return { id: String(att.id()), name: String(att.name()) };
    });
  } else {
    report.make_attachment = { skipped: 'no IMAGE_FILE' };
  }

  // ---------- 3. body type coercion ----------
  // Try assigning a non-string value to note.body via JXA.
  // We DO NOT actually modify the note here (read-only probe). Instead we
  // construct values and check if the JXA bridge accepts them. To avoid any
  // side effects, we only inspect what JXA does with the constructed values.

  // Build an NSAttributedString from a tagged HTML containing a Title-styled
  // paragraph using NSAttributedString attributes. We can't actually use this
  // without writing — caller does the writing separately.
  report.nsAttrString_construct = safe(() => {
    const htmlStr = '<h1>T-Test</h1><p>body</p>';
    const nsHtml = $.NSString.alloc.initWithUTF8String(htmlStr);
    const data = nsHtml.dataUsingEncoding($.NSUTF8StringEncoding);
    const options = $.NSDictionary.dictionaryWithObjectsForKeys(
      [$.NSNumber.numberWithInt(0)],
      [$.NSCharacterEncodingDocumentAttribute]
    );
    const errRef = Ref();
    // NSAttributedString HTML init signature is annoying; this is a smoke test
    const attr = $.NSAttributedString.alloc.initWithHTMLDocumentAttributes(
      data, Ref()
    );
    if (!attr || attr.isNil()) return null;
    return {
      length: Number(attr.length),
      string_sample: String(ObjC.unwrap(attr.string)).slice(0, 200),
    };
  });

  return JSON.stringify(report, null, 2);
}
