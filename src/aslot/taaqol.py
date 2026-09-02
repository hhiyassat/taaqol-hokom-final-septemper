"""جسرُ تعقُّل — الحوامل المستوردة، ومرساةُ الأثر، وجردُ الرفض المغلق.

هذه الوحدة تنفّذ **ثلاث مراحل فقط** من خطّة التحويل، وهي المراحل التي نصّت
الخطّةُ نفسُها على أنها *تُنفَّذ بلا حكمٍ جديدٍ من المالك*:

    T-1  تاكسونومية الرفض المغلقة   ← جردٌ مستخرَجٌ من مخرجاتٍ فعليّة
    T-2  حاملات النواة              ← استيرادٌ مباشر من المستودع المُنزَل
    T-3  مرساة الأثر لكل صفّ         ← trace_ref و parent_anchor

وما فوقها (T-4 فما بعد) **موقوفٌ بإنذار مالك**: تصنيفُ البقايا وسقوفُها،
والغلقُ Γ، والخطوطُ الممنوعة، والبوّابات — كلُّها تغيّر أحكامًا، وتغييرُ
الحكم ليس لي. انظر `OWNER_DECISIONS_PENDING` في آخر الملف.

قرارُ الاستيراد مقابل النسخ
---------------------------
الخطّةُ رفعته إلى المالك، وحكمُه فيه صريحٌ بأمره: «`gh repo clone
sonaiso/Taaqol-GPT` وادمجه مع كودك». فالمستودعُ مُنزَلٌ في `vendor/Taaqol-GPT`
ويُستورَد منه مباشرةً. وأثرُ ذلك معلن: تطوُّرُ أسلوط مربوطٌ بتطوُّر تعقُّل عند
هذه الحوامل، والبصمةُ أدناه هي ما يجعل الارتباطَ **مرئيًّا** لا صامتًا.

الحدّ
-----
* لا تُستورد إلا **حواملُ النواة**: أسماءٌ وجبرٌ ومحاضر. ولا يُستورد `gamma`
  ولا `TransitionGate` ولا `ForbiddenLines` — تلك أدواتُ حكمٍ، وتشغيلُها
  تغييرُ أحكام، وهو موقوفٌ (T-5 ، T-6 ، T-7).
* **فشلٌ مغلق**: غيابُ المستودع أو انحرافُ بصمةٍ يقف بإنذار مالك ولا يمضي
  بحواملَ بديلة. ولا يُلتقط استثناءُ الاستيراد ليُستبدل بصنفٍ محلّيّ — ذلك
  فشلٌ مفتوح، وهو الخرقُ رقم ٨ في تقرير الخطّة.
* لا يُكتب في `vendor/` شيء. المستودعُ يُقرأ ولا يُعدَّل.
"""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

from .errors import owner_alert
from .trace import anchor, parent_anchor

#: جذرُ المستودع المُنزَل، نسبةً إلى جذر المشروع.
VENDOR_ROOT = Path(__file__).resolve().parents[2] / "vendor" / "Taaqol-GPT"
_SRC = VENDOR_ROOT / "src"

#: الالتزامُ المُنزَل. تُثبَّت لتكون الترقيةُ حدثًا مرئيًّا لا انجرافًا صامتًا.
VENDOR_COMMIT = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
VENDOR_LICENSE = "Apache-2.0"

#: بصماتُ الحوامل المستوردة وحدَها — لا المستودعِ كلِّه. فما لا يُقرأ لا يُثبَّت،
#: وتثبيتُ ما لا يُقرأ يجعل التحقّقَ يفشل لتغييرٍ لا يمسّنا.
PINNED_CARRIERS: dict[str, str] = {
    "core/closure_state.py":
        "c21f3c97eed353af1972693c2a80dffc5cf1ec47873c26220f1f213a865d22da",
    "core/rank_lattice.py":
        "e11d470ddf2dba20b1769bcebdfba12909233e6451cf59769de31ada966468a0",
    "core/transition_state.py":
        "14b8c99cb2ffe7d8e0dc3684ee518cb104acf409005e94de74b781261002e82c",
    "core/residual_policy.py":
        "dbee4befbc3ab81376dc6ba3230542e3fc59e1a50b02091a40fc22a164f9e281",
    "core/failure_taxonomy.py":
        "dec78566f331f16bda216c720c84bc96efd26f1580dd60cd61ff79d33834def7",
    "core/trace_ledger.py":
        "ccc09d631c463053d24ca21bb48aa07984d88b80a7b58f384130c76775b62dd8",
}


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def verify_carriers() -> dict[str, str]:
    """يتحقّق من بصمةِ كلّ حاملٍ مستورَد. **فشلٌ مغلق**: الانحرافُ يقف بإنذار.

    وليست البصمةُ زينةً في تقرير: هي العقدُ الذي يجعل ترقيةَ تعقُّل حدثًا
    يُرى. فلو تغيّر `RankLattice.meet` — وعليه يقوم قانونُ عدم الترقية —
    لوجب أن تقف السلسلة، لا أن تمضيَ بجبرٍ آخر.
    """
    out: dict[str, str] = {}
    for rel, pinned in PINNED_CARRIERS.items():
        path = _SRC / "taaqqul_slot_geometry" / rel
        if not path.is_file():
            raise owner_alert(
                "حاملٌ من حوامل تعقُّل غيرُ موجود",
                الملف=str(path),
                العلاج="git clone https://github.com/sonaiso/Taaqol-GPT vendor/Taaqol-GPT")
        actual = _sha256(path)
        if actual != pinned:
            raise owner_alert(
                "انحرفت بصمةُ حاملٍ من حوامل تعقُّل — الجبرُ الذي بُني عليه تغيّر",
                الحامل=rel, المثبَّت=pinned[:12], المقيس=actual[:12],
                العلاج="راجع الفرق ثم ثبّت البصمة الجديدة بحكمٍ صريح")
        out[rel] = actual
    return out


#: أدنى إصدار بايثون تحتاجه حواملُ تعقُّل — مقيسٌ لا مقدَّر: مصادرُها تستعمل
#: ``enum.StrEnum`` وهو من ٣٫١١. وأسلوط نفسُه يعمل على ٣٫١٠، فالقيدُ على
#: الجسر وحده ويُعلَن بإنذارٍ مفهوم لا بـ``ImportError`` خام.
MIN_PYTHON = (3, 11)


def _stub_packages() -> None:
    """يسجّل حزمةَ تعقُّل **بلا تنفيذ `__init__`** قبل استيراد الحوامل.

    **الحجّة مقيسة، وقد صُحّح تعليلُها.** كان التعليلُ الأوّل «استيرادُ حاملٍ
    يجرّ محوِّلَ نموذج، وهو أوّلُ سطرٍ في السطح الممنوع» — وهو **باطل**:
    ``ModelClient`` بروتوكولٌ مجرَّد لا محوِّلُ نموذجٍ حقيقيّ، والحدُّ لا
    يُخرق باستيراد اسمٍ. وتعليلٌ باطلٌ يُبقي البابَ مفتوحًا لخطأٍ مشابهٍ في
    موضعٍ آخر، فيُستبدل بالمقيس:

        استيرادُ الحزمة من أعلى  ينفّذ  ٨١ وحدة
        المثبَّتُ ببصمته          ٦ وحدات

    فتثبيتُ ستٍّ وتنفيذُ إحدى وثمانين **يُبطل معنى التثبيت نفسَه**: خمسٌ
    وسبعون وحدةً تتغيّر بلا أن يقف شيء. فتُسجَّل حزمتان فارغتان لهما
    ``__path__`` الصحيح، فيُنفَّذ ما ثُبِّتت بصمتُه لا غير — والعددان
    ``6`` و``81`` مقيسان في تقرير الامتثال لا منقولان.
    """
    import types
    root = _SRC / "taaqqul_slot_geometry"
    for name, path in (("taaqqul_slot_geometry", root),
                       ("taaqqul_slot_geometry.core", root / "core")):
        if name in sys.modules:
            continue
        module = types.ModuleType(name)
        module.__path__ = [str(path)]
        sys.modules[name] = module


def _import_carriers():
    """يستورد الحواملَ من المستودع المُنزَل. فشلُه **مغلق**: إنذارُ مالك.

    ولا يُكتب هنا ``except ImportError`` يُبدّل الحواملَ بصنفٍ محلّيّ: ذاك
    فشلٌ مفتوح — «خطأٌ لا يوقف السلسلة أبدًا» — وهو نقيضُ العقد.
    """
    if not _SRC.is_dir():
        raise owner_alert(
            "مستودعُ تعقُّل غيرُ مُنزَل، والحواملُ لا تُصطنع محلّيًّا",
            المسار=str(VENDOR_ROOT),
            العلاج="git clone --depth 1 https://github.com/sonaiso/Taaqol-GPT "
                   "vendor/Taaqol-GPT")
    if sys.version_info < MIN_PYTHON:
        raise owner_alert(
            "حواملُ تعقُّل تحتاج بايثون أحدث — والحاملُ لا يُقلَّد محلّيًّا",
            المطلوب=".".join(map(str, MIN_PYTHON)),
            المتاح=".".join(map(str, sys.version_info[:3])),
            العلاج="شغّل السلسلة ببايثون ٣٫١١ فأعلى، أو استعمل محاورَ أسلوط "
                   "وحدها فهي تعمل على ٣٫١٠")
    verify_carriers()
    if str(_SRC) not in sys.path:
        sys.path.insert(0, str(_SRC))
    _stub_packages()
    from taaqqul_slot_geometry.core.closure_state import ClosureState
    from taaqqul_slot_geometry.core.failure_taxonomy import FailureCode
    from taaqqul_slot_geometry.core.rank_lattice import Rank, RankLattice
    from taaqqul_slot_geometry.core.residual_policy import (
        Residual,
        ResidualKind,
        ResidualPolicy,
    )
    from taaqqul_slot_geometry.core.trace_ledger import TraceEntryCandidate, TraceLedger
    from taaqqul_slot_geometry.core.transition_state import TransitionState
    return (ClosureState, FailureCode, Rank, RankLattice, Residual, ResidualKind,
            ResidualPolicy, TraceEntryCandidate, TraceLedger, TransitionState)


#: الحواملُ تُستورَد **عند أوّل طلب** لا عند استيراد الوحدة.
#:
#: كان الاستيرادُ يقع في زمن الاستيراد، فصار مجرّدُ `import aslot.cli` يوقف
#: المحرّكَ كلَّه على بايثون ٣٫١٠ — لأن `cli` يستورد محورَ الامتثال، وهو
#: يستورد هذه الوحدة. فادّعاءُ «القيدُ على الجسر وحده» كان **باطلًا في
#: التنفيذ** وإن صحّ في القصد: خمسةُ محاورَ لا شأن لها بتعقُّل كانت تسقط.
#:
#: والكسلُ هنا ليس تحسينَ أداء بل **تصحيحُ حدّ**: من لم يطلب الحاملَ لا
#: يُطالَب بشرطه. وفشلُ الطلب يبقى مغلقًا كما كان.
_CARRIERS: dict[str, object] = {}


def carriers() -> dict[str, object]:
    """الحواملُ المستوردة، مرّةً واحدة. فشلُ الاستيراد **مغلق**."""
    if not _CARRIERS:
        names = ("ClosureState", "FailureCode", "Rank", "RankLattice", "Residual",
                 "ResidualKind", "ResidualPolicy", "TraceEntryCandidate",
                 "TraceLedger", "TransitionState")
        _CARRIERS.update(dict(zip(names, _import_carriers(), strict=True)))
    return _CARRIERS


def __getattr__(name: str):
    """يجعل `from .taaqol import Rank` يعمل، ويؤجّل الاستيرادَ إلى طلبه."""
    if name in ("ClosureState", "FailureCode", "Rank", "RankLattice", "Residual",
                "ResidualKind", "ResidualPolicy", "TraceEntryCandidate",
                "TraceLedger", "TransitionState"):
        return carriers()[name]
    raise AttributeError(name)


# ---------------------------------------------------------------------------
# T-1 — تاكسونومية الرفض المغلقة
# ---------------------------------------------------------------------------

#: كلُّ قيمةٍ هنا **مستخرَجةٌ من مخرجٍ فعليّ** لا من اليد: شُغّلت السلسلة على
#: كامل النصّ وجُرِدت القيمُ الظاهرة في أعمدة الحكم كلِّها. والممنوع الذي
#: نصّت عليه الخطّة — «رمزٌ لا شاهدَ له في مخرج» — مُثبَتٌ بفحصٍ ذاتيّ.
#:
#: والمقابلةُ مع `FailureCode` **ليست ترجمةً حرّة**: ما لم يكن له رمزٌ في
#: جرد تعقُّل المغلق يُترك ``None`` صراحةً ويُرفع إلى المالك، ولا يُلوى رمزٌ
#: قريبٌ ليملأ الفراغ. اختراعُ مقابلٍ أسوأُ من الاعتراف بغيابه.
ASLOT_REFUSALS: dict[str, tuple[str, str | None]] = {
    # ── المحور ١ — التطبيع ──────────────────────────────────────────────
    "NORMALIZED": ("axis1.status", None),
    "NORMALIZED_OWNER_DECISION_REQUIRED": ("axis1.status", None),
    "EXCLUDED_LAFZ_AL_JALALAH": ("axis1.status", None),
    "EXCLUDED_FAWATIH_AL_SUWAR": ("axis1.status", None),
    "STOPPED_OWNER_DECISION_REQUIRED_NO_CARRIER_FOR_A_HARAKA":
        ("axis1.status", "IDENTITY_BROKEN"),
    "MULTIWORD_SURFACE_IN_ONE_CELL": ("axis1.stop", "IDENTITY_BROKEN"),
    # ── المحور ٢ — الحصر ────────────────────────────────────────────────
    "PROVEN": ("axis2.proof", None),
    "NOT_MATCHED": ("axis2.proof", None),
    "UNRESOLVED": ("axis2.proof", None),
    "NOT_A_CLOSED_FORM_VERBAL_OPERATOR": ("axis2.proof", None),
    "ACCEPT": ("verdict", None),
    "BLOCK": ("verdict", None),
    "DEFER": ("verdict", None),
    "OWNER_DECISION_REQUIRED": ("axis2.eligibility", None),
    "CONTINUE": ("axis2.route", None),
    "STOP_CLOSED_FORM": ("axis2.route", None),
    "DEFER_UNRESOLVED_CLOSURE": ("route", None),
    "DEFER_VERBAL_OPERATOR_REGISTRY_TAG": ("route", None),
    # ── المحور ٣ — التقطيع ──────────────────────────────────────────────
    "SYLLABLE_WITHOUT_ONSET": ("axis3.block", "REQUIRED_SLOT_EMPTY"),
    "PATTERN_OUTSIDE_CLOSED_SIX": ("axis3.block", "UNLICENSED_OPENING"),
    # ── المحور ٤ — التقشير ──────────────────────────────────────────────
    "STEM_NOT_FURTHER_PEELABLE": ("axis4.termination", None),
    "CLOSED_REMAINDER": ("axis4.termination", None),
    "DEFER_INITIAL_LETTER_MAY_BE_RADICAL": ("axis4.termination", None),
    "DEFER_ELIDED_LETTER_NOT_RESTORABLE": ("axis4.termination", None),
    "DEFER_REMAINDER_STANDING_UNPROVEN": ("axis4.termination", None),
    "BLOCK_SYLLABLE_BOUNDARY_CROSSED": ("axis4.termination", "UNLICENSED_OPENING"),
    "BLOCK_AXIS_3_REJECTED": ("axis4.termination", "REQUIRED_SLOT_EMPTY"),
    "BLOCK_EMPTY_REMAINDER": ("axis4.termination", "REQUIRED_SLOT_EMPTY"),
}


def unmapped_refusals() -> list[str]:
    """أسماءٌ عندنا لا مقابلَ لها في جرد تعقُّل — تُعلَن ولا تُلوى."""
    return sorted(k for k, (_, code) in ASLOT_REFUSALS.items() if code is None)


def mapped_refusals() -> dict[str, str]:
    """ما له مقابلٌ **موجودٌ فعلًا** في `FailureCode` — يُتحقَّق منه لا يُدَّعى."""
    out: dict[str, str] = {}
    names = {member.value for member in carriers()['FailureCode']}
    for key, (_, code) in ASLOT_REFUSALS.items():
        if code is None:
            continue
        if code not in names:
            raise owner_alert("رمزُ رفضٍ مُدَّعًى ليس في جرد تعقُّل المغلق",
                              الاسم=key, الرمز=code)
        out[key] = code
    return out


# ---------------------------------------------------------------------------
# ما هو موقوفٌ على حكم المالك — لا يُنفَّذ منه شيء
# ---------------------------------------------------------------------------

#: كلُّ بندٍ هنا **يغيّر حكمًا**، وتغييرُ الحكم ليس لي. مذكورةٌ بأسمائها
#: في الخطّة (القسم الخامس)، ومسجّلةٌ هنا لتكون غيابُها مرئيًّا في الكود
#: لا في وثيقةٍ منفصلة.
OWNER_DECISIONS_PENDING: tuple[str, ...] = (
    "T-4:RESIDUAL_KIND_FOR_SEVEN_UNRATIFIED_CLASSES",
    "T-4:TANWEEN_DEFECT_BLOCK_OR_VISIBLE_DEFERRABLE",
    "T-5:GAMMA_CLOSURE_CHANGES_VERDICTS",
    "T-6:FORBIDDEN_LINES_DEMOTE_KATABA_PEEL",
    "T-7:TRANSITION_GATES_BETWEEN_AXES",
    "T-8:DELETE_DUPLICATED_FROZEN_SOURCE_IN_HOKOM",
    "OPEN:ALEF_MADDA_OUTSIDE_AL",
    "OPEN:N2_2_SHADDA_AFTER_AL",
    "OPEN:LAKUM_DEMOTION_IN_CL16",
)

__all__ = [
    "ASLOT_REFUSALS",
    "OWNER_DECISIONS_PENDING",
    "VENDOR_COMMIT",
    "VENDOR_LICENSE",
    "VENDOR_ROOT",
    # الحواملُ تُنشر عبر `carriers()` و`__getattr__` لا هنا: إدراجُها في
    # `__all__` يجعل `import *` يستوردها فيسقط الكسلُ الذي هو الحدّ نفسُه.
    "anchor",
    "carriers",
    "mapped_refusals",
    "parent_anchor",
    "unmapped_refusals",
    "verify_carriers",
]
