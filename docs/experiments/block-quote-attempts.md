# ブロック引用段落の HTML 経路での再現可否

## 目的

GUI で適用されるブロック引用段落スタイルを、`<blockquote>` 等の HTML 入力から `set_body` 経由で再現できるかを検証する。

## 背景

`experiments/roundtrip.md` で T04 (等幅とブロック引用) を観察した結果、以下が確認された。

- GUI で適用されたブロック引用段落は、`get_body` の HTML 上ではプレーン `<div>` として出力され、本文段落と区別がつかない
- したがって `set_body` を通すとブロック引用の段落属性は失われる (本文化される)
- `attachments()` にも痕跡が残らない

`experiments/paragraph-style-search.md` でも `<blockquote>` タグを試したが「完全ストリップ」と判定された。本実験ではこの結論を別経路から確認するための補助実験として T19-probe を実施した。

## 方法

`scripts/py/seed_t_probes.py` の T19-probe で 6 バリアントを `create_note` で投入し、`get_body` の出力と、GUI で開いた際の Format メニュー判定 (「本文 / タイトル / 見出し / 小見出し / ブロック引用 / 等幅」) を確認する。

## バリアント全列挙

| バリアント | 入力 HTML | テスト意図 |
|---|---|---|
| A | `<blockquote>bare blockquote</blockquote>` | bare `<blockquote>` タグ |
| B | `<div><blockquote>div-wrapped blockquote</blockquote></div>` | `<div>` ラップで挙動が変わるか |
| C | `<blockquote class="Apple-blockquote">classed blockquote</blockquote>` | `Apple-*` class で hardcoded マッピングがあるか (`Apple-dash-list` の前例) |
| D | `<div>plain body sample</div>` | control |
| E | `<h1>bare h1</h1>` | タイトル段落の再確認 (`experiments/paragraph-style-search.md` の結論の補強) |
| F | `<div><h1>div-wrapped h1</h1></div>` | 同上の `<div>` ラップ版 |

## 観察結果

`data/probes/HTMLTest/T19-probe.html` の `get_body` 出力:

```
<div><b><span style="font-size: 24px">T19-probe</span></b></div>
<div>Variant A (bare blockquote):</div>
<div>bare blockquote</div>
<div>Variant B (div-wrapped blockquote):</div>
<div>div-wrapped blockquote</div>
<div>Variant C (blockquote class=Apple-blockquote):</div>
<div>classed blockquote</div>
<div>Variant D (plain body control):</div>
<div>plain body sample</div>
<div>Variant E (bare h1):</div>
<div><b><span style="font-size: 24px">bare h1</span></b></div>
<div>Variant F (div-wrapped h1):</div>
<div><b><span style="font-size: 24px">div-wrapped h1</span></b></div>
```

### ブロック引用バリアント (A, B, C)

`<blockquote>` タグも `class="Apple-blockquote"` 属性も完全に剥がれ、プレーン `<div>` となる。GUI 上で Format メニューで判定すると「本文」となる (ブロック引用段落スタイルにはならない。ユーザー目視で確認、2026-05-23)。control バリアント D との区別はつかない。

### h1 バリアント (E, F)

`<h1>` は `<div><b><span style="font-size: 24px">...</span></b></div>` に変換される (`experiments/roundtrip.md` および `experiments/paragraph-style-search.md` の結論通り)。GUI 上で Format メニューで判定すると「本文」となる (タイトル段落スタイルにはならず、太字本文となる)。bare 版と `<div>` ラップ版で挙動の差はない。

## 結論

ブロック引用段落スタイルは HTML 経路では再現できない (`experiments/paragraph-style-search.md` の結論を本実験で再確認した)。

`experiments/paragraph-style-search.md` では以下を試行したが、いずれも再現に至らなかった。

- `<blockquote>` 単体: ストリップされる
- `class="Apple-blockquote"`: ストリップされる (`Apple-dash-list` のような hardcoded マッピングは存在しない)
- `class="Apple-block-quote"`, `Apple-quote` 等のバリエーション: いずれもストリップされる

本実験 (T19) では `<div>` ラップおよび class 単独をさらに試したが、これらもいずれも再現に至らなかった。

ブロック引用を設定する唯一の方法は GUI 操作 (Format → ブロック引用、Cmd+') であり、`set_body` を経由する API には経路が存在しない。

## 編集レシピへの影響

`docs/01-facts.md` の §2.5 (ストリップされる装飾系) および §3.1 (検出不可能な損失) にこの結果が反映されている。実用上は以下となる。

- ブロック引用を含むメモは編集対象から外す (`set_body` 通過で完全に消失し、検出も不可能である。プレーンな `<div>` と区別がつかないため)
- ブロック引用を新規に付与する方法は HTML 経路には存在しない (GUI 操作以外に手段なし)

## 副次観察: h1 バリアントの挙動

バリアント E および F の h1 試行は、`experiments/paragraph-style-search.md` の結論を再確認する control として機能した。`<div>` ラップの有無にかかわらず、`<h1>` は太字と 24px の `<span>` の組み合わせに変換されるが、内部の paragraph style 属性は立たない。

この挙動は `experiments/paragraph-style-search.md` の T23-heading-combo (16 種類の組み合わせ試行) でも追試され、見出し関連は全候補で再現に至らないことが最終確定した。
