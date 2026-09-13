# TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT

**تشغيل فعلي مربوط بالإدخال — لا renderer فوق artifacts جاهزة، ولا إعادة استعمال جواب سابق لجملة جديدة.**

> INPUT_SENTENCE: مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ، فَأَرَادَ وَارِثُهُ طَرْدَهَا، فَتَحَاكَمَا
> INPUT_SHA256: ada6cfcc770ac452111bcf9cca0e7eda69de672c9dc7b1c1f676c46bbf3901a2
> generated_at_runtime = YES · reused_prior_artifact = NO · reused_prior_final_answer = NO

## جدول الكلمات (من هذا الإدخال)
- r000 = «مَاتَ»
- r001 = «مَلِكٌ»
- r002 = «عَنْ»
- r003 = «أُخْتٍ»
- r004 = «سَاكِنَةٍ»
- r005 = «مَعَهُ،»
- r006 = «فَأَرَادَ»
- r007 = «وَارِثُهُ»
- r008 = «طَرْدَهَا،»
- r009 = «فَتَحَاكَمَا»

## المرشحات (من هذا الإدخال)
- fc000 = «مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ،» [TEXT_CANDIDATE_ONLY] FACT_ACCEPTED=NO
- fc001 = «فَأَرَادَ وَارِثُهُ طَرْدَهَا،» [TEXT_CANDIDATE_ONLY] FACT_ACCEPTED=NO
- fc002 = «فَتَحَاكَمَا» [TEXT_CANDIDATE_ONLY] FACT_ACCEPTED=NO

## طبقات السلسلة العمودية (مربوطة بالـ sha)
- FINAL_MANAT = YES [MATCHED · TAAQOL_MAT_MALIK_FINAL_MANAT_BIRTH_48.json]
- NORMATIVE_SOURCE = YES [MATCHED · TAAQOL_MAT_MALIK_NORMATIVE_SOURCE_ACCEPTANCE_50.json]
- TANZIL = YES [MATCHED · TAAQOL_MAT_MALIK_TANZIL_APPLICATION_51.json]
- FINAL_HUKM = YES [MATCHED · TAAQOL_MAT_MALIK_FINAL_HUKM_BIRTH_52.json]
- FINAL_ANSWER = YES [MATCHED · TAAQOL_MAT_MALIK_FINAL_ANSWER_53.json]

VERDICT = ACCEPT_RUNTIME_FINAL_ANSWER
FINAL_ANSWER = YES · SCOPE = FNM1_ONLY · JUDICIAL_OUTCOME_PRODUCED = NO · FULL_TAAQOL_PROJECT_CLOSED = NO

## الجواب النهائي (FINAL_ANSWER_TEXT)
> بناءً على المناط النهائي المصدّق، وعلى المصدر المعياري NS1 بعد تطبيقه، وعلى الحكم الداخلي FHK1: لا يُنتَج أثر إخراج الأخت الساكنة من العين قبل نظر النزاع في مجلس الحكم المختص، ضمن حدود هذه الحالة فقط.

> parent_artifact_hashes: TAAQOL_MAT_MALIK_FINAL_MANAT_BIRTH_48.json=d4f16c660c7b…، TAAQOL_MAT_MALIK_NORMATIVE_SOURCE_ACCEPTANCE_50.json=a4ec1cf7dab4…، TAAQOL_MAT_MALIK_TANZIL_APPLICATION_51.json=a99a39ffd972…، TAAQOL_MAT_MALIK_FINAL_HUKM_BIRTH_52.json=51875d7caec9…، TAAQOL_MAT_MALIK_FINAL_ANSWER_53.json=a323f786a16b…

---
*تشغيل مربوط بالإدخال؛ الجواب النهائي لا يُحمَّل إلا إذا طابق sha الجملة كل طبقة مصدَّقة.*
