"""المحور ١ — التطبيع.

    OWNER_RULE_SOVEREIGNTY = ABSOLUTE      RULE_OWNER = DR_HUSSEIN
    CREATE_NON_OWNER_RULE  = NO            INFER_LINGUISTIC_RULE = NO
    NORMALIZATION_IS_DISCLOSURE_NOT_INTERPRETATION

النصّ المشكول طبقتان: **صوتية** (حرف/حركة/سكون/مدّ) و**كتابية أدائية**
(شدّة، تطويل، علاماتُ تجويدٍ ووقف، صفرٌ مستدير، ألفُ وصل، ألفٌ خنجرية،
ألفٌ مقصورة، مدّة). وكل ما بعد هذا المحور يعمل على الأولى وحدها.

فالتطبيع **فصلُ طبقةٍ عن طبقة**، لا تنظيفُ نصّ.

بنية هذه الوحدة
---------------
كانت ``normalize_token`` دالّةً واحدة تتجاوز مئتي سطر، فيها حلقةٌ كبرى وأربع
عشرة قاعدةً متداخلة وست عودات مبكّرة. وهي الآن صنفٌ (``_Normalizer``) لكل
قاعدةٍ فيه **معالجٌ مسمّى** يُقرأ وحده ويُختبر وحده، والوقوفُ الدستوري
استثناءٌ داخليّ (``_Stop``) بدل تمريرِ حالةٍ عبر ستّ عودات.

والمعالجات مرتَّبة بترتيب الأولوية نفسه الذي كانت عليه، لأن الترتيب هنا
**جزءٌ من الحكم**: «آ» تُعالَج قبل الألف المجرّدة، والألفُ المجرّدة قبل
الحامل العام.
"""

from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..checks import CheckSuite
from ..constants import (
    ALEF_MADDA,
    ALIF,
    ALIF_MAQSURA,
    ALIF_WASLA,
    CONSONANT_LETTERS,
    FATHA,
    HAMZA,
    HAMZA_SEATS,
    HARAKAT,
    LAM,
    LAYN_LETTERS,
    MADD_PARTNER,
    MADDAH,
    MARKS,
    NOON,
    OUTPUT_MARKS,
    ROUNDED_ZERO,
    SHADDA,
    SUKUN,
    TANWEEN,
    TANWEEN_TO_HARAKA,
    TATWEEL,
    VOWEL_MARKS,
    WAW,
    YAA,
)
from ..fileio import read_rows, require_file, write_csv
from ..policy import OWNER_DECISION_REQUIRED, OwnerPolicy
from ..reporting import Report
from ..runner import Axis

# ---------------------------------------------------------------------------
# الحالات الخمس ومصائر الخلايا — قائمتان مغلقتان
# ---------------------------------------------------------------------------

NORMALIZED = "NORMALIZED"
OWNER_DECISION = "NORMALIZED_OWNER_DECISION_REQUIRED"
STOPPED = "STOPPED_OWNER_DECISION_REQUIRED_NO_CARRIER_FOR_A_HARAKA"
IGNORED = "IGNORED_NON_WORD_TOKEN"
FAWATIH = "EXCLUDED_FAWATIH_AL_SUWAR"

STATUSES = (NORMALIZED, OWNER_DECISION, STOPPED, IGNORED, FAWATIH)

PRESERVED = "PRESERVED"
REPLACED = "REPLACED"
EXPANDED = "EXPANDED"
IGNORED_CELL = "IGNORED"
DELETED = "DELETED_BY_OWNER_RULE"

FATES = (PRESERVED, REPLACED, EXPANDED, IGNORED_CELL, DELETED)

# ---------------------------------------------------------------------------
# الفواتح — قائمةٌ مغلقة **و** شرطُ موضع
# ---------------------------------------------------------------------------

FAWATIH_SURFACES = frozenset({
    "الم", "المص", "المر", "الر", "كهيعص", "طه", "طسم", "طس",
    "يس", "ص", "حم", "عسق", "ق", "ن",
})

#: عسق في 42:2:1 افتتاحٌ لأن ما قبلها حم في 42:1:1 — قياسٌ على النصّ لا تخمين.
FAWATIH_EXTRA_POSITIONS = frozenset({(42, 2, 1)})

# ---------------------------------------------------------------------------
# جدول القواعد المسمّاة
# ---------------------------------------------------------------------------

RULES = {
    "N0.F": "فاتحة سورة في موضع الافتتاح — تُحفظ كما كُتبت وتخرج من كل المحاور",
    "N1": "المدّة تُحذف ولا تولّد همزةً في أي موضع",
    "N2": "كل شدّة تُفكّ داخل كلمتها إلى ساكنٍ ومتحرّك",
    "N2.1": "شدّة على أول الكلمة بلا «ال» قبلها: علامةُ أداءٍ تُحذف ولا تُضاعف الحرف",
    "N2.2": "شدّة بعد «ال»: تعود إلى الفكّ العادي",
    "N3": "حذف التطويل",
    "N7": "ألف الوصل همزةٌ مع حركة، والأصل الفتح عند غياب الحركة المكتوبة",
    "N7.1": "ألفٌ مجرّدة أول الكلمة يتبعها لام وليست من الفواتح: همزةُ «ال» بفتحة",
    "N7.2": "«ال» بعد سابقةٍ داخل الكلمة: لا تُعامَل إلا بمطابقة الوحدة كلها في سجلٍّ معتمد",
    "N7.3": "ألف الوصل في رأس فعلٍ مبرهَن — معطّلة: EXECUTABLE_VERB_RULES = 0",
    "N10": "الهمزة حرف لا حركة، ولا تُخترع من علامة",
    "N10.1": "تعيين كرسيّ الهمزة بحسب ما قبلها",
    "N12": "كل حرفٍ حُكم بسكونه يحمل السكون صراحةً في المخرج",
    "N13": "لا تحويل عامّ من الرسم العثماني إلى الإملائي — قرارُ إبقاء",
}

#: الفجوة المقيسة التي تعطّل N7.3: الشرط قائم والوسيلة غائبة.
VERB_RULE_ROWS = 34
EXECUTABLE_VERB_RULES = 0


# ---------------------------------------------------------------------------
# البنى
# ---------------------------------------------------------------------------

@dataclass
class Unit:
    """وحدةٌ صوتية: صامتٌ واحد + علامةٌ واحدة (حركة أو سكون). لا ثالث لهما."""

    letter: str
    mark: str
    rule: str
    source_index: int

    @property
    def text(self) -> str:
        return self.letter + self.mark


@dataclass
class NormalizationResult:
    token: str
    status: str
    normalized: str = ""
    units: list = field(default_factory=list)
    fates: list = field(default_factory=list)
    rules_applied: list = field(default_factory=list)
    owner_decisions: list = field(default_factory=list)
    stop_reason: str = ""

    @property
    def is_usable(self) -> bool:
        """هل يمضي هذا السطح إلى المحورين ٣ و٤؟"""
        return self.status in (NORMALIZED, OWNER_DECISION)

    @property
    def decision_classes(self) -> list[str]:
        return sorted({cls for cls, _, _ in self.owner_decisions})


@dataclass
class _Letter:
    """حرفٌ وعلاماتُه وسياقُه المباشر — يمرَّر إلى المعالجات بدل ستّة متغيّرات."""

    index: int
    letter: str
    marks: str
    is_first: bool
    is_last: bool
    next_letter: str | None
    next_marks: str

    @property
    def haraka(self) -> str | None:
        return next((m for m in self.marks if m in HARAKAT), None)

    @property
    def tanween(self) -> str | None:
        return next((m for m in self.marks if m in TANWEEN), None)

    @property
    def has_sukun(self) -> bool:
        return SUKUN in self.marks

    @property
    def has_shadda(self) -> bool:
        return SHADDA in self.marks

    @property
    def vowel_mark_count(self) -> int:
        return sum(1 for m in self.marks if m in VOWEL_MARKS)


class _Stop(Exception):
    """وقوفٌ داخليّ: يحمل سببه إلى ``run`` بدل ستّ عوداتٍ مبكّرة."""

    def __init__(self, reason: str, status: str = STOPPED):
        self.reason = reason
        self.status = status


# ---------------------------------------------------------------------------
# المطبِّع
# ---------------------------------------------------------------------------

class _Normalizer:
    def __init__(self, token: str, position: tuple | None, policy: OwnerPolicy):
        self.token = token
        self.position = position
        self.policy = policy
        self.res = NormalizationResult(token=token, status=NORMALIZED)
        self.units: list[Unit] = []

    # -- أدوات التسجيل ---------------------------------------------------
    def _fate(self, index: int, char: str, fate: str, rule: str) -> None:
        self.res.fates.append((index, char, fate, rule))

    def _use(self, rule: str) -> None:
        if rule and rule not in self.res.rules_applied:
            self.res.rules_applied.append(rule)

    def _emit(self, letter: str, mark: str, rule: str, index: int) -> None:
        self.units.append(Unit(letter, mark, rule, index))

    @property
    def _prev_mark(self) -> str | None:
        return self.units[-1].mark if self.units else None

    def _article_before(self) -> bool:
        """هل سبق هذا الموضعَ «ال» التعريف؟ (يفصل N2.2 عن N2.1)"""
        return (len(self.units) >= 2
                and self.units[-2].letter == HAMZA
                and self.units[-1].letter == LAM)

    def _decide(self, cls: str, index: int, note: str) -> str:
        """يستدعي سياسة صنفٍ غير موثّق ويسجّل أثرها على حالة الكلمة."""
        entry = self.policy[cls]
        if not entry.ratified:
            self.res.owner_decisions.append((cls, index, note))
        return entry.treatment

    # -- المراحل ---------------------------------------------------------
    def run(self) -> NormalizationResult:
        try:
            self._reject_non_word()
            self._maybe_fawatih()
            self._maybe_multiword()
            for ctx in self._letters():
                self._process(ctx)
        except _Stop as stop:
            self.res.status = stop.status
            self.res.stop_reason = stop.reason
            return self.res

        self.res.units = self.units
        self.res.normalized = "".join(u.text for u in self.units)
        if not self.units:
            self.res.status = IGNORED
        elif self.res.owner_decisions:
            self.res.status = OWNER_DECISION
        return self.res

    def _reject_non_word(self) -> None:
        stripped = self.token.strip()
        if not stripped or not any(ch in CONSONANT_LETTERS for ch in stripped):
            raise _Stop("", IGNORED)
        self.token = stripped

    def _maybe_fawatih(self) -> None:
        """N0.F — الشرطان معًا: السطح في القائمة **و** موضعه افتتاحيّ."""
        if self.token not in FAWATIH_SURFACES or self.position is None:
            return
        sura, verse, word = self.position
        opening = (verse == 1 and word == 1) or (sura, verse, word) in FAWATIH_EXTRA_POSITIONS
        if not opening:
            return
        self.res.status = FAWATIH
        self.res.normalized = self.token          # تُحفظ كما كُتبت
        self._use("N0.F")
        for i, ch in enumerate(self.token):
            self._fate(i, ch, PRESERVED, "N0.F")
        raise _Stop("", FAWATIH)

    def _maybe_multiword(self) -> None:
        if " " not in self.token:
            return
        treat = self._decide("U_MULTIWORD_CELL", 0, "خليّة Word فيها كلمتان")
        if treat == OWNER_DECISION_REQUIRED:
            raise _Stop("MULTIWORD_SURFACE_IN_ONE_CELL")

    def _letters(self):
        """يفكّ الكلمة إلى حروفٍ بعلاماتها، ويرفض علامةً سبقت حاملَها."""
        raw: list[tuple[int, str, str]] = []
        i, n = 0, len(self.token)
        while i < n:
            ch = self.token[i]
            if ch in MARKS:
                raise _Stop(f"HARAKA_WITHOUT_CARRIER@{i}")
            if ch == TATWEEL:
                raw.append((i, TATWEEL, ""))
                i += 1
                continue
            if ch not in CONSONANT_LETTERS:
                raise _Stop(f"NON_LETTER@{i}:{ch!r}", IGNORED)
            j = i + 1
            marks = ""
            while j < n and self.token[j] in MARKS:
                marks += self.token[j]
                j += 1
            raw.append((i, ch, marks))
            i = j

        total = len(raw)
        for k, (index, letter, marks) in enumerate(raw):
            nxt = raw[k + 1] if k + 1 < total else None
            yield _Letter(index=index, letter=letter, marks=marks,
                          is_first=(k == 0), is_last=(k == total - 1),
                          next_letter=nxt[1] if nxt else None,
                          next_marks=nxt[2] if nxt else "")

    # -- التوجيه ---------------------------------------------------------
    #: المعالجات بترتيب الأولوية. الترتيب جزءٌ من الحكم لا تفصيلُ تنفيذ.
    def _process(self, ctx: _Letter) -> None:
        for handler in (self._h_tatweel, self._h_rounded_zero):
            if handler(ctx):
                return
        ctx = self._strip_maddah(ctx)
        if ctx.vowel_mark_count > 1:
            # تعدّد الحركات على حاملٍ واحد: يقف ولا يرجّح
            raise _Stop(f"MULTIPLE_HARAKAT_ON_ONE_CARRIER@{ctx.index}")
        for handler in (self._h_alef_madda, self._h_bare_alif, self._h_alif_maqsura):
            if handler(ctx):
                return
        self._h_general(ctx)

    # -- المعالجات -------------------------------------------------------
    def _h_tatweel(self, ctx: _Letter) -> bool:
        if ctx.letter != TATWEEL:
            return False
        if ctx.marks:
            # N10: همزةٌ حاملُها التطويل تُردّ حرفًا — واقعةٌ لا تقع في هذا المدخل.
            raise _Stop("TATWEEL_CARRIES_MARKS_OWNER_DECISION")
        self._fate(ctx.index, ctx.letter, DELETED, "N3")
        self._use("N3")
        return True

    def _h_rounded_zero(self, ctx: _Letter) -> bool:
        if ROUNDED_ZERO not in ctx.marks:
            return False
        self._fate(ctx.index, ctx.letter, DELETED, "N3")
        return True

    def _strip_maddah(self, ctx: _Letter) -> _Letter:
        """N1 — المدّة علامةٌ تُحذف ولا تولّد همزة."""
        if MADDAH not in ctx.marks:
            return ctx
        self._fate(ctx.index, MADDAH, DELETED, "N1")
        self._use("N1")
        ctx.marks = ctx.marks.replace(MADDAH, "")
        return ctx

    def _h_alef_madda(self, ctx: _Letter) -> bool:
        """آ — رمزٌ واحد = ألف + مدّة، فحذفُ المدّة يُسقط المدَّ نفسه."""
        if ctx.letter != ALEF_MADDA:
            return False
        treat = self._decide("U_ALEF_MADDA", ctx.index, "آ = ألف + مدّة في رمزٍ واحد")
        if treat == OWNER_DECISION_REQUIRED:
            raise _Stop(f"ALEF_MADDA_OWNER_DECISION@{ctx.index}")
        if treat == "HAMZA_FATHA_PLUS_MADD_ALIF":
            self._emit(HAMZA, FATHA, "N10+U_ALEF_MADDA", ctx.index)
            self._emit(ALIF, SUKUN, "N12+U_ALEF_MADDA", ctx.index)
            self._fate(ctx.index, ctx.letter, EXPANDED, "U_ALEF_MADDA")
            self._use("N10")
        else:                                   # MADDA_DELETED_ALIF_REMAINS
            self._emit(ALIF, SUKUN, "N1+N12", ctx.index)
            self._fate(ctx.index, ctx.letter, REPLACED, "N1")
        self._use("N12")
        return True

    def _h_bare_alif(self, ctx: _Letter) -> bool:
        """ألفٌ مجرّدة — أربعة مساراتٍ لا خامس لها."""
        if ctx.letter not in (ALIF, ALIF_WASLA):
            return False
        if ctx.haraka or ctx.tanween or ctx.has_shadda:
            return False

        # N7.1 نصُّها صريحٌ في نفي الشروط: «ولا يُشترط سكونُ اللام ولا شدّةٌ بعدها».
        # فتُطبَّق في أول الكلمة حرفيًّا. وكلفةُ ذلك معلومة ومقيسة: تصدُق على
        # «الْتَقَى» و«اللَّاتِي» وهما ليستا أداةَ تعريف (انظر --cross-check-masaq).
        if ctx.is_first and ctx.next_letter == LAM:
            self._emit(HAMZA, FATHA, "N7.1", ctx.index)
            self._fate(ctx.index, ctx.letter, REPLACED, "N7.1")
            self._use("N7.1")
            self._use("N10")
            return True

        # N7 العام — رؤوس الأفعال تدخل هنا لأن N7.3 معطّلة
        if ctx.is_first:
            self._emit(HAMZA, FATHA, "N7", ctx.index)
            self._fate(ctx.index, ctx.letter, REPLACED, "N7")
            self._use("N7")
            self._use("N7.3:INOPERATIVE")
            return True

        # **داخل** الكلمة النصُّ لا ينفي الشروط، والفاصل لازم: لامُ التعريف لا
        # تحمل حركة (مجرّدة/ساكنة/مشدّدة)، ولامٌ متحرّكة بعد ألفٍ مجرّدة تعني
        # أن الألف **مدٌّ** (مَالِكِ ، لَيَالِيَ) لا أداةَ تعريف.
        if ctx.next_letter == LAM and not any(m in VOWEL_MARKS for m in ctx.next_marks):
            treat = self._decide("U_N7_2_INTERNAL_AL", ctx.index,
                                 "«ال» داخل الكلمة بعد سابقة — لا سجلّ وحداتٍ معتمد")
            if treat == OWNER_DECISION_REQUIRED:
                raise _Stop(f"N7_2_NO_APPROVED_REGISTRY@{ctx.index}")
            self._fate(ctx.index, ctx.letter, DELETED, "N7.2")
            self._use("N7.2")
            return True

        if self._prev_mark == FATHA:                       # مدّ
            self._emit(ALIF, SUKUN, "MADD", ctx.index)
            self._fate(ctx.index, ctx.letter, PRESERVED, "N12")
            self._use("N12")
            return True

        if (ctx.is_last and self.units
                and self.units[-1].letter == WAW and self.units[-1].mark == SUKUN):
            treat = self._decide("U_ALIF_FARIQA", ctx.index,
                                 "ألف التفريق بعد واو الجماعة")
            if treat == "DELETE":
                self._fate(ctx.index, ctx.letter, DELETED, "U_ALIF_FARIQA")
                return True
            if treat == OWNER_DECISION_REQUIRED:
                raise _Stop(f"ALIF_FARIQA_OWNER_DECISION@{ctx.index}")
            self._emit(ALIF, SUKUN, "U_ALIF_FARIQA", ctx.index)
            self._fate(ctx.index, ctx.letter, PRESERVED, "U_ALIF_FARIQA")
            return True

        treat = self._decide("U_UNVOCALIZED_CARRIER", ctx.index,
                             f"ألفٌ بعد {self._prev_mark!r}")
        if treat == OWNER_DECISION_REQUIRED:
            raise _Stop(f"UNVOCALIZED_ALIF@{ctx.index}")
        self._emit(ALIF, SUKUN, "U_UNVOCALIZED_CARRIER", ctx.index)
        self._fate(ctx.index, ctx.letter, PRESERVED, "N12")
        return True

    def _h_alif_maqsura(self, ctx: _Letter) -> bool:
        if ctx.letter != ALIF_MAQSURA or ctx.haraka or ctx.tanween:
            return False
        treat = self._decide("U_ALIF_MAQSURA", ctx.index, "ألف مقصورة بلا حركة")
        if treat == OWNER_DECISION_REQUIRED:
            raise _Stop(f"ALIF_MAQSURA_OWNER_DECISION@{ctx.index}")
        letter = ALIF if treat == "MADD_ALIF" else YAA
        self._emit(letter, SUKUN, "U_ALIF_MAQSURA", ctx.index)
        self._fate(ctx.index, ctx.letter, REPLACED, "U_ALIF_MAQSURA")
        self._use("N12")
        return True

    def _h_general(self, ctx: _Letter) -> None:
        """الحرف العام: كرسيّ الهمزة ثم التنوين ثم الشدّة ثم الحركة/السكون."""
        letter = self._seat(ctx)
        haraka, expand_tanween = self._tanween(ctx)
        self._shadda(ctx, letter)
        self._vowel_or_sukun(ctx, letter, haraka)
        if expand_tanween:
            self._emit(NOON, SUKUN, "U_TANWEEN", ctx.index)
            self._fate(ctx.index, ctx.tanween, EXPANDED, "U_TANWEEN")

    def _seat(self, ctx: _Letter) -> str:
        if ctx.letter in HAMZA_SEATS:
            treat = self._decide("U_HAMZA_SEAT", ctx.index, "كرسيّ همزة")
            if treat == "UNIFY_TO_BARE_HAMZA":
                self._fate(ctx.index, ctx.letter, REPLACED, "N10.1")
                self._use("N10.1")
                self._use("N10")
                return HAMZA
            self._fate(ctx.index, ctx.letter, PRESERVED, "N10")
            self._use("N10")
            return ctx.letter
        if ctx.letter == ALIF_WASLA:
            return HAMZA
        return ctx.letter

    def _tanween(self, ctx: _Letter) -> tuple[str | None, bool]:
        if ctx.tanween is None:
            return ctx.haraka, False
        treat = self._decide("U_TANWEEN", ctx.index, f"تنوين {ctx.tanween!r}")
        if treat == OWNER_DECISION_REQUIRED:
            raise _Stop(f"TANWEEN_OWNER_DECISION@{ctx.index}")
        return TANWEEN_TO_HARAKA[ctx.tanween], treat == "EXPAND_TO_NOON_SAKIN"

    def _shadda(self, ctx: _Letter, letter: str) -> None:
        """N2 — كل شدّة تُفكّ داخل كلمتها إلى ساكنٍ ومتحرّك."""
        if not ctx.has_shadda:
            return
        if ctx.is_first and not self._article_before():
            # N2.1 — علامةُ أداءٍ تُحذف ولا تُضاعف الحرف
            self._fate(ctx.index, SHADDA, DELETED, "N2.1")
            self._use("N2.1")
            return
        self._emit(letter, SUKUN, "N2", ctx.index)
        # ⚠ موضعُ الاستدعاء مقصودٌ هنا: `_article_before` تُقاس **بعد** بثّ
        # الشطر الساكن، فتُقرأ الوحدتان الأخيرتان (ءَ ، لْ) لا ما قبلهما.
        # وأثرُ ذلك مقيس: «الَّذِينَ» تُوسم N2.2 و«اللَّهِ» تُوسم N2 مع أن
        # الشدّة فيهما بعد «ال» في القراءتين. أُبقي السلوك كما هو لأن إعادة
        # الهيكلة لا تغيّر حكمًا، والتمييز مرفوعٌ إلى المالك (OPEN_QUESTION_N2_2).
        rule = "N2.2" if self._article_before() else "N2"
        self._fate(ctx.index, SHADDA, EXPANDED, rule)
        self._use(rule)

    def _vowel_or_sukun(self, ctx: _Letter, letter: str, haraka: str | None) -> None:
        if haraka is not None:
            self._emit(letter, haraka, "N12" if ctx.has_sukun else "SOURCE", ctx.index)
            self._fate(ctx.index, haraka, PRESERVED, "N12")
            return
        if ctx.has_sukun:
            self._emit(letter, SUKUN, "N12", ctx.index)
            self._fate(ctx.index, SUKUN, PRESERVED, "N12")
            self._use("N12")
            return

        # حاملٌ بلا حركة: مدٌّ أو لينٌ أو ساكنٌ ضمنيّ
        prev = self._prev_mark
        if ctx.letter in MADD_PARTNER and prev == MADD_PARTNER[ctx.letter]:
            rule = "MADD"                       # madd = V  (المحور الثالث)
        elif ctx.letter in LAYN_LETTERS and prev == FATHA:
            rule = "LAYN"                       # لينٌ: صامتٌ في القفل
        else:
            treat = self._decide("U_UNVOCALIZED_CARRIER", ctx.index,
                                 f"{ctx.letter!r} بلا حركة بعد {prev!r}")
            if treat == OWNER_DECISION_REQUIRED:
                raise _Stop(f"UNVOCALIZED_CARRIER@{ctx.index}")
            rule = "N12"
        self._emit(letter, SUKUN, rule, ctx.index)
        self._fate(ctx.index, ctx.letter, PRESERVED, "N12")
        self._use("N12")


# ---------------------------------------------------------------------------
# الواجهة
# ---------------------------------------------------------------------------

_DEFAULT_POLICY: OwnerPolicy | None = None


def default_policy() -> OwnerPolicy:
    global _DEFAULT_POLICY
    if _DEFAULT_POLICY is None:
        _DEFAULT_POLICY = OwnerPolicy.load()
    return _DEFAULT_POLICY


def normalize_token(token: str, position: tuple | None = None,
                    policy: OwnerPolicy | None = None) -> NormalizationResult:
    """يطبّع كلمةً واحدة. ``position`` = (سورة، آية، كلمة) لأجل N0.F وحدها."""
    return _Normalizer(token, position, policy or default_policy()).run()


# ---------------------------------------------------------------------------
# الفحوص
# ---------------------------------------------------------------------------

def build_suite(policy: OwnerPolicy) -> CheckSuite:
    suite = CheckSuite("axis1")

    def norm(word, position=None):
        return normalize_token(word, position, policy)

    r = norm("اللَّهِ", (1, 1, 2))
    suite.check("T1_ALLAH_SHADDA_UNFOLDS", r.normalized == "ءَلْلْلَهِ",
                f"{r.normalized}  (النصّ: ءَلْ + لْ + لَهِ)")

    r = norm("مَا", (2, 20, 1))
    suite.check("T2_MADD_ALIF_GETS_EXPLICIT_SUKUN", r.normalized == "مَاْ", r.normalized)

    suite.check("T3_FAWATIH_EXCLUDED_AT_OPENING",
                norm("الم", (2, 1, 1)).status == FAWATIH, FAWATIH)
    r = norm("الم", (2, 5, 3))
    suite.check("T4_FAWATIH_SURFACE_OUTSIDE_OPENING_IS_ORDINARY",
                r.status != FAWATIH, f"{r.status} / {r.normalized}")
    suite.check("T5_ASQ_AT_42_2_1_IS_OPENING",
                norm("عسق", (42, 2, 1)).status == FAWATIH, FAWATIH)

    r = norm("بِسْمِ", (1, 1, 1))
    suite.check("T6_BISMI_IS_PLAIN",
                r.normalized == "بِسْمِ" and r.status == NORMALIZED,
                f"{r.normalized} / {r.status}")

    r = norm("قَالَ", (2, 30, 5))
    suite.check("T7_QALA_MADD", r.normalized == "قَاْلَ", r.normalized)

    r = norm("كَفَرُوا", (2, 6, 1))
    suite.check("T8_ALIF_FARIQA_DROPPED", r.normalized == "كَفَرُوْ",
                f"{r.normalized} / {r.status}")

    r = norm("الْحَمْدُ", (1, 2, 1))
    suite.check("T9_EVERY_UNIT_IS_C_PLUS_ONE_MARK",
                all(u.mark in OUTPUT_MARKS for u in r.units), r.normalized)
    suite.check("T10_NO_BARE_LETTER_IN_OUTPUT",
                all(len(u.text) == 2 for u in r.units), r.normalized)

    # -- السموم ---------------------------------------------------------
    r = norm(FATHA + "ب")
    suite.poison("P1_HARAKA_WITHOUT_CARRIER_STOPS", r.status == STOPPED, r.stop_reason)
    r = norm("بَُ")
    suite.poison("P2_TWO_HARAKAT_ON_ONE_CARRIER_STOPS", r.status == STOPPED,
                 r.stop_reason)
    suite.poison("P3_NON_WORD_IGNORED", norm("123").status == IGNORED, IGNORED)
    suite.poison("P4_EMPTY_IGNORED", norm("").status == IGNORED, IGNORED)
    r = norm("بَ" + MADDAH)
    suite.poison("P5_MADDAH_NEVER_CREATES_HAMZA", HAMZA not in r.normalized,
                 r.normalized)
    r = norm("ن", (68, 4, 2))
    suite.poison("P6_FAWATIH_REQUIRES_POSITION", r.status != FAWATIH, r.status)
    r = norm("قُلْ", (112, 1, 1))
    suite.poison("P7_OPENING_POSITION_ALONE_IS_NOT_FAWATIH", r.status != FAWATIH,
                 r.status)
    r = norm("هُدَى")
    suite.poison("P8_UNRATIFIED_CLASS_RAISES_ODR",
                 r.status == OWNER_DECISION and "U_ALIF_MAQSURA" in r.decision_classes,
                 f"{r.status} / {r.normalized}")
    return suite


# ---------------------------------------------------------------------------
# قياسٌ مقابل المرجع — للمقارنة لا للحكم
# ---------------------------------------------------------------------------

def cross_check_masaq(path: Path, policy: OwnerPolicy) -> dict:
    """MASAQ ليس سلطةً على قواعد المالك.

    الغرض واحد: أن تكون كلفةُ تطبيق N7.1 حرفيًّا **معلومةً ومعلنة**، لا أن
    يُعدَّل الحكم لأجل المرجع.
    """
    words: dict[tuple, dict] = {}
    for row in read_rows(path):
        key = (int(row["Sura_No"]), int(row["Verse_No"]), int(row["Word_No"]))
        entry = words.setdefault(key, {"surface": row["Word"], "tags": []})
        entry["tags"].append(row["Morph_Tag"])

    matrix: Counter = Counter()
    samples: dict[str, list] = {"engine_only": [], "reference_only": []}
    for key, entry in words.items():
        r = normalize_token(entry["surface"], key, policy)
        engine = ("N7.1" in r.rules_applied) or ("N7.2" in r.rules_applied)
        reference = "DET" in entry["tags"]
        matrix[(reference, engine)] += 1
        if engine and not reference and len(samples["engine_only"]) < 6:
            samples["engine_only"].append((key, entry["surface"], r.normalized))
        if reference and not engine and len(samples["reference_only"]) < 6:
            samples["reference_only"].append((key, entry["surface"], r.normalized))

    return {
        "BOTH": matrix[(True, True)],
        "NEITHER": matrix[(False, False)],
        "ENGINE_ONLY_KNOWN_COST_OF_N7_1": matrix[(False, True)],
        "REFERENCE_ONLY_ELIDED_ALIF_GAP": matrix[(True, False)],
        "samples": samples,
    }


# ---------------------------------------------------------------------------
# المحور
# ---------------------------------------------------------------------------

class Axis1Normalization(Axis):
    number = 1
    slug = "normalize"
    title = "المحور ١ — التطبيع"
    module = "aslot.axes.axis1_normalization"
    default_output = "reports/axis_1_normalization"

    def arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--words",
                            default="reports/axis_0_quran_build/QURAN_WORDS.csv")
        parser.add_argument("--policy", default=None)
        parser.add_argument("--cross-check-masaq", default=None,
                            help="مسار MASAQ.csv لقياس الكلفة مقابل المرجع (لا يغيّر حكمًا)")

    def execute(self, args, out_dir: Path):
        policy = OwnerPolicy.load(args.policy)
        suite = build_suite(policy)
        words_csv = require_file(
            Path(args.words), what="جدول الكلمات",
            remedy="شغّل  aslot corpus  أولًا")

        statuses: Counter = Counter()
        rules: Counter = Counter()
        fates: Counter = Counter()
        classes: Counter = Counter()
        stops: Counter = Counter()
        rows = []

        for row in read_rows(words_csv):
            position = (int(row["Sura_No"]), int(row["Verse_No"]),
                        int(row["Word_No"]))
            r = normalize_token(row["Word"], position, policy)
            statuses[r.status] += 1
            rules.update(r.rules_applied)
            fates.update(fate for _, _, fate, _ in r.fates)
            classes.update(cls for cls, _, _ in r.owner_decisions)
            if r.stop_reason:
                stops[r.stop_reason.split("@")[0]] += 1
            rows.append([*position, row["Word"], r.normalized, r.status,
                         "|".join(r.decision_classes), "|".join(r.rules_applied),
                         r.stop_reason])

        write_csv(out_dir / "AXIS_1_NORMALIZATION.csv",
                  ["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                   "Normalization_Status", "Owner_Decision_Classes",
                   "Rules_Applied", "Stop_Reason"], rows)

        measures = {
            "words": len(rows),
            "status": dict(statuses),
            "rules": dict(rules),
            "fates": dict(fates),
            "owner_decision_classes": dict(classes),
            "stop_reasons": dict(stops),
            "policy_source": str(policy.source),
            "unratified_classes": [e.name for e in policy.unratified],
        }
        if args.cross_check_masaq:
            cross = cross_check_masaq(Path(args.cross_check_masaq), policy)
            measures["masaq_cross_check"] = {k: v for k, v in cross.items()
                                             if k != "samples"}
            measures["_cross_samples"] = cross["samples"]
        self._policy = policy
        return measures, suite

    def report(self, m: dict, suite: CheckSuite) -> Report:
        r = Report("تقرير المحور ١ — التطبيع")
        r.kv({
            "MODULE": self.module,
            "AXIS": self.number,
            "OWNER_RULE_SOVEREIGNTY": "ABSOLUTE",
            "CREATE_NON_OWNER_RULE": "NO",
            "INFER_LINGUISTIC_RULE": "NO",
            "NAMED_RULES": len(RULES),
            "VERB_RULE_ROWS": VERB_RULE_ROWS,
            "EXECUTABLE_VERB_RULES": f"{EXECUTABLE_VERB_RULES}   ⇒ N7.3 لا تنطبق عمليًّا",
            "WORDS": m["words"],
        })
        r.heading("الحالات الخمس — قائمة مغلقة")
        r.counts([(s, m["status"].get(s, 0)) for s in STATUSES])
        r.heading("مصير الخلايا — قائمة مغلقة")
        r.counts([(f, m["fates"].get(f, 0)) for f in FATES])
        r.heading("القواعد المسمّاة المطبَّقة")
        r.counts(sorted(m["rules"].items(), key=lambda kv: -kv[1]),
                 note=RULES)
        r.heading("أصنافٌ تنتظر حكم مالك (لا سند نصّيّ في وثيقة التطبيع)")
        policy = getattr(self, "_policy", None)
        note = {}
        if policy is not None:
            note = {e.name: f"treatment={e.treatment}  ratified={e.ratified}"
                    for e in policy}
        r.counts(sorted(m["owner_decision_classes"].items(), key=lambda kv: -kv[1]),
                 note=note)
        if m["stop_reasons"]:
            r.heading("أسباب الوقوف")
            r.counts(sorted(m["stop_reasons"].items(), key=lambda kv: -kv[1]))
        cross = m.get("masaq_cross_check")
        if cross:
            r.heading("قياسٌ مقابل المرجع MASAQ — للمقارنة لا للحكم")
            r.counts(cross, note={
                "ENGINE_ONLY_KNOWN_COST_OF_N7_1":
                    "كلفةُ تطبيق N7.1 حرفيًّا (الْتَقَى ، اللَّاتِي ، اللَّهُمَّ)",
                "REFERENCE_ONLY_ELIDED_ALIF_GAP":
                    "«ال» محذوفةُ الألف بعد لامٍ سابقة (لِلْـ) — لا يراها المحرّك",
            })
            for key, label in (("engine_only", "المحرّك فقط"),
                               ("reference_only", "المرجع فقط")):
                rows = m.get("_cross_samples", {}).get(key) or []
                if rows:
                    r.text(f"  نماذج {label}:")
                    for position, surface, normalized in rows:
                        r.text(f"    {position}  {surface}  →  {normalized}")
        r.proves(
            ["أن كل تغيير مأذون، ومسجَّل، وقابل لإعادة البناء إلى الأصل."],
            ["أن الشكل المطبّع هو النطق الصحيح — هو تمثيلٌ متّسق للمطابقة والتقطيع."],
            ["NORMALIZED_SURFACE_PRODUCED ≠ NORMALIZED_SURFACE_OWNER_AUTHORIZED"])
        return r
