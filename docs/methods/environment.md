# 環境

`docs/01-facts.md` および `docs/experiments/*.md` が前提とする実行環境の記録。バージョンが変われば挙動が変わり得るため、追試する場合は環境の差分も併せて記録する。

## 実行環境

| 項目 | 値 | 確認方法 |
|---|---|---|
| macOS | 26.4.1 (Build 25E253) | About This Mac |
| メモ.app CFBundleShortVersionString | 4.13 | Notes → About Notes、または `defaults read /System/Applications/Notes.app/Contents/Info.plist CFBundleShortVersionString` |
| メモ.app CFBundleVersion | 3146.101.28 | 同上 |
| Notes Default Text Size | Medium | Notes → Settings → Default Text Size |
| 新規メモのデフォルトスタイル | タイトル | Notes → Settings → New notes start with: タイトル |
| Python | 3.12 (uv 管理。`.python-version` および `pyproject.toml` で固定) | `uv run python --version` |
| シェル | zsh | `echo $SHELL` |
| 調査開始日 | 2026-05-19 | — |

`Default Text Size` はタイトル / 見出し / 小見出し / 本文の実フォントサイズ (pt 値) に直接影響する。Medium 以外の設定で測定値を再現したい場合は `docs/experiments/font-size-measurement.md` 末尾の注意書きを参照。

## メモ.appのアカウントおよびフォルダ構成

iCloud アカウントに調査専用フォルダを 2 つ作成して実施する。

| フォルダ | 用途 |
|---|---|
| `HTMLTest copy` | GUI で作成した GUI 由来メモ (T01〜T17b) の原本。`set_body` を絶対に呼ばない (paragraph style 破壊のリスクがあるため) |
| `HTMLTest` | 作業用フォルダ。`HTMLTest copy` から Cmd+D で複製した作業コピーと、`seed_t_probes.py` で投入される観測用メモ (T18-T23) を置く |

詳細な作成手順は `docs/methods/test-notes.md` を参照。

スクリプトは `HTMLTest` フォルダ外のメモに一切触らないようガードされている (`scripts/py/notes.py` の `DEFAULT_ACCOUNT` および `DEFAULT_FOLDER` を参照)。本番メモで試したい場合はモジュールレベルで上書きする (`docs/02-recipe.md` の環境節を参照)。

### iCloud アカウントを使うことの影響

| 影響 | 対策 |
|---|---|
| `set_body` 後に同期処理が走り、`get_body` の結果が遅延あるいは揺らぐ | `set_body` の後に `time.sleep(1.5)` を入れる (`scripts/py/edit_recipe.py:DEFAULT_DELAY` を参照)。不安定なら各 edit recipe 関数の `delay` キーワード引数を延長する (例: `replace_unique_text("Note", "old", "new", delay=3.0)`) |
| 他デバイス (iPhone, iPad) に `HTMLTest` フォルダが同期される | 機能的には問題ない。気になる場合は他デバイス側で非表示にする |
| 同じメモに対して iCloud server 側の編集と競合する可能性がある | テスト中は他デバイスで `HTMLTest` を開かない |

## On My Mac アカウントを使わない理由

System Settings → Notes で「On My Mac」アカウントを有効化することを当初計画したが、これは GUI 操作が必要でありスクリプトから有効化できない。調査開始時の方針として、iCloud アカウントの `HTMLTest` フォルダで実施する形に変更した。

## バックアップ

ファイルシステムレベルのバックアップは TCC 制限により不可能である (macOS Transparency, Consent, and Control 保護)。

- 対象ディレクトリ: `~/Library/Group Containers/group.com.apple.notes/`
- 試行結果: Terminal および Claude Code からの `ls` / `du` / `cp` も、Finder 経由 (`osascript`) も、いずれも `Operation not permitted` (-8067) で失敗する
- 対応方法: Full Disk Access を Terminal に付与すれば可能だが、System Settings → Privacy & Security → Full Disk Access での手動操作が必要となる

### 代替の安全策

1. `HTMLTest` 系フォルダのみを操作する。スクリプトはガード実装により他のフォルダには触らない。
2. メモ.app内部の整合性管理に依存する。`set_body` は Apple Events API 経由の正規の入力であるため、内部データの整合性はメモ.app自身が維持する (内部表現には触らない)。
3. iCloud のバージョン履歴に依存する。iCloud Notes はサーバ側で履歴を保持しており、復元が可能である (保持期間に制限あり)。

万一に備えて、本格的なテストの前にメモ.appの「ファイル → メモを書き出す」で重要なメモを個別にバックアップすることを推奨する。

## 復元手順 (参考)

スクリプトがテストフォルダ内のメモを破壊した場合の復元手順:

1. iCloud.com にログインし、Notes から該当メモの履歴復元、または「最近削除した項目」から復元する。
2. ローカルキャッシュが壊れた場合は、メモ.appを終了し、`~/Library/Group Containers/group.com.apple.notes/` を削除してから、メモ.appを起動して iCloud から再ダウンロードする。

## ツールチェーン

### Python (uv 管理)

```bash
uv sync           # 依存セットアップ
uv run python scripts/py/notes.py list   # 動作確認
```

`pyproject.toml` および `uv.lock` をコミット対象とする。`uv.lock` をコミットすることで再現性を担保する (個人ルール、`MEMORY.md` を参照)。

### JXA (JavaScript for Automation)

macOS 標準のツールであり、追加インストールは不要である。

```bash
osascript -l JavaScript scripts/jxa/get_body.js
```

`scripts/jxa/` 以下に低レベルツール群が用意されている。

| スクリプト | 用途 |
|---|---|
| `ensure_folder.js` | `HTMLTest` フォルダの作成および存在確認 |
| `list_folders.js` / `list_notes.js` | フォルダおよびメモの一覧 |
| `get_body.js` / `set_body.js` / `create_note.js` / `delete_note.js` | メモの基本操作 |
| `add_attachment.js` | 単一添付の追加 (`Notes.make({new:'attachment', ...})` の実用版) |
| `probe_*.js` | 公開 API の探索用 (詳細は `docs/experiments/api-surface.md`) |

## 最小動作確認

```bash
uv sync
uv run python scripts/py/notes.py list | head
uv run python scripts/py/notes.py smoke     # h1 と body を持つメモを create_note → get_body → delete_note する
```

実行結果が `<div><b><span style="font-size: 24px">_smoke_test</span></b><br></div><div>hello world</div>` のような形で返れば成功である (`<h1>` が `<div><b><span style="font-size: 24px">` に正規化される)。
