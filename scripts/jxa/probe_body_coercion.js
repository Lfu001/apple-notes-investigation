#!/usr/bin/env osascript -l JavaScript
// Probe whether note.body accepts non-string values via the JXA bridge.
//
// All attempts are DESTRUCTIVE — only run on sacrificial notes.
//
// Env: NOTE_NAME (required), ACCOUNT, FOLDER

ObjC.import('Foundation');
ObjC.import('AppKit');

function safe(fn) {
  try { fn(); return { ok: true }; }
  catch (e) { return { ok: false, error: String(e).slice(0, 250) }; }
}

function run() {
  const env = $.NSProcessInfo.processInfo.environment;
  const accountName = ObjC.unwrap(env.objectForKey('ACCOUNT')) || 'iCloud';
  const folderName = ObjC.unwrap(env.objectForKey('FOLDER')) || 'HTMLTest';
  const noteName = ObjC.unwrap(env.objectForKey('NOTE_NAME'));

  const Notes = Application('Notes');
  Notes.includeStandardAdditions = false;

  const folder = Notes.accounts.whose({ name: accountName })[0]
                 .folders.whose({ name: folderName })[0];
  // Iterate notes manually — whose() is unreliable when folder has many notes
  let note = null;
  for (const n of folder.notes()) {
    if (n.name() === noteName) { note = n; break; }
  }
  if (!note) throw new Error(`Note not found: ${noteName}`);

  const report = { noteName, attempts: [] };

  // Construct an NSAttributedString from HTML
  const html = '<h1>COERCE-Title</h1><div>body paragraph</div>';
  const htmlData = $.NSString.alloc.initWithUTF8String(html)
                   .dataUsingEncoding($.NSUTF8StringEncoding);

  // ---- Attempt 1: assign NSAttributedString to note.body ----
  report.attempts.push(Object.assign(
    { name: '1_NSAttributedString_to_body' },
    safe(() => {
      const attr = $.NSAttributedString.alloc
                    .initWithHTMLDocumentAttributes(htmlData, Ref());
      note.body = attr;
    })
  ));
  report.body_after_1 = note.body().slice(0, 200);

  // ---- Attempt 2: assign NSData (raw HTML bytes) to note.body ----
  report.attempts.push(Object.assign(
    { name: '2_NSData_to_body' },
    safe(() => { note.body = htmlData; })
  ));
  report.body_after_2 = note.body().slice(0, 200);

  // ---- Attempt 3: assign an NSDictionary to note.body ----
  report.attempts.push(Object.assign(
    { name: '3_NSDictionary_to_body' },
    safe(() => {
      const d = $.NSDictionary.dictionaryWithObjectsForKeys(
        [$.NSString.alloc.initWithUTF8String('value')],
        [$.NSString.alloc.initWithUTF8String('key')]
      );
      note.body = d;
    })
  ));
  report.body_after_3 = note.body().slice(0, 200);

  // ---- Attempt 4: assign a number to note.body ----
  report.attempts.push(Object.assign(
    { name: '4_number_to_body' },
    safe(() => { note.body = 42; })
  ));
  report.body_after_4 = note.body().slice(0, 200);

  // Reset body to known plain content
  report.cleanup = safe(() => {
    note.body = '<div>' + noteName + '</div><div>after coercion probe</div>';
  });

  return JSON.stringify(report, null, 2);
}
