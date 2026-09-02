#!/usr/bin/env python3
"""دفترُ الانتقالات — مصفوفةٌ مغلقة بين جولتين، لا فروقٌ منفصلة.

    python3 scripts/transition_matrix.py <قديم.csv> <جديد.csv>

**لماذا مصفوفةٌ لا فروق.** نشرُ ثلاثة فروقٍ منفصلة («خرج ١٬٩٠٣، دخل ٢٬٠٥٢»)
يترك فرقًا بلا تفسير، ويُخفي السؤالَ الحقيقيّ: هل **تحسَّن** شيء أم **تحرّك**؟
والمصفوفةُ تُغلق الدفتر: مجموعُ سطورها وأعمدتها عددُ الصفوف بلا بقيّة، وكلُّ
صفٍّ يُرى من أين جاء وإلى أين ذهب.

وتُثبت خاصّيّتين لا تُثبتهما الفروق:

    LEDGER_CLOSES        مجموعُ الخانات = عددُ الصفوف المشتركة، ولا صفَّ مفقود
    PEEL_LEDGER_CLOSES   فرقُ القشور مفسَّرٌ كلُّه بحركات الصفوف — وهو دفترٌ
                         **ثانٍ**: صفٌّ واحد قد يحمل ثلاث قشور، فإقفالُ
                         الصفوف لا يُقفل الإنتاج
    NO_PROMOTION         لا صفَّ انتقل من تأجيلٍ أو حجبٍ إلى **قبول**

والثانيةُ هي الحكم: التغييرُ الذي يرفع صفًّا إلى القبول يحتاج دليلًا جديدًا،
وتغييرُ قاعدةٍ ليس دليلًا. فإن سقطت فالجولةُ رقّت رتبةً بلا بوّابة.
"""
from __future__ import annotations

import collections
import csv
import sys
from pathlib import Path

#: حالاتُ القبول — ما عداها تأجيلٌ أو حجب.
ACCEPTING = frozenset({"STEM_NOT_FURTHER_PEELABLE", "CLOSED_REMAINDER"})

SHORT = {
    "STEM_NOT_FURTHER_PEELABLE": "STEM", "CLOSED_REMAINDER": "CLOSED",
    "DEFER_INITIAL_LETTER_MAY_BE_RADICAL": "D_GATE",
    "DEFER_UNRESOLVED_CLOSURE": "D_UNRES",
    "DEFER_VERBAL_OPERATOR_REGISTRY_TAG": "D_VERB",
    "DEFER_ELIDED_LETTER_NOT_RESTORABLE": "D_ELIS",
    "DEFER_REMAINDER_STANDING_UNPROVEN": "D_STAND",
    "BLOCK_SYLLABLE_BOUNDARY_CROSSED": "B_BOUND",
    "BLOCK_AXIS_3_REJECTED": "B_AX3", "BLOCK_EMPTY_REMAINDER": "B_EMPTY",
}


def load(path: Path) -> dict[str, tuple[str, int]]:
    """لكلّ صفٍّ: مخرجُه وعددُ قشوره. والثاني يُغلق دفترًا ثانيًا."""
    with open(path, encoding="utf-8", newline="") as fh:
        return {f'{r["Sura_No"]}:{r["Verse_No"]}:{r["Word_No"]}':
                (r["Termination"], int(r.get("Peel_Count") or 0))
                for r in csv.DictReader(fh)}


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        print(__doc__)
        return 2
    before, after = load(Path(argv[1])), load(Path(argv[2]))
    shared = set(before) & set(after)
    matrix = collections.Counter((before[k][0], after[k][0]) for k in shared)
    total = sum(matrix.values())

    froms = sorted({a for a, _ in matrix})
    tos = sorted({b for _, b in matrix})
    print("من \\ إلى".ljust(10)
          + "".join(SHORT.get(t, t[:8]).rjust(9) for t in tos)
          + "المجموع".rjust(10))
    for a in froms:
        row = [matrix.get((a, b), 0) for b in tos]
        print(SHORT.get(a, a[:10]).ljust(10)
              + "".join((f"{v:,}" if v else "·").rjust(9) for v in row)
              + f"{sum(row):,}".rjust(10))
    print("المجموع".ljust(10)
          + "".join(f"{sum(matrix.get((a, b), 0) for a in froms):,}".rjust(9)
                    for b in tos)
          + f"{total:,}".rjust(10))

    same = sum(v for (a, b), v in matrix.items() if a == b)
    print(f"\nثابت = {same:,} ({same / total:.1%})   متحرّك = {total - same:,}")

    # ── الدفترُ الثاني: القشور ──────────────────────────────────────────
    # دفترُ الصفوف يقفل ولا يقفل به دفترُ القشور: صفٌّ واحد قد يحمل ثلاثًا.
    # فالفرقُ في الإنتاج لا يُقاس بعدد الصفوف المتحرّكة، ويُقفل هنا صراحةً.
    peels_before = sum(v[1] for v in before.values())
    peels_after = sum(v[1] for v in after.values())
    delta_rows = collections.Counter()
    for k in shared:
        gap = before[k][1] - after[k][1]
        if gap:
            delta_rows[(before[k][0], after[k][0])] += gap
    accounted = sum(delta_rows.values())
    print(f"\nدفترُ القشور   قبل {peels_before:,} · بعد {peels_after:,} · "
          f"الفرق {peels_before - peels_after:,}")
    print(f"  مفسَّرٌ بحركات الصفوف = {accounted:,}"
          f"   البقيّة = {peels_before - peels_after - accounted:,}")
    for (a, b), v in sorted(delta_rows.items(), key=lambda kv: -kv[1])[:6]:
        print(f"    {v:>6,}  قشرةً فقدها  {SHORT.get(a, a)} → {SHORT.get(b, b)}")

    promotions = {(a, b): v for (a, b), v in matrix.items()
                  if a != b and b in ACCEPTING and a not in ACCEPTING}
    closes = (total == len(shared) and not (set(before) ^ set(after)))
    peels_close = (peels_before - peels_after) == accounted
    print("\nما تثبته هذه المصفوفة")
    print(f"  LEDGER_CLOSES = {'YES' if closes else 'NO'}"
          f"   ({len(before):,} قديمًا · {len(after):,} جديدًا · "
          f"{total:,} خانةً، بلا بقيّة)")
    print(f"  PEEL_LEDGER_CLOSES = {'YES' if peels_close else 'NO'}"
          f"   ({peels_before:,} − {peels_after:,} = {accounted:,} مفسَّرةً بالحركات)")
    print(f"  NO_PROMOTION  = {'YES' if not promotions else 'NO'}"
          "   لا صفَّ انتقل من تأجيلٍ أو حجبٍ إلى قبول")
    for (a, b), v in sorted(promotions.items(), key=lambda kv: -kv[1]):
        print(f"      ⚠ {v:,}  {a} → {b}")
    print("\nكلُّ حركةٍ غير صفرية")
    for (a, b), v in sorted(matrix.items(), key=lambda kv: -kv[1]):
        if a != b:
            print(f"  {v:>6,}  {SHORT.get(a, a)} → {SHORT.get(b, b)}")
    return 0 if (closes and peels_close and not promotions) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
