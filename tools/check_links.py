#!/usr/bin/env python3
"""生成済み HTML の内部リンク切れと、ノートの体裁をチェックする。
`python3 tools/check_links.py` で実行。異常があれば終了コード1。"""
import pathlib
import re
import sys
import urllib.parse

ROOT = pathlib.Path(__file__).resolve().parent.parent
CAT_RE = re.compile(r"^\d\d_")
STATE_RE = re.compile(r"^- 状態:\s*(\w+)", re.MULTILINE)
TITLE_RE = re.compile(r"^#\s+.+$", re.MULTILINE)


def main() -> int:
    problems: list[str] = []

    # 1. HTML の内部リンク
    for f in ROOT.rglob("*.html"):
        text = f.read_text(encoding="utf-8")
        for href in re.findall(r'href="([^"#]+)"', text):
            if href.startswith(("http", "#", "mailto")):
                continue
            if not (f.parent / urllib.parse.unquote(href)).resolve().exists():
                problems.append(f"リンク切れ: {f.relative_to(ROOT)} -> {href}")

    # 2. Markdown 内の相対リンク（.md 参照先の実在）
    for md in ROOT.rglob("*.md"):
        if ".claude" in md.parts:
            continue
        for href in re.findall(r"\]\(([^)]+\.md)[^)]*\)", md.read_text(encoding="utf-8")):
            if href.startswith("http"):
                continue
            if not (md.parent / urllib.parse.unquote(href)).resolve().exists():
                problems.append(f"md リンク切れ: {md.relative_to(ROOT)} -> {href}")

    # 3. ノートの体裁（H1 があるか、README に状態があるか）
    for cdir in sorted(p for p in ROOT.iterdir() if p.is_dir() and CAT_RE.match(p.name)):
        for idir in sorted(p for p in cdir.iterdir() if p.is_dir()):
            readme = idir / "README.md"
            if not readme.exists():
                problems.append(f"README.md がない: {idir.relative_to(ROOT)}")
                continue
            body = readme.read_text(encoding="utf-8")
            if not STATE_RE.search(body):
                problems.append(f"「- 状態:」行がない: {readme.relative_to(ROOT)}")
            for md in idir.glob("*.md"):
                if not TITLE_RE.search(md.read_text(encoding="utf-8")):
                    problems.append(f"H1 見出しがない: {md.relative_to(ROOT)}")

    if problems:
        print(f"NG: {len(problems)} 件")
        for p in problems[:40]:
            print("  -", p)
        return 1
    print("OK: リンク切れ・体裁の問題なし")
    return 0


if __name__ == "__main__":
    sys.exit(main())
