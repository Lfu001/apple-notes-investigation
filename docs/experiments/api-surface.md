# AppleScript / JXA の公開 API の探索

## 動機

`experiments/paragraph-style-search.md` で `<html>` 入力経路の網羅は尽きたと結論したが、それは `note.body = <html>` 経由の経路に限った話であった。メモ.appの scripting dictionary には `body` 以外の経路が存在するため、これらを改めて網羅的に探索した結果が本ドキュメントである。

特に `set_body` を経由しない paragraph style 保持の経路がいくつか発見できた。

---

## 1. scripting dictionary の完全ダンプ

`sdef /System/Applications/Notes.app` の主要部:

```
suite "Notes Suite" {
  command "open note location"   (URL → open)
  command "show"                  (account|folder|note|attachment → show in UI)
  class "application" {
    property "default account"
    property "selection"
    elements: account, folder, note, attachment
  }
  class "account" { properties: default folder, name, upgraded, id }
  class "folder"  { properties: name, id, shared, container; elements: folder, note }
  class "note" {
    properties: name, id, container, body, plaintext, creation date,
                modification date, password protected, shared
    elements: attachment
  }
  class "attachment" {
    properties: name, id, container, content identifier, creation date,
                modification date, URL, shared
    contents (hidden file)
    responds to: save
  }
  enumeration "saveable file format" { "native format" (public.item) }
}
```

加えて、Cocoa Standard Suite (`make`, `delete`, `duplicate`, `set`, `get`, `count`, `exists`, `copy`, `move`, `save`, `close`, `open`) が xi:include されている。

note クラスの書き込み可能プロパティは `name` と `body` の 2 つのみである (詳細は `docs/01-facts.md` §1.1 を参照)。

---

## 2. 各 API の検証結果

### 2.1 `note.plaintext` プロパティ (動作する)

JXA から `note.plaintext()` で取得できる。

特徴は以下のとおりである。

- 添付の位置が `￼` (U+FFFC Object Replacement Character) で示される
- 改行は `\n` で表現される (body HTML の `<div>` 段落区切りに対応する)
- 装飾 (bold / italic / color / highlight) は痕跡が残らない
- タイトル / 見出し / 小見出しの段落スタイルも痕跡が残らない

実例 (T16-all):

```
T16-all
This is a Heading
This is a Subheading
Body paragraph with bold and italic and underline and strike.
First bullet
Second bullet
nested bullet
Checklist task a
Checklist task b
Paragraph with red word and highlighted word.
This last paragraph uses Helvetica 22pt.
```

用途: 添付の存在位置の特定、テキスト内容の比較。

### 2.2 `every attachment of note` (要素アクセス、動作する)

JXA の `note.attachments()` で動作する。

取得できるプロパティ:

- `id` — Core Data URI
- `name` — 元のファイル名 (例: `image.jpeg`, `doc.pdf`)
- `contentIdentifier` (cid) — `cid:UUID@icloud.apple.com` 形式
- `creationDate`, `modificationDate`
- `shared` (boolean)
- `URL` — 画像 / PDF / table の添付ではタイプ変換エラーとなる (URL 専用と推定される)

#### 重要な発見: どのメモ要素が attachment 化されるか

| メモ種別 | attachment 数 | 種別 |
|---|---:|---|
| T03 (タイトル / 見出し段落) | 0 | attachment ではない (paragraph 属性) |
| T04 (ブロック引用 / 等幅) | 0 | paragraph 属性 |
| T08 (チェックリスト) | 0 | paragraph 属性 |
| T10 (リンク) | 0 | character 属性 (URL は body にも plaintext にも出ない) |
| T11 (Custom font) | 0 | character 属性 |
| T12 (色とハイライト) | 0 | character 属性 |
| T13 (Table) | 1 | テーブルも attachment である |
| T14 (画像) | 1 | attachment |
| T15 (PDF) | 1 | attachment |
| T16 (複合、添付なし) | 0 | すべて属性 |

つまりメモ.app内部では以下の区別がある。

- NSTextAttachment 系 (ファイル参照を伴うもの): 画像、PDF、テーブル
- NSAttributedString attribute 系 (テキストに付随する属性): 色、ハイライト、リンク、フォント、タイトル / 見出し段落、ブロック引用、チェックリスト状態

これにより、`check_safety` を attachment 認識型に強化できる (`scripts/py/edit_recipe.py:check_safety()`)。

### 2.3 `attachment.save({in: Path})` (動作する)

scripting dictionary に `<responds-to command="save">` が定義されている。JXA から以下のように呼び出せる。

```javascript
att.save({ in: Path('/tmp/dump.jpeg') });
```

これで attachment の元ファイルを取り出せる。

実証 (T14 の image.jpeg): 取り出されたファイルは 542558 バイト、JPEG 896×1200 (元画像そのもの) であった。

`as: "native format"` のパラメータを渡すこともできるが、効果は確認していない。

参考として、`attachment.contents()` で Group Container 内の元ファイルパスを取得することもできる。ただしこれはメモ.appが管理する内部パスであり、直接アクセスは推奨されない。

### 2.4 `Notes.make({new:'attachment', at: note, withData: Path})` (動作する)

scripting dictionary の attachment クラスのコメントに以下の例がある。

> "make new attachment with data myFile" の例

JXA で 4 通りの構文を試した結果は以下のとおり。

| 構文 | 結果 |
|---|---|
| `Notes.Attachment().make({new:'attachment', at: note, withData: Path})` | 失敗。「添付ファイルは特定のメモに追加する必要があります」 |
| `Notes.make({new:'attachment', at: note.attachments, withData: Path})` | 失敗。「ハンドラは一つのオブジェクトだけを取り扱います」 |
| `Notes.make({new:'attachment', withProperties: {container: note}, withData: Path})` | 失敗。「タイプを変換できません」 |
| `Notes.make({new:'attachment', at: note, withData: Path})` | 成功 |

`scripts/jxa/add_attachment.js` がこの最終形を実装する。

#### 既知の現象: `<img>` の二重化

1 回の `make new attachment` を呼ぶと、以下の状態となる。

- 戻り値は 1 個の attachment オブジェクト
- `attachments()` で見ると 2 個として数えられる (両方とも同じ id および同じ cid)
- body HTML には 2 個の `<img>` が出る (両方とも同じ data URL)

つまりメモ.appは 1 個の attachment レコードを作り、それを body に 2 回 inline する。期待動作とは異なるが、実用上の制約として認識する必要がある。原因は現時点で特定していない。

#### `<img>` の挿入位置が状況に依存する

同じスクリプト `add_attachment.js` を実行しても、メモ.appが `<img>` を body に挿入する位置のパターンが揺らぐ。

パターン 1 として、行内挿入の場合がある (T03 旧、PRB-attach-single で観察):

```html
<div>Body paragraph.<img/><img/></div>
```

画像が末尾段落の行内に入り、レイアウト計算でテキストの上に画像が重なる表示破綻が起こる。

パターン 2 として、独立段落への挿入の場合がある (T03 新で観察、実演で再現に成功):

```html
<div>Body paragraph.</div>
<div><img/><br></div>
<div><img/>...</div>
```

画像が独立 `<div>` に入り、`<br>` まで付与される。GUI 上で本文段落の下に画像が縦に並ぶ正常な表示となる。

両者の違いを生む条件は現時点で特定していない (メモ.app内部のキャッシュ状態、同期状態、OS の編集モード等の可能性がある)。プログラムからパターン 2 を強制する手段は不明だが、T03 の実演ではパターン 2 を観察できた。

### 2.5 `make new attachment` は paragraph style を保持する

本探索における最大の発見である。

```
BEFORE:
  <div><h1>T03-headings</h1></div>
  <div><h2>Heading level 2</h2></div>
  <div><h3>Subheading level 3</h3></div>
  <div>Body paragraph.</div>

AFTER (make new attachment 適用後):
  <div><h1>T03-headings</h1></div>          ← タイトルが保持される
  <div><h2>Heading level 2</h2></div>       ← 見出しが保持される
  <div><h3>Subheading level 3</h3></div>    ← 小見出しが保持される
  <div>Body paragraph.<img .../><img .../></div>
```

つまり、メモ.appが内部で保持するタイトル / 見出し / 小見出しの段落スタイルは、`make new attachment` の操作では破壊されない。

これは `set_body` 経由ではない body 操作経路として確認された唯一のものである。

### 2.6 `note.name = newName` は body に影響しないが永続しない

```
BEFORE:
  name: "PRB-attach-single"
  body: "<div>PRB-attach-single</div>..."

AFTER (note.name = "PRB-attach-renamed" を適用):
  name: "PRB-attach-renamed"        ← name の変更は反映される
  body: "<div>PRB-attach-single</div>..."  ← body の最初の行は変わらない
```

T03 で実証された追加検証は以下のとおりである。

- name を `"T03-headings"` から `"T03-renamed-demo"` に変更すると、直後の読み取りで反映される。
- 続けて `make new attachment` を呼ぶ。
- 直後の note の name が `"T03-headings"` に戻る (body の最初の行から再計算される)。

つまり、name の独立した設定は一時的であり、後続のスクリプト編集操作が name を body の最初の行から再計算する。

実用上の含意は以下のとおりである。

- `name = ...` を編集レシピの主軸として使うのは危険である (再計算で消える)。
- 名前を変えたい場合は body の最初の行を変えるしかない。
- ただし body 編集は `set_body` 経由となるため、paragraph style 破壊のリスクがある。

唯一の安全な name 変更は、GUI で Cmd+D により複製したテンプレートにおいて、body の最初の行が既に欲しい名前と一致している場合のみである。

### 2.7 GUI Cmd+D による複製 (paragraph style を完全に保持する)

ユーザーが手動で `HTMLTest copy` の T01 から T16 を Cmd+D で複製して `HTMLTest` にコピーした結果は以下のとおりである。

#### 保持されるもの

- タイトル / 見出し / 小見出しの段落スタイル: `<h1>` / `<h2>` / `<h3>` がそのまま (T03)。GUI 上で折りたたみ矢印やテーマサイズも維持される。
- 画像の添付 (T14): 元と複製先で attachment 1 件が保持され、body HTML の `<img>` も維持される。
- テーブルの添付 (T13): 元と複製先で attachment 1 件が保持され、body の `<object><table>` も維持される。
- PDF の添付 (T15): GUI 上で PDF プレビューが見える状態のまま複製される。
- その他のスタイル: 箇条書きリスト、番号付きリスト、ダッシュ付きリスト、装飾、色、フォントサイズ、ブロック引用、等幅 (推定)。

#### scripting bridge の制限 (Cmd+D 自体の制限ではない)

T15 の PDF は GUI 上は保持されているが、`note.attachments()` 経由では 0 件として報告される。

- plaintext には `￼` (添付マーカー) が含まれており、内部表現には PDF が存在する。
- `HTMLTest copy` 側の T15 (オリジナル) では `attachments()` は 1 件を返す。
- 同じ PDF を持つにもかかわらず、Cmd+D による複製先では scripting bridge が enumeration に失敗する。
- 原因は現時点で特定していない (同期待ち、attachment レコードの新規生成 ID の認識遅延、scripting bridge の不具合、等の可能性がある)。

これは Cmd+D の問題ではなく、`note.attachments()` の信頼性問題である。

検証結果のサマリ:

| メモ | 元 (`HTMLTest copy`) | Cmd+D による複製 (`HTMLTest`) | GUI 表示 | 結果 |
|---|:-:|:-:|:-:|---|
| T03 (タイトル / 見出し) | paragraph style あり | paragraph style が保持される | 正常 | 成功 |
| T13 (table) | attachment 1 | attachment 1 | 正常 | 成功 |
| T14 (画像) | attachment 1 | attachment 1 | 正常 | 成功 |
| T15 (PDF) | attachment 1 | attachment 0 (scripting bridge の問題) | 正常 (PDF が見える) | scripting bridge から取得できない |
| T16 (複合) | attachment 0 | attachment 0 | 正常 | 成功 |

重要な含意として、`note.attachments()` の戻り値は信頼できないケースがある (Cmd+D による複製先など)。`check_safety` を attachment ベースで強化する場合、attachment コレクションが空でも実際には添付がある可能性があるため、plaintext 中の `￼` の存在で交差チェックするのが堅牢である。

ただし、複製先に対して `set_body` を呼んだ瞬間に paragraph style は破壊される (`experiments/roundtrip.md` の結論通り)。複製はあくまでテンプレートを複製する用途に限る。

### 2.8 動かなかったもの

#### `duplicate` (scripting コマンド)

```javascript
note.duplicate({ to: dstFolder });
// → Error: Notes can not be copied.
```

Cocoa Standard Suite に含まれているが、メモ.app側がハードコードで拒否している。

#### AppleScript text suite

```javascript
note.body.paragraphs()   // → タイプを変換できません
note.body.text()          // → タイプを変換できません
note.body.characters()    // → タイプを変換できません
note.paragraphs[0]()      // → タイプを変換できません
```

メモ.appは標準テキストスイートを実装していない。`body` は単なる `text` 型 (文字列) として扱われ、サブオブジェクトを持たない。

#### body プロパティへの非文字列代入

```javascript
note.body = NSAttributedString;  // → タイプを変換できません
note.body = NSData;              // → タイプを変換できません
note.body = NSDictionary;        // → タイプを変換できません
note.body = 42;                  // → "<div>42</div>" として保存される (数値が文字列に coerce される)
```

JXA の scripting bridge は `body` を `text` 型として扱い、文字列に coerce 可能なものだけを受け入れる。NSAttributedString および NSData は coerce 不可能である。

つまり、NSAttributedString を直接メモに書き込む経路は存在しない。

---

## 3. 編集ワークフローへの影響

### 3.1 attachment 認識型の安全性チェック (信頼性に制約あり)

従来の `check_safety` は body HTML から `<img>` および `<object>` を検出するだけだったが、`note.attachments()` を見ればテーブルも attachment として扱われるため、より正確な検出ができる。

```python
def check_safety_v2(note_name):
    atts = list_attachments(note_name)
    issues = []
    for a in atts:
        name = a.get('name', '')
        if name.endswith(('.jpeg', '.jpg', '.png', '.gif', '.heic')):
            issues.append(f'image ({name})')
        elif name.endswith('.pdf'):
            issues.append(f'PDF ({name})')
        elif name is None or name == 'None':
            # name が空の attachment はテーブル (T13 で確認済み)
            # body HTML には <object><table> として出るため、これは安全
            pass
        else:
            issues.append(f'other attachment ({name})')
    return issues
```

信頼性に関する注意として、§2.7 で観察した通り、`note.attachments()` は Cmd+D による複製先で PDF を取得できないケースがある。堅牢な判定のためには、plaintext 中の `￼` の数で交差チェックすべきである。

```python
def has_destructive_attachment(note_name):
    pt = get_plaintext(note_name)
    ofc_count = pt.count('￼')  # plaintext 中の添付マーカー数
    atts = list_attachments(note_name)
    table_count = sum(1 for a in atts if a.name is None)
    return ofc_count > (len(atts) - table_count) or any(
        a.name and a.name.lower().endswith(('.jpeg','.jpg','.png','.gif','.pdf','.heic'))
        for a in atts
    )
```

なお、現状の `scripts/py/edit_recipe.py:check_safety()` の実装は plaintext での交差チェックまでは行っていない。

### 3.2 attachment の退避と復元ワークフロー

`set_body` 通過後は `note.attachments()` が空を返す (添付参照が消える) が、`save` と `make new attachment` を組み合わせれば退避と復元ができる。

```python
def edit_with_attachment_preservation(note_name, edit_fn):
    # Step 1: すべての添付をバックアップする
    backups = []
    for att in get_attachments(note_name):
        tmp_path = f'/tmp/notes-att-{att.id}'
        att.save(in=tmp_path)
        backups.append({'cid': att.cid, 'name': att.name, 'path': tmp_path})

    # Step 2: body を編集する (set_body 通過後は <img>/<object> が消え、attachments() も空となる)
    body = get_body(note_name)
    new_body = edit_fn(body)
    set_body(note_name, new_body)

    # Step 3: 添付を再添付する
    for b in backups:
        add_attachment(note_name, b['path'])
        # 注意: <img> は body の末尾に追加されるため、元の挿入位置は失われる
        # 注意: 1 回の make new attachment で <img> が 2 個 body に挿入される (§2.4)
```

制約は以下のとおりである。

- 元の挿入位置 (body 中のどこに `<img>` があったか) は失われる。末尾に追加される。
- 1 回の `make new attachment` で `<img>` が 2 個追加される。
- タイトル / 見出し段落は依然として保持できない (`set_body` が破壊する)。

### 3.3 タイトル段落を保持する唯一の経路

`set_body` でタイトル段落を作る入力 HTML は存在しない (`experiments/paragraph-style-search.md` で確定)。`body` プロパティに NSAttributedString 等を coerce することも不可能である (§2.8)。

したがって、タイトル / 見出し / 小見出し段落を持つメモをプログラムで「作る」手段はない。

ただし、既存のテンプレート (GUI で作成済みのもの) を Cmd+D で複製する経路は paragraph style を保持する。

```
ユーザーの手動操作:
  HTMLTest copy にテンプレート T03 (タイトル / 見出し / 小見出し付き) を置く
  ↓
  メモ.appの GUI 上で Cmd+D により複製し、HTMLTest に移動する
  ↓
  この時点で paragraph style は保持されている

その後、スクリプト経由で可能な編集:
  - make new attachment with data (画像または PDF を末尾に追加する) — 可能
  - note.name = "新しい名前" — 一時的。後続操作で再計算により消える
  - set_body — 不可 (paragraph style を破壊する)
```

#### T03 で実証 (2026-05-20 に確認)

T03 (タイトル / 見出し / 小見出し付きで、Cmd+D による複製済み) に対して以下を試した。

1. `rename_note` で name を `"T03-headings"` から `"T03-renamed-demo"` に変更する。
   - 直後の body は無傷である: `<div><h1>T03-headings</h1></div><div><h2>...</h2></div>...`
2. `add_attachment` で画像を追加する (1 回目の試行)。
   - body: `<div><h1>T03-headings</h1></div><div><h2>Heading level 2</h2></div><div><h3>Subheading level 3</h3></div><div>Body paragraph.<img/><img/></div>`
   - タイトル / 見出し / 小見出しの `<h1>` / `<h2>` / `<h3>` が完全に保持される。
   - ただし `<img>` が Body paragraph と同じ `<div>` の中に入ったため、GUI 上で画像がテキストの上に重なる表示破綻となった (§2.4 のパターン 1)。
3. 別の Cmd+D 複製版で同じ `add_attachment` を実行する (再実演、23:05 実施)。
   - body: 今度は `<div>Body paragraph.</div><div><img/><br></div><div><img/>...</div>` の形となる (§2.4 のパターン 2)。
   - タイトル / 見出し / 小見出し段落の保持と画像の独立段落への配置が両立し、GUI 上で正常に表示された。
   - スクリーンショットでも確認: タイトル (大きい太字)、見出し、小見出し、本文の段落構造が維持されたうえで、赤い 100×100 の PNG が縦に 2 個並ぶ。

つまり、「テンプレート複製と画像追加のみで完結する編集」は paragraph style を保持して実行できる。ただし `<img>` の挿入位置が状況に依存して揺らぐため、`add_attachment` 後に body HTML を確認してパターン 2 になっていることをチェックするのが安全である。

name の変更も一瞬は効くが、後続編集で消えるため主軸にすべきではない。

逆に、本文テキストを書き換える操作 (`set_body`) を一度でも挟むと、paragraph style は不可逆に破壊される。

---

## 4. 今後の選択肢

ブラックボックスでの API 探索は本探索で尽きた。
