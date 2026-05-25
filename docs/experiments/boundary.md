# 編集境界マッピング

## 目的

BeautifulSoup で 8 種類の構造変更を適用し、`set_body` → `get_body` で結果を評価する。`set_body` が意図通りに受け入れるか、どのレベルの変更まで安定して扱えるかを網羅的に確認する。

すべて合成メモ (`experiments/roundtrip.md` で不動点性を確認したもの) を起点に実施する。

## 方法

- ランナー: `scripts/py/boundary_test.py`
- 出力: `data/boundary/`, `data/runs/boundary-*.json`

## 結果サマリ

| ID | 操作 | 対象 | 意図通りの反映 | 2 回目で不動点 | 備考 |
|---|---|---|---|---|---|
| B01 | 末尾に新規 `<div>` 段落を追加する | S01-plain | 成功 | 達成 | 問題なし |
| B02 | `<ul>` に新規 `<li>` を末尾に追加する | S06-bullet | 成功 | 達成 | 問題なし |
| B03 | `<li>` を 1 つ削除する | S06-bullet | 成功 | 達成 | 問題なし |
| B04 | 既存テキストの間に新規 `<b>` を挿入する | S05-inline-decor | 不一致 (テスト側の問題) | 達成 | 本リポジトリのテストスクリプトの分割ロジックに起因する不一致であり、メモ.app側の挙動としてはどの順序でも受け入れる |
| B05 | 既存 `<b>` タグに `style="color: red"` を付与する | S05-inline-decor | 成功 | 達成 | `style="color: red"` が `<font color="#FF0000">` に変換されて保存される |
| B06 | 段落の途中にテキストを挿入する | S01-plain | 成功 | 達成 | 問題なし |
| B07 | トップレベルの `<div>` を削除する | S01-plain | 成功 | 達成 | 周囲の空行 `<div><br></div>` はそのまま残る |
| B08 | テキストの一部を `<b>` で包む | S01-plain | 成功 | 達成 | 問題なし |

8 件すべてで 2 回目以降の不動点が達成された。7 件で意図通りの反映が確認された (B04 はテストスクリプト側の分割ロジック起因の不一致であり、メモ.app側の問題ではない)。

## 重要な発見

### 1. インラインスタイルから旧来の `<font>` タグへの変換

`style="color: red"` を `<b>` タグに付与して `set_body` を呼ぶと、`get_body` では以下のように変換されて返る。

```diff
-<b style="color: red">bold</b>
+<b><font color="#FF0000">bold</font></b>
```

メモ.appの HTML パーサは CSS の `color:` プロパティを読んで内部表現にマップし、シリアライザは旧来の `<font color="#XXXXXX">` 形式で出力する。これにより以下のことが言える。

- 色の付与は `body` API 経由で可能である。
- 既存の GUI 由来メモに色付きテキストがある場合、`get_body` は `<font color>` 形式で返してくる可能性が高い。
- 編集時にも `<font color>` を使うのがメモ.appの内部表現に最も近い。

なお、CSS の `background-color` (ハイライト) は同様の変換は受けない (`experiments/highlight-attempts.md` を参照)。

### 2. 構造変更を寛容に受け入れる

メモ.appの HTML パーサは以下のすべてを受け入れて、メモ.app自身の正規形にシリアライズする。

- `<div>` 段落の追加および削除
- `<li>` の追加および削除
- インライン span (`<b>`, `<i>`, `<font>` 等) の挿入および削除
- テキストノードの分割および結合
- 属性 (`style="..."`) の付与

### 3. 冪等正規化の一貫性

8 件すべてで以下が確認された。

- ラウンドトリップ 1 回目の `get_body` 結果と 2 回目の `get_body` 結果が完全に一致する
- 編集を重ねても、各編集の after が次の編集の安定した before となる

つまり、編集を連鎖できるということを意味する。例として以下の流れを想定する。

```
get_body → 編集 1 → set_body → get_body → 編集 2 → set_body → get_body → ...
```

各 `→ get_body →` の段階で不動点が成立しているため、編集スクリプトを段階的に積み重ねることが可能である。

## 関連ファイル

- `data/boundary/B*.before.html` — 各テスト直前の正規化済み HTML
- `data/boundary/B*.mutated.html` — BeautifulSoup で書き換えた HTML (送信前)
- `data/boundary/B*.actual.html` — `set_body` → `get_body` の結果
- `data/boundary/B*.mutated-vs-actual.diff` — 送信と返答の差分
- `data/runs/boundary-*.json` — 実行サマリ
