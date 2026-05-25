# テストメモ作成手順

本ドキュメントは、GUI から手作業で作成する GUI 由来メモ (T01〜T17b) の作成手順をまとめたものである。前提環境は `docs/methods/environment.md` を参照。

GUI 由来メモは `HTMLTest copy` フォルダに置き、`HTMLTest` 側にはこれを Cmd+D で複製したものを置いて運用する。これは GUI 由来の原本を破壊から守るためである。

T18-T23 の観測用メモは GUI ではなくスクリプトから投入する。詳細は本ドキュメント末尾の「T18-T23 (スクリプトから投入する観測用メモ)」節を参照。

## 共通の操作ルール

- **コピーとペーストの流れ**: 各セクションの「貼り付け本文」のコードブロック内のテキストをコピーし、`iCloud > HTMLTest copy` フォルダに新規メモを作成してペーストする。続いて「フォーマット指示」に従って書式を適用する。
- **タイトル行**: 各メモの最初の行 (メモ名と一致する行) には必ず「タイトル」スタイルを適用する (Cmd+Shift+T)。新規メモのデフォルトスタイルをタイトルにしていれば自動で適用される (`docs/methods/environment.md` を参照)。
- **メモ名マッチング**: スクリプトはメモの「最初の行のテキスト」でマッチングを行う。タイトル文字列は表記通り正確に入力する。
- **段落分け**: メモ.appは Return で新段落、Shift + Return でソフトブレイク (段落内改行) を生成する。コードブロック内の空行は段落区切りとしてそのままペーストする。
- **ペースト直後の自動変換**: メモ.appが自動でリスト変換やリンク化を試みる場合がある。意図しない変換が起きた場合は Cmd+Z で戻し、Format メニューから明示的に再設定する。
- **作成後の検証**: 全 GUI 由来メモの作成後、`HTMLTest copy` 全体を Cmd+A で全選択し、Cmd+D で複製してから `HTMLTest` フォルダに移動する。これで `HTMLTest` 側に作業用コピーが揃う。

---

## T01 — `T01-plain` (プレーン段落、空行あり)

**貼り付け本文**:

```
T01-plain

First paragraph.

Second paragraph.

Third paragraph.
```

**フォーマット指示**: なし (すべて本文スタイルで、書式装飾なし)。

---

## T02 — `T02-softbreak` (段落内ソフトブレイク)

**貼り付け本文** (タイトル行のみペーストし、本文行は手入力を推奨):

```
T02-softbreak
```

**フォーマット指示**:

1. タイトル行をペーストし Return を押す。
2. `line 1` と入力して Shift + Return を押す。
3. `line 2` と入力して Shift + Return を押す。
4. `line 3` と入力する。
5. 以上の操作により、3 行が 1 つの段落としてソフトブレイクで連結される。

完成形のイメージ:

```
T02-softbreak
line 1↵
line 2↵
line 3
```

`↵` は Shift + Return によるソフトブレイクを表す。

---

## T03 — `T03-headings` (タイトル / 見出し / 小見出し / 本文)

**貼り付け本文**:

```
T03-headings
Heading level 2
Subheading level 3
Body paragraph.
```

**フォーマット指示**:

1. ペーストする。
2. `Heading level 2` の行にカーソルを置き、Format → 見出し (Cmd+Shift+H) を適用する。
3. `Subheading level 3` の行で Format → 小見出し (Cmd+Shift+J) を適用する。
4. `Body paragraph.` の行は Format → 本文 (既定の場合は不要)。

---

## T04 — `T04-mono-quote` (等幅およびブロック引用)

**貼り付け本文**:

```
T04-mono-quote
This paragraph should be Monostyled.
This paragraph should be a Block Quote.
```

**フォーマット指示**:

1. ペーストする。
2. 2 行目 (`This paragraph should be Monostyled.`) にカーソルを置き、Format → 等幅 (Cmd+Shift+M) を適用する。
3. 3 行目 (`This paragraph should be a Block Quote.`) で Format → ブロック引用 (Cmd+') を適用する。

---

## T05 — `T05-inline-decor` (Bold / Italic / Underline / Strikethrough)

**貼り付け本文**:

```
T05-inline-decor
Normal bold italic underline strike bold-italic back to normal.
```

**フォーマット指示**: 2 行目に対して、以下の単語を選択して書式を適用する。

- `bold` を選択し Cmd+B
- `italic` を選択し Cmd+I
- `underline` を選択し Cmd+U
- `strike` を選択し Format → Font → Strikethrough
- `bold-italic` を選択し Cmd+B と Cmd+I を両方適用

---

## T06 — `T06-bullet` (箇条書きリスト、ネスト)

**貼り付け本文**:

```
T06-bullet
item one
item two
nested item
item three
```

**フォーマット指示**:

1. ペーストする。
2. `item one` から `item three` までを範囲選択し、Format → 箇条書きリスト (Cmd+Shift+7) を適用する。
3. `nested item` の行頭にカーソルを置き、Tab キーでネストを下げる。

---

## T06b — `T06b-dashed` (ダッシュ付きリスト、ネスト)

**貼り付け本文**:

```
T06b-dashed
dash item one
dash item two
nested dash
dash item three
```

**フォーマット指示**:

1. ペーストする。
2. 最初の行で Cmd + Shift + T (タイトル) を適用する。
3. `dash item one` から `dash item three` までを範囲選択し、Format → ダッシュ付きリスト を適用する。
4. `nested dash` の行頭にカーソルを置き、Tab キーでネストを下げる。

> ダッシュ付きリストは、箇条書き (`•`) でも番号付き (`1.`) でもチェックリスト (`☐`) でもない 4 番目のリスト種別である。HTML 表現は `<ul class="Apple-dash-list">` として保持される (`01-facts.md` §2.2 を参照)。

---

## T07 — `T07-numbered` (番号付きリスト、ネスト)

**貼り付け本文**:

```
T07-numbered
first
second
nested
third
```

**フォーマット指示**:

1. ペーストする。
2. `first` から `third` までを範囲選択し、Format → 番号付きリスト (Cmd+Shift+8) を適用する。
3. `nested` の行頭にカーソルを置き、Tab キーでネストを下げる。

---

## T08 — `T08-checklist` (チェックリスト、一部チェック済み)

**貼り付け本文**:

```
T08-checklist
Buy milk
Buy bread
Write report
Send email
```

**フォーマット指示**:

1. ペーストする。
2. `Buy milk` から `Send email` までを範囲選択し、Format → チェックリスト (Cmd+Shift+L) を適用する。
3. `Buy milk` と `Write report` の左側の `○` (空のチェックボックス) をクリックして `●` (チェック済み) に切り替える。

> メモ.appのチェックリストは「未チェック ○」と「チェック済み ●」の 2 状態のみで、半チェック状態は存在しない。チェック済みの項目をリストの末尾に自動移動する設定 (Notes Settings → "Sort Checked Items to Bottom") は OFF にしておく (順序を観察したいため)。
>
> 保存された出力との不一致は意図的なものである。step 3 のチェック状態は `get_body` (`data/probes/HTMLTest-copy/T08-checklist.html`) には現れず、プレーンな `<ul><li>` の箇条書きリストと区別がつかなくなる (`01-facts.md` §3.1 を参照)。保存された出力から確認できるのは step 1-2 の `<ul>` / `<li>` 構造までであり、step 3 を実行したかどうかは GUI から目視で検証する必要がある。

---

## T09 — `T09-mixed-list` (混在リスト 3 階層)

**貼り付け本文**:

```
T09-mixed-list
Top bullet A
Numbered child 1
Numbered child 2
Checklist grandchild a
Checklist grandchild b
Top bullet B
```

**フォーマット指示**:

1. ペーストする。
2. 2〜7 行目を範囲選択し、Format → 箇条書きリスト を適用する。
3. `Numbered child 1` と `Numbered child 2` を範囲選択し、Tab でネストを下げ、Format → 番号付きリスト を適用する。
4. `Checklist grandchild a` と `Checklist grandchild b` を範囲選択し、Tab を 2 回押して 2 段ネストを下げ、Format → チェックリスト を適用する。

完成形のイメージ:

```
T09-mixed-list
• Top bullet A
  1. Numbered child 1
  2. Numbered child 2
     ☐ Checklist grandchild a
     ☐ Checklist grandchild b
• Top bullet B
```

---

## T10 — `T10-link` (テキストリンクと裸 URL)

**貼り付け本文**:

```
T10-link
Visit example for details.
Bare URL: https://www.apple.com
```

**フォーマット指示**:

1. ペーストする。
2. 2 行目の `example` を選択し、Edit → Add Link (Cmd+K) を選び、URL に `https://example.com` を入力する。
3. 3 行目の URL はメモ.appが自動でリンク化する。自動リンク化が行われない場合は放置でよい。

---

## T11 — `T11-custom-font` (任意フォントおよびサイズ)

本テストメモ群の中で最も重要な観測対象の 1 つである。任意のフォントサイズ (18, 20, 22, 28 等) が `set_body` 経由のラウンドトリップで保持されるかを確認するためのメモとして用いる。フォントサイズの実 pt 値は Notes Default Text Size の影響を受けず、フォントパネルの指定が優先される。

**貼り付け本文**:

```
T11-custom-font
This paragraph uses Helvetica 22pt.
```

**フォーマット指示**:

1. ペーストする。
2. 2 行目全体を選択し、Format → Font → Show Fonts (Cmd+T) でフォントパネルを開く。
3. Family に Helvetica を指定する (macOS にバンドルされている素の "Helvetica" であり、"Helvetica Neue" や "Helvetica Light" 等の派生ではない)。Size に 22 を指定する。

---

## T12 — `T12-color-highlight` (文字色とハイライト)

**貼り付け本文**:

```
T12-color-highlight
This word is red and this word is highlighted.
```

**フォーマット指示**:

1. ペーストする。
2. `red` を選択し、Format → Font → Show Colors (Cmd+Shift+C) を開き、Apple Color Picker から純赤 (`#FF0000`) を選択する。色相環の場合は赤の真上、RGB タブの場合は `R=255, G=0, B=0` を指定する。
3. `highlighted` を選択し、Format → ハイライト (メニューバー)、または右クリック → ハイライト → Yellow を選択する (デフォルトの黄色ハイライト。他の色は選ばないこと)。

> 保存された出力との不一致は意図的なものである。step 2 の赤色は `<font color="#FF0000">` として `get_body` に現れる (保存された出力から確認可能である)。一方、step 3 の Yellow ハイライトは `get_body` には一切現れない (`01-facts.md` §3.1 を参照)。step 3 を実行したかどうかは GUI から目視で検証する必要がある。

---

## T13 — `T13-table` (3 行 × 3 列のテーブル)

**貼り付け本文**:

```
T13-table
```

**フォーマット指示**:

1. タイトル行をペーストし Return を押して空行に移動する。
2. Format → Table (Cmd+Option+T) を選ぶと、初期状態の 2×2 テーブルが挿入される。
3. 行および列を追加して 3×3 にする。
   - 列ヘッダ (テーブル上端の細い帯) にホバーすると各列の上に「∨」ボタンが表示されるので、Add Column After で 3 列にする。
   - 行ヘッダ (テーブル左端の細い帯) にホバーすると各行の左に「∨」ボタンが表示されるので、Add Row Below で 3 行にする。
4. 各セルに以下を入力する (Tab でセル移動)。

```
A1  B1  C1
A2  B2  C2
A3  B3  C3
```

---

## T14 — `T14-image` (画像添付)

**貼り付け本文**:

```
T14-image
This note contains an image:
```

**フォーマット指示**:

1. ペーストし Return を押して新しい段落に移る。
2. 任意の小さな画像 (PNG または JPEG、200KB 以下が望ましい) を Finder からドラッグ&ドロップ、または Cmd+V でペーストする。

---

## T15 — `T15-pdf` (PDF 添付)

**貼り付け本文**:

```
T15-pdf
This note contains a PDF:
```

**フォーマット指示**:

1. ペーストし Return を押す。
2. 1 ページ程度の PDF を Finder からドラッグ&ドロップする。
3. PDF が用意できない場合はスキップしてよい。

---

## T16 — `T16-all` (複合)

**貼り付け本文**:

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

**フォーマット指示**: 上記の T03, T05, T06, T08, T11, T12 と同じ要領で、それぞれの行に適切な書式を適用する。テーブル、画像、PDF は省略してよい。

---

## T17a — `T17a-sizes` (段落スタイルと実フォントサイズ計測の before)

`set_body` を通していない GUI 由来の状態でのフォントサイズを Font Panel で実測するための原本である。

**貼り付け本文**:

```
T17a-sizes
Title sample
Heading sample
Subheading sample
Body sample
Monostyled sample
Block quote sample
```

**フォーマット指示**:

1. ペースト後、各行にカーソルを置いて Format メニューから以下のスタイルを適用する。
   - `T17a-sizes` → タイトル (Cmd+Shift+T)
   - `Title sample` → タイトル (Cmd+Shift+T)
   - `Heading sample` → 見出し (Cmd+Shift+H)
   - `Subheading sample` → 小見出し (Cmd+Shift+J)
   - `Body sample` → 本文 (デフォルト)
   - `Monostyled sample` → 等幅 (Cmd+Shift+M)
   - `Block quote sample` → ブロック引用 (Cmd+')

2. 作成は `HTMLTest copy` フォルダで行う。`HTMLTest` 側にはこれを Cmd+D で複製したコピーを置く。

`get_body` の出力が以下になっていれば成功である (リポジトリには参考用に `data/probes/HTMLTest-copy/T17a-sizes.html` がコミットされている)。

```html
<div><h1>T17a-sizes</h1></div>
<div><h1>Title sample</h1></div>
<div><h2>Heading sample</h2></div>
<div><h3>Subheading sample</h3></div>
<div>Body sample</div>
<div><tt>Monostyled sample</tt></div>
<div>Block quote sample</div>
```

---

## T17b — `T17b-sizes` (同 after、`set_body` を 1 回通したもの)

T17a と同一の GUI 由来の状態から出発し、`set_body` を 1 回通して正規化された版である。同一の出発点から一方は `set_body` を通し、もう一方は通さないことで実フォントサイズの差を見るために、T17a と T17b の両方が GUI 由来の原本 (`HTMLTest copy`) と作業コピー (`HTMLTest`) の両フォルダに存在する形となる。

**作成手順**:

1. `HTMLTest copy` で T17a を選択し、Cmd+D で複製する。複製の最初の行を `T17b-sizes` に書き換える (`HTMLTest copy/T17b` は GUI 由来の原本である)。
2. `HTMLTest copy` 全体 (T01〜T17b、18 件) を Cmd+A で全選択し、Cmd+D で再複製してから複製群を `HTMLTest` フォルダにドラッグして移動する。`HTMLTest/T17a` および `HTMLTest/T17b` はこの時点ではまだ GUI 由来である。T18-T23 は GUI で作成しないため `HTMLTest copy` には存在せず、後述の `seed_t_probes.py` で `HTMLTest` に直接投入する。
3. `HTMLTest` 側の T17b に対してのみ `set_body` を 1 回通す。

   ```bash
   uv run python -c "import sys; sys.path.insert(0,'scripts/py'); import notes; notes.set_body('T17b-sizes', notes.get_body('T17b-sizes'))"
   ```

4. 検証: `uv run python scripts/py/notes.py get T17b-sizes` の出力が `<div><b><span style="font-size: 24px">...</span></b></div>` 形式に正規化されていれば成功である (`data/probes/HTMLTest/T17b-sizes.html` と一致する)。

---

## T18-T23 (スクリプトから投入する観測用メモ)

T18 以降は GUI からの手作業ではなく、`scripts/py/seed_t_probes.py` で `create_note` 経由でまとめて投入する。各観測用メモはラベル付き `<div>` とバリアント入力 HTML を交互に並べた単一メモとして構成されており、`get_body` の出力を読めばどのバリアントがどの結果になったかを追跡できる。

| メモ名 | 何を試すか | バリアント数 |
|---|---|---:|
| `T18-mono-probe` | 等幅 paragraph style への HTML 経路 (`<tt>` / `<pre>` / Courier face) | 4 |
| `T19-probe` | ブロック引用および bare `<h1>` の段落スタイル作成可否 | 6 |
| `T20-tag-probe` | セマンティック HTML タグの網羅 (`<code>` / `<kbd>` / `<samp>` / `<var>` / `<cite>` / `<q>` / `<mark>` / `<small>` / `<ins>` / `<del>` / `<dfn>` / `<abbr>` / `<figure>` / `<figcaption>` / `<ruby>`) | 16 |
| `T21-highlight-probe` | ハイライト (背景色) を作る CSS バリアント | 10 |
| `T22-checklist-link-probe` | チェックリストの state とハイパーリンクの HTML 経路 | 10 |
| `T22b-checklist-link-probe` | T22 を 1 回ラウンドトリップした状態 (URL 保持の崩壊確認用) | 10 |
| `T23-heading-combo` | タイトル / 見出し段落スタイルの作成のための組み合わせ試行 | 16 |

実行例:

```bash
# 全観測用メモを seed する (既存の同名メモを削除してから create_note する)
uv run python scripts/py/seed_t_probes.py

# 特定の観測用メモだけを処理する
uv run python scripts/py/seed_t_probes.py --filter T20

# 実投入せず HTML だけを確認する
uv run python scripts/py/seed_t_probes.py --dry-run --filter T20
```

> 投入先フォルダは `--folder` で指定可能である (デフォルトは `notes.DEFAULT_FOLDER = "HTMLTest"`)。T01-T17b は GUI 手作業のため `HTMLTest copy` を原本に置く運用だが、観測用メモ (T18-T23) は `set_body` 経由で何度でも投入し直せるため、作業フォルダの `HTMLTest` に直接入れる。

スクリプトに記録された入力 HTML は、過去の観測出力に付けたラベルからの再構築である (オリジナルの入力 HTML は当時記録されなかった)。再構築の正当性は、再 seed 後の `get_body` 出力が元の保存出力とバイト一致するかで検証されており、7 つの観測用メモのうち 6 件 (T18, T19, T21, T22, T22b, T23) は完全一致を確認している。T20 のみ ruby variant の末尾の `<br>` 1 文字の差分が残っており、この差分はスクリプト中にコメントで記録してある。

---

## 完成後の確認

すべてのメモを作成し終えたら、以下のコマンドで一覧を確認する。

```bash
uv run python scripts/py/notes.py list
```

期待される出力は、`HTMLTest copy` に `T01-plain` から `T17b-sizes` までの 18 件、`HTMLTest` に同名コピーと `T18-mono-probe` から `T23-heading-combo` まで (合計 25-27 件、`PRB-*` 等は除く) である。

そのうえで以下を実行するとラウンドトリップテストが走る。

```bash
uv run python scripts/py/roundtrip.py --filter T
```
