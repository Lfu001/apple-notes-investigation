# ハイパーリンクの保持と作成の可否

## 目的

GUI で作成されたハイパーリンクを `set_body` で保持できるか、また `set_body` 経由で新規にリンクを作成できるかを検証する。

## 背景

`experiments/roundtrip.md` で T10 (リンク) を観察した結果、以下が確認された。

- GUI で Cmd+K により作成したリンクは、`get_body` の HTML に URL 情報が一切現れない (`<u>` すら付かず、純粋なプレーンテキストとなる)
- したがって `set_body` で書き戻すと URL は失われる
- リンクの状態は `attachments()` にも出ない

「`<a href>` を含む HTML を `set_body` で投入したらどうなるか」を確認するのが T22-checklist-link-probe のリンク部分である。さらに「投入後にもう一度 `set_body` した場合に URL は保持されるか」を T22b で検証する。

## 方法

`scripts/py/seed_t_probes.py` の T22-checklist-link-probe で 10 バリアント (リンク 5 種 + チェックリスト 4 種 + control の Z) を `create_note` で投入する。T22b-checklist-link-probe は T22 と同じ入力で投入した後、追加で `set_body(get_body(...))` を 1 回適用してラウンドトリップを検証する。

## バリアント全列挙 (リンク部分のみ)

| バリアント | 入力 HTML |
|---|---|
| E | `<div><a href="https://example.com">E basic link</a></div>` |
| F | `<div><a href="https://example.com" class="Apple-link">F classed link</a></div>` |
| G | `<div><a href="https://example.com" rel="noopener">G rel attr</a></div>` |
| H | `<div><a name="anchor">H named anchor</a></div>` (href なし) |
| I | `<div><a href="https://example.com"><b>I bold inside a</b></a></div>` |

チェックリスト関連のバリアント A-D は `experiments/paragraph-style-search.md` の対象であり、本ドキュメントの範囲外である。

## 観察結果

### T22 の `get_body` 出力 (`set_body` 1 回目通過後)

```html
<div>Variant E basic a-href:</div>
<div><u>E basic link</u><br></div>
<div>Variant F a-href + Apple-link class:</div>
<div><u>F classed link</u><br></div>
<div>Variant G a-href + rel attr:</div>
<div><u>G rel attr</u><br></div>
<div>Variant H a-name anchor:</div>
<div>H named anchor</div>
<div>Variant I a-href wrapping bold:</div>
<div><b><u>I bold inside a</u></b><br></div>
```

href を持つバリアント (E, F, G, I) は `<u>text</u>` として出力される。URL 情報は HTML に現れない。name 属性のみ (href なし) のバリアント H は `<u>` すら付かず、プレーンテキストとなる。

### GUI 上での動作確認 (ユーザー目視とクリック操作、2026-05-23)

T22 をメモ.appで開いて各バリアントをクリックした結果は以下のとおり。

- E / F / G / I: クリックでブラウザが起動し `https://example.com` を開く。URL は内部表現に保存されている。
- H (href なし): プレーンテキストとして表示され、クリックには反応しない。

つまり、`<a href="...">` を `set_body` で投入すると、GUI 上で動作する青リンクが作成される。URL は NSAttributedString の属性として内部に保存されるが、`get_body` で HTML に書き出されない (メモ.appのシリアライザの入出力の非対称性)。

### T22b: ラウンドトリップ後の URL 検証

T22 と同一の内容で T22b を投入し、追加で `set_body(get_body("T22b"))` を 1 回適用した。

T22b の GUI 確認 (ユーザー目視とクリック、2026-05-23) の結果は以下のとおり。

- E / F / G / I: クリックに反応せず、URL が完全に消失している。

したがって、`<a href>` で作成したリンクも、ラウンドトリップで URL が破壊される。

## バリアント別の挙動

| 入力 | `get_body` 出力 | GUI 動作 (新規作成時) | ラウンドトリップ後 |
|---|---|---|---|
| `<a href="X">text</a>` | `<u>text</u>` | クリックで X を開く | URL は破壊される |
| `<a href="X" class="Apple-link">text</a>` | `<u>text</u>` (class は剥がれる) | 動作するリンク | URL は破壊される |
| `<a href="X" rel="noopener">text</a>` | `<u>text</u>` (rel は剥がれる) | 動作するリンク | URL は破壊される |
| `<a href="X"><b>text</b></a>` | `<b><u>text</u></b>` | 動作するリンク + 太字 | URL は破壊される |
| `<a name="anchor">text</a>` | `text` (`<u>` も付かない) | プレーンテキスト (href が必須) | 該当なし |

## 入出力の非対称性のパターン分類

| 機能 | `get_body` で保持 | `set_body` で作成 | `set_body` で保持 (ラウンドトリップ生存) |
|---|:-:|:-:|:-:|
| タイトル / 見出し段落 | 可 (`<h1>` 等) | 不可 | 不可 |
| 等幅段落 | 可 | 可 | 可 |
| ダッシュ付きリスト | 可 | 可 | 可 |
| ハイパーリンク (URL) | 不可 | 可 | 不可 |
| ハイライト (背景色) | 不可 | 不可 | 不可 |
| チェックリスト状態 | 不可 | 不可 | 不可 |
| ブロック引用段落 | 不可 | 不可 | 不可 |

ハイパーリンクは唯一「`set_body` での作成は可能だが、保持はできない」というパターンに該当する。

## 編集レシピへの含意

`docs/01-facts.md` の §2.4 (書き込み専用) および `docs/02-recipe.md` の `append_link` 関数にこの結果が反映されている。

- 既存メモへの新規リンク追加は可能である。`edit_recipe.append_link("Note", "text", "https://...")` で `<a href>` を含む HTML を追加すると、GUI 上で動作するリンクが表示される。
- GUI 由来のリンクの保護は不可能である (`experiments/roundtrip.md` の結論通り)。
- ラウンドトリップ後のリンクは破壊される。一度 `set_body` で作成したリンクも、その後の `get_body` → 編集 → `set_body` の流れで URL が失われる。
- 編集前の URL の抽出も不可能である。`get_body` にも `plaintext` にも URL は出ないため、ブラックボックスからは取り出せない。

したがって、リンクの実用パターンは新規メモおよび末尾追加かつ書き込み専用に限定される (`edit_recipe.append_link` の用途)。
