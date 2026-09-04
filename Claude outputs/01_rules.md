# القواعدُ الستّ — ولكلٍّ سمٌّ أو وسمُ UNPOISONED

## `MEASURED_NOT_PRESET`

**القاعدة**: ما لم يُقَس لا يُطبع صفرًا. والمرحلةُ التي لم تُفتح لا تُنتج عددًا يساوي صفرًا، بل لا تُنتج عددًا.

**الواقعة**: RELATION_CLOSED_COUNT = 0 كان يُقرأ «قِيس فكان صفرًا» وهو لم يُقس.

**السمّ**: `tests_taaqol/test_closure_guards.py::test_x4_no_cell_from_a_closed_stage_carries_a_value`

## `CAUSE_IS_A_CLAIM`

**القاعدة**: العلّةُ في تقريرٍ إمّا لها أمرٌ منشورٌ يُعيد إنتاجها، وإمّا تُوسَم HYPOTHESIS.

**الواقعة**: ثلاثةُ تعليلاتٍ باطلةٍ سُحبت في ثلاث جولات، ولا واحدةَ منها أوقفها إجراء.

**السمّ**: `tests_taaqol/test_remediation_guards.py::test_every_measured_number_in_the_ledger_has_a_command`

## `FILE_HASH_IS_NOT_CONTENT_HASH`

**القاعدة**: لقاعدةِ بياناتٍ يُقابَل البيان لا الملفّ.

**الواقعة**: 35c7062d ≠ a8333229 أوهم اختلافًا، والبيانُ لم يختلف في صفٍّ واحد — وكلّف ثلاثَ جولاتٍ من الفحص.

**السمّ**: `UNPOISONED`

الوثيقةُ في ~/hokom/docs، والمقابلةُ أُجريت مرّةً بيدٍ (بصمتا ملفٍّ متساويتان وبصمتا بيانٍ متساويتان) ولم يُكتب لها سمٌّ يُشغَّل. فتُوسَم بحقيقتها.

## `NO_TEXTUAL_GUARD`

**القاعدة**: لا حارسَ يفحص ورودَ اسمٍ في نصّ. يُشغَّل أو لا يُعدّ.

**الواقعة**: حارسٌ نصّيٌّ يمرّ لو كُتب CORPUS_ABSENT في تعليقٍ ولم يُرفع.

**السمّ**: `tests_taaqol/test_nazila_matrix_guards.py::test_a_blocked_preflight_writes_nothing`

أوّلُ إحالةٍ ذكرت سمًّا في السويت الخطأ — واصطاده test_every_named_poison_actually_exists. وسمٌّ مذكورٌ لا وجودَ له أسوأُ من UNPOISONED: هذا يُخفي الغياب، وذاك يُعلنه.

## `DENOMINATOR_IS_PINNED`

**القاعدة**: نقلُ بندٍ بين أسر الأسباب يضيّق المقامَ ويرفع العلامةَ بلا عمل — فيُقابَل بالجولة السابقة ويُعلَن.

**الواقعة**: علامتان بمقامين عُرضتا كواحدة: 52% للدفتر و70.9% للنازلة.

**السمّ**: `tests_taaqol/test_nazila_outputs.py::test_reason_family_moves_are_reported_against_the_previous_round`

## `GUARD_MUST_REPORT_NOT_DIE`

**القاعدة**: الغيابُ يُبلَّغ (C3:ABSENT) ولا يُنهي الفحص.

**الواقعة**: guard رفع StopIteration حين غاب C3، وKeyError حين غاب status. واستثناءٌ داخل حارسٍ يُنهي الفحصَ كلَّه، فتُقرأ بقيّةُ الحرّاس سليمةً وهي لم تُشغَّل.

**السمّ**: `tests_taaqol/test_upstream_doors.py::test_a_done_status_in_c_is_caught`
