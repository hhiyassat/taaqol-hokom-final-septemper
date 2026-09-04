# الأبواب — ثلاثةُ محاورَ لا واحد

```text
ما تملك الأداةُ إغلاقَه = 0
GROUNDED 207/292 خانة · STAGES_OPENED 1/16
VENDOR_HEAD = 3cccdded7951ba71b3cb2a8b9b477f3fb3d91095 · porcelain 0
CLAIM_PROJECT_FINISHED = NO
```

**ولا يُغيّر هذا الجدولُ علامةً واحدة.** الأبوابُ توصيفٌ لمن يملك ماذا، لا فتحٌ لبابٍ منها.

## الأبواب

| الباب | المالك | cells | correctness | ceiling | cost |
|---|---|---|---|---|---|
| `C5` | SONAISO | `42/292` | gamma=False · ClosureState=False · TransitionState=False · forbidden_lines=False | `NO_EFFECT_MEASURED` | تغييرٌ في بنية المشغّل — UNMEASURED كلفةً |
| `C1` | SONAISO | `17/292` | stages_closed_per_token=12 | `1/16 ⟶ 14/16` | سطرٌ في مرحلةٍ واحدة يفتح اثنتَي عشرة — تقديرٌ من قراءة المصدر، لا قياس |
| `C2` | SONAISO | `0/292` | inventory_hit_unmarked=11/11 · inventory_hit_marked=0/17 | `NO_EFFECT_MEASURED` | UNMEASURED |
| `C3` | SONAISO | `0/292` | corpus_words_matching=10013 · corpus_words=77411 · percent=12.9 · crosses={'Grapheme→FunctionalLetter': True, 'Orthography→Pronunciation': True, 'Matching→Meaning': True} | `NO_EFFECT_MEASURED` | UNMEASURED |
| `C4` | SONAISO | `0/292` | seals_issued=0 | `14/16 ⟶ 16/16` | UNMEASURED |
| `B2` | DR_HUSSEIN | `0/292` | classes=7 · words_affected=18143 · words_affected_denominator=كلماتُ الجرد المتأثّرة · by_class={'U_N7_2_INTERNAL_AL': 1616, 'U_TANWEEN': 8894, 'U_ALEF_MADDA': 1505, 'U_ALIF_MAQSURA': 2498, 'U_ALIF_FARIQA': 3561, 'U_UNVOCALIZED_CARRIER': 60, 'U_MULTIWORD_CELL': 9} | `NO_EFFECT_MEASURED` | سبعةُ قراراتٍ صغيرة — تقديرٌ من عدد الأصناف، لا قياس |

### `C5` · corpus_runner لا يستشير الحوامل ولا سجلَّ الخطوط

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/corpus_runner.py:7`

```json
{
 "cells": "42/292",
 "cells_denominator": "خاناتُ وثيقة النازلة",
 "correctness": {
  "gamma": false,
  "ClosureState": false,
  "TransitionState": false,
  "forbidden_lines": false,
  "EntryBoundary": false
 },
 "correctness_command": "grep -nE '^(import|from) ' vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/corpus_runner.py",
 "ceiling": "NO_EFFECT_MEASURED",
 "ceiling_note": "الاستشارةُ لا تفتح مرحلةً — تملأ حقولًا",
 "cost": "تغييرٌ في بنية المشغّل — UNMEASURED كلفةً"
}
```

### `C1` · PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:300`

```json
{
 "cells": "17/292",
 "cells_denominator": "خاناتُ وثيقة النازلة",
 "correctness": {
  "stages_closed_per_token": 12
 },
 "correctness_command": "python -c \"from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus as R; r=R('probe',('مَاتَ',)); print(sum(1 for t in r.token_results for x in t.records if x.transition_state.value=='NOT_OPENED'))\"",
 "ceiling": "1/16 ⟶ 14/16",
 "ceiling_note": "C4 لا تُفتح بفتح C1: هي `runtime_implemented=False` مثلها. فسقفُ فتح C1 هو أربعَ عشرةَ لا ستَّ عشرة.",
 "cost": "سطرٌ في مرحلةٍ واحدة يفتح اثنتَي عشرة — تقديرٌ من قراءة المصدر، لا قياس"
}
```

### `C2` · مفاتيحُ classify_token_paths غيرُ مشكولة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:105`
**لماذا سقط من الجدول السابق**: cells = 0 — وأثرُه في الصحّة لا في العدد: يصيب على المعيب ويخطئ على السليم

```json
{
 "cells": "0/292",
 "cells_denominator": "خاناتُ وثيقة النازلة",
 "correctness": {
  "inventory_hit_unmarked": "11/11",
  "inventory_hit_marked": "0/17"
 },
 "correctness_command": "python3 scripts/probe_path_classifier.py",
 "ceiling": "NO_EFFECT_MEASURED",
 "ceiling_note": "التصنيفُ لا يفتح مرحلةً",
 "cost": "UNMEASURED"
}
```

### `C3` · startswith("ال") ⟶ JamidPath يعبر خطوطًا ممنوعة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:206`

```json
{
 "cells": "0/292",
 "cells_denominator": "خاناتُ وثيقة النازلة",
 "correctness": {
  "corpus_words_matching": 10013,
  "corpus_words": 77411,
  "percent": 12.9,
  "crosses": {
   "Grapheme→FunctionalLetter": true,
   "Orthography→Pronunciation": true,
   "Matching→Meaning": true
  }
 },
 "correctness_command": "python3 scripts/build_upstream.py  (يستفتي السجلَّ حيًّا)",
 "ceiling": "NO_EFFECT_MEASURED",
 "ceiling_note": "القاعدةُ لا تفتح مرحلةً",
 "cost": "UNMEASURED"
}
```

### `C4` · ANSWER_AUDIT غيرُ منفَّذة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:520`

```json
{
 "cells": "0/292",
 "cells_denominator": "خاناتُ وثيقة النازلة",
 "correctness": {
  "seals_issued": 0
 },
 "correctness_command": "python -c \"from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus as R; r=R('probe',('مَاتَ',)); print(sum(1 for t in r.token_results for x in t.records if x.transition_state.value=='NOT_OPENED'))\"",
 "ceiling": "14/16 ⟶ 16/16",
 "ceiling_note": "لا تُفتح بفتح C1 — فهي runtime_implemented=False",
 "cost": "UNMEASURED"
}
```

### `B2` · أصنافُ البقيّة السبعة (T-4)


```json
{
 "cells": "0/292",
 "cells_denominator": "خاناتُ وثيقة النازلة",
 "correctness": {
  "classes": 7,
  "words_affected": 18143,
  "words_affected_denominator": "كلماتُ الجرد المتأثّرة",
  "by_class": {
   "U_N7_2_INTERNAL_AL": 1616,
   "U_TANWEEN": 8894,
   "U_ALEF_MADDA": 1505,
   "U_ALIF_MAQSURA": 2498,
   "U_ALIF_FARIQA": 3561,
   "U_UNVOCALIZED_CARRIER": 60,
   "U_MULTIWORD_CELL": 9
  }
 },
 "correctness_command": "python3 -m aslot compliance",
 "ceiling": "NO_EFFECT_MEASURED",
 "ceiling_note": "لا يمسّ مراحلَ تعقُّل — يفتح T-5 في أسلوط",
 "cost": "سبعةُ قراراتٍ صغيرة — تقديرٌ من عدد الأصناف، لا قياس"
}
```

## الحرّاس

| الحارس | مخالفات |
|---|---|
| `G_ALL_UPSTREAM_PRESENT` | `لا شيء` |
| `G_NO_AXIS_BLANK` | `لا شيء` |
| `G_NO_BIAS` | `لا شيء` |
| `G_B1_RETIRED` | `لا شيء` |
| `G_DOORS_DERIVED` | `لا شيء` |

## ذيلٌ — بابٌ حُسم فشُطب

* `B1` — حُسم `(أ) 1a7f8b76` بحكم DR_HUSSEIN. لم يعد بابًا — هويّةُ المدخل ثبتت
