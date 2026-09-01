#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الكود ٤ — المحور الثالث: تحويل الكلمة إلى مقاطع صوتية

AXIS   = 3
MODULE = a3_syllabify.py

المسألة (T3 §٣ـ١)
------------------
بعد التطبيع صارت الكلمة سلسلةً صوتية نظيفة، لكنها **مسطّحة**: حروفٌ وحركات
بلا بنية. والتقشير لا يستطيع أن يقطع حيث شاء؛ يحتاج أن يعرف **أين تقع حدود
المقاطع**، لأن القطع الذي يشقّ مقطعًا ليس قشرًا بل كسرٌ للبنية.

فالمحور الثالث هو **الذي يمنح التقشير حقّ القطع أو يمنعه**، وهو **الذي يعدّ
الصوامت**.

المبدأ الحاكم (T3 §٣ـ٢)
    ALLOWED_PATTERNS = CV · CVC · CVV · CVVC · CVCC · CVVCC
ونمطٌ خارج الستة ليس نمطًا نادرًا يُقبل بتحفّظ، بل **رفضٌ للتحليل كلّه**.

الأطروحة المركزية (T3 §٣ـ٤)
    madd = V      madd ≠ C
فألف المدّ في `مَاْ` ليست صامتًا؛ المقطع CVV فيه صامتٌ واحد لا اثنان.

الواجهة التي يستدعيها المحور الرابع
    analyze_normalized_surface(surface, context=None) -> SyllableAnalysis

المحور الثالث **لا يقرأ نصًّا خامًا** — يقرأ مخرجات المحور الأول، وهذا شرطُ
ألّا يعيد تطبيعًا من عنده.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from a1_normalize import (FATHA, DAMMA, KASRA, SUKUN, HARAKAT, MADD_PARTNER,
                          WAW, YAA, CONSONANT_LETTERS)

MODULE = "a3_syllabify.py"
AXIS = 3

# ---------------------------------------------------------------------------
# ١ — القائمة المغلقة: ستة أنماط، لا سابع لها
# ---------------------------------------------------------------------------

ALLOWED_PATTERNS = ("CV", "CVC", "CVV", "CVVC", "CVCC", "CVVCC")
ALLOWED_PATTERN_SET = frozenset(ALLOWED_PATTERNS)

#: T3 §٣ـ٨ — ما لا يثبته هذا المحور
IMPLEMENT_WAZN = False

#: T3 §٣ـ٥ — مصدرٌ واحد لعدّ الصوامت، لا اجتهاد
CONSONANT_COUNT_SOURCE = "AXIS_3_CV_PATTERN"

VERDICT_ACCEPT = "ACCEPT"
VERDICT_BLOCK = "BLOCK"


# ---------------------------------------------------------------------------
# ٢ — البنى
# ---------------------------------------------------------------------------

@dataclass
class Phone:
    """وحدةٌ صوتية بعد التصنيف: صامتٌ أو امتدادُ مدّ."""
    letter: str
    mark: str
    role: str            # ONSET_OR_CODA_C | NUCLEUS_V | MADD_V
    text: str


@dataclass
class Syllable:
    pattern: str
    text: str
    start: int           # موضع البداية بالحروف داخل السطح المطبّع
    end: int
    phones: list = field(default_factory=list)


@dataclass
class SyllableAnalysis:
    surface: str
    verdict: str = VERDICT_ACCEPT
    syllables: list = field(default_factory=list)
    cv_pattern: str = ""                # نمط الكلمة كاملًا (CV متسلسل)
    pattern_sequence: list = field(default_factory=list)  # ['CVC','CV',...]
    consonant_count: int = 0
    madd_status: str = ""               # PROVEN أو فراغ — لا استنتاج من الشكل
    layn_status: str = ""
    reconstruction_verified: bool = False
    boundaries: list = field(default_factory=list)   # مواضع القطع المرخّصة
    block_reason: str = ""

    @property
    def ok(self) -> bool:
        return self.verdict == VERDICT_ACCEPT


# ---------------------------------------------------------------------------
# ٣ — التحليل
# ---------------------------------------------------------------------------

def _units(surface: str):
    """يفكّ السطح المطبّع إلى (حرف، علامة). المخرج المطبّع مكتفٍ بذاته (N12)."""
    out = []
    i, n = 0, len(surface)
    while i < n:
        ch = surface[i]
        if ch not in CONSONANT_LETTERS:
            raise ValueError(f"UNEXPECTED_CHAR@{i}:{ch!r}")
        if i + 1 >= n or surface[i + 1] not in (HARAKAT | {SUKUN}):
            raise ValueError(f"LETTER_WITHOUT_MARK@{i}")
        out.append((ch, surface[i + 1]))
        i += 2
    return out


def analyze_normalized_surface(surface: str, context=None) -> SyllableAnalysis:
    """التقطيع المقطعيّ لسطحٍ **مطبَّع**. لا يطبّع ولا يصحّح."""
    res = SyllableAnalysis(surface=surface)

    if not surface:
        res.verdict = VERDICT_BLOCK
        res.block_reason = "EMPTY_SURFACE"
        return res

    try:
        units = _units(surface)
    except ValueError as exc:
        res.verdict = VERDICT_BLOCK
        res.block_reason = str(exc)
        return res

    # ---- (أ) تصنيف الوحدات: صامت / نواة / امتداد مدّ --------------------
    phones: list[Phone] = []
    prev_vowel: str | None = None
    for letter, mark in units:
        if mark in HARAKAT:
            phones.append(Phone(letter, mark, "NUCLEUS_V", letter + mark))
            prev_vowel = mark
        else:                                   # SUKUN
            if letter in MADD_PARTNER and prev_vowel == MADD_PARTNER[letter] \
                    and phones and phones[-1].role in ("NUCLEUS_V", "MADD_V"):
                # T3 §٣ـ٤ : madd = V ، madd ≠ C
                phones.append(Phone(letter, mark, "MADD_V", letter + mark))
                res.madd_status = "PROVEN"
            else:
                if letter in (WAW, YAA) and prev_vowel == FATHA:
                    res.layn_status = "PROVEN"   # لينٌ: صامتٌ في القفل، لا مدّ
                phones.append(Phone(letter, mark, "ONSET_OR_CODA_C", letter + mark))
                prev_vowel = None

    # ---- (ب) بناء المقاطع: الصامت الساكن لا يكون بدايةً أبدًا -----------
    syllables: list[Syllable] = []
    i, n = 0, len(phones)
    offset = 0
    while i < n:
        p = phones[i]
        if p.role != "NUCLEUS_V":
            # صامتٌ ساكن بلا نواةٍ قبله = مقطعٌ بلا صدر
            if not syllables:
                res.verdict = VERDICT_BLOCK
                res.block_reason = "SYLLABLE_WITHOUT_ONSET"
                return res
            res.verdict = VERDICT_BLOCK
            res.block_reason = "ORPHAN_CONSONANT"
            return res

        # الصدر + النواة
        pat = "CV"
        text = p.text
        start = offset
        offset += len(p.text)
        i += 1
        # امتداد المدّ
        while i < n and phones[i].role == "MADD_V":
            pat += "V"
            text += phones[i].text
            offset += len(phones[i].text)
            i += 1
        # القفل: كلُّ ساكنٍ يليه مباشرةً حتى نواةٍ جديدة
        while i < n and phones[i].role == "ONSET_OR_CODA_C" and \
                not (i + 1 < n and phones[i + 1].role == "NUCLEUS_V" and False):
            # الساكن لا يصلح صدرًا، فهو قفلٌ لهذا المقطع
            pat += "C"
            text += phones[i].text
            offset += len(phones[i].text)
            i += 1

        syllables.append(Syllable(pat, text, start, offset))

    res.syllables = syllables
    res.pattern_sequence = [s.pattern for s in syllables]
    res.cv_pattern = "".join(res.pattern_sequence)
    res.consonant_count = res.cv_pattern.count("C")
    res.boundaries = [s.start for s in syllables] + [len(surface)]

    # ---- (ج) القائمة المغلقة: نمطٌ خارج الستة = رفضُ التحليل كلّه ------
    bad = [s.pattern for s in syllables if s.pattern not in ALLOWED_PATTERN_SET]
    if bad:
        res.verdict = VERDICT_BLOCK
        res.block_reason = f"PATTERN_OUTSIDE_CLOSED_SIX:{','.join(sorted(set(bad)))}"
        return res

    # ---- (د) إعادة البناء شرطٌ للقبول (T3 §٣ـ٧) -------------------------
    res.reconstruction_verified = ("".join(s.text for s in syllables) == surface)
    if not res.reconstruction_verified:
        res.verdict = VERDICT_BLOCK
        res.block_reason = "RECONSTRUCTION_FAILED"
        return res

    return res


def boundary_positions(analysis: SyllableAnalysis) -> set:
    """المواضع التي يجوز القطع عندها. أي قطعٍ في غيرها يعبر حدًّا مقطعيًّا."""
    return set(analysis.boundaries)


# ---------------------------------------------------------------------------
# ٤ — الفحوص والسموم
# ---------------------------------------------------------------------------

def self_checks() -> list:
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    r = analyze_normalized_surface("مَاْ")
    add("T1_MAA_IS_ONE_CONSONANT", r.ok and r.cv_pattern == "CVV" and r.consonant_count == 1,
        f"{r.cv_pattern} / C={r.consonant_count}   (T3 §٣ـ٤)")
    add("T2_MADD_PROVEN_ON_MAA", r.madd_status == "PROVEN", r.madd_status)

    r = analyze_normalized_surface("بِمَاْ")
    add("T3_BIMAA_IS_TWO_CONSONANTS_NOT_THREE",
        r.ok and r.consonant_count == 2,
        f"{r.pattern_sequence} / C={r.consonant_count}   (T3 §٣ـ٤: الباء صامت، ومَاْ ميمٌ وألفُ مدّ)")

    r = analyze_normalized_surface("بِسْمِ")
    add("T4_BISMI_FIRST_SYLLABLE_IS_CVC",
        r.ok and r.pattern_sequence == ["CVC", "CV"],
        f"{r.pattern_sequence}   (T3 §٣ـ٦: لا يجوز فصل بِ عمّا بعدها)")
    add("T5_BISMI_CUT_AFTER_BI_CROSSES_BOUNDARY",
        2 not in boundary_positions(r),
        f"الحدود = {r.boundaries}")

    r = analyze_normalized_surface("قَاْلَ")
    add("T6_QAALA_CVV_CV", r.ok and r.pattern_sequence == ["CVV", "CV"], f"{r.pattern_sequence}")

    r = analyze_normalized_surface("ءَلْحَمْدُ")
    add("T7_ALHAMDU", r.ok and r.pattern_sequence == ["CVC", "CVC", "CV"],
        f"{r.pattern_sequence}")

    r = analyze_normalized_surface("بَيْتٌ".replace("ٌ", "ُ"))
    add("T8_LAYN_IS_A_CONSONANT", r.ok and r.layn_status == "PROVEN" and "CVC" in r.pattern_sequence,
        f"{r.pattern_sequence} / layn={r.layn_status}")

    r = analyze_normalized_surface("قَاْلَ")
    add("T9_RECONSTRUCTION_VERIFIED", r.reconstruction_verified, str(r.reconstruction_verified))

    add("T10_CLOSED_SIX_IS_PRIOR_TO_DATA", len(ALLOWED_PATTERNS) == 6,
        "القائمة سابقةٌ على البيانات لا مشتقّةٌ منها")

    return out


def poison_checks() -> list:
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    r = analyze_normalized_surface("ْبَ")           # يبدأ بساكن
    add("P1_ONSETLESS_SYLLABLE_BLOCKED", not r.ok, r.block_reason)

    r = analyze_normalized_surface("بَتْثْجْحْ")     # ثلاثة سواكن متتالية ⇒ CVCCCC
    add("P2_PATTERN_OUTSIDE_SIX_BLOCKS_WHOLE_ANALYSIS",
        not r.ok and r.block_reason.startswith("PATTERN_OUTSIDE_CLOSED_SIX"), r.block_reason)

    r = analyze_normalized_surface("بم")            # حرفان بلا علامات
    add("P3_UNMARKED_LETTER_BLOCKED", not r.ok, r.block_reason)

    r = analyze_normalized_surface("")
    add("P4_EMPTY_BLOCKED", not r.ok, r.block_reason)

    r = analyze_normalized_surface("بِمَاْ")
    add("P5_MADD_NEVER_COUNTED_AS_CONSONANT", r.consonant_count == 2,
        f"C={r.consonant_count} — لو عُدّ المدّ صامتًا لصارت ٣ ولعُدّت مرشّحَ جذر")

    add("P6_SEVENTH_PATTERN_CANNOT_BE_ADDED_AT_RUNTIME",
        "CVVV" not in ALLOWED_PATTERN_SET, "القائمة مغلقة")

    r = analyze_normalized_surface("بِسْمِ")
    add("P7_LICENSED_PREFIX_ALONE_DOES_NOT_CREATE_A_BOUNDARY",
        2 not in boundary_positions(r),
        "بِ سابقةٌ مرخّصة ومع ذلك لا حدَّ عندها")

    return out


# ---------------------------------------------------------------------------
# ٥ — التشغيل على مخرج المحور الأول
# ---------------------------------------------------------------------------

def run_corpus(axis1_csv: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    pattern_hist = Counter()
    verdict_count = Counter()
    block_reasons = Counter()
    status_skipped = Counter()
    rows = []

    with axis1_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            status = row["Normalization_Status"]
            if status in ("EXCLUDED_FAWATIH_AL_SUWAR",
                          "IGNORED_NON_WORD_TOKEN") or \
               status.startswith("STOPPED_"):
                status_skipped[status] += 1
                continue
            r = analyze_normalized_surface(row["Normalized_Word"])
            verdict_count[r.verdict] += 1
            if r.ok:
                for p in r.pattern_sequence:
                    pattern_hist[p] += 1
            else:
                block_reasons[r.block_reason.split(":")[0]] += 1
            rows.append([
                row["Sura_No"], row["Verse_No"], row["Word_No"], row["Word"],
                row["Normalized_Word"], r.verdict,
                "·".join(r.pattern_sequence), r.consonant_count,
                r.madd_status, r.layn_status,
                "YES" if r.reconstruction_verified else "NO",
                "|".join(str(b) for b in r.boundaries),
                r.block_reason,
            ])

    with (out_dir / "AXIS_3_SYLLABLES.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                    "Verdict", "Syllable_Pattern", "Consonant_Count",
                    "Madd_Status", "Layn_Status", "Reconstruction_Verified",
                    "Boundaries", "Block_Reason"])
        w.writerows(rows)

    return {
        "analyzed": sum(verdict_count.values()),
        "verdicts": dict(verdict_count),
        "pattern_histogram": {p: pattern_hist.get(p, 0) for p in ALLOWED_PATTERNS},
        "block_reasons": dict(block_reasons),
        "skipped_by_axis_1_status": dict(status_skipped),
    }


def render_report(m, checks, poisons) -> str:
    L = []
    L.append("=" * 72)
    L.append("تقرير الكود ٤ — المحور الثالث: المقاطع الصوتية")
    L.append("=" * 72)
    L.append("")
    L.append("```")
    L.append(f"MODULE                 = {MODULE}")
    L.append(f"AXIS                   = {AXIS}")
    L.append(f"ALLOWED_PATTERNS       = {' · '.join(ALLOWED_PATTERNS)}")
    L.append(f"CONSONANT_COUNT_SOURCE = {CONSONANT_COUNT_SOURCE}")
    L.append("MADD                   = V        (madd ≠ C)")
    L.append(f"IMPLEMENT_WAZN         = {'YES' if IMPLEMENT_WAZN else 'NO'}")
    L.append(f"ANALYZED               = {m['analyzed']:,}")
    L.append("```")
    L.append("")
    L.append("## القياس على كامل النصّ — والنمط السادس هو الشاهد")
    L.append("```")
    total = sum(m["pattern_histogram"].values())
    for p in ALLOWED_PATTERNS:
        c = m["pattern_histogram"][p]
        note = "  ← مرخَّصٌ غير مشهود" if c == 0 else ""
        L.append(f"{p:6s} = {c:>9,}{note}")
    L.append(f"{'المجموع':6s} = {total:>9,}")
    L.append("```")
    L.append("القائمة لم تُبنَ على ما ظهر، فبقي فيها ما لم يظهر — وهذا شرط كونها اختبارًا.")
    L.append("")
    L.append("## الأحكام")
    L.append("```")
    for k, v in sorted(m["verdicts"].items(), key=lambda t: -t[1]):
        L.append(f"{k:10s} = {v:>9,}")
    L.append("```")
    if m["block_reasons"]:
        L.append("### أسباب الرفض")
        L.append("```")
        for k, v in sorted(m["block_reasons"].items(), key=lambda t: -t[1]):
            L.append(f"{k:36s} = {v:>7,}")
        L.append("```")
    if m["skipped_by_axis_1_status"]:
        L.append("### لم تدخل المحور الثالث أصلًا (بحكم المحور الأول)")
        L.append("```")
        for k, v in sorted(m["skipped_by_axis_1_status"].items(), key=lambda t: -t[1]):
            L.append(f"{k:56s} = {v:>7,}")
        L.append("```")
    L.append("")
    L.append(f"## الفحوص الذاتية: {sum(1 for _, o, _ in checks if o)}/{len(checks)}")
    for n, ok, d in checks:
        L.append(f"  [{'PASS' if ok else 'FAIL'}] {n:48s} {d}")
    L.append("")
    L.append(f"## السموم: {sum(1 for _, o, _ in poisons if o)}/{len(poisons)}")
    for n, ok, d in poisons:
        L.append(f"  [{'PASS' if ok else 'FAIL'}] {n:48s} {d}")
    L.append("")
    L.append("## ما يثبته المحور الثالث وما لا يثبته (T3 §٣ـ٨)")
    L.append("  يثبت   : بنيةً مقطعية من ستة أنماط مغلقة، مُعادةَ البناء تمامًا،")
    L.append("           وعددَ صوامتٍ له مصدرٌ واحد، وحدودًا يجوز القطع عندها.")
    L.append("  لا يثبت: وزنًا، ولا جذرًا، ولا إعرابًا.")
    L.append("  جبر    : THREE_CONSONANT_REMAINDER ≠ ROOT_PROVEN")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="المحور الثالث — المقاطع الصوتية")
    ap.add_argument("--axis1-csv",
                    default="reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv")
    ap.add_argument("--output-dir", default="reports/axis_3_syllables")
    args = ap.parse_args(argv)

    checks = self_checks()
    poisons = poison_checks()

    src = Path(args.axis1_csv)
    if not src.exists():
        raise SystemExit(
            "STOP / OWNER_ALERT / NO_INFERENCE\n"
            f"  السبب = مخرج المحور الأول غير موجود: {src}\n"
            "  الحكم = BLOCK (المحور الثالث لا يقرأ نصًّا خامًا)"
        )
    out_dir = Path(args.output_dir)
    m = run_corpus(src, out_dir)

    report = render_report(m, checks, poisons)
    (out_dir / "AXIS_3_REPORT.txt").write_text(report + "\n", encoding="utf-8")
    (out_dir / "AXIS_3_MEASURES.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report)
    return 1 if [n for n, ok, _ in checks + poisons if not ok] else 0


if __name__ == "__main__":
    sys.exit(main())
