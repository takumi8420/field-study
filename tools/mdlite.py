#!/usr/bin/env python3
"""依存ライブラリなしの軽量 Markdown レンダラ。
このノート群で使う記法（見出し・表・リスト・引用・コードブロック・リンク・強調・用語チップ）に対応する。"""
import html
import re

_FENCE = re.compile(r"^```(\w*)\s*$")
_HEAD = re.compile(r"^(#{1,6})\s+(.*)$")
_HR = re.compile(r"^(-{3,}|\*{3,})\s*$")
_LI = re.compile(r"^(\s*)([-*]|\d+[.)])\s+(.*)$")
_QUOTE = re.compile(r"^>\s?(.*)$")
_TABLE_SEP = re.compile(r"^\s*\|?[\s:|-]+\|[\s:|-]*$")
_COMMENT = re.compile(r"<!--.*?-->", re.DOTALL)


def _link(m: re.Match) -> str:
    text, href = m.group(1), m.group(2)
    if not re.match(r"^[a-z]+://|^#|^mailto:", href):
        href = re.sub(r"\.md(#|$)", r".html\1", href)
    return f'<a href="{html.escape(href, quote=True)}">{text}</a>'


def _term_chip(m: re.Match) -> str:
    """[[用語]] / [[用語|説明]] を学習用チップに変換する。"""
    content = m.group(1)
    if "|" not in content:
        return f'<span class="term-chip">{content.strip()}</span>'

    label, description = (part.strip() for part in content.split("|", 1))
    if not description:
        return f'<span class="term-chip">{label}</span>'

    # inline() ですでに本文を HTML エスケープしている。属性境界になる引用符だけ追加で保護する。
    attr = description.replace('"', "&quot;")
    aria = f"{label}：{description}".replace('"', "&quot;")
    return (
        f'<span class="term-chip has-tip" tabindex="0" '
        f'data-tooltip="{attr}" aria-label="{aria}">{label}</span>'
    )


def _plain_text(text: str) -> str:
    """ツールチップ用に、短い Markdown から装飾とリンク先URLを除く。"""
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\[\[([^\]|]+)(?:\|[^\]]*)?\]\]", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)
    text = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"\1", text)
    return " ".join(text.split())


def _glossary_chip(label: str, description: str) -> str:
    """用語集テーブルの1行目を、隣の説明を持つチップにする。"""
    plain_label = _plain_text(label)
    plain_description = _plain_text(description)
    if not plain_label or not plain_description or "[[" in label:
        return inline(label)
    attr = html.escape(plain_description, quote=True)
    aria = html.escape(f"{plain_label}：{plain_description}", quote=True)
    return (
        f'<span class="term-chip has-tip" tabindex="0" '
        f'data-tooltip="{attr}" aria-label="{aria}">{inline(label)}</span>'
    )


def inline(text: str) -> str:
    codes: list[str] = []

    def stash(m: re.Match) -> str:
        codes.append(m.group(1))
        return f"\x00{len(codes) - 1}\x00"

    text = re.sub(r"`([^`]+)`", stash, text)
    text = html.escape(text, quote=False)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", _link, text)
    text = re.sub(r"\[\[([^\[\]\n]+)\]\]", _term_chip, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"(?<![\*\w])\*([^*\n]+)\*(?!\*)", r"<em>\1</em>", text)
    text = re.sub(
        r"\x00(\d+)\x00",
        lambda m: "<code>" + html.escape(codes[int(m.group(1))]) + "</code>",
        text,
    )
    return text


def _cells(line: str) -> list[str]:
    line = line.strip()
    if line.startswith("|"):
        line = line[1:]
    if line.endswith("|"):
        line = line[:-1]
    return [c.strip() for c in line.split("|")]


def render(md: str) -> tuple[str, list[tuple[int, str, str]], list[tuple[str, str]]]:
    """(html, toc, terms) を返す。terms はページ内の (用語, 説明) のリスト。"""
    md = _COMMENT.sub("", md)
    lines = md.replace("\r\n", "\n").split("\n")
    out: list[str] = []
    toc: list[tuple[int, str, str]] = []
    terms: list[tuple[str, str]] = []
    seen_terms: set[str] = set()

    def add_term(label: str, description: str = "") -> None:
        label = _plain_text(label).strip(" ・、。:：")
        description = _plain_text(description).strip()
        if label and label not in seen_terms:
            seen_terms.add(label)
            terms.append((label, description))

    for explicit in re.finditer(r"\[\[([^\]|]+)\|([^\]]+)\]\]", md):
        add_term(explicit.group(1), explicit.group(2))

    i = 0
    hid = 0
    n = len(lines)
    in_glossary = False

    while i < n:
        line = lines[i]

        # コードブロック
        m = _FENCE.match(line)
        if m:
            lang = m.group(1)
            i += 1
            buf = []
            while i < n and not _FENCE.match(lines[i]):
                buf.append(lines[i])
                i += 1
            i += 1
            cls = f' class="lang-{lang}"' if lang else ""
            out.append(
                f"<pre{cls}><code>" + html.escape("\n".join(buf)) + "</code></pre>"
            )
            continue

        # 空行
        if not line.strip():
            i += 1
            continue

        # 見出し
        m = _HEAD.match(line)
        if m:
            level = len(m.group(1))
            text = m.group(2).strip()
            if level == 2:
                in_glossary = "用語" in _plain_text(text) or "単語" in _plain_text(text)
            hid += 1
            anchor = f"s{hid}"
            out.append(f'<h{level} id="{anchor}">{inline(text)}</h{level}>')
            if 2 <= level <= 3:
                toc.append((level, re.sub(r"[*`]", "", text), anchor))
            i += 1
            continue

        # 水平線
        if _HR.match(line):
            out.append("<hr>")
            i += 1
            continue

        # 表
        if "|" in line and i + 1 < n and _TABLE_SEP.match(lines[i + 1]):
            header = _cells(line)
            plain_header = [_plain_text(c) for c in header]
            glossary_description_index = next(
                (idx for idx, cell in enumerate(plain_header[1:], 1) if "意味" in cell or "説明" in cell),
                None,
            )
            is_glossary = bool(plain_header and plain_header[0] == "用語" and glossary_description_index)
            i += 2
            rows = []
            while i < n and "|" in lines[i] and lines[i].strip():
                rows.append(_cells(lines[i]))
                i += 1
            out.append('<div class="table-wrap"><table><thead><tr>')
            out.extend(f"<th>{inline(c)}</th>" for c in header)
            out.append("</tr></thead><tbody>")
            for row in rows:
                row += [""] * (len(header) - len(row))
                if is_glossary:
                    add_term(row[0], row[glossary_description_index])
                cells = []
                for idx, cell in enumerate(row):
                    if is_glossary and idx == 0:
                        rendered = _glossary_chip(cell, row[glossary_description_index])
                    else:
                        rendered = inline(cell)
                    cells.append(f"<td>{rendered}</td>")
                out.append("<tr>" + "".join(cells) + "</tr>")
            out.append("</tbody></table></div>")
            continue

        # 引用
        if _QUOTE.match(line):
            buf = []
            while i < n and _QUOTE.match(lines[i]):
                buf.append(_QUOTE.match(lines[i]).group(1))
                i += 1
            inner, _, quote_terms = render("\n".join(buf))
            for label, description in quote_terms:
                add_term(label, description)
            out.append(f"<blockquote>{inner}</blockquote>")
            continue

        # リスト
        if _LI.match(line):
            stack: list[tuple[int, str]] = []
            while i < n and _LI.match(lines[i]):
                m = _LI.match(lines[i])
                indent = len(m.group(1).expandtabs(4))
                ordered = not m.group(2) in ("-", "*")
                tag = "ol" if ordered else "ul"
                while stack and indent < stack[-1][0]:
                    out.append(f"</{stack.pop()[1]}>")
                if not stack or indent > stack[-1][0]:
                    out.append(f"<{tag}>")
                    stack.append((indent, tag))
                content = [m.group(3)]
                i += 1
                # 継続行（インデントされた非リスト行）を同じ <li> に取り込む
                while i < n and lines[i].strip() and not _LI.match(lines[i]) and (
                    len(lines[i]) - len(lines[i].lstrip())
                ) >= indent + 2 and not _FENCE.match(lines[i]) and not _HEAD.match(lines[i]):
                    content.append(lines[i].strip())
                    i += 1
                rendered_content = []
                for c in content:
                    definition = re.match(r"^\*\*(.+?)\*\*\s*[：:]\s*(.+)$", c)
                    if definition:
                        label, description = definition.group(1), definition.group(2)
                        add_term(label, description)
                        rendered_content.append(
                            _glossary_chip(f"**{label}**", description) + "：" + inline(description)
                        )
                    else:
                        rendered_content.append(inline(c))
                out.append("<li>" + "<br>".join(rendered_content) + "</li>")
            while stack:
                out.append(f"</{stack.pop()[1]}>")
            continue

        # 段落
        buf = [line]
        i += 1
        while i < n and lines[i].strip() and not (
            _HEAD.match(lines[i])
            or _LI.match(lines[i])
            or _QUOTE.match(lines[i])
            or _FENCE.match(lines[i])
            or _HR.match(lines[i])
        ):
            buf.append(lines[i])
            i += 1
        if in_glossary:
            plain = _plain_text("\n".join(buf))
            separators = plain.count("／") + plain.count("、")
            if separators >= 2 and not plain.lstrip().startswith("→"):
                for candidate in re.split(r"[／、\n]", plain):
                    candidate = candidate.strip(" ・、。:：")
                    if candidate and len(candidate) <= 60 and "→" not in candidate and "。" not in candidate:
                        add_term(candidate)
        out.append("<p>" + inline("<br>".join(buf)).replace("&lt;br&gt;", "<br>") + "</p>")

    return "\n".join(out), toc, terms
