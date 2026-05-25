# テキスト 1 ノード置換テスト

## 目的

正規化済みの HTML を BeautifulSoup でパースし、テキストノードを 1 つだけ文字列置換した上で再シリアライズし、`set_body` で書き戻して `get_body` で結果を確認する。意図した変化のみが発生するかを検証する。

## 方法

`experiments/roundtrip.md` でラウンドトリップ 2 回目以降に不動点となった合成メモ 5 件を対象とし、`set_body` 後の `get_body` 結果 (actual) と、正規化済み HTML の対応箇所だけを文字列置換した結果 (expected) を比較する。ランナーは `scripts/py/edit_test.py`。

## 結果

### 5 件すべてで意図した変化のみが発生した

| メモ | 編集内容 | 意図通りの編集 | 編集後の不動点 | 備考 |
|---|---|---|---|---|
| S01-plain | 第 1 段落のテキスト置換 | 成功 | 達成 | |
| S05-inline-decor | `<b>bold</b>` 周辺のテキスト置換 | 成功 | 達成 | インライン装飾の隣接テキスト |
| S06-bullet | `<li>` 内のテキスト置換 | 成功 | 達成 | |
| S07-numbered | 番号付き `<li>` 内のテキスト置換 | 成功 | 達成 | |
| S03-headings | 見出しの `<span>` 内テキスト置換 | 成功 | 達成 | `font-size:18px` は維持される |

正規化済みの HTML 上でテキストノードを 1 つ置換し `set_body` を呼ぶという編集パターンは、意図した文字列変化のみを発生させることが確認された。

### BeautifulSoup のシリアライザの非透過性は問題にならない

シリアライザが完全に透過 (出力バイト列が入力と完全一致) となるケースは 0 件である。差分は `<br>` と `<br/>` (HTML5 自閉スタイル) の表現の違いのみであり、メモ.appはこの 2 つを同一として正規化するため、最終的には `actual == expected` が成立する。

```diff
-<div><b><span style="font-size: 24px">S05-inline-decor</span></b><br></div>
+<div><b><span style="font-size: 24px">S05-inline-decor</span></b><br/></div>
```

### 編集後のメモも不動点

編集後の `get_body` 結果をさらに `set_body` → `get_body` しても完全に一致する (5 件すべてで達成)。したがって、編集を繰り返し連続して安全に行える。

## 編集レシピへの含意

GUI で作成された既存メモを破壊せずに編集するための基本パターンが、本テストで確立した。

```python
# Step 1: 正規化 (1 回ラウンドトリップする)
body = notes.get_body(note_name)
notes.set_body(note_name, body)
time.sleep(1.5)
normalized = notes.get_body(note_name)

# Step 2: パースし、テキストノードを 1 つ置換し、再シリアライズする
soup = BeautifulSoup(normalized, "html.parser")
target = find_unique_text_node(soup, "needle")
target.replace_with(NavigableString(new_text))

# Step 3: 書き戻し
notes.set_body(note_name, str(soup))
```

注意点として、編集対象のテキストはメモ内で一意な部分文字列でなければならない (複数マッチを避ける必要がある)。また、既存のリンク (`<a href>`) を含むメモは別問題である。`get_body` の出力 HTML には URL が含まれないため、`set_body` で書き戻すとリンクが切れる (`experiments/roundtrip.md` を参照)。

実装は `scripts/py/edit_recipe.py` にあり、使い方は `docs/02-recipe.md` を参照。

## 関連ファイル

- `data/edit/*.normalized.html` — 編集前の正規化済み HTML
- `data/edit/*.expected.html` — 期待値 (純粋な文字列置換結果)
- `data/edit/*.bs4-out.html` — BeautifulSoup のシリアライズ出力
- `data/edit/*.actual.html` — `set_body` → `get_body` の結果
- `data/edit/*.bs4-vs-expected.diff` — BeautifulSoup の出力と期待値の差分 (`<br/>` の差のみ)
- `data/runs/edit-*.json` — 実行サマリ
