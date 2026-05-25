# ハイライト (背景色) の HTML 経路での再現可否

## 目的

GUI で適用されるハイライト (背景色) を `set_body` 経由で再現できるかを、CSS バリアントを網羅的に試行して検証する。

## 背景

`experiments/roundtrip.md` で T12 (色とハイライト) を観察した結果、文字色 (`<font color="#FF0000">`) は完全に保存される一方で、ハイライト (黄色背景) は body HTML に痕跡が残らず、`attachments()` にも出てこない。検出も保存もできない状態である。

本実験ではハイライトを HTML 経路から作る方法があるかを T21-highlight-probe で検証した。

## 方法

`scripts/py/seed_t_probes.py` の T21-highlight-probe で 10 バリアント (CSS 9 種類と control 1 種類) を `create_note` で投入し、`get_body` の出力を確認する。

## バリアント全列挙

入力 HTML (`seed_t_probes.py` 内の `T21_HIGHLIGHT_PROBE`):

| バリアント | 入力 HTML |
|---|---|
| A | `<span style="background-color: yellow">A span bg yellow</span>` |
| B | `<span style="background-color: #FFFF00">B span bg #FFFF00</span>` |
| C | `<span style="background: yellow">C span background yellow</span>` |
| D | `<font style="background-color: yellow">D font style bg yellow</font>` |
| E | `<div><font background="yellow">E font background attr</font></div>` |
| F | `<mark style="background-color: yellow">F mark + style bg</mark>` |
| G | `<div><span style="-apple-highlight: yellow">G -apple-highlight prop</span></div>` |
| H | `<span style="background-color: yellow; color: black">H bg yellow + color black</span>` |
| I | `<div><span style="-webkit-text-fill-color: yellow">I webkit text-fill</span></div>` |
| Z | `<div>Z plain body</div>` (control) |

## 観察結果

`data/probes/HTMLTest/T21-highlight-probe.html` の `get_body` 出力:

```
<div><b><span style="font-size: 24px">T21-highlight-probe</span></b></div>
<div>Variant A span bg-color yellow:</div>
<div>A span bg yellow</div>
<div>Variant B span bg-color hex:</div>
<div>B span bg #FFFF00</div>
<div>Variant C span background shorthand:</div>
<div>C span background yellow</div>
<div>Variant D font with style bg:</div>
<div>D font style bg yellow</div>
<div>Variant E font background attr:</div>
<div>E font background attr</div>
<div>Variant F mark with style bg:</div>
<div>F mark + style bg</div>
<div>Variant G apple-highlight property:</div>
<div>G -apple-highlight prop</div>
<div>Variant H bg + fg color:</div>
<div>H bg yellow + color black</div>
<div>Variant I webkit text-fill-color:</div>
<div>I webkit text-fill</div>
<div>Variant Z control:</div>
<div>Z plain body</div>
```

9 バリアントすべてで `background-color` 関連のスタイルが完全に剥がされ、プレーンテキスト化される。GUI 上でも目視で確認したが、ハイライトは適用されない (Format メニューでも「本文」と判定される)。

副次的な観察として、バリアント H (`background-color: yellow; color: black`) では `color: black` も同時に剥がれた。文字色は単独であれば保存される (`experiments/boundary.md` の B05 で確認済み) ため、`background-color` と組み合わせるとパーサが `style` 属性全体をストリップする挙動になると推測される。

## 結論

ハイライト (背景色) は HTML 経路では再現できない (`experiments/roundtrip.md` の結論を本実験で再確認した)。

`background-color` プロパティ自体が NSAttributedString の HTML reader に未マッピングであると推定される。`-apple-highlight` のような Apple 独自のトークンも同様にマッピングされていない。ハイライトを設定する唯一の方法は GUI 操作 (Format → ハイライト → Yellow) であり、`set_body` を経由する API には経路が存在しない。

## 編集レシピへの影響

`docs/01-facts.md` の §2.5 (ストリップされる装飾系) および §3.1 (検出不可能な損失) にこの結果が反映されている。実用上は以下となる。

- ハイライトを含むメモは編集対象から外す (`set_body` 通過で完全に消失し、検出も不可能である)
- ハイライトを新規に付与する方法は HTML 経路には存在しない (GUI 操作以外に手段なし)
