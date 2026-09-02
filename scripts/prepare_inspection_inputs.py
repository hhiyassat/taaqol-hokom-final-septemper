#!/usr/bin/env python3
"""يُحضّر مدخلات المثبَّتات الثلاثة بصيغة المحور صفر — بلا طبعِ سطحٍ باليد.

    python3 scripts/prepare_inspection_inputs.py

**العلّة.** المحورُ صفر يقرأ «سورة|آية|كلماتها»، والنصّان المصدران نصّان
عاريان. فالتحويلُ آليّ: يُقرأ الملفّ ويُلفّ سطرُه بموضعه، ولا يُعاد طبعُ حرف.

و`F2` أشدّ: نصُّه **مشتقٌّ من عمود `Example_Vocalized`** في جدول العوامل، لا
مكتوبٌ بيد. فلو كُتب باليد لكان دعوى — وهي بعينها الواقعةُ المسجَّلة: أوّلُ
جردٍ للفظ الجلالة كُتب باليد فلم يطابق منه إلا سطحٌ واحد من ٢٬٧٠٤.

    F1  ayat.txt      البقرة ٢٨٢          2|282|…
    F2  operators.csv عمود الشاهد المشكول  0|n|…   (0 = خارجُ المصحف)
    F3  story.txt     نثرٌ حديث            0|n|…
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INSPECTION = ROOT / "inspection"
OPERATORS = INSPECTION / "data" / "operators_catalog_split_vocalized_corrected.csv"

#: موضعُ `F1` في المصحف — سورةُ البقرة، آيةُ الدَّين.
F1_POSITION = (2, 282)
#: `0` تُعلن أنّ النصَّ خارجُ المصحف، فلا يُدَّعى له موضعٌ ليس له.
OUTSIDE = 0


def lines_of(path: Path) -> list[str]:
    return [ln.strip() for ln in path.read_text(encoding="utf-8").splitlines()
            if ln.strip()]


def write_positioned(dest: Path, rows: list[tuple[int, int, str]]) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text("".join(f"{s}|{v}|{t}\n" for s, v, t in rows),
                    encoding="utf-8")
    return sum(len(t.split()) for _, _, t in rows)


def main() -> int:
    if not OPERATORS.is_file():
        print(f"OWNER_ALERT: جدولُ العوامل غائب — {OPERATORS}", file=sys.stderr)
        return 2

    f1 = [(F1_POSITION[0], F1_POSITION[1], ln)
          for ln in lines_of(INSPECTION / "ayat.txt")]

    with OPERATORS.open(encoding="utf-8-sig", newline="") as fh:
        catalog = list(csv.DictReader(fh))
    f2: list[tuple[int, int, str]] = []
    for index, row in enumerate(catalog, start=1):
        example = (row.get("Example_Vocalized") or "").strip()
        if example:
            f2.append((OUTSIDE, index, example))

    f3 = [(OUTSIDE, index, ln)
          for index, ln in enumerate(lines_of(INSPECTION / "story.txt"), start=1)]

    for name, rows in (("f1", f1), ("f2", f2), ("f3", f3)):
        tokens = write_positioned(INSPECTION / "runs" / name / "input.txt", rows)
        print(f"{name}  سطورًا {len(rows):>4}   توكنات {tokens:>5}")
    print(f"\nF2 مشتقٌّ من {len(catalog)} صفًّا، منها {len(f2)} ذاتُ شاهدٍ مشكول.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
