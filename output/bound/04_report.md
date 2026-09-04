# `BOUND_AND_RECONCILE` — تقييدُ الترديد، والأصلُ الثالث، والعددُ المتغيّر

```text
NAZILA_REGENERATED = 2026-09-04T19:43:41+00:00
NAZILA_SCORE       = 70.9% (207/292)   ·   STAGES_OPENED = 1/16
NAZILA_HTML        = 14 فصلًا · 299 = 292 + 7 · حقولُ EntryBoundary 7 [ENTRY_BOUNDARY_FIELDS]
```

```text
TASK_ID = BOUND_AND_RECONCILE
VENDOR_HEAD = 3cccdded7951ba71b3cb2a8b9b477f3fb3d91095 · porcelain 0 · MATCHES_PIN = TRUE
VENDOR_UNTOUCHED = TRUE · NO_COMMIT = TRUE
SCORE_RAISED = NO · STAGE_OPENED = NO
CLAIM_PROJECT_FINISHED = NO
```

**ولا يرفع هذا العملُ علامةً، ولا يفتح مرحلة.**

## `R1` — `C3` مقيَّدًا في الوثائق الثلاث

| ما هو | القيمة | الحال |
|---|---|---|
| العدد | `10013/77411` (12.9٪) | **يبقى** — مقيسٌ وسليم |
| ما بقي دليلًا | قاعدةٌ تُصنّف بالرسم الإملائيّ، وتمسّ 12.9٪ من الجرد | `EVIDENCE` — وهذا وحدَه يُرفع |
| دعوى العبور | `crosses: True ×3` | `TAUTOLOGY` |
| نسبةُ القاعدة إلى السطر | `startswith("ال")` ⟶ `Grapheme→FunctionalLetter` | `NOT_DERIVABLE` |
| الحكم | — | `OWNER_RULING_REQUIRED` |
| أمُحيت؟ | — | **لا** — الدعوى تُقيَّد لا تُمحى |

**والوثائقُ الثلاث**: `00_upstream.json` و`00_doors.json` و`upstream_report.md` — والثالثُ يُصاغ من الثاني فقيدُه قيدُه.

**والحارسُ الجديد** `G_EVIDENCE_IS_NOT_TAUTOLOGY` يقيس **مصدرَ المدخل** لا الجواب، وسمُّه ذو وجهَين:

| الوجه | المصدر | يلزم |
|---|---|---|
| الأوّل | `CANONICAL_REGISTRY.lines` | `TAUTOLOGY` |
| الثاني | `get_native_stage_registry().allowed_successors` | `EVIDENCE` |

ووجهٌ واحدٌ يُوهم أنّ الحارسَ يقيس مصدرًا وهو يقيس جوابًا: لو اكتُفي بالأوّل لمرّ حارسٌ يقول «كلُّ `True` ترديد» — وهو باطل.

```text
REPORT_TO_SONAISO  RAISED     = قاعدةٌ تُصنّف بالرسم الإملائيّ، وتمسّ 12.9٪ من الجرد
                   NOT_RAISED = دعوى العبور — ترديدٌ ونسبةٌ غيرُ مشتقّة
                   SENT = NO · AUTHORITY_TO_SEND = OWNER
```

## `R2` — الأصلُ الثالثُ في `T-7`

| | كان | صار |
|---|---|---|
| الصفوف | 288 | **432** |
| الحساب | `288 = 2 × 4 × 6 × 6` | `432 = 3 × 4 × 6 × 6` |
| الأصولُ المقيسة | 2/3 | **3/3** |

**والقرار**: قِيس CANDIDATE — فالمقامُ تامٌّ ولا يحتاج التقييدُ النصّيّ. والدعوى تُعمَّم أو تُنقض بالقياس لا بالكلام.

**والحكم**: الدعوى تصمد على المقام التامّ: لا رتبةَ CERTIFICATE تُمنح من هذه البوّابة في أيٍّ من الأصول الثلاثة. والرتبُ الممنوحةُ كلُّها: `CANDIDATE · HYPOTHESIS · TRACE · ZERO`.

و`CANDIDATE` بُني من **قِطَع فَخّ الـ vendor نفسِها**، ولم يُبدَّل منها إلا `generation_source`؛ و`entry_boundary` تُرك `None` لأنّ الحاملَ يرفضه لغير `DECLARED_ENTRY` — حكمُ الحامل لا اختيارٌ منّي.

## `R3` — ٦٠ و٥٢: مقامان لا خطأ

| المقام | المصدر | الصنف | المجموع |
|---|---|---|---|
| **أحداث** (مواضعُ حرف) | `axis1_normalization.py:1233` | 60 | 18143 |
| **كلمات** | `axis1_normalization.py:224` — `decision_classes` مجموعة | 52 | 18135 |

**والثمانيةُ لم تخرج.** لا كلمةَ واحدة. هي 8 **مواضعِ حرفٍ زائدة** على 5 كلماتٍ معدودةٍ أصلًا:

| الموضع | الكلمة | يُرفع | الزائد |
|---|---|---|---|
| `3:112:4` | أَيْنَما | ×2 | +1 |
| `5:2:8` | ولا | ×3 | +2 |
| `23:44:5` | كُلَّما | ×2 | +1 |
| `28:38:14` | على | ×2 | +1 |
| `40:38:8` | الرشاد | ×4 | +3 |

**لا تُصحَّح 18,143 — هي مجموعُ الأحداث بمقامه. و18,135 مجموعُ الكلمات. والخطأُ كان عرضَهما بلا مقام، لا أحدَهما.**

## `E5` — عددُ `INDEX.md` يُشتقّ

| كان | صار |
|---|---|
| «خمسةُ مقاماتٍ لا مقام» مكتوبًا، والجدولُ فوقه 6 | `len(idx)` — 6 |

والمفارقةُ في موضعها: السطرُ الذي حمل الرقمَ الميّت هو نفسُه الذي يقول «ولا رقمَ جامعٌ عبر المقامات».

## `R5` — سحوبٌ تُسجَّل بمصادرها ولا تُمحى

| # | المصدر | الدعوى | الحكم | ما حلّ محلَّها | تُنسَب للأداة؟ |
|---|---|---|---|---|---|
| `REVIEWER_WITHDRAWN_1` | `REVIEWER` | G_FORBIDDEN_LINES_QUERIED — الاستفتاءُ دليل | **باطل** | G_EVIDENCE_IS_NOT_TAUTOLOGY — يقيس مصدرَ المدخل لا الجواب، وسمُّه ذو وجهَين. | لا |
| `REVIEWER_WITHDRAWN_2` | `REVIEWER` | مميِّزُ M1: صوامتُ بعدُ > قبلُ | **لا يميّز** | المميِّزُ المقيس: تنوينُ فتحٍ على ألفٍ صامتة — 3059/5835، يقفل. | لا |
| `REVIEWER_WITHDRAWN_3A` | `TOOL` | C1 = «PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة» عنوانًا في 03_upstream | **ناقصٌ لا كاذب** | «PRE_WEIGHT مبنيّةُ الحوامل، غيرُ موصولةٍ بالمشغّل» — والحقلُ نفسُه يبقى مقيسًا في C1.measure.pre_weight_state.stage_runtime_implemented | **نعم** — TOOL |
| `REVIEWER_WITHDRAWN_3B` | `REVIEWER` | PRE_WEIGHT غيرُ مكتوبةٍ عند sonaiso · تحتاج كتابةَ منطق | **باطل** | الحالُ المقيسة في C1.measure.pre_weight_state — PRs 4/4 · اختباراتٌ تمرّ · corpus_runner لا يستورد من weight/ حرفًا. فالفجوةُ وصلةٌ لا بناء. | لا |

كلُّ سحبٍ يُسجَّل بمصدره: REVIEWER 3 · TOOL 1. ولا يُنسب خطأُ المراجع إلى الأداة، ولا يُخفى خطأُ الأداة تحت اسم المراجع. والأداةُ سجّلتها ولم تمحُ منها شيئًا.

**`REVIEWER_WITHDRAWN_3` شُطر** بحكم DR_HUSSEIN: بندٌ واحدٌ مصدرُه TOOL ⟶ `REVIEWER_WITHDRAWN_3A` · `REVIEWER_WITHDRAWN_3B`.

دعويان تشتركان في اسمٍ واحد: حقلٌ صادقٌ نقلته الأداة، وتأويلٌ باطلٌ للمراجع. والاسمُ المشترك جمعهما، فقُرئا دعوى واحدةً ونُسبا إلى جهةٍ واحدة.

والإسناد: REVIEWER 2 · TOOL 1  ⟶  REVIEWER 3 · TOOL 1.

## `R6` — ادّعاءٌ بائدٌ يُسحب حيث ورد

```text
CLAIM         تقشيرُ كَتَبَ ينزل عن ACCEPT بـT-6
STATUS        SUPERSEDED
SUPERSEDED_BY نزل بالفعل عند 2.9.0 بحكم المالك في T4B — لا بـT-6، ولا بأثرِ الأداة.
MEASURED      كَتَبَ ورد 8 صفًّا · قشرَ في 0 · Root_Proven=YES في 0 من 74668
READING       فلا واقعةَ تحت Signifier→WordForm — EXPECTED_EVENT_ABSENT
DELETED       FALSE — الدعوى تُقيَّد لا تُمحى.
OCCURRENCES   3 في هذه الشجرة
```

وُسم في 3/3 موضعًا عند موضعه، ولم يُحذف منها شيء.

## الحرّاس

| الحارس | من | النتيجة |
|---|---|---|
| `G_EVIDENCE_IS_NOT_TAUTOLOGY` | R1 | PASS |
| `G_ALL_ORIGINS` | R2 | PASS |
| `G_BOTH_DENOMINATORS_NAMED` | R3 | PASS |
| `G_DIFFERENCE_IS_ACCOUNTED` | R3 | PASS |
| `G_DETAIL_AGREES_WITH_BOTH` | R3 | PASS |
| `G_OBSOLETE_TAGGED_IN_PLACE` | R6 | PASS |
| `G_VENDOR` | — | PASS |

```text
CLAIM_PROJECT_FINISHED = NO
```

