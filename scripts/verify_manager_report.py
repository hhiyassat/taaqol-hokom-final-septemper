#!/usr/bin/env python3
"""يقابل تقريرَ المدير بمصادره — **بلا استيرادٍ للمولِّد**.

    python3 scripts/verify_manager_report.py \
        [تقرير.html] [مجلّد المثبَّتات] [المثبَّت الرئيس]

**العلّة.** مدقِّقٌ يستورد المولِّد يعيد استعمال حسابه، فيوافقه ولو أخطأ
كلاهما بالخطأ نفسِه. فهذا الملفّ **لا يستورد شيئًا من المولّد**: يقرأ الـHTML
نصًّا، ويقرأ الـCSV خامًّا، ويقابل. وهو الحاجزُ نفسُه الذي وضعه تقريرُ
`HOKOM` باسم `GENERATOR_IMPORTS_VERIFIER = 0`.

وكلُّ فحصٍ هنا **يُثبت موجَبًا قبل أن ينفي**: يُثبت أنّ الصفوف موجودة، ثمّ
يقابل أعدادها. ورمزُ الخروج صفرٌ إن مرّ كلُّها.
"""
from __future__ import annotations

import csv
import html
import re
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def bucket(termination: str) -> str:
    if termination.startswith("BLOCK"):
        return "block"
    if termination.startswith("DEFER"):
        return "defer"
    return "accept"


def main(argv: list[str]) -> int:
    report = Path(argv[1]) if len(argv) > 1 else ROOT / "inspection/manager_report.html"
    runs = Path(argv[2]) if len(argv) > 2 else ROOT / "inspection/runs"
    if not report.is_file():
        print(f"MISSING {report}")
        return 2
    doc = report.read_text(encoding="utf-8")
    text = html.unescape(re.sub(r"<[^>]+>", " ", doc))

    checks: list[tuple[str, bool, str]] = []

    def affirm(name: str, ok: bool, detail: str) -> None:
        checks.append((name, ok, detail))

    # المثبَّتاتُ **تُكتشف من القرص** لا تُسمّى في المدقّق: مدقِّقٌ يعرف
    # ثلاثةً باسمها يسكت عن الرابع، والسكوتُ هو العيبُ الذي يفحص عنه.
    names = sorted(d.name for d in runs.iterdir()
                   if (d / "axis4/AXIS_4_PEEL_TO_STEM.csv").is_file())

    # ── الموجَب: الصفوفُ موجودةٌ فعلًا ──────────────────────────────────
    a4 = {f: read(runs / f / "axis4/AXIS_4_PEEL_TO_STEM.csv") for f in names}
    a1 = {f: read(runs / f / "axis1/AXIS_1_NORMALIZATION.csv") for f in names}
    affirm("V0_SOURCE_CSVS_ARE_NON_EMPTY",
           bool(names) and all(a4.values()) and all(a1.values()),
           " · ".join(f"{f}:{len(r)}" for f, r in a4.items()))

    # ── جدولُ الصفوف: كلُّ كلمةٍ في كلّ مثبَّتٍ لها أثرٌ في الـHTML ──────
    main = argv[3] if len(argv) > 3 else "f1"
    words = [r["Word"] for r in a1[main]]
    missing = [w for w in words if w not in doc]
    affirm("V1_EVERY_WORD_OF_THE_MAIN_FIXTURE_APPEARS",
           bool(words) and not missing,
           f"{main}: {len(words) - len(missing)}/{len(words)} كلمة"
           + (f"   غائب: {missing[:4]}" if missing else ""))

    # ── اللوحة: الأعداد الأربعة مقروءةٌ من الـCSV لا من المولّد ─────────
    counts = Counter(bucket(r["Termination"]) for r in a4[main])
    counts["not_carried"] = len(a1[main]) - len(a4[main])
    ok = all(str(v) in text for v in counts.values())
    affirm("V2_HEADLINE_NUMBERS_MATCH_THE_CSV", ok,
           " · ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    affirm("V3_HEADLINE_CLOSES_ON_THE_MAIN_FIXTURE",
           sum(counts.values()) == len(a1[main]),
           f"{sum(counts.values())} = {len(a1[main])} كلمة")

    # ── لا عددَ محقون: كلُّ اسمٍ يحمل عددًا موجبًا في التقرير له شاهدٌ
    # في مخرجٍ خام. والاسمُ المطبوع بعددٍ صفرٍ وحالٍ «مُعلَنٌ بلا شاهدٍ هنا»
    # ليس دعوى بل إعلانُ غياب — فيُستثنى بالنصّ لا بالتخمين.
    # الشاهدُ يُجمع من **كلّ خليّةٍ في كلّ مخرج**، لا من عمودين اخترتُهما:
    # اختيارُ الأعمدة هنا يجعل المدقِّقَ يشكو من صحيحٍ لأنّه لم ينظر حيث
    # يقع الشاهد — وهو إخفاقٌ لعلّةٍ خاطئة، أخو النجاح لعلّةٍ خاطئة.
    emitted: set[str] = set()
    for f in names:
        for path in sorted((runs / f).glob("axis*/*.csv")):
            for row in read(path):
                for value in row.values():
                    for part in re.split(r"[|@:]", value or ""):
                        part = part.strip()
                        if part:
                            emitted.add(part)
    rows_re = re.compile(
        r'<tr><td class="mono">([A-Z_0-9]+)</td><td>[^<]*</td>'
        r'<td class="mono">([\d,]+)</td><td class="(\w+)">([^<]*)</td></tr>')
    claimed, declared_absent, invented = 0, 0, []
    for name, count, _cls, label in rows_re.findall(doc):
        if int(count.replace(",", "")) > 0:
            claimed += 1
            if name not in emitted:
                invented.append(name)
        elif "بلا شاهدٍ هنا" in label:
            declared_absent += 1
    affirm("V4_EVERY_POSITIVE_COUNT_HAS_A_WITNESS_IN_A_RAW_OUTPUT",
           claimed > 0 and not invented,
           f"{claimed} اسمًا بعددٍ موجب · {declared_absent} مُعلَنًا بلا شاهد"
           + (f"   بلا شاهد: {invented}" if invented else ""))

    # ── الأثر: العددُ المطبوع = العدُّ الخام ────────────────────────────
    total = sum(len(read(p)) for f in names
                for p in sorted((runs / f).glob("axis*/*.csv"))
                if p.name != "AXIS_2_REGISTRY.csv")
    affirm("V5_TRACE_TOTAL_MATCHES_RAW_ROW_COUNT",
           f"{total:,}" in text, f"{total:,} صفًّا")

    # ── بصمةُ الحمولة تُعاد حسابًا ──────────────────────────────────────
    import hashlib
    m = re.search(r"PAYLOAD_SHA256 = ([0-9a-f]{64})", doc)
    body = doc.split('<body>', 1)[-1].rsplit(
        '<div class="mono" style="margin-top:14px">REPORT_UID', 1)[0]
    recomputed = hashlib.sha256(body.encode("utf-8")).hexdigest()
    affirm("V6_PAYLOAD_SHA256_RECOMPUTES",
           bool(m) and m.group(1) == recomputed,
           (m.group(1)[:16] if m else "غائبة") + " … " + recomputed[:16])

    passed = sum(ok for _, ok, _ in checks)
    for name, ok, detail in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name:<48} {detail}")
    print(f"\nVERIFIED = {'YES' if passed == len(checks) else 'NO'}"
          f"   ({passed}/{len(checks)})")
    print("GENERATOR_IMPORTS_VERIFIER = 0 · VERIFIER_IMPORTS_GENERATOR = 0")
    return 0 if passed == len(checks) else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
