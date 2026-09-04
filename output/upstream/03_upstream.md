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
stages_not_opened_today    12
stages_C1_would_open       11
still_closed_after_C1      ANSWER_AUDIT
reachable_on_a_content_token 14/16   (16 − 1 − 1 = 14)
```

تعقُّل مكتوبٌ إلا مرحلتين، وإحداهما تُغلق اثنتَي عشرة. فليست خمسةَ إصلاحاتٍ تُطلب من sonaiso، بل مرحلةٌ واحدةٌ تفتح اثنتَي عشرة، وأربعةٌ دونها.

## البنود

| البند | العنوان | الحال | الموضع |
|---|---|---|---|
| `C1` | PRE_WEIGHT مبنيّةُ الحوامل، غيرُ موصولةٍ بالمشغّل | `DECLARED` | `native_stage_registry.py:300` |
| `C2` | مفاتيحُ classify_token_paths غيرُ مشكولة | `DECLARED` | `native_stage_registry.py:105` |
| `C3` | startswith("ال") ⟶ JamidPath يعبر خطوطًا ممنوعة | `DECLARED` | `native_stage_registry.py:206` |
| `C4` | ANSWER_AUDIT غيرُ منفَّذة | `DECLARED` | `native_stage_registry.py:520` |
| `C5` | corpus_runner لا يستشير الحوامل ولا سجلَّ الخطوط | `DECLARED` | `corpus_runner.py:7` |
| `C_PATH` | المسلكُ المختار لبنود (ج) | `NOT_CHOSEN` | — |

### `C1` · PRE_WEIGHT مبنيّةُ الحوامل، غيرُ موصولةٍ بالمشغّل

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:300` — `runtime_implemented=False`

**العنوانُ السابق**: «PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة» — DR_HUSSEIN — بعد قياسِ القانون والحوامل والاختبارات، وقياسِ غياب الوصلة وحدَه. والدعوى تُقيَّد لا تُمحى.

**علّةٌ مشتركة** `SHARED_CAUSE_RUNNER_NOT_WIRED` مع C5 — المشغّلُ لا يصل إلى ما بُني — لا يستورد الحوامل، ولا يفتح المرحلةَ التي تستدعيها.

```text
C1 17 خانة  ·  C5 42 خانة  ·  ∩ 0  ·  ∪ 59
MERGED = FALSE   (17 + 42 = 59 — ولا يُكتب عددًا)
DISJOINTNESS_BASIS = BY_DESIGN
MEMBERSHIP_IS_THE_BASIS = FALSE
```

SHARED_CAUSE_IS_NOT_SHARED_EFFECT — اتّحادُ العلّة لا يُثبت اتّحادَ الأثر.

**أساسُ التباين**: reason_family حقلٌ واحدٌ لكلّ خانة، فلا خانةَ تحمل أسرتين. والحقلُ لا يحتمل العضويّةَ المزدوجة أصلًا.

**والعضويّة**: تعضيدٌ لا أساس: ∩ = 0 خبرٌ عن هذا التشغيل، والتصميمُ خبرٌ عن البنية. ولو تعارضا لكان التصميمُ هو المتَّهَم.

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
 "pre_weight_state": {
  "laws_ratified": {
   "docs/20_PRE_WEIGHT_LICENSING_LAW.md": 675,
   "docs/22_PRE_WEIGHT_PATH_GATE_LAW.md": 183,
   "docs/23_PRE_WEIGHT_CHAIN_OPERATIONS_LAW.md": 209
  },
  "prs_shipped": {
   "PR-10": {
    "module": "taaqqul_slot_geometry.weight.pre_weight",
    "importable": true,
    "symbols_promised": 6,
    "missing": [],
    "shipped": true
   },
   "PR-11": {
    "module": "taaqqul_slot_geometry.weight.path_gate",
    "importable": true,
    "symbols_promised": 4,
    "missing": [],
    "shipped": true
   },
   "PR-12": {
    "module": "taaqqul_slot_geometry.weight.mu_chain",
    "importable": true,
    "symbols_promised": 3,
    "missing": [],
    "shipped": true
   },
   "PR-13": {
    "module": "taaqqul_slot_geometry.weight.weight_fit",
    "importable": true,
    "symbols_promised": 4,
    "missing": [],
    "shipped": true
   }
  },
  "prs_shipped_count": "4/4",
  "prs_shipped_denominator": "PR-10..PR-13 — ما يَعِد به قانونُ docs/20",
  "carrier_tests": {
   "files_direct": [
    "test_mu_chain.py",
    "test_path_gate_pre_weight.py",
    "test_weight_fit.py"
   ],
   "files_direct_denominator": "ملفُّ اختبارٍ يستورد حاملًا ويحمل اسمَه",
   "files_importing_a_carrier": 22,
   "files_importing_a_carrier_denominator": "مقامٌ أوسع — يُذكر ولا يُخلط بالأوّل",
   "passed": 107,
   "failed": false,
   "summary": "107 passed in 0.33s",
   "command": "PYTHONPATH=src python -m pytest -q tests/test_mu_chain.py tests/test_path_gate_pre_weight.py tests/test_weight_fit.py"
  },
  "runner_imports_touching_weight": [],
  "runner_is_wired_to_carriers": false,
  "stage_runtime_implemented": false,
  "reading": "القانونُ مصادَقٌ والحواملُ مشحونةٌ واختباراتُها تمرّ — والمشغّلُ لا يستوردها. فالفجوةُ وصلةٌ، لا بناء.",
  "supersedes_description": "«غيرُ منفَّذة»",
  "superseded_because": "الوصفُ الأوّلُ يُقرأ نفيًا للبناء كلِّه، وهو مقيسٌ موجودًا.",
  "command": ".venv-taaqol/bin/python scripts/build_upstream.py"
 },
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
 "what_remains_evidence": {
  "claim": "قاعدةٌ تُصنّف بالرسم الإملائيّ، وتمسّ 12.9٪ من الجرد",
  "matched": 10013,
  "denominator": 77411,
  "denominator_note": "كلماتُ جرد المحور صفر",
  "input_drawn_from": "runtime/native_stage_registry.py",
  "status": "EVIDENCE",
  "raise_to_source": true
 },
 "crossing_claim": {
  "was": "startswith(\"ال\") ⟶ JamidPath يعبر خطوطًا ممنوعة — crosses: True ×3",
  "crosses_queried": {
   "Grapheme→FunctionalLetter": true,
   "Orthography→Pronunciation": true,
   "Matching→Meaning": true
  },
  "all_three_forbidden": true,
  "query_used": "CANONICAL_REGISTRY.is_forbidden_direct(a, b)",
  "input_drawn_from": "CANONICAL_REGISTRY.lines",
  "crosses": "TAUTOLOGY",
  "crosses_why": "الأزواجُ الثلاثةُ من السجلّ، فتردّ True بحكم الأخذ لا بحكم الواقع.",
  "mapping": "NOT_DERIVABLE",
  "mapping_why": "أنّ startswith(\"ال\") هو Grapheme→FunctionalLetter ليس في الشيفرة ما يدلّ عليه: لا Grapheme ولا FunctionalLetter اسمُ طبقةٍ ولا مرحلة.",
  "status": "OWNER_RULING_REQUIRED",
  "withdrawn": false,
  "retained_because": "الدعوى تُقيَّد لا تُمحى.",
  "raise_to_source": false
 },
 "note": "العددُ سعةٌ مقيسة، ودعوى العبور موقوفةٌ على حكم المالك.",
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

**علّةٌ مشتركة** `SHARED_CAUSE_RUNNER_NOT_WIRED` مع C1 — المشغّلُ لا يصل إلى ما بُني — لا يستورد الحوامل، ولا يفتح المرحلةَ التي تستدعيها.

```text
C1 17 خانة  ·  C5 42 خانة  ·  ∩ 0  ·  ∪ 59
MERGED = FALSE   (17 + 42 = 59 — ولا يُكتب عددًا)
DISJOINTNESS_BASIS = BY_DESIGN
MEMBERSHIP_IS_THE_BASIS = FALSE
```

SHARED_CAUSE_IS_NOT_SHARED_EFFECT — اتّحادُ العلّة لا يُثبت اتّحادَ الأثر.

**أساسُ التباين**: reason_family حقلٌ واحدٌ لكلّ خانة، فلا خانةَ تحمل أسرتين. والحقلُ لا يحتمل العضويّةَ المزدوجة أصلًا.

**والعضويّة**: تعضيدٌ لا أساس: ∩ = 0 خبرٌ عن هذا التشغيل، والتصميمُ خبرٌ عن البنية. ولو تعارضا لكان التصميمُ هو المتَّهَم.

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
 "cells_runner_does_not_consult": "35/292",
 "cells_runner_does_not_consult_denominator": "خاناتُ وثيقة النازلة",
 "cells_entry_boundary_not_constructed": "7/292",
 "cells_entry_boundary_not_constructed_denominator": "خاناتُ وثيقة النازلة",
 "cells_C5_total": "42/292",
 "cells_C5_total_denominator": "خاناتُ وثيقة النازلة",
 "entry_boundary_placement": "INSIDE_C5_AS_A_NAMED_PART",
 "entry_boundary_is_a_fifth_door": false,
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
| `G_EVIDENCE_IS_NOT_TAUTOLOGY` | `لا شيء` |
| `G_SHARED_CAUSE_NOT_MERGED` | `لا شيء` |
| `G_DENOMINATOR_NAMED` | `لا شيء` |
| `G_JOINT_FIELD_PRESENT` | `لا شيء` |
| `G_NO_DONE_IN_C` | `لا شيء` |
