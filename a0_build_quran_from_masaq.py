#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الكود ١ — بناء ملف القرآن من MASAQ.csv

AXIS               = 0  (تمهيدي، ليس محورًا من المحاور الأربعة)
MODULE             = a0_build_quran_from_masaq.py
INPUT              = data/MASAQ.csv
CONSUMED_FIELDS    = Sura_No , Verse_No , Word_No , Segment_No , Word
REFERENCE_ONLY     = كل ما عدا الخمسة أعلاه  (لا يدخل المحرّك)
OWNER_RULE         = لا يُنشأ سطحٌ باليد ، ولا يُصحَّح رسمٌ ، ولا يُخمَّن ترتيب

المسألة
-------
MASAQ جدولٌ على مستوى **المقطع الصرفي** (segment): الكلمة الواحدة موزّعة على
عدّة صفوف، وعمود Word يكرّر سطح الكلمة كاملًا في كل صفٍّ من صفوفها.

فبناء «ملف القرآن» ليس نسخًا للعمود، بل **طيُّ الصفوف إلى كلمات** ثم
**طيُّ الكلمات إلى آيات** ثم **طيُّ الآيات إلى سور** — مع إثبات أن الطيّ
لم يفقد شيئًا ولم يخترع شيئًا.

قاعدة الجبر الحاكمة هنا:

    ROW_COUNT ≠ WORD_COUNT
    WORD_SURFACE = القيمة المتّفق عليها في كل صفوف الكلمة ، لا القيمة الأولى

المخرجات
--------
  QURAN_FROM_MASAQ.txt     نصّ مقروء: سطر لكل آية  "sura|verse|كلماتها"
  QURAN_WORDS.csv          جدول الكلمات المفردة (مدخل المحور الأول)
  QURAN_BUILD_REPORT.txt   كتلة القياس key=value
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from collections import Counter, OrderedDict
from pathlib import Path

# ---------------------------------------------------------------------------
# ١ — الثوابت المعلنة
# ---------------------------------------------------------------------------

MODULE = "a0_build_quran_from_masaq.py"
AXIS = 0

#: الحقول الخمسة التي أذن بها المالك لهذا الكود — قائمة مغلقة
CONSUMED_FIELDS = ("Sura_No", "Verse_No", "Word_No", "Segment_No", "Word")

#: كل ما عداها مرجعٌ لا مدخل. يُنسخ عند الطلب ولا يُبنى عليه قرار.
REFERENCE_ONLY_FIELDS = (
    "ID", "Without_Diacritics", "Segmented_Word", "Morph_Tag", "Morph_Type",
    "Punctuation_Mark", "Invariable_Declinable", "Syntactic_Role",
    "Possessive_Construct", "Case_Mood", "Case_Mood_Marker", "Phrase",
    "Phrasal_Function", "Gloss",
)

EXPECTED_SURA_COUNT = 114


# ---------------------------------------------------------------------------
# ٢ — أدوات
# ---------------------------------------------------------------------------

def sha256_of_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def as_int(value: str, field: str, row_no: int) -> int:
    """تحويلٌ صارم: لا يُصلَح حقلٌ تالف، بل يُعلَن.

    ملاحظة مقصودة: ``int()`` في بايثون يقبل الأرقام العربية-الهندية (٢ → 2)،
    وهذا قبولٌ ضمنيّ لم يأذن به المالك. فيُشترط هنا أن تكون الخانات ASCII
    صراحةً قبل التحويل.
    """
    raw = str(value).strip()
    if not raw or not all("0" <= ch <= "9" for ch in raw.lstrip("-")):
        raise SystemExit(
            f"STOP / OWNER_ALERT / NO_INFERENCE\n"
            f"  السبب  = حقلٌ عدديّ غير قابل للقراءة\n"
            f"  الحقل  = {field}\n"
            f"  الصفّ  = {row_no}\n"
            f"  القيمة = {value!r}\n"
            f"  الحكم  = BLOCK (لا يُخمَّن رقمُ سورةٍ أو آيةٍ أو كلمة)"
        )
    return int(raw)


# ---------------------------------------------------------------------------
# ٣ — الطيّ: صفوف → كلمات
# ---------------------------------------------------------------------------

class WordRecord:
    """كلمةٌ واحدة مطويّةٌ من صفوف MASAQ الخاصة بها."""

    __slots__ = ("sura", "verse", "word_no", "surface", "segments",
                 "surface_conflict", "segment_gap")

    def __init__(self, sura: int, verse: int, word_no: int):
        self.sura = sura
        self.verse = verse
        self.word_no = word_no
        self.surface: str | None = None
        self.segments: list[tuple[int, str]] = []   # (Segment_No, Word)
        self.surface_conflict = False
        self.segment_gap = False

    def add(self, segment_no: int, word_surface: str) -> None:
        if self.surface is None:
            self.surface = word_surface
        elif self.surface != word_surface:
            # عمود Word يجب أن يتّفق في كل صفوف الكلمة. اختلافه واقعةٌ تُسجَّل ولا تُرجَّح.
            self.surface_conflict = True
        self.segments.append((segment_no, word_surface))

    def finalize(self) -> None:
        self.segments.sort(key=lambda t: t[0])
        expected = list(range(1, len(self.segments) + 1))
        actual = [s for s, _ in self.segments]
        self.segment_gap = (expected != actual)

    @property
    def key(self) -> tuple[int, int, int]:
        return (self.sura, self.verse, self.word_no)

    @property
    def segment_count(self) -> int:
        return len(self.segments)


def fold_rows_to_words(csv_path: Path) -> tuple[OrderedDict, dict]:
    """يقرأ MASAQ.csv ويطوي صفوفه إلى كلمات. لا يفتح غير الحقول الخمسة."""
    words: OrderedDict[tuple[int, int, int], WordRecord] = OrderedDict()
    stats = Counter()

    with csv_path.open(encoding="utf-8", newline="") as fh:
        reader = csv.DictReader(fh)
        missing = [f for f in CONSUMED_FIELDS if f not in (reader.fieldnames or [])]
        if missing:
            raise SystemExit(
                "STOP / OWNER_ALERT / NO_INFERENCE\n"
                f"  السبب = حقولٌ مأذونة غائبة عن المدخل: {missing}\n"
                "  الحكم = BLOCK"
            )
        stats["input_columns"] = len(reader.fieldnames or [])

        for row_no, row in enumerate(reader, start=2):
            stats["rows_read"] += 1
            sura = as_int(row["Sura_No"], "Sura_No", row_no)
            verse = as_int(row["Verse_No"], "Verse_No", row_no)
            word_no = as_int(row["Word_No"], "Word_No", row_no)
            seg_no = as_int(row["Segment_No"], "Segment_No", row_no)
            surface = row["Word"]

            key = (sura, verse, word_no)
            rec = words.get(key)
            if rec is None:
                rec = WordRecord(sura, verse, word_no)
                words[key] = rec
            rec.add(seg_no, surface)

    for rec in words.values():
        rec.finalize()
        if rec.surface_conflict:
            stats["surface_conflicts"] += 1
        if rec.segment_gap:
            stats["segment_numbering_gaps"] += 1

    return words, stats


# ---------------------------------------------------------------------------
# ٤ — الفحوص الذاتية (اختبارات تُشغَّل على البيانات نفسها، لا على عيّنة)
# ---------------------------------------------------------------------------

def self_checks(words: OrderedDict) -> list[tuple[str, bool, str]]:
    checks: list[tuple[str, bool, str]] = []

    def add(name, ok, detail=""):
        checks.append((name, bool(ok), detail))

    keys = list(words.keys())

    # T1: ترتيب الصفوف في المدخل يوافق ترتيب (سورة، آية، كلمة)
    add("T1_INPUT_ORDER_IS_CANONICAL", keys == sorted(keys),
        "ترتيب ورود الكلمات في MASAQ = الترتيب المصحفي")

    # T2: عدد السور
    suras = sorted({k[0] for k in keys})
    add("T2_SURA_COUNT", len(suras) == EXPECTED_SURA_COUNT, f"{len(suras)}/{EXPECTED_SURA_COUNT}")
    add("T3_SURA_NUMBERING_CONTIGUOUS", suras == list(range(1, len(suras) + 1)),
        "أرقام السور متّصلة من ١")

    # T4: أرقام الآيات متّصلة من ١ داخل كل سورة
    verses_by_sura: dict[int, set[int]] = {}
    for s, v, _ in keys:
        verses_by_sura.setdefault(s, set()).add(v)
    bad_verses = [s for s, vs in verses_by_sura.items()
                  if sorted(vs) != list(range(1, len(vs) + 1))]
    add("T4_VERSE_NUMBERING_CONTIGUOUS", not bad_verses, f"سور مخالفة = {bad_verses[:5]}")

    # T5: سطح الكلمة متّفق عليه في كل صفوفها
    conflicts = [r.key for r in words.values() if r.surface_conflict]
    add("T5_WORD_SURFACE_AGREES_ACROSS_SEGMENTS", not conflicts, f"تعارضات = {len(conflicts)}")

    # T6: لا كلمة بلا سطح
    empty = [r.key for r in words.values() if not (r.surface or "").strip()]
    add("T6_NO_EMPTY_SURFACE", not empty, f"فارغة = {len(empty)}")

    # T7: الطيّ لا يفقد صفًّا — مجموع مقاطع الكلمات = عدد الصفوف المقروءة
    add("T7_FOLD_IS_LOSSLESS", True, "يُتحقَّق منه في التقرير مقابل ROWS_READ")

    return checks


def input_defects(words: OrderedDict) -> list[tuple[str, int, str, list]]:
    """عيوبٌ **في المدخل** لا في المحرّك.

    الفرق جوهريّ: الفحص الذاتي يقيس التزام الكود، وهذا يقيس حالة MASAQ.
    فلا يُعالَج أيٌّ منها هنا، ولا يُرقَّع ترقيم، ولا تُدرَج كلمةٌ مفقودة.
    الحكم في جميعها: DEFER + OWNER_ALERT.
    """
    keys = list(words.keys())
    defects: list[tuple[str, int, str, list]] = []

    # D1: ثغرات في ترقيم الكلمات داخل الآية (رقمٌ مفقود في MASAQ)
    words_by_verse: dict[tuple[int, int], set[int]] = {}
    for s, v, w in keys:
        words_by_verse.setdefault((s, v), set()).add(w)
    d1 = [k for k, ws in words_by_verse.items()
          if sorted(ws) != list(range(1, len(ws) + 1))]
    defects.append(("D1_WORD_NUMBER_GAPS_IN_VERSE", len(d1),
                    "أرقام كلماتٍ مفقودة داخل آيات — لا تُردَم", d1[:8]))

    # D2: ترقيم مقاطع غير متّصل داخل الكلمة (تكرارٌ أو ثغرة)
    d2_dup, d2_gap = [], []
    for rec in words.values():
        nums = [s for s, _ in rec.segments]
        if len(set(nums)) != len(nums):
            d2_dup.append(rec.key)
        elif nums != list(range(1, len(nums) + 1)):
            d2_gap.append(rec.key)
    defects.append(("D2A_SEGMENT_NUMBER_DUPLICATED", len(d2_dup),
                    "تكرار Segment_No داخل الكلمة (أشهره «يا» الموصولة بما بعدها)", d2_dup[:8]))
    defects.append(("D2B_SEGMENT_NUMBER_GAP", len(d2_gap),
                    "ثغرة في ترقيم المقاطع", d2_gap[:8]))

    # D3: سطحٌ يحمل فراغًا داخله — أي كلمتين في خليّة كلمةٍ واحدة
    d3 = [rec.key for rec in words.values() if " " in (rec.surface or "")]
    defects.append(("D3_MULTIWORD_SURFACE_IN_ONE_CELL", len(d3),
                    "خليّة Word فيها أكثر من كلمة", d3[:8]))

    return defects


def poison_checks() -> list[tuple[str, bool, str]]:
    """سمومٌ: مدخلاتٌ يجب أن تُرفض. النجاح = أن تُرفض فعلًا."""
    poisons: list[tuple[str, bool, str]] = []

    def add(name, ok, detail=""):
        poisons.append((name, bool(ok), detail))

    # P1: رقم سورة غير عدديّ يجب أن يوقف التنفيذ
    try:
        as_int("٢", "Sura_No", 0)
        add("P1_REJECT_NON_ASCII_DIGIT", False, "قُبل وهو يجب أن يُرفض")
    except SystemExit:
        add("P1_REJECT_NON_ASCII_DIGIT", True, "رُفض كما يجب")

    # P2: حقل فارغ يجب أن يوقف التنفيذ
    try:
        as_int("", "Verse_No", 0)
        add("P2_REJECT_EMPTY_NUMERIC", False, "قُبل وهو يجب أن يُرفض")
    except SystemExit:
        add("P2_REJECT_EMPTY_NUMERIC", True, "رُفض كما يجب")

    # P3: كلمةٌ سطحُها مختلفٌ بين صفّين يجب أن تُوسم تعارضًا لا أن تُرجَّح
    rec = WordRecord(1, 1, 1)
    rec.add(1, "بِسْمِ")
    rec.add(2, "بسم")
    rec.finalize()
    add("P3_SURFACE_CONFLICT_IS_FLAGGED_NOT_RESOLVED", rec.surface_conflict,
        "التعارض يُسجَّل ولا يُختار أحد الطرفين")

    # P4: مقاطع بترتيب مقلوب يجب أن تُرتَّب لا أن تُقبل كما وردت
    rec2 = WordRecord(1, 1, 1)
    rec2.add(2, "بِسْمِ")
    rec2.add(1, "بِسْمِ")
    rec2.finalize()
    add("P4_SEGMENTS_SORTED_NOT_TRUSTED", [s for s, _ in rec2.segments] == [1, 2],
        "تُرتَّب المقاطع ولا يُعتمد ترتيب الورود")

    # P5: فجوةٌ في ترقيم المقاطع يجب أن تُكشف
    rec3 = WordRecord(1, 1, 1)
    rec3.add(1, "و"); rec3.add(3, "و")
    rec3.finalize()
    add("P5_SEGMENT_GAP_DETECTED", rec3.segment_gap, "الفجوة تُكشف")

    # P6: الأرقام العربية-الهندية يجب ألّا تُقبل ضمنيًّا
    try:
        as_int("٢٣", "Verse_No", 0)
        add("P6_REJECT_ARABIC_INDIC_DIGITS", False, "قُبل وهو يجب أن يُرفض")
    except SystemExit:
        add("P6_REJECT_ARABIC_INDIC_DIGITS", True, "رُفض كما يجب")

    # P7: مسافةٌ مقحمة في رقمٍ يجب ألّا تُبتلع صامتًا
    try:
        as_int("1 2", "Word_No", 0)
        add("P7_REJECT_SPACED_NUMBER", False, "قُبل وهو يجب أن يُرفض")
    except SystemExit:
        add("P7_REJECT_SPACED_NUMBER", True, "رُفض كما يجب")

    return poisons


# ---------------------------------------------------------------------------
# ٥ — الكتابة
# ---------------------------------------------------------------------------

def write_quran_text(words: OrderedDict, out: Path) -> int:
    verses: OrderedDict[tuple[int, int], list[str]] = OrderedDict()
    for rec in words.values():
        verses.setdefault((rec.sura, rec.verse), []).append(rec.surface or "")
    with out.open("w", encoding="utf-8") as fh:
        for (s, v), ws in verses.items():
            fh.write(f"{s}|{v}|{' '.join(ws)}\n")
    return len(verses)


def write_words_csv(words: OrderedDict, out: Path) -> None:
    with out.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow([
            "Sura_No", "Verse_No", "Word_No", "Word",
            "Segment_Count", "Segment_Numbers",
            "Surface_Conflict", "Segment_Numbering_Gap",
        ])
        for rec in words.values():
            w.writerow([
                rec.sura, rec.verse, rec.word_no, rec.surface,
                rec.segment_count,
                "|".join(str(s) for s, _ in rec.segments),
                "YES" if rec.surface_conflict else "NO",
                "YES" if rec.segment_gap else "NO",
            ])


def render_report(csv_path: Path, digest: str, words: OrderedDict, stats: Counter,
                  verse_count: int, checks, poisons, defects) -> str:
    seg_hist = Counter(r.segment_count for r in words.values())
    ok_checks = sum(1 for _, ok, _ in checks if ok)
    ok_poisons = sum(1 for _, ok, _ in poisons if ok)

    lines = []
    lines.append("=" * 72)
    lines.append("تقرير الكود ١ — بناء ملف القرآن من MASAQ")
    lines.append("=" * 72)
    lines.append("")
    lines.append("```")
    lines.append(f"MODULE                = {MODULE}")
    lines.append(f"AXIS                  = {AXIS}")
    lines.append(f"INPUT                 = {csv_path}")
    lines.append(f"INPUT_SHA256          = {digest}")
    lines.append(f"CONSUMED_FIELDS       = {', '.join(CONSUMED_FIELDS)}")
    lines.append(f"INPUT_COLUMNS         = {stats['input_columns']}")
    lines.append(f"REFERENCE_ONLY_FIELDS = {len(REFERENCE_ONLY_FIELDS)}  (لا تدخل المحرّك)")
    lines.append("")
    lines.append(f"ROWS_READ             = {stats['rows_read']:,}")
    lines.append(f"WORDS_BUILT           = {len(words):,}")
    lines.append(f"VERSES_BUILT          = {verse_count:,}")
    lines.append(f"SURAS_BUILT           = {len({r.sura for r in words.values()}):,}")
    lines.append(f"ROW_COUNT_MINUS_WORDS = {stats['rows_read'] - len(words):,}  (الفرق = مقاطع زائدة عن كلمة)")
    lines.append("")
    lines.append("SEGMENTS_PER_WORD_HISTOGRAM")
    for k in sorted(seg_hist):
        lines.append(f"  {k}_SEGMENTS          = {seg_hist[k]:,}")
    lines.append("")
    lines.append(f"SURFACE_CONFLICTS     = {stats['surface_conflicts']}")
    lines.append("")
    lines.append(f"SELF_CHECKS           = {ok_checks}/{len(checks)}")
    lines.append(f"POISONS               = {ok_poisons}/{len(poisons)}")
    lines.append(f"INPUT_DEFECTS         = {sum(1 for _, n, _, _ in defects if n)} صنفًا"
                 f"  (الحكم = DEFER + OWNER_ALERT ، لا يُرقَّع منها شيء)")
    lines.append("```")
    lines.append("")
    lines.append("## الفحوص الذاتية (التزام المحرّك)")
    for name, ok, detail in checks:
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {name:42s} {detail}")
    lines.append("")
    lines.append("## السموم (مدخلاتٌ يجب أن تُرفض)")
    for name, ok, detail in poisons:
        lines.append(f"  [{'PASS' if ok else 'FAIL'}] {name:42s} {detail}")
    lines.append("")
    lines.append("## عيوب المدخل المقيسة — حالة MASAQ لا حالة المحرّك")
    lines.append("  الحكم في جميعها DEFER: تُسجَّل ولا تُعالَج، ولا يُخترع رقمٌ ولا تُدرَج كلمة.")
    for name, count, detail, sample in defects:
        lines.append(f"  [{'DEFER' if count else 'CLEAR'}] {name:36s} = {count:>6,}   {detail}")
        if sample:
            lines.append(f"          نماذج: {sample}")
    lines.append("")
    lines.append("## ما لا يثبته هذا الكود")
    lines.append("  - لا يثبت صحّة رسم MASAQ ؛ ينقله كما هو.")
    lines.append("  - لا يثبت تطبيعًا ولا تقطيعًا ولا تقشيرًا — تلك محاور تالية.")
    lines.append("  - لا يستعمل Segmented_Word ولا Morph_Tag ؛ هما مرجعٌ للمقارنة لا مدخل.")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ٦ — التشغيل
# ---------------------------------------------------------------------------

def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="بناء ملف القرآن من MASAQ.csv")
    ap.add_argument("--masaq", default="data/MASAQ.csv")
    ap.add_argument("--output-dir", default="reports/axis_0_quran_build")
    args = ap.parse_args(argv)

    csv_path = Path(args.masaq)
    if not csv_path.exists():
        raise SystemExit(
            "STOP / OWNER_ALERT / NO_INFERENCE\n"
            f"  السبب = المدخل غير موجود: {csv_path}\n"
            "  الحكم = BLOCK"
        )
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    digest = sha256_of_file(csv_path)
    words, stats = fold_rows_to_words(csv_path)

    verse_count = write_quran_text(words, out_dir / "QURAN_FROM_MASAQ.txt")
    write_words_csv(words, out_dir / "QURAN_WORDS.csv")

    checks = self_checks(words)
    poisons = poison_checks()
    defects = input_defects(words)

    # T7 يُحسم هنا لا في الدالّة: الطيّ لا يفقد صفًّا
    total_segments = sum(r.segment_count for r in words.values())
    checks = [(n, (total_segments == stats["rows_read"]) if n == "T7_FOLD_IS_LOSSLESS" else ok,
               f"{total_segments:,} مقطعًا = {stats['rows_read']:,} صفًّا"
               if n == "T7_FOLD_IS_LOSSLESS" else d)
              for n, ok, d in checks]

    report = render_report(csv_path, digest, words, stats, verse_count,
                           checks, poisons, defects)
    (out_dir / "QURAN_BUILD_REPORT.txt").write_text(report + "\n", encoding="utf-8")
    (out_dir / "QURAN_BUILD_MEASURES.json").write_text(json.dumps({
        "module": MODULE,
        "input_sha256": digest,
        "rows_read": stats["rows_read"],
        "words_built": len(words),
        "verses_built": verse_count,
        "suras_built": len({r.sura for r in words.values()}),
        "self_checks": {n: ok for n, ok, _ in checks},
        "poisons": {n: ok for n, ok, _ in poisons},
        "input_defects": {n: c for n, c, _, _ in defects},
    }, ensure_ascii=False, indent=2), encoding="utf-8")

    print(report)
    failed = [n for n, ok, _ in checks + poisons if not ok]
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
