# メモ.app HTML API: 現在の事実

本ドキュメントは、Apple メモ.appの `body` AppleScript API をブラックボックステストで確認した、現時点で動作する事実のみを集成したものである。歴史的経緯 (発見および訂正の順序、試して失敗した候補一覧、推定の鎖) については `docs/experiments/` 以下を参照。

検証環境は `docs/methods/environment.md` を参照。各事実の根拠データはすべて `docs/experiments/*.md` 内で出典 (`file:line`) を引いている。

---

## 1. 公開 API

### 1.1 Notes scripting dictionary の note クラスのプロパティ

| プロパティ | 型 | 書き込み | 備考 |
|---|---|:-:|---|
| `name` | text | 可 | メモ名。通常は body の最初の行から自動算出される。直接書き込んでも後続編集で再計算されるため永続しない (§4.2) |
| `body` | text | 可 | メモの HTML 本文 |
| `id` | text | 不可 | Core Data URI |
| `container` | folder | 不可 | 所属フォルダ |
| `plaintext` | text | 不可 | プレーンテキスト表現 (添付位置に `U+FFFC`) |
| `creation date` | date | 不可 | |
| `modification date` | date | 不可 | |
| `password protected` | boolean | 不可 | |
| `shared` | boolean | 不可 | |

書き込み可能なのは `name` と `body` の 2 つのみである (確認方法: `sdef /System/Applications/Notes.app`)。

### 1.2 主要オペレーション

| オペレーション | 経由 | 効果 |
|---|---|---|
| `get_body(note)` | `note.body` 読み取り | HTML 文字列を返す |
| `set_body(note, html)` | `note.body = html` | HTML 文字列を受け取り、メモ.app内部で正規化して保存する |
| `get_plaintext(note)` | `note.plaintext` 読み取り | プレーンテキストを返す。添付位置は `U+FFFC` (`￼`) で示される |
| `list_attachments(note)` | `note.attachments()` | 添付オブジェクトの配列 (画像 / PDF / テーブル) |
| `attachment.save({in: Path})` | scripting コマンド | 添付の元ファイルのバイナリを指定パスに書き出す |
| `Notes.make({new:'attachment', at:note, withData:Path})` | scripting コマンド | 添付を本文末尾に追加する (`set_body` を経由しない) |
| `note.name = newName` | プロパティ書き込み | name を変更する。body には触らず paragraph style は保持されるが、永続せず、後続編集の際に body から再計算される |

---

## 2. `set_body` の入力 HTML から出力 HTML へのマッピング

### 2.1 そのまま保存される要素

以下の要素については、`set_body` への入力 HTML がそのままの構造で `get_body` から返ってくる。

| 要素 | 入力 | 出力 |
|---|---|---|
| プレーン段落 | `<div>X</div>` | `<div>X</div>` |
| 太字 | `<b>X</b>` | `<b>X</b>` |
| イタリック | `<i>X</i>` | `<i>X</i>` |
| 下線 | `<u>X</u>` | `<u>X</u>` |
| 取消線 | `<strike>X</strike>` | `<strike>X</strike>` |
| 文字色 | `<font color="#XXXXXX">X</font>` | (入力と同じ) |
| フォントサイズ | `<span style="font-size: Npx">X</span>` | (入力と同じ) |
| 箇条書きリスト | `<ul><li>X</li></ul>` | (入力と同じ。ネスト含む) |
| 番号付きリスト | `<ol><li>X</li></ol>` | (入力と同じ。ネスト含む) |
| ダッシュ付きリスト | `<ul class="Apple-dash-list"><li>X</li></ul>` | (入力と同じ。`class` も保持) |
| テーブル | `<object><table>...</table></object>` | (入力と同じ) |

これらに加えて、以下のような小さな正規化が適用されるが、いずれも意味は変わらない: `<br/>` の `<br>` への統一、空の `<div>` 末尾への `<br>` 追加、`style="color: red"` から `<font color="#FF0000">` への変換など。

### 2.2 段落スタイルとして再現される要素

HTML 入力から `set_body` で作れる paragraph style は、以下の 2 種類のみである。

| 段落スタイル | 入力 HTML | 出力 HTML | GUI 上の表示 |
|---|---|---|---|
| ダッシュ付きリスト | `<ul class="Apple-dash-list"><li>X</li></ul>` | (入力と同じ) | ダッシュ付きリスト |
| 等幅 | `<tt>X</tt>` または `<pre>X</pre>` または `<code>X</code>` または `<kbd>X</kbd>` または `<samp>X</samp>` | `<font face="Courier"><tt>X</tt></font>` | 等幅段落 (Format メニューの「等幅」にチェックが入った状態) |

これら以外の paragraph style (タイトル / 見出し / 小見出し / ブロック引用 / チェックリスト) は HTML 入力経路では作成できない。詳細は `docs/experiments/paragraph-style-search.md` を参照。300 を超える候補を試行し、いずれも再現に至らなかった。

### 2.3 タグが書き換えられる要素

| 入力 | 出力 | 補足 |
|---|---|---|
| `<h1>X</h1>` | `<div><b><span style="font-size: 24px">X</span></b></div>` | サイズは GUI のタイトル (20pt) と異なり 24px 固定 |
| `<h2>X</h2>` | `<div><b><span style="font-size: 18px">X</span></b></div>` | サイズは GUI の見出し (16pt) と異なり 18px 固定 |
| `<h3>X</h3>` | `<div><b>X</b></div>` | サイズ指定なし (デフォルト 13pt) |
| `<ins>X</ins>` | `<u>X</u>` | 下線のエイリアスとして扱われる |
| `<del>X</del>` | `<strike>X</strike>` | 取消線のエイリアスとして扱われる |
| `<var>X</var>` / `<cite>X</cite>` / `<dfn>X</dfn>` | `<i>X</i>` | いずれもイタリックに統合される |
| `<a href="X">Y</a>` | `<u>Y</u>` (URL は内部保存) | §2.4 参照 |
| `<q>X</q>` | `"X"` (引用符付きのプレーンテキスト) | |
| `<font face="-apple-system">X</font>` | `<font face=".AppleSystemUIFont">X</font>` | Apple 独自のフォント指定 (`-apple-system` 等) の場合のみ face 属性が保持される |

### 2.4 書き込み専用 (新規作成は可能だがラウンドトリップで破壊される)

| 要素 | 挙動 |
|---|---|
| ハイパーリンク (`<a href="X">Y</a>`) | `set_body` で投入すると GUI 上で動作するリンクとして表示される (URL は内部に保存される)。ただし `get_body` の出力 HTML には URL が含まれず `<u>Y</u>` のみが返る。再度 `set_body` を呼び出すと URL は失われる |

したがって、リンクの実用パターンは新規追加かつ書き込み専用に限定される (`edit_recipe.append_link` がこの用途を提供する)。

### 2.5 完全にストリップされる要素

#### 添付系 (要素ごと消失する)

| 入力 | `set_body` 後の状態 | 検出方法 |
|---|---|---|
| `<img src="data:...">` | body から消失し、`note.attachments()` も空を返すようになる | HTML および `attachments()` の両方で検出可能 |
| `<object>` で `<table>` を含まないもの (PDF 等) | body から消失し、`note.attachments()` からも消える | `attachments()` で検出可能 (信頼性に制約あり、§4.3) |

#### 装飾系 (タグが消失し、テキストのみが残る)

| 入力 | 結果 |
|---|---|
| `<span style="background-color: yellow">X</span>` | `<div>X</div>` (背景色が消失する。9 種類の CSS バリアントすべてで同様) |
| `<mark>X</mark>` | `<div>X</div>` (mark タグが消失する) |
| `<input type="checkbox" checked>X` | `X` (input タグが消失する。`ul class="Apple-checklist"` も剥がれる) |
| `<blockquote>X</blockquote>` | `<div>X</div>` (blockquote タグが消失し、ブロック引用段落にはならない) |
| `<font face="Helvetica">X</font>` | `<div>X</div>` (face 属性がドロップされる。size は保持される) |
| `<header>X</header>` / `<article>X</article>` / `<main>` / `<section>` / `<aside>` / `<details>` / `<summary>` 等のラッパータグ | タグが完全にストリップされる |
| `<style>...</style>` | 完全に無視される |
| `<small>` / `<abbr>` / `<figure>` / `<figcaption>` | タグが完全にストリップされる |
| `<ruby>X<rt>Y</rt></ruby>` | `XY` (ルビ情報が失われ、ベースとルビが連結される) |
| `<!DOCTYPE>` / `<html>` / `<body>` / `<meta>` のエンベロープ | 完全に無視される |

### 2.6 ソフトブレイク

`Shift+Return` で作られた段落内改行は、GUI の表示上は段落内改行のままだが、`get_body` の時点で既に半角スペースに変換されている。HTML から検出する手段はない。

---

## 3. 既存 GUI 由来メモに `set_body` を呼んだ場合の影響

GUI で作成された既存メモに対して `set_body` を一度通すと、以下が起こる。

### 3.1 失われる要素 (不可逆)

| 要素 | 結果 | `set_body` 後の検出方法 |
|---|---|---|
| タイトル / 見出し / 小見出し段落スタイル | 段落スタイル属性が消失し、太字本文に変わる。折りたたみ矢印も消滅する。タイトルは実フォントサイズも 20→24pt に拡大 (+4pt)、見出しも 16→18pt (+2pt) に拡大する。小見出しは 13pt のまま | 出力 HTML には `<h1>` / `<h2>` / `<h3>` として現れるため見かけ上は保存されているが、内部の paragraph style 属性は失われており、GUI で開くと別物となる。HTML だけからの検出は不可能 |
| GUI 由来のハイパーリンク | URL が完全に消失する (`get_body` の時点で既に痕跡が残っていない) | 不可能 |
| ハイライト (背景色) | 完全に消失する | 不可能 |
| チェックリストのチェック状態 | チェック状態が消失し、プレーンな `<ul><li>` と区別がつかなくなる | 不可能 |
| ブロック引用段落スタイル | プレーンな `<div>` と区別がつかなくなる | 不可能 |
| カスタムフォントファミリ (Helvetica 等) | face 属性がドロップされる。サイズは保持される | `set_body` 前は `<font face>` で出るが、`set_body` 後は出力されない |
| 画像 (`<img>`) | body から消失し、`note.attachments()` も空を返すようになる | HTML および `attachments()` の両方で検出可能 |
| PDF およびその他の添付 | 同上 | `attachments()` のみで検出可能 (HTML には現れない) |
| ソフトブレイク | `get_body` の時点で既に半角スペースに変換されている | 不可能 |

### 3.2 保持される要素

§2.1 と同じ。加えて、既存の等幅段落も保持される (`<tt>` から再生成できるため)。

---

## 4. `set_body` を経由しない経路

### 4.1 読み取り

- `plaintext`: メモ全体のプレーンテキストを返す。添付の位置は `￼` (`U+FFFC`) で示される。装飾や段落スタイルの情報は含まれない。
- `attachments()`: 添付オブジェクトの配列を返す。各オブジェクトの `name` (例: `image.jpeg`, `doc.pdf`)、`contentIdentifier` (`cid:UUID`)、`creationDate` 等が取得できる。テーブルも 1 つの添付として返されるが、`name` は空となる。
- `attachment.save({in: Path})`: 添付の元ファイルのバイナリを指定パスに書き出す。

### 4.2 編集 (paragraph style を破壊しない経路)

| API | 挙動 | paragraph style への影響 |
|---|---|---|
| `Notes.make({new:'attachment', at:note, withData:Path})` | 添付を body 末尾に追加する (`set_body` を経由しない) | 保持される |
| `note.name = newName` | name を変更する (body には触らない) | 保持される (ただし一時的) |
| GUI Cmd+D による複製 (手動操作) | 内部表現を完全にコピーする (タイトル / 見出し / 添付すべて) | 保持される |

`make new attachment` には制約があり、1 回呼び出すと body に `<img>` が 2 個追加される (メモ.app側の挙動。原因は現時点で特定していない)。`<img>` の挿入位置も状況に依存し、本文段落の行内に入る場合と、独立した `<div>` に入る場合がある。

`note.name = X` にも制約があり、直接設定すると `name` と body の最初の行が乖離する。後続の scripting 編集操作 (`make new attachment` 等) が走ると、メモ.appが name を body の最初の行から再計算するため、name の変更は永続しない。

### 4.3 `attachments()` の信頼性

`note.attachments()` は、GUI で Cmd+D により複製したメモに対して PDF を 0 件として返すケースが観測されている。原因は現時点で特定していないが、scripting bridge 側のバグの可能性がある。添付の有無を確実に検出するには、`plaintext` 中の `￼` の数と `attachments()` の戻り値を交差チェックする必要がある。

### 4.4 動かないことが確認されている経路

| 試行 | 結果 |
|---|---|
| `note.duplicate({to: folder})` | "Notes can not be copied" (メモ.appが拒否する) |
| `note.body = NSAttributedString` | "タイプを変換できません" |
| `note.body = NSData` | "タイプを変換できません" |
| AppleScript text suite (`paragraphs of body` 等) | "タイプを変換できません" |

---

## 5. パーサの個別挙動

### 5.1 `<div>` ラッパー越しに書き換えられた inline タグは末尾に `<br>` を残す

ストリップまたは別タグへの書き換えが発生する inline タグを `<div>` で囲うと、出力の親 `<div>` 末尾に `<br>` が付与される。トップレベル (`<div>` で囲わない) で書くと `<br>` は付かない。

| 入力 | 出力 | 根拠 |
|---|---|---|
| `<mark>X</mark>` | `<div>X</div>` | T20-G の直接観察 |
| `<div><mark>X</mark></div>` | `<div>X<br></div>` | 入力再構成中の派生観察 |
| `<span style="background-color: yellow">X</span>` | `<div>X</div>` | T21-A の直接観察 |
| `<div><span style="background-color: yellow">X</span></div>` | `<div>X<br></div>` | 入力再構成中の派生観察 |

詳細および根拠の分類 (直接観察と派生観察の区別) は `docs/experiments/parser-quirks.md` を参照。

### 5.2 `<abbr title="...">` は `<u>` に書き換えられる

`<abbr>` タグに `title` 属性があれば `<u>` (下線) としてレンダリングされ、`title` 属性がなければタグが削除されてテキストのみが残る。`<abbr title>` の dotted-underline 標準挙動を Cocoa の HTML reader が下線の文字属性にマップしているためと推定される。

---

## 6. 編集戦略の含意

### 6.1 `set_body` で安全に編集できるメモ

以下の要素を含まない GUI 由来メモが対象となる: 画像 / PDF / 添付 (§3.1 添付系)、ハイパーリンク (既存および GUI 由来のもの。新規追加は別問題)、ハイライト、チェックリスト (チェック状態を保ちたい場合)、ブロック引用段落、カスタムフォントファミリ (face)、タイトル / 見出し / 小見出し段落。

これらを含まない場合、以下の要素を組み合わせて安全に編集できる: プレーン本文、装飾 (`<b>` / `<i>` / `<u>` / `<strike>`)、箇条書きリスト、番号付きリスト、ダッシュ付きリスト、等幅、文字色、フォントサイズ、テーブル。

### 6.2 部分的に編集できる経路

| シナリオ | 経路 | 制約 |
|---|---|---|
| 画像または PDF を含むメモ | 添付を `attachment.save` で退避し、`set_body` で本文を編集してから `make new attachment` で復元する | 添付の元の位置情報は失われる (末尾に追加される)。`<img>` 二重化現象あり |
| タイトル / 見出し段落を持つメモ | GUI で Cmd+D により複製し、複製先に `make new attachment` または `name` の変更のみを適用する | 本文テキストの書き換えはできない (`set_body` を呼んだ瞬間に paragraph style が破壊される) |
| 既存メモへの新規リンクの追加 | `set_body` で `<a href>` を含む HTML を末尾に追加する | 一度だけ書き込み可能。ラウンドトリップで URL が破壊される |

### 6.3 編集前の安全性チェック

`scripts/py/edit_recipe.py:check_safety()` は以下を検査する。

- 検出可能: 画像 (`<img>`)、`<object>` で `<table>` を含まないもの、`attachments()` に含まれる画像 / PDF
- 検出不可能 (事前知識に頼るほかない): ハイパーリンク、ハイライト、チェックリストのチェック状態、ブロック引用、ソフトブレイク、タイトル / 見出し / 小見出し

詳細は `02-recipe.md` を参照。
