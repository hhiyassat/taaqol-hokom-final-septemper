# `T5.3` — أثرُ الإسناد قبل وقوعه

```text
TASK_ID = MAX_EXECUTABLE · T5.3
P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED = TRUE
ASSIGNMENTS_FILLED = 0/7   ←  الاختيارُ حكمُ المالك (B2)
SHADOW_ONLY = TRUE   ←  لا يدخل هذا المخرَجُ قرارًا في أسلوط
```

## السقوفُ — مستفتاةً حيًّا

| الصنفُ الدستوريّ | السقف | قراءتُه | يُسنَد؟ |
|---|---|---|---|
| `BLOCKING` | `ZERO` | يُصفَّر — لا حكمَ يخرج من كلمةٍ تحمل هذا الصنف | نعم |
| `DEFERRABLE` | `HYPOTHESIS` | يقف عند فرضيّة — ACCEPT لا يبقى ACCEPT — يصير فرضيّة | نعم |
| `NON_BLOCKING` | `CERTIFICATE` | لا يُخفَض — الصنفُ لا يمسّ الرتبةَ ألبتّة | نعم |
| `EXPLANATORY` | `CERTIFICATE` | لا يُخفَض — الصنفُ لا يمسّ الرتبةَ ألبتّة | نعم |
| `HIDDEN_FORBIDDEN` | `ZERO` | يُصفَّر — لا حكمَ يخرج من كلمةٍ تحمل هذا الصنف | **لا** — يُكتشف ولا يُختار |

**ثلاثةُ مآلاتٍ لا خمسة.** `NON_BLOCKING` و`EXPLANATORY` يشتركان في سقفٍ واحد، و`BLOCKING` و`HIDDEN_FORBIDDEN` كذلك. فاختيارُ المالك بين أربعةِ أسماءٍ يقع على **ثلاثةِ آثار**.

## مصفوفةُ الانتقال — لكلّ صنفٍ في كلّ سيناريو

| الصنف | الكلمات | لو أُسند | السقف | ACCEPT قبلُ ⟶ بعدُ | DEFER | BLOCK | أحكامٌ تتحرّك |
|---|---|---|---|---|---|---|---|
| `U_TANWEEN` | 8894 | `BLOCKING` | `ZERO` | 7829 ⟶ 0 | 771 ⟶ 0 | 294 ⟶ 8894 | **8600** |
| `U_TANWEEN` | 8894 | `DEFERRABLE` | `HYPOTHESIS` | 7829 ⟶ 0 | 771 ⟶ 8600 | 294 ⟶ 294 | **7829** |
| `U_TANWEEN` | 8894 | `NON_BLOCKING` | `CERTIFICATE` | 7829 ⟶ 7829 | 771 ⟶ 771 | 294 ⟶ 294 | **0** |
| `U_TANWEEN` | 8894 | `EXPLANATORY` | `CERTIFICATE` | 7829 ⟶ 7829 | 771 ⟶ 771 | 294 ⟶ 294 | **0** |
| `U_ALIF_FARIQA` | 3561 | `BLOCKING` | `ZERO` | 2401 ⟶ 0 | 550 ⟶ 0 | 610 ⟶ 3561 | **2951** |
| `U_ALIF_FARIQA` | 3561 | `DEFERRABLE` | `HYPOTHESIS` | 2401 ⟶ 0 | 550 ⟶ 2951 | 610 ⟶ 610 | **2401** |
| `U_ALIF_FARIQA` | 3561 | `NON_BLOCKING` | `CERTIFICATE` | 2401 ⟶ 2401 | 550 ⟶ 550 | 610 ⟶ 610 | **0** |
| `U_ALIF_FARIQA` | 3561 | `EXPLANATORY` | `CERTIFICATE` | 2401 ⟶ 2401 | 550 ⟶ 550 | 610 ⟶ 610 | **0** |
| `U_ALIF_MAQSURA` | 2498 | `BLOCKING` | `ZERO` | 2353 ⟶ 0 | 130 ⟶ 0 | 15 ⟶ 2498 | **2483** |
| `U_ALIF_MAQSURA` | 2498 | `DEFERRABLE` | `HYPOTHESIS` | 2353 ⟶ 0 | 130 ⟶ 2483 | 15 ⟶ 15 | **2353** |
| `U_ALIF_MAQSURA` | 2498 | `NON_BLOCKING` | `CERTIFICATE` | 2353 ⟶ 2353 | 130 ⟶ 130 | 15 ⟶ 15 | **0** |
| `U_ALIF_MAQSURA` | 2498 | `EXPLANATORY` | `CERTIFICATE` | 2353 ⟶ 2353 | 130 ⟶ 130 | 15 ⟶ 15 | **0** |
| `U_N7_2_INTERNAL_AL` | 1616 | `BLOCKING` | `ZERO` | 14 ⟶ 0 | 1602 ⟶ 0 | 0 ⟶ 1616 | **1616** |
| `U_N7_2_INTERNAL_AL` | 1616 | `DEFERRABLE` | `HYPOTHESIS` | 14 ⟶ 0 | 1602 ⟶ 1616 | 0 ⟶ 0 | **14** |
| `U_N7_2_INTERNAL_AL` | 1616 | `NON_BLOCKING` | `CERTIFICATE` | 14 ⟶ 14 | 1602 ⟶ 1602 | 0 ⟶ 0 | **0** |
| `U_N7_2_INTERNAL_AL` | 1616 | `EXPLANATORY` | `CERTIFICATE` | 14 ⟶ 14 | 1602 ⟶ 1602 | 0 ⟶ 0 | **0** |
| `U_ALEF_MADDA` | 1505 | `BLOCKING` | `ZERO` | 1389 ⟶ 0 | 116 ⟶ 0 | 0 ⟶ 1505 | **1505** |
| `U_ALEF_MADDA` | 1505 | `DEFERRABLE` | `HYPOTHESIS` | 1389 ⟶ 0 | 116 ⟶ 1505 | 0 ⟶ 0 | **1389** |
| `U_ALEF_MADDA` | 1505 | `NON_BLOCKING` | `CERTIFICATE` | 1389 ⟶ 1389 | 116 ⟶ 116 | 0 ⟶ 0 | **0** |
| `U_ALEF_MADDA` | 1505 | `EXPLANATORY` | `CERTIFICATE` | 1389 ⟶ 1389 | 116 ⟶ 116 | 0 ⟶ 0 | **0** |
| `U_UNVOCALIZED_CARRIER` | 52 | `BLOCKING` | `ZERO` | 31 ⟶ 0 | 9 ⟶ 0 | 12 ⟶ 52 | **40** |
| `U_UNVOCALIZED_CARRIER` | 52 | `DEFERRABLE` | `HYPOTHESIS` | 31 ⟶ 0 | 9 ⟶ 40 | 12 ⟶ 12 | **31** |
| `U_UNVOCALIZED_CARRIER` | 52 | `NON_BLOCKING` | `CERTIFICATE` | 31 ⟶ 31 | 9 ⟶ 9 | 12 ⟶ 12 | **0** |
| `U_UNVOCALIZED_CARRIER` | 52 | `EXPLANATORY` | `CERTIFICATE` | 31 ⟶ 31 | 9 ⟶ 9 | 12 ⟶ 12 | **0** |
| `U_MULTIWORD_CELL` | 9 | `BLOCKING` | `ZERO` | 0 ⟶ 0 | 0 ⟶ 0 | 0 ⟶ 0 | **0** |
| `U_MULTIWORD_CELL` | 9 | `DEFERRABLE` | `HYPOTHESIS` | 0 ⟶ 0 | 0 ⟶ 0 | 0 ⟶ 0 | **0** |
| `U_MULTIWORD_CELL` | 9 | `NON_BLOCKING` | `CERTIFICATE` | 0 ⟶ 0 | 0 ⟶ 0 | 0 ⟶ 0 | **0** |
| `U_MULTIWORD_CELL` | 9 | `EXPLANATORY` | `CERTIFICATE` | 0 ⟶ 0 | 0 ⟶ 0 | 0 ⟶ 0 | **0** |

**والمقامُ**: أحكامُ المحور الرابع على كلماتِ ذلك الصنف وحدَها. ولا تُجمع الصفوفُ: كلمةٌ قد تحمل صنفَين، فمجموعُ العمودِ ليس عددَ كلماتٍ متمايزة.

**وعمودُ «الكلمات» بمقام الكلمات** (18135) لا بمقام الأحداث (18143). والثاني هو ما يُطبع في `output/doors` و`output/remediation`، وكلاهما مقيس؛ والفرقُ مواضعُ حرفٍ زائدة على كلماتٍ معدودةٍ أصلًا، مشروحٌ في `output/bound/02_class_count.json`.

## الحرّاس

| الحارس | المقام | النتيجة |
|---|---|---|
| `G_NO_ASSIGNMENT` | 7 | PASS |
| `G_CEILING_IS_LIVE` | 5 | PASS |
| `G_TOTALS_PRESERVED` | 28 | PASS |
| `G_EVERY_CLASS_PROJECTED` | 7 | PASS |

## ما لا يُقاس هنا

- **أثرُ الصنف على المحور الأوّل والثاني** — الصنفُ يُصدَر في الأوّل، فحكمُ الأوّل عليه سابقٌ على السقف.
- **تراكبُ الأصناف** — كلمةٌ تحمل صنفَين تحتها سقفان، و`meet` هو الحاكم؛ ولا يُقاس التراكبُ قبل أن يُسنَد صنفٌ واحد.
- **الرتبةُ الفعليّة** — هذه المصفوفةُ تقرأ السقفَ لا الرتبةَ الممنوحة؛ والرتبةُ من `meet` بأربعةِ مدخلات، وثلاثةٌ منها خارجَ هذا القياس.

