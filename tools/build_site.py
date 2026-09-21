#!/usr/bin/env python3
"""Markdown ノート群から、ブラウザで読める静的サイトを生成する。

 - 各 .md と同じ場所に .html を出力
 - 大分類ごとの index.html とルートの index.html（ダッシュボード）を出力
 - assets/nav.js（全ページ共通の検索インデックス）を出力
依存ライブラリなし。`python3 tools/build_site.py` で再生成する。
"""
import html
import json
import pathlib
import re
import sys
from datetime import date

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import mdlite  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAT_RE = re.compile(r"^\d\d_")
META_RE = re.compile(r"^- (大分類|状態|更新日):\s*(.*)$", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+(.*)$", re.MULTILINE)
E = lambda s: html.escape(str(s), quote=True)  # noqa: E731


# ── 走査 ──────────────────────────────────────────────
def scan() -> list[dict]:
    cats = []
    for cdir in sorted(p for p in ROOT.iterdir() if p.is_dir() and CAT_RE.match(p.name)):
        cat = {"name": cdir.name.split("_", 1)[1], "dir": cdir.name, "items": []}
        for idir in sorted(p for p in cdir.iterdir() if p.is_dir()):
            mds = sorted(idir.glob("*.md"), key=lambda p: (p.name != "README.md", p.name))
            notes = []
            state = "todo"
            updated = ""
            for md in mds:
                raw = md.read_text(encoding="utf-8")
                m = TITLE_RE.search(raw)
                title = m.group(1).strip() if m else md.stem
                if md.name == "README.md":
                    for key, val in META_RE.findall(raw):
                        if key == "状態":
                            state = val.split()[0] if val.split() else "todo"
                        elif key == "更新日":
                            updated = val.strip()
                notes.append(
                    {
                        "md": md,
                        "file": md.stem + ".html",
                        "title": title,
                        "label": "概要" if md.name == "README.md" else re.sub(r"^\d\d_", "", md.stem),
                        "rel": f"{cdir.name}/{idir.name}/{md.stem}.html",
                    }
                )
            cat["items"].append(
                {
                    "name": idir.name.split("_", 1)[1],
                    "dir": idir.name,
                    "path": f"{cdir.name}/{idir.name}",
                    "rel": f"{cdir.name}/{idir.name}/README.html",
                    "state": state,
                    "updated": updated,
                    "notes": notes,
                }
            )
        cats.append(cat)
    return cats


# ── 共通パーツ ────────────────────────────────────────
def shell(title: str, root: str, crumb: str, body: str, extra_class: str = "") -> str:
    return f"""<!DOCTYPE html>
<html lang="ja" data-root="{E(root)}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{E(title)}</title>
<link rel="stylesheet" href="{E(root)}assets/style.css">
</head>
<body class="{extra_class}">
<div class="bar"><div class="bar-in">
  <a class="brand" href="{E(root)}index.html">業界地図ノート</a>
  <nav class="crumb">{crumb}</nav>
  <div class="bar-right">
    <div class="search"><input type="search" id="q" placeholder="業界を検索  /" autocomplete="off"></div>
    <button class="icon-btn" data-theme-toggle title="ライト / ダーク切替">◐</button>
  </div>
</div></div>
{body}
<script src="{E(root)}assets/nav.js"></script>
<script src="{E(root)}assets/app.js"></script>
</body>
</html>
"""


def crumbs(parts: list[tuple[str, str | None]]) -> str:
    out = []
    for i, (label, href) in enumerate(parts):
        if i:
            out.append("<span>›</span>")
        out.append(f'<span><a href="{E(href)}">{E(label)}</a></span>' if href else f"<span>{E(label)}</span>")
    return "".join(out)


def sidebar(cats, cur_cat, cur_item, cur_file, root) -> str:
    out = ['<nav class="side"><h3>大分類</h3><ul>']
    for c in cats:
        on = " on" if c is cur_cat else ""
        out.append(
            f'<li><a class="cat{on}" href="{E(root + c["dir"])}/index.html">{E(c["name"])}'
            f'</a>'
        )
        if c is cur_cat:
            out.append('<ul class="sub">')
            for it in c["items"]:
                ion = " on" if it is cur_item else ""
                out.append(f'<li><a class="{ion.strip()}" href="{E(root + it["rel"])}">{E(it["name"])}</a>')
                if it is cur_item and len(it["notes"]) > 1:
                    out.append('<ul class="sub note-list">')
                    for nt in it["notes"]:
                        non = " on" if nt["file"] == cur_file else ""
                        out.append(f'<li><a class="{non.strip()}" href="{E(nt["file"])}">{E(nt["label"])}</a></li>')
                    out.append("</ul>")
                out.append("</li>")
            out.append("</ul>")
        out.append("</li>")
    out.append("</ul></nav>")
    return "".join(out)


def toc_html(toc) -> str:
    if len(toc) < 2:
        return ""
    links = "".join(
        f'<a class="lv{lv}" href="#{E(anchor)}">{E(text)}</a>' for lv, text, anchor in toc
    )
    return f'<aside class="toc"><h3>目次</h3>{links}</aside>'


def cards(items, prefix="") -> str:
    out = ['<ul class="grid">']
    for it in items:
        cls = "card done" if it["state"] == "done" else "card"
        notes = ""
        extra = [n for n in it["notes"] if n["label"] != "概要"]
        if extra:
            notes = '<div class="notes">' + "".join(
                f'<a class="note" href="{E(prefix + n["rel"])}">{E(n["label"])}</a>'
                for n in extra
            ) + "</div>"
        out.append(
            f'<li class="{cls}"><a class="main" href="{E(prefix + it["rel"])}">'
            f'<span class="dot"></span>{E(it["name"])}</a>{notes}</li>'
        )
    out.append("</ul>")
    return "".join(out)


def progress(done: int, total: int) -> str:
    pct = round(done / total * 100) if total else 0
    return (
        f'<div class="stat"><b>{done}<span style="font-size:13px;color:var(--muted)"> / {total}</span></b>'
        f'<span>学習済み</span></div><div class="bar-line"><i style="width:{pct}%"></i></div>'
    )


# ── 出力 ──────────────────────────────────────────────
def resolve_terms(
    terms: list[tuple[str, str]], definitions: dict[str, str]
) -> list[tuple[str, str]]:
    """ページ内用語を重複排除し、同じ業界の定義で補完する。"""
    resolved = []
    seen = set()
    for label, description in terms:
        if not label or label in seen:
            continue
        seen.add(label)
        resolved.append((label, description or definitions.get(label, "")))
    return resolved


def page_glossary(terms: list[tuple[str, str]], definitions: dict[str, str]) -> str:
    """各ページ上部に共通の単語集を表示する。"""
    resolved = resolve_terms(terms, definitions)

    count = len(resolved)
    if not resolved:
        content = '<p class="page-glossary-empty">このページには、まだ用語が登録されていません。</p>'
    else:
        chips = []
        for label, description in resolved:
            if description:
                chips.append(
                    f'<span class="term-chip has-tip" tabindex="0" '
                    f'data-tooltip="{E(description)}" aria-label="{E(label + "：" + description)}">{E(label)}</span>'
                )
            else:
                chips.append(f'<span class="term-chip">{E(label)}</span>')
        content = '<div class="page-glossary-chips">' + "".join(chips) + "</div>"

    return (
        '<details class="page-glossary">'
        '<summary><span class="page-glossary-summary-main">'
        '<span class="page-glossary-icon" aria-hidden="true">あ</span>'
        '<span class="page-glossary-copy"><span class="page-glossary-label">このページの単語集</span>'
        '<span class="page-glossary-hint">用語に触れると意味を確認できます</span></span></span>'
        f'<span class="page-glossary-count">{count}語</span></summary>{content}</details>'
    )


def quiz_plain(text: str) -> str:
    """クイズの回答観点用にMarkdown装飾を取り除く。"""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    text = re.sub(r"<[^>]+>", "", text)
    return " ".join(text.strip(" #>*-・\t").split())


def section_points(body: str) -> list[str]:
    """章の本文から、口頭回答と照合するための主要観点を最大4件抽出する。"""
    body = re.sub(r"```.*?```", "", body, flags=re.DOTALL)
    candidates: list[str] = []
    for block in re.split(r"\n\s*\n", body):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if all(line.startswith("|") for line in lines):
            rows = [line.strip("|").split("|") for line in lines]
            rows = [row for row in rows if not all(re.fullmatch(r"[\s:|-]+", cell) for cell in row)]
            for row in rows[1:4]:  # 見出し行を除き、代表的な行を回答観点にする
                cells = [quiz_plain(cell) for cell in row if quiz_plain(cell)]
                if cells:
                    candidates.append("：".join(cells[:3]))
            continue
        if any(re.match(r"^(?:[-*]|\d+[.)])\s+", line) for line in lines):
            items: list[str] = []
            current = ""
            for line in lines:
                item = re.match(r"^(?:[-*]|\d+[.)])\s+(.+)$", line)
                if item:
                    if current:
                        items.append(current)
                    current = item.group(1)
                elif current:
                    current += " " + line
            if current:
                items.append(current)
            candidates.extend(quiz_plain(item) for item in items[:5])
            continue
        text = quiz_plain(" ".join(re.sub(r"^>\s?", "", line) for line in lines))
        if text and not text.startswith(("詳細は", "参考：", "出典：")):
            candidates.append(text)

    points: list[str] = []
    for candidate in candidates:
        candidate = candidate.strip()
        if len(candidate) < 12 or candidate in points or candidate.endswith(("：", ":")):
            continue
        points.append(candidate[:220] + ("…" if len(candidate) > 220 else ""))
        if len(points) == 4:
            break
    return points


def business_question(title: str, heading: str) -> str:
    """標準的な章名を、ビジネス会話向けの説明問題へ変換する。"""
    label = re.sub(r"^\d+[.．]\s*", "", quiz_plain(heading))
    patterns = [
        (("全体像", "まとめ"), f'「{title}」の章「{label}」を30秒で要約してください。結論だけでなく、重要な因果関係も含めてください。'),
        (("定義", "範囲"), f'「{title}」とは何を指しますか。含まれる製品・技術・企業群を具体的に挙げ、隣接領域との違いも説明してください。'),
        (("市場規模", "成長性", "市場の波"), f'「{title}」の「{label}」で示された市場は、何によって拡大・縮小しますか。数字を見る際に、対象範囲や推計差へ注意すべき理由も説明してください。'),
        (("バリューチェーン", "サプライチェーン", "業界構造"), f'「{title}」の「{label}」では、誰が誰に何を売っていますか。利益・交渉力・ボトルネックがどこに集まるかも説明してください。'),
        (("プレイヤー", "競争構図", "シェア"), f'「{title}」の「{label}」に登場する企業を役割別に挙げ、各社の優位性・依存関係・競争軸を説明してください。'),
        (("収益モデル", "コスト構造", "儲け方", "経済性"), f'「{title}」の「{label}」について、誰から何の対価を受け取って稼ぐのか、売上と利益率を左右する主要コストは何かを説明してください。'),
        (("競争要因", "KSF", "参入障壁"), f'「{title}」の「{label}」について、顧客に選ばれる条件と、その条件が新規参入を難しくする理由を説明してください。'),
        (("規制", "法制度", "政策"), f'「{title}」の「{label}」で扱う規制・制度は、参入、商用化、採算性にどう影響しますか。事業機会と制約の両面から説明してください。'),
        (("トピック", "トレンド", "現在地"), f'「{title}」の「{label}」で何が変わっていますか。有利になる企業・不利になる企業と、収益への影響を説明してください。'),
        (("リスク", "制約"), f'「{title}」における「{label}」は、どのようなリスクですか。問題が起きてから事業・業績へ波及する経路を説明してください。'),
        (("仕組み", "原理", "なぜ", "作り方", "製造"), f'「{title}」における「{label}」は、どのような仕組みですか。そうなる理由と、収益・競争上の意味を説明してください。'),
    ]
    for words, question in patterns:
        if any(word in label for word in words):
            return question
    return f'「{title}」における「{label}」について、何が起きているか、なぜ起きるか、企業の収益や競争へどう影響するかを説明してください。'


def business_quiz_questions(raw: str, title: str) -> list[dict]:
    """ページの導入と主要章から、ビジネス理解を問う記述式問題を作る。"""
    matches = list(re.finditer(r"^##\s+(.+)$", raw, re.MULTILINE))
    questions: list[dict] = []
    used_questions: set[str] = set()

    intro = raw[: matches[0].start()] if matches else raw
    intro_points = section_points(intro)
    if intro_points:
        intro_question = f'「{title}」とは何か、ビジネス上なぜ重要なのかを30秒で説明してください。'
        questions.append({"question": intro_question, "points": intro_points})
        used_questions.add(intro_question)

    skip_words = ("用語", "単語", "参考", "関連", "読み方", "このフォルダの読み方")
    for index, match in enumerate(matches):
        heading = quiz_plain(match.group(1))
        if any(word in heading for word in skip_words):
            continue
        end = matches[index + 1].start() if index + 1 < len(matches) else len(raw)
        points = section_points(raw[match.end() : end])
        if points:
            question = business_question(title, heading)
            if question in used_questions:
                question = question.rstrip("。") + f'。特に章「{heading}」で扱う内容を軸に説明してください。'
            if question in used_questions:
                question = question.rstrip("。") + f'（第{index + 1}章）。'
            questions.append({"question": question, "points": points})
            used_questions.add(question)
    return questions


def page_quiz(
    raw: str,
    title: str,
    terms: list[tuple[str, str]],
    definitions: dict[str, str],
    page_key: str,
) -> str:
    """主要章から、ビジネスの場で説明するための想起練習を生成する。"""
    has_learning_content = any(description for _, description in resolve_terms(terms, definitions))
    questions = business_quiz_questions(raw, title) if has_learning_content else []
    count = len(questions)
    payload = json.dumps(questions, ensure_ascii=False).replace("</", "<\\/")

    if not questions:
        return (
            '<section class="page-quiz is-empty">'
            '<div class="quiz-heading"><span class="quiz-icon" aria-hidden="true">?</span>'
            '<div><span class="quiz-eyebrow">RETRIEVAL PRACTICE</span>'
            '<h2>このページの理解度クイズ</h2></div></div>'
            '<p class="quiz-empty">本文が登録されると、ここに背景理解を確認するクイズが自動生成されます。</p>'
            '</section>'
        )

    return (
        f'<section class="page-quiz" data-quiz-key="{E(page_key)}">'
        '<div class="quiz-heading"><span class="quiz-icon" aria-hidden="true">?</span>'
        '<div><span class="quiz-eyebrow">RETRIEVAL PRACTICE</span>'
        '<h2>このページの理解度クイズ</h2></div>'
        f'<span class="quiz-count">全{count}問</span></div>'
        '<div class="quiz-intro" data-quiz-intro>'
        '<p>各章の背景・因果関係・ビジネス上の意味を、自分の言葉で説明する練習です。声に出して答えてから回答の観点を開いてください。</p>'
        '<div class="quiz-intro-actions"><button class="quiz-button primary" type="button" data-quiz-start>クイズを始める</button>'
        '<span class="quiz-best" data-quiz-best></span></div></div>'
        '<div class="quiz-run" data-quiz-run hidden>'
        '<div class="quiz-progress-row"><span data-quiz-progress-text></span><span data-quiz-score></span></div>'
        '<div class="quiz-progress"><i data-quiz-progress-bar></i></div>'
        '<span class="quiz-prompt-label">BUSINESS DISCUSSION</span>'
        '<p class="quiz-question" data-quiz-question></p>'
        '<button class="quiz-button quiz-reveal" type="button" data-quiz-reveal>回答の観点を見る</button>'
        '<div class="quiz-feedback" data-quiz-feedback hidden aria-live="polite"></div>'
        '<div class="quiz-self-rating" data-quiz-rating hidden>'
        '<span>自分の言葉で説明できましたか？</span>'
        '<button class="quiz-button primary" type="button" data-quiz-known>説明できた</button>'
        '<button class="quiz-button" type="button" data-quiz-review>復習する</button></div>'
        '<button class="quiz-button primary quiz-next" type="button" data-quiz-next hidden>次の問題へ</button>'
        '</div>'
        '<div class="quiz-result" data-quiz-result hidden aria-live="polite">'
        '<span class="quiz-result-label">RESULT</span><strong data-quiz-result-score></strong>'
        '<p data-quiz-result-message></p><div class="quiz-result-actions">'
        '<button class="quiz-button primary" type="button" data-quiz-retry-missed>復習する問題に再挑戦</button>'
        '<button class="quiz-button" type="button" data-quiz-retry-all>全問もう一度</button>'
        '</div></div>'
        f'<script class="quiz-data" type="application/json">{payload}</script></section>'
    )


def term_keys(label: str) -> list[str]:
    """表記揺れ補完用。末尾の英語名・別名の括弧を外したキーも返す。"""
    base = re.sub(r"\s*[（(][^）)]*[）)]\s*$", "", label).strip()
    return [label] if not base or base == label else [label, base]


def write_note(cats, cat, item, note, flat, definitions, root="../../") -> None:
    raw = note["md"].read_text(encoding="utf-8")
    raw = TITLE_RE.sub("", raw, count=1)
    meta = dict(META_RE.findall(raw))
    raw = "\n".join(l for l in raw.split("\n") if not META_RE.match(l))
    body_html, toc, terms = mdlite.render(raw)

    chips = []
    state = meta.get("状態", item["state"]).split()[0] if meta.get("状態", item["state"]) else "todo"
    if note["label"] == "概要":
        chips.append(f'<span class="chip {E(state)}">{"学習済み" if state == "done" else "未着手"}</span>')
        if meta.get("更新日", "").strip():
            chips.append(f'<span class="chip">更新 {E(meta["更新日"].strip())}</span>')
    chips.append(f'<span class="chip">{E(cat["name"])}</span>')
    if note["label"] != "概要":
        chips.append(f'<span class="chip">{E(item["name"])}</span>')

    i = flat.index(note["rel"])
    pager = []
    if i > 0:
        prev = ROOT_PAGES[flat[i - 1]]
        pager.append(
            f'<a class="prev" href="{E(root + flat[i - 1])}"><span class="lbl">← 前</span>{E(prev)}</a>'
        )
    if i + 1 < len(flat):
        nxt = ROOT_PAGES[flat[i + 1]]
        pager.append(
            f'<a class="next" href="{E(root + flat[i + 1])}"><span class="lbl">次 →</span>{E(nxt)}</a>'
        )

    toc_block = toc_html(toc)
    layout_cls = "layout" if toc_block else "layout no-toc"
    body = f"""<div class="{layout_cls}">
{sidebar(cats, cat, item, note["file"], root)}
<main class="doc">
  <div class="doc-head"><h1>{E(note["title"])}</h1><div class="chips">{"".join(chips)}</div></div>
  <div class="prose">{page_glossary(terms, definitions)}{body_html}{page_quiz(raw, note["title"], terms, definitions, note["rel"])}</div>
  <div class="pager">{"".join(pager)}</div>
</main>
{toc_block}
</div>"""
    crumb = crumbs(
        [
            ("ホーム", root + "index.html"),
            (cat["name"], root + cat["dir"] + "/index.html"),
            (item["name"], root + item["rel"] if note["label"] != "概要" else None),
        ]
        + ([(note["label"], None)] if note["label"] != "概要" else [])
    )
    out = note["md"].with_suffix(".html")
    out.write_text(shell(note["title"], root, crumb, body), encoding="utf-8")


def write_category(cats, cat) -> None:
    root = "../"
    done = sum(1 for i in cat["items"] if i["state"] == "done")
    body = f"""<div class="hero">
  <h1>{E(cat["name"])}</h1>
  <p>{len(cat["items"])} 業界。カードを開くと概要ノート、タグ付きリンクは個別ノートです。</p>
  <div class="stats">{progress(done, len(cat["items"]))}</div>
</div>
<div class="layout wide">{cards(cat["items"], prefix=root)}</div>
<footer class="site">再生成: <code>python3 tools/build_site.py</code></footer>"""
    (ROOT / cat["dir"] / "index.html").write_text(
        shell(cat["name"], root, crumbs([("ホーム", root + "index.html"), (cat["name"], None)]), body),
        encoding="utf-8",
    )


def write_index(cats) -> None:
    total = sum(len(c["items"]) for c in cats)
    done = sum(1 for c in cats for i in c["items"] if i["state"] == "done")
    notes = sum(len(i["notes"]) for c in cats for i in c["items"])
    secs = []
    for c in cats:
        cdone = sum(1 for i in c["items"] if i["state"] == "done")
        secs.append(
            f'<section class="cat-sec"><div class="cat-head">'
            f'<h2><a href="{E(c["dir"])}/index.html">{E(c["name"])}</a></h2>'
            f'<span class="count">{cdone}/{len(c["items"])}</span></div>{cards(c["items"])}</section>'
        )
    body = f"""<div class="hero">
  <h1>業界地図ノート</h1>
  <p>業界地図の各業界について、常識レベルの知識を1業界1フォルダで貯めていくノート。
     検索は右上（<code>/</code> キー）から。</p>
  <div class="stats">
    <div class="stat"><b>{len(cats)}</b><span>大分類</span></div>
    <div class="stat"><b>{total}</b><span>業界</span></div>
    <div class="stat"><b>{notes}</b><span>ノート</span></div>
    {progress(done, total)}
  </div>
</div>
<div class="layout wide">{"".join(secs)}</div>
<footer class="site">
  ノート本体は各フォルダの <code>*.md</code>。編集後に <code>python3 tools/build_site.py</code> で再生成。
  業界の追加は <code>tools/industries.tsv</code> → <code>python3 tools/build_tree.py</code>。
  最終生成: {date.today().isoformat()}
</footer>"""
    (ROOT / "index.html").write_text(
        shell("業界地図ノート", "", crumbs([("すべての業界", None)]), body), encoding="utf-8"
    )


def write_nav(cats) -> None:
    """検索インデックス。業界そのものに加えて、個別ノートも引けるようにする。"""
    data = []
    for c in cats:
        for i in c["items"]:
            data.append({"n": i["name"], "c": c["name"], "p": i["rel"]})
            for nt in i["notes"]:
                if nt["label"] == "概要":
                    continue
                data.append({"n": nt["label"], "c": i["name"], "p": nt["rel"]})
    (ROOT / "assets" / "nav.js").write_text(
        "var NAV = " + json.dumps(data, ensure_ascii=False) + ";\n", encoding="utf-8"
    )


ROOT_PAGES: dict[str, str] = {}


def main() -> int:
    cats = scan()
    flat = [n["rel"] for c in cats for i in c["items"] for n in i["notes"]]
    definitions: dict[str, str] = {}
    definitions_by_item: dict[str, dict[str, str]] = {}
    for c in cats:
        for i in c["items"]:
            local_definitions: dict[str, str] = {}
            for n in i["notes"]:
                raw = n["md"].read_text(encoding="utf-8")
                _, _, terms = mdlite.render(raw)
                for label, description in terms:
                    if description:
                        for key in term_keys(label):
                            definitions.setdefault(key, description)
                            local_definitions.setdefault(key, description)
            definitions_by_item[i["path"]] = local_definitions
    for c in cats:
        for i in c["items"]:
            for n in i["notes"]:
                ROOT_PAGES[n["rel"]] = n["title"]
    pages = 0
    for c in cats:
        for i in c["items"]:
            for n in i["notes"]:
                page_definitions = {**definitions, **definitions_by_item[i["path"]]}
                write_note(cats, c, i, n, flat, page_definitions)
                pages += 1
        write_category(cats, c)
    write_index(cats)
    write_nav(cats)
    print(f"generated: {pages} note pages + {len(cats)} category pages + index.html")
    return 0


if __name__ == "__main__":
    sys.exit(main())
