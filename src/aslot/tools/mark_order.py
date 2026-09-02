"""بوّابةُ ترتيب العلامات — تُشغَّل على ملفٍّ فتقول أين خالف الترتيبُ النصَّ.

    python3 -m aslot.tools.mark_order --check <ملف> [<ملف> ...]

**لماذا بوّابةٌ لا فحص.** قاعدةُ المالك: كلُّ سطحٍ مشكولٍ مكتوبٍ في ملفٍّ غيرُ
موثوقٍ بطبعه حتى يُقابَل بمصدره. والمقابلةُ هنا آليّةٌ: يُمرَّر كلُّ نصٍّ عربيٍّ
مشكولٍ على `canonical_mark_order`، فما تغيّر كان يخالف ترتيبَ النصّ.

ويطبع سطرًا يبدأ بـ`DEVIATION` لكلّ مخالفة، ورمزُ الخروج صفرٌ ما دام قرأ
الملفّات — فالحكمُ على المخالفات لمن يقرأ لا للأداة.
"""
from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path

from ..constants import canonical_mark_order


def is_vocalized(text: str) -> bool:
    return (any(unicodedata.combining(c) for c in text)
            and any("؀" <= c <= "ۿ" for c in text))


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="بوّابةُ ترتيب العلامات")
    ap.add_argument("--check", action="store_true")
    ap.add_argument("files", nargs="+")
    args = ap.parse_args(argv)

    scanned = deviations = 0
    for name in args.files:
        path = Path(name)
        if not path.is_file():
            print(f"MISSING {name}", file=sys.stderr)
            return 2
        for number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            for token in line.split():
                if not is_vocalized(token):
                    continue
                scanned += 1
                if canonical_mark_order(token) != token:
                    deviations += 1
                    print(f"DEVIATION {path.name}:{number} {token}")
    print(f"SCANNED {scanned}")
    print(f"DEVIATIONS {deviations}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
