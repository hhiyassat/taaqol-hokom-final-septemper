# بنودُ الحكم — تُرفع ولا تُرجَّح

لكلّ بندٍ أثرُ خياراته **مقيسًا**، ولا ترجيحَ في واحدٍ منها.

## `B1` · أيُّ نصٍّ هو النازلة

```json
{
 "أ": {
  "sha256": "1a7f8b76",
  "effect_measured": "الفاصلةُ والنقطة تُقطعان بحكمك، و٣ توكناتٍ تحملهما"
 },
 "ب": {
  "sha256": "d04892e5",
  "effect_measured": "النصُّ بلا فاصلةٍ ولا نقطة ⟶ حكمُك في القطع لا محلَّ له على هذه النازلة"
 },
 "note": "الخياران يعطيان بصمتَي مدخلٍ مختلفتين، فكلُّ تقريرٍ لاحقٍ يتغيّر مقامُه"
}
```

## `B2` · أصنافُ البقيّة السبعة (T-4)

```json
{
 "unassigned": {
  "U_N7_2_INTERNAL_AL": 1616,
  "U_TANWEEN": 8894,
  "U_ALEF_MADDA": 1505,
  "U_ALIF_MAQSURA": 2498,
  "U_ALIF_FARIQA": 3561,
  "U_UNVOCALIZED_CARRIER": 60,
  "U_MULTIWORD_CELL": 9
 },
 "total_words_affected": 18143,
 "note": "لم يُسنَد صنفٌ واحد — P4 يمنع الإسنادَ الذاتيّ"
}
```

## `B3` · عيبُ التنوين

```json
{
 "count": 3059,
 "حجب": {
  "effect_measured": "3059 كلمةً تخرج من ACCEPT"
 },
 "بقيّةٌ ظاهرةٌ مؤجَّلة": {
  "effect_measured": "تبقى في المخرج موسومةً، والمقامُ ثابت"
 }
}
```

## `B4` · سجلّا العوامل والمبنيّات — الاسمُ لا العدد

```json
{
 "files_on_disk": [
  {
   "path": "reports/axis_2_mabniyat_operators/AXIS_2_REGISTRY.csv",
   "sha256": "647e08de31f4",
   "rows": 134,
   "unique_first_column": 134
  },
  {
   "path": "reports/axis_2_mabniyat_operators/AXIS_2_TOKENS.csv",
   "sha256": "ed9aa403e9ac",
   "rows": 74668,
   "unique_first_column": 114
  }
 ],
 "numbers_in_circulation": [
  107,
  160,
  153,
  102,
  565
 ],
 "note": "الفصلُ باسم الملفّ وبصمته، لا بعدد صفوفه"
}
```

## `B5` · كَتَبَ — تخفيضُ التقشير أم توسيعُ شرط البوّابة

```json
{
 "witness_loaded": {
  "verdict": "DEFER",
  "peels": 9630
 },
 "witness_absent": {
  "verdict": "ACCEPT",
  "peels": 17268
 },
 "corpus_effect_measured": {
  "accept_delta": 5618,
  "defer_delta": -6348
 },
 "finding": "المسارُ بلا شاهدٍ يُرخّص القبولَ في ٥٬٦١٨ كلمةً — وحكمُك T4B: «القبولُ دعوى كالمنع سواء»"
}
```

## `B6` · «آ» خارج «أل» · N2_2 · لكم

```json
{
 "status": "أصنافٌ مسمّاةٌ بلا حكمٍ منذ وثيقة التسليم",
 "open_in_engine": [
  "OPEN:ALEF_MADDA_OUTSIDE_AL",
  "OPEN:N2_2_SHADDA_AFTER_AL",
  "OPEN:LAKUM_DEMOTION_IN_CL16"
 ]
}
```

## `B7` · المذهبُ والولايةُ القضائيّة

```json
{
 "gates": [
  "§10 المنطوق والمفهوم",
  "§12 المناط"
 ],
 "effect_measured": "الفصلان يخرجان «غير متوفرة» حتى يُحكم"
}
```

## `B8` · حذفُ نسخة maqayis_v2 · index.lock · المحوّل

```json
{
 "found_in_this_container": {
  "*maqayis_v2*": [],
  "*index.lock*": []
 },
 "adapter_for_stages_1_and_2": "NOT_PRESENT",
 "effect_measured": "لا واحدٌ من الثلاثة موجودٌ في هذه الحاوية. فالبندُ إمّا مُنجَزٌ قبلها، وإمّا يخصّ نسخةً عندك — ولا يُقاس من هنا.",
 "blocked_by": "A1 — لا تاريخَ يُبيّن أزالها أم لم تُنقَل أصلًا"
}
```

## `B9` · قاعدةُ startswith("ال")

```json
{
 "إصلاحُ المفاتيح": {
  "touches": 2,
  "note": "مفتاحان من ١١ يتغيّر تصنيفُهما"
 },
 "رفعُ القاعدة": {
  "touches": 10013,
  "of": 77411
 },
 "note": "تنفيذُه في (ج) — لا يُلمس المصدر — وحكمُه هنا"
}
```
