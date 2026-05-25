# 段落スタイルを生成する HTML 入力の網羅探索

## 目的

`set_body` 経由で、タイトル / 見出し / 小見出し / ブロック引用 / 等幅といったメモ.appの GUI 段落スタイルを再現できる HTML 入力パターンを探索する。

## 方法

可能性のある入力を網羅的に作成し、`notes.create_note(html)` で投入してから `notes.get_body()` で出力を観察し、メモ.appの GUI 上でユーザー目視によって最終確認を行う、という流れで以下の観点をテストする。

1. HTML タグの違い: `<h1>` から `<h6>` まで、`<header>`, `<hgroup>`, `<article>`, `<main>`, `<section>`, `<aside>`, `<details>`, `<summary>`, `<dl>` / `<dt>`, `<blockquote>`, `<pre>`, `<address>`, `<title>` 等
2. HTML 構造の違い: bare 形と `<div>` ラップ、`<!DOCTYPE>`, `<meta charset>`, `<html><body>`、ドキュメント先頭と中間など
3. CSS class 名: `Apple-*`, `apple-*`, `x-apple-*`, `IC*`, `ic-*`, `AppleX`, `NSAttributedString-*`, `com.apple.notes.*`, `Apple-paragraph-*`, `Apple-style-*`, `Apple-text-style-*` 等
4. CSS データ属性: `data-paragraph-style`, `data-apple-paragraph-style` 等
5. インライン CSS プロパティ: `-apple-paragraph-style`, `-webkit-text-style-name` 等
6. 要素別: 同じ class 名でも `<div>` / `<p>` / `<h1>` / `<header>` / `<blockquote>` / `<ul>` / `<ol>` 上でそれぞれ試行する
7. 非 HTML 入力: RTF (`{\rtf1...}`) およびプレーンテキスト
8. WebKit や Mail 由来の既知の `Apple-*` class: `Apple-style-span`, `Apple-converted-space`, `Apple-tab-span`, `Apple-interchange-newline`

使用スクリプト: `scripts/py/heading_probe.py`, `heading_probe2.py`, `class_probe.py`, `class_probe2.py`、および `scripts/py/seed_t_probes.py` の T19 / T20 / T23 (追加分)。

## 探索結果

合計で 300 を超える候補を試行した (本探索の本体で約 300、T19 / T20 / T23 でさらに約 40 候補)。

### 機能した特殊 class: `<ul>` 上の `Apple-dash-list`

```html
<ul class="Apple-dash-list">
  <li>item</li>
</ul>
```

- `get_body` で `class="Apple-dash-list"` が保持される (本探索で保持された唯一の class)
- GUI 上で真の「ダッシュ付きリスト」段落スタイルとして表示される (ユーザー目視で確認済み)
- 他の class 名 (`Apple-bullet-list`, `Apple-numbered-list`, `Apple-checklist`, `Apple-title`, `Apple-heading` 等) はすべて剥がれる

### 等幅段落を作る 5 種のタグ

以下のいずれかをトップレベルまたは `<div>` ラップで送ると、GUI 上で真の等幅段落スタイルとして描画される (Format メニューの「等幅」にチェックが入った状態。ユーザー目視で確認、2026-05-23)。

| 入力 | `get_body` 出力 |
|---|---|
| `<tt>X</tt>` | `<font face="Courier"><tt>X</tt></font>` |
| `<pre>X</pre>` | `<font face="Courier"><tt>X</tt></font>` |
| `<code>X</code>` | `<font face="Courier"><tt>X</tt></font>` |
| `<kbd>X</kbd>` | `<font face="Courier"><tt>X</tt></font>` |
| `<samp>X</samp>` | `<font face="Courier"><tt>X</tt></font>` |

5 タグすべてが HTML 出力上は区別不能となる (メモ.appが `<font face="Courier"><tt>` に統一する)。

検証元: `scripts/py/seed_t_probes.py` の T18-mono-probe (4 バリアント) および T20-tag-probe (15 バリアント)。ダンプは `data/probes/HTMLTest/T18-mono-probe.html` および `T20-tag-probe.html` を参照。

### タイトル / 見出し / 小見出しを再現するパターンは見つからなかった

試行した全候補とその結果は以下のとおり。

| 入力パターン | 結果 |
|---|---|
| `<h1>` / `<h2>` / `<h3>` | 太字本文化される (それぞれ 24px / 18px / 明示なし)。段落スタイル属性は立たない |
| `<header><h1>...</h1></header>` | header タグがストリップされ、`<h1>` 単体と同じ結果になる |
| `<hgroup>`, `<article>`, `<main>`, `<section>`, `<aside>` | ラッパータグが完全にストリップされる |
| `<details><summary>` | details および summary が完全にストリップされる |
| `<dl>` / `<dt>` / `<dd>` | `<div>` にフラット化される |
| `<blockquote>` | 完全にストリップされる (ブロック引用段落スタイルにはならない。詳細は `experiments/block-quote-attempts.md` を参照) |
| `<tt>` / `<pre>` / `<code>` / `<kbd>` / `<samp>` | 等幅段落となる (前述) |
| `<var>` / `<cite>` / `<dfn>` | `<i>` (イタリック) に変換される |
| `<q>` | プレーンテキストと引用符 (`"..."`) に変換される (段落スタイルなし) |
| `<mark>` / `<small>` / `<abbr>` / `<figure>` / `<figcaption>` | 完全にストリップされる (ハイライト等は作れない) |
| `<ins>` | `<u>` (下線) に変換される |
| `<del>` | `<strike>` (取り消し線) に変換される |
| `<ruby>...<rt>...</rt></ruby>` | ルビ情報が失われ、本文とルビが連結されてプレーンテキスト化する |
| `<title>X</title>` | タグが消失する |
| `<address>`, `<aside>` | 同上、ストリップされる |
| `<!DOCTYPE>` / `<html><body>` / `<meta charset>` | 完全に無視される |
| `<style>` タグ内の CSS ルール | 完全に無視される |
| インライン CSS の `-apple-*` および `-webkit-text-style-name` 等 | 完全に無視される |
| `data-paragraph-style="title"` 等のデータ属性 | 完全にストリップされる |
| `class="Apple-title"`, `Apple-heading`, `Apple-paragraph-title` 等 約 300 候補 | すべてストリップされる |
| `<ul class="Apple-{box,disc,hyphen,square,...}-list">` (NSTextList のマーカー名のバリエーション) | dash 以外はすべてストリップされる。`Apple-dash-list` のみ hardcoded である |
| RTF (`{\rtf1...}`) | リテラル文字列として保存される (RTF は解釈されない) |
| プレーンテキスト (改行のみ) | 改行が半角スペースに変換され、段落が分かれない |

### T23-heading-combo: 組み合わせ試行 16 種

単一属性の試行に加え、複合属性 / ラッパー / Apple 独自トークン等を組み合わせた 16 バリアントをすべて試行した。16 件すべてでプレーンな太字本文化となり、タイトル / 見出し段落スタイルにはならなかった (Format メニューで「本文」と判定。ユーザー目視で確認、2026-05-23)。

副産物として、バリアント D の `<h1 style="font: -apple-system-headline">` で `.SFNS-Regular_wdth_opsz110000_GRAD_wght2BC0000` が face 属性として保持されることが分かった。これは「`<font face>` の face 属性は常にドロップされる」という一般則に対する唯一の例外である。

検証元: `scripts/py/seed_t_probes.py` の T23-heading-combo (15 バリアント + Z control)。ダンプは `data/probes/HTMLTest/T23-heading-combo.html` を参照。

### AppleScript / JXA scripting dictionary の確認

メモ.appの `note` クラスの書き込み可能プロパティは `name` と `body` の 2 つのみである (`docs/01-facts.md` §1.1 を参照)。`body` 以外で段落スタイルを設定する API は存在しない。

## 構造的な結論

メモ.appの HTML の入出力は非対称である。

- シリアライザ (内部表現 → HTML): GUI 由来のタイトル / 見出し / 小見出し段落を `<h1>` / `<h2>` / `<h3>` に、ダッシュ付きリストを `<ul class="Apple-dash-list">` に、テーブルを `<table>` に、それぞれ出力する。
- パーサ (HTML → 内部表現): Cocoa の NSAttributedString HTML reader が使われている (推定)。これは generic な HTML パーサであり、以下の挙動を持つ。
  - `<h1>` は「太字 + font-size:24px」の属性を立てる (メモ.appの「タイトル」段落スタイル属性ではない)
  - `<h2>` と `<h3>` も同様に inline の font 属性のみを立てる
  - `<ul class="Apple-dash-list">` だけが特別扱いされ、NSTextList の hyphen マーカー (ダッシュ付きリスト) に変換される (hardcoded 例外)
  - `<tt>` / `<pre>` / `<code>` / `<kbd>` / `<samp>` は等幅段落属性にマップされる (hardcoded 例外)
  - その他の CSS class、データ属性、カスタムプロパティはすべて無視される

したがって、タイトル / 見出し / 小見出しの段落スタイル属性を立てる入力 HTML パターンは存在しない。これはメモ.app自体の制限ではなく、Cocoa の HTML reader がメモ.app独自の段落スタイル属性をマッピングしていないことに起因すると推定される。

## 残された選択肢

| アプローチ | 評価 |
|---|---|
| UI スクリプティング (System Events で Cmd+Shift+T 等を送信する) | 唯一実用的だが Accessibility 権限が必要である。代わりに Cmd+D による複製と name の変更と `make new attachment` を組み合わせる経路を `experiments/api-surface.md` で発見している |
| pasteboard 経由でのペースト | NSAttributedString を clipboard に置いて Cmd+V で投入する経路。paste の発火には UI スクリプティング (Cmd+V の送信) が必要であり、Accessibility 権限が前提となる |

## 編集レシピへの影響

`docs/01-facts.md` の §6 および `docs/02-recipe.md` の制約に集約される。

- タイトル / 見出し / 小見出し / ブロック引用 / チェックリスト (チェック状態) / ハイライト / 画像および添付は、`set_body` 経由では再現できない。
- ハイパーリンクは新規追加のみ可能である (ラウンドトリップで破壊される。`experiments/hyperlink-attempts.md` を参照)。
- 等幅およびダッシュ付きリストは HTML 経路から再現可能な段落スタイルである (例外的なケース)。
- 上記の再現不可能な要素を含むメモは、編集対象から外すことを推奨する。

## 実験データ

- 本探索のスクリプト: `scripts/py/heading_probe.py`, `heading_probe2.py`, `class_probe.py`, `class_probe2.py`
- 本探索の結果データ: `data/heading_probe/`, `data/class_probe/` (gitignored、再実行で再生成可能)
- 追加分のスクリプト: `scripts/py/seed_t_probes.py` の T18 / T19 / T20 / T23
- 追加分のダンプ: `data/probes/HTMLTest/T18-mono-probe.html`, `T19-probe.html`, `T20-tag-probe.html`, `T23-heading-combo.html`
