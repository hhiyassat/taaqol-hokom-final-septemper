# `MAX_EXECUTABLE` — ما نُفِّذ، وما وقف، ولمن الباب

```text
NAZILA_REGENERATED = 2026-09-04T19:43:41+00:00
NAZILA_SCORE       = 70.9% (207/292)   ·   STAGES_OPENED = 1/16
NAZILA_HTML        = 14 فصلًا · 299 = 292 + 7 · حقولُ EntryBoundary 7 [ENTRY_BOUNDARY_FIELDS]
AXIS_BYTE_IDENTITY = MEASURED · 18/18 ملفًّا
```

```text
TASK_ID = MAX_EXECUTABLE
VENDOR_HEAD = 3cccdded7951ba71b3cb2a8b9b477f3fb3d91095 · porcelain 0 · VENDOR_UNTOUCHED = TRUE
NO_COMMIT = TRUE   ·   LICENSE_GRANTED = NO
P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED = TRUE
CLAIM_PROJECT_FINISHED = NO
```

## التحريراتُ الأربع

| # | كان | صار | لماذا | السمّ |
|---|---|---|---|---|
| `E1` | حارسُ الفهرس `len(idx) >= 5` — عددٌ لا هُويّة. | جردٌ مُثبَّتٌ بالمسار: ستّةُ دفاترَ مسمّاةٌ بمساراتها على آلتَين. | العددُ يمرّ بعد حذفِ دفترٍ ما دام سادسٌ قد أُضيف. والمسارُ لا يمرّ. | `test_poison_a_deleted_ledger_falls_even_when_another_is_added` |
| `E2` | `G_NO_LEDGER_MERGE` يُقرأ حارسًا بنيويًّا. | `NO_MERGE_KIND = NUMERIC_COINCIDENCE_CHECK` — والوسمُ في اسم الحارس نفسِه في الدفتر. | لا يقرأ نسبًا ولا مسارات: يبحث عن مصادفةٍ عدديّة. فيتّهم بريئًا صادف المجموعَ، ويُبرّئ مدموجًا لم يصادف. | `test_no_merge_is_labelled_a_numeric_coincidence_check` |
| `E3` | ٢٩٩ و٢٩٢ مكتوبتان في تعليق، والفرقُ مشروحٌ نثرًا. | `repeat_is_entry_boundary(page)` — يُشتقّ الفرقُ ويُقابَل بحقول `EntryBoundary` مستفتاةً من الصنف حيًّا. | رقمٌ مكتوبٌ في تعليقٍ لا يسقط حين يتغيّر المخرَج. | `test_poison_e3_falls_when_a_foreign_pair_repeats` |
| `E4` | القاعدةُ السابعةُ مذكورةٌ في الكلام، غيرُ موثَّقةٍ ولا مسمومة. | `COUNT_IS_NOT_MEMBERSHIP` سابعةً في `RULES` — وُسِّعت بحكم المالك إلى الجهتين بعد أن كانت في جهةٍ واحدة. | العددُ ظلُّ المجموعة لا هي. وأوّلُ صيغةٍ قالت «تساوٍ بلا اتّحاد» وحدَها، فمرّ الخطأُ المعاكس: «Example سقط» رُفع لاختلافِ 55/160 ولم يضع صفٌّ واحد. فصارت الجهتان معًا. | `test_count_is_not_membership_in_both_directions` |

## `B2` — ما قيس، وما بقي للمالك

| القياس | النتيجة |
|---|---|
| `M1` المميِّزُ المقترَح | 8894/8894 — يشطر؟ **False** |
| `M1` المميِّزُ المقيس | 3059 · 5835 — يشطر؟ **True** |
| `M2` الأصنافُ التي تبلغ محورًا لاحقًا | 6/7 |
| `M3` الاختياراتُ المملوءة | **0/7** — والاختيارُ حكمُ المالك |
| السقوفُ المتمايزة | CERTIFICATE · HYPOTHESIS · ZERO — **ثلاثةٌ لا خمسة** |

**وأربعةُ أسماءٍ على ثلاثةِ آثار.** `NON_BLOCKING` و`EXPLANATORY` سقفُهما واحد؛ فاختيارُ أحدهما دون الآخر لا يغيّر حكمًا واحدًا في المخرَج. وهذا ممّا يُعرَض على المالك قبل أن يختار.

## أثرُ الإسناد قبل وقوعه — `T5.3`

28 سيناريو = 7 أصناف × 4 إسنادات. والتفصيلُ في `reports/gamma_shadow/PROJECTED_IMPACT.md`.

| الصنف | أقصى ما يتحرّك | تحت |
|---|---|---|
| `U_TANWEEN` | 8600 حكمًا | `BLOCKING` ⟶ `ZERO` |
| `U_ALIF_FARIQA` | 2951 حكمًا | `BLOCKING` ⟶ `ZERO` |
| `U_ALIF_MAQSURA` | 2483 حكمًا | `BLOCKING` ⟶ `ZERO` |
| `U_N7_2_INTERNAL_AL` | 1616 حكمًا | `BLOCKING` ⟶ `ZERO` |
| `U_ALEF_MADDA` | 1505 حكمًا | `BLOCKING` ⟶ `ZERO` |
| `U_UNVOCALIZED_CARRIER` | 40 حكمًا | `BLOCKING` ⟶ `ZERO` |
| `U_MULTIWORD_CELL` | 0 حكمًا | `BLOCKING` ⟶ `ZERO` |

## `T-6` — ظلُّ الخطوط المستقيمة الممنوعة

صفوفٌ 104 · **دليلٌ 29** · ترديدٌ 59.

**والسؤالُ الذي يجيب نفسَه ليس دليلًا.** استفتاءُ السجلّ عن صفوفِ السجلّ يردّ `True` في 47 من 47 — وهذا ترديد، لا شهادة. والدليلُ ما جاء من خارجه:

| المصدر | مفحوصٌ | يقع |
|---|---|---|
| حوافُّ رسم المراحل | 17 | 0 |
| أزواجُ طبقات البوّابة | 12 | 1 |

فمن 47 صفًّا في السجلّ يبلغه رسمُ المراحلِ **0**، وتبلغه طبقاتُ البوّابةِ **1**: `CANDIDATE->CERTIFICATE`. والباقي مكتوبٌ لا مسؤولٌ عنه في هذا التشغيل — وذلك خبرٌ عن **مدى الاستفتاء**، لا طعنٌ في السجلّ.

**والواقعةُ المتوقَّعةُ لم تقع.** `Signifier → WordForm` سطرٌ قائمٌ في السجلّ، غير أنّ `كَتَبَ` في هذا الجسد لم يقشِر مرّةً واحدة، و`Root_Proven` لم يصر `YES` في صفٍّ واحدٍ من ٧٤٬٦٦٨. فلا واقعةَ تقع تحت السطر. وأمّا **أنّ قشرَ المحور الرابع هو هذا الانتقالُ بعينه** فليس في الشيفرة ما يدلّ عليه — `OWNER_RULING_REQUIRED`.

## `T-7` — ظلُّ البوّابة

432 صفًّا، حاملُها من فَخّ الـ vendor نفسِه — لا من لوحة المفاتيح.

| الحالة | العدد |
|---|---|
| `APPROVED` | 180 |
| `BLOCKED` | 72 |
| `DEFERRED` | 36 |
| `FORBIDDEN_LEAP` | 72 |
| `REJECTED` | 72 |

والرتبُ الممنوحةُ كلُّها: `CANDIDATE · HYPOTHESIS · TRACE · ZERO` — ولا `CERTIFICATE` بحال، ولو كانت البيّنةُ برتبة `CERTIFICATE` والبوّابةُ `LICENSED`. لأنّ الـ`meet` يُقيَّد برتبةِ الحاملِ نفسِه.

## الحرّاس

| الحارس | من | المقام | النتيجة |
|---|---|---|---|
| `G_SHADOW_ONLY` | T-6 | 5 | PASS |
| `G_FORBIDDEN_QUERIED` | T-6 | 103 | PASS |
| `G_TAUTOLOGY_DECLARED` | T-6 | 104 | PASS |
| `G_SHADOW_ONLY` | T-7 | 5 | PASS |
| `G_GATE_QUERIED` | T-7 | 432 | PASS |
| `G_RANK_FROM_MEET` | T-7 | 180+180 | PASS |
| `G_NO_CERTIFICATE_FROM_GATE` | T-7 | 432 | PASS |
| `G_ALL_ORIGINS` | T-7 | 3 | PASS |
| `G_NO_ASSIGNMENT` | T5.3 | 7 | PASS |
| `G_CEILING_IS_LIVE` | T5.3 | 5 | PASS |
| `G_TOTALS_PRESERVED` | T5.3 | 28 | PASS |
| `G_EVERY_CLASS_PROJECTED` | T5.3 | 7 | PASS |
| `G_BYTE_IDENTICAL` | MAX | 18 | PASS |

## ما وقف — ولمن الباب

| الموقوف | الحال | لمن |
|---|---|---|
| `T-5` (Γ على المحاور) | `BLOCKED_AWAITING_B2` — 7/7 بلا إسناد، ولا يُكتب ملفٌّ واحد | **المالك** — `B2` |
| إسنادُ الأصناف السبعة | `null` × 7 | **المالك** — `P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED` |
| نسبةُ قشرِ المحور الرابع إلى سطرٍ في السجلّ | `OWNER_RULING_REQUIRED` | **المالك** |
| إحدى عشرةَ مرحلةً تفتحها `C1` | خارجَ الولاية | **المالك** |
| `ANSWER_AUDIT` | `runtime_implemented = False` — لا تفتحها `C1` ولا `B2` | **المالك** |

```text
CLAIM_PROJECT_FINISHED = NO
```

