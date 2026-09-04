# مصفوفة تعقّل للنازلة — محتوًى من الكود وحدَه

```text
GENERATED_BY        = scripts/build_nazila_matrix.py
CONTENT_SOURCE      = CODE_ONLY
CLAIM_PROJECT_FINISHED = NO
```

## رأس الوثيقة

*من الكود 10 · غير متوفرة 4*

| الخانة | القيمة | المصدر |
|---|---|---|
| `INPUT_TEXT` | مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ، فَأَرَادَ وَارِثُهُ طَرْدَهَا، فَتَحَاكَمَا. | الملفّ |
| `INPUT_SHA256` | `1a7f8b76d719bc019fe200ea952cce211a7a4283814d9cee0d04a39251d8b3e2` | hashlib |
| `CORPUS_ID` | `nazila` | الوسيط |
| `RUN_ID` | `native:nazila` | run_native_corpus |
| `STAGE_COVERAGE` | `16/16` | عدُّ المراحل |
| `RUNTIME_EXECUTION` | 1/16 EXECUTED | عدُّ الحالات |
| `MEASURED_RECORDS` | 160 = 10 × 16 | عدُّ السجلّات |
| `FINAL_HUKM` | `NOT_OPENED` | حالُ HUKM |
| `FINAL_TANZIL` | `NOT_OPENED` | حالُ TANZIL |
| `VENDOR_HEAD` | `3cccdded7951ba71b3cb2a8b9b477f3fb3d91095` | git rev-parse |
| `DOCUMENT_LABEL` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `LAYER_RULE` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `NO_LAYER_MIXING` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `REPRODUCES` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |

## 0. حدّ الدخول المعلن

*من الكود 0 · غير متوفرة 7*

| الخانة | القيمة | المصدر |
|---|---|---|
| `declared_entry_kind` | غير متوفرة · `NOT_CONSTRUCTED_IN_SOURCE` | — |
| `representation_status` | غير متوفرة · `NOT_CONSTRUCTED_IN_SOURCE` | — |
| `ontological_status` | غير متوفرة · `NOT_CONSTRUCTED_IN_SOURCE` | — |
| `sound_status` | غير متوفرة · `NOT_CONSTRUCTED_IN_SOURCE` | — |
| `meaning_status` | غير متوفرة · `NOT_CONSTRUCTED_IN_SOURCE` | — |
| `prior_trace_status` | غير متوفرة · `NOT_CONSTRUCTED_IN_SOURCE` | — |
| `produces_only` | غير متوفرة · `NOT_CONSTRUCTED_IN_SOURCE` | — |

## 1. بطاقة النازلة

*من الكود 1 · غير متوفرة 5*

| الخانة | القيمة | المصدر |
|---|---|---|
| `عدد التوكنات المقيسة` | `10` | len(text.split()) |
| `نوع المدخل` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `طبيعة النص` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `محل النزاع الظاهر` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `ما يجوز إنتاجه الآن` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `ما لا يجوز إنتاجه الآن` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |

## 2. بصمة القياس

*من الكود 9 · غير متوفرة 1*

| الخانة | القيمة | المصدر |
|---|---|---|
| `taaqol_commit` | `3cccdded7951ba71b3cb2a8b9b477f3fb3d91095` | git rev-parse |
| `pin_matches` | `True` | مقابلةُ التثبيت |
| `sha256(INPUT_TEXT)` | `1a7f8b76d719bc019fe200ea952cce211a7a4283814d9cee0d04a39251d8b3e2` | hashlib |
| `python` | `3.11.15` | platform |
| `platform` | Linux x86_64 | platform |
| `utc_timestamp` | `2026-09-03T04:09:24+00:00` | datetime |
| `corpus_id` | `nazila` | الوسيط |
| `run_id` | `native:nazila` | run_native_corpus |
| `runner` | `runtime.corpus_runner.run_native_corpus` | الاستيراد |
| `MEASURED_BY` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |

## 3. الجرد المغلق المستعمل

*من الكود 6 · غير متوفرة 0*

| الخانة | القيمة | المصدر |
|---|---|---|
| `Rank` | `ZERO` · `TRACE` · `CANDIDATE` · `HYPOTHESIS` · `LICENSED` · `STRONG` · `CERTIFICATE` | سردُ أعضاء التعداد |
| `ClosureState` | `OPEN` · `MINIMALLY_CLOSED` · `PERFORATED_CLOSED` · `BLOCKED` · `INVALID` · `FORBIDDEN_LEAP` | سردُ أعضاء التعداد |
| `TransitionState` | `APPROVED` · `DEFERRED` · `BLOCKED` · `REJECTED` · `FORBIDDEN_LEAP` | سردُ أعضاء التعداد |
| `StageTransitionState` | `EXECUTED` · `BLOCKED` · `DEFERRED` · `DECLARED_NOT_IMPLEMENTED` · `NOT_OPENED` · `NOT_APPLICABLE` | سردُ أعضاء التعداد |
| `FailureCode (الجرد كلُّه)` | `92` | len(list(FailureCode)) |
| `FailureCode المستعمل في الخطوط` | `FORBIDDEN_STRAIGHT_LINE` | ForbiddenLine.failure_code |

## 4. مصفوفة المراحل الست عشرة

*من الكود 64 · غير متوفرة 32*

| الخانة | القيمة | المصدر |
|---|---|---|
| `1. PATH_CLASSIFICATION · StageTransitionState` | `EXECUTED` | السجلّ |
| `1. PATH_CLASSIFICATION · الرتبة` | `ZERO->ZERO` | السجلّ |
| `1. PATH_CLASSIFICATION · hint` | `—` | السجلّ |
| `1. PATH_CLASSIFICATION · residuals_after` | `—` | السجلّ |
| `1. PATH_CLASSIFICATION · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `1. PATH_CLASSIFICATION · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `2. PRE_WEIGHT_CAPACITY_AUDIT · StageTransitionState` | `DECLARED_NOT_IMPLEMENTED` | السجلّ |
| `2. PRE_WEIGHT_CAPACITY_AUDIT · الرتبة` | `ZERO->ZERO` | السجلّ |
| `2. PRE_WEIGHT_CAPACITY_AUDIT · hint` | `runtime_implementation_missing` | السجلّ |
| `2. PRE_WEIGHT_CAPACITY_AUDIT · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `2. PRE_WEIGHT_CAPACITY_AUDIT · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `2. PRE_WEIGHT_CAPACITY_AUDIT · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `3. DAL_ONLY · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `3. DAL_ONLY · الرتبة` | `ZERO->ZERO` | السجلّ |
| `3. DAL_ONLY · hint` | `previous_gate_not_proven` | السجلّ |
| `3. DAL_ONLY · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `3. DAL_ONLY · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `3. DAL_ONLY · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `4. VERBAL_MADLUL · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `4. VERBAL_MADLUL · الرتبة` | `ZERO->ZERO` | السجلّ |
| `4. VERBAL_MADLUL · hint` | `previous_gate_not_proven` | السجلّ |
| `4. VERBAL_MADLUL · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `4. VERBAL_MADLUL · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `4. VERBAL_MADLUL · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `5. DAL_MADLUL_BINDING · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `5. DAL_MADLUL_BINDING · الرتبة` | `ZERO->ZERO` | السجلّ |
| `5. DAL_MADLUL_BINDING · hint` | `previous_gate_not_proven` | السجلّ |
| `5. DAL_MADLUL_BINDING · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `5. DAL_MADLUL_BINDING · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `5. DAL_MADLUL_BINDING · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `6. CONTRACTABLE_UNIT · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `6. CONTRACTABLE_UNIT · الرتبة` | `ZERO->ZERO` | السجلّ |
| `6. CONTRACTABLE_UNIT · hint` | `previous_gate_not_proven` | السجلّ |
| `6. CONTRACTABLE_UNIT · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `6. CONTRACTABLE_UNIT · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `6. CONTRACTABLE_UNIT · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `7. RELATION · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `7. RELATION · الرتبة` | `ZERO->ZERO` | السجلّ |
| `7. RELATION · hint` | `previous_gate_not_proven` | السجلّ |
| `7. RELATION · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `7. RELATION · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `7. RELATION · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `8. FORMAL_SHAPE · StageTransitionState` | `DEFERRED` | السجلّ |
| `8. FORMAL_SHAPE · الرتبة` | `ZERO->ZERO` | السجلّ |
| `8. FORMAL_SHAPE · hint` | `missing_context:FORMAL_ONLY` | السجلّ |
| `8. FORMAL_SHAPE · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `8. FORMAL_SHAPE · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `8. FORMAL_SHAPE · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `9. MUFRAD_DALALAH · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `9. MUFRAD_DALALAH · الرتبة` | `ZERO->ZERO` | السجلّ |
| `9. MUFRAD_DALALAH · hint` | `previous_gate_not_proven` | السجلّ |
| `9. MUFRAD_DALALAH · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `9. MUFRAD_DALALAH · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `9. MUFRAD_DALALAH · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `10. RELATION_CLOSURE · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `10. RELATION_CLOSURE · الرتبة` | `ZERO->ZERO` | السجلّ |
| `10. RELATION_CLOSURE · hint` | `previous_gate_not_proven` | السجلّ |
| `10. RELATION_CLOSURE · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `10. RELATION_CLOSURE · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `10. RELATION_CLOSURE · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `11. IFADAH · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `11. IFADAH · الرتبة` | `ZERO->ZERO` | السجلّ |
| `11. IFADAH · hint` | `previous_gate_not_proven` | السجلّ |
| `11. IFADAH · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `11. IFADAH · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `11. IFADAH · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `12. HUKM · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `12. HUKM · الرتبة` | `ZERO->ZERO` | السجلّ |
| `12. HUKM · hint` | `previous_gate_not_proven` | السجلّ |
| `12. HUKM · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `12. HUKM · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `12. HUKM · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `13. MANAT · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `13. MANAT · الرتبة` | `ZERO->ZERO` | السجلّ |
| `13. MANAT · hint` | `previous_gate_not_proven` | السجلّ |
| `13. MANAT · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `13. MANAT · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `13. MANAT · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `14. TANZIL · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `14. TANZIL · الرتبة` | `ZERO->ZERO` | السجلّ |
| `14. TANZIL · hint` | `previous_gate_not_proven` | السجلّ |
| `14. TANZIL · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `14. TANZIL · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `14. TANZIL · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `15. ANSWER_AUDIT · StageTransitionState` | `NOT_OPENED` | السجلّ |
| `15. ANSWER_AUDIT · الرتبة` | `ZERO->ZERO` | السجلّ |
| `15. ANSWER_AUDIT · hint` | `previous_gate_not_proven` | السجلّ |
| `15. ANSWER_AUDIT · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `15. ANSWER_AUDIT · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `15. ANSWER_AUDIT · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `16. NON_CONTENT_FORMAL_ROUTE · StageTransitionState` | `NOT_APPLICABLE` | السجلّ |
| `16. NON_CONTENT_FORMAL_ROUTE · الرتبة` | `ZERO->ZERO` | السجلّ |
| `16. NON_CONTENT_FORMAL_ROUTE · hint` | `—` | السجلّ |
| `16. NON_CONTENT_FORMAL_ROUTE · residuals_after` | `RUNTIME_CONTEXT_PENDING` | السجلّ |
| `16. NON_CONTENT_FORMAL_ROUTE · ClosureState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |
| `16. NON_CONTENT_FORMAL_ROUTE · TransitionState` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |

## 4.b شكل سجل التنفيذ وقواعده

*من الكود 8 · غير متوفرة 0*

| الخانة | القيمة | المصدر |
|---|---|---|
| `حقولُ StageExecutionRecord` | `run_id` · `corpus_id` · `token_id` · `span_id` · `stage_id` · `path_id` · `input_carrier_id` · `output_carrier_id` · `applicability` · `transition_state` · `evidence_refs` · `rank_before` · `rank_after` · `residuals_before` · `residuals_after` · `identity_invariants_checked` · `trace_parent_ids` · `trace_entry_id` · `failure_code` · `remediation_hints` · `next_admissible_stage_ids` · `source_commit_sha` · `registry_version` · `registry_hash` | __dataclass_fields__ |
| `Rule 1` | no output carrier without preserved input carrier. | تعليقاتُ execution_record.py |
| `Rule 3` | no implicit rank upgrade. | تعليقاتُ execution_record.py |
| `Rule 4` | no residual deletion. | تعليقاتُ execution_record.py |
| `Rule 6` | no executed stage without traceability. | تعليقاتُ execution_record.py |
| `Rule 7` | deferred must declare missing condition. | تعليقاتُ execution_record.py |
| `Rule 8` | blocked must carry failure code. | تعليقاتُ execution_record.py |
| `Rule 9` | NOT_APPLICABLE requires NOT_APPLICABLE applicability. | تعليقاتُ execution_record.py |

## 5. سجل الأثر والأدلة

*من الكود 4 · غير متوفرة 1*

| الخانة | القيمة | المصدر |
|---|---|---|
| `evidence_refs (عيّنة)` | `token:t000` | السجلّ |
| `trace_entry_id (عيّنة)` | `trace:t000:PATH_CLASSIFICATION` | السجلّ |
| `trace_parent_ids (عيّنة)` | `trace:t000` | السجلّ |
| `سجلّاتٌ بمرجع أثر` | `160` | عدٌّ |
| `سقفُ الرتبة لكلّ دليل` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |

## 6. البقايا المقيسة

*من الكود 6 · غير متوفرة 1*

| الخانة | القيمة | المصدر |
|---|---|---|
| `hint · missing_context:FORMAL_ONLY` | `10` | عدٌّ من remediation_hints |
| `hint · previous_gate_not_proven` | `120` | عدٌّ من remediation_hints |
| `hint · runtime_implementation_missing` | `10` | عدٌّ من remediation_hints |
| `residual · RUNTIME_CONTEXT_PENDING` | `150` | عدٌّ من residuals_after |
| `TOTAL_STAGE_RECORDS` | `160` | عدٌّ |
| `EMPTY_RESIDUAL_ROWS` | `10` | عدٌّ |
| `HIDDEN_RESIDUALS` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |

## 7. فجوة القانون والمشغّل

*من الكود 5 · غير متوفرة 1*

| الخانة | القيمة | المصدر |
|---|---|---|
| `corpus_runner يستورد gamma` | `False` | فحصُ مصدر المشغّل |
| `corpus_runner يستورد ClosureState` | `False` | فحصُ مصدر المشغّل |
| `corpus_runner يستورد TransitionState` | `False` | فحصُ مصدر المشغّل |
| `corpus_runner يستورد forbidden_lines` | `False` | فحصُ مصدر المشغّل |
| `corpus_runner يستورد EntryBoundary` | `False` | فحصُ مصدر المشغّل |
| `حكم الوثيقة` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |

## 8. مصفوفة الألفاظ: ما يجوز وما لا يجوز

*من الكود 30 · غير متوفرة 20*

| الخانة | القيمة | المصدر |
|---|---|---|
| `t000 · اللفظ` | `مَاتَ` | التوكنات |
| `t000 · path_id` | `RootStemPath` | classify_token_paths |
| `t000 · confidence` | `0.55` | classify_token_paths |
| `t000 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t000 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t001 · اللفظ` | `مَلِكٌ` | التوكنات |
| `t001 · path_id` | `RootStemPath` | classify_token_paths |
| `t001 · confidence` | `0.55` | classify_token_paths |
| `t001 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t001 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t002 · اللفظ` | `عَنْ` | التوكنات |
| `t002 · path_id` | `RootStemPath` | classify_token_paths |
| `t002 · confidence` | `0.55` | classify_token_paths |
| `t002 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t002 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t003 · اللفظ` | `أُخْتٍ` | التوكنات |
| `t003 · path_id` | `RootStemPath` | classify_token_paths |
| `t003 · confidence` | `0.55` | classify_token_paths |
| `t003 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t003 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t004 · اللفظ` | `سَاكِنَةٍ` | التوكنات |
| `t004 · path_id` | `RootStemPath` | classify_token_paths |
| `t004 · confidence` | `0.55` | classify_token_paths |
| `t004 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t004 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t005 · اللفظ` | `مَعَهُ،` | التوكنات |
| `t005 · path_id` | `RootStemPath` | classify_token_paths |
| `t005 · confidence` | `0.55` | classify_token_paths |
| `t005 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t005 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t006 · اللفظ` | `فَأَرَادَ` | التوكنات |
| `t006 · path_id` | `RootStemPath` | classify_token_paths |
| `t006 · confidence` | `0.55` | classify_token_paths |
| `t006 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t006 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t007 · اللفظ` | `وَارِثُهُ` | التوكنات |
| `t007 · path_id` | `RootStemPath` | classify_token_paths |
| `t007 · confidence` | `0.55` | classify_token_paths |
| `t007 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t007 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t008 · اللفظ` | `طَرْدَهَا،` | التوكنات |
| `t008 · path_id` | `RootStemPath` | classify_token_paths |
| `t008 · confidence` | `0.55` | classify_token_paths |
| `t008 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t008 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `t009 · اللفظ` | `فَتَحَاكَمَا.` | التوكنات |
| `t009 · path_id` | `RootStemPath` | classify_token_paths |
| `t009 · confidence` | `0.55` | classify_token_paths |
| `t009 · إفادة لغوية محتملة` | غير متوفرة · `NOT_OPENED:VERBAL_MADLUL` | — |
| `t009 · ما لا يجوز أخذه منه وحده` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |

## 9. العلاقات اللغوية والحدود

*من الكود 1 · غير متوفرة 3*

| الخانة | القيمة | المصدر |
|---|---|---|
| `حالُ RELATION_CLOSURE` | `NOT_OPENED` | السجلّ |
| `RELATION_CLOSED_COUNT` | غير متوفرة · `NOT_OPENED:RELATION_CLOSURE` | — |
| `NO_ADJACENT_PAIR_CLOSURE` | غير متوفرة · `NOT_OPENED:RELATION_CLOSURE` | — |
| `صفوفُ العلاقات` | غير متوفرة · `NOT_OPENED:RELATION` | — |

## 10. المنطوق والمفهوم

*من الكود 0 · غير متوفرة 3*

| الخانة | القيمة | المصدر |
|---|---|---|
| `المنطوق` | غير متوفرة · `NOT_OPENED:MUFRAD_DALALAH` | — |
| `مفهوم الموافقة` | غير متوفرة · `NOT_OPENED:MUFRAD_DALALAH` | — |
| `مفهوم المخالفة` | غير متوفرة · `NOT_OPENED:MUFRAD_DALALAH` | — |

## 11. الخطوط المستقيمة الممنوعة

*من الكود 50 · غير متوفرة 1*

| الخانة | القيمة | المصدر |
|---|---|---|
| `عدد الخطوط في السجل` | `47` | CANONICAL_REGISTRY |
| `حقولُ كلّ خطّ` | `source` · `target` · `reason` · `required_bridge` · `origin_law` · `failure_code` | __dataclass_fields__ |
| `أزواجٌ (مصدر ⟶ هدف) متمايزة` | `44/47` | عدٌّ |
| `Binary -> Text` | FORBIDDEN_STRAIGHT_LINE · EncodingIdentityGate | CANONICAL_REGISTRY |
| `Unicode -> ArabicLetter #1` | FORBIDDEN_STRAIGHT_LINE · LetterIdentityGate | CANONICAL_REGISTRY |
| `CodePoint -> Phoneme #2` | FORBIDDEN_STRAIGHT_LINE · PhoneticRealisationGate | CANONICAL_REGISTRY |
| `Grapheme -> FunctionalLetter #3` | FORBIDDEN_STRAIGHT_LINE · LetterFunctionGate | CANONICAL_REGISTRY |
| `HarakaMark -> CaseFunction` | FORBIDDEN_STRAIGHT_LINE · HarakaFunctionGate | CANONICAL_REGISTRY |
| `Orthography -> Pronunciation` | FORBIDDEN_STRAIGHT_LINE · PhoneticRealisationGate | CANONICAL_REGISTRY |
| `Pronunciation -> Syllable` | FORBIDDEN_STRAIGHT_LINE · SyllableStructureGate | CANONICAL_REGISTRY |
| `Syllable -> Word` | FORBIDDEN_STRAIGHT_LINE · LexicalIdentityGate | CANONICAL_REGISTRY |
| `Signifier -> WordForm` | FORBIDDEN_STRAIGHT_LINE · MorphologicalRealisationGate | CANONICAL_REGISTRY |
| `WordForm -> Meaning` | FORBIDDEN_STRAIGHT_LINE · SignificationGate | CANONICAL_REGISTRY |
| `Root -> LexicalMeaning` | FORBIDDEN_STRAIGHT_LINE · DerivationGate | CANONICAL_REGISTRY |
| `Weight -> Agency` | FORBIDDEN_STRAIGHT_LINE · RelationRoleGate | CANONICAL_REGISTRY |
| `Pattern -> SyntaxRole` | FORBIDDEN_STRAIGHT_LINE · RelationRoleGate | CANONICAL_REGISTRY |
| `VerbalSignified -> PureConcept` | FORBIDDEN_STRAIGHT_LINE · ConceptualAbstractionGate | CANONICAL_REGISTRY |
| `Wadʿ -> Dalālah` | FORBIDDEN_STRAIGHT_LINE · DomainBoundDalalahGate | CANONICAL_REGISTRY |
| `Dalālah -> ContextualMeaning` | FORBIDDEN_STRAIGHT_LINE · ContextualResolutionGate | CANONICAL_REGISTRY |
| `PureConcept -> IntendedMeaning` | FORBIDDEN_STRAIGHT_LINE · IntentAttributionGate | CANONICAL_REGISTRY |
| `Context -> Relation` | FORBIDDEN_STRAIGHT_LINE · RelationDeclarationGate | CANONICAL_REGISTRY |
| `Relation -> Ifādah` | FORBIDDEN_STRAIGHT_LINE · IfadahGate | CANONICAL_REGISTRY |
| `Ifādah -> Judgment` | FORBIDDEN_STRAIGHT_LINE · JudgmentGate | CANONICAL_REGISTRY |
| `Judgment -> Application` | FORBIDDEN_STRAIGHT_LINE · ApplicationGate | CANONICAL_REGISTRY |
| `Evidence -> Certainty` | FORBIDDEN_STRAIGHT_LINE · RankLattice (no auto-promote) | CANONICAL_REGISTRY |
| `LexiconEntry -> Candidate` | FORBIDDEN_STRAIGHT_LINE · LexiconEvidenceGate | CANONICAL_REGISTRY |
| `Candidate -> Certificate` | FORBIDDEN_STRAIGHT_LINE · CertificationGate | CANONICAL_REGISTRY |
| `ResidualHidden -> ApprovedOutput` | FORBIDDEN_STRAIGHT_LINE · ResidualPolicy (visibility) | CANONICAL_REGISTRY |
| `RankBelow -> RankAbove` | FORBIDDEN_STRAIGHT_LINE · TransitionGate + RankLattice | CANONICAL_REGISTRY |
| `Tool -> Knowledge` | FORBIDDEN_STRAIGHT_LINE · ToolBoundaryGate | CANONICAL_REGISTRY |
| `Number -> Knowledge` | FORBIDDEN_STRAIGHT_LINE · ToolBoundaryGate | CANONICAL_REGISTRY |
| `LCNV -> Knowledge` | FORBIDDEN_STRAIGHT_LINE · ToolBoundaryGate | CANONICAL_REGISTRY |
| `HumanVoice -> ArabicText` | FORBIDDEN_STRAIGHT_LINE · AudioDecodingGate + ASRGate | CANONICAL_REGISTRY |
| `BinaryAudio -> Text` | FORBIDDEN_STRAIGHT_LINE · AudioDecodingGate | CANONICAL_REGISTRY |
| `BinaryAudio -> UnicodeText` | FORBIDDEN_STRAIGHT_LINE · AudioDecodingGate + ASRGate | CANONICAL_REGISTRY |
| `BinaryAudio -> Meaning` | FORBIDDEN_STRAIGHT_LINE · Full pre-text + interpretation chain | CANONICAL_REGISTRY |
| `BinaryText -> Unicode` | FORBIDDEN_STRAIGHT_LINE · EncodingDecodeGate | CANONICAL_REGISTRY |
| `BinaryText -> ArabicLetter` | FORBIDDEN_STRAIGHT_LINE · EncodingDecodeGate + LetterIdentityGate | CANONICAL_REGISTRY |
| `Unicode -> ArabicText` | FORBIDDEN_STRAIGHT_LINE · UnicodeTextNormalizationGate | CANONICAL_REGISTRY |
| `Unicode -> ArabicLetter #36` | FORBIDDEN_STRAIGHT_LINE · ArabicLetterIdentityGate | CANONICAL_REGISTRY |
| `CodePoint -> Phoneme #37` | FORBIDDEN_STRAIGHT_LINE · PhonemeEvidenceBridge | CANONICAL_REGISTRY |
| `Grapheme -> FunctionalLetter #38` | FORBIDDEN_STRAIGHT_LINE · FunctionalLetterGate | CANONICAL_REGISTRY |
| `VocalizedText -> ValidAnalysis` | FORBIDDEN_STRAIGHT_LINE · TextEntryValidationGate | CANONICAL_REGISTRY |
| `DeclaredEntry -> OntologicalOrigin` | FORBIDDEN_STRAIGHT_LINE · none — refusal is constitutional | CANONICAL_REGISTRY |
| `Identity -> Truth` | FORBIDDEN_STRAIGHT_LINE · Gamma + Gate + Evidence + Rank | CANONICAL_REGISTRY |
| `Matching -> Meaning` | FORBIDDEN_STRAIGHT_LINE · Signification chain + Gate | CANONICAL_REGISTRY |
| `Potentiality -> Actuality` | FORBIDDEN_STRAIGHT_LINE · Opening control + Closure + Gate | CANONICAL_REGISTRY |
| `Opening -> Closure` | FORBIDDEN_STRAIGHT_LINE · Γ then Gate | CANONICAL_REGISTRY |
| `Closure -> Certificate` | FORBIDDEN_STRAIGHT_LINE · Rank lattice + Gate | CANONICAL_REGISTRY |
| `Candidate -> Truth` | FORBIDDEN_STRAIGHT_LINE · Certification gate + Evidence | CANONICAL_REGISTRY |
| `هل اشتعلت في runner؟` | غير متوفرة · `NOT_EMITTED_BY_RUNNER` | — |

## 12. مصفوفة المناط: أسئلة المالك

*من الكود 0 · غير متوفرة 1*

| الخانة | القيمة | المصدر |
|---|---|---|
| `أسئلةُ المناط` | غير متوفرة · `NOT_OPENED:MANAT` | — |

## 12.b سجل الغموض اللغوي الموقوف على المالك

*من الكود 0 · غير متوفرة 1*

| الخانة | القيمة | المصدر |
|---|---|---|
| `مواضعُ الغموض` | غير متوفرة · `OWNER_DECISION` | — |

## 13. التنزيل وما سُحب

*من الكود 2 · غير متوفرة 1*

| الخانة | القيمة | المصدر |
|---|---|---|
| `حالُ HUKM` | `NOT_OPENED` | السجلّ |
| `حالُ TANZIL` | `NOT_OPENED` | السجلّ |
| `الدعاوى وأسبابُها` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |

## 14. الحكم النهائي على الوثيقة

*من الكود 11 · غير متوفرة 3*

| الخانة | القيمة | المصدر |
|---|---|---|
| `STATE·DECLARED_NOT_IMPLEMENTED` | `10/160` | عدٌّ |
| `STATE·DEFERRED` | `10/160` | عدٌّ |
| `STATE·EXECUTED` | `10/160` | عدٌّ |
| `STATE·NOT_APPLICABLE` | `10/160` | عدٌّ |
| `STATE·NOT_OPENED` | `120/160` | عدٌّ |
| `HINT·missing_context:FORMAL_ONLY` | `10/160` | عدٌّ |
| `HINT·previous_gate_not_proven` | `120/160` | عدٌّ |
| `HINT·runtime_implementation_missing` | `10/160` | عدٌّ |
| `RESIDUAL·RUNTIME_CONTEXT_PENDING` | `150/160` | عدٌّ |
| `RANK·ZERO->ZERO` | `160/160` | عدٌّ |
| `CLAIM_PROJECT_FINISHED` | `NO` | ثابتٌ في المولّد |
| `سبب` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `شروط` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
| `مانع` | غير متوفرة · `HUMAN_DECLARED_ONLY` | — |
