# خمسة أكواد تقرأ `MASAQ.csv`

`RULE_OWNER = DR_HUSSEIN` · `MEASURED_NOT_PRESET` · تاريخ الجولة: 2026-09-01
`INPUT_SHA256 = 76f3cc26dd64f2a33ff31e656c3c91dcd8190fe72879749e9129a72ab477620e`

كلُّ رقمٍ في هذا الملف **مقيسٌ من جولة تشغيل فعلية**، لا مفترضًا ولا منقولًا عن
الوثائق النظرية. حيث اختلف المقيسُ عن المذكور في `T1..T4` صُرِّح بالفرق.

---

## ١ ـ الملفات

| # | الملف | المحور | ماذا يفعل |
|---|---|---|---|
| ١ | `a0_build_quran_from_masaq.py` | ٠ | يطوي صفوف MASAQ إلى كلماتٍ ثم آيات ثم سور، من الحقول الخمسة وحدها |
| ٢ | `a1_normalize.py` | ١ | التطبيع بقواعد المالك المسمّاة `N0.F … N13` |
| ٣ | `a2_classify_mabniyat_and_operators.py` | ٢ | حصر العوامل والمبنيات، وبرهان الانغلاق بأربع قيم |
| ٤ | `a3_syllabify.py` | ٣ | التقطيع إلى ستة أنماط مغلقة، وعدّ الصوامت، وحدود القطع |
| ٥ | `a4_peel_to_stem.py` | ٤ | التقشير بترخيصٍ مسمّى حتى **جذعٍ غير قابل للقشر** |

ملفّان مساندان: `data/axis_1_owner_policy.json` (سياسة أصنافٍ تنتظر حكمك)،
و`run_all.sh` (تشغيل السلسلة بالترتيب).

**السلسلة**: كل محورٍ يقرأ **مخرجَ ما قبله** لا المدخل الخام. والمحور الرابع
لا يفتح `MASAQ.csv` قطّ إلا لبناء جرد المحور الثاني.

```bash
./run_all.sh                      # الخمسة بالترتيب
python3 a4_peel_to_stem.py --emit-masaq-like   # جدول MASAQ-like وحده
```

---

## ٢ ـ الحكمان اللذان بنيتُ عليهما

سألتُ فأجبتَ، وهذا أثرُ جوابك في الكود:

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

## ٣ ـ القياس على كامل النصّ

### ٣ـ١ بناء ملف القرآن

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

### ٣ـ٢ التطبيع

```
NORMALIZED                          = 55,075
NORMALIZED_OWNER_DECISION_REQUIRED  = 22,297
STOPPED_…_NO_CARRIER_FOR_A_HARAKA   =      9
EXCLUDED_FAWATIH_AL_SUWAR           =     30      ← يوافق T1 §١ـ٥ تمامًا
SELF_CHECKS = 10/10        POISONS = 8/8
```

### ٣ـ٣ العوامل والمبنيات

```
مدخلات الجرد = 134     فهرس المطابقة = 97 سطحًا     فهرس الدليل = 110
PROVEN = 8,972    UNRESOLVED = 3,753    VERBAL_OPERATOR = 61    NOT_MATCHED = 64,586
SELF_CHECKS = 11/11        POISONS = 6/6
```

### ٣ـ٤ المقاطع الصوتية

```
CV = 109,900   CVC = 65,037   CVV = 47,619   CVCC = 5,403   CVVC = 1,029   CVVCC = 5
ACCEPT = 77,365      BLOCK = 7
SELF_CHECKS = 10/10        POISONS = 7/7
```

### ٣ـ٥ التقشير

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

**المجموع: 77/77 فحصًا ذاتيًّا و36/36 سمًّا.**

---

## ٤ ـ فروقٌ عن الوثائق النظرية — مصرَّحٌ بها

| الموضع | T1..T4 | المقيس هنا | السبب |
|---|---|---|---|
| نمط `CVVCC` | `0` (مرخَّص غير مشهود) | **5** | `آللَّهُ` ، `آلذَّكَرَيْنِ` ، `إِلْيَاسيْنَ`. حدثٌ يستحق التسجيل لا التصحيح (T3 §٣ـ١٠) |
| كلمات أوقفها المحور ٢ | 14,299 | 8,972 + 3,753 مؤجَّلة | الجرد هنا شاهدٌ مشتقّ (134 مدخلة) لا سجلُّ مالك (725 مدخلة) |
| صفوف MASAQ-like | 86,922 | 88,770 | اختلاف قاعدة توليد الصفوف مع إغلاق مسار الجذر |
| مرفوضات المحور ٣ | 204 | 7 | مدخلٌ مختلف: هذا الرسم إملائيّ لا عثمانيّ |

---

## ٥ ـ ما لم يُفعل — بالتصريح نفسه

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

KNOWN_LIMIT_KAFARU = مثبَّتٌ اختبارًا
    الكاف في «كَفَرُوا» أصلٌ ونحن نقشّرها. شرط البوابة C يشترط نمط CVV·CV·CV
    و«فَرُوْ» ليس منه. حدٌّ معروف لا نقضٌ للمانع (T4 §٤ـ٨).
```

---

## ٦ ـ ما ينتظر حكمك — `data/axis_1_owner_policy.json`

سبعة أصنافٍ ظهرت في MASAQ ولا سند نصّيّ لها في `T1`. كلٌّ منها له معالجةٌ
مؤقّتة تُمضي القياس، و`ratified: false` يرفع حالة الكلمة إلى
`NORMALIZED_OWNER_DECISION_REQUIRED`. تصديقُ صنفٍ = تغيير `false` إلى `true`.

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

---

## ٧ ـ المخرجات

```
reports/axis_0_quran_build/QURAN_FROM_MASAQ.txt      نصّ: سطر لكل آية
reports/axis_0_quran_build/QURAN_WORDS.csv           77,411 كلمة
reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv
reports/axis_2_mabniyat_operators/AXIS_2_REGISTRY.csv  +  AXIS_2_TOKENS.csv
reports/axis_3_syllables/AXIS_3_SYLLABLES.csv
reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv
reports/axis_4_peel_to_stem/MASAQ_LIKE_OUTPUT.csv    88,770 صفًّا
```

ومع كل محورٍ `*_REPORT.txt` بكتلة `key=value` و`*_MEASURES.json` للقياس الآليّ.

---

## ٨ ـ بصمات هذه الجولة

```
a0_build_quran_from_masaq.py            db2c73702e71e923…
a1_normalize.py                         f8a1b2b79be2f3ac…
a2_classify_mabniyat_and_operators.py   f60a97518c5f3a52…
a3_syllabify.py                         cf564721915b8103…
a4_peel_to_stem.py                      51a8ee19a11b1120…
data/axis_1_owner_policy.json           fca7f471b43f5a3a…
```
