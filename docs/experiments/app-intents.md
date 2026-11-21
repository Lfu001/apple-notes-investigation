# macOS 27 のメモで書式を保つ本文編集

macOS 27.2.1（26B131）、メモ 4.13（3195.42.3）で、本文を変更したときに段落スタイルや文字サイズが保たれるかを調べた。調査期間は 2026 年 11 月 18〜21 日。

| 操作 | 確認した結果 |
| --- | --- |
| ショートカットと Siri AI による末尾追記 | 3 つの文字サイズ設定すべてで、既存の段落スタイルと RTF のポイント値を保持した |
| ショートカットで本文を読み取り、新規作成 | 段落スタイルとチェック状態が変わった。リンク先 URL は保持した |
| メモの「検索と置換」で本文の 1 語を置換 | 置換した語の太字、周囲の段落スタイル、リンク先 URL、チェック状態を保持した |
| App Intents 経由で本文の選択範囲を置換 | 同梱メタデータにアクションの定義があった。試した経路では実行できなかった |

## 末尾追記と HTML の全文書き戻し

メモの設定にある「デフォルトのテキストサイズ」を、左から 1〜3 番目の目盛りに切り替えた。以下の `0`、`1`、`2` は目盛りの位置を示すアクセシビリティ上の値。実験後は初期設定の `1` に戻した。[メモのテキストサイズ設定](https://support.apple.com/ja-jp/guide/notes/-apd8b73d28be/mac)

タイトル、見出し、小見出し、太字の本文 2 行からなる試験用メモを使い、操作の前後で AppleScript の `body` プロパティから HTML を取得した。

- ショートカットの「メモに追加」では、Markdown の解釈をオフにし、セクションを指定せず、固定の文字列を末尾に追加した。どの設定でも既存の HTML 5 行は同一で、末尾に 1 段落が加わった。
- Siri AI では、ショートカットで追記済みのメモを一意の名前で指定し、別の固定文字列を末尾に追加するよう指示した。どの設定でも既存の HTML 6 行は同一で、末尾に空段落が 2 つと追記の段落が 1 つ加わった。Siri が使用したインテントの識別子は取得していない。
- 比較対照では、同じ書式を持つ別の試験用メモに、取得した HTML を `body` プロパティへそのまま書き戻した。3 件とも `h1`・`h2`・`h3` が通常段落に変わった。

### 書き戻し後の HTML のサイズ指定

| 書き戻し時の設定値 | タイトル | 見出し | 小見出し・本文 |
| --- | ---: | ---: | ---: |
| `0` | 29 px | 22 px | 16 px |
| `1` | 24 px | 18 px | 指定なし |
| `2` | 21 px | 15 px | 11 px |

設定値 `1` で書き戻したメモを設定値 `0` で読み直しても、HTML は同一だった。

### コピーした RTF のポイント値

メモで本文を選択してコピーし、ペーストボードの `public.rtf` を AppKit の `NSAttributedString` で読み取った。書式区間ごとの `NSFont.pointSize` を次に示す。設定値 `1` で操作前に測った見出しの値は、フォントパネルの **16 pt** と一致した。

| 設定値 | 操作前（タイトル・見出し・本文） | ショートカットと Siri AI の追記後 | 同じ設定で HTML を書き戻した後 |
| --- | --- | --- | --- |
| `0` | 20・16・13 pt | 20・16・13 pt | 28.8・21.6・15.6 pt |
| `1` | 20・16・13 pt | 20・16・13 pt | 24・18・13 pt |
| `2` | 20・16・13 pt | 20・16・13 pt | 20.571・15.167・11.143 pt |

小見出しのポイント値は各試験用メモの本文と同じだった。ショートカットと Siri AI で追加した行はいずれも 13 pt。設定値 `1` で HTML を書き戻したメモを `0` と `2` で再度コピーしても、24・18・13 pt のままだった。

表の値は RTF に含まれるフォントサイズを示す。表示時に適用される拡大・縮小を含めた画面上のサイズは、3 設定での直接測定に至っていない。macOS 26.4.1 では、フォントパネルで書き戻し前後の値を測った。[macOS 26.4.1 のフォントサイズ実測](font-size-measurement.md)

## 読み取った本文からの新規作成

ショートカットの「メモを検索」で試験用メモを名前で絞り込み、取得件数の上限を 1 件にした。検索結果の「本文」プロパティを「メモを作成」の「内容」に渡し、Markdown としての解釈をオフにした。同じ試験用メモを使い、各設定で別名のメモを作成した。タイトル行には、作成時に指定した新しい名前が入った。

| 元の書式 | 設定値 `0` の結果 | 設定値 `1`・`2` の結果 |
| --- | --- | --- |
| 見出し | タイトル段落（`h1`）に変化 | 見出し（`h2`）を保持 |
| 小見出し | 見出し（`h2`）に変化 | 太字の通常段落に変化 |
| 太字の本文 2 行 | どちらも見出し（`h2`）に変化 | 太字の通常段落を保持 |
| リンク | リンク先 URL を保持 | リンク先 URL を保持 |
| 未完了のチェック項目 | 箇条書きに変化 | 箇条書きに変化 |
| 完了済みのチェック項目 | 未完了のチェック項目に変化 | 未完了のチェック項目に変化 |

リンク先は HTML の `href` とメモの画面で確認した。チェックリストは新規作成の前後で同じ `ul` と `li` に出力されたため、画面上のチェックボタンとチェック印を比較した。

## 選択範囲の部分置換

次の検証では、本文行に含まれる `ALPHA` 1 件を `OMEGA` に置き換え、前後の HTML とメモの画面を比較した。

### メモ内蔵の「検索と置換」

試験用メモを単独のウインドウで開き、`⌘F` で `ALPHA` を検索した。一致が 1 件であることを確認して「置き換え」を有効にし、`OMEGA` を入力して 1 件だけ置換した。

保存後の HTML は次の 1 行だけが変わった。見出しなどの段落スタイルとリンク先 URL は同一で、完了・未完了のチェック項目も画面上で維持された。

```diff
-<div><b>Body marker ALPHA remains.</b></div>
+<div><b>Body marker OMEGA remains.</b></div>
```

### インテントの実行を試した経路

同梱のアクション定義に `ReplaceSelectionLinkAction` があり、置換文字列 `text` を受け取る。説明では、対象はメモの編集画面で選択中のテキスト。日本語の表示名「選択したテキストを置き換える」は、同梱の `Localizable.loctable` で確認した。

| 経路 | 結果 |
| --- | --- |
| ショートカットのアクション検索 | 日本語の表示名で検索したが該当なし |
| Spotlight のアクション検索 | メモのアクションは検索結果に現れなかった |
| Siri AI のチャット | 選択範囲だけを変更できないと応答し、本文は変更されなかった |
| メモの「Siriで作文」 | 置換を指示した後に入力欄が閉じ、本文は変更されなかった |
| App Intents Testing | 実行時に XPC セッションがキャンセルされ、本文は変更されなかった |

Spotlight には「テキストを置き換え」という項目が表示された。同名の標準ショートカットアクションは、入力として受け取った文字列を変換する。既存メモの本文を更新するには、変換結果を書き戻す経路が必要になる。

### Swift SDK からの直接呼び出し

Apple は WWDC26 の質疑で、複数のアプリにまたがるインテントの実行をシステムが仲介すると説明している。別のアプリから任意のインテントをアプリの識別子と名前で実行できる汎用 API は、macOS 27.2 SDK の公開インターフェースで確認できなかった。[WWDC26 Apple Intelligence Group Lab（8 分 18 秒）](https://developer.apple.com/videos/play/wwdc2026/8011/)

- `AppIntents` の `callAsFunction(donate:)` では、自作のインテントを Swift プログラムから実行できた。純正メモの `ReplaceSelectionLinkAction` を同じモジュールから Swift 型として参照すると、コンパイル時に名前を解決できなかった。[callAsFunction(donate:) の仕様](https://developer.apple.com/documentation/appintents/appintent/callasfunction%28donate%3A%29-3qvbt)
- `AppIntentsTesting` には、対象アプリのバンドル ID とインテント名を指定して、別プロセスから `run()` を呼ぶ API がある。Apple が案内する構成は、対象アプリと同じ署名チームの UI テストターゲット。純正メモを対象にした単体の Swift プログラムで発生した XPC キャンセルの詳細な原因は未確認。[App Intents Testing の設定手順](https://developer.apple.com/documentation/appintentstesting/testing-your-app-intents-code)

2026 年 11 月 21 日に、ロック解除済みの Mac で再試行した。メモを前面に出し、試験用メモの `OMEGA` のみを選択して `ReplaceSelectionLinkAction` を実行したところ、同じ `RemoteInvocationCancellationError` が発生した。実行前後の HTML は同一で、読み取り専用の `NoteEntity` 検索も同じエラーになった。試験プロセスのログで XPC 接続先の切断は確認できたが、切断の理由は特定できなかった。

## 同梱メタデータにある本文関連の定義

| 定義 | メタデータにある入出力 |
| --- | --- |
| `NoteEntity`（`notes.note`） | 名前と本文を持つ。既定のクエリは `VisibleNotesQuery` |
| `CreateNoteIntent`（`notes.createNote`） | 名前、本文、添付、固定状態、フォルダを受け取り、メモを返す |
| `NoteAppendTextIntent`（`notes.appendText`） | 対象と追記する本文を受け取り、メモを返す |
| `UpdateNoteIntent`（`notes.updateNote`） | 対象、名前、添付、固定状態、フォルダを受け取る。本文や文字範囲の引数はない |
| `CreateNoteLinkAction` | ショートカットの「メモを作成」。本文と名前、フォルダ、Markdown の解釈を指定できる |
| `AppendToNoteLinkAction` | ショートカットの「メモに追加」。対象、追加するテキスト、先頭・末尾、セクションなどを指定できる |
| `ReplaceSelectionLinkAction` | 置換文字列を受け取る。メモや文字範囲の引数はない |

Siri スキーマに対応する作成・追記には `assistantOnly: true` が記録されている。同名で表示されるショートカットの作成・追記は別の定義を持つ。また、`UpdateNoteIntent` と `ReplaceSelectionLinkAction` の `isDiscoverable` は `true` だった。この属性から、個別の画面で検索できるか、呼び出しが成功するかは判断できない。[メモのアプリスキーマ](https://developer.apple.com/documentation/appintents/appschema/notesintent)、[更新の引数](https://developer.apple.com/documentation/appintents/appschema/notesintent/updatenote)

同梱ファイルからこれらの項目を確認するには `jq` を使う。以下はメモのデータにアクセスせず、アプリに同梱された定義を読み取る。

```sh
metadata=/System/Applications/Notes.app/Contents/Resources/Metadata.appintents/extract.actionsdata
jq '{
  actions: (.actions | with_entries(select(.key |
    IN("CreateNoteIntent", "NoteAppendTextIntent", "UpdateNoteIntent",
       "CreateNoteLinkAction", "AppendToNoteLinkAction",
       "ReplaceSelectionLinkAction"))) |
    map_values({
      schema: [.assistantDefinedSchemas[]?.publicIdentifier],
      visibility: .visibilityMetadata,
      openAppWhenRun,
      parameters: [.parameters[].name]
    })),
  note: (.entities.NoteEntity | {defaultQueryIdentifier, transferableContentTypes})
}' "$metadata"
```

`transferableContentTypes` には RTF や HTML などの書き出し形式が宣言されている。追記のショートカットを CLI で 1 回実行し、`--output-type public.rtf` と `--output-path` を指定した試行では、追記は保存されたがファイルは生成されなかった。前述の RTF の測定は、メモの編集画面からコピーして行った。

## 追試の手順

1. iCloud の試験用フォルダ `HTMLTest` に、タイトル、見出し、小見出し、本文 2 行を設定したメモを作る。本文の 1 行に `Body marker ALPHA remains.` を入れて太字にする。リンクとチェック状態を比較する場合は、試験用の URL（例 `https://example.com/`）へのリンク、未完了と完了済みのチェック項目を 1 つずつ加える。
2. 「メモ」＞「設定」でデフォルトのテキストサイズの初期位置を記録する。本実験と同じ比較には左から 1〜3 番目を使う。設定と操作ごとに試験用メモを複製し、一意の名前を付けて、操作前の書式を画面で確認する。
3. 末尾追記、本文からの新規作成、メモ内蔵の検索と置換のうち、比較したい操作を上記の手順で実行する。追記を比較する場合は、まずショートカットで追記し、その結果に Siri AI で別の文字列を追記する。HTML の全文書き戻しを比較する場合は、専用の複製に取得した HTML を [set_body.js](../../scripts/jxa/set_body.js) で書き戻すと、書式の変化を比較できる。
4. 各操作の前後で HTML を取得し、差分を確認する。リンク先とチェック状態はメモの画面でも確認する。文字サイズを比較するときは、コピーした RTF のポイント値とフォントパネルの表示値を別々に記録する。終了後はスライダを実験前の位置に戻す。

操作前の HTML を取得する例。リポジトリのルートで実行し、`NOTE_NAME` には実際の試験用メモの名前を指定する。使用するスクリプトは、既定で iCloud の `HTMLTest` を検索する。

```sh
output_dir=$(mktemp -d -t notes-app-intents)
NOTE_NAME='Notes format probe' osascript -l JavaScript scripts/jxa/get_body.js \
  > "$output_dir/before.html"
```

操作後も同じ手順で `after.html` に保存して `diff -u "$output_dir/before.html" "$output_dir/after.html"` を実行する。新規作成の結果を調べる場合は、読み取り対象に作成先メモの名前を指定する。
