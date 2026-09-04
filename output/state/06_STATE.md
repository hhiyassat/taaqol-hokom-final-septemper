# `STATE_OF_PROJECT` — أين المشروعُ من وثائقه الحاكمة

```text
NAZILA 70.9% (207/292) · STAGES_OPENED 1/16
VENDOR_HEAD 3cccdded7951ba71b3cb2a8b9b477f3fb3d91095 · porcelain 0 · MATCHES_PIN TRUE
AUTHORITY = PROJECTION — إسقاطٌ لا سلطة · NO_PROSE_DONE = TRUE
VENDOR_UNTOUCHED = TRUE · NO_COMMIT = TRUE · CLAIM_PROJECT_FINISHED = NO
```

**ولا يُنشئ هذا التقريرُ حكمًا ولا يُغلق بندًا ولا يُصحّح رقمًا.**

## ١ · الوثائقُ الحاكمة

| السلطة | ما تُلزم به | العدد |
|---|---|---|
| `LAW` | ما يُلزم | 11 |
| `RUNTIME` | ما يُنفَّذ | 2 |
| `EVIDENCE` | ما يُثبت | 8 |
| `PROJECTION` | ما يُشتقّ | 2 |
| `HISTORICAL` | ما مضى | 3 |

مؤرَّخةٌ **14** · `UNDATED` **12** · `AUTHORITY_UNCLEAR` 0. والتأريخُ مقيسٌ على `~/final-september` — لا في الحاوية، فهي بلا `git` ألبتّة.

| سببُ غياب التاريخ | العدد |
|---|---|
| `ABSENT_ON_DEVICE` | 9 |
| `UNTRACKED_OR_NEVER_COMMITTED` | 3 |

**سلطةُ EVIDENCE بلا بيتٍ مؤرَّخ: دفاترُ الإثبات كلُّها في حاويةٍ تُستردّ، وغائبةٌ عن المستودع الوحيد الذي يؤرّخها.** وغيرُ المؤرَّخ بالسلطة: `LAW` 2 · `EVIDENCE` 8 · `PROJECTION` 2

**وأشدُّ منه: `data/residual_kind_assignment.json` سلطتُه `LAW` — وهو موضعُ حكمِ `B2` حين يقع — وغائبٌ عن المستودع كذلك. فحكمٌ يُودَع في حاويةٍ تُستردّ ليس مودَعًا.**

**والمستودعات**: 6 مجلَّدًا موصولًا، منها 2 بـ.git و4 بلا. المجلَّداتُ الموصولةُ اليوم — ومقامُ B14 كان خمسةً حين قيس، والفرقُ مقامٌ لا خطأ.

## ٢ · المراحلُ `T-0..T-10` — مقيسةً

| المرحلة | العنوان | الحال | الأثر |
|---|---|---|---|
| `T-0` | تجميدُ المرجع | **DONE** | 7 ملفَّ قانونٍ ببصماتها · all_hashes_hold=True |
| `T-1` | تاكسونومية الرفض المغلقة | **PARTIAL** | مُعلَنٌ 30 · مشهودٌ 27 · بلا شاهدٍ في هذا التشغيل 3 (BLOCK_EMPTY_REMAINDER · IGNORED_NON_WORD_TOKEN · NON_LETTER) |
| `T-2` | حواملُ النواة | **DONE_WITH_LIMIT** | 6 حواملَ مثبَّتةَ البصمة · ولا سابعَ يُنفَّذ |
| `T-3` | مرساةُ الأثر | **DONE** | 378,826 صفًّا · بمرساةٍ 378,826 · قابلةٌ لإعادة البناء 378,826 · بلا مرساة 0 |
| `T-4` | أصنافُ البقيّة | **BLOCKED** | 7/7 بلا إسناد · P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED |
| `T-5` | Γ على كلّ صفّ | **BLOCKED** | مبنيٌّ فارغًا وفاشلًا مغلقًا · exit 3 · BLOCKED_AWAITING_B2 · ولا يُكتب ملفٌّ واحد |
| `T-6` | سجلُّ الخطوط الممنوعة | **PARTIAL** | ظلٌّ: 104 صفًّا · دليلٌ 29 · يقع ['CANDIDATE->CERTIFICATE'] · ولا تنفيذ |
| `T-7` | البوّابات | **PARTIAL** | ظلٌّ: 432 صفًّا · أصولٌ 3/3 · رتبٌ ['CANDIDATE', 'HYPOTHESIS', 'TRACE', 'ZERO'] |
| `T-8` | حدُّ المصدر المجمَّد | **PARTIAL** | 7 بنودٍ · B8.3=DONE · B11=DONE · B12=DONE · B14=DONE · B15=RAISED · FUSE=DONE · A1=DONE |
| `T-9` | إسقاطُ الحالة | **NOT_STARTED** | مُعلَنةٌ في STAGES_PENDING_OWNER (axis9_compliance.py:48) · ولا أثرَ لها في الشجرة: صفرُ ذكرٍ في HANDOFF · README · docs/ARCHITECTURE |
| `T-10` | هندسةُ الاختبار الدستوريّ | **NOT_STARTED** | مُعلَنةٌ في STAGES_PENDING_OWNER (axis9_compliance.py:49) · ولا أثرَ لها في الشجرة: صفرُ ذكرٍ في الوثائق الثلاث |

**بالحال**: BLOCKED 2 · DONE 2 · DONE_WITH_LIMIT 1 · NOT_STARTED 2 · PARTIAL 4. والمفتوحُ في التشغيل: `1/16` — T-0 · T-1 · T-2 · T-3.

و`T-9` و`T-10` مُعلَنتان في `STAGES_PENDING_OWNER` ولا أثرَ لهما في الشجرة: صفرُ ذكرٍ في `HANDOFF` و`README` و`docs/ARCHITECTURE`. **مقيستان لا مفترضتان.**

## ٣ · القواعدُ الثمان

| القاعدة | الحال | السمّ |
|---|---|---|
| `MEASURED_NOT_PRESET` | **POISONED** | `test_x4_no_cell_from_a_closed_stage_carries_a_value` |
| `CAUSE_IS_A_CLAIM` | **POISONED** | `test_every_measured_number_in_the_ledger_has_a_command` |
| `FILE_HASH_IS_NOT_CONTENT_HASH` | **UNPOISONED** | `UNPOISONED` |
| `NO_TEXTUAL_GUARD` | **POISONED** | `test_a_blocked_preflight_writes_nothing` |
| `DENOMINATOR_IS_PINNED` | **POISONED** | `test_reason_family_moves_are_reported_against_the_previous_round` |
| `GUARD_MUST_REPORT_NOT_DIE` | **POISONED** | `test_a_done_status_in_c_is_caught` |
| `COUNT_IS_NOT_MEMBERSHIP` | **POISONED** | `test_count_is_not_membership_in_both_directions` |
| `CLOSED_MATRIX_ON_ONE_COLUMN_IS_NOT_THE_AXIS` | **POISONED** | `test_the_positional_id_finding_is_raised_not_folded` |
| `SHARED_CAUSE_IS_NOT_SHARED_EFFECT` | **POISONED** | `test_a_shared_cause_may_not_become_a_shared_count` |

مُعلَنةٌ 9 · حاضرةٌ 9 · مسمومةٌ 8 · وبلا سمّ: FILE_HASH_IS_NOT_CONTENT_HASH.

## ٤ · طابورُ المالك

| الحال | العدد |
|---|---|
| `BLOCKED` | 2 |
| `DECLARED` | 5 |
| `DONE` | 18 |
| `NOT_CHOSEN` | 1 |
| `RAISED` | 15 |
| `STRUCK` | 1 |

**والدفترُ يقفل**: 24 مغلقًا + 17 موقوفًا + 1 خارجَ الولاية = 42 / 42.

**ومقامان لا مقام**: الموقوفُ 17 (`RAISED` 15 + `BLOCKED` 2)، والجدولُ أدناه **15** صفًّا — لأنّه بنودُ المالك وحدَها، والـ`BLOCKED` بنودُ أداةٍ موقوفةٌ على غيرها. فالعددان مختلفان بمقامَيهما لا بخطأ.

| البند | العنوان | الحال | أثرُ الخيارات |
|---|---|---|---|
| `B1` | أيُّ نصٍّ هو النازلة | `RAISED` | مقيس |
| `B2` | أصنافُ البقيّة السبعة (T-4) | `RAISED` | مقيس |
| `B3` | عيبُ التنوين | `RAISED` | مقيس |
| `B4` | سجلّا العوامل والمبنيّات — الاسمُ لا العدد | `RAISED` | مقيس |
| `B5` | كَتَبَ — تخفيضُ التقشير أم توسيعُ شرط البوّابة | `RAISED` | مقيس |
| `B6` | «آ» خارج «أل» · N2_2 · لكم | `RAISED` | مقيس |
| `B7` | المذهبُ والولايةُ القضائيّة | `RAISED` | مقيس |
| `B8` | حذفُ نسخة maqayis_v2 · index.lock · المحوّل | `RAISED` | مقيس |
| `B9` | قاعدةُ startswith("ال") | `RAISED` | مقيس |
| `B15` | توزيعُ entry_type وأثرُه على CL-16 | `RAISED` | مقيس |
| `B17` | مؤشّرُ الوحدة الفرعيّة غيرُ الملتزَم | `RAISED` | مقيس |
| `P1` | همزةٌ بتنوين فتح | `RAISED` | مقيس · 82 صفًّا |
| `P2` | تاءٌ مربوطةٌ مع الضمّ والكسر | `RAISED` | مقيس · 735 صفًّا |
| `P3` | الكلمةُ الواحدة · ON_PENULT_FINAL_BARE | `RAISED` | مقيس · 1 صفًّا |
| `Q4` | أيُضيَّق U_TANWEEN إلى الموقوف وحدَه؟ | `RAISED` | مقيس |

### `Q4` — سؤالٌ يُطرح ولا يُجاب

```text
U_TANWEEN يُرفع الآن على   8894
منها لا قرارَ مطلوبًا فيها 8076
ومنها موقوفةٌ حقًّا        818
الحساب                    8894 = 8076 + 818
التضييقُ المقترَح إلى      818
الحال                     ولا يُرجَّح — OWNER_PENDING
```

وما لا أثرَ مقيسٌ لخياراته: لا شيء — `EFFECT_UNMEASURED`، وسؤالٌ بلا أثرٍ مقيسٍ ترجيحٌ مؤجَّل.

## ٥ · ما عند `sonaiso`

| الباب | العنوان | الخانات | السقف | الصحّة |
|---|---|---|---|---|
| `C1` | PRE_WEIGHT مبنيّةُ الحوامل، غيرُ موصولةٍ | `17/292` | `1/16 ⟶ 14/16` | stages_closed_per_token=12 · pre_weight_prs_shipped=4/4 · pre_weight_carrier_tests_passed=107 |
| `C2` | مفاتيحُ classify_token_paths غيرُ مشكولة | `0/292` | `NO_EFFECT_MEASURED` | inventory_hit_unmarked=11/11 · inventory_hit_marked=0/17 |
| `C3` | startswith("ال") ⟶ JamidPath يعبر خطوطًا | `0/292` | `NO_EFFECT_MEASURED` | corpus_words_matching=10013 · corpus_words=77411 · percent=12.9 |
| `C4` | ANSWER_AUDIT غيرُ منفَّذة | `0/292` | `14/16 ⟶ 16/16` | seals_issued=0 |
| `C5` | corpus_runner لا يستشير الحوامل ولا سجلَ | `42/292` | `NO_EFFECT_MEASURED` | imports={'gamma': False, 'ClosureState': False, 'TransitionState': False, 'forbidden_lines': False, 'EntryBoun |
| `C_PATH` | المسلكُ المختار لبنود (ج) | `NOT_A_DOOR` | `NOT_CHOSEN` | — |

و`C3` مقيَّد: العددُ `10013/77411` يبقى · والعبورُ `TAUTOLOGY` · والنسبةُ `NOT_DERIVABLE`. ويُرفع منه: «قاعدةٌ تُصنّف بالرسم الإملائيّ، وتمسّ 12.9٪ من الجرد».

```text
C_PATH = NOT_CHOSEN · SENT = NO · AUTHORITY_TO_SEND = OWNER
```

## ٦ · العلاماتُ الأربع — بمقاماتها

| العلامة | القيمة | المقام |
|---|---|---|
| `NAZILA` | 70.9% (207/292) | خاناتُ وثيقة النازلة |
| `TWO_COLUMN` | 0% فعليّة · 85.9% ممكنة (55/64) | صفوفُ ملفّ العمودَين وحدَه |
| `REMEDIATION` | 58.6% (17/29) | بنودُ دفتر الإصلاح |
| `STAGES` | 1/16 | مراحلُ تعقُّل المفتوحة |

**أربعةُ مقاماتٍ لا مقام · ولا متوسّطَ ولا جمع** · `G_NO_LEDGER_MERGE`

### مقامُ `TWO_COLUMN` تحرّك ثلاثًا — ومقابلتُه

| الجولة | grounded | named+delta | المقام | النسبة | المصدر |
|---|---|---|---|---|---|
| 1 | 44 | 9 | 53 | 83.0٪ | `OWNER_STATED` |
| 2 | 49 | 9 | 58 | 84.5٪ | `OWNER_STATED` |
| 3 | 55 | 9 | 64 | 85.9٪ | `MEASURED` |

```text
previous_denominator      58
current_denominator       64
delta_total               6
delta_grounded            6
delta_named_plus_delta    0
named_plus_delta_constant True
```

**نموُّ المقام مقيسٌ لا انحراف: الزيادةُ كلُّها في GROUNDED، و(named + delta) ثابتٌ عند 9 في الجولات الثلاث. فالملفُّ ينمو بأسطرٍ مقيسةٍ لا معلَنة.**

و85.9٪ و84.5٪ نسبتان بمقامَين (64 و58) — ولا تُقرأ الثانيةُ تحسُّنًا على الأولى إلا بذكر المقام.

والجولتان [1, 2] مصدرُهما `OWNER_STATED`: الجولتان الأولى والثانية من نصّ المالك، ولا ملفَّ باقيًا يشهد لهما — تُنقل بمصدرها ولا تُقرأ قياسًا.

## الحرّاس

| الحارس | المقام | النتيجة |
|---|---|---|
| `G_ALL_T_PHASES_PRESENT` | 11 | PASS |
| `G_ALL_RULES_PRESENT` | 9 | PASS |
| `G_EVERY_DONE_HAS_EVIDENCE` | 3 | PASS |
| `G_AUTHORITY_DECLARED` | 26 | PASS |
| `G_OWNER_QUEUE_COMPLETE` | 42 | PASS |
| `G_STATE_LEDGER_CLOSES` | 42 | PASS |
| `G_AXES_AGREE` | 4 | PASS |
| `G_DENOMINATOR_DELTA_DECLARED` | 4 | PASS |
| `G_NO_LEDGER_MERGE` | 4 | PASS |

```text
CLAIM_PROJECT_FINISHED = NO
```

