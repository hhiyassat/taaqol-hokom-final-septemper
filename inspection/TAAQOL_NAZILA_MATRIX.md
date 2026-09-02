# مصفوفة تعقّل للنازلة — النسخة 5.4 المبنية

```text
DOCUMENT_LABEL = TAAQOL_CONFORMANT_MATRIX_DRAFT
DOCUMENT_LABEL_SCOPE = this document only, not a Taaqol enum
INPUT_TEXT = مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ، فَأَرَادَ وَارِثُهُ طَرْدَهَا، فَتَحَاكَمَا.
INPUT_SHA256 = 1a7f8b76d719bc019fe200ea952cce211a7a4283814d9cee0d04a39251d8b3e2
CORPUS_ID = nazila
RUN_ID = native:nazila
REPRODUCES = RECORD_IDENTITY
LAYER_RULE = MEASURED_RUNTIME_OUTPUT + DECLARED_NOT_MEASURED + OWNER_PENDING_DECISIONS
NO_LAYER_MIXING = TRUE
STAGE_COVERAGE = COMPLETE (16/16 declared)
RUNTIME_EXECUTION = LIMITED (1/16 measured executed)
MEASURED_RECORDS = 160 = 10 tokens × 16 stages
FINAL_HUKM = NOT_PRODUCED
FINAL_TANZIL = NOT_OPENED
```

## 0. حدّ الدخول المعلن

| الحقل | القيمة |
|---|---|
| `declared_entry_kind` | `ARABIC_VOCALIZED_TEXT` |
| `ontological_status` | `NOT_AN_ORIGIN` |
| `sound_status` | `NOT_A_SOUND` |
| `meaning_status` | `NOT_A_MEANING` |
| `produces_only` | `TEXT_TRACE_CANDIDATE` |
| الأثر | النصّ المشكول يدخل بوصفه أثرًا نصيًا مرشحًا، لا أصلًا، ولا صوتًا، ولا معنى، ولا حكمًا. |

## 1. بطاقة النازلة

| الحقل | القيمة |
|---|---|
| نوع المدخل | نص عربي مشكول قصير |
| طبيعة النص | نازلة مصاغة لغويًا، لا حكم شرعي جاهز |
| محل النزاع الظاهر | موت مالك، أخت ساكنة معه، وارث يريد طردها، ثم تحاكم |
| عدد التوكنات المقيسة | 10 |
| ما يجوز إنتاجه الآن | أثر نصي، أسئلة، فرضيات، بقايا ظاهرة، حدود ممنوعة |
| ما لا يجوز إنتاجه الآن | حكم نهائي، تنزيل قضائي، إثبات حق سكن، إلزام بمسكن بديل |

## 2. بصمة القياس

| الحقل | القيمة |
|---|---|
| `MEASURED_BY` | `USER_REVIEW_CONTAINER` |
| `RUN_FINGERPRINT` | `PROVIDED_BY_USER_REVIEW` |
| `taaqol_commit` | `3cccdded7951ba71b3cb2a8b9b477f3fb3d91095` |
| `sha256(INPUT_TEXT)` | `1a7f8b76d719bc019fe200ea952cce211a7a4283814d9cee0d04a39251d8b3e2` |
| `python` | `3.12.3` |
| `utc_timestamp` | `2026-09-02T12:34:18+00:00` |
| `corpus_id` | `nazila` |
| `run_id` | `native:nazila` |
| `runner` | `runtime.corpus_runner.run_native_corpus("nazila", tokens)` |
| `REPRODUCES` | `RECORD_IDENTITY` |
| حكم هذه الخانة | الأرقام والسجلات مسندة إلى بصمة تشغيل حاوية المراجعة. إعادة التشغيل بنفس `corpus_id` تعيد هوية السجلات، لا توزيع الأحكام فقط. |

## 3. الجرد المغلق المستعمل

| الجرد | القيم المعتمدة |
|---|---|
| `Rank` | `ZERO`, `TRACE`, `CANDIDATE`, `HYPOTHESIS`, `LICENSED`, `STRONG`, `CERTIFICATE` |
| `ClosureState` | `OPEN`, `MINIMALLY_CLOSED`, `PERFORATED_CLOSED`, `BLOCKED`, `INVALID`, `FORBIDDEN_LEAP` |
| `TransitionState` | `APPROVED`, `DEFERRED`, `BLOCKED`, `REJECTED`, `FORBIDDEN_LEAP` |
| `StageTransitionState` | `EXECUTED`, `BLOCKED`, `DEFERRED`, `DECLARED_NOT_IMPLEMENTED`, `NOT_OPENED`, `NOT_APPLICABLE` |
| `FailureCode` المستعمل هنا | `FORBIDDEN_STRAIGHT_LINE` فقط عند خطوط المنع المستقيمة |

## 4. مصفوفة المراحل الست عشرة

في هذا التشغيل المقيس: المشغّل لا يستورد `gamma` ولا `ClosureState` ولا `TransitionState`. لذلك لا يُملأ حكم الغلق ولا حكم البوابة في صفوف التشغيل.

| # | المرحلة | `StageTransitionState` المقيس | الرتبة المقيسة | `ClosureState` | `TransitionState` | `hint` | `residuals_after` |
|---:|---|---|---|---|---|---|---|
| 1 | `PATH_CLASSIFICATION` | `EXECUTED` | `ZERO -> ZERO` | — | — | — | — |
| 2 | `PRE_WEIGHT_CAPACITY_AUDIT` | `DECLARED_NOT_IMPLEMENTED` | `ZERO -> ZERO` | — | — | `runtime_implementation_missing` | `RUNTIME_CONTEXT_PENDING` |
| 3 | `DAL_ONLY` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 4 | `VERBAL_MADLUL` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 5 | `DAL_MADLUL_BINDING` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 6 | `CONTRACTABLE_UNIT` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 7 | `RELATION` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 8 | `FORMAL_SHAPE` | `DEFERRED` | `ZERO -> ZERO` | — | — | `missing_context:FORMAL_ONLY` | `RUNTIME_CONTEXT_PENDING` |
| 9 | `MUFRAD_DALALAH` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 10 | `RELATION_CLOSURE` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 11 | `IFADAH` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 12 | `HUKM` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 13 | `MANAT` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 14 | `TANZIL` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 15 | `ANSWER_AUDIT` | `NOT_OPENED` | `ZERO -> ZERO` | — | — | `previous_gate_not_proven` | `RUNTIME_CONTEXT_PENDING` |
| 16 | `NON_CONTENT_FORMAL_ROUTE` | `NOT_APPLICABLE` | `ZERO -> ZERO` | — | — | — | `RUNTIME_CONTEXT_PENDING` |

## 4.b شكل سجل التنفيذ وقواعده

| القاعدة | النص المقتبس للمعنى |
|---|---|
| `Rule 1` | no output carrier without preserved input carrier |
| `Rule 3` | no implicit rank upgrade |
| `Rule 4` | no residual deletion: `residuals_after ⊇ residuals_before` |
| `Rule 6` | no executed stage without traceability |
| `Rule 7` | deferred must declare missing condition |
| `Rule 8` | blocked must carry failure code |
| `Rule 9` | `NOT_APPLICABLE` requires `NOT_APPLICABLE` applicability |

```text
RECORD_FIELD_STATUS = NOT_FULLY_RECONSTRUCTED_IN_THIS_DOCUMENT
RECORD_RULE_STATUS = QUOTED_BY_USER_REVIEW_MEASUREMENT
```

## 5. سجل الأثر والأدلة

| الدليل | هل المرجع مقيس؟ | هل سقف الرتبة مقيس؟ | التعليق |
|---|---:|---:|---|
| `E1` surface text | نعم | لا | النص المصدر هو مدخل القياس وسطحه الأول. |
| `E2` token trace | نعم | لا | `evidence_refs = ("token:t000", …)` مقيسة في السجلات. |
| `E3` stage trace | نعم | لا | أثر المرحلة موجود في سجل التشغيل، لكن لا يحمل سقف رتبة مستقلًا في المخرج. |
| `missing_facts` | لا | لا | ليست دليلًا؛ هي بقايا أو قرارات ناقصة. |

## 6. البقايا المقيسة

| اسم البقية | العدد المقيس | المقام | موضعها |
|---|---:|---|---|
| `previous_gate_not_proven` | 120 | 12 مراحل غير مفتوحة × 10 توكنات | مراحل لم تُفتح بسبب عدم ثبوت البوابة السابقة |
| `runtime_implementation_missing` | 10 | مرحلة واحدة غير منفذة × 10 توكنات | `PRE_WEIGHT_CAPACITY_AUDIT` |
| `missing_context:FORMAL_ONLY` | 10 | مرحلة واحدة مؤجلة × 10 توكنات | `FORMAL_SHAPE` |
| `RUNTIME_CONTEXT_PENDING` | 150 | 15 سجلًا ذا بقايا × 10 توكنات | `residuals_after` في كل المراحل عدا `PATH_CLASSIFICATION` |

```text
HIDDEN_RESIDUALS = UNMEASURED
DECLARED_RESIDUALS = measured names above only
TOTAL_STAGE_RECORDS = 160 = 10 tokens × 16 stages
EMPTY_RESIDUAL_ROWS = 10 = PATH_CLASSIFICATION × 10 tokens
```

## 7. فجوة القانون والمشغّل

| المطلوب دستوريًا | حاله في المشغّل المقيس | حكم الوثيقة |
|---|---|---|
| استدعاء Γ | غير مستورد في runner | لا يُدّعى كخرج runtime |
| `ClosureState` | غير مستورد | يترك فارغًا في مصفوفة runtime |
| `TransitionState` | غير مستورد | يترك فارغًا في مصفوفة runtime |
| `StageExecutionRecord` كامل الحقول | غير مُعاد بناؤه هنا | يعلن كفجوة لا يملأ بالتخمين |
| قياس Γ المباشر على دعاوى مصطنعة للفحص | ممكن خارج runner | طبقة إضافية إن شُغّلت، لا تُخلط بالخرج الأصلي |

## 8. مصفوفة الألفاظ: ما يجوز وما لا يجوز

هذه طبقة `DECLARED_NOT_MEASURED`: تصلح كعمل بشري مفسر، لا كخرج runtime.

| اللفظ | إفادة لغوية محتملة | ما لا يجوز أخذه منه وحده |
|---|---|---|
| `مَاتَ` | وقوع الموت وانقطاع الحياة | لا يثبت وحده انتقال ملكية معينة أو حقًا قضائيًا |
| `مَلِكٌ` | شخص ذو ملك أو سلطان | لا يثبت نظام حكم أو قانون دولة |
| `عَنْ` | مجاوزة أو ترك أو تعلق بالفعل | لا يثبت وارثًا ولا تركة بلا قرينة |
| `أُخْتٍ` | قرابة أخوة | لا يحدد شقيقة أو لأب أو لأم |
| `سَاكِنَةٍ` | حلول واستقرار في مكان | لا يثبت حق سكن قانوني دائم |
| `مَعَهُ` | معية ومصاحبة | لا يثبت إذنًا قانونيًا مستقلًا |
| `فَأَرَادَ` | الفاء تعقيب، و`أَرَادَ` يدل على قصد الطرد | لا يثبت تعسفًا ولا ولايةً ولا حقًا بمجرد الإرادة |
| `وَارِثُهُ` | مدعي وراثة أو حامل صفة وارث | لا يحدد نصيبه ولا ولايته |
| `طَرْدَهَا` | إخراج أو إبعاد | لا يثبت تعسفًا إلا بقرائن الضرر والحق |
| `فَتَحَاكَمَا` | الفاء تعقيب، و`تَحَاكَمَا` يدل على اشتراك الطرفين في التحاكم | لا يحدد جهة الحكم ولا القانون الحاكم |

## 9. العلاقات اللغوية والحدود

| الدعوى | الحالة |
|---|---|
| `NO_ADJACENT_PAIR_CLOSURE` | `TRUE` |
| `RELATION_CLOSED_COUNT` | `0` |
| علاقة `مَاتَ ← مَلِكٌ` | فرضية نحوية بشرية، لا `RELATION_CLOSED` |
| علاقة `عَنْ ← أُخْتٍ` | مرشح عامل ومعمول يحتاج ترخيصًا |
| علاقة `أُخْتٍ ← سَاكِنَةٍ` | فرضية نعت ومنعوت؛ وهي شرط إعلان مفهوم الصفة، لا علاقة مغلقة |
| علاقة `سَاكِنَةٍ ← مَعَهُ` | فرضية تعلق تحتاج ترخيصًا |
| علاقة `أَرَادَ ← وَارِثُهُ` | فرضية فعل وفاعل تحتاج ترخيصًا |
| علاقة `أَرَادَ ← طَرْدَهَا` | فرضية مفعول أو مصدر مؤول تحتاج ترخيصًا |
| علاقة `فَتَحَاكَمَا ← ألف الاثنين` | أثر صرفي/نحوي يحتاج مسارًا منفذًا |

## 10. المنطوق والمفهوم

| الباب | الصياغة | الحالة |
|---|---|---|
| المنطوق | النص يحكي موت ملك، ووجود أخت ساكنة معه، وإرادة وارثه طردها، ثم تحاكمهما. | `DECLARED_NOT_MEASURED` |
| مفهوم الموافقة | الطرد قد يثير ضررًا أشد من مجرد أذى القول. | `DECLARED_NOT_MEASURED` |
| مفهوم المخالفة | قيد `سَاكِنَةٍ مَعَهُ` قد يؤثر في الحق المدعى إذا ثبتت علاقة النعت ومذهب حجية المفهوم. | `DECLARED_NOT_MEASURED`; العلة المعلنة: `MADHHAB_NOT_DECLARED` كوسم وثيقة لا كـ `FailureCode` |

## 11. الخطوط المستقيمة الممنوعة

| البند | القيمة |
|---|---|
| عدد الخطوط في السجل | 47 |
| `failure_code` الحقيقي لها | `FORBIDDEN_STRAIGHT_LINE` |
| قسمة الانطباق | 17 ما قبل النص `NOT_APPLICABLE`، و30 على مدخل نصي مشكول |
| مصدر القسمة | `USER_PROVIDED_REVIEW_MEASUREMENT`; يجب اشتقاقها آليًا قبل النشر العام |
| هل اشتعلت في runner؟ | `UNMEASURED` |

| المفتاح الحرفي | `is_forbidden_direct` |
|---|---:|
| `VocalizedText → ValidAnalysis` | `TRUE` |
| `DeclaredEntry → OntologicalOrigin` | `TRUE` دستوريًا بلا جسر |
| `Closure → Certificate` | `TRUE` |
| `Ifādah → Judgment` | `TRUE` |
| `Judgment → Application` | `TRUE` |
| `Word → Sentence` | `FALSE` |

## 12. مصفوفة المناط: أسئلة المالك

| السؤال | لماذا يوقف الحكم؟ | الحالة |
|---|---|---|
| ما القانون أو المذهب الحاكم؟ | يحدد حجية المفهوم وشروط الحق والضرر. | `OWNER_PENDING` |
| هل الوارث مالك منفرد أم شريك؟ | يؤثر في سلطة الإخلاء. | `OWNER_PENDING` |
| هل السكن بإذن المورث أم بحق مستقل؟ | يفرق بين الإباحة والحق. | `OWNER_PENDING` |
| هل الأخت وارثة أم غير وارثة؟ | يغير مركزها في التركة. | `OWNER_PENDING` |
| هل وقع ضرر محقق من الطرد؟ | مناط منع الطرد لا يثبت بدونه. | `OWNER_PENDING` |
| هل توجد بينة على دوام السكن؟ | تثبيت اليد يحتاج قرينة. | `OWNER_PENDING` |
| ما جهة التحاكم وصلاحيتها؟ | التنزيل لا يقع بلا ولاية. | `OWNER_PENDING` |

## 12.b سجل الغموض اللغوي الموقوف على المالك

| الموضع | السؤال كما يجب أن يصل |
|---|---|
| `طَرْدَهَا` | إضافة المصدر لفاعله أم لمفعوله؟ |
| `عَنْ أُخْتٍ` | متعلق بمحذوف حال من `مَلِك`، أو متعلق بالفعل `مَاتَ`؟ |
| `أُخْتٍ` | شقيقة أم لأب أم لأم؟ |

## 13. التنزيل وما سُحب

| الدعوى | الحالة | السبب |
|---|---|---|
| حرمة الطرد التعسفي | `NOT_PRODUCED` | تحتاج حكمًا ومناطًا وولاية وتنزيلًا. |
| إلزام الوارث بمسكن بديل | `WITHDRAWN_AS_MANUFACTURED_HUKM` | كان حكمًا مصنوعًا وسُحب؛ لا يخرج من النص وحده. |
| رفض طلب الطرد الفوري | `NOT_PRODUCED` | لا يوجد `TANZIL` مفتوح في runtime. |
| الجمع بين حق الملكية وحق الأمان | `DECLARED_NOT_MEASURED` | صياغة مصلحية بشرية تحتاج مصدرًا ونطاقًا. |

## 14. الحكم النهائي على الوثيقة

```text
DECISION = "هل هذه المصفوفة توافق تعقّل حسب آخر الإرشادات؟"

سبب =
  الطبقات الثلاث منفصلة
  حد الدخول معلن
  المراحل 16/16 معلنة
  التنفيذ المقيس محدود لا يُوسّع
  الرتب ZERO كما قيست
  الغلق والبوابة فارغان حيث لم يستوردهما runner
  البقايا بأسمائها المقيسة فقط
  خطوط المنع بمفاتيحها الحرفية
  الأسئلة الموقوفة على المالك ظاهرة

شروط =
  STAGE_COVERAGE = COMPLETE
  RUNTIME_EXECUTION = LIMITED
  MEASURED_BY = USER_REVIEW_CONTAINER
  RUN_FINGERPRINT = PROVIDED_BY_USER_REVIEW
  CORPUS_ID = nazila
  RUN_ID = native:nazila
  REPRODUCES = RECORD_IDENTITY
  INPUT_SHA256 = 1a7f8b76d719bc019fe200ea952cce211a7a4283814d9cee0d04a39251d8b3e2
  HIDDEN_RESIDUALS = UNMEASURED
  RELATION_CLOSED_COUNT = 0
  FINAL_HUKM = NOT_PRODUCED
  FINAL_TANZIL = NOT_OPENED

مانع =
  لا يوجد مانع داخلي بعد فصل hint عن residuals_after
  وإلصاق بصمة تشغيل حاوية المراجعة.

VERDICT =
  ACCEPT_AS_CONFORMANT_DRAFT
  VALID_AS_REVIEW_CONTAINER_MEASURED_MATRIX
  READY_AS_STANDARD_MATRIX_FOR_THIS_NAZILA
```
