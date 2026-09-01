# محرّك أسلوط — خمسة محاور تقرأ `MASAQ.csv`

`aslot 2.0.0` · `RULE_OWNER = DR_HUSSEIN` · `MEASURED_NOT_PRESET`
`INPUT_SHA256 = 76f3cc26dd64f2a33ff31e656c3c91dcd8190fe72879749e9129a72ab477620e`

كلُّ رقمٍ هنا **مقيسٌ من جولة تشغيل فعلية**، لا مفترضًا ولا منقولًا عن الوثائق
النظرية. وحيث اختلف المقيسُ عن المذكور في `T1..T4` صُرِّح بالفرق.

---

## ١ ـ التشغيل

```bash
pip install -e ".[dev]"     # أو:  export PYTHONPATH=src

aslot all                   # السلسلة الخماسية كاملةً
aslot normalize --help      # محورٌ واحد
make test                   # pytest
make lint                   # ruff
```

بلا تثبيت: `python3 -m aslot all`. والغلاف القديم `scripts/run_all.sh` يعمل كما كان.

---

## ٢ ـ المحاور

| # | الأمر | ماذا يفعل |
|---|---|---|
| ٠ | `aslot corpus` | يطوي صفوف MASAQ إلى كلماتٍ فآياتٍ فسور، من الحقول الخمسة وحدها |
| ١ | `aslot normalize` | التطبيع بقواعد المالك المسمّاة `N0.F … N13` |
| ٢ | `aslot registry` | حصر العوامل والمبنيات، وبرهان الانغلاق بأربع قيم |
| ٣ | `aslot syllabify` | ستة أنماط مقطعية مغلقة، وعدّ الصوامت، وحدود القطع |
| ٤ | `aslot peel` | التقشير بترخيصٍ مسمّى حتى **جذعٍ غير قابل للقشر** |

كلُّ محورٍ يقرأ **مخرجَ ما قبله** لا المدخل الخام. البنية في
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md).

---

## ٣ ـ الحكمان اللذان بُني عليهما

```
AXIS_2_REGISTRY_SOURCE = DERIVED_WITNESS_FROM_MASAQ
    REGISTRY_AUTHORITY = EVIDENCE_ONLY      LICENSE_GRANTED = NO
    (السجلّان الحقيقيان غير مرفقين. مرّر --operators و--mabniyat
     لتحويل الوضع إلى OWNER_REGISTRY دون تعديل سطرٍ واحد.)

AXIS_4_ROOT_WORK = NONE
    STEM_OUTPUT = REMAINDER_WITH_NO_FURTHER_LICENSED_PEEL
    STEM_PROOF  = NOT_CLAIMED
    THREE_CONSONANT_GATE = NOT_APPLIED
    ROOT_PROVEN = 0   WAZN_EXECUTION = 0   SUFFIX_OUTPUT = 0
```

---

## ٤ ـ القياس على كامل النصّ

### ٤ـ١ بناء ملف القرآن

```
ROWS_READ    = 157,676        WORDS_BUILT = 77,411
VERSES_BUILT =   6,236        SURAS_BUILT =     114
FOLD_IS_LOSSLESS = YES        SELF_CHECKS = 7/7      POISONS = 7/7
```

عيوبُ **المدخل** — مقيسة، مؤجَّلة، غير مرقَّعة:

```
D1_WORD_NUMBER_GAPS_IN_VERSE       =   9   أرقام كلماتٍ مفقودة داخل آيات
D2A_SEGMENT_NUMBER_DUPLICATED      = 386   تكرار Segment_No («يا» الموصولة)
D3_MULTIWORD_SURFACE_IN_ONE_CELL   =   9   خليّة Word فيها كلمتان
```

### ٤ـ٢ التطبيع

```
NORMALIZED                          = 55,075
NORMALIZED_OWNER_DECISION_REQUIRED  = 22,297
STOPPED_…_NO_CARRIER_FOR_A_HARAKA   =      9
EXCLUDED_FAWATIH_AL_SUWAR           =     30      ← يوافق T1 §١ـ٥ تمامًا
SELF_CHECKS = 10/10        POISONS = 8/8
```

### ٤ـ٣ العوامل والمبنيات

```
مدخلات الجرد = 134     فهرس المطابقة = 97 سطحًا     فهرس الدليل = 110
PROVEN = 8,972    UNRESOLVED = 3,753    VERBAL_OPERATOR = 61    NOT_MATCHED = 64,586
SELF_CHECKS = 11/11        POISONS = 6/6
```

### ٤ـ٤ المقاطع الصوتية

```
CV = 109,900   CVC = 65,037   CVV = 47,619   CVCC = 5,403   CVVC = 1,029   CVVCC = 5
ACCEPT = 77,365      BLOCK = 7
SELF_CHECKS = 10/10        POISONS = 7/7
```

### ٤ـ٥ التقشير

```
WORDS = 77,372     ACTUAL_PEELS = 17,286     STEMS_EMITTED = 53,901
ACCEPT = 66,256    DEFER = 5,575             BLOCK = 5,541
STEM_NOT_FURTHER_PEELABLE       = 53,901
CLOSED_REMAINDER                = 12,355
BLOCK_SYLLABLE_BOUNDARY_CROSSED =  5,454
DEFER_INITIAL_LETTER_MAY_BE_RADICAL = 16
MASAQ_LIKE_ROWS = 88,770
SELF_CHECKS = 11/11        POISONS = 8/8
```

**المجموع: 77/77 فحصًا ذاتيًّا و36/36 سمًّا، و42 اختبار pytest.**

---

## ٥ ـ فروقٌ عن الوثائق النظرية — مصرَّحٌ بها

| الموضع | T1..T4 | المقيس هنا | السبب |
|---|---|---|---|
| نمط `CVVCC` | `0` (مرخَّص غير مشهود) | **5** | `آللَّهُ` ، `آلذَّكَرَيْنِ` ، `إِلْيَاسيْنَ`. حدثٌ يستحق التسجيل لا التصحيح |
| كلمات أوقفها المحور ٢ | 14,299 | 8,972 + 3,753 مؤجَّلة | الجرد هنا شاهدٌ مشتقّ (134 مدخلة) لا سجلُّ مالك (725 مدخلة) |
| صفوف MASAQ-like | 86,922 | 88,770 | اختلاف قاعدة توليد الصفوف مع إغلاق مسار الجذر |
| مرفوضات المحور ٣ | 204 | 7 | مدخلٌ مختلف: هذا الرسم إملائيّ لا عثمانيّ |

---

## ٦ ـ ما لم يُفعل — بالتصريح نفسه

* **مسار الجذر مغلق بالكامل** بحكمك: لا `Root`، ولا وسم «مرشّح جذر»، ولا حدّ ثلاثة صوامت.
* **اللواحق مغلقة**: `SUFFIX_OUTPUT = 0`.
* **`ال` غير مفتوحة**: `AL_OPENED = NO`.
* **`N7.3` معطّلة**: `VERB_RULE_ROWS = 34` و`EXECUTABLE_VERB_RULES = 0` — الشرط قائم والوسيلة غائبة.
* **مقاطعُ الكلمات المركّبة لم تدخل جرد المحور الثاني**: عمود `Segmented_Word` غير مشكول، ومطابقةُ غير المشكول بالمشكول ممنوعة بـ `OWNER_RULING_2`.

### حدّان معلومان ومقيسان في التقشير

```
KNOWN_COST_OF_N7_1_APPLIED_LITERALLY = 1,174
    نصّ N7.1 ينفي الشروط صراحةً، فتصدُق على «الْتَقَى» و«اللَّاتِي» وليستا أداةَ تعريف.

AL_WITH_ELIDED_ALIF_NOT_DETECTED = 343
    «لِلْـ» — أُسقطت ألفُ «ال» رسمًا فلا يراها المحرّك. أكبر فجوةٍ مفردة.

KNOWN_LIMIT_KAFARU = مثبَّتٌ اختبارًا (T3_KNOWN_LIMIT_KAFARU_IS_WRONGLY_PEELED)
    الكاف في «كَفَرُوا» أصلٌ ونحن نقشّرها. شرط البوابة C يشترط نمط CVV·CV·CV
    و«فَرُوْ» ليس منه. حدٌّ معروف لا نقضٌ للمانع.
```

---

## ٧ ـ ما ينتظر حكمك — `data/axis_1_owner_policy.json`

سبعة أصنافٍ ظهرت في MASAQ ولا سند نصّيّ لها في `T1`. كلٌّ منها له معالجةٌ
مؤقّتة تُمضي القياس، و`ratified: false` يرفع حالة الكلمة إلى
`NORMALIZED_OWNER_DECISION_REQUIRED`. **تصديقُ صنفٍ = تغيير `false` إلى `true`
في JSON، لا تعديلُ سطرٍ في محرّك.**

| الصنف | كلمات | المعالجة المؤقّتة |
|---|---:|---|
| `U_TANWEEN` | 8,894 | فكٌّ إلى حركة + نونٍ ساكنة — التنوين غير مذكور في T1 بتاتًا |
| `U_UNVOCALIZED_CARRIER` | 5,460 | سكونٌ صريح |
| `U_ALIF_FARIQA` | 3,561 | حذف ألف التفريق بعد واو الجماعة |
| `U_ALIF_MAQSURA` | 2,498 | ألفُ مدّ |
| `U_N7_2_INTERNAL_AL` | 1,766 | حذف همزة الوصل — N7.2 قاعدةٌ بلا وسيلة |
| `U_ALEF_MADDA` | 1,511 | همزة + فتحة + ألف مدّ — يعارض ظاهرَ N1 |
| `U_MULTIWORD_CELL` | 9 | وقوفٌ تامّ |

تصديقُ الأربعة الأولى وحدها يخفض `OWNER_DECISION_REQUIRED` من 22,297 إلى ما دون 4,000.

**وسؤالٌ ثامنٌ مفتوح** (`OPEN_QUESTION_N2_2`): وسمُ الشدّة بعد «ال» يُقاس بعد
بثّ الشطر الساكن، فتُوسم «الَّذِينَ» بـ `N2.2` و«اللَّهِ» بـ `N2` مع أن
الشدّة فيهما بعد «ال». الموضع معلَّمٌ في الكود وينتظر حكمك.

---

## ٨ ـ المخرجات

```
reports/axis_0_quran_build/   QURAN_FROM_MASAQ.txt · QURAN_WORDS.csv
reports/axis_1_normalization/ AXIS_1_NORMALIZATION.csv
reports/axis_2_mabniyat_operators/ AXIS_2_REGISTRY.csv · AXIS_2_TOKENS.csv
reports/axis_3_syllables/     AXIS_3_SYLLABLES.csv
reports/axis_4_peel_to_stem/  AXIS_4_PEEL_TO_STEM.csv · MASAQ_LIKE_OUTPUT.csv (88,770 صفًّا)
```

ومع كل محورٍ `AXIS_n_REPORT.txt` بكتل `key=value` و`AXIS_n_MEASURES.json` للقياس الآليّ.

`reports/*.csv` و`data/MASAQ.csv` مستبعدة من git بسياسة U1 — المدخل يُعرَّف
ببصمته لا بنسخه.
