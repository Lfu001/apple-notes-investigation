# メモ.appの HTML パーサの個別挙動

`set_body` の HTML パーサが見せる、副次的だが再現性があり、入出力の対応関係に影響する挙動の置き場である。`docs/01-facts.md` の §5 から参照される、入出力マッピングの細部に関する観察集として位置づけられる。

エビデンスの強さに関する注意: 本ドキュメントの観察は、(a) コミット済みの観測メモのダンプで直接示されているもの、(b) `scripts/py/seed_t_probes.py` の入力再構成の過程で副次的に得られたが現在のダンプには残っていないもの、の 2 種類が混在する。各挙動の節内で直接観察と入力再構成中の派生観察を明示する。

---

## 1. `<div>` ラッパー越しに「パーサに書き換えられた」inline 要素は末尾に `<br>` を残す

### 観察の核 (直接観察)

ある inline タグがトップレベル (`<div>` ラップなし) で書かれた場合、パーサがストリップしても出力には `<br>` が付かない。これは現在のダンプから直接観察できる。

| 入力 | `get_body` 出力 | 出典 |
|---|---|---|
| `<mark>X</mark>` | `<div>X</div>` | `scripts/py/seed_t_probes.py` T20-G / `data/probes/HTMLTest/T20-tag-probe.html` の line 14-15 |
| `<span style="background-color: yellow">X</span>` | `<div>X</div>` | T21-A / `data/probes/HTMLTest/T21-highlight-probe.html` の line 2-3 |
| `<font style="background-color: yellow">X</font>` | `<div>X</div>` | T21-D / `T21-highlight-probe.html` の line 8-9 |
| `<abbr>X</abbr>` | `<div>X</div>` | T20-L / `T20-tag-probe.html` の line 24-25 |

### 派生観察 (入力再構成中)

T20 および T21 の入力を再構成する過程で、上記の各タグを `<div>` 内に置いた版を試したところ、`get_body` の出力に末尾の `<br>` が混入し、元のダンプとバイト一致しなかった。最終的に「トップレベル形に書き直す」ことでダンプと一致した。この経緯は `scripts/py/seed_t_probes.py` の T21 バリアント上のコメントに残っている (`# NOTE: variants that ended up stripped to plain text were written at top level — wrapping in <div> causes Notes to emit a trailing <br>`)。

したがって、以下が間接的に示唆されるが、現状のダンプに直接の証拠は残っていない。

| 入力 (再構成中に試行) | 観察された `get_body` 出力 |
|---|---|
| `<div><mark>X</mark></div>` | `<div>X<br></div>` |
| `<div><span style="background-color: yellow">X</span></div>` | `<div>X<br></div>` |
| `<div><font style="background-color: yellow">X</font></div>` | `<div>X<br></div>` |
| `<div><abbr>X</abbr></div>` | `<div>X<br></div>` |
| `<div><abbr title="X">Y</abbr></div>` | `<div><u>Y</u><br></div>` (本節と次節の効果が合算された結果) |

これらを将来ダンプ化したい場合は、`seed_t_probes.py` に専用の観測用メモを追加して直接観察に格上げする。

### ルールの解釈 (推定)

上記の派生観察を額面通りに取ると、「`<div>` 内に置かれた inline 要素をパーサが書き換える (ストリップするか、別タグにマップするか) と、出力の親 `<div>` 末尾に `<br>` が付与される」と読める。

`<abbr title>` の事例 (`<u>` に書き換わるが `<br>` も付く) があるため、「ストリップ限定」ではなく「書き換えが発生したケース全般」と読むのが整合的である。

### 適用範囲外と未確認

- そのまま生き残る装飾タグ (`<b>`, `<i>`, `<u>`, `<strike>`, `<font color>`, `<span style="font-size">`) は、書き換えが発生しないため本節の対象外と推定される。ただし `<div><b>X</b></div>` を直接観測用メモで確かめてはいない。
- `<ruby>` をストリップして `<div>漢字かんじ</div>` 等にする挙動 (ルビ情報損失) は T20-O で直接観察済みである。一方、元の T20 ダンプ (`data/probes/HTMLTest/T20-tag-probe.html` の line 31) は `<div>漢字かんじ<br></div>` (`<br>` 付き) であるが、現在の入力再構成 (トップレベルおよび `<div>` ラップのいずれの形) では `<br>` を再現できていない。ストリップ自体は観察済みだが、`<br>` の有無は現時点で特定していない。
- 多重ラップ (`<div><div><span>X</span></div></div>` 等) は未試行である。

### なぜ気にするか

- 入力から出力への逆算に役立つ。`get_body` の出力に「装飾は剥がれた + 末尾 `<br>`」の組が出たら、元の入力に `<div>` 系のブロックラップがあった可能性が高い。T18-T23 の入力再構成で実際に有用であった。
- 編集時の `<br>` ノイズを抑制できる。`<span>` 等でラップした装飾がパーサに書き換えられる場合、ラップ方法次第で末尾 `<br>` が増減する。連続編集で `<br>` のカウントが予測しにくくなる原因の 1 つである。

---

## 2. `<abbr title="...">` は `<u>` に書き換えられる

### 観察の核 (直接観察)

`<abbr>` タグに `title` 属性がない場合、プレーンテキストとしてストリップされる。これは現在のダンプから直接観察できる。

| 入力 | `get_body` 出力 | 出典 |
|---|---|---|
| `<abbr>X</abbr>` | `<div>X</div>` | T20-L / `data/probes/HTMLTest/T20-tag-probe.html` の line 24-25 |

### 派生観察 (入力再構成中)

T20-L バリアントの最初の試行 `<div><abbr title="abbreviation">abbr sample</abbr></div>` は `<div><u>abbr sample</u><br></div>` を出力した。元の T20 ダンプは `<div>abbr sample</div>` (下線なし、`<br>` なし) であったため、`title` 属性と `<div>` ラップの両方を外した形でバイト一致した。

したがって、以下が間接的に示唆される。

| 入力 (再構成中に試行) | 観察された `get_body` 出力 |
|---|---|
| `<div><abbr title="X">Y</abbr></div>` | `<div><u>Y</u><br></div>` |

`<u>` は `title` 属性に起因し、`<br>` は §1 の `<div>` ラップに起因する。両者は独立した別のルールの合成として読める。

### ルールの解釈 (推定)

ブラウザにおける `<abbr title>` の標準的な挙動は「説明付きの省略語、ドット下線表示」である。Cocoa の HTML reader はこれを下線の文字属性 (NSAttributedString の underline) にマップしているものと推定される。意図せずに `<abbr title>` を使うと、装飾上は `<u>` と区別がつかない。

### 適用範囲外と未確認

- トップレベルの `<abbr title="X">Y</abbr>` (`<div>` ラップなし) の挙動は直接観測していない。`<u>` だけ付いて `<br>` は付かないと推測されるが、現時点で確認していない。

### なぜ気にするか

入力 HTML を組み立てるときに `title` 属性を付け忘れるか付けてしまうかの違いで、装飾が出たり消えたりする。意図的に `<u>` を使いたい場合は素直に `<u>` または `<ins>` を使うほうが副作用が少ない (`<ins>` は `<u>` のエイリアスである。`experiments/paragraph-style-search.md` を参照)。

---

## 追記の方針

新しい個別挙動が見つかった場合は、以下の形式で末尾に追記する。

```
## N. 見出し

### 観察の核 (直接観察)

コミット済みの観測メモまたはダンプで直接示せる入力 → 出力の対応を表で列挙し、出典 (file:line) を引く。

### 派生観察 (入力再構成中)  ※あれば

ダンプに残っていないが、入力再構成等で副次的に得られた観察。後でダンプ化したいものはここに残しておく。

### ルールの解釈 (推定)  ※あれば

観察の核と派生観察から導かれるルールの仮説。「推定」と明示する。

### 適用範囲外と未確認

ルールが当てはまらない領域、または試していない領域。

### なぜ気にするか
```

「観察の核」が空のもの (派生観察と推測のみ) は本ドキュメントには置かない。それは別の場所で仮説として管理する。
