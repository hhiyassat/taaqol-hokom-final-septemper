#!/usr/bin/env python3
"""جردُ الأسطح المشكولة المكتوبة باليد — المقامُ المجهول يُعرَف.

    python3 scripts/audit_handwritten_surfaces.py [جذر]

**العلّة.** اصطيد بالعرض فحصٌ كان يمرّ **لعلّةٍ خاطئة** منذ كُتب
(`T1_ALLAH_SHADDA_UNFOLDS`): سطحُه المكتوب باليد لم يكن يطابق جردَ لفظ
الجلالة، فيسلك مسارَ التطبيع العامّ ويُصدّق ما لم يقع. واحدٌ اصطيد؛ والسؤالُ
الذي لم يُسأل: **كم غيرُه؟**

وصنفُ الخطر معلومٌ محدود: كلُّ سطحٍ مشكولٍ مكتوبٍ بيدٍ في كودٍ أو اختبار.
فيُجرَد كلُّه ويُمرَّر على `canonical_mark_order`، ويُطبع ما يتغيّر.

**ما يعنيه المخرج.** سطحٌ يتغيّر ترتيبُ علاماته = سطحٌ كان — قبل القاعدة
العامّة — **لا يطابق النصّ**. وأيُّ اختبارٍ بُني عليه كان يقيس مسارًا غيرَ
المسار المقصود، سواءٌ مرّ أم سقط.

    HANDWRITTEN_VOCALIZED_SURFACES_AUDITED = <المفحوص> / <المقام>
    REORDERED_BY_CANONICALISATION          = <ما كان يخالف النصّ>

ورقمُ الخروج ليس حكمًا على السلامة: التغيُّرُ اليومَ لا يضرّ لأن التوحيد
يقع عند الحدّ. وإنما هو **جردُ ما كان يخالف** قبل القاعدة، ودليلُ أن المقام
لم يعد مجهولًا.
"""
from __future__ import annotations

import ast
import sys
import unicodedata
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from aslot.constants import canonical_mark_order

#: المجلداتُ التي تُجرَد — الكودُ والاختباراتُ والبياناتُ المكتوبةُ بيدٍ.
#: `tests_taaqol` أُنشئ بعد كتابة هذا الجرد فبقي خارج نطاقه — ومجلَّدٌ
#: جديدٌ خارج النطاق يجعل المقامَ يبدو كاملًا وهو ناقص. فالنطاقُ يُوسَّع
#: صراحةً، والبصمةُ في المخرج تُظهر أنّ الشجرةَ المفحوصة تغيّرت.
SCANNED = ("src", "tests", "tests_taaqol", "scripts", "data", "laws")
SKIP_PARTS = {"__pycache__", "vendor", "reports", ".git"}

#: **يُستثنى النصُّ المصدر.** أوّلُ تشغيلٍ لهذا الجرد أعطى ٣٩٬٩٣٧ سطحًا
#: «مخالفًا»، جُلُّها من `MASAQ.csv` — وذلك خطأُ نطاقٍ لا كشف: النصُّ
#: المصدر هو **مرجعُ** الترتيب لا منحرفٌ عنه، وعدُّه مخالفًا يقلب المقياس
#: على رأسه. والسؤالُ عن المكتوب **بيدٍ** في كودٍ أو اختبار، لا عن المنقول.
SOURCE_CORPORA = {"data/MASAQ.csv"}

#: ملفّاتٌ **مولَّدةٌ من النصّ حرفًا بحرف** لا مكتوبةٌ بيد. ترتيبُها ترتيبُ
#: النصّ (شدّةٌ قبل حركة)، فتظهر «مخالفةً» للترتيب القانونيّ وهي أصدقُ ما
#: يكون — والمحمِّلُ يوحّد الطرفين عند الحدّ. تُعدّ على حدةٍ ولا تُخلط
#: بالمكتوب بيدٍ: خلطُهما يُغرق الإشارةَ في ضجيج.
CORPUS_DERIVED = {"data/lafz_al_jalalah.json"}


def is_vocalized(text: str) -> bool:
    """سطحٌ عربيٌّ يحمل علامةً مركّبةً واحدة على الأقلّ."""
    return (any(unicodedata.combining(c) for c in text)
            and any("؀" <= c <= "ۿ" for c in text))


def literals(path: Path):
    """كلُّ نصٍّ عربيٍّ مشكولٍ في الملفّ — من الشيفرة لا من التخمين."""
    raw = path.read_text(encoding="utf-8", errors="replace")
    if path.suffix == ".py":
        try:
            tree = ast.parse(raw)
        except SyntaxError:
            return
        for node in ast.walk(tree):
            if (isinstance(node, ast.Constant) and isinstance(node.value, str)
                    and is_vocalized(node.value)):
                yield node.lineno, node.value
        return
    for number, line in enumerate(raw.splitlines(), start=1):
        for chunk in line.replace('"', " ").replace(",", " ").split():
            if is_vocalized(chunk):
                yield number, chunk


def main(argv: list[str]) -> int:
    root = Path(argv[1]) if len(argv) > 1 else Path(__file__).resolve().parents[1]
    import hashlib
    digest = hashlib.sha256()
    audited = 0
    reordered: list[tuple[str, int, str]] = []
    derived: list[tuple[str, int, str]] = []
    files = 0
    for folder in SCANNED:
        base = root / folder
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or set(path.parts) & SKIP_PARTS:
                continue
            if path.suffix not in (".py", ".json", ".md", ".csv"):
                continue
            if str(path.relative_to(root)) in SOURCE_CORPORA:
                continue
            digest.update(str(path.relative_to(root)).encode())
            digest.update(path.read_bytes())
            seen = False
            for line, text in literals(path):
                audited += 1
                seen = True
                if canonical_mark_order(text) != text:
                    rel = str(path.relative_to(root))
                    (derived if rel in CORPUS_DERIVED else reordered).append(
                        (rel, line, text))
            files += 1 if seen else 0

    fingerprint = digest.hexdigest()
    print("# جردُ الأسطح المشكولة المكتوبة باليد\n")
    print(f"النطاق: {' · '.join(SCANNED)}"
          f"   — مستثنًى: {' · '.join(sorted(SOURCE_CORPORA))} (نصٌّ مصدر لا مكتوبٌ بيد)\n")
    # المقامُ **دالّةٌ في الشجرة لا ثابت**: أوّلُ نشرٍ قال ٨٢١ وثانٍ ٨٢٧،
    # والفرقُ ستّةُ نصوصٍ عربية في سكربتين أُضيفا بين الجولتين. فرقمٌ بلا
    # حالةِ الشجرة التي قِيس عليها **لا يقفل**، فتُنشر معه بصمتُها.
    print(f"TREE_FINGERPRINT                       = {fingerprint[:16]}"
          f"   ({files} ملفًّا مفحوصًا)")
    print(f"HANDWRITTEN_VOCALIZED_SURFACES_AUDITED = {audited:,}"
          "   ← دالّةٌ في الشجرة أعلاه، لا ثابتٌ للمشروع")
    print(f"HANDWRITTEN_REORDERED                  = {len(reordered):,}"
          "   ← هذا هو الرقمُ الذي كان مجهولًا")
    print(f"CORPUS_DERIVED_REORDERED               = {len(derived):,}"
          "   (ترتيبُ النصّ نفسِه، لا خطأ)")
    print()
    if reordered:
        print("أسطحٌ مكتوبةٌ بيدٍ كانت تخالف ترتيبَ النصّ:")
        for where, line, text in reordered:
            print(f"  {where}:{line}  {text}")
    else:
        print("**لا سطحَ مكتوبٌ بيدٍ يخالف ترتيبَ النصّ.**")
        print("فالفحصُ الذي اصطيد كان الوحيدَ من صنفه، والمقامُ لم يعد مجهولًا.")
    if derived:
        print(f"\nومن المولَّد من النصّ: {len(derived)} سطحًا في "
              f"{' · '.join(sorted({w for w, _, _ in derived}))} — "
              "ترتيبُها ترتيبُ النصّ، والمحمِّلُ يوحّد الطرفين.")
    print("\nوالتغيُّرُ اليومَ لا يضرّ: التوحيدُ يقع عند الحدّ قبل أيّ مقارنة.")
    print("وإنما هذا جردُ ما كان **يمرّ لعلّةٍ خاطئة** لولا القاعدة.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
