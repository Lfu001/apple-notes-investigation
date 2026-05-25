# 編集レシピライブラリ

`scripts/py/edit_recipe.py` は、ブラックボックステストで安全と確認されたパターンのみを使って GUI 由来メモを編集するための高レベル関数および CLI を提供する。

本ドキュメントは利用者側のリファレンスである。なぜ各パターンが安全と分かっているかについては `01-facts.md` を、個別の実験データについては `docs/experiments/` 以下を参照。

---

## 使用例

CLI から呼び出す場合:

```bash
# 1. 編集対象が安全かチェックする (これを呼ばずに編集してはならない)
uv run python scripts/py/edit_recipe.py safety MyNote

# 2. 安全と判定されたなら編集可能
uv run python scripts/py/edit_recipe.py replace MyNote "old text" "new text"
uv run python scripts/py/edit_recipe.py append-para MyNote "新しい段落"
uv run python scripts/py/edit_recipe.py append-li MyNote "新しいリスト項目"
uv run python scripts/py/edit_recipe.py remove-li MyNote "削除する項目を含む文字列"
uv run python scripts/py/edit_recipe.py color MyNote "強調する語" "#FF0000"
uv run python scripts/py/edit_recipe.py append-link MyNote "リンクテキスト" "https://example.com"
```

Python ライブラリとして使う場合:

```python
import sys; sys.path.insert(0, "scripts/py")
import edit_recipe

report = edit_recipe.check_safety("MyNote")
if not report.safe:
    raise SystemExit(f"破壊要因あり: {report}")

edit_recipe.replace_unique_text("MyNote", "old", "new")
edit_recipe.append_paragraph("MyNote", "新しい段落")
edit_recipe.color_text("MyNote", "重要", "#FF0000")
```

---

## 安全な編集対象の条件

`check_safety(note_name)` は、body HTML および `note.attachments()` から検出可能な破壊要因として以下を検査する。

- body HTML 内の `<img>` (画像)
- body HTML 内の `<object>` で `<table>` を含まないもの (PDF 等の添付)
- `note.attachments()` に含まれる画像ファイル (`.jpeg` / `.png` / `.gif` / `.heic` 等)
- `note.attachments()` に含まれる PDF
- `note.attachments()` に含まれるその他不明な拡張子の添付

これらのいずれかが見つかれば `safe=False` を返す。

ただし、以下の要素は body HTML にも `attachments()` にも痕跡が出ないため、`check_safety` では検出できない。

- ハイパーリンク (GUI 由来のもの。URL 情報が body HTML に出ない)
- ハイライト (背景色)
- チェックリストのチェック状態 (プレーンな `<ul><li>` と区別不能)
- ブロック引用段落 (プレーンな `<div>` と区別不能)
- ソフトブレイク (`get_body` の時点で既に半角スペース化されている)
- カスタムフォントファミリ (Helvetica 等)
- タイトル / 見出し / 小見出し段落スタイル

したがって、これらを含むことが既知のメモには操作してはならない。`check_safety` が `safe=True` を返しても、上記のいずれかが含まれている可能性は否定できないため、GUI から目視で事前に確認する必要がある。

---

## 各関数の挙動

すべての関数は内部で `set_body` を 2 段階で呼び出す。1 回目で HTML を不動点に正規化し、2 回目で実際の編集を適用する。タイトル / 見出し / 小見出しの段落スタイルを持つメモに対してこれらを使うと、当該 paragraph style は破壊される (`01-facts.md` §3.1)。

### `check_safety(note_name) -> SafetyReport`

メモの破壊リスクを検査する。`SafetyReport.safe` が `True` なら、HTML から検出可能な破壊要因はない。`SafetyReport.note` には検出不能な損失に関するリマインダーが格納される。

```python
report = edit_recipe.check_safety("MyNote")
if report.safe:
    print("安全に編集可能 (ただし検出不能な要素には注意)")
else:
    print(f"破壊要因あり: {report.visible_destroyers + report.attachment_destroyers}")
```

### `replace_unique_text(note_name, needle, replacement)`

メモ内で `needle` が一意な NavigableString に出現する場合に限り置換する。複数マッチした場合および不在の場合は `ValueError` を送出する。

```python
edit_recipe.replace_unique_text("MyNote", "First paragraph.", "Replaced!")
```

### `append_paragraph(note_name, text)`

末尾に新しい `<div>text</div>` 段落を追加する。

### `append_list_item(note_name, text)`

メモ内で最初に見つかった `<ul>` または `<ol>` の末尾に `<li>text</li>` を追加する。

### `remove_list_item(note_name, marker)`

メモ内で `marker` を含む最初の `<li>` を削除する。

### `color_text(note_name, needle, hex_color)`

一意な `needle` を `<font color="#XXXXXX">needle</font>` で囲む。`hex_color` は `"#FF0000"` または `"#F00"` 形式で指定する。

### `append_link(note_name, text, url)`

末尾に `<div><a href="url">text</a></div>` 段落を追加する。GUI 上では動作するリンクとして表示される。

このリンクは書き込み専用である。追加したリンクは `get_body` の HTML には URL が含まれず (`<u>text</u>` のみが出力される)、同じメモに再度 `set_body` を呼び出すと URL が失われる。したがって連続編集する用途には使えず、新規メモに 1 度だけ追加する用途に限定される。

---

## 禁止される操作

| 操作 | 理由 |
|---|---|
| 画像または PDF を含むメモに編集系関数を呼ぶ | 添付が消失する (`check_safety` が拒否する想定) |
| タイトル / 見出し / 小見出し段落を含むメモに編集系関数を呼ぶ | 段落スタイルが破壊される (折りたたみ矢印が消滅し、フォントサイズが拡大する)。`check_safety` では検出できないため、GUI から目視で確認する必要がある |
| チェックリスト状態を保ちたいメモを編集する | チェック状態は body HTML に存在しないため必ず失われる |
| 既存のハイパーリンクを保ちたいメモを編集する | URL は body HTML に存在しないため必ず失われる |
| ハイライト付きテキストを保ちたいメモを編集する | ハイライトは body HTML に存在しないため必ず失われる |
| 追加した `append_link` のリンクを後から維持したい | ラウンドトリップで URL が失われる。新規追加かつ書き込み専用である |

---

## 限定的に編集できる経路 (`set_body` を経由しない)

`edit_recipe.py` ではまだサポートしていないが、`scripts/jxa/` 以下に低レベルツールが用意されている。

### 画像 / PDF を含むメモを編集する場合: 添付の退避と復元

1. `note.attachments()` で添付を列挙する。
2. `attachment.save({in: '/tmp/...'})` で各添付をローカルに退避する。
3. 通常通り `set_body` で本文を編集する。この時点で body から `<img>` および `<object>` が消え、`note.attachments()` も空を返すようになる。
4. `Notes.make({new:'attachment', at:note, withData:'/tmp/...'})` で添付を復元する。

制約として、復元時の添付は末尾に追加されるため元の挿入位置情報は失われる。また、1 回の `make new attachment` で `<img>` が 2 個 body に挿入される現象が観測されており、原因は現時点で特定していない。さらに、タイトル / 見出し段落は依然として `set_body` で破壊される。

### タイトル / 見出し段落を持つメモを限定的に編集する場合: テンプレート複製

1. GUI で Cmd+D により複製する。内部表現が完全にコピーされ、paragraph style も保持される。
2. 複製先に対してスクリプトから `make new attachment` で末尾に添付を追加する。これは安全に行える。
3. 同じく `note.name = X` で名前を変更できるが、これは一時的で後続編集の際に再計算される。
4. `set_body` は呼んではならない。

この経路では本文テキストの書き換えはできない。テンプレートに従って画像だけが違うメモを大量生成するような限定的な用途に使える。詳細は `experiments/api-surface.md` を参照。

---

## 環境

`scripts/py/notes.py` の `DEFAULT_ACCOUNT = "iCloud"` および `DEFAULT_FOLDER = "HTMLTest"` を参照するため、テストメモは iCloud アカウントの `HTMLTest` フォルダに置く前提となる。

`edit_recipe.py` の関数 (`check_safety`, `replace_unique_text` 等) は account や folder のパラメータを受け取らない。別フォルダのメモに対して使いたい場合は、`notes.DEFAULT_ACCOUNT` および `notes.DEFAULT_FOLDER` をモジュールレベルで上書きしてから呼び出す。

```python
import notes
notes.DEFAULT_ACCOUNT = "iCloud"
notes.DEFAULT_FOLDER = "MyWorkFolder"
import edit_recipe
edit_recipe.check_safety("MyNote")
```

または、`notes.get_body` および `notes.set_body` を直接呼び出す。これらは `account` および `folder` のキーワード引数を受け取る。

---

## delay 値の調整

`set_body` を呼んだ直後に `get_body` を呼ぶと、まれに書き戻し前の値が返ることがある (iCloud 同期遅延)。本リポジトリのテスト環境では 1.5 秒の待機で安定したが、環境によってはこの待機時間を延ばす必要が出ることがある。各関数は `delay` キーワード引数で待機時間を個別に上書きできる。

```python
edit_recipe.replace_unique_text("MyNote", "foo", "bar", delay=3.0)
```
