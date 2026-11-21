# フォントサイズの実測

## 目的

GUI で設定した各段落スタイルと、`set_body` 通過後の同じ段落の実レンダリングサイズ (pt) を Font Panel (Cmd+T) で計測する。`experiments/roundtrip.md` で「`set_body` はタイトル / 見出し等の段落スタイルを破壊する」ことは確認済みだが、その影響が実フォントサイズ (pt 値) のレベルで何 pt の差になるのかを定量的に確認する。

## 測定方法

1. メモ.appの `HTMLTest` フォルダで対象メモを開く。
2. 各段落の本文をトリプルクリックで全選択する。
3. Format → Font → Show Fonts (Cmd+T) で Font Panel を開く。
4. Family / Typeface / Size を記録する。

## テスト対象

- `T17a-sizes` — GUI で各段落スタイルを設定したもの (paragraph style が生きている before)
- `T17b-sizes` — T17a を Cmd+D で複製し、`get_body` → `set_body` でラウンドトリップしたもの (after)

T17a と T17b は作成時点では完全に同一の HTML である (両方とも `<h1>` / `<h2>` / `<h3>` / `<tt>` のセマンティック HTML)。違いは T17b に `set_body` を 1 回通したかどうかのみである。

作成手順は `docs/methods/test-notes.md` の T17a / T17b の節を参照。

### T17b ラウンドトリップ 1 回目の HTML (参考)

```
<div><b><span style="font-size: 24px">T17b-sizes</span></b></div>
<div><b><span style="font-size: 24px">Title sample</span></b></div>
<div><b><span style="font-size: 18px">Heading sample</span></b></div>
<div><b>Subheading sample</b></div>
<div>Body sample</div>
<div><font face="Courier"><tt>Monostyled sample</tt></font>...</div>
<div>Block quote sample</div>
```

## 計測結果

計測は 2026-05-23 にユーザー目視で実施した。実行環境は `docs/methods/environment.md` を参照。

### T17a-sizes (GUI 由来、paragraph style が生存)

| 段落 | Family | Typeface | Size (pt) |
|---|---|---|---|
| Title sample | System font | Bold | 20 |
| Heading sample | System font | Bold | 16 |
| Subheading sample | System font | Bold | 13 |
| Body sample | System font | Regular | 13 |
| Monostyled sample | (不明、「フォントを選択してください」) | — | 12 |
| Block quote sample | System font | Regular | 13 |

### T17b-sizes (`set_body` 通過後、paragraph style が消失)

| 段落 | Family | Typeface | Size (pt) | HTML 上の font-size |
|---|---|---|---|---|
| Title sample | System font | Bold | 24 | 24px |
| Heading sample | System font | Bold | 18 | 18px |
| Subheading sample | System font | Bold | 13 | (指定なし) |
| Body sample | System font | Regular | 13 | (指定なし) |
| Monostyled sample | (不明、「フォントを選択してください」) | — | 12 | (指定なし、`<tt>` のみ) |
| Block quote sample | System font | Regular | 13 | (指定なし、`<div>` のみ) |

## 差分の所見

| 段落 | GUI 由来 (pt) | `set_body` 後 (pt) | 差 | コメント |
|---|---:|---:|---:|---|
| タイトル | 20 | 24 | +4 | HTML の `font-size: 24px` がそのまま pt として焼き付き、GUI 由来より 20% 大きく描画される |
| 見出し | 16 | 18 | +2 | HTML の `font-size: 18px` がそのまま pt として焼き付き、12.5% 大きく描画される |
| 小見出し | 13 | 13 | 0 | HTML 上は `<b>` のみで size 指定がなく、デフォルトの 13pt にフォールバックする。サイズは一致するが、paragraph style 属性のみが失われ、太字本文と区別がつかない状態となる |
| 本文 | 13 | 13 | 0 | 元から無印 `<div>` のため、変化なし |
| 等幅 | 12 | 12 | 0 | `<tt>` (`set_body` 後は `<font face="Courier"><tt>`) で Courier 12pt が維持される |
| ブロック引用 | 13 | 13 | 0 | プレーン `<div>` で表現されるため、本文と同じ 13pt となる |

CSS の px の数値がそのまま pt として描画されることが Font Panel の計測で確認できた。メモ.appは `<span style="font-size: Npx">` の N を pt 値として扱っている (CSS における px ≠ pt の通常仕様とは異なる挙動である)。

## 結論

1. `set_body` はタイトルと見出しの見た目サイズを物理的に大きくする。それぞれ +4pt (20→24)、+2pt (16→18) の差となる。これまで「テーマサイズより大きい」と定性的に書かれていた挙動の定量的な裏付けが取れた。
2. 小見出し / 本文 / ブロック引用 / 等幅は見た目のサイズが変わらない。HTML 上で `font-size` の指定がないか、本文と同じ無印 `<div>` に正規化されるため、デフォルトの 13pt (等幅は 12pt) にフォールバックする。
3. paragraph style 属性の消失とサイズの変化は独立している。小見出しは paragraph style が消えてもサイズは保たれる。タイトルと見出しは paragraph style が消え、かつサイズが拡大する (二重に変化する)。
4. メモ.appは CSS の px を pt として描画している。24px の HTML が 24pt で描画されている。これはブラウザ的な CSS 解釈ではなく、メモ.app独自の単位読み替えと推定される。

### デフォルトのテキストサイズとの関係

この記録のポイント値は、macOS 26.4.1 でデフォルトのテキストサイズを Medium にした場合の実測値。他の設定での書き戻し後の値は、この環境では測定していない。

macOS 27.2.1 の追試では、書き戻し後の HTML のサイズ指定と、メモからコピーした RTF のポイント値が、いずれも書き戻し時の設定によって変化した。画面上の表示サイズは 3 設定での直接測定に至っていない。[3 段階での比較](app-intents.md#末尾追記と-html-の全文書き戻し)

## 編集者への含意

`docs/01-facts.md` の §3.1 にこの結果が反映されている。

`set_body` 後の見た目は「太字 + 元と違うサイズ」であり、単なる太字本文ではなく強調された別段落のような印象となる。タイトル / 見出しを含むメモに `set_body` を一度でも通すと、視覚的にも明らかに別物となる。
