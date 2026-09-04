# بلاغُ ج-٢ — مصوغٌ وغيرُ مرسَل

```text
RECIPIENT = sonaiso/Taaqol-GPT
SENT = NO
AUTHORITY_TO_SEND = OWNER
VENDOR_PIN = 3cccdded7951ba71b3cb2a8b9b477f3fb3d91095
```

لا يُقترح إصلاحٌ بعينه: يُعرض العيبُ وقياسُه، والحلُّ لصاحب المستودع. و`C4` ليست في هذا البلاغ — هي إعلانُ حدٍّ لا طلبُ تغيير.

## C5 · corpus_runner لا يستشير الحوامل ولا سجلَّ الخطوط

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/corpus_runner.py:7` — `from taaqqul_slot_geometry.core.rank_lattice import Rank`

**القياس** (`grep -nE '^(import|from) ' vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/corpus_runner.py`):

```json
{
 "gamma": false,
 "ClosureState": false,
 "TransitionState": false,
 "forbidden_lines": false,
 "EntryBoundary": false
}
```

**ما لا يُدَّعى**: لم يُقترح تغييرٌ بعينه، ولم يُقس أثرُ أيّ إصلاحٍ على بقيّة المشغّل.

## C1 · PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:300` — `runtime_implemented=False`

**القياس** (`python -c "from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus as R; r=R('probe',('مَاتَ',)); print(sum(1 for t in r.token_results for x in t.records if x.transition_state.value=='NOT_OPENED'))"`):

```json
{
 "stages_closed_per_token": 12
}
```

**ما لا يُدَّعى**: لم يُقترح تغييرٌ بعينه، ولم يُقس أثرُ أيّ إصلاحٍ على بقيّة المشغّل.

## C2 · مفاتيحُ classify_token_paths غيرُ مشكولة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:105` — `def classify_token_paths(surface: str) -> tuple[PathEvidence, ...]:`

**القياس** (`python3 scripts/probe_path_classifier.py`):

```json
{
 "inventory_hit_unmarked": "11/11",
 "inventory_hit_marked": "0/17"
}
```

**ما لا يُدَّعى**: لم يُقترح تغييرٌ بعينه، ولم يُقس أثرُ أيّ إصلاحٍ على بقيّة المشغّل.

## C3 · startswith("ال") ⟶ JamidPath يعبر خطوطًا ممنوعة

**الموضع**: `vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/native_stage_registry.py:206` — `if token.startswith("ال"):`

**القياس** (`python3 scripts/build_upstream.py  (يستفتي السجلَّ حيًّا)`):

```json
{
 "corpus_words_matching": 10013,
 "corpus_words": 77411,
 "percent": 12.9,
 "crosses": {
  "Grapheme→FunctionalLetter": true,
  "Orthography→Pronunciation": true,
  "Matching→Meaning": true
 }
}
```

**ما لا يُدَّعى**: لم يُقترح تغييرٌ بعينه، ولم يُقس أثرُ أيّ إصلاحٍ على بقيّة المشغّل.
