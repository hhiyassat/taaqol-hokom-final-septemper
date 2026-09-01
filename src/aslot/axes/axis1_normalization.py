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
import unicodedata
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
    DAGGER_ALIF,
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
    SUN_LETTERS,
    TANWEEN,
    TANWEEN_TO_HARAKA,
    TATWEEL,
    VOWEL_MARKS,
    WAW,
    YAA,
)
from ..fileio import read_rows, require_file, write_csv
from ..jalalah import JalalahRegistry, default_registry
from ..policy import OWNER_DECISION_REQUIRED, OwnerPolicy
from ..reporting import Report
from ..runner import Axis
from ..uthmani import ALL_SIGNS, COMBINING_HAMZA, PERFORMANCE, PHONETIC, SIGNS, uncovered_marks

# ---------------------------------------------------------------------------
# الحالات الخمس ومصائر الخلايا — قائمتان مغلقتان
# ---------------------------------------------------------------------------

NORMALIZED = "NORMALIZED"
OWNER_DECISION = "NORMALIZED_OWNER_DECISION_REQUIRED"
STOPPED = "STOPPED_OWNER_DECISION_REQUIRED_NO_CARRIER_FOR_A_HARAKA"
IGNORED = "IGNORED_NON_WORD_TOKEN"
FAWATIH = "EXCLUDED_FAWATIH_AL_SUWAR"

#: الحالة السادسة — أضافها المالك بحكمه في 2026-09-01 (القاعدة ن٠-ج).
#: كانت القائمة خمسًا، وصارت ستًّا بنصٍّ لا باستنباط. وما بقي مغلقًا كما كان:
#: لا حالةَ سابعة تُولَد من حاجةٍ وقت التشغيل.
JALALAH = "EXCLUDED_LAFZ_AL_JALALAH"

STATUSES = (NORMALIZED, OWNER_DECISION, STOPPED, IGNORED, FAWATIH, JALALAH)

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
    "N0.J": "لفظ الجلالة — يُمنع تصريفه وتقطيعه وكلُّ إجراء، وتُقشَّر سابقتُه بالجرد",
    "N1": "المدّة تُحذف ولا تولّد همزةً في أي موضع",
    "N2": "كل شدّة تُفكّ داخل كلمتها إلى ساكنٍ ومتحرّك",
    "N2.1": "شدّة على أول الكلمة بلا «ال» قبلها: علامةُ أداءٍ تُحذف ولا تُضاعف الحرف",
    "N2.2": "شدّة بعد «ال»: تعود إلى الفكّ العادي",
    "N3": "حذف التطويل",
    "N7": "ألف الوصل همزةٌ مع حركة، والأصل الفتح عند غياب الحركة المكتوبة",
    "N7.1": "ألفٌ مجرّدة أول الكلمة يتبعها لام وليست من الفواتح: همزةُ «ال» بفتحة",
    "N7.2": "«ال» بعد سابقةٍ داخل الكلمة: لا تُعامَل إلا بمطابقة الوحدة كلها في سجلٍّ معتمد",
    "N7.3": "ألف الوصل في رأس فعلٍ مبرهَن — معطّلة: EXECUTABLE_VERB_RULES = 0",
    "N7.4": "همزةُ «أل» تسقط رسمًا بعد لامٍ سابقة، واللامُ التالية لامُ التعريف",
    "N8": "الألف الخنجرية على الواو والألف المقصورة: مقعدٌ لا صامت، يُستبدل بألف مدّ",
    "N9": "اللام الشمسية: تُحذف لامُ «أل» ويُكرَّر الحرفُ الشمسيّ ساكنًا فمتحرّكًا",
    "N10": "الهمزة حرف لا حركة، ولا تُخترع من علامة",
    "N10.1": "تعيين كرسيّ الهمزة بحسب ما قبلها",
    "N10.2": "آ الداخلة على «أل»: المدّةُ رمزُ أداءٍ تُحذف بلا أثر، والباقي همزةُ استفهام",
    "N12": "كل حرفٍ حُكم بسكونه يحمل السكون صراحةً في المخرج",
    "N13": "لا تحويل عامّ من الرسم العثماني إلى الإملائي — قرارُ إبقاء",
    "N3.Q": "علاماتُ التجويد والوقف والثناء: طبقةٌ أدائية تُحذف (سندُها §١ـ١)",
}

#: سوابقُ مفردة قد تتقدّم لامَ الجرّ فلا تمنع سقوطَ همزة «أل» (N7.4).
#: قائمة مغلقة، مقيسة: 23 موضعًا يوافق المرجعُ عليها كلِّها.
ELIDING_PREFIXES = frozenset("وف")

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
    #: تُملأ من قائمة لفظ الجلالة وحدها — بالجرد لا بالتحليل.
    jalalah_prefix: str = ""
    jalalah_preserved: str = ""

    @property
    def is_usable(self) -> bool:
        """هل يمضي هذا السطح إلى المحورين ٣ و٤؟"""
        return self.status in (NORMALIZED, OWNER_DECISION)

    @property
    def is_jalalah(self) -> bool:
        return self.status == JALALAH

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
    ordinal: int = 0
    prev_letter: str | None = None
    prev_marks: str = ""

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
    def __init__(self, token: str, position: tuple | None, policy: OwnerPolicy,
                 jalalah: JalalahRegistry):
        self.token = token
        self.position = position
        self.policy = policy
        self.jalalah = jalalah
        self.res = NormalizationResult(token=token, status=NORMALIZED)
        self.units: list[Unit] = []
        #: تُرفع حين تُعالَج همزةُ «أل»، وتُستهلك عند الحرف التالي مباشرةً.
        #: بها يُعرف أن اللام لامُ التعريف لا لامًا أصلية — والفرق حكمٌ لا شكل.
        self._article_alif_just_seen = False

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
            # ن٠-ج قبل كل شيء: لفظ الجلالة لا يُطبَّع ولو خطوةً واحدة.
            self._maybe_jalalah()
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

    def _maybe_jalalah(self) -> None:
        """ن٠-ج — مطابقةٌ تامّة بالسطح المشكول، لا تشابهَ ولا احتواء.

        ويقع الفحص **قبل** أيّ خطوةٍ من خطوات التطبيع: لا فكَّ شدّةٍ، ولا
        همزةَ وصل، ولا تصريحَ بسكون. فما بعد هذه الدالّة لا يمسّ اللفظ.
        """
        entry = self.jalalah.get(self.token)
        if entry is None:
            return
        self.res.status = JALALAH
        self.res.normalized = self.token          # يُحفظ كما كُتب
        self.res.jalalah_prefix = entry.prefix
        self.res.jalalah_preserved = entry.preserved
        self._use("N0.J")
        for i, ch in enumerate(self.token):
            self._fate(i, ch, PRESERVED, "N0.J")
        raise _Stop("", JALALAH)

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
            if ch in MARKS or ch in ALL_SIGNS:
                raise _Stop(f"HARAKA_WITHOUT_CARRIER@{i}")
            if ch == TATWEEL:
                raw.append((i, TATWEEL, ""))
                i += 1
                continue
            if ch not in CONSONANT_LETTERS:
                # الضمانة: علامةٌ مركّبة مجهولة **تقف بإنذار** ولا تُصنَّف
                # «ليست كلمة». الفرق بين الحكمين هو الفرق بين الاعتراف
                # بالجهل وادّعاء العلم.
                if unicodedata.category(ch) in ("Mn", "Lm"):
                    raise _Stop(f"UNKNOWN_MARK@{i}:U+{ord(ch):04X}")
                raise _Stop(f"NON_LETTER@{i}:{ch!r}", IGNORED)
            j = i + 1
            marks = ""
            while j < n and (self.token[j] in MARKS or self.token[j] in ALL_SIGNS):
                marks += self.token[j]
                j += 1
            raw.append((i, ch, marks))
            i = j

        total = len(raw)
        for k, (index, letter, marks) in enumerate(raw):
            nxt = raw[k + 1] if k + 1 < total else None
            prv = raw[k - 1] if k else None
            yield _Letter(index=index, letter=letter, marks=marks,
                          is_first=(k == 0), is_last=(k == total - 1),
                          next_letter=nxt[1] if nxt else None,
                          next_marks=nxt[2] if nxt else "",
                          ordinal=k,
                          prev_letter=prv[1] if prv else None,
                          prev_marks=prv[2] if prv else "")

    # -- التوجيه ---------------------------------------------------------
    #: المعالجات بترتيب الأولوية. الترتيب جزءٌ من الحكم لا تفصيلُ تنفيذ.
    def _process(self, ctx: _Letter) -> None:
        article_lam = self._article_alif_just_seen
        self._article_alif_just_seen = False       # تُستهلك عند الحرف التالي
        self._detect_elided_article(ctx)
        ctx = self._strip_quranic_signs(ctx)
        for handler in (self._h_tatweel, self._h_rounded_zero):
            if handler(ctx):
                return
        ctx = self._strip_maddah(ctx)
        if ctx.vowel_mark_count > 1:
            # تعدّد الحركات على حاملٍ واحد: يقف ولا يرجّح
            raise _Stop(f"MULTIPLE_HARAKAT_ON_ONE_CARRIER@{ctx.index}")
        if article_lam:
            if self._h_sun_lam(ctx):
                return
            if self._h_moon_lam(ctx):
                return
        for handler in (self._h_dagger_alif, self._h_interrogative_madda,
                        self._h_alef_madda,
                        self._h_bare_alif, self._h_alif_maqsura):
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

    def _strip_quranic_signs(self, ctx: _Letter) -> _Letter:
        """الطبقة الأدائية في الرسم العثمانيّ — ثلاثة أصنافٍ بأحكامٍ مختلفة.

        الأدائيةُ تُحذف بسندٍ نصّيّ (§١ـ١ تعدّها من الطبقة الكتابية). والصوتيةُ
        والهمزةُ المركّبة **تنتظران حكمًا**: الأولى أختُ الألف الخنجرية في
        المعنى، والثانية يقرّر النصُّ أنها حرفٌ لا حركة ولا يقرّر كيف تُردّ
        حرفًا وهي مرسومةٌ علامة.
        """
        present = [m for m in ctx.marks if m in SIGNS]
        if not present:
            return ctx
        for mark in present:
            kind = SIGNS[mark].kind
            if kind == PERFORMANCE:
                self._fate(ctx.index, mark, DELETED, "N3.Q")
                self._use("N3.Q")
                continue
            cls = ("U_QURANIC_SMALL_VOWEL_OR_MADD" if kind == PHONETIC
                   else "U_COMBINING_HAMZA")
            treat = self._decide(cls, ctx.index,
                                 f"{SIGNS[mark].unicode_name}")
            if treat == OWNER_DECISION_REQUIRED:
                raise _Stop(f"QURANIC_SIGN_OWNER_DECISION@{ctx.index}"
                            f":U+{ord(mark):04X}")
            self._fate(ctx.index, mark, DELETED, cls)
        ctx.marks = "".join(m for m in ctx.marks if m not in SIGNS)
        return ctx

    def _strip_maddah(self, ctx: _Letter) -> _Letter:
        """N1 — المدّة علامةٌ تُحذف ولا تولّد همزة."""
        if MADDAH not in ctx.marks:
            return ctx
        self._fate(ctx.index, MADDAH, DELETED, "N1")
        self._use("N1")
        ctx.marks = ctx.marks.replace(MADDAH, "")
        return ctx

    def _detect_elided_article(self, ctx: _Letter) -> None:
        """N7.4 — «أل» محذوفةُ الهمزة بعد لامٍ سابقة.

        حكم المالك (2026-09-01): «لِلنَّاسِ = لامُ الجرّ + الناس، وهمزةُ الوصل
        تسقط للوصل مع اللام». فالسطحُ ثلاثةُ أجزاء: لِ + ال + ناس، وألفُ «أل»
        غائبةٌ عن الرسم لا عن البنية.

        وقياسُ الكشف على النصّ: **302 موضعًا، يوافق المرجعُ عليها كلِّها** —
        لا موضعَ واحد خاطئ. فالنمط (لامٌ متحرّكة أولَ الكلمة + لامٌ مجرّدة)
        لا يقع في العربية إلا هنا.

        ولا تُبثّ همزة: الوصلُ يُسقطها نطقًا كما أسقطها الرسم. وإنما تُرفع
        الرايةُ فتُعامَل اللامُ التالية معاملةَ لام التعريف — تُحذف قبل
        الشمسيّ (N9) وتبقى ساكنةً قبل القمريّ.
        """
        if ctx.letter != LAM or not ctx.haraka or ctx.next_letter != LAM:
            return
        # اللامُ أوّلَ الكلمة، أو بعد سابقةٍ مفردةٍ متحرّكة (وَ ، فَ).
        # والسابقةُ لا تغيّر شيئًا في الحكم: الهمزةُ تسقط للوصل باللام سواءٌ
        # أكانت اللامُ أوّلَ الكلمة أم بعد واوٍ أو فاء. وقياسُه 23 موضعًا
        # يوافق المرجعُ عليها كلِّها.
        after_prefix = (ctx.ordinal == 1 and ctx.prev_letter in ELIDING_PREFIXES
                        and any(m in HARAKAT for m in ctx.prev_marks))
        if not (ctx.is_first or after_prefix):
            return
        # اللامُ التالية مجرّدة: لا حركةَ عليها ولا شدّة.
        # والمشدّدةُ التقاءُ لامين (لِلَّذِينَ) لها مسارُها في N2.
        if SHADDA in ctx.next_marks or any(m in VOWEL_MARKS for m in ctx.next_marks):
            return
        self._article_alif_just_seen = True
        self._fate(ctx.index, ctx.letter, PRESERVED, "N7.4")
        self._use("N7.4")

    def _h_sun_lam(self, ctx: _Letter) -> bool:
        """N9 — لامُ «أل» قبل حرفٍ شمسيّ مشدّد: تُحذف.

        حكم المالك: «اللام الشمسية تُحذف اللام والشدّة، ويُكرَّر الحرفُ
        الشمسيّ بحرفين: أحدهما الأوّل ساكن، والثاني نفسُ حركة الشدّة».

        وتكريرُ الحرف عملُ N2 نفسه، فلا يزيد هذا المعالج عليه إلا **حذف
        اللام**. وأثرُه أن يسقط صامتٌ من كل كلمةٍ شمسية:
            الرَّحْمَنِ   قبل: ءَلْرْرَحْمَنِ   بعد: ءَرْرَحْمَنِ

        واللامُ مستثناةٌ من الحروف الشمسية بحكم المالك: «هذه لا تُدغم وتبقى
        اللام» — «الَّذِينَ» تبقى ءَلْلَذِيْنَ. والسطحُ لا يتغيّر باستثنائها،
        لأن المحذوفة والمكرَّر لامان في الحالين؛ لكن التوصيف يتغيّر، وهو
        المقصود.

        والقمريةُ لا يمسّها شيء: لا شدّة بعدها فلا سبب.
        """
        if ctx.letter != LAM or ctx.haraka or ctx.tanween or ctx.has_shadda:
            return False
        if ctx.next_letter not in SUN_LETTERS or SHADDA not in ctx.next_marks:
            return False
        self._fate(ctx.index, ctx.letter, DELETED, "N9")
        self._use("N9")
        return True

    def _h_moon_lam(self, ctx: _Letter) -> bool:
        """لامُ «أل» أمام قمريّ: تبقى ساكنة — وتُوسم بالقاعدة لا بصنفٍ مؤجَّل.

        كانت تُصنَّف `U_UNVOCALIZED_CARRIER` فترفع الكلمةَ إلى «تنتظر حكمًا»،
        وهي لامٌ مبرهنةٌ بحكمٍ مسمّى لا حاملٌ مجهول. والفرق ليس شكليًّا:
        الأوّل اعترافٌ بجهل، والثاني حكمٌ قائم.
        """
        if ctx.letter != LAM or ctx.haraka or ctx.tanween or ctx.has_shadda:
            return False
        self._emit(LAM, SUKUN, "N7.4", ctx.index)
        self._fate(ctx.index, ctx.letter, PRESERVED, "N7.4")
        self._use("N12")
        return True

    def _h_interrogative_madda(self, ctx: _Letter) -> bool:
        """N10.2 — «آ» الداخلة على «أل»: همزةُ استفهامٍ لا مدّ.

        حكم المالك (2026-09-01): «آ تُحذف بدون أيّ أثر لأنها رمزُ أداء وليست
        جزءًا من الكلام العربيّ، وتتحوّل إلى ء استفهام».

        فالمدّةُ هنا ليست صوتًا في الكلمة، وإنما علامةُ تلاوةٍ تفصل همزةَ
        الاستفهام عن همزة الوصل حتى لا يلتبس الخبرُ بالسؤال. فإذا حُذفت
        الأداءُ لم يبقَ إلا الهمزة، ولا يُبثّ بعدها ألفُ مدّ.

        وعلّةُ الحكم منضبطةٌ بموضعها: «آ» يتلوها لامٌ عاطلةٌ من الحركة —
        أي لامُ «أل» التي ابتُلعت همزتُها في الرمز. وقياسُه على النصّ كلِّه:
        **٦ مواضع لا سابعَ لها**، وهي أسطحٌ ثلاثة (آلذَّكَرَيْنِ ، آلْآنَ ،
        آللَّهُ)، وكلُّها استفهام. وما عداها من «آ» يتلوها لامٌ متحرّكة
        (آلِ ، آلَاءِ ، آلِهَة — ٨٧ موضعًا) لا يمسّه هذا الحكم.

        وتُرفع بعدها رايةُ «أل» فتعمل عليها N9: آلذَّكَرَيْنِ ← ءَذْذَكَرَيْنِ.

        ⚠ الفتحةُ على الهمزة **موروثةٌ من المعالجة القائمة** لصنف
        `U_ALEF_MADDA` (همزة + فتحة)، لا منصوصةٌ في الحكم. وهي الجزء
        الوحيد من هذه القاعدة الذي لم يَرِد بنصّه.
        """
        if ctx.letter != ALEF_MADDA or not ctx.is_first:
            return False
        if ctx.haraka or ctx.tanween:
            return False
        if ctx.next_letter != LAM or any(m in VOWEL_MARKS for m in ctx.next_marks):
            return False
        self._emit(HAMZA, FATHA, "N10.2", ctx.index)
        self._fate(ctx.index, ctx.letter, REPLACED, "N10.2")
        self._article_alif_just_seen = True
        self._use("N10")
        self._use("N10.2")
        return True

    def _h_dagger_alif(self, ctx: _Letter) -> bool:
        """الألف الخنجرية — ألفُ مدٍّ حُذفت رسمًا وبقيت علامتُها.

        وحكم المالك (2026-09-01): على **الواو** كحكمها على **الألف المقصورة**.
        وعلّتُه أن الحرفين هناك **مقعدٌ لا صامت**: لا يُنطقان، وإنما يحملان
        الألف المحذوفة. فيُستبدلان بها ولا يُعدّان في الصوامت.
        فـ«الصلوٰة» ← «الصلاة» ، و«علىٰ» ← «علا».

        ويقع هذا المعالج **قبل** معالج الألف المقصورة عمدًا: «ىٰ» يحكمها هذا
        الحكم لا حكمُ المقصورة المجرّدة، والترتيب هنا جزءٌ من الحكم.
        """
        if DAGGER_ALIF not in ctx.marks:
            return False

        # المقعدُ **مجرّد** بالضرورة: حرفٌ لا يُنطق فلا يحمل حركة.
        # فإن حملها فهو صامتٌ حقيقيّ والخنجريةُ مدٌّ بعده — وهو ما كشفه
        # القياس على «ٱلصَّلَوَٰتِ»: الواو فيها منطوقة (صَلَوَات) بخلاف
        # «ٱلصَّلَوٰةِ» التي حكم فيها المالك بأن الواو مقعدٌ يُستبدل.
        seat = ctx.letter in (WAW, ALIF_MAQSURA) and not (ctx.haraka or ctx.tanween)
        cls = "U_DAGGER_ALIF_ON_SEAT" if seat else "U_DAGGER_ALIF_OTHER_CARRIER"
        treat = self._decide(cls, ctx.index,
                             f"ألفٌ خنجرية على {ctx.letter!r}")
        if treat == OWNER_DECISION_REQUIRED:
            raise _Stop(f"DAGGER_ALIF_OWNER_DECISION@{ctx.index}")

        if seat:
            self._emit(ALIF, SUKUN, "N8", ctx.index)
            self._fate(ctx.index, ctx.letter, REPLACED, "N8")
            self._fate(ctx.index, DAGGER_ALIF, EXPANDED, "N8")
            self._use("N8")
            self._use("N12")
            return True

        # حاملٌ غير مقعد: صامتٌ بحركته، ثم ألفُ المدّ بعده
        if ctx.haraka is None:
            raise _Stop(f"DAGGER_ALIF_ON_UNVOCALIZED_CARRIER@{ctx.index}")
        letter = self._seat(ctx)
        self._emit(letter, ctx.haraka, "SOURCE", ctx.index)
        self._fate(ctx.index, ctx.haraka, PRESERVED, "N12")
        self._emit(ALIF, SUKUN, "U_DAGGER_ALIF_OTHER_CARRIER", ctx.index)
        self._fate(ctx.index, DAGGER_ALIF, EXPANDED, "U_DAGGER_ALIF_OTHER_CARRIER")
        self._use("N12")
        return True

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
            self._article_alif_just_seen = True
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
        # لامُ التعريف لا تحمل حركةً **مفردة**: مجرّدةٌ أو ساكنة أو مشدّدة.
        # والمشدّدةُ منها التقاءُ لام «أل» بلامِ الاسم (بِالَّذِي)، وكانت تسقط
        # من هذا الشرط فتُقرأ الألفُ مدًّا — عيبٌ في الشرط لا في القاعدة.
        # ولامٌ **متحرّكة بلا شدّة** بعد ألفٍ مجرّدة تعني أن الألف مدٌّ
        # (مَالِكِ ، لَيَالِيَ) — وهو الفاصل الذي يحميه هذا الشرط.
        if ctx.next_letter == LAM and (
                SHADDA in ctx.next_marks
                or not any(m in VOWEL_MARKS for m in ctx.next_marks)):
            treat = self._decide("U_N7_2_INTERNAL_AL", ctx.index,
                                 "«ال» داخل الكلمة بعد سابقة — لا سجلّ وحداتٍ معتمد")
            if treat == OWNER_DECISION_REQUIRED:
                raise _Stop(f"N7_2_NO_APPROVED_REGISTRY@{ctx.index}")
            self._fate(ctx.index, ctx.letter, DELETED, "N7.2")
            self._use("N7.2")
            self._article_alif_just_seen = True
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
                    policy: OwnerPolicy | None = None,
                    jalalah: JalalahRegistry | None = None) -> NormalizationResult:
    """يطبّع كلمةً واحدة. ``position`` = (سورة، آية، كلمة) لأجل N0.F وحدها."""
    return _Normalizer(token, position, policy or default_policy(),
                       jalalah or default_registry()).run()


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
    # -- القاعدة ن٠-ج: لفظ الجلالة ---------------------------------------
    # العيّنة تُؤخذ **من الجرد نفسه** لا تُكتب باليد. وسببُه واقعةٌ مقيسة:
    # النصّ يكتب الشدّة قبل الحركة، واليدُ تعكسهما، فيسقط السطحُ من المطابقة
    # وهو حاضر. فأيُّ سطحٍ مشكولٍ مكتوبٍ في ملفّ اختبار غيرُ موثوق بطبعه.
    reg = default_registry()
    bare_only = [e for e in reg if not e.has_prefix]
    with_prefix = reg.with_prefix
    suite.check("T12_JALALAH_REGISTRY_IS_LOADED",
                bool(bare_only) and bool(with_prefix),
                f"{len(reg)} سطحًا ، منها {len(with_prefix)} بسابقة")

    entry = bare_only[0]
    r = norm(entry.surface)
    suite.check("T13_JALALAH_LEAVES_ALL_AXES",
                r.status == JALALAH and r.normalized == entry.surface,
                f"{entry.surface} → {r.status}")
    suite.check("T14_JALALAH_IS_NOT_TOUCHED",
                r.rules_applied == ["N0.J"],
                f"القواعد المطبَّقة = {r.rules_applied}  (لا فكَّ شدّةٍ ولا همزةَ وصل ولا سكون)")

    entry = with_prefix[0]
    r = norm(entry.surface)
    suite.check("T15_JALALAH_PREFIX_SPLIT_BY_REGISTRY",
                r.jalalah_prefix == entry.prefix
                and r.jalalah_preserved == entry.preserved,
                f"{entry.surface} = {entry.prefix} + {entry.preserved}")
    suite.check("T16_EVERY_JALALAH_ENTRY_REBUILDS_ITS_SURFACE",
                all(e.prefix + e.preserved == e.surface for e in reg),
                "السابقة + البقيّة = السطح، في كل مدخلة")
    suite.check("T17_NO_JALALAH_SURFACE_IS_EVER_NORMALIZED",
                all(norm(e.surface).status == JALALAH for e in reg),
                f"{len(reg)}/{len(reg)} سطحًا خرجت من كل المحاور")

    # -- القاعدة N8: الألف الخنجرية ---------------------------------------
    # لا شاهدَ لها في هذا المدخل (صفرُ خنجرية)، فتُبنى العيّنة من **الثوابت
    # المسمّاة** لا من كتابةٍ يدوية: لا مصدرَ في النصّ يُنقل منه.
    on_waw = "ع" + FATHA + "ل" + FATHA + WAW + DAGGER_ALIF
    on_maqsura = "ع" + FATHA + "ل" + FATHA + ALIF_MAQSURA + DAGGER_ALIF
    expected = "ع" + FATHA + "ل" + FATHA + ALIF + SUKUN

    r = norm(on_waw)
    suite.check("T18_DAGGER_ALIF_ON_WAW_BECOMES_MADD_ALIF",
                r.normalized == expected and r.status == NORMALIZED
                and "N8" in r.rules_applied,
                f"{r.normalized} / {r.status}")
    suite.check("T19_DAGGER_ALIF_ON_WAW_EQUALS_ON_ALIF_MAQSURA",
                norm(on_waw).normalized == norm(on_maqsura).normalized,
                "حكمُ المالك: الواو كالألف المقصورة — المقعدُ لا يُنطق")
    suite.check("T20_DAGGER_SEAT_IS_REPLACED_NOT_KEPT",
                WAW not in r.normalized and ALIF_MAQSURA not in r.normalized,
                "المقعد يُستبدل ولا يبقى صامتًا يُعدّ")

    # -- الطبقة الأدائية في الرسم العثمانيّ --------------------------------
    suite.check("T21_UTHMANI_SIGN_TABLE_SELF_AUDITS", len(SIGNS) >= 40,
                f"{len(SIGNS)} علامة، كلٌّ منها طوبق اسمُها بيونيكود عند التحميل")
    gaps = uncovered_marks(MARKS)
    suite.check("T22_NO_MARK_IS_EVER_SILENTLY_SWALLOWED", not gaps,
                "لا علامةَ مركّبة في النطاقات المغطّاة خارج الجرد"
                if not gaps else f"ثغرات = {gaps[:3]}")

    waqf = next(c for c, sg in SIGNS.items() if sg.kind == PERFORMANCE)
    plain, marked = norm("قُلْ"), norm("قُلْ" + waqf)
    suite.check("T23_PERFORMANCE_SIGN_LEAVES_NO_TRACE",
                plain.normalized == marked.normalized,
                f"{marked.normalized}   (علامةُ الوقف حُذفت ولم تغيّر الطبقة الصوتية)")

    # -- القاعدة N9: اللام الشمسية ------------------------------------------
    r = norm("الرَّحْمَنِ")
    suite.check("T24_SUN_LAM_IS_DELETED",
                LAM not in r.normalized and "N9" in r.rules_applied,
                f"{r.normalized}   (سقطت لامُ «أل» وبقي التكرير)")

    r = norm("الْحَمْدُ")
    suite.check("T25_MOON_LAM_STAYS", LAM in r.normalized and "N9" not in r.rules_applied,
                f"{r.normalized}   (لا شدّةَ بعدها فلا سبب)")

    r = norm("الَّذِينَ")
    suite.check("T26_LAM_IS_NOT_A_SUN_LETTER",
                "N9" not in r.rules_applied and r.normalized.count(LAM) == 2,
                f"{r.normalized}   (حكم المالك: هذه لا تُدغم وتبقى اللام)")

    r = norm("وَالشَّمْسِ")
    suite.check("T27_SUN_LAM_ALSO_AFTER_A_PREFIX",
                "N9" in r.rules_applied and LAM not in r.normalized, r.normalized)

    # -- القاعدة N7.4: «أل» محذوفةُ الهمزة بعد لام ---------------------------
    r = norm("لِلنَّاسِ")
    suite.check("T28_ELIDED_ARTICLE_THEN_SUN_LETTER",
                "N7.4" in r.rules_applied and "N9" in r.rules_applied
                and r.normalized.count(LAM) == 1,
                f"{r.normalized}   (لامُ الجرّ باقية، ولامُ «أل» حُذفت)")

    r = norm("لِلْمُتَّقِينَ")
    suite.check("T29_ELIDED_ARTICLE_THEN_MOON_LETTER",
                "N7.4" in r.rules_applied and "N9" not in r.rules_applied
                and r.normalized.count(LAM) == 2, r.normalized)

    r = norm("لِلَّذِينَ")
    suite.check("T30_TWO_LAMS_WITH_SHADDA_IS_NOT_ELIDED_ARTICLE",
                "N7.4" not in r.rules_applied,
                f"{r.normalized}   (التقاءُ لامين، مسارُه N2)")

    # -- القاعدة N10.2: «آ» الداخلة على «أل» همزةُ استفهام ------------------
    r = norm("آلذَّكَرَيْنِ")
    suite.check("T31_INTERROGATIVE_MADDA_IS_A_HAMZA_THEN_THE_ARTICLE",
                "N10.2" in r.rules_applied and "N9" in r.rules_applied
                and ALIF not in r.normalized,
                f"{r.normalized}   (المدّةُ حُذفت بلا أثر، والرايةُ رُفعت لـN9)")

    r = norm("آلْآنَ")
    suite.check("T32_INTERROGATIVE_MADDA_THEN_MOON_LETTER",
                "N10.2" in r.rules_applied and r.normalized.count(LAM) == 1,
                f"{r.normalized}   (والـ«آ» الثانيةُ معجميّةٌ لا أداءٌ فتبقى في صنفها)")

    r = norm("آلَاءِ")
    suite.poison("P18_A_VOCALIZED_LAM_IS_NOT_THE_ARTICLE",
                 "N10.2" not in r.rules_applied,
                 f"{r.normalized}   (آلاء ، آلِ ، آلهة — لامٌ متحرّكة لا لامُ تعريف)")

    for word in ("آمَنُوا", "الْقُرْآنَ"):
        suite.poison(f"P19_LEXICAL_MADDA_IS_UNTOUCHED_BY_N10_2:{word}",
                     "N10.2" not in norm(word).rules_applied,
                     "الحكم مقصورٌ على «آ» أوّلَ الكلمة يتلوها لامُ «أل»")

    r = norm("هُدَى")
    suite.poison("P8_UNRATIFIED_CLASS_RAISES_ODR",
                 r.status == OWNER_DECISION and "U_ALIF_MAQSURA" in r.decision_classes,
                 f"{r.status} / {r.normalized}")

    # المطابقةُ تامّة: سطحٌ نقص منه محرفٌ واحد ليس هو
    suite.poison("P9_JALALAH_MATCH_IS_EXACT",
                 all(norm(e.surface[:-1]).status != JALALAH for e in reg),
                 "حذفُ علامةٍ واحدة يُخرج السطحَ من القائمة")
    # ولا احتواء: سطحٌ زِيد عليه ليس منها
    suite.poison("P10_JALALAH_IS_NOT_SUBSTRING_MATCHING",
                 all(norm(e.surface + "ب").status != JALALAH for e in reg),
                 "لا يُبنى الحكم على احتواء الرسم")
    # وما يشبهه رسمًا مجرّدًا ليس منه — والمقارنة هنا بلا شكلٍ فلا يدَ فيها
    marks = "".join(sorted(HARAKAT | TANWEEN | {SUKUN, SHADDA}))
    def strip(x): return "".join(c for c in x if c not in marks)
    lookalikes = {"اللهب", "اللهو", "يضلله", "للهدى"}
    # واوٌ متحرّكة تحمل خنجرية ليست مقعدًا بل صامتٌ منطوق (صَلَوَات):
    # تُرحَّل إلى الصنف الذي ينتظر حكمًا، ولا تُعامَل معاملة المقعد
    r = norm("ع" + FATHA + WAW + FATHA + DAGGER_ALIF)
    suite.poison("P12_VOCALIZED_WAW_IS_NOT_A_SEAT",
                 WAW in r.normalized
                 and "U_DAGGER_ALIF_OTHER_CARRIER" in r.decision_classes,
                 f"{r.normalized} — الواو بقيت صامتًا ولم تُستبدل")
    # خنجريةٌ على حاملٍ آخر: صنفٌ لم يُصادَق فيُرفع إلى قرار مالك
    r = norm("ه" + FATHA + DAGGER_ALIF + "ذ" + FATHA + ALIF)
    suite.poison("P13_DAGGER_ON_OTHER_CARRIER_IS_UNRATIFIED",
                 r.status == OWNER_DECISION
                 and "U_DAGGER_ALIF_OTHER_CARRIER" in r.decision_classes,
                 f"{r.status} — الحكم نصّ على الواو والمقصورة لا غير")
    # الضمانة عمليًّا: علامةٌ مجهولة تقف بإنذار ولا تُصنَّف «ليست كلمة»
    r = norm("بَ" + "\u0300")
    suite.poison("P14_UNKNOWN_MARK_STOPS_AND_IS_NOT_CALLED_A_NON_WORD",
                 r.status == STOPPED and r.stop_reason.startswith("UNKNOWN_MARK"),
                 f"{r.status} / {r.stop_reason}")
    hamza_sign = next(c for c, sg in SIGNS.items() if sg.kind == COMBINING_HAMZA)
    r = norm("بَ" + hamza_sign)
    suite.poison("P15_COMBINING_HAMZA_IS_UNRATIFIED",
                 r.status == OWNER_DECISION
                 and "U_COMBINING_HAMZA" in r.decision_classes,
                 "الهمزة حرفٌ لا حركة — وردُّها حرفًا لم يرد فيه نصّ")
    # لامٌ أصلية في أول الكلمة ليست لام «أل» ولو تلاها مشدّدٌ شمسيّ
    r = norm("لَذَّةٍ")
    suite.poison("P16_A_ROOT_LAM_IS_NEVER_DELETED", "N9" not in r.rules_applied,
                 f"{r.normalized} — الراية لا تُرفع إلا بعد همزة «أل»")
    # لامٌ متحرّكة يتلوها حرفٌ آخر ليست هذا النمط
    for word in ("لِسَانٍ", "لَيَالِيَ"):
        suite.poison(f"P17_NOT_EVERY_INITIAL_LAM_IS_A_PREFIX:{word}",
                     "N7.4" not in norm(word).rules_applied,
                     "النمطُ لامٌ متحرّكة + لامٌ مجرّدة، لا لامٌ فحسب")
    suite.poison("P11_LOOKALIKES_ARE_NOT_IN_THE_REGISTRY",
                 not ({strip(e.surface) for e in reg} & lookalikes),
                 f"{sorted(lookalikes)} تشترك في الحروف وليست منه")
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
        # الكلماتُ الخارجةُ بحكم مالك ليست إخفاقَ مطابقة: استثناؤها مقصود،
        # وعدُّها في الفجوة يخلط «لم يُعالَج بأمرك» بـ«لم يره المحرّك».
        if r.status == JALALAH:
            matrix["EXCLUDED_BY_OWNER_RULE"] += 1
            continue
        engine = any(rule in r.rules_applied
                     for rule in ("N7.1", "N7.2", "N7.4", "N10.2"))
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
        "EXCLUDED_BY_OWNER_RULE": matrix["EXCLUDED_BY_OWNER_RULE"],
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
                         r.stop_reason, r.jalalah_prefix, r.jalalah_preserved])

        write_csv(out_dir / "AXIS_1_NORMALIZATION.csv",
                  ["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                   "Normalization_Status", "Owner_Decision_Classes",
                   "Rules_Applied", "Stop_Reason",
                   "Jalalah_Prefix", "Jalalah_Preserved"], rows)

        measures = {
            "words": len(rows),
            "status": dict(statuses),
            "rules": dict(rules),
            "fates": dict(fates),
            "owner_decision_classes": dict(classes),
            "stop_reasons": dict(stops),
            "jalalah_words": statuses.get(JALALAH, 0),
            "jalalah_with_prefix": sum(1 for r in rows if r[9]),
            "jalalah_registry_size": len(default_registry()),
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
        r.heading("الحالات الستّ — قائمة مغلقة (الخامسة أضافها المالك بالقاعدة ن٠-ج)")
        r.counts([(s, m["status"].get(s, 0)) for s in STATUSES])
        r.heading("لفظ الجلالة — القاعدة ن٠-ج")
        r.counts({
            "أسطحُ القائمة المغلقة": m["jalalah_registry_size"],
            "كلماتٌ خرجت من كل المحاور": m["jalalah_words"],
            "منها ما قُشّرت سابقتُه بالجرد": m["jalalah_with_prefix"],
        })
        r.text("لم يُطبَّع اللفظ ولم يُقطَّع ولم يُقَس؛ والفصلُ من نصّ القائمة لا من تحليل.")
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
                "EXCLUDED_BY_OWNER_RULE":
                    "خرجت بالقاعدة ن٠-ج — استثناءٌ مقصود لا فجوةُ مطابقة",
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
