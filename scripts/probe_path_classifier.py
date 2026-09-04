#!/usr/bin/env python3
"""يقيس ما يميّزه `classify_token_paths` وما لا يميّزه، وأين يعبر خطًّا ممنوعًا.

    .venv-taaqol/bin/python scripts/probe_path_classifier.py

**لا رقمَ في هذا الشرح.** كلُّ عددٍ يخرج إلى
`inspection/nazila/02_path_classifier.json` ويُقرأ منه. وسببُ هذا القيد
واقعةٌ مسجَّلة: بقي في شرحِ ملفٍّ عددان من قياسٍ سابق بعد أن تغيّر القياس،
فقال الشرحُ غيرَ ما يقيس الملفّ. ورقمٌ في نثرٍ لا يُعاد حسابُه يموت صامتًا،
فالنثرُ هنا يصف ولا يعدّ.

**والمقامان يُعلَنان.** «كم مسارًا يميّز؟» سؤالٌ بمقامين: أوّلُ شاهدٍ لكلّ
مفتاح، أو كلُّ الشواهد. وأوّلُ قياسٍ لي خلط بينهما فخرج عددان لشيءٍ واحد —
وهو الخطأُ الذي أُلاحقه في المحرّك. فيُقاس الاثنان ويُسمَّيان.

**والقسمةُ داخل الجرد، وبما يقع عليه الجوابُ الثاني.** ما ليس في الجرد يسقط
إلى الافتراضيّ مجرَّدًا كان أو مشكولًا فيتّفق الحالان، والاتّفاقُ هنا ليس
تمييزًا — فتُقسم مفاتيحُ الجرد وحدَها. وقسمتُها **ليست** «يعطي جوابًا آخر»
مقابلَ «يسقط صامتًا»: المفتاحُ لا يُعطي الافتراضيَّ مجرَّدًا، فسقوطُه إليه
مشكولًا هو أيضًا جوابٌ آخر. فالقسمةُ بما يقع عليه:

    مسارٌ مسمًّى غيرُ الأوّل   دعوى موجبةٌ خاطئة تمرّ صامتة   ← الأخطر
    الافتراضيّ                عجزٌ يُرى في العدد

**والخطُّ الممنوع يُستشار في سجلّ تعقُّل نفسِه.** قاعدةُ الاحتياط
`startswith("ال")` تُصنّف بالرسم الإملائيّ، و`CANONICAL_REGISTRY` يمنع
`Grapheme → FunctionalLetter`. فتُستفتى الدالّةُ ولا يُنقل عنها.

**ولا يُؤخذ أوّلُ مطابقٍ بعد التجريد.** التجريدُ يجمع المتجانسات: يُجرَّد
`أَنَّ` و`أَنْ` و`أَنِ` فتصير كلُّها `أن`. وكان الفهرسُ يأخذ أوّلَ ما يرد في
المصحف، فوقع على `أَنَّ` — وهي من أخوات «إنّ» لا المصدريّةَ الناصبة. فالمقيسُ
كلمةٌ أخرى تشبه المفتاحَ بعد التجريد، والجوابُ حينئذٍ صحيحٌ بالمصادفة.

    FIRST_MATCH_ON_STRIPPED_SURFACE = HOMOGRAPH_UNSAFE

والعلاجُ **ليس اختيارًا أفضل** — كلُّ اختيارٍ بين المتجانسات حكمٌ لغويّ.
فلا يُختار: تُقاس **كلُّ** صورةٍ للمفتاح في المصحف، ويُعلَن تعدُّدُها. فإن
اتّفقت مساراتُها فالنتيجةُ ثابتةٌ لا مختارة، وإن اختلفت رُفعت بإنذار مالك
ولم تُطوَ بأخذ إحداها.

**وصفرُ الغياب ليس صفرَ القياس.** إن غاب المصحفُ أو غاب مخرجُ المحور الأوّل
يقف الملفُّ بإنذار مالك: `CORPUS_ABSENT` و`AXIS1_REPORT_ABSENT`. وكان يُكمل
بصفرين وقاموسٍ فارغ، فيُقرأ «قاعدةُ ال لا تشتعل» و«الصورُ بلا صنفٍ في
أسلوط» — وكلاهما دعوى مبناها أنّ ملفًّا لم يُقرأ.
"""
from __future__ import annotations

import csv
import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = (ROOT / "vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime"
            / "native_stage_registry.py")
CORPUS = ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv"
AXIS1 = ROOT / "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv"
sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))

#: الخطوطُ التي تعبرها قاعدةُ الاحتياط — تُستفتى ولا تُدَّعى.
FORBIDDEN_TO_QUERY = [
    ("Grapheme", "FunctionalLetter"),
    ("Orthography", "Pronunciation"),
    ("Matching", "Meaning"),
]

#: شواهدُ الاحتياط كما هي في مصدر تعقُّل — تُقرأ منه لا تُوصف.
FALLBACK_EVIDENCE = frozenset({
    "definite lexical surface",
    "default lexical-content fallback",
})

DEFINITE_PREFIX = "ال"  # ا ل
#: مسارُ الاحتياط الأخير في المصنِّف — يُقرأ منه لا يُدَّعى.
DEFAULT_PATH = "RootStemPath"


def registry_keys() -> list[str]:
    """يقرأ المفاتيحَ من مصدر تعقُّل — فلو زيدت ظهرت هنا بلا تعديل."""
    src = REGISTRY.read_text(encoding="utf-8")
    body = src.split("mapping: dict[str, tuple[PathEvidence, ...]] = {")[1]
    return re.findall(r'^\s{8}"([^"]+)":', body, re.M)


def strip_marks(text: str) -> str:
    return "".join(c for c in text if not unicodedata.combining(c))


def has_marks(text: str) -> bool:
    return any(unicodedata.combining(c) for c in text)


def corpus_forms(keys: list[str]) -> dict[str, dict[str, dict]]:
    """كلُّ صورةٍ للمفتاح في المصحف، بعددها وبحالها — **لا أولاها**.

    **والاسمُ صُحّح.** كانت تُسمّى `vocalized_forms`، وهي تردّ كلَّ سطحٍ
    يطابق المفتاحَ بعد التجريد — ومنه سطحٌ لا علامةَ عليه أصلًا. فسطحُ
    ``ولا`` في المصحف بلا شَكْلة، وتسميتُه «صورةً مشكولة» وصفٌ كاذب. وهو
    الصنفُ نفسُه الذي أُلاحقه: الاسمُ يقول غيرَ ما تحمله القيمة.

    ولا يُستبعد غيرُ المشكول — استبعادُه يُخفي `U_UNVOCALIZED_CARRIER`، وهو
    أثمنُ ما ظهر. بل يُعلَّم كلُّ سطحٍ بـ``has_marks``، فيُرى أنّ تفرّقَ
    المسارات سببُه **غيابُ علامة** لا اختلافُ تشكيل.

    وردُّ الصور كلِّها بدل واحدةٍ هو الفرقُ بين قياسٍ واختيار: أخذُ الأولى
    يحسم بين متجانسين حسمًا لغويًّا لا يملكه هذا الملفّ.
    """
    if not CORPUS.is_file():
        raise SystemExit(
            f"OWNER_ALERT: CORPUS_ABSENT — {CORPUS}. ولا يُكمَل بصفرٍ يُقرأ "
            f"نتيجةً: «لا صورةَ للمفتاح» و«لم يُقرأ المصحف» ليسا واحدًا.")
    wanted = set(keys)
    found: dict[str, dict[str, dict]] = {k: {} for k in wanted}
    with CORPUS.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            surface = row.get("Word") or ""
            bare = strip_marks(surface)
            if bare in wanted:
                cell = found[bare].setdefault(
                    surface, {"count": 0, "has_marks": has_marks(surface)})
                cell["count"] += 1
    return {k: v for k, v in found.items() if v}


def aslot_classes_for(divergent: list[dict]) -> dict[str, str]:
    """صنفُ كلّ صورةٍ متفرّقةٍ كما سمّاه المحورُ الأوّل — لا كما أفسّره أنا.

    والحارسُ مشروط: يقف **حين توجد صورٌ تنتظر صنفَها** ويغيب الملفّ. فالوقوفُ
    بلا حاجةٍ تعطيل، والمضيُّ مع الحاجة قاموسٌ فارغٌ يُقرأ «بلا صنف» وحقيقتُه
    «لم يُقرأ الملفّ». والشرطُ هو الفرق.
    """
    if not divergent:
        return {}
    if not AXIS1.is_file():
        raise SystemExit(
            f"OWNER_ALERT: AXIS1_REPORT_ABSENT — {AXIS1}. وثمّة صورٌ متفرّقةٌ "
            f"تنتظر صنفَها، و«بلا صنف» غيرُ «لم يُقرأ الملفّ».")
    wanted = {v for d in divergent for v in d["corpus_forms"]}
    out: dict[str, str] = {}
    with AXIS1.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            w = row.get("Word") or ""
            if w in wanted and w not in out:
                out[w] = (row.get("Owner_Decision_Classes")
                          or row.get("Stop_Reason")
                          or row.get("Normalization_Status") or "")
    return out


def main() -> int:
    from taaqqul_slot_geometry.core.forbidden_lines import CANONICAL_REGISTRY
    from taaqqul_slot_geometry.runtime.native_stage_registry import (
        classify_token_paths,
    )

    keys = registry_keys()
    if not keys:
        raise SystemExit("OWNER_ALERT: لم تُقرأ مفاتيحُ الجرد — تغيّر المصدر؟")
    def top(surface: str) -> tuple[str, float]:
        p = classify_token_paths(surface)[0]
        return p.path_id.value, p.confidence

    def every(surface: str) -> list[tuple[str, float]]:
        return [(p.path_id.value, p.confidence)
                for p in classify_token_paths(surface)]

    # ── المقامان ────────────────────────────────────────────────────────
    top_paths = {top(k)[0] for k in keys}
    top_conf = [top(k)[1] for k in keys]
    all_pairs = [pc for k in keys for pc in every(k)]
    all_paths = {p for p, _ in all_pairs}
    all_conf = [c for _, c in all_pairs]

    # ── القسمةُ داخل الجرد ──────────────────────────────────────────────
    # **تصحيحٌ لقسمةٍ ظاهرها معقول.** قُسِّمت أوّلًا إلى «يعطي جوابًا آخر»
    # و«يسقط صامتًا»، والقسمتان **ليستا متقابلتين**: مفتاحٌ في الجرد لا
    # يُعطي الافتراضيَّ أبدًا مجرَّدًا، فكلُّ سقوطٍ إلى الافتراضيّ هو أيضًا
    # جوابٌ آخر. فالقسمةُ الصحيحة بما يقع عليه الجواب الثاني:
    #
    #     مسارٌ مسمًّى غيرُ الأوّل   ← دعوى موجبةٌ خاطئة، تمرّ صامتة
    #     الافتراضيُّ RootStemPath  ← عجزٌ يُرى في العدد
    #
    # والأولى أخطر: الثانيةُ تقول «لا أعرف»، والأولى تقول شيئًا آخر بثقة.
    #
    # وكلُّ صورةٍ في المصحف تُقاس، فإن اختلفت مساراتُها رُفع المفتاحُ إلى
    # خانةٍ ثالثة ولم يُحسم بأخذ إحداها.
    forms = corpus_forms(keys)
    named_other, to_default, divergent, unmeasurable = [], [], [], []
    homographs = []
    for k in keys:
        variants = forms.get(k, {})
        if not variants:
            unmeasurable.append(k)
            continue
        if len(variants) > 1:
            homographs.append({"key": k, "corpus_forms": variants})
        answers = {v: top(v) for v in variants}
        paths = {p for p, _ in answers.values()}
        entry = {"bare": k, "path_bare": top(k)[0],
                 "confidence_bare": top(k)[1],
                 "corpus_forms": {v: {**variants[v],
                                      "path": answers[v][0],
                                      "confidence": answers[v][1]}
                                  for v in sorted(variants)}}
        if len(paths) > 1:
            divergent.append(entry)
            continue
        only = next(iter(paths))
        if only == top(k)[0]:
            continue
        (to_default if only == DEFAULT_PATH else named_other).append(entry)

    # ── هل جاء التصنيفُ من الجرد أم من الاحتياط؟ ────────────────────────
    # الصياغةُ الأحدّ: ليست «يخطئ أحيانًا على السليم»، بل انعكاسٌ تامّ.
    # ويُقاس بشاهد التصنيف نفسِه — فشواهدُ الاحتياط معلومةٌ في المصدر،
    # وما عداها إصابةُ جرد. ولا يُقاس بالمسار: `JamidPath` مسارٌ مسمًّى
    # وهو مخرجُ الاحتياط لا الجرد، فالخلطُ بينهما يقلب النتيجة.
    def from_inventory(surface: str) -> bool:
        ev = classify_token_paths(surface)[0].evidence
        return not any(e in FALLBACK_EVIDENCE for e in ev)

    hits_unmarked = sum(1 for k in keys if from_inventory(k))
    marked_forms = [v for k in keys for v in forms.get(k, {})
                    if forms[k][v]["has_marks"]]
    hits_marked = sum(1 for v in marked_forms if from_inventory(v))
    inventory_hits = {
        "measured_by": "evidence string of the top PathEvidence",
        "fallback_evidence_in_source": sorted(FALLBACK_EVIDENCE),
        "unmarked_keys_total": len(keys),
        "unmarked_keys_classified_by_inventory": hits_unmarked,
        "marked_corpus_forms_total": len(marked_forms),
        "marked_corpus_forms_classified_by_inventory": hits_marked,
    }

    # ── مدى قاعدة «ال» على النصّ الكامل ─────────────────────────────────
    # `corpus_forms` أعلاه ترفع الإنذارَ إن غاب المصحف، فلا يُبلَغ هنا
    # بصفرين يُقرآن «القاعدةُ لا تشتعل». والصفرُ في موضع المجهول دعوى.
    definite = corpus_words = 0
    with CORPUS.open(encoding="utf-8-sig", newline="") as fh:
        for row in csv.DictReader(fh):
            corpus_words += 1
            if (row.get("Word") or "").startswith(DEFINITE_PREFIX):
                definite += 1

    # ── الخطوطُ الممنوعة: تُستفتى ────────────────────────────────────────
    forbidden = {f"{a}->{b}": bool(CANONICAL_REGISTRY.is_forbidden_direct(a, b))
                 for a, b in FORBIDDEN_TO_QUERY}

    aslot_classes = aslot_classes_for(divergent)

    nazila = (ROOT / "inspection/case.txt").read_text(encoding="utf-8").split()
    out = {
        "registry_keys": len(keys),
        "registry_keys_vocalized": sum(
            1 for k in keys if any(unicodedata.combining(c) for c in k)),
        "denominator_top_evidence_only": {
            "distinct_paths": sorted(top_paths),
            "confidence_min": min(top_conf), "confidence_max": max(top_conf)},
        "denominator_all_evidence": {
            "distinct_paths": sorted(all_paths),
            "confidence_min": min(all_conf), "confidence_max": max(all_conf)},
        "classified_by_the_closed_inventory": inventory_hits,
        "homograph_policy": {
            "rule": "FIRST_MATCH_ON_STRIPPED_SURFACE = HOMOGRAPH_UNSAFE",
            "applied": ("كلُّ صورةٍ مشكولةٍ تُقاس، ولا تُختار واحدة"),
            "keys_with_more_than_one_form": homographs},
        "inside_registry_split": {
            "note": ("مفتاحُ الجرد لا يُعطي الافتراضيَّ مجرَّدًا، فالقسمةُ "
                     "بما يقع عليه الجوابُ الثاني لا بوجوده"),
            "answers_with_another_named_path": named_other,
            "falls_to_default_path": to_default,
            "paths_diverge_across_corpus_forms": divergent,
            "aslot_axis1_class_of_divergent_forms": aslot_classes,
            "not_witnessed_in_corpus": unmeasurable},
        "on_the_nazila": {
            "tokens": len(nazila),
            "distinct_paths": sorted({top(t)[0] for t in nazila}),
            "all_vocalized": all(
                any(unicodedata.combining(c) for c in t) for t in nazila)},
        "definite_article_fallback": {
            "rule": 'startswith("ال") -> JamidPath',
            "corpus_words": corpus_words,
            "corpus_words_matching": definite,
            "crosses_forbidden_lines_in_CANONICAL_REGISTRY": forbidden},
        "fallback_rules_in_source": [
            "exact match on the bare surface",
            'startswith("ال") -> JamidPath',
            "otherwise -> RootStemPath",
        ],
    }
    dest = ROOT / "inspection/nazila/02_path_classifier.json"
    dest.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                    encoding="utf-8")

    o = out
    print(f"KEYS                 {o['registry_keys']} · "
          f"مشكولٌ منها {o['registry_keys_vocalized']}")
    print(f"PATHS top-evidence   {len(top_paths)} · "
          f"{min(top_conf)}–{max(top_conf)}")
    print(f"PATHS all-evidence   {len(all_paths)} · "
          f"{min(all_conf)}–{max(all_conf)}   ← مقامٌ آخر، يُعلَن ولا يُخلط")
    print(f"NAMED_OTHER_PATH     {len(named_other)}/{len(keys)} مفتاحًا "
          f"يُعطي مسارًا مسمًّى آخر بالشكل  ← دعوى تمرّ")
    print(f"FALLS_TO_DEFAULT     {len(to_default)}/{len(keys)} يسقط إلى "
          f"{DEFAULT_PATH}  ← عجزٌ يُرى")
    print(f"PATHS_DIVERGE        {len(divergent)}/{len(keys)} مفتاحًا تختلف "
          f"مساراتُ صوره  ← OWNER_ALERT، لا يُحسم بأخذ إحداها")
    for d in divergent:
        for v, info in d["corpus_forms"].items():
            print(f"     {d['bare']:<8}{v:<12}{info['path']} "
                  f"({info['count']})")
    for w, cls in aslot_classes.items():
        print(f"     أسلوط يسمّي {w}: {cls}")
    print(f"HOMOGRAPHS           {len(homographs)}/{len(keys)} مفتاحًا له أكثرُ "
          f"من صورةٍ في المصحف")
    print(f"NOT_WITNESSED        {len(unmeasurable)} مفتاحًا لا شاهدَ له في "
          f"المصحف — لا يُصوَّر بالظنّ")
    print(f"INVENTORY_HIT        غيرُ مشكولٍ "
          f"{hits_unmarked}/{len(keys)}  ·  مشكولٌ "
          f"{hits_marked}/{len(marked_forms)}   ← انعكاسٌ تامّ")
    print(f"NAZILA               {o['on_the_nazila']['distinct_paths']}")
    print(f"DEFINITE_RULE_REACH  {definite}/{corpus_words} كلمةً في المصحف "
          f"تبدأ بـ«ال»")
    for line, is_forbidden in forbidden.items():
        print(f"   FORBIDDEN {line:<32} {is_forbidden}")
    print(f"→ {dest}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
