"""المحور ٣ — تحويل الكلمة إلى مقاطع صوتية.

بعد التطبيع صارت الكلمة سلسلةً صوتية نظيفة، لكنها **مسطّحة**: حروفٌ وحركات
بلا بنية. والتقشير لا يستطيع أن يقطع حيث شاء؛ يحتاج أن يعرف **أين تقع حدود
المقاطع**، لأن القطع الذي يشقّ مقطعًا ليس قشرًا بل كسرٌ للبنية.

فهذا المحور هو **الذي يمنح التقشير حقّ القطع أو يمنعه**، وهو **الذي يعدّ
الصوامت**.

المبدأ الحاكم
    ALLOWED_PATTERNS = CV · CVC · CVV · CVVC · CVCC · CVVCC
ونمطٌ خارج الستة ليس نمطًا نادرًا يُقبل بتحفّظ، بل **رفضٌ للتحليل كلّه**.
سببُه أن القائمة المغلقة تجعل التحليل **قابلًا للتكذيب**: لو سُمح بنمطٍ
سابعٍ عند الحاجة لصار كل تقطيعٍ صحيحًا بحكم التعريف.

الأطروحة المركزية
    madd = V      madd ≠ C
فألف المدّ في «مَاْ» ليست صامتًا؛ المقطع CVV فيه صامتٌ واحد لا اثنان.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..checks import CheckSuite
from ..constants import (
    CONSONANT_LETTERS,
    FATHA,
    LAYN_LETTERS,
    MADD_PARTNER,
    OUTPUT_MARKS,
    SUKUN,
)
from ..fileio import require_file, write_csv
from ..reporting import Report
from ..runner import Axis
from ..verdicts import ACCEPT, BLOCK
from .axis2_registry import iter_usable

ALLOWED_PATTERNS = ("CV", "CVC", "CVV", "CVVC", "CVCC", "CVVCC")
ALLOWED_PATTERN_SET = frozenset(ALLOWED_PATTERNS)

IMPLEMENT_WAZN = False
#: مصدرٌ واحد لعدّ الصوامت، لا اجتهاد.
CONSONANT_COUNT_SOURCE = "AXIS_3_CV_PATTERN"

# أدوار الوحدات الصوتية
CONSONANT = "C"
NUCLEUS = "V"
MADD = "MADD_V"


@dataclass
class Phone:
    letter: str
    mark: str
    role: str
    text: str


@dataclass
class Syllable:
    pattern: str
    text: str
    start: int
    end: int


@dataclass
class Analysis:
    surface: str
    verdict: str = ACCEPT
    syllables: list = field(default_factory=list)
    cv_pattern: str = ""
    pattern_sequence: list = field(default_factory=list)
    consonant_count: int = 0
    madd_status: str = ""          # PROVEN أو فراغ — لا استنتاج من الشكل
    layn_status: str = ""
    reconstruction_verified: bool = False
    boundaries: list = field(default_factory=list)
    block_reason: str = ""

    @property
    def ok(self) -> bool:
        return self.verdict == ACCEPT

    @property
    def cut_points(self) -> set:
        """المواضع التي يجوز القطع عندها. ما عداها يعبر حدًّا مقطعيًّا."""
        return set(self.boundaries)


def _units(surface: str):
    """يفكّ السطح المطبَّع إلى (حرف، علامة). المخرج المطبَّع مكتفٍ بذاته."""
    out = []
    index, total = 0, len(surface)
    while index < total:
        letter = surface[index]
        if letter not in CONSONANT_LETTERS:
            raise ValueError(f"UNEXPECTED_CHAR@{index}:{letter!r}")
        if index + 1 >= total or surface[index + 1] not in OUTPUT_MARKS:
            raise ValueError(f"LETTER_WITHOUT_MARK@{index}")
        out.append((letter, surface[index + 1]))
        index += 2
    return out


def _phones(units, analysis: Analysis) -> list[Phone]:
    """تصنيف الوحدات: صامتٌ / نواة / امتدادُ مدّ."""
    phones: list[Phone] = []
    previous_vowel: str | None = None
    for letter, mark in units:
        if mark != SUKUN:
            phones.append(Phone(letter, mark, NUCLEUS, letter + mark))
            previous_vowel = mark
            continue
        is_madd = (letter in MADD_PARTNER
                   and previous_vowel == MADD_PARTNER[letter]
                   and phones and phones[-1].role in (NUCLEUS, MADD))
        if is_madd:
            phones.append(Phone(letter, mark, MADD, letter + mark))
            analysis.madd_status = "PROVEN"
            continue
        if letter in LAYN_LETTERS and previous_vowel == FATHA:
            analysis.layn_status = "PROVEN"     # لينٌ: صامتٌ في القفل لا مدّ
        phones.append(Phone(letter, mark, CONSONANT, letter + mark))
        previous_vowel = None
    return phones


def analyze_normalized_surface(surface: str, context=None) -> Analysis:
    """التقطيع المقطعيّ لسطحٍ **مطبَّع**. لا يطبّع ولا يصحّح."""
    analysis = Analysis(surface=surface)
    if not surface:
        analysis.verdict = BLOCK
        analysis.block_reason = "EMPTY_SURFACE"
        return analysis

    try:
        units = _units(surface)
    except ValueError as exc:
        analysis.verdict = BLOCK
        analysis.block_reason = str(exc)
        return analysis

    phones = _phones(units, analysis)

    # بناء المقاطع: الصامتُ الساكن لا يكون صدرًا أبدًا، فهو قفلُ ما قبله.
    syllables: list[Syllable] = []
    index, total, offset = 0, len(phones), 0
    while index < total:
        phone = phones[index]
        if phone.role != NUCLEUS:
            analysis.verdict = BLOCK
            analysis.block_reason = ("SYLLABLE_WITHOUT_ONSET" if not syllables
                                     else "ORPHAN_CONSONANT")
            return analysis

        pattern, text, start = "CV", phone.text, offset
        offset += len(phone.text)
        index += 1
        while index < total and phones[index].role == MADD:
            pattern += "V"
            text += phones[index].text
            offset += len(phones[index].text)
            index += 1
        while index < total and phones[index].role == CONSONANT:
            pattern += "C"
            text += phones[index].text
            offset += len(phones[index].text)
            index += 1
        syllables.append(Syllable(pattern, text, start, offset))

    analysis.syllables = syllables
    analysis.pattern_sequence = [s.pattern for s in syllables]
    analysis.cv_pattern = "".join(analysis.pattern_sequence)
    analysis.consonant_count = analysis.cv_pattern.count("C")
    analysis.boundaries = [s.start for s in syllables] + [len(surface)]

    outside = sorted({s.pattern for s in syllables} - ALLOWED_PATTERN_SET)
    if outside:
        analysis.verdict = BLOCK
        analysis.block_reason = f"PATTERN_OUTSIDE_CLOSED_SIX:{','.join(outside)}"
        return analysis

    # إعادة البناء شرطٌ للقبول: التقطيع **قسمةٌ** للكلمة لا وصفٌ موازٍ لها.
    analysis.reconstruction_verified = (
        "".join(s.text for s in syllables) == surface)
    if not analysis.reconstruction_verified:
        analysis.verdict = BLOCK
        analysis.block_reason = "RECONSTRUCTION_FAILED"
    return analysis


def boundary_positions(analysis: Analysis) -> set:
    return analysis.cut_points


# ---------------------------------------------------------------------------
# الفحوص
# ---------------------------------------------------------------------------

def build_suite() -> CheckSuite:
    suite = CheckSuite("axis3")

    a = analyze_normalized_surface("مَاْ")
    suite.check("T1_MAA_IS_ONE_CONSONANT",
                a.ok and a.cv_pattern == "CVV" and a.consonant_count == 1,
                f"{a.cv_pattern} / C={a.consonant_count}")
    suite.check("T2_MADD_PROVEN_ON_MAA", a.madd_status == "PROVEN", a.madd_status)

    a = analyze_normalized_surface("بِمَاْ")
    suite.check("T3_BIMAA_IS_TWO_CONSONANTS_NOT_THREE",
                a.ok and a.consonant_count == 2,
                f"{a.pattern_sequence} / C={a.consonant_count}"
                "   (الباء صامت، ومَاْ ميمٌ وألفُ مدّ)")

    a = analyze_normalized_surface("بِسْمِ")
    suite.check("T4_BISMI_FIRST_SYLLABLE_IS_CVC",
                a.ok and a.pattern_sequence == ["CVC", "CV"],
                f"{a.pattern_sequence}   (لا يجوز فصل بِ عمّا بعدها)")
    suite.check("T5_BISMI_CUT_AFTER_BI_CROSSES_BOUNDARY", 2 not in a.cut_points,
                f"الحدود = {a.boundaries}")

    a = analyze_normalized_surface("قَاْلَ")
    suite.check("T6_QAALA_CVV_CV", a.ok and a.pattern_sequence == ["CVV", "CV"],
                str(a.pattern_sequence))
    suite.check("T9_RECONSTRUCTION_VERIFIED", a.reconstruction_verified, "YES")

    a = analyze_normalized_surface("ءَلْحَمْدُ")
    suite.check("T7_ALHAMDU", a.ok and a.pattern_sequence == ["CVC", "CVC", "CV"],
                str(a.pattern_sequence))

    a = analyze_normalized_surface("بَيْتُ")
    suite.check("T8_LAYN_IS_A_CONSONANT",
                a.ok and a.layn_status == "PROVEN" and "CVC" in a.pattern_sequence,
                f"{a.pattern_sequence} / layn={a.layn_status}")

    # مقعدُ الألف الخنجرية بعد تطبيعه: ألفُ مدٍّ لا صامت (القاعدة N8)
    from ..constants import ALIF
    from ..constants import FATHA as _F
    from ..constants import SUKUN as _S
    a = analyze_normalized_surface("ع" + _F + "ل" + _F + ALIF + _S)
    suite.check("T11_DAGGER_SEAT_IS_NOT_A_CONSONANT",
                a.ok and a.consonant_count == 2 and a.pattern_sequence == ["CV", "CVV"],
                f"{a.pattern_sequence} / C={a.consonant_count}"
                "   (لو بقيت الواو صامتًا لصارت ٣)")

    suite.check("T10_CLOSED_SIX_IS_PRIOR_TO_DATA", len(ALLOWED_PATTERNS) == 6,
                "القائمة سابقةٌ على البيانات لا مشتقّةٌ منها")

    # -- السموم ---------------------------------------------------------
    a = analyze_normalized_surface("ْبَ")
    suite.poison("P1_ONSETLESS_SYLLABLE_BLOCKED", not a.ok, a.block_reason)
    a = analyze_normalized_surface("بَتْثْجْحْ")
    suite.poison("P2_PATTERN_OUTSIDE_SIX_BLOCKS_WHOLE_ANALYSIS",
                 not a.ok and a.block_reason.startswith("PATTERN_OUTSIDE_CLOSED_SIX"),
                 a.block_reason)
    a = analyze_normalized_surface("بم")
    suite.poison("P3_UNMARKED_LETTER_BLOCKED", not a.ok, a.block_reason)
    a = analyze_normalized_surface("")
    suite.poison("P4_EMPTY_BLOCKED", not a.ok, a.block_reason)
    a = analyze_normalized_surface("بِمَاْ")
    suite.poison("P5_MADD_NEVER_COUNTED_AS_CONSONANT", a.consonant_count == 2,
                 f"C={a.consonant_count} — لو عُدّ المدّ صامتًا لصارت ٣")
    suite.poison("P6_SEVENTH_PATTERN_CANNOT_BE_ADDED_AT_RUNTIME",
                 "CVVV" not in ALLOWED_PATTERN_SET, "القائمة مغلقة")
    a = analyze_normalized_surface("بِسْمِ")
    suite.poison("P7_LICENSED_PREFIX_ALONE_DOES_NOT_CREATE_A_BOUNDARY",
                 2 not in a.cut_points, "بِ سابقةٌ مرخّصة ومع ذلك لا حدَّ عندها")
    return suite


# ---------------------------------------------------------------------------
# المحور
# ---------------------------------------------------------------------------

class Axis3Syllabification(Axis):
    number = 3
    slug = "syllabify"
    title = "المحور ٣ — المقاطع الصوتية"
    module = "aslot.axes.axis3_syllabification"
    default_output = "reports/axis_3_syllables"

    def arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--axis1-csv",
                            default="reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv")

    def execute(self, args, out_dir: Path):
        suite = build_suite()
        axis1 = require_file(Path(args.axis1_csv), what="مخرج المحور الأول",
                             remedy="هذا المحور لا يقرأ نصًّا خامًا")

        patterns: Counter = Counter()
        verdicts: Counter = Counter()
        reasons: Counter = Counter()
        skipped: Counter = Counter()
        rows = []
        for row in iter_usable(axis1, skipped):
            a = analyze_normalized_surface(row["Normalized_Word"])
            verdicts[a.verdict] += 1
            if a.ok:
                patterns.update(a.pattern_sequence)
            else:
                reasons[a.block_reason.split(":")[0]] += 1
            rows.append([row["Sura_No"], row["Verse_No"], row["Word_No"],
                         row["Word"], row["Normalized_Word"], a.verdict,
                         "·".join(a.pattern_sequence), a.consonant_count,
                         a.madd_status, a.layn_status,
                         "YES" if a.reconstruction_verified else "NO",
                         "|".join(map(str, a.boundaries)), a.block_reason])

        write_csv(out_dir / "AXIS_3_SYLLABLES.csv",
                  ["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                   "Verdict", "Syllable_Pattern", "Consonant_Count",
                   "Madd_Status", "Layn_Status", "Reconstruction_Verified",
                   "Boundaries", "Block_Reason"], rows)

        measures = {
            "analyzed": sum(verdicts.values()),
            "verdicts": dict(verdicts),
            "pattern_histogram": {p: patterns.get(p, 0) for p in ALLOWED_PATTERNS},
            "block_reasons": dict(reasons),
            "skipped_by_axis_1_status": dict(skipped),
        }
        return measures, suite

    def report(self, m: dict, suite: CheckSuite) -> Report:
        r = Report("تقرير المحور ٣ — المقاطع الصوتية")
        r.kv({
            "MODULE": self.module,
            "AXIS": self.number,
            "ALLOWED_PATTERNS": " · ".join(ALLOWED_PATTERNS),
            "CONSONANT_COUNT_SOURCE": CONSONANT_COUNT_SOURCE,
            "MADD": "V        (madd ≠ C)",
            "IMPLEMENT_WAZN": "YES" if IMPLEMENT_WAZN else "NO",
            "ANALYZED": m["analyzed"],
        })
        r.heading("القياس على كامل النصّ")
        histogram = m["pattern_histogram"]
        r.counts(histogram, note={p: "← مرخَّصٌ غير مشهود"
                                  for p, c in histogram.items() if c == 0})
        r.text("القائمة لم تُبنَ على ما ظهر، فبقي فيها ما لم يظهر —",
               "وهذا شرط كونها اختبارًا لا وصفًا.")
        r.heading("الأحكام")
        r.counts(sorted(m["verdicts"].items(), key=lambda kv: -kv[1]))
        if m["block_reasons"]:
            r.heading("أسباب الرفض")
            r.counts(sorted(m["block_reasons"].items(), key=lambda kv: -kv[1]))
        if m["skipped_by_axis_1_status"]:
            r.heading("لم تدخل هذا المحور أصلًا (بحكم المحور الأول)")
            r.counts(sorted(m["skipped_by_axis_1_status"].items(),
                            key=lambda kv: -kv[1]))
        r.proves(
            ["بنيةً مقطعية من ستة أنماط مغلقة، مُعادةَ البناء تمامًا،",
             "وعددَ صوامتٍ له مصدرٌ واحد، وحدودًا يجوز القطع عندها."],
            ["وزنًا، ولا جذرًا، ولا إعرابًا."],
            ["THREE_CONSONANT_REMAINDER ≠ ROOT_PROVEN"])
        return r
