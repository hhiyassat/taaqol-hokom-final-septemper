# بنودُ ما خرج عن الولاية — تُقاس وتُعلَن، ولا تُلمس

```text
VENDOR_IS_FROZEN = TRUE
VENDOR_HEAD = 3cccdded7951ba71b3cb2a8b9b477f3fb3d91095
VENDOR_PORCELAIN_LINES = 0
CLAIM_PROJECT_FINISHED = NO
```

## الحقلُ الجامع — يُقرأ قبل البنود

```text
stages_total               16
runtime_implemented = True 14/16
runtime_implemented = False 2/16   PRE_WEIGHT_CAPACITY_AUDIT · ANSWER_AUDIT
stages_blocked_by_C1       12
```

تعقُّل مكتوبٌ إلا مرحلتين، وإحداهما تُغلق اثنتَي عشرة. فليست خمسةَ إصلاحاتٍ تُطلب من sonaiso، بل مرحلةٌ واحدةٌ تفتح اثنتَي عشرة، وأربعةٌ دونها.

## البنود

| البند | العنوان | الحال | الموضع |
|---|---|---|---|
| `C1` | PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة | `DECLARED` | `native_stage_registry.py:300` |
| `C2` | مفاتيحُ classify_token_paths غيرُ مشكولة | `DECLARED` | `native_stage_registry.py:105` |
| `C3` | startswith("ال") ⟶ JamidPath يعبر خطوطًا ممنوعة | `DECLARED` | `native_stage_registry.py:206` |
| `C4` | ANSWER_AUDIT غيرُ منفَّذة | `DECLARED` | `native_stage_registry.py:520` |
| `C5` | corpus_runner لا يستشير الحوامل ولا سجلَّ الخطوط | `DECLARED` | `corpus_runner.py:7` |
| `C_PATH` | المسلكُ المختار لبنود (ج) | `NOT_CHOSEN` | — |

### `C1` · PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:300` — `runtime_implemented=False`

```json
{
 "stages_closed_per_token": 12,
 "stages_closed_names": [
  "ANSWER_AUDIT",
  "CONTRACTABLE_UNIT",
  "DAL_MADLUL_BINDING",
  "DAL_ONLY",
  "HUKM",
  "IFADAH",
  "MANAT",
  "MUFRAD_DALALAH",
  "RELATION",
  "RELATION_CLOSURE",
  "TANZIL",
  "VERBAL_MADLUL"
 ],
 "command": "python -c \"from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus as R; r=R('probe',('مَاتَ',)); print(sum(1 for t in r.token_results for x in t.records if x.transition_state.value=='NOT_OPENED'))\""
}
```

### `C2` · مفاتيحُ classify_token_paths غيرُ مشكولة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:105` — `def classify_token_paths(surface: str) -> tuple[PathEvidence, ...]:`

```json
{
 "registry_keys": 11,
 "vocalized_keys": 0,
 "inventory_hit_unmarked": "11/11",
 "inventory_hit_unmarked_denominator": "مفاتيحُ الجرد",
 "inventory_hit_marked": "0/17",
 "inventory_hit_marked_denominator": "صورُ المصحف المشكولةُ لتلك المفاتيح",
 "inventory_hit_marked_source": "inspection/nazila/02_path_classifier.json · classified_by_the_closed_inventory",
 "finding": "المرحلةُ الوحيدةُ المنفَّذة تصيب على السطح المجرَّد وتخطئ على المشكول — والعلّةُ في مفاتيح الجرد.",
 "command": "python3 scripts/probe_path_classifier.py"
}
```

### `C3` · startswith("ال") ⟶ JamidPath يعبر خطوطًا ممنوعة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:206` — `if token.startswith("ال"):`

```json
{
 "corpus_words_matching": 10013,
 "corpus_words": 77411,
 "percent": 12.9,
 "crosses_queried": {
  "Grapheme→FunctionalLetter": true,
  "Orthography→Pronunciation": true,
  "Matching→Meaning": true
 },
 "all_three_forbidden": true,
 "query_used": "CANONICAL_REGISTRY.is_forbidden_direct(a, b)",
 "note": "العددُ سعةٌ، والخطُّ حجّة. والخطوطُ مُستفتاةٌ لا منقولة.",
 "command": "python3 scripts/build_upstream.py  (يستفتي السجلَّ حيًّا)"
}
```

### `C4` · ANSWER_AUDIT غيرُ منفَّذة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:520` — `runtime_implemented=False`

```json
{
 "seals_issued": 0,
 "seals_issued_denominator": "أختامٌ صدرت في أيّ تشغيل",
 "not_opened_by_C1": true,
 "note": "لا تُفتح بفتح C1 — فهي runtime_implemented=False",
 "command": "python -c \"from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus as R; r=R('probe',('مَاتَ',)); print(sum(1 for t in r.token_results for x in t.records if x.transition_state.value=='NOT_OPENED'))\""
}
```

### `C5` · corpus_runner لا يستشير الحوامل ولا سجلَّ الخطوط

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/corpus_runner.py:7` — `from taaqqul_slot_geometry.core.rank_lattice import Rank`

```json
{
 "imports": {
  "gamma": false,
  "ClosureState": false,
  "TransitionState": false,
  "forbidden_lines": false,
  "EntryBoundary": false
 },
 "none_present": true,
 "import_lines_in_runner": [
  1,
  3,
  4,
  5,
  7,
  8,
  13
 ],
 "cells_not_emitted": 35,
 "cells_not_emitted_denominator": "خاناتُ وثيقة النازلة (292)",
 "command": "grep -nE '^(import|from) ' vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/corpus_runner.py"
}
```

### `C_PATH` · المسلكُ المختار لبنود (ج)

```json
{
 "paths": [
  "ج-١ تُقاس وتُعلن",
  "ج-٢ بلاغٌ إلى المصدر",
  "ج-٣ فرعٌ مُعلَنٌ بـpin ثانٍ"
 ],
 "chosen": null,
 "currently": "ج-١ يجري",
 "paths_measured_ready": [
  "C1",
  "C2",
  "C3",
  "C5"
 ],
 "C4_not_a_request": true,
 "AUTHORITY_TO_SEND": "OWNER",
 "SENT": "NO",
 "command": "—"
}
```

## الحرّاس

| الحارس | مخالفات |
|---|---|
| `G_EVERY_NUMBER_HAS_A_COMMAND` | `لا شيء` |
| `G_LOCATION_RESOLVES` | `لا شيء` |
| `G_FORBIDDEN_LINES_QUERIED` | `لا شيء` |
| `G_DENOMINATOR_NAMED` | `لا شيء` |
| `G_JOINT_FIELD_PRESENT` | `لا شيء` |
| `G_NO_DONE_IN_C` | `لا شيء` |
