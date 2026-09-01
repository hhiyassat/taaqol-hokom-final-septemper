"""الطبقة الكتابية الأدائية في الرسم العثمانيّ — جردٌ مغلق يدقّق نفسه.

المسألة
-------
يقول المحور الأول إن النصّ طبقتان، وإن **علامات التجويد وعلامات الوقف** من
الطبقة الكتابية الأدائية. لكن المحرّك كان يعرف إحدى عشرة علامةً من اثنتين
وخمسين في نطاقات العربية، فأيُّ كلمةٍ عثمانيّة تحمل واحدةً من الإحدى والأربعين
الباقية تُصنَّف ``IGNORED_NON_WORD_TOKEN`` — أي **تُسقَط بوصفها ليست كلمة**.

وذلك أخطر من خطأ معالجة: هو تحويلُ الجهل إلى حكم. فالمحرّك لا يقول «لا أعرف
هذه العلامة»، بل يقول «هذه ليست كلمة» — دعوى لم يقم عليها دليل.

الضمانة التي يقيمها هذا الملف
-----------------------------
    NO_MARK_IS_EVER_SILENTLY_SWALLOWED

كلُّ علامةٍ مركّبة إمّا أن تكون في هذا الجرد بحكمٍ مسمّى، وإمّا أن يقف المحرّك
عندها بإنذار مالك. ولا ثالث.

الجرد يدقّق نفسه
----------------
لكل مدخلةٍ **رقمُها في يونيكود واسمُها المعياريّ**، ويُتحقَّق من تطابق الاسم عند
التحميل. وهذا ليس احتياطًا زائدًا: تصنيفُ خمسين علامةً بالعين وحدها هو تكرارٌ
للخطأ الذي وقع في جرد لفظ الجلالة — سطحٌ يُكتب باليد فيُظنّ صوابًا. والاسمُ
المعياريّ مرجعٌ خارجيّ يكشف الخلط مكانيكيًّا.
"""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from .errors import owner_alert

# ---------------------------------------------------------------------------
# أصناف الطبقة الأدائية — ثلاثة، بأحكامٍ مختلفة
# ---------------------------------------------------------------------------

#: علاماتُ أداءٍ وتجويدٍ ووقفٍ وثناء. سندُها نصّيّ: المحور الأول يعدّها من
#: الطبقة الكتابية الأدائية، وكلُّ ما بعده يعمل على الطبقة الصوتية وحدها.
PERFORMANCE = "U_QURANIC_PERFORMANCE_SIGN"

#: علاماتٌ وظيفتُها **صوتية**: حركاتٌ صغيرة وحروفُ مدٍّ مصغَّرة. أختُ الألف
#: الخنجرية في المعنى، ولم يرد فيها حكمٌ — فتنتظر.
PHONETIC = "U_QURANIC_SMALL_VOWEL_OR_MADD"

#: همزةٌ مركّبة. والمحور الأول يقرّر أن الهمزة **حرفٌ لا حركة**، لكنه لا يقرّر
#: كيف تُردّ حرفًا وهي مرسومةٌ علامةً على حاملها — فتنتظر.
COMBINING_HAMZA = "U_COMBINING_HAMZA"


@dataclass(frozen=True)
class Sign:
    codepoint: int
    unicode_name: str
    kind: str

    @property
    def char(self) -> str:
        return chr(self.codepoint)


#: الجرد المغلق. (رقم يونيكود ، الاسم المعياريّ ، الصنف)
#: الاسم مكتوبٌ للتدقيق لا للزينة: يُقارَن بما تقوله مكتبة يونيكود عند التحميل.
_TABLE: tuple[tuple[int, str, str], ...] = (
    # -- ثناءٌ وأدعية ------------------------------------------------------
    (0x0610, "ARABIC SIGN SALLALLAHOU ALAYHE WASSALLAM", PERFORMANCE),
    (0x0611, "ARABIC SIGN ALAYHE ASSALLAM", PERFORMANCE),
    (0x0612, "ARABIC SIGN RAHMATULLAH ALAYHE", PERFORMANCE),
    (0x0613, "ARABIC SIGN RADI ALLAHOU ANHU", PERFORMANCE),
    (0x0614, "ARABIC SIGN TAKHALLUS", PERFORMANCE),
    # -- علاماتُ تجويدٍ صغيرة ----------------------------------------------
    (0x0615, "ARABIC SMALL HIGH TAH", PERFORMANCE),
    (0x0616, "ARABIC SMALL HIGH LIGATURE ALEF WITH LAM WITH YEH", PERFORMANCE),
    (0x0617, "ARABIC SMALL HIGH ZAIN", PERFORMANCE),
    # -- حركاتٌ صغيرة: وظيفتُها صوتية ---------------------------------------
    (0x0618, "ARABIC SMALL FATHA", PHONETIC),
    (0x0619, "ARABIC SMALL DAMMA", PHONETIC),
    (0x061A, "ARABIC SMALL KASRA", PHONETIC),
    # -- همزةٌ مركّبة --------------------------------------------------------
    (0x0654, "ARABIC HAMZA ABOVE", COMBINING_HAMZA),
    (0x0655, "ARABIC HAMZA BELOW", COMBINING_HAMZA),
    (0x065F, "ARABIC WAVY HAMZA BELOW", COMBINING_HAMZA),
    # -- ألفٌ ودمّةٌ مقلوبة: مدٌّ مرسومٌ علامة ------------------------------
    (0x0656, "ARABIC SUBSCRIPT ALEF", PHONETIC),
    (0x0657, "ARABIC INVERTED DAMMA", PHONETIC),
    # -- غنّةٌ وعلاماتُ رسمٍ غير قرآنية --------------------------------------
    (0x0658, "ARABIC MARK NOON GHUNNA", PERFORMANCE),
    (0x0659, "ARABIC ZWARAKAY", PERFORMANCE),
    (0x065A, "ARABIC VOWEL SIGN SMALL V ABOVE", PERFORMANCE),
    (0x065B, "ARABIC VOWEL SIGN INVERTED SMALL V ABOVE", PERFORMANCE),
    (0x065C, "ARABIC VOWEL SIGN DOT BELOW", PERFORMANCE),
    (0x065D, "ARABIC REVERSED DAMMA", PERFORMANCE),
    (0x065E, "ARABIC FATHA WITH TWO DOTS", PERFORMANCE),
    # -- علاماتُ الوقف ------------------------------------------------------
    (0x06D6, "ARABIC SMALL HIGH LIGATURE SAD WITH LAM WITH ALEF MAKSURA", PERFORMANCE),
    (0x06D7, "ARABIC SMALL HIGH LIGATURE QAF WITH LAM WITH ALEF MAKSURA", PERFORMANCE),
    (0x06D8, "ARABIC SMALL HIGH MEEM INITIAL FORM", PERFORMANCE),
    (0x06D9, "ARABIC SMALL HIGH LAM ALEF", PERFORMANCE),
    (0x06DA, "ARABIC SMALL HIGH JEEM", PERFORMANCE),
    (0x06DB, "ARABIC SMALL HIGH THREE DOTS", PERFORMANCE),
    (0x06DC, "ARABIC SMALL HIGH SEEN", PERFORMANCE),
    # -- أصفارٌ وعلاماتُ حذف ------------------------------------------------
    (0x06E0, "ARABIC SMALL HIGH UPRIGHT RECTANGULAR ZERO", PERFORMANCE),
    (0x06E1, "ARABIC SMALL HIGH DOTLESS HEAD OF KHAH", PERFORMANCE),
    (0x06E2, "ARABIC SMALL HIGH MEEM ISOLATED FORM", PERFORMANCE),
    (0x06E3, "ARABIC SMALL LOW SEEN", PERFORMANCE),
    (0x06E4, "ARABIC SMALL HIGH MADDA", PHONETIC),
    (0x06E7, "ARABIC SMALL HIGH YEH", PHONETIC),
    (0x06E8, "ARABIC SMALL HIGH NOON", PERFORMANCE),
    (0x06EA, "ARABIC EMPTY CENTRE LOW STOP", PERFORMANCE),
    (0x06EB, "ARABIC EMPTY CENTRE HIGH STOP", PERFORMANCE),
    (0x06EC, "ARABIC ROUNDED HIGH STOP WITH FILLED CENTRE", PERFORMANCE),
    (0x06ED, "ARABIC SMALL LOW MEEM", PERFORMANCE),
)

#: حرفان صغيران في يونيكود فئتُهما حرفٌ لا علامة (Lm)، ووظيفتُهما مدٌّ صامت.
#: يُعامَلان معاملةَ العلامات الصوتية لأن دورهما دورُ الألف الخنجرية.
SMALL_LETTERS: tuple[tuple[int, str, str], ...] = (
    (0x06E5, "ARABIC SMALL WAW", PHONETIC),
    (0x06E6, "ARABIC SMALL YEH", PHONETIC),
)

#: النطاقات التي يجب أن يغطّيها الجرد كاملةً. أيُّ علامةٍ مركّبة فيها خارج
#: الجرد = ثغرةٌ دستورية، لا حالةٌ يُمضى عليها.
COVERED_RANGES = ((0x0610, 0x061A), (0x064B, 0x065F), (0x0670, 0x0670),
                  (0x06D6, 0x06ED))


def _build() -> dict[str, Sign]:
    signs: dict[str, Sign] = {}
    for codepoint, name, kind in _TABLE + SMALL_LETTERS:
        actual = unicodedata.name(chr(codepoint), "")
        # التدقيق المكانيكيّ: الاسم المعياريّ مرجعٌ خارجيّ يكشف الخلط.
        if actual != name:
            raise owner_alert(
                "مدخلةٌ في جرد الرسم العثمانيّ اسمُها لا يطابق يونيكود",
                الرمز=f"U+{codepoint:04X}", المكتوب=name, المعياريّ=actual)
        signs[chr(codepoint)] = Sign(codepoint, name, kind)
    return signs


SIGNS: dict[str, Sign] = _build()

#: مجموعاتٌ جاهزة للفحص السريع
PERFORMANCE_SIGNS = frozenset(c for c, s in SIGNS.items() if s.kind == PERFORMANCE)
PHONETIC_SIGNS = frozenset(c for c, s in SIGNS.items() if s.kind == PHONETIC)
HAMZA_SIGNS = frozenset(c for c, s in SIGNS.items() if s.kind == COMBINING_HAMZA)
ALL_SIGNS = frozenset(SIGNS)


def uncovered_marks(known: frozenset) -> list[tuple[int, str]]:
    """علاماتٌ مركّبة في النطاقات المغطّاة لا يعرفها المحرّك ولا هذا الجرد.

    مخرجُها يجب أن يكون فارغًا دائمًا؛ وهو الاختبار الذي يثبت الضمانة
    ``NO_MARK_IS_EVER_SILENTLY_SWALLOWED``.
    """
    out = []
    for low, high in COVERED_RANGES:
        for codepoint in range(low, high + 1):
            char = chr(codepoint)
            if unicodedata.category(char) != "Mn":
                continue
            if char in known or char in SIGNS:
                continue
            out.append((codepoint, unicodedata.name(char, "?")))
    return out
