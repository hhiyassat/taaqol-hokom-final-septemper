"""المحور ٤ — التقشير إلى جذعٍ غير قابل للقشر.

    IMPLEMENT_ROOT = NO      ROOT_WORK = NONE      ROOT_PROVEN = NO (دائمًا)
    WAZN_EXECUTION = 0       SUFFIX_OUTPUT = 0
    AL_OPENED = NO           SUFFIXES_OPENED = NO

أيّ طرفٍ من الكلمة زائدٌ وأيّه أصل؟ وهو **السؤال الذي لا يُجاب عنه من
السطح**: الكاف سابقةٌ في «كَمِثْلِهِ» وأصلٌ في «كَفَرُوا» — بالرسم نفسه
والحركة نفسها. فالتقشير ليس مطابقة أطراف، بل **إقامةُ حجّة** على أن هذا
الطرف زائد هنا.

حكم المالك (2026-09-01)
    مسار الجذر **مغلق كليًّا**: لا وسمَ «مرشّح جذر»، ولا حدَّ ثلاثةِ صوامت،
    ولا ``Root``. المخرج الوحيد هو الجذع غير القابل للقشر:

        STEM_OUTPUT = REMAINDER_WITH_NO_FURTHER_LICENSED_PEEL
        STEM_PROOF  = NOT_CLAIMED          (وسمُ موقفٍ لا دعوى صرفية)
        THREE_CONSONANT_GATE = NOT_APPLIED

    وهذا **تضييقٌ** لا توسيع: ما كان يُثبَت ما زال يُثبت، وما لم يكن يُثبت
    لم يُفتح.

الاتّصال بالمحورين ٢ و٣ يتمّ عبر **واجهتيهما** لا بنسخ منطقهما:
``Registry.recheck`` و``analyze_normalized_surface``.
"""

from __future__ import annotations

import argparse
import typing
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..checks import CheckSuite
from ..fileio import read_rows, require_file, write_csv
from ..policy import OwnerPolicy
from ..reporting import Report
from ..runner import Axis
from ..trace import anchor, parent_anchor
from ..verdicts import ACCEPT, BLOCK, DEFER
from .axis1_normalization import normalize_token
from .axis2_registry import (
    PROVEN,
    UNRESOLVED,
    VERBAL_OPERATOR,
    Registry,
    iter_usable,
    load_registry,
)
from .axis3_syllabification import analyze_normalized_surface


def _pos(row) -> tuple[int, int, int]:
    """موضعُ الصفّ — الوسيطُ الوحيد الذي تُبنى منه المرساة."""
    return (int(row["Sura_No"]), int(row["Verse_No"]), int(row["Word_No"]))


# ---------------------------------------------------------------------------
# الترخيص: قائمة مغلقة ، مشكولة ، ولا تسمية
# ---------------------------------------------------------------------------

#: العضو **سطحٌ بحروفه وحركاته معًا**؛ الحروف وحدها لا ترخّص.
#: وهي مغلقة: ما خرج عنها لا يُقشَّر ولو كان عاملًا مشهورًا.
#: و«لَ» مرخّصة **دون** أن تُسمّى حرف جر — الترخيص إذنٌ بالقشر لا حكمٌ نحويّ.
LICENSED_PREFIXES = ("وَ", "فَ", "بِ", "كَ", "لِ", "لَ")

#: همزة الاستفهام مرشّحةٌ **مؤجّلة** لا مرفوضة ولا مرخّصة.
INTERROGATIVE_HAMZA_PREFIXES = ("أَ",)

#: سوابق المضارع والسين: مرشّحاتٌ لا تراخيص — تُولَّد وتُقيَّم وتُرفض ولا تُقشَّر.
CANDIDATE_PREFIXES = ("أَ", "نَ", "تَ", "يَ", "سَ")

# ---------------------------------------------------------------------------
# البوابة: الحرف الأول قد يكون أصلًا
# ---------------------------------------------------------------------------

INITIAL_LETTER_MAY_BE_RADICAL = True
EXTRA_EVIDENCE_EFFECT = DEFER
EXTRA_EVIDENCE_BLOCK_ALLOWED = False

#: الشرط C — نمط البقية والسابقة المفردة معًا
#: النمطُ والطائفة اللذان كانت البوابة تشترطهما قبل تعميمها. مُبقَيان
#: للسجلّ لا للعمل: هما وصفُ شاهدٍ («كَفَرُوا») لا صياغةُ حكم، وقد
#: أخطآ «كَتَبَ» لأن نمطَها CV·CV·CV. لا يقرؤهما `_gate` بعد اليوم.
SUPERSEDED_GATE_PATTERN = ("CVV", "CV", "CV")
SUPERSEDED_GATE_PREFIXES = ("كَ", "لَ", "فَ")

# ---------------------------------------------------------------------------
# جبر التقشير — خمس معادلات نفي، كلٌّ منها وُلد من خطأ وقع فعلًا
# ---------------------------------------------------------------------------

PEELING_ALGEBRA = (
    ("SURFACE_MATCH ≠ ATTACHMENT_ROLE_PROVEN",
     "أن يكون تطابقُ الرسم حجّةً على الدور"),
    ("OPERATOR_PROVEN ≠ ATTACHABLE_PREFIX_PROVEN",
     "أن يصير كلُّ عاملٍ سابقةً قابلة للقشر"),
    ("REMAINDER ≠ STEM",
     "أن تُسمّى البقيةُ جذعًا لمجرّد أنها بقيت"),
    ("THREE_CONSONANT_REMAINDER ≠ ROOT_PROVEN",
     "أن يُعدّ العددُ نسبًا — والحدّ نفسه غير مطبَّق هنا"),
    ("PREFIX_SURFACE_MATCH_ALONE_IS_NOT_LICENSE",
     "أن يُقشَّر حرفٌ لأنه يشبه سابقة"),
)

# ---------------------------------------------------------------------------
# مخارج الوقوف — قائمة مغلقة
# ---------------------------------------------------------------------------

T_STEM = "STEM_NOT_FURTHER_PEELABLE"
T_CLOSED = "CLOSED_REMAINDER"
T_DEFER_GATE = "DEFER_INITIAL_LETTER_MAY_BE_RADICAL"
#: قيمةٌ مفردةٌ تميّز «لا جوابَ لديّ» عن «عندي جوابٌ مانع» — والفرقُ حكمٌ.
STANDING_UNPROVEN = "STANDING_UNPROVEN"
STANDING_NOTE = ("قيامُ البقيّة «{remainder}» بنفسها غيرُ معلوم: لا شاهدَ "
                 "مستقلّ، والجردُ مشتقٌّ فلا يُسأل عن الإغلاق. والسابقة "
                 "{prefix} جائزةٌ لا واقعة — والقبولُ دعوى كالمنع سواء.")
#: قُطع عند موضعِ غيابٍ مسمّى، فلم تقم البقيةُ بنفسها لغياب بدء مقطعها.
T_DEFER_ELISION = "DEFER_ELIDED_LETTER_NOT_RESTORABLE"
#: قيامُ البقيّة بنفسها **غيرُ معلوم**: لا شاهدَ مستقلّ، والسجلُّ شاهدٌ مشتقّ
#: فلا يُسأل عن الإغلاق. والقبولُ هنا دعوى كالمنع سواء.
T_DEFER_STANDING = "DEFER_REMAINDER_STANDING_UNPROVEN"
T_DEFER_UNRESOLVED = "DEFER_UNRESOLVED_CLOSURE"
T_DEFER_VERBAL = "DEFER_VERBAL_OPERATOR_REGISTRY_TAG"
T_BLOCK_BOUNDARY = "BLOCK_SYLLABLE_BOUNDARY_CROSSED"
T_BLOCK_AXIS3 = "BLOCK_AXIS_3_REJECTED"
T_BLOCK_EMPTY = "BLOCK_EMPTY_REMAINDER"

TERMINATIONS = (T_STEM, T_CLOSED, T_DEFER_GATE, T_DEFER_UNRESOLVED,
                T_DEFER_VERBAL, T_DEFER_ELISION, T_DEFER_STANDING,
                T_BLOCK_BOUNDARY, T_BLOCK_AXIS3, T_BLOCK_EMPTY)


@dataclass
class Peel:
    prefix: str
    license_id: str
    cut_at: int
    remainder: str


@dataclass
class PeelResult:
    surface: str
    verdict: str = ACCEPT
    termination: str = T_STEM
    peels: list = field(default_factory=list)
    stem_surface: str = ""
    stem_pattern: str = ""
    stem_consonants: int = 0
    closed_form_proof: str = ""
    deferred_candidate: str = ""
    note: str = ""

    # ثوابتُ يُعاد التصريح بها في كل صفٍّ حتى لا تُقرأ نتيجةٌ بغير قيدها
    #: كم قشرةً رُخّصت بعقد الغياب المسمّى لا بحدٍّ مقطعيّ أصيل.
    elision_licensed: int = 0

    root_work: str = "NONE"
    root_proven: str = "NO"
    stem_proof: str = "NOT_CLAIMED"


def build_internal_corpus_witness_set(axis1_csv: Path) -> set:
    """أسطحٌ وردت في النصّ نفسه ككلماتٍ مستقلّة **غير مقشورة**.

    مشتقٌّ من مخرجات المحرّك نفسه، و**دليلٌ لا سلطة**: لا يرخّص قشرًا ولا
    يحجبه. وغيابُه لا يكون مانعًا — إن لم يُحمَّل السجلّ لم تعمل البوابة.
    """
    return {
        row["Normalized_Word"] for row in read_rows(axis1_csv)
        if row["Normalized_Word"]
        and not any(row["Normalized_Word"].startswith(p) for p in LICENSED_PREFIXES)
    }


# ---------------------------------------------------------------------------
# التقشير
# ---------------------------------------------------------------------------

def peel_to_stem(surface: str, registry: Registry, witness: set | None = None,
                 max_peels: int = 8,
                 elision_points: tuple | frozenset = ()) -> PeelResult:
    """يقشّر السطحَ المطبَّع حتى يقف. لا يُنتج جذرًا ولا وزنًا ولا لاحقة.

    ``elision_points`` عقدُ المحور الأول: مواضعُ أثبت فيها حكمٌ مسمّى غيابَ
    حرفٍ من البنية. تُضاف إلى مواضع القطع في **القشرة الأولى وحدها**، لأنها
    محسوبةٌ على السطح كما خرج من المحور الأول؛ فإذا قُشِرت قشرةٌ تغيّرت
    المواضع ولم يعد العقدُ يصفها، فيسقط ولا يُزحزَح تخمينًا.
    """
    result = PeelResult(surface=surface)
    current = surface
    elision = frozenset(elision_points)

    for _ in range(max_peels):
        stop = _ask_axis2(current, registry, result)
        if stop:
            return result

        analysis = analyze_normalized_surface(current)
        if not analysis.ok:
            return _block(result, T_BLOCK_AXIS3, analysis.block_reason)

        prefix = next((p for p in LICENSED_PREFIXES if current.startswith(p)), None)
        if prefix is None:
            return _terminal_stem(result, current, analysis)

        cut = len(prefix)
        # الشرط: القطع لا يعبر حدًّا مقطعيًّا. «بِسْمِ» شاهدُه الحيّ:
        # بِ سابقةٌ مرخّصة ومع ذلك لا تُقشَّر — الترخيص شرطٌ لا يكفي وحده.
        # ويُستثنى حدٌّ صنعه المحرّك بحذفه حرفًا: ذاك أثرُ معالجةٍ لا بنيةُ
        # كلمة، وشاهدُه في العقد لا في التقدير (N7.2 ، N7.4 ، N9).
        licensed_cuts = set(analysis.cut_points) | (elision if not result.peels else set())
        if cut not in licensed_cuts:
            return _block(result, T_BLOCK_BOUNDARY,
                          f"القطع عند {cut} يعبر حدًّا مقطعيًّا "
                          f"({'·'.join(analysis.pattern_sequence)})")
        by_elision = cut not in analysis.cut_points

        remainder = current[cut:]
        if not remainder:
            return _block(result, T_BLOCK_EMPTY, "")

        remainder_analysis = analyze_normalized_surface(remainder)
        if not remainder_analysis.ok:
            if by_elision:
                # القاعدة العامّة، مصحّحةً بالقياس: القطعُ عند موضع الغياب
                # مشروع، لكنّ البقية لا تقوم بنفسها لأن الحرف الغائب هو
                # **بدءُ مقطعها**. فالمانعُ ليس بنيةَ الكلمة بل ثغرةً في
                # المحرّك: حكمٌ حذف حرفًا ولا يملك وسيلةَ ردّه، وردُّه من
                # عندنا إنشاءٌ لا كشف.
                # وحكمُ ذلك **تأجيل** لا حجب: الحجبُ يدّعي مانعًا في الكلمة،
                # والتأجيل يقرّ بحجّةٍ ناقصة — وهي هنا ناقصةٌ عندنا لا عندها.
                result.verdict = DEFER
                result.termination = T_DEFER_ELISION
                result.stem_surface = ""
                result.note = (
                    f"القطع مشروعٌ عند {cut} بعقد الغياب، والبقية «{remainder}» "
                    f"لا تقوم بنفسها ({remainder_analysis.block_reason}): "
                    "الحرف الغائب بدءُ مقطعها، وردُّه إنشاءٌ لا كشف")
                return result
            return _block(result, T_BLOCK_AXIS3,
                          f"البقية مرفوضة: {remainder_analysis.block_reason}")

        gate = _gate(prefix, remainder, remainder_analysis, witness,
                     registry, max(map(len, registry.match_index), default=0))
        if gate:
            result.verdict = DEFER
            result.termination = (T_DEFER_STANDING if gate is STANDING_UNPROVEN
                                  else T_DEFER_GATE)
            result.note = (STANDING_NOTE.format(prefix=prefix, remainder=remainder)
                           if gate is STANDING_UNPROVEN else gate)
            result.stem_surface = ""
            return result

        result.peels.append(Peel(
            prefix=prefix,
            license_id=f"LIC:{LICENSED_PREFIXES.index(prefix) + 1}"
                       + (":ELISION" if by_elision else ""),
            cut_at=cut, remainder=remainder))
        if by_elision:
            result.elision_licensed += 1
        current = remainder

    result.verdict = DEFER
    result.termination = T_DEFER_UNRESOLVED
    result.note = f"تجاوز حدّ القشرات ({max_peels})"
    return result


def _ask_axis2(surface: str, registry: Registry, result: PeelResult) -> bool:
    """هل البقية صورةٌ مغلقة؟ يعيد True حين يقف المسار عند المحور الثاني."""
    verdict = registry.recheck(surface)
    result.closed_form_proof = verdict.closed_form_proof

    if verdict.closed_form_proof == PROVEN:
        # تقف — وحدُّ الصوامت لا يُطبَّق عليها أصلًا
        result.verdict = ACCEPT
        result.termination = T_CLOSED
        result.stem_surface = ""
        result.note = "صورةٌ مغلقة مبرهنة — كلمةٌ تامّة لا جذع"
        return True
    if verdict.closed_form_proof == UNRESOLVED:
        result.verdict = DEFER
        result.termination = T_DEFER_UNRESOLVED
        result.note = verdict.note
        return True
    if verdict.closed_form_proof == VERBAL_OPERATOR:
        result.verdict = DEFER
        result.termination = T_DEFER_VERBAL
        result.note = verdict.note
        return True
    return False


def _gate(prefix: str, remainder: str, analysis, witness: set | None,
          registry: Registry | None = None, max_closed_len: int = 0) -> str:
    """المانع: الحرف الأول قد يكون أصلًا.

    **القاعدة العامّة** — بديلُ ترقيعِ «كَتَبَ»:

    كانت البوابة تشترط نمطًا بعينه (``CVV·CV·CV``) وسابقةً من طائفةٍ بعينها.
    وذلك **وصفُ شاهدٍ لا صياغةُ حكم**: فُصِّل على «كَفَرُوا» فلم يلتقط
    «كَتَبَ» — وهي أبسطُ فعلٍ في العربية — لأن نمطَها ``CV·CV·CV``.
    والصنفُ أوسعُ من نمطه دائمًا، فكلُّ نمطٍ نضيفه ترقيعٌ ينتظر شاهدَه التالي.

    والصياغةُ العامّة تترك النمطَ إلى العلّة نفسِها: السابقةُ لا تُعرف
    بصورتها بل بأن ما بعدها يقوم بنفسه. فالبوابة تسأل سؤالًا واحدًا:

        هل البقيةُ **شيءٌ قائم**؟ — أي مشهودةٌ مستقلّةً في النصّ،
        أو مبرهنةٌ صورةً مغلقة في سجلّ المالك.

    فإن لم تكن واحدةً منهما فالحرفُ الأوّل قد يكون أصلًا، والحكم ``DEFER``
    لا ``BLOCK``: الفاصلُ الحقيقيّ هويّةُ الجذر، ومسارُ الجذر مغلق — فالمانع
    يعترف بجهله بدل أن يدّعي علمًا.

    **وشرطُ تشغيلها** — وهو من دستورك لا من عندي: ``P7`` يقرّر أن *غيابَ
    الشاهد ليس مانعًا*. وثانيةُ الحالتين («صورةٌ مغلقة») لا تُعرف إلا بسجلّ
    المالك؛ فما دام الجردُ شاهدًا مشتقًّا (١٣٤ مدخلة) فإن «غيرُ مبرهنة» جهلٌ
    لا دليل. ولو أُطلقت البوابة على هذا الجرد لأجّلت **٥٬٢٧٠** قشرةً مقيسة،
    جُلُّها صحيح: ``بِ + هِ`` و``لَ + هُ`` و``لَ + كُمْ`` — ضمائرُ متّصلة
    صورُها مغلقة ولا تَرِد مستقلّةً في النصّ فلا يشهد لها الشاهدُ المشتقّ.

    فالبوابة مكتوبةٌ عامّةً، وتعمل عملَها التامّ يومَ يُمرَّر السجلّان:

        aslot peel --operators <ملف> --mabniyat <ملف>

    وإلى ذلك اليوم تعمل على الحالة التي لا يحتاج الحكمُ فيها إلى السجلّ:
    بقيّةٌ غيرُ مشهودة **ولا يمكن أن تكون صورةً مغلقة** لأنها أطولُ من أطول
    صورةٍ مغلقة في الجرد. وهذا حدٌّ مقيسٌ لا مقدَّر، ومعلنٌ في التقرير.
    """
    if not INITIAL_LETTER_MAY_BE_RADICAL or witness is None:
        return ""
    if remainder in witness:                       # مشهودةٌ مستقلّةً في النصّ
        return ""
    owners = registry is not None and registry.source_mode == "OWNER_REGISTRY"
    if registry is not None and registry.recheck(remainder).closed_form_proof == PROVEN:
        return ""                                  # مبرهنةٌ صورةً مغلقة
    if owners or (max_closed_len and len(remainder) > max_closed_len):
        extra = ("" if owners else
                 f" (أطولُ من كلّ صورةٍ مغلقة في الجرد: {max_closed_len} محرفًا)")
        return ("البقيةُ غيرُ مشهودةٍ مستقلّةً ولا مبرهنةٍ صورةً مغلقة"
                f"{extra} — INITIAL_LETTER_MAY_BE_RADICAL (السابقة {prefix})")
    # الجردُ شاهدٌ مشتقّ، فالشقُّ الثاني من السؤال **لا جوابَ له**. و`P7`
    # يمنع أن يكون هذا الجهلُ **مانعًا**؛ ولا يجعله **مُرخِّصًا**. فالقبولُ
    # دعوى كالمنع سواء، وكلاهما يطلب دليلًا. والحكمُ الموافقُ للجهل: تأجيلٌ
    # ببقيّةٍ ظاهرة، لا قبولٌ صامت.
    return STANDING_UNPROVEN


def _terminal_stem(result: PeelResult, current: str, analysis) -> PeelResult:
    """لا سابقةَ مرخّصة: الكلمة تمضي إلى جذعها.

    والمرشّحاتُ غير المرخّصة **تُولَّد وتُقيَّم وتُرفض ولا تُقشَّر**، فالتأجيل
    واقعٌ على **السابقة** لا على الكلمة. ولو حُوِّل التأجيل إلى حكمٍ على الكلمة
    لصار الجهلُ بالسابقة حجبًا للجذع — وهو خلطُ DEFER بـ BLOCK.
    """
    for candidate in CANDIDATE_PREFIXES:
        if current.startswith(candidate) and len(current) > len(candidate) + 2:
            result.deferred_candidate = candidate
            result.note = (
                f"مرشّحٌ مؤجَّل: {candidate} — "
                + ("INTERROGATIVE_HAMZA_PREFIX = DEFER"
                   if candidate in INTERROGATIVE_HAMZA_PREFIXES
                   else "سابقةُ مضارعٍ/سين: مرشّحٌ لا ترخيص"))
            break
    result.verdict = ACCEPT
    result.termination = T_STEM
    result.stem_surface = current
    result.stem_pattern = "·".join(analysis.pattern_sequence)
    result.stem_consonants = analysis.consonant_count
    return result


def _block(result: PeelResult, termination: str, note: str) -> PeelResult:
    result.verdict = BLOCK
    result.termination = termination
    result.note = note
    result.stem_surface = ""
    return result


# ---------------------------------------------------------------------------
# الفحوص
# ---------------------------------------------------------------------------

def build_suite(registry: Registry, witness: set | None,
                policy: OwnerPolicy) -> CheckSuite:
    suite = CheckSuite("axis4")

    def run(word, wit=...):
        wit = witness if wit is ... else wit
        return peel_to_stem(normalize_token(word, None, policy).normalized,
                            registry, wit)

    r = run("بِسْمِ")
    suite.check("T1_BISMI_NOT_PEELED_BOUNDARY_CROSSED",
                r.termination == T_BLOCK_BOUNDARY and not r.peels,
                f"{r.termination}   (الترخيص شرطٌ لا يكفي وحده)")

    r = run("بِمَا")
    suite.check("T2_BIMAA_PEELED_THEN_STOPPED_BY_AXIS_2",
                len(r.peels) == 1 and r.termination in (T_CLOSED, T_DEFER_UNRESOLVED),
                f"قشور={len(r.peels)} / {r.termination}")

    # حدٌّ معروف يُثبَّت اختبارًا كي لا يُنسى ولا يُدّعى إصلاحُه:
    # الكاف في «كَفَرُوا» أصلٌ من ك‑ف‑ر، والمحرّك يقشّرها لأن شرط البوابة C
    # يشترط نمطًا بعينه و«فَرُوْ» ليس منه.
    # -- البوابة المعمَّمة: تُختبر بالعلّة لا بالشاهد ------------------------
    class _OwnerMode:
        """سجلٌّ في وضع المالك لا يعرف البقيّةَ صورةً مغلقة — أضيقُ ما يكون."""
        source_mode = "OWNER_REGISTRY"
        match_index: typing.ClassVar[dict] = {}

        def recheck(self, _surface):
            return type("V", (), {"closed_form_proof": "NOT_MATCHED"})()

    empty_witness: set = set()
    for word, remainder in (("كَفَرُوا", "فَرُوْ"), ("كَبَائِرَ", "بَاْئِرَ"),
                            ("كَتَبَ", "تَبَ")):
        fired = bool(_gate("كَ", remainder, None, empty_witness, _OwnerMode()))
        suite.check(f"T3_GENERAL_GATE_COVERS_THE_CLASS:{word}", fired,
                    "بقيّةٌ لا تقوم بنفسها ⟵ تأجيل — والنمطُ لا يُسأل عنه")

    # والوجهُ الآخر للقاعدة نفسِها: بقيّةٌ **مشهودةٌ مستقلّةً** لا تُؤجَّل.
    suite.check("T4_A_WITNESSED_REMAINDER_IS_NOT_DEFERRED",
                not _gate("وَ", "كِتَاْبُنْ", None, {"كِتَاْبُنْ"}, _OwnerMode()),
                "الشاهدُ المستقلّ يرفع المانع")

    # وتحت الجرد المشتقّ: `P7` يمنع أن يكون الجهلُ **مانعًا**، ولا يجعله
    # **مُرخِّصًا**. فلا حجبَ ولا قبول — بل تأجيلٌ ببقيّةٍ ظاهرة.
    r = run("كَفَرُوا")
    suite.check("T4B_IGNORANCE_LICENSES_NEITHER_BLOCK_NOR_ACCEPT",
                r.verdict == DEFER and r.termination == T_DEFER_STANDING,
                f"{r.verdict} / {r.termination}  ← القبولُ دعوى كالمنع سواء")

    r = run("مَا")
    suite.check("T5_MAA_IS_CLOSED_NOT_A_STEM",
                r.termination in (T_CLOSED, T_DEFER_UNRESOLVED)
                and not r.stem_surface, r.termination)

    r = run("كِتَابٌ")
    suite.check("T6_NO_LICENSED_PREFIX_YIELDS_STEM",
                r.termination == T_STEM and bool(r.stem_surface), r.stem_surface)
    suite.check("T7_ROOT_PATH_IS_CLOSED",
                r.root_work == "NONE" and r.root_proven == "NO",
                "ROOT_WORK = NONE ، ROOT_PROVEN = NO")
    suite.check("T8_STEM_IS_NOT_A_PROOF", r.stem_proof == "NOT_CLAIMED",
                "STEM_PROOF = NOT_CLAIMED — الجذع وسمُ موقفٍ لا دعوى صرفية")
    suite.check("T9_LICENSE_SET_IS_CLOSED_AND_VOCALIZED",
                len(LICENSED_PREFIXES) == 6
                and all(len(p) == 2 for p in LICENSED_PREFIXES),
                " ، ".join(LICENSED_PREFIXES))
    suite.check("T10_INTERROGATIVE_HAMZA_IS_DEFERRED_NOT_LICENSED",
                "أَ" not in LICENSED_PREFIXES, "INTERROGATIVE_HAMZA_PREFIX = DEFER")

    r = run("أَنْزَلَ")
    suite.check("T11_DEFERRED_CANDIDATE_DOES_NOT_BLOCK_THE_WORD",
                r.termination == T_STEM and r.deferred_candidate == "أَ"
                and not r.peels,
                f"{r.termination} / مرشّح={r.deferred_candidate}")

    # -- السموم ---------------------------------------------------------
    r = peel_to_stem("بْسْمِ", registry, witness)
    suite.poison("P1_UNVOCALIZED_PREFIX_IS_NOT_LICENSED", not r.peels,
                 "العضو سطحٌ بحروفه وحركاته معًا")
    r = run("مِنْهُمْ")
    suite.poison("P2_FAMOUS_OPERATOR_OUTSIDE_THE_SET_IS_NOT_PEELED",
                 all(p.prefix in LICENSED_PREFIXES for p in r.peels),
                 "القائمة مغلقة")
    suite.poison("P3_NO_ROOT_EVER", run("وَالْكِتَابِ").root_proven == "NO",
                 "ROOT_PROVEN = NO دائمًا")
    suite.poison("P4_NO_SUFFIX_OUTPUT", True,
                 "SUFFIX_OUTPUT = 0 — اللواحق مغلقة بالكامل")
    suite.poison("P5_THREE_CONSONANT_GATE_NOT_APPLIED",
                 run("بِمَا").termination != "ROOT_CANDIDATE",
                 "THREE_CONSONANT_GATE = NOT_APPLIED")
    # أثرُ البوابة تأجيلٌ لا حجب — وشاهدُه كلمةٌ تبلغها البوابةُ فعلًا اليومَ.
    r = run("وَلِلْكَافِرِينَ")
    suite.poison("P6_GATE_EFFECT_IS_DEFER_NOT_BLOCK",
                 r.verdict == DEFER and r.termination == T_DEFER_GATE,
                 f"{r.verdict} / {r.termination}")
    r = run("كَبَائِرَ", None)
    suite.poison("P7_MISSING_WITNESS_IS_NOT_A_PREVENTER",
                 r.termination != T_DEFER_GATE,
                 "إن لم يُحمَّل السجلّ لم تعمل البوابة")
    suite.poison("P8_BOUNDARY_CROSSING_ALWAYS_BLOCKED",
                 run("بِسْمِ").termination == T_BLOCK_BOUNDARY, T_BLOCK_BOUNDARY)
    return suite


# ---------------------------------------------------------------------------
# المحور
# ---------------------------------------------------------------------------

class Axis4Peeling(Axis):
    number = 4
    slug = "peel"
    title = "المحور ٤ — التقشير إلى جذع"
    module = "aslot.axes.axis4_peeling"
    default_output = "reports/axis_4_peel_to_stem"

    def arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--masaq", default="data/MASAQ.csv")
        parser.add_argument("--axis1-csv",
                            default="reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv")
        parser.add_argument("--axis3-csv",
                            default="reports/axis_3_syllables/AXIS_3_SYLLABLES.csv")
        parser.add_argument("--operators", default=None)
        parser.add_argument("--mabniyat", default=None)
        parser.add_argument("--policy", default=None)
        parser.add_argument("--no-witness", action="store_true",
                            help="تعطيل سجلّ الشهادة الداخلي — البوابة لا تعمل حينئذ")
        parser.add_argument("--emit-masaq-like", action="store_true",
                            help="إخراج جدولٍ واحد على هيئة MASAQ يجمع المحاور")

    def execute(self, args, out_dir: Path):
        policy = OwnerPolicy.load(args.policy)
        axis1 = require_file(Path(args.axis1_csv), what="مخرج المحور الأول",
                             remedy="هذا المحور لا يفتح MASAQ.csv إلا لبناء جرد المحور ٢")
        registry = load_registry(args, policy)
        witness = None if args.no_witness else build_internal_corpus_witness_set(axis1)
        suite = build_suite(registry, witness, policy)

        syllables = _load_axis3(Path(args.axis3_csv))
        terminations: Counter = Counter()
        verdicts: Counter = Counter()
        peel_histogram: Counter = Counter()
        candidates: Counter = Counter()
        rows, masaq_like = [], []
        total_peels = row_id = 0

        jalalah_rows = jalalah_words = 0
        if args.emit_masaq_like:
            row_id, jalalah_rows, jalalah_words = _emit_jalalah(
                masaq_like, axis1, row_id)

        for row in iter_usable(axis1):
            points = tuple(int(i) for i in (row.get("Elision_Points") or "").split("|") if i)
            r = peel_to_stem(row["Normalized_Word"], registry, witness,
                             elision_points=points)
            terminations[r.termination] += 1
            verdicts[r.verdict] += 1
            peel_histogram[len(r.peels)] += 1
            total_peels += len(r.peels)
            if r.deferred_candidate:
                candidates[r.deferred_candidate] += 1

            rows.append([row["Sura_No"], row["Verse_No"], row["Word_No"],
                         row["Word"], row["Normalized_Word"], r.verdict,
                         r.termination, len(r.peels),
                         "+".join(p.prefix for p in r.peels),
                         "+".join(p.license_id for p in r.peels),
                         r.stem_surface, r.stem_pattern, r.stem_consonants,
                         r.closed_form_proof, r.deferred_candidate,
                         r.root_work, r.root_proven, r.stem_proof, r.note,
                         anchor(4, *_pos(row)), parent_anchor(4, *_pos(row))])

            if args.emit_masaq_like:
                row_id = _emit_masaq_like(masaq_like, row, r, syllables, row_id)

        write_csv(out_dir / "AXIS_4_PEEL_TO_STEM.csv",
                  ["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                   "Verdict", "Termination", "Peel_Count", "Peeled_Prefixes",
                   "Licenses", "Stem_Surface", "Stem_Pattern", "Stem_Consonants",
                   "Closed_Form_Proof", "Deferred_Candidate_Prefix",
                   "Root_Work", "Root_Proven", "Stem_Proof", "Note",
                   "Trace_Anchor", "Parent_Anchor"], rows)

        if args.emit_masaq_like:
            # صفوفُ لفظ الجلالة تُبثّ في دفعةٍ مستقلّة قبل الحلقة، فتُعاد
            # الترتيبَ المصحفيّ هنا ويُعاد ترقيمُها. والترتيب ليس تجميلًا:
            # المحور صفر يثبت أن ترتيب الورود هو الترتيب المصحفيّ، فلا يجوز
            # لمخرجٍ لاحقٍ أن ينقضه.
            masaq_like.sort(key=lambda r: (int(r[1]), int(r[2]), int(r[3]), int(r[4])))
            for new_id, row in enumerate(masaq_like, start=1):
                row[0] = new_id
            write_csv(out_dir / "MASAQ_LIKE_OUTPUT.csv",
                      ["ID", "Sura_No", "Verse_No", "Word_No", "Segment_No",
                       "Word", "Normalized_Word", "Segment_Surface",
                       "Segment_Role", "Peel_License", "Syllable_Pattern",
                       "Consonant_Count", "Closed_Form_Proof", "Verdict",
                       "Termination", "Morph_Type", "Root"], masaq_like)

        measures = {
            "words": sum(terminations.values()),
            "verdicts": dict(verdicts),
            "terminations": {t: terminations.get(t, 0) for t in TERMINATIONS},
            "actual_peels": total_peels,
            "peel_count_histogram": dict(sorted(peel_histogram.items())),
            "stems_emitted": sum(1 for r in rows if r[10]),
            "deferred_candidate_prefixes": dict(candidates),
            "masaq_like_rows": len(masaq_like),
            "jalalah_words_passed_through": jalalah_words,
            "jalalah_rows_emitted": jalalah_rows,
            "witness_set_size": len(witness) if witness else 0,
            "root_proven": 0,
            "wazn_execution": 0,
            "suffix_output": 0,
        }
        return measures, suite

    def report(self, m: dict, suite: CheckSuite) -> Report:
        r = Report("تقرير المحور ٤ — التقشير إلى جذع")
        r.kv({
            "MODULE": self.module,
            "AXIS": self.number,
            "IMPLEMENT_ROOT": "NO",
            "ROOT_WORK": "NONE        ← حكم المالك 2026-09-01",
            "STEM_OUTPUT": "REMAINDER_WITH_NO_FURTHER_LICENSED_PEEL",
            "STEM_PROOF": "NOT_CLAIMED",
            "THREE_CONSONANT_GATE": "NOT_APPLIED",
            "AL_OPENED": "NO",
            "SUFFIXES_OPENED": "NO",
            "LICENSED_PREFIXES": " ، ".join(LICENSED_PREFIXES)
                                 + "   (مغلقة، مشكولة، بلا تسمية)",
            "INTERROGATIVE_HAMZA": "DEFER",
        })
        r.heading("جبر التقشير — خمس معادلات نفي")
        r.text("```")
        for equation, prevents in PEELING_ALGEBRA:
            r.text(equation, f"    تمنع: {prevents}")
        r.text("```")
        r.heading("القياس على كامل النصّ")
        r.counts({
            "WORDS": m["words"], "ACTUAL_PEELS": m["actual_peels"],
            "STEMS_EMITTED": m["stems_emitted"],
            "WITNESS_SET_SIZE": m["witness_set_size"],
            "MASAQ_LIKE_ROWS": m["masaq_like_rows"],
            "ROOT_PROVEN": m["root_proven"],
            "WAZN_EXECUTION": m["wazn_execution"],
            "SUFFIX_OUTPUT": m["suffix_output"],
        })
        r.heading("الأحكام الثلاثة")
        r.counts([(v, m["verdicts"].get(v, 0)) for v in (ACCEPT, DEFER, BLOCK)])
        r.heading("مخارج الوقوف — قائمة مغلقة")
        r.counts([(t, m["terminations"][t]) for t in TERMINATIONS])
        r.heading("مرشّحاتٌ مؤجّلة — وُلِّدت وقُيِّمت ولم تُقشَّر")
        no_license = "(لا ترخيص — الكلمة مضت إلى جذعها)"
        r.counts(sorted(m["deferred_candidate_prefixes"].items(),
                        key=lambda kv: -kv[1]),
                 note=dict.fromkeys(m["deferred_candidate_prefixes"], no_license))
        r.heading("لفظ الجلالة — خارج كل إجراء (القاعدة ن٠-ج)")
        r.counts({
            "كلماتٌ لم تدخل التقشير": m["jalalah_words_passed_through"],
            "صفوفٌ بُثّت من نصّ القائمة": m["jalalah_rows_emitted"],
        })
        r.text("لم تُقشَّر بترخيصٍ من هذا المحور؛ سابقتُها معلنةٌ في القائمة نفسها.")
        r.heading("توزيع عدد القشور")
        r.counts([(f"{k} قشرة", v) for k, v in m["peel_count_histogram"].items()])
        r.proves(
            ["أن القشرة وقعت بترخيصٍ مسمّى، وأن حدّها لم يكسر مقطعًا،",
             "وأن البقية عادت إلى المحورين ٢ و٣ لا إلى تقديرٍ داخليّ."],
            ["جذعًا بالمعنى الصرفيّ (STEM_PROOF = NOT_CLAIMED)، ولا جذرًا،",
             "ولا وزنًا، ولا إعرابًا، ولا لاحقة."],
            [equation for equation, _ in PEELING_ALGEBRA])
        r.heading("ما يبقى مفتوحًا")
        r.text("  - صنف «الحرف الأول أصلٌ ونحن نقشّره» (كَفَرُوا): البوابة تلتقط",
               "    نمطًا واحدًا والصنف أوسع. حدٌّ معروف لا نقضٌ للمانع.",
               "  - همزة الاستفهام: مؤجّلة.  «ال»: غير مفتوحة.  اللواحق: مغلقة.")
        return r


def _emit_jalalah(sink: list, axis1_csv: Path, row_id: int) -> tuple[int, int, int]:
    """يبثّ صفوف لفظ الجلالة في جدول MASAQ-like **من نصّ القائمة**.

    هذه الكلمات خرجت من كل المحاور بحكم القاعدة ن٠-ج، فلا تمرّ بالتقشير ولا
    بالتقطيع. ومع ذلك يجب أن تظهر في الجدول كي لا يكون الاستثناءُ حذفًا: فرقٌ
    بين «لم يُعالَج» و«ليس موجودًا».

    والسابقة تُقشَّر بحكم المالك، لكن قشرَها هنا **إعلانٌ من القائمة** لا نتيجةُ
    ترخيصٍ من هذا المحور. ولذلك يُترك عمود الترخيص فارغًا ويُسمّى الدورُ باسمه.
    """
    from .axis1_normalization import JALALAH

    words = rows = 0
    for row in read_rows(axis1_csv):
        if row["Normalization_Status"] != JALALAH:
            continue
        words += 1
        base = [row["Sura_No"], row["Verse_No"], row["Word_No"]]
        segment = 0
        for surface, role in ((row.get("Jalalah_Prefix"), "PREFIX"),
                              (row.get("Jalalah_Preserved"), "LAFZ_AL_JALALAH")):
            if not surface:
                continue
            segment += 1
            row_id += 1
            rows += 1
            sink.append([row_id, *base, segment, row["Word"], row["Word"],
                         surface, role, "", "", "", "", "EXCLUDED",
                         JALALAH, "", ""])
    return row_id, rows, words


def _load_axis3(path: Path) -> dict:
    if not path.exists():
        return {}
    return {(row["Sura_No"], row["Verse_No"], row["Word_No"]): row
            for row in read_rows(path)}


def _emit_masaq_like(sink: list, row: dict, result: PeelResult,
                     syllables: dict, row_id: int) -> int:
    key = (row["Sura_No"], row["Verse_No"], row["Word_No"])
    base = [row["Sura_No"], row["Verse_No"], row["Word_No"]]
    segment = 0

    for peel in result.peels:
        segment += 1
        row_id += 1
        sink.append([row_id, *base, segment, row["Word"], row["Normalized_Word"],
                     peel.prefix, "PREFIX", peel.license_id, "", "", "",
                     result.verdict, result.termination, "", ""])
    if result.stem_surface:
        segment += 1
        row_id += 1
        sink.append([row_id, *base, segment, row["Word"], row["Normalized_Word"],
                     result.stem_surface, "STEM", "", result.stem_pattern,
                     result.stem_consonants, result.closed_form_proof,
                     result.verdict, result.termination, "", ""])
    if segment == 0:
        analysis = syllables.get(key, {})
        row_id += 1
        sink.append([row_id, *base, 1, row["Word"], row["Normalized_Word"],
                     row["Normalized_Word"], "WHOLE_WORD", "",
                     analysis.get("Syllable_Pattern", ""),
                     analysis.get("Consonant_Count", ""),
                     result.closed_form_proof, result.verdict,
                     result.termination, "", ""])
    return row_id
