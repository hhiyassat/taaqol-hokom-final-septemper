# HUSSEIN_SCRIPT — تقرير تنفيذي بنيوي محايد

> محايد بنيويًّا (STRUCTURAL_ONLY): لا مجال نهائي، لا حكم، لا جواب نهائي، لا واقعة مقبولة، لا رأي كود، لا موافقة ولا رفض. الشكل مقتبس من نمط تقرير Taaqol (Round-44) عبر مُصيّر عام؛ المحتوى محايد ولا يحوي محتوى Round-44.

## 1. ملخص للمدير

- تقرير بنيوي محايد لجملة مدخلة — لا يقرّر مجالًا ولا ينتج حكمًا ولا يوافق ولا يرفض.
- عدد الكلمات (تقطيع سطحي) = 10 · عدد المرشحات البنيوية = 3.
- لا واقعة مقبولة (FACT_ACCEPTED_COUNT = 0)؛ الحكم البنيوي الافتراضي = DEFER_STRUCTURAL_ONLY.
حياد صريح: CONTENT_NEUTRAL = YES · DOMAIN_DECISION = NO · HUKM = NO · FINAL_ANSWER = NO · APPROVAL = NO · REFUSAL = NO · CODE_OPINION = NO · لا مصدر خارجي · لا FrameNet.
DOCUMENT_TYPE = NEUTRAL_SENTENCE_STRUCTURAL_REPORT · report_hash = 5ffdf15071 · GENERATOR = HUSSEIN_SCRIPT · RENDERER=TAAQOL_STYLE

## 2. الجملة محل التشغيل

> مَاتَ مَلِكٌ عَنْ أُخٍ سَاكِنٍَ مَعَهُ، فَأَرَادَ وِلَدَهُ طَرْدَهُ، فَتَحَاكَمَا


## 3. جدول الكلمات (تقطيع سطحي naive split)

| token_id | surface |
| --- | --- |
| n000 | مَاتَ |
| n001 | مَلِكٌ |
| n002 | عَنْ |
| n003 | أُخٍ |
| n004 | سَاكِنٍَ |
| n005 | مَعَهُ، |
| n006 | فَأَرَادَ |
| n007 | وِلَدَهُ |
| n008 | طَرْدَهُ، |
| n009 | فَتَحَاكَمَا |

## 4. الإفادة

لا إفادة تُنتَج ولا تُدَّعى؛ عرضٌ بنيوي فقط. IFADAH = NO.

## 5. المقام

لا مقام يُقرَّر ولا سياق يُفترَض؛ الأداة محايدة للمحتوى. MAQAM_DECIDED = NO.

## 6. سياسة المرجع

REFERENCE_POLICY = NONE · EXTERNAL_REFS = 0 · NO_EXTERNAL_SOURCE = YES · NO_FRAMENET · لا معرفة طبية/فقهية/قانونية.

## 7. الدعوى الواقعية ورخصة العبور

لا دعوى تُقبَل ولا رخصة عبور تُمنَح؛ المرشحات تبقى مرشحات. FACT_ACCEPTED_COUNT = 0 · CROSSING_LICENSE = NO.

## 8. المرشحات البنيوية

المرشحات الخبرية (TEXT_CANDIDATE_ONLY):
| id | raw_segment | FACT_ACCEPTED |
| --- | --- | --- |
| c000 | مَاتَ مَلِكٌ عَنْ أُخٍ سَاكِنٍَ مَعَهُ، | NO |
| c001 | فَأَرَادَ وِلَدَهُ طَرْدَهُ، | NO |
| c002 | فَتَحَاكَمَا | NO |
مرشحات الطلب/السؤال (REQUEST_OR_QUESTION_CANDIDATE):
(لا مرشحات طلب/سؤال)
الوقائع المعروفة: none accepted — FACT_ACCEPTED_COUNT = 0.
- CAUSE = OWNER_SUPPLIED_INPUT_SENTENCE
- CONDITIONS = STRUCTURAL_SEGMENTATION_ONLY، NO_DOMAIN_DECISION، NO_FACT_ACCEPTANCE
- PREVENTERS = DOMAIN_UNDECIDED، NO_OWNER_RATIFICATION_IN_THIS_TOOL، NO_HUKM_LICENSE
- VERDICT = DEFER_STRUCTURAL_ONLY

## 9. موضع التوقف — البقايا (Residuals)

- DOMAIN_NOT_DECIDED
- FACTS_NOT_ACCEPTED
- HUKM_NOT_PRODUCED
- FINAL_ANSWER_NOT_PRODUCED
- OWNER_RATIFICATION_REQUIRED_FOR_ANY_FACT

## 10. المعلومات الناقصة / الطلب الأدق

OWNER_RATIFICATION_REQUIRED_FOR_ANY_FACT — this first tool provides no ratification path; no candidate becomes a fact here.
لقبول أي واقعة أو تقرير أي مجال: يلزم تصديق المالك صراحةً (غير متاح في هذه الأداة).

## 11. ما يلزم بعد الوصول

لو صدّق المالك لاحقًا (أداة/جولة منفصلة) يبقى هذا التقرير بنيويًّا؛ لا يُنتِج حكمًا ولا جوابًا ولا موافقة/رفضًا.

## 12. الاختبارات

tests/test_neutral_sentence_report_generator.py — NEUTRAL_REPORT_TESTS = passed · الحياد والبنية مُختبَران على ثلاث جمل غير متجانسة.
جدول التتبّع (مستقل عن جدول الوسوم)
| requirement | source | artifact | test | status |
| --- | --- | --- | --- | --- |
| REQ-NEUTRAL-REPORT-JSON | OWNER_SUPPLIED_INPUT_SENTENCE | neutral_sentence_report_5ffdf15071.json | tests/test_neutral_sentence_report_generator.py | TRACEABLE |
| REQ-NEUTRAL-REPORT-MD | OWNER_SUPPLIED_INPUT_SENTENCE | neutral_sentence_report_5ffdf15071.md | tests/test_neutral_sentence_report_generator.py | TRACEABLE |
| REQ-NEUTRAL-REPORT-HTML | OWNER_SUPPLIED_INPUT_SENTENCE | neutral_sentence_report_5ffdf15071.html | tests/test_neutral_sentence_report_generator.py | TRACEABLE |

## 13. إثبات سلسلة التوليد


## 14. الخلاصة التنفيذية

سجّلت الأداة بنية الجملة المدخلة فقط (كلمات + مرشحات خبرية/طلبية) في قالب تنفيذي، دون تقرير مجال ولا حكم ولا جواب ولا موافقة/رفض ولا رأي كود؛ لا واقعة مقبولة، والحكم البنيوي DEFER_STRUCTURAL_ONLY.
| flag | value |
| --- | --- |
| CONTENT_NEUTRAL | YES |
| DOMAIN_DECISION | NO |
| HUKM | NO |
| FINAL_ANSWER | NO |
| FACT_ACCEPTED_COUNT | 0 |
| VERDICT | DEFER_STRUCTURAL_ONLY |
| NO_DOMAIN_KNOWLEDGE | YES |
| NO_EXTERNAL_SOURCE | YES |
| NO_MEDICAL_ADVICE | YES |
| NO_FIQH_HUKM | YES |
| NO_LEGAL_HUKM | YES |
| NO_FACT_ACCEPTANCE | YES |
| NO_FINAL_ANSWER | YES |
| REPORT_IS_STRUCTURE_ONLY | YES |

## أعلام الإغلاق داخل التقرير
CONTENT_NEUTRAL = YES · DOMAIN_DECISION = NO · HUKM = NO · FINAL_ANSWER = NO · FACT_ACCEPTED_COUNT = 0 · VERDICT = DEFER_STRUCTURAL_ONLY · REPORT_IS_STRUCTURE_ONLY = YES · RENDERER = TAAQOL_STYLE.

**نتيجة الاختبارات:** NEUTRAL_REPORT_TESTS = passed

---
تقرير بنيوي محايد — لا مجال، لا حكم، لا جواب نهائي، لا واقعة مقبولة (RENDERER=TAAQOL_STYLE).
