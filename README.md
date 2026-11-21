# Apple メモ.app HTML ラウンドトリップ調査

Mac のメモで本文を編集したとき、段落スタイル、文字サイズ、リンク、チェックリストなどの書式がどこまで保たれるかを調べるリポジトリ。macOS 26 の AppleScript による HTML 書き戻しと、macOS 27 の App Intents に関連する操作を記録している。

## 調査手法と範囲

従来の調査では、Apple が公開している AppleScript および JXA を経由したブラックボックステストを行った。具体的には、`osascript` からメモ.appの scripting dictionary (Script Editor → File → Open Dictionary で閲覧可能な公開面) を呼び出し、`body` / `plaintext` / `attachments` / `name` 等のプロパティに入力を与えた際の戻り値を記録している。

macOS 27.2.1 では、アプリ同梱の App Intents メタデータを読み取り、Siri AI とショートカットの操作を試した。末尾追記は 3 つの文字サイズ設定で既存の段落スタイルと RTF のポイント値を保持した。部分置換はメモ内蔵の「検索と置換」で書式を保持できた。App Intents 経由の部分置換は実行できなかった。[macOS 27 の実験結果](docs/experiments/app-intents.md)

範囲外として、以下の行為は行っていない。

- メモ.appバイナリの逆コンパイル、逆アセンブル、class-dump、静的解析
- 実行中プロセスへのアタッチ、メモリダンプ、動的解析
- `NoteStore.sqlite` (`~/Library/Group Containers/group.com.apple.notes/`) の protobuf 直編集およびスキーマ解析
- iCloud 通信の復号と解析
- Apple Software 本体の改変、派生物作成、再配布

## 用語

本ドキュメント全体で繰り返し用いる用語を以下に定義する。

- **ラウンドトリップ**: 同一のメモに対して `get_body` で HTML を取得し、その HTML を `set_body` で書き戻し、再度 `get_body` で取得する一連の操作。前後の HTML の差分が、`set_body` が入力 HTML をどう正規化するかを直接表す。複数回繰り返した場合の各回を「0 回目 (初回取得)」「1 回目 (1 回目の書き戻し後)」「2 回目 (2 回目の書き戻し後)」のように呼ぶ。
- **不動点**: ある関数 `f` に対して `f(X) = X` を満たす入力 `X`。本調査では `set_body(get_body(X)) = get_body(X)` となる状態を指す。
- **観測用メモ**: 特定の HTML 入力に対する `set_body` の挙動を観測するために、スクリプトから投入するメモ (T18-T23)。コード上は `scripts/py/seed_t_probes.py` および `data/probes/` のように "probe" として参照される。
- **GUI 由来メモ**: メモ.appの GUI でユーザが手作業で作成したメモ (T01-T17b)。
- **合成メモ**: AppleScript の `make new note` で投入したメモ (S01-)。GUI 由来メモと比べて `body` の HTML 出力に系統的な差がある。

## ドキュメント構成

```
docs/
├── 01-facts.md            現在の事実集大成 (set_body が何をするか、何が保たれ何が失われるか)
├── 02-recipe.md           編集レシピライブラリの取扱説明書 (scripts/py/edit_recipe.py)
├── methods/
│   ├── environment.md     実行環境、バックアップ手順、ツールチェーン
│   └── test-notes.md      T01-T23 テストメモの作成手順
└── experiments/
    ├── app-intents.md            macOS 27 の末尾追記、新規作成、部分置換の実験
    ├── roundtrip.md              ラウンドトリップが不動点に収束するかの検証
    ├── minimal-edit.md           BeautifulSoup によるテキスト 1 ノード置換が他要素を変更しないかの検証
    ├── boundary.md               8 種の構造変更が意図通りに反映されるかの検証
    ├── paragraph-style-search.md 段落スタイルを生成する HTML 入力の網羅探索 (300 候補以上を試行)
    ├── api-surface.md            plaintext / attachments / make new attachment / Cmd+D 複製の挙動
    ├── font-size-measurement.md  T17a / T17b のフォントサイズの実測 (タイトル 20→24pt 等)
    ├── highlight-attempts.md     ハイライトの CSS 9 バリアントの試行と、いずれも再現に至らなかった結果
    ├── hyperlink-attempts.md     ハイパーリンクの新規作成可否とラウンドトリップ後の保持挙動
    ├── block-quote-attempts.md   ブロック引用の 6 バリアントの試行と、いずれも再現に至らなかった結果
    └── parser-quirks.md          パーサの個別挙動 (`<div>` ラッパーへの `<br>` 挿入、`<abbr title>` の `<u>` 化等)
```

AppleScript の調査結果と編集手順は、[HTML 書き戻しの挙動](docs/01-facts.md) と [編集レシピ](docs/02-recipe.md) を参照。Siri AI、ショートカット、メモ内蔵の「検索と置換」の結果は、[macOS 27 の実験記録](docs/experiments/app-intents.md) にまとめている。

## AppleScript による HTML 書き戻しの要点

GUI で作成されたメモに対して `body` API 経由で編集を加えると、多くの要素が不可逆に失われる。`body` API での編集が安全な対象は、画像、PDF、添付ファイル、ハイパーリンク、ハイライト、チェックリスト、ブロック引用、タイトル、見出し、小見出し段落のいずれも含まないメモに限られる。

HTML 入力経路から再現可能な段落スタイルは 2 種類に限られる。`<ul class="Apple-dash-list">` から得られるダッシュ付きリストと、`<tt>` / `<pre>` / `<code>` / `<kbd>` / `<samp>` のいずれかから得られる等幅段落である。

ハイパーリンクは、`<a href="...">` を含む HTML を `set_body` で投入することで GUI 上で機能するリンクを新規作成できる。ただし、その後のラウンドトリップで URL が失われるため、追加のみ可能な書き込み専用パスである。

詳細はすべて [`docs/01-facts.md`](docs/01-facts.md) に集約し、実用レシピの使い方は [`docs/02-recipe.md`](docs/02-recipe.md) を参照。

## リポジトリ構成

```
.
├── docs/             ドキュメント (上記参照)
├── scripts/
│   ├── jxa/          JXA (JavaScript for Automation) スクリプト群
│   └── py/           Python オーケストレーション (uv 管理)
├── pyproject.toml    uv プロジェクト定義
├── uv.lock           依存ロック (commit 対象)
└── data/
    ├── before/        ラウンドトリップ 0 回目の get_body 結果 [gitignored]
    ├── after/         ラウンドトリップ 1 回目および 2 回目の get_body 結果 [gitignored]
    ├── diffs/         各回間の diff [gitignored]
    ├── edit/          最小編集テストの結果 [gitignored]
    ├── boundary/      境界テストの結果 [gitignored]
    ├── class_probe/   段落スタイル class 名の探索結果 [gitignored]
    ├── heading_probe/ 見出し候補の探索結果 [gitignored]
    ├── multi/         ラウンドトリップ収束テストの結果 [gitignored]
    ├── runs/          実行サマリ JSON [gitignored]
    └── probes/        観測用メモおよび GUI 由来メモの get_body dump [committed]
        ├── HTMLTest/      作業フォルダ側
        └── HTMLTest-copy/ GUI 由来メモの原本側
```

## セットアップと実行手順

```bash
# 1. 依存セットアップ
uv sync

# 2. HTMLTest および HTMLTest copy フォルダの確認と作成
ACCOUNT=iCloud FOLDER=HTMLTest osascript -l JavaScript scripts/jxa/ensure_folder.js
ACCOUNT=iCloud FOLDER="HTMLTest copy" osascript -l JavaScript scripts/jxa/ensure_folder.js

# 3. テストメモの作成 (詳細は docs/methods/test-notes.md)
#    GUI 手作業: T01-T17b を HTMLTest copy で作成し、Cmd+A → Cmd+D で複製して HTMLTest にドラッグ
#    スクリプト投入: T18-T23 の観測用メモを HTMLTest に投入
uv run python scripts/py/seed_synthetic.py    # 合成メモ S01- を AppleScript で生成
uv run python scripts/py/seed_t_probes.py     # 観測用メモ T18-T23 を投入

# 4. ラウンドトリップテスト
uv run python scripts/py/roundtrip.py             # 全メモ
uv run python scripts/py/roundtrip.py --filter T  # 観測用メモおよび GUI 由来メモのみ

# 5. 編集前安全性チェック (必須)
uv run python scripts/py/edit_recipe.py safety MyNote

# 6. レシピを用いた編集 (詳細は docs/02-recipe.md)
uv run python scripts/py/edit_recipe.py replace T01-plain "First paragraph." "Replaced!"
uv run python scripts/py/edit_recipe.py color   T01-plain "Replaced" "#FF0000"
uv run python scripts/py/edit_recipe.py append-para T01-plain "新しい段落"
```

## 編集時の制約

`body` API 経由でメモを編集する際は、以下の制約を守る必要がある。

1. 編集前に必ず `check_safety` を実行する。画像または添付があれば編集を中止する。
2. ハイパーリンク、ハイライト、チェックリスト、タイトル / 見出し / 小見出し段落を含むことが既知のメモには触らない。これらは body HTML から検出できないため、`check_safety` も通過してしまう。
3. テスト中はメモ.appの表示を HTMLTest 以外のフォルダに切り替えるか、メモ.appを終了させる。
4. テスト中は iPhone および iPad で HTMLTest フォルダを開かない。iCloud 同期競合を避けるため。
5. スクリプトには iCloud アカウントの HTMLTest フォルダ外のメモを操作しないガードが組み込まれている。

## 環境

実行環境の詳細は [`docs/methods/environment.md`](docs/methods/environment.md) を参照。
