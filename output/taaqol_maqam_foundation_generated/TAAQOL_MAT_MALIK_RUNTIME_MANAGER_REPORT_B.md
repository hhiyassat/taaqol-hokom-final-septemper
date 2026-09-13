# TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT

**تشغيل فعلي مربوط بالإدخال — لا renderer فوق artifacts جاهزة، ولا إعادة استعمال جواب سابق لجملة جديدة.**

> INPUT_SENTENCE: مَاتَ مَلِكٌ عَنْ أُخٍ سَاكِنٍَ مَعَهُ، فَأَرَادَ وِلَدَهُ طَرْدَهُ، فَتَحَاكَمَا
> INPUT_SHA256: 9c18efaf613d8970e0b7a13363aabb801a41260a77679d499251e16f6cfae798
> generated_at_runtime = YES · reused_prior_artifact = NO · reused_prior_final_answer = NO

## جدول الكلمات (من هذا الإدخال)
- r000 = «مَاتَ»
- r001 = «مَلِكٌ»
- r002 = «عَنْ»
- r003 = «أُخٍ»
- r004 = «سَاكِنٍَ»
- r005 = «مَعَهُ،»
- r006 = «فَأَرَادَ»
- r007 = «وِلَدَهُ»
- r008 = «طَرْدَهُ،»
- r009 = «فَتَحَاكَمَا»

## المرشحات (من هذا الإدخال)
- fc000 = «مَاتَ مَلِكٌ عَنْ أُخٍ سَاكِنٍَ مَعَهُ،» [TEXT_CANDIDATE_ONLY] FACT_ACCEPTED=NO
- fc001 = «فَأَرَادَ وِلَدَهُ طَرْدَهُ،» [TEXT_CANDIDATE_ONLY] FACT_ACCEPTED=NO
- fc002 = «فَتَحَاكَمَا» [TEXT_CANDIDATE_ONLY] FACT_ACCEPTED=NO

## طبقات السلسلة العمودية (مربوطة بالـ sha)
- FINAL_MANAT = DEFER [SENTENCE_SHA_MISMATCH]
- NORMATIVE_SOURCE = DEFER [SENTENCE_SHA_MISMATCH]
- TANZIL = DEFER [SENTENCE_SHA_MISMATCH]
- FINAL_HUKM = DEFER [SENTENCE_SHA_MISMATCH]
- FINAL_ANSWER = DEFER [SENTENCE_SHA_MISMATCH]

VERDICT = DEFER_RUNTIME_DERIVATION_INCOMPLETE
FINAL_ANSWER = NO · SCOPE = N/A · JUDICIAL_OUTCOME_PRODUCED = NO · FULL_TAAQOL_PROJECT_CLOSED = NO

> لا جواب نهائي لهذا الإدخال: لا توجد طبقات مصدَّقة تطابق sha الجملة. DEFER_RUNTIME_DERIVATION_INCOMPLETE.

> parent_artifact_hashes: (none — no layer bound to this input)

---
*تشغيل مربوط بالإدخال؛ الجواب النهائي لا يُحمَّل إلا إذا طابق sha الجملة كل طبقة مصدَّقة.*
