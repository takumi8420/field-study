#!/usr/bin/env python3
"""industries.tsv から 大分類/業界 の階層フォルダと README テンプレートを生成する。
既存の README は上書きしない（追記した内容は保護される）。"""
import pathlib, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
TSV = ROOT / "tools" / "industries.tsv"

TEMPLATE = """# {industry}

- 大分類: {category}
- 状態: todo  <!-- 学習したら done に変更（index.html の進捗に反映される） -->
- 更新日:

## 1. 業界の定義・範囲
（この業界が何を指すのか。隣接業界との境界。）

## 2. 市場規模と成長性
（国内／世界の規模、成長率、サイクル性。出典を書く。）

## 3. バリューチェーン（川上 → 川下）
（誰が何を作り、誰に売るか。どこに付加価値が集まるか。）

## 4. 主要プレイヤーとシェア
| 企業 | 立ち位置 | 特徴 |
| --- | --- | --- |
|  |  |  |

## 5. 収益モデル・コスト構造
（何で儲けるか。固定費／変動費、利益率の目安。）

## 6. 競争要因（KSF）と参入障壁
（規模、技術、ブランド、免許、ネットワーク効果 など。）

## 7. 規制・法制度
（許認可、業法、政府方針、補助金。）

## 8. 最近のトピック・技術トレンド
（直近数年の構造変化。）

## 9. 用語メモ
- 

## 10. 参考リンク
- 
"""


def main() -> int:
    rows = []
    for line in TSV.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        category, industry = line.split("\t")
        rows.append((category, industry))

    categories = []
    for category, _ in rows:
        if category not in categories:
            categories.append(category)

    created_dirs = created_files = 0
    for ci, category in enumerate(categories, start=1):
        cdir = ROOT / f"{ci:02d}_{category}"
        if not cdir.exists():
            created_dirs += 1
        cdir.mkdir(exist_ok=True)

        members = [i for c, i in rows if c == category]
        for ii, industry in enumerate(members, start=1):
            idir = cdir / f"{ii:02d}_{industry}"
            if not idir.exists():
                created_dirs += 1
            idir.mkdir(exist_ok=True)

            readme = idir / "README.md"
            if not readme.exists():
                readme.write_text(
                    TEMPLATE.format(industry=industry, category=category),
                    encoding="utf-8",
                )
                created_files += 1

    print(f"categories={len(categories)} industries={len(rows)}")
    print(f"created dirs={created_dirs} readme={created_files}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
