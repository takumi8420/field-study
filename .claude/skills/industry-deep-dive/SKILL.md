---
name: industry-deep-dive
description: 業界地図の各業界を「常識レベルで語れる」水準まで深掘りし、Markdown ノート群＋静的HTMLサイト（業界理解の教科書）として本リポジトリに書き足すスキル。「○○業界を深掘りして」「○○業界を教えて／まとめて」「この業界のノートを書いて」「業界理解の教科書を作りたい」「前工程みたいに仕組みを解説して」「直近トピックも拾って」「用語集を作って」「まとめて5業界やって」のようなリクエスト、または業界名だけが投げられて学習意図が読み取れる場合に発動する。/industry-deep-dive で明示起動も可。1業界ずつ丁寧に深掘りするモードと、複数業界をサブエージェントで並列に書くモードの両方を持つ。ノートを書いたら必ずサイト生成と検証まで行う。
allowed-tools: Read, Write, Edit, Bash, Glob, Grep, WebSearch, WebFetch, Agent, AskUserQuestion
---

# 業界深掘り・解説スキル

業界地図に載る各業界を、**素人が読んで構造を語れるようになる**水準の教科書ノートにする。
出力先はこのリポジトリ。`*.md` を書き、`tools/build_site.py` で HTML 化して読む。

## 起動タイミング

- 「○○業界を深掘りして／教えて／まとめて」と業界名が示された時
- 「業界理解の教科書を作りたい」「網羅的にやりたい」と言われた時
- 既存ノートへの追記（「直近トピックも拾って」「用語集を作って」「原理を説明して」）
- 業界名だけが短く投げられ、学習目的が読み取れる時

## 前提：リポジトリの構造

```
index.html                    ← 生成物。直接編集しない
assets/                       ← 生成物
tools/build_site.py           ← *.md → *.html 変換＋一覧生成
tools/build_tree.py           ← industries.tsv からフォルダ雛形生成
tools/check_links.py          ← リンク切れ・体裁チェック
tools/industries.tsv          ← 業界マスタ（大分類 TAB 業界名）
NN_大分類/NN_業界名/README.md ← 手で書くのはここだけ
NN_大分類/NN_業界名/NN_〇〇.md ← 深掘りノート
```

**書くのは `*.md` だけ。`*.html` は必ず生成する（手書きしない）。**

## ワークフロー

### Step 1: 対象と粒度を決める

1. 対象業界のフォルダを `ls` で特定する（`NN_大分類/NN_業界名/`）
2. 無ければ `tools/industries.tsv` に追記し `python3 tools/build_tree.py` で雛形を作る
3. 既存ノートがあれば全部読み、**重複を書かない**。加筆か新規かを決める
4. 3業界以上をまとめて指示された場合は「並列モード」（後述）を提案する

### Step 2: 骨格を決める（最重要）

業界タイプごとに「仕組み」の切り口が違う。
[references/note-structure.md](references/note-structure.md) の**業界タイプ別の型**を必ず参照し、
その業界に合う 4〜7 本のノート構成を先に決めてからリサーチに入る。

最低限そろえる5本：

| ノート | 役割 |
| --- | --- |
| `README.md` | 概要10章＋ノート索引＋状態・更新日 |
| `01_サプライチェーンと業界構造.md`（相当） | 誰が何を作り誰に売るか、プレイヤー類型、利益の在処 |
| `02_〜.md`（業界固有の仕組み） | 工程／資金の流れ／店舗経済 など、その業界の中核メカニズム |
| `0N_直近トピック_YYYY.md` | Web検索で調べた最新動向。**出典URL必須** |
| `0N_用語集.md` | 用語索引。既存の用語集があるなら追記で足りる |

### Step 3: リサーチ

[references/research.md](references/research.md) の手順に従う。**Web検索は毎回必ず行う**。

- 基礎知識は自分の知識で書いてよいが、**数値・シェア・時期は必ず年を添える**
- 直近動向は WebSearch で最低3〜5クエリ。一次情報（IR・官公庁・業界団体）を優先
- 推計・報道ベースの数字は「〜と報じられる」「推計」と明示し、鵜呑みにしない

### Step 4: 執筆

[references/writing-style.md](references/writing-style.md) の作法に従う。要点：

- **結論を先に、理由を1行で**。「何が起きるか」でなく「なぜそうなるか」を書く
- 表とASCIIの図解を使う。文章の羅列にしない
- 専門用語は初出で必ず噛み砕く
- 各ノート末尾に「用語メモ」
- 読者は**その業界を知らない人**。前提知識を要求しない

### Step 5: 相互リンク

- README のノート索引表を更新する
- 関連業界・用語集へ相対リンクを張る（`../../NN_大分類/NN_業界名/README.md`）
- 学習が済んだら README の `- 状態: todo` を `done` に、`- 更新日:` を当日に

### Step 6: 生成と検証（必須）

```bash
python3 tools/build_site.py && python3 tools/check_links.py
```

`check_links.py` が NG を出したら直してから報告する。詳細は
[references/build-and-verify.md](references/build-and-verify.md)。

### Step 7: 報告

- 何をどこに書いたかをファイルリンクで示す
- **内容の要点を3〜5行で説明する**（ファイル名の羅列で終わらせない）
- 出典URLを提示する
- 次に深掘りすべき隣接業界を1つ提案する

## 並列モード（複数業界を一括）

3業界以上をまとめて指示された時のみ使う。

1. 対象業界ごとに `Agent`（subagent_type: `general-purpose`）を1つずつ、同一メッセージで起動する
2. 各エージェントへのプロンプトには必ず以下を含める：
   - リポジトリのルートパスと対象フォルダ
   - 「`.claude/skills/industry-deep-dive/references/` を最初に全部読んでから書くこと」
   - 「`*.md` のみ書き、`build_site.py` は実行しないこと」（生成は親で1回だけ）
   - 最低5本のノート構成と、Web検索で直近トピックを必ず入れること
3. 全エージェント完了後、**親セッションで1回だけ** `build_site.py` と `check_links.py` を実行
4. 文体・粒度のばらつきを親が点検し、README の索引を整える

## リファレンス

| ファイル | 内容 |
| --- | --- |
| [references/note-structure.md](references/note-structure.md) | ノート構成の型、README 10章テンプレ、業界タイプ別の切り口 |
| [references/writing-style.md](references/writing-style.md) | 文体・図解・表の作法、品質チェックリスト |
| [references/research.md](references/research.md) | 調査手順、検索クエリの型、出典の扱い、数値の書き方 |
| [references/build-and-verify.md](references/build-and-verify.md) | サイト生成・検証・状態管理・業界追加の手順 |
| [references/example-semiconductor.md](references/example-semiconductor.md) | 実例：半導体10本立ての構成と、そこから学べる型 |

## アンチパターン

- ❌ `*.html` を手で書く／編集する（必ず `build_site.py` で生成）
- ❌ 生成・検証をせずに「できました」と報告する
- ❌ 用語を説明せずに使う（EUV、CoWoS、CAGR、粗利率…）
- ❌ 数値に年・出典を付けない、古い数字を最新のように書く
- ❌ 1ファイルに全部詰め込む（1ノート=1テーマ。長くなったら分割）
- ❌ 既存ノートと重複する内容を別ファイルで書く（先に読む）
- ❌ 箇条書きだけで構造を説明する（表と図を使う）
- ❌ 断定できないことを断定する（推計・報道は明示する）
