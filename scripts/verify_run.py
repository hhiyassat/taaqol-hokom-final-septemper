#!/usr/bin/env python3
"""تحقّقٌ يُثبت موجَبًا قبل أن ينفيَ إخفاقًا — قاعدةٌ عامّة لا حارسٌ واحد.

    python3 scripts/verify_run.py [جذر]

**العلّة، بنصّ المالك:**

> «كلُّ تحقّقٍ يُثبت عددًا موجَبًا متوقَّعًا قبل أن ينفيَ الإخفاق.
>  `axes_run == 5 ∧ rows == 74,668` ثمّ `failures == 0`.»

وسببُها واقعةٌ مسجَّلة: عُدَّت أسطرُ `[FAIL]` فوُجدت صفرًا، **والمخرجُ خالٍ
من المحاور أصلًا** — إذ كان `aslot all` يموت عند الاستيراد. فصفرُ الإخفاقات
لم يكن دليلَ سلامةٍ بل دليلَ أنّ شيئًا لم يجرِ.

والنفيُ وحدَه **لا يميّز** بين «جرى ولم يُخفق» و«لم يجرِ». وهذه ثالثةُ صنفٍ
واحد: اختبارٌ يمرّ لعلّةٍ خاطئة، ثمّ تحقّقٌ يمرّ لعلّةٍ خاطئة. فيُسدّ الصنفُ
بقاعدة لا يُرقَّع المثال.

**البنية**: كلُّ فحصٍ هنا `(اسمٌ ، متوقَّعٌ موجَب ، مقيس)`. ولا يُقبل فحصٌ
متوقَّعُه صفرٌ أو نفيٌ إلا بعد أن يمرّ موجَبٌ يُثبت أنّ الطاحونة دارت.

ورمزُ الخروج `0` فقط إن مرّ **كلُّ** موجَبٍ ثمّ كلُّ منفيّ.
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parents[1]

#: ما يجب أن يوجد بعد جولةٍ تامّة — أعدادٌ موجبة، لا نفي.
EXPECTED_AXES = 5
EXPECTED_ROWS = 74_668
EXPECTED_WORDS = 77_411

MEASURES = {
    0: "reports/axis_0_quran_build/AXIS_0_MEASURES.json",
    1: "reports/axis_1_normalization/AXIS_1_MEASURES.json",
    2: "reports/axis_2_mabniyat_operators/AXIS_2_MEASURES.json",
    3: "reports/axis_3_syllables/AXIS_3_MEASURES.json",
    4: "reports/axis_4_peel_to_stem/AXIS_4_MEASURES.json",
}


class Verifier:
    def __init__(self) -> None:
        self.positive: list[tuple[str, bool, str]] = []
        self.negative: list[tuple[str, bool, str]] = []

    def affirm(self, name: str, ok: bool, detail: str) -> None:
        """موجَبٌ: يُثبت أنّ شيئًا **جرى**. يُقاس أوّلًا."""
        self.positive.append((name, ok, detail))

    def deny(self, name: str, ok: bool, detail: str) -> None:
        """منفيّ: يُثبت أنّ شيئًا **لم يُخفق**. لا يُقرأ إلا بعد الموجَب."""
        self.negative.append((name, ok, detail))

    def report(self) -> int:
        affirmed = all(ok for _, ok, _ in self.positive)
        print("## الموجَب — أنّ الطاحونة دارت")
        for name, ok, detail in self.positive:
            print(f"  [{'PASS' if ok else 'FAIL'}] {name:<42} {detail}")
        print("\n## المنفيّ — أنّها لم تُخفق"
              + ("" if affirmed else "   ⚠ لا يُقرأ: الموجَبُ لم يمرّ"))
        for name, ok, detail in self.negative:
            mark = "PASS" if ok else "FAIL"
            print(f"  [{mark if affirmed else '—— '}] {name:<42} {detail}")
        denied = all(ok for _, ok, _ in self.negative)
        verdict = affirmed and denied
        print(f"\nVERIFIED = {'YES' if verdict else 'NO'}"
              f"   (موجَب {sum(ok for _, ok, _ in self.positive)}"
              f"/{len(self.positive)} · منفيّ "
              f"{sum(ok for _, ok, _ in self.negative)}/{len(self.negative)})")
        if not affirmed:
            print("والنفيُ ساقطٌ حكمًا: صفرُ إخفاقاتٍ في مخرجٍ فارغ ليس سلامة.")
        return 0 if verdict else 1


def main() -> int:
    v = Verifier()
    loaded: dict[int, dict] = {}
    for axis, rel in MEASURES.items():
        path = ROOT / rel
        if path.is_file():
            loaded[axis] = json.loads(path.read_text(encoding="utf-8"))

    # ── الموجَب ────────────────────────────────────────────────────────
    v.affirm("A1_ALL_FIVE_AXES_PRODUCED_MEASURES",
             len(loaded) == EXPECTED_AXES,
             f"{len(loaded)}/{EXPECTED_AXES} محورًا")
    words = loaded.get(0, {}).get("words_built", 0)
    v.affirm("A2_CORPUS_BUILT_THE_EXPECTED_WORDS",
             words == EXPECTED_WORDS, f"{words:,} كلمة")
    rows = 0
    a4 = ROOT / "reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv"
    if a4.is_file():
        with open(a4, encoding="utf-8", newline="") as fh:
            rows = sum(1 for _ in csv.DictReader(fh))
    v.affirm("A3_PEEL_EMITTED_THE_EXPECTED_ROWS",
             rows == EXPECTED_ROWS, f"{rows:,} صفًّا")
    checks = sum(len(m.get("self_checks", {})) for m in loaded.values())
    poisons = sum(len(m.get("poisons", {})) for m in loaded.values())
    v.affirm("A4_SUITES_ACTUALLY_RAN",
             checks > 0 and poisons > 0, f"{checks} فحصًا · {poisons} سمًّا")
    terminations = loaded.get(4, {}).get("terminations", {})
    v.affirm("A5_EVERY_ROW_HAS_A_TERMINATION",
             sum(terminations.values()) == rows,
             f"{sum(terminations.values()):,} = {rows:,}")

    # ── المنفيّ ────────────────────────────────────────────────────────
    failing = [f"{axis}:{name}"
               for axis, m in loaded.items()
               for kind in ("self_checks", "poisons")
               for name, ok in m.get(kind, {}).items() if not ok]
    v.deny("N1_NO_CHECK_OR_POISON_FAILED", not failing,
           "0 إخفاق" if not failing else " · ".join(failing[:4]))
    v.deny("N2_NO_ROW_WITHOUT_A_TRACE_ANCHOR",
           _anchors_present(a4), "كلُّ صفٍّ يحمل مرساة")
    return v.report()


def _anchors_present(path: Path) -> bool:
    if not path.is_file():
        return False
    with open(path, encoding="utf-8", newline="") as fh:
        return all((r.get("Trace_Anchor") or "").strip()
                   for r in csv.DictReader(fh))


if __name__ == "__main__":
    raise SystemExit(main())
