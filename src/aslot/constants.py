"""حروف العربية وعلاماتها — مصدرٌ واحد لكل المحاور.

قبل إعادة الهيكلة كانت هذه الثوابت مقيمةً في وحدة المحور الأول، فاضطُرّ
المحور الثالث إلى استيرادها منه. وذلك خلطُ **بيانات** بـ**سلوك**: المحور
الثالث لا يعتمد على منطق التطبيع، وإنما يعرف الأبجدية نفسها.

فصلُها هنا يجعل الاعتماد بين المحاور مقصورًا على **الواجهات** لا على الثوابت.
"""

from __future__ import annotations

# --- الحركات والعلامات -----------------------------------------------------
FATHA = "َ"
DAMMA = "ُ"
KASRA = "ِ"

FATHATAN = "ً"
DAMMATAN = "ٌ"
KASRATAN = "ٍ"

SUKUN = "ْ"
SHADDA = "ّ"
MADDAH = "ٓ"
DAGGER_ALIF = "ٰ"
ROUNDED_ZERO = "۟"
TATWEEL = "ـ"

HARAKAT = frozenset({FATHA, DAMMA, KASRA})
TANWEEN = frozenset({FATHATAN, DAMMATAN, KASRATAN})
TANWEEN_TO_HARAKA = {FATHATAN: FATHA, DAMMATAN: DAMMA, KASRATAN: KASRA}
VOWEL_MARKS = HARAKAT | TANWEEN
MARKS = VOWEL_MARKS | {SUKUN, SHADDA, MADDAH, DAGGER_ALIF, ROUNDED_ZERO}

#: العلامة الوحيدة المسموح بها على وحدةٍ في المخرج المطبَّع: حركةٌ أو سكون.
OUTPUT_MARKS = HARAKAT | {SUKUN}

# --- الحروف ----------------------------------------------------------------
ALIF = "ا"
ALIF_WASLA = "ٱ"
ALIF_MAQSURA = "ى"
ALEF_MADDA = "آ"
HAMZA = "ء"
WAW = "و"
YAA = "ي"
LAM = "ل"
NOON = "ن"

#: كراسيّ الهمزة المكتوبة (N10.1)
HAMZA_SEATS = frozenset({"أ", "إ", "ؤ", "ئ"})

CONSONANT_LETTERS = frozenset(
    "ءآأؤإئابةتثج"
    "حخدذرزسشصضطظ"
    "عغفقكلمنهوىي"
    "ٱ"
)

#: حروف المدّ والحركة التي تسبقها. أساسُ الأطروحة `madd = V ، madd ≠ C`.
MADD_PARTNER = {ALIF: FATHA, WAW: DAMMA, YAA: KASRA}

#: حرفا اللين — صامتان في القفل لا امتدادَ نواة.
LAYN_LETTERS = frozenset({WAW, YAA})
