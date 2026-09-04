#!/usr/bin/env python3
"""`M1` · `M2` — توزيعُ المنوَّن على أشكاله، قبل أن يُكتب حرف.

    PYTHONPATH=src .venv-taaqol/bin/python scripts/measure_tanween.py

**ولا يُكتب حرفٌ قبل هذا.** فقد يكون في الجرد شكلٌ رابعٌ لم يُحكم فيه،
ولو نُفِّذ قبل القياس لعُومل بالقياس — وهو `NO_RULE_WIDENING` بعينه.

**والمصفوفةُ مغلقة**: (نوعُ التنوين × شكلُ آخِر الرسم) وثالثٌ هو موقعُ
التنوين. ومجموعُها = عددُ المنوَّن كلِّه، بلا بقيّة. وشكلٌ لا اسمَ له في
`SHAPES` يُوسَم `UNCLASSIFIED_SHAPE` ويُبلَّغ، ولا يُدسّ في «حرفٍ صحيح».

**والفرقُ البنيويّ** الذي يجب أن يظهر:

* `شَيْئًا` · `مُسَمًّى` — التنوينُ على حرفٍ **قبلَ** الصامت، والصامتُ
  (ألفٌ أو مقصورة) يُحذف.
* `تِجَارَةً` — التنوينُ على الحرف **نفسِه** الذي ينقلب، والانقلابُ لا حذف.

حالتان مختلفتا الآليّة، وحكمُهما واحدٌ في النتيجة لا في الإجراء.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aslot.constants import (  # noqa: E402
    ALIF,
    ALIF_MAQSURA,
    ALIF_WASLA,
    DAMMATAN,
    FATHATAN,
    HAMZA,
    HAMZA_SEATS,
    KASRATAN,
    MARKS,
    TANWEEN,
)

WORDS = ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv"
AXES = tuple(sorted(str(p.relative_to(ROOT))
                    for p in (ROOT / "reports").glob("axis_*/*")
                    if p.is_file()))

TAA_MARBUTA = "ة"

#: أسماءُ التنوين — جردٌ مغلق.
KINDS = {FATHATAN: "FATH", DAMMATAN: "DAMM", KASRATAN: "KASR"}

#: أشكالُ آخِر الرسم — جردٌ مغلق. وما خرج عنه يُوسَم ولا يُدسّ.
SHAPES = ("ALIF", "ALIF_MAQSURA", "TAA_MARBUTA", "HAMZA", "SOUND_LETTER")

#: الأشكالُ **الثلاثة** المصادَقة — بنصّ الجدول المنقول، سطرًا سطرًا،
#: ولا تُوسَّع. وثلاثتُها في تنوين الفتح.
RATIFIED = {
    ("FATH", "ALIF"): {"action": "DELETE_CARRIER",
                       "example": "شَيْئًا ⟶ شَيْئَنْ"},
    ("FATH", "ALIF_MAQSURA"): {"action": "DELETE_CARRIER",
                               "example": "مُسَمًّى ⟶ مُسَمَّنْ"},
    ("FATH", "TAA_MARBUTA"): {"action": "TURN_TO_OPEN_TAA",
                              "example": "تِجَارَةً ⟶ تِجَارَتَنْ"},
}

#: **توتّرٌ نصّيٌّ يُعرَض ولا يُحسم.** صياغةُ `T1` تقول «وإن كان الحرفُ
#: الأخيرُ تاءً مربوطة … وتُكتب **حركةُ التنوين** ثمّ نونٌ ساكنة» — بلا
#: تقييدٍ بنوع التنوين، وظاهرُها الثلاثة. و`4ب` في القسم الأوّل يجعل
#: «ة مع الضمّ والكسر» **معلَّقًا**. ولا يجتمعان.
#:
#: والمأخوذُ هنا هو **الأضيق**: الجدولُ المنقول ثلاثةُ أسطرٍ كلُّها فتح،
#: والعنوانُ «ثلاثةُ أشكالٍ لا رابع»، و`4ب` معروضٌ صراحةً. فالأضيقُ هو
#: ما يوافق البنيةَ كلَّها، والأوسعُ قراءةٌ في نثرِ سطرٍ واحد.
#: وقراءتي ليست حكمًا: التوتّرُ يُطبع في `OWNER_PENDING`.
BROAD_READING = {
    ("DAMM", "TAA_MARBUTA"): "تِجَارَةٌ ⟶ تِجَارَتُنْ",
    ("KASR", "TAA_MARBUTA"): "تِجَارَةٍ ⟶ تِجَارَتِنْ",
}
TEXTUAL_TENSION = {
    "id": "T1_VS_4B",
    "narrow": "الجدولُ المنقول ثلاثةُ أسطرٍ كلُّها فتح · و«ثلاثةُ أشكالٍ "
              "لا رابع» · و4ب معروضٌ صراحةً",
    "broad": "صياغةُ T1 تقول «حركةُ التنوين» بلا تقييدٍ بنوعه، فظاهرُها "
             "شمولُ الضمّ والكسر على التاء",
    "taken": "NARROW",
    "why": "الأضيقُ يوافق البنيةَ كلَّها، والأوسعُ نثرَ سطرٍ واحد. "
           "وعند التعارض يؤخَذ ما لا يُوسِّع.",
    "rows_at_stake": None,
    "status": "OWNER_PENDING",
    "decided_by_tool": False,
}

UNRULED = {
    "4A": {"title": "تنوينُ فتحٍ بلا ألفٍ ولا مقصورةٍ ولا تاء",
           "example": "مَاءً · دُعَاءً",
           "match": lambda k, s: k == "FATH" and s not in
           ("ALIF", "ALIF_MAQSURA", "TAA_MARBUTA")},
    "4B": {"title": "تاءٌ مربوطةٌ مع تنوين الضمّ والكسر",
           "example": "رَحْمَةٌ · رَحْمَةٍ",
           "match": lambda k, s: s == "TAA_MARBUTA" and k in ("DAMM", "KASR")},
    "4C": {"title": "همزةٌ آخِرَ الرسم",
           "example": "شَيْءٍ · جُزْءٌ",
           "match": lambda k, s: s == "HAMZA"},
    "4D": {"title": "ألفٌ مقصورةٌ مع تنوين الضمّ والكسر",
           "example": "إن وُجد",
           "match": lambda k, s: s == "ALIF_MAQSURA" and k in ("DAMM", "KASR")},
}


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


# ───────────────────────────────────────────────── التصنيف — بالرسم وحدَه
def rasm(word: str) -> str:
    """الرسمُ وحدَه: الحروفُ بلا علامات."""
    return "".join(c for c in word if c not in MARKS)


def shape_of(letter: str) -> str:
    """شكلُ آخِر الرسم — من جردٍ مغلق. وما خرج عنه يُسمّى."""
    if letter in (ALIF, ALIF_WASLA):
        return "ALIF"
    if letter == ALIF_MAQSURA:
        return "ALIF_MAQSURA"
    if letter == TAA_MARBUTA:
        return "TAA_MARBUTA"
    if letter == HAMZA or letter in HAMZA_SEATS:
        return "HAMZA"
    return "SOUND_LETTER"


def classify(word: str) -> dict | None:
    """يردّ تصنيفَ كلمةٍ منوَّنة، أو `None` إن لم تحمل تنوينًا.

    والموقعُ يُقاس ولا يُفترَض: أعلى آخِرِ الرسم، أم أعلى ما قبلَه
    وآخِرُ الرسم بلا علامة.
    """
    marks_at: dict[int, list[str]] = {}
    letters: list[tuple[int, str]] = []
    for ch in word:
        if ch in MARKS:
            if letters:
                marks_at.setdefault(len(letters) - 1, []).append(ch)
        else:
            letters.append((len(letters), ch))
    tan = [(i, m) for i, ms in marks_at.items() for m in ms if m in TANWEEN]
    if not tan:
        return None
    if not letters:
        return {"kind": "UNCLASSIFIED_SHAPE", "shape": "NO_LETTERS",
                "position": "UNKNOWN", "tanween_count": len(tan)}
    idx, mark = tan[-1]
    last = len(letters) - 1
    final_letter = letters[last][1]
    shape = shape_of(final_letter)
    if idx == last:
        position = "ON_FINAL"
    elif idx == last - 1:
        position = "ON_PENULT_FINAL_BARE"
    else:
        position = "ON_EARLIER"
    return {
        "kind": KINDS[mark],
        "shape": shape,
        "position": position,
        "final_letter": final_letter,
        "tanween_count": len(tan),
        "rasm": rasm(word),
    }


# ─────────────────────────────────────────────────────────── M1 · التوزيع
def m1(rows: list[dict]) -> dict:
    grid: collections.Counter = collections.Counter()
    pos: collections.Counter = collections.Counter()
    multi = 0
    total_words = 0
    tanweened = 0
    unclassified: list[dict] = []
    samples: dict[tuple, list] = collections.defaultdict(list)

    for r in rows:
        total_words += 1
        c = classify(r["Word"])
        if c is None:
            continue
        tanweened += 1
        if c.get("tanween_count", 1) > 1:
            multi += 1
        if c["kind"] == "UNCLASSIFIED_SHAPE":
            unclassified.append({"position": pos_of(r), "word": r["Word"]})
            continue
        key = (c["kind"], c["shape"])
        grid[key] += 1
        pos[(c["kind"], c["shape"], c["position"])] += 1
        if len(samples[key]) < 5:
            samples[key].append({"position": pos_of(r), "word": r["Word"],
                                 "rasm": c["rasm"],
                                 "tanween_position": c["position"]})

    closes = sum(grid.values()) + len(unclassified) == tanweened
    return {
        "corpus_words": total_words,
        "corpus_words_denominator": "صفوفُ QURAN_WORDS.csv",
        "tanweened_words": tanweened,
        "tanweened_denominator": "كلماتٌ تحمل علامةَ تنوينٍ واحدةً فأكثر",
        "words_with_more_than_one_tanween_mark": multi,
        "grid": {f"{k}×{s}": n for (k, s), n in sorted(grid.items())},
        "grid_denominator": "نوعُ التنوين × شكلُ آخِر الرسم",
        "grid_total": sum(grid.values()),
        "by_position": {f"{k}×{s}×{p}": n
                        for (k, s, p), n in sorted(pos.items())},
        "unclassified_shape": unclassified,
        "closes": closes,
        "closes_arithmetic": f"{sum(grid.values())} + {len(unclassified)} "
                             f"= {tanweened}",
        "samples": {f"{k}×{s}": v for (k, s), v in sorted(samples.items())},
        "command": "PYTHONPATH=src .venv-taaqol/bin/python "
                   "scripts/measure_tanween.py",
    }


def pos_of(r: dict) -> str:
    return f'{r["Sura_No"]}:{r["Verse_No"]}:{r["Word_No"]}'


def mechanism(m: dict) -> dict:
    """الفرقُ البنيويُّ بين الحذف والانقلاب — مقيسًا من عمود الموقع."""
    out = {}
    for key, n in m["grid"].items():
        kind, shape = key.split("×")
        on_final = m["by_position"].get(f"{key}×ON_FINAL", 0)
        on_penult = m["by_position"].get(f"{key}×ON_PENULT_FINAL_BARE", 0)
        earlier = m["by_position"].get(f"{key}×ON_EARLIER", 0)
        out[key] = {
            "total": n,
            "tanween_on_final_letter": on_final,
            "tanween_on_letter_before_final": on_penult,
            "tanween_earlier": earlier,
            # الآليّةُ تُشتقّ من الموقع المقيس، ولا تُكتب. وجملةٌ تقول
            # «التنوينُ قبلَ الصامت» بجوار عمودٍ يقول عكسَه هي الصفرُ
            # الميّتُ في أخطر صوره: دعوى بجانب نقضها.
            "action": ("DELETE_CARRIER" if shape in ("ALIF", "ALIF_MAQSURA")
                       else "TURN_TO_OPEN_TAA" if shape == "TAA_MARBUTA"
                       else "NOT_RULED"),
            "mark_order_measured": (
                "TANWEEN_AFTER_CARRIER" if on_final > on_penult
                else "TANWEEN_BEFORE_CARRIER" if on_penult > on_final
                else "MIXED"),
            "mark_order_split": f"بعدَ الحامل {on_final} · قبلَه {on_penult}",
            "ratified": (kind, shape) in RATIFIED,
        }
    return out


# ────────────────────────────────────────────── M2 · الأشكالُ غيرُ المحكومة
def m2(rows: list[dict]) -> dict:
    out = {}
    for tag, spec in UNRULED.items():
        hits = []
        n = 0
        for r in rows:
            c = classify(r["Word"])
            if c is None or c["kind"] == "UNCLASSIFIED_SHAPE":
                continue
            if spec["match"](c["kind"], c["shape"]):
                n += 1
                if len(hits) < 5:
                    hits.append({"position": pos_of(r), "word": r["Word"],
                                 "kind": c["kind"], "shape": c["shape"]})
        out[tag] = {"title": spec["title"], "example_in_prompt": spec["example"],
                    "count": n, "denominator": "كلماتٌ منوَّنة",
                    "first_five": hits, "status": "OWNER_PENDING",
                    "ruled": False}
    return out


# ─────────────────────────────────────────── T2 · نقطةُ الرجوع قبل الكتابة
def rollback_point() -> dict:
    axes = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
            for rel in AXES}
    src = ROOT / "src/aslot/axes/axis1_normalization.py"
    con = ROOT / "src/aslot/constants.py"
    device = device_git()
    changed = device.get("files_to_be_changed", [])
    return {
        # `T2` — نقطةُ الرجوع: شرطُ الشجرة النظيفة **لم يتحقّق** حرفيًّا،
        # ويُعلَن ساقطًا لا مؤوَّلًا. والمقيسُ إلى جانبه: الملفّان اللذان
        # سيتغيّران نظيفان في git ومتطابقان بايتةً بايتة بين الحاوية
        # وشجرة المالك — فالرجوعُ إليهما ممكنٌ بأمرٍ واحد. والحكمُ في
        # الاكتفاء بذلك **للمالك**، لا للأداة.
        "clean_tree_precondition": {
            "required": "git status نظيفٌ في final-september",
            "measured": device.get("state"),
            "passes": device.get("state") == "CLEAN",
            "dirty_under_src": device.get("dirty_under_src"),
            "files_to_be_changed_are_clean":
                device.get("files_to_be_changed_are_clean"),
            "restore_command":
                "git -C ~/final-september checkout -- " + " ".join(changed)
                if changed else None,
            "waived_by_tool": False,
            "authority_to_waive": "OWNER",
        },
        "axis_outputs": axes,
        "axis_outputs_denominator": "كلُّ ملفٍّ تحت reports/axis_*",
        "source_files": {
            str(p.relative_to(ROOT)):
                hashlib.sha256(p.read_bytes()).hexdigest()
            for p in (src, con)},
        "container_git": "NO_REPOSITORY — النسخةُ في الحاوية بلا git، "
                         "فنقطةُ الرجوع هي هذه البصمات",
        "device_git": device,
    }


def device_git() -> dict:
    """حالُ شجرة المالك — تُقرأ من ملفٍّ مقيسٍ بأمره، ولا تُفترَض.

    الحاويةُ لا تبلغ شجرةَ المالك، فتُقاس هناك بأمرها ويُودَع الناتجُ
    في `data/device_git.json`. وغيابُ الملفّ يُعلَن ولا يُقرأ «نظيفًا».
    """
    p = ROOT / "data" / "device_git.json"
    if not p.is_file():
        return {"state": "NOT_MEASURED",
                "note": "لا يُقرأ الغيابُ نظافةً — يُقاس بأمره ويُودَع."}
    return json.loads(p.read_text(encoding="utf-8"))


def guards(m: dict, unruled: dict) -> list[dict]:
    g = [{
        "guard": "G_LEDGER_CLOSES",
        "denominator": m["tanweened_words"],
        "arithmetic": m["closes_arithmetic"],
        "passes": m["closes"],
        "note": "مصفوفةُ (نوع × شكل) + غيرُ المصنَّف = المنوَّنُ كلُّه، "
                "بلا بقيّة.",
    }, {
        "guard": "G_NO_UNCLASSIFIED_SHAPE",
        "denominator": m["tanweened_words"],
        "count": len(m["unclassified_shape"]),
        "passes": not m["unclassified_shape"],
        "note": "شكلٌ لا اسمَ له في الجرد يُسمّى ولا يُدسّ في «حرفٍ صحيح».",
    }, {
        "guard": "G_NO_RULE_WIDENING",
        "denominator": len(RATIFIED),
        "broad_reading_not_taken": sorted(f"{k}×{s}" for k, s in BROAD_READING),
        "textual_tension": TEXTUAL_TENSION["id"],
        "ratified_pairs": sorted(f"{k}×{s}" for k, s in RATIFIED),
        "unruled_tags": sorted(unruled),
        "overlap": sorted(
            f"{k}×{s}" for k, s in RATIFIED
            if any(spec["match"](k, s) for spec in UNRULED.values())),
        "passes": True,   # يُملأ أدناه
        "note": "لا زوجَ يكون مصادَقًا ومعلَّقًا معًا.",
    }]
    g[2]["passes"] = not g[2]["overlap"]

    # القسمةُ تُقاس على **الأزواج المتمايزة** لا على مجاميع الصفوف:
    # فالأربعةُ المعلَّقة ليست متباينة (4أ ⊂ 4ج)، وجمعُ أعدادِها يعدّ
    # صفوفًا مرّتين. والزوجُ يُعدّ مرّةً واحدة مهما تعدّدت الخانةُ التي
    # ذكرته — وهذا هو `EQUAL_NUMBERS_MAY_BE_DIFFERENT_SETS` في موضعه.
    # وثلاثةُ أصنافٍ لا اثنان. فالحكمُ يقول: «وما سوى ذلك: **لا يتغيّر** ·
    # ويُوسَم OWNER_PENDING إن كان من الأربعة». فالزوجُ الذي ليس مصادَقًا
    # ولا من الأربعة **محكومٌ فيه بالإبقاء**، لا يتيمٌ بلا حكم. وقسمةٌ
    # بصنفَين تجعله يتيمًا وهو مشمول.
    present = {tuple(k.split("×")) for k in m["grid"]}
    ratified_pairs = {(k, s) for k, s in RATIFIED} & present
    pending_pairs = {p for p in present
                     if any(spec["match"](*p) for spec in UNRULED.values())
                     } - ratified_pairs
    unchanged_pairs = present - ratified_pairs - pending_pairs
    orphans: list[str] = []
    rows = lambda ps: sum(m["grid"].get(f"{k}×{s}", 0) for k, s in ps)
    g.append({
        "guard": "G_SCOPE_IS_PARTITIONED",
        "denominator": len(present),
        "denominator_note": "أزواجٌ متمايزةٌ حاضرةٌ في الجرد — لا مجاميعُ صفوف",
        "ratified_pairs": sorted(f"{k}×{s}" for k, s in ratified_pairs),
        "pending_pairs": sorted(f"{k}×{s}" for k, s in pending_pairs),
        "unchanged_by_rule_pairs": sorted(f"{k}×{s}"
                                          for k, s in unchanged_pairs),
        "unchanged_by_rule_clause": "«وما سوى ذلك: لا يتغيّر»",
        "orphan_pairs": orphans,
        "ratified_rows": rows(ratified_pairs),
        "pending_rows": rows(pending_pairs),
        "unchanged_rows": rows(unchanged_pairs),
        "rows_sum": (rows(ratified_pairs) + rows(pending_pairs)
                     + rows(unchanged_pairs)),
        "rows_total": m["grid_total"],
        "rows_close": (rows(ratified_pairs) + rows(pending_pairs)
                       + rows(unchanged_pairs) == m["grid_total"]),
        "passes": (not orphans
                   and rows(ratified_pairs) + rows(pending_pairs)
                   + rows(unchanged_pairs) == m["grid_total"]),
        "note": "ثلاثةُ أصناف: مصادَقٌ · معروضٌ · محكومٌ بالإبقاء. "
                "ومجموعُها كلُّ المنوَّن المصنَّف، بلا يتيم.",
    })
    g.append({
        "guard": "G_UNRULED_SETS_MAY_OVERLAP",
        "denominator": len(UNRULED),
        "overlaps": sorted(
            f"{a}∩{b}"
            for i, a in enumerate(sorted(UNRULED))
            for b in sorted(UNRULED)[i + 1:]
            if any(UNRULED[a]["match"](k, s) and UNRULED[b]["match"](k, s)
                   for k, s in present)),
        "passes": True,
        "note": "الأربعةُ ليست متباينة — تُعلَن التقاطعاتُ ولا تُجمع "
                "أعدادُها. وحارسٌ يجمعها يعدّ صفوفًا مرّتين.",
    })
    return g


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/tanween")
    a = ap.parse_args()

    if not WORDS.is_file():
        raise Blocked(f"OWNER_ALERT: CORPUS_ABSENT — {WORDS}")
    with WORDS.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    m = m1(rows)
    mech = mechanism(m)
    unruled = m2(rows)
    g = guards(m, unruled)
    rb = rollback_point()

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "00_before.json").write_text(json.dumps(
        {"task": "M1_TANWEEN_DISTRIBUTION", **m, "mechanism": mech,
         "ratified_pairs": {f"{k}×{s}": v for (k, s), v in RATIFIED.items()},
         "broad_reading_not_taken":
             {f"{k}×{s}": v for (k, s), v in BROAD_READING.items()},
         "textual_tension": {**TEXTUAL_TENSION,
                             "rows_at_stake": sum(
                                 m["grid"].get(f"{k}×{s}", 0)
                                 for k, s in BROAD_READING)},
         "rollback_point": rb, "guards": g,
         "all_guards_pass": all(x["passes"] for x in g)},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "01_unruled.json").write_text(json.dumps(
        {"task": "M2_UNRULED_SHAPES", "shapes": unruled,
         "total_pending": sum(v["count"] for v in unruled.values()),
         "status": "OWNER_PENDING",
         "rule": "لا يُحكم فيها ولو بدا الحكمُ بيّنًا — NO_RULE_WIDENING"},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print(f'M1 كلماتُ الجرد {m["corpus_words"]} · منوَّنةٌ '
          f'{m["tanweened_words"]} · يقفل {m["closes"]} '
          f'({m["closes_arithmetic"]})')
    print("   المصفوفة (نوع × شكل):")
    for k, n in sorted(m["grid"].items(), key=lambda kv: -kv[1]):
        kind, shape = k.split("×")
        mark = "★ مصادَق" if (kind, shape) in RATIFIED else "  معلَّق"
        d = mech[k]
        print(f'     {k:28} {n:6}  {mark}  '
              f'على الأخير {d["tanween_on_final_letter"]} · '
              f'قبلَه {d["tanween_on_letter_before_final"]}')
    print(f'M2 الأشكالُ الأربعةُ المعلَّقة — تُعدّ ولا يُحكم فيها:')
    for tag, v in unruled.items():
        print(f'     {tag}  {v["count"]:6}  {v["title"]}')
        for h in v["first_five"][:5]:
            print(f'            {h["position"]:12} {h["word"]}')
    print(f'T2 نقطةُ الرجوع: {len(rb["axis_outputs"])} ملفَّ محورٍ · '
          f'{len(rb["source_files"])} ملفَّ مصدر · '
          f'شجرةُ المالك {rb["device_git"]["state"]}')
    for x in g:
        print(f'   {x["guard"]:26} {"PASS" if x["passes"] else "FALLS"} '
              f'/{x["denominator"]}')
    if not all(x["passes"] for x in g):
        raise Blocked("GUARD_FALLS — ولا يُكتب حرف")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
