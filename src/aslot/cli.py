"""واجهة سطر الأوامر: ``aslot <المحور>``.

كانت لكلّ محورٍ نقطةُ دخولٍ خاصة به وسكربت ``run_all.sh`` يرتّبها بأسماء
ملفاتٍ مكتوبة بخطّ اليد. فاسمُ الملف كان جزءًا من الواجهة، وتغييرُه يكسر
كلَّ من اعتاد عليه.

الآن الواجهةُ **أسماءُ محاورٍ** لا أسماءَ ملفات:

    aslot corpus  →  المحور ٠
    aslot normalize · registry · syllabify · peel
    aslot all     →  السلسلة كاملةً بالترتيب، تقف عند أول إخفاق
"""

from __future__ import annotations

import sys

from .axes.axis0_corpus import Axis0Corpus
from .axes.axis1_normalization import Axis1Normalization
from .axes.axis2_registry import Axis2Registry
from .axes.axis3_syllabification import Axis3Syllabification
from .axes.axis4_peeling import Axis4Peeling
from .axes.axis9_compliance import Axis9Compliance
from .runner import AxisRunner

AXES = (Axis0Corpus(), Axis1Normalization(), Axis2Registry(),
        Axis3Syllabification(), Axis4Peeling(), Axis9Compliance())
BY_SLUG = {axis.slug: axis for axis in AXES}

#: وسائط السلسلة الكاملة: المحور الأول يقيس كلفته مقابل المرجع،
#: والرابع يُخرج جدول MASAQ-like. وما عداهما بالافتراضات.
PIPELINE = (
    ("corpus", []),
    ("normalize", ["--cross-check-masaq", "data/MASAQ.csv"]),
    ("registry", []),
    ("syllabify", []),
    ("peel", ["--emit-masaq-like"]),
    ("compliance", []),
)

USAGE = """الاستعمال:
  aslot <المحور> [وسائط]
  aslot all [--quiet]

المحاور:
""" + "\n".join(f"  {a.slug:<10} {a.title}" for a in AXES)


def run_pipeline(extra: list[str]) -> int:
    """يشغّل السلسلة بالترتيب ويقف عند أول إخفاق.

    الوقوفُ عند أول إخفاق مقصود: المحور التالي يقرأ مخرجَ سابقه، فتشغيلُه
    على مخرجٍ مشكوكٍ فيه يُنتج قياسًا لا معنى له.
    """
    for slug, args in PIPELINE:
        print(f"\n### {BY_SLUG[slug].title}", flush=True)
        code = AxisRunner(BY_SLUG[slug]).run(args + extra)
        if code:
            print(f"\nتوقّفت السلسلة عند «{slug}» — راجع تقريره.", file=sys.stderr)
            return code
    print("\nتمّت السلسلة. المخرجات تحت reports/")
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(USAGE)
        return 0
    command, rest = argv[0], argv[1:]
    if command == "all":
        return run_pipeline(rest)
    axis = BY_SLUG.get(command)
    if axis is None:
        print(f"محورٌ غير معروف: {command}\n\n{USAGE}", file=sys.stderr)
        return 2
    return AxisRunner(axis).run(rest)


if __name__ == "__main__":            # pragma: no cover
    sys.exit(main())
