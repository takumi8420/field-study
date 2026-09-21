# 生成・検証・運用の手順

すべてリポジトリのルートで実行する。

## 1. サイト生成（ノートを書いたら必ず実行）

```bash
python3 tools/build_site.py
```

- `*.md` → 同じ場所に `*.html` を生成
- 大分類ごとの `index.html`、ルートの `index.html`、`assets/nav.js`（検索インデックス）を更新
- **`*.html` は生成物。手で編集しない**

## 2. 検証

```bash
python3 tools/check_links.py
```

チェック内容：

- HTML の内部リンク切れ
- Markdown 内の `.md` 相対リンクの実在
- 各業界フォルダに README.md があるか
- README に `- 状態:` 行があるか
- 各ノートに H1 見出しがあるか

NG が出たら直してから再実行する。**OK を確認してから報告する**。

## 3. 業界を新規に追加する

```bash
# tools/industries.tsv に「大分類<TAB>業界名」を追記してから
python3 tools/build_tree.py && python3 tools/build_site.py
```

`build_tree.py` は既存 README を上書きしない（追記内容は保護される）。

## 4. 進捗の管理

- README の `- 状態: todo` → `done` にすると、一覧の学習済みカウントとカードの色に反映される
- `- 更新日: YYYY-MM-DD` も更新する
- 「途中まで書いた」状態は `todo` のままにしておく

## 5. ブラウザで確認する

- `index.html` を直接開く（file:// でも CSS/JS は動く）
- ローカルサーバーで見る場合：`python3 -m http.server 8765`
  （`.claude/launch.json` に `notes` として登録済み）
- 確認したいのは、表の崩れ・コードブロックの折り返し・目次の見出し拾い

## 6. サイト側の仕組み（必要なときだけ読む）

| ファイル | 役割 |
| --- | --- |
| `tools/mdlite.py` | 依存ゼロの Markdown レンダラ。見出し・表・リスト・引用・コード・リンクに対応 |
| `tools/build_site.py` | 走査してページ生成。README の `- 状態:` を読んで進捗に反映 |
| `assets/style.css` | 共通スタイル（3カラム、ライト/ダーク、レスポンシブ） |
| `assets/app.js` | 検索・テーマ切替・目次ハイライト |

Markdown の記法で表示が崩れる場合は `tools/mdlite.py` の対応範囲を確認する。
対応外の記法（脚注、定義リスト、HTML直書き等）は使わない。

## 7. トラブル時

| 症状 | 対処 |
| --- | --- |
| ノートがサイトに出ない | `NN_大分類/NN_業界名/` の直下に置かれているか確認。階層が深いと拾われない |
| 検索に出ない | `build_site.py` を再実行（`assets/nav.js` が再生成される） |
| リンク切れ | `.md` のまま書いているか確認（`.html` と書くと変換されない） |
| 表が崩れる | セル内の `|` をエスケープするか表現を変える |
