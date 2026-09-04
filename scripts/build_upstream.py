#!/usr/bin/env python3
"""بنودُ ما خرج عن الولاية — بأمرٍ يُعيد كلَّ رقم، وموضعٍ يُقرأ  (`UPSTREAM_REBUILD`).

    .venv-taaqol/bin/python scripts/build_upstream.py --out output/upstream

**ما لا يفعله هذا الملفّ.** لا يُغيّر عيبًا واحدًا في تعقُّل، ولا يلمس بايتة.
وإنما يجعل العيوبَ الخمسةَ **قابلةً للرفع**: بأمرٍ يُعيد الرقم، وموضعٍ يُقرأ،
وحجّةٍ تُستفتى، ومقامٍ مسمًّى. وذلك أقصى ما تملكه الأداةُ في (ج).

**والحقلُ الجامعُ يقلب القراءة.** الوثيقةُ السابقة تُقرأ «تعقُّل ناقصٌ في
خمسة مواضع»، والمقيسُ غيرُ ذلك: `runtime_implemented=False` في **مرحلتين
من ستَّ عشرة**، وأربعَ عشرةَ مكتوبةً تنتظر سلفَها. فتُقرأ: «مكتوبٌ إلا
مرحلتين، وإحداهما تُغلق اثنتَي عشرة». وهي أدقُّ وأرجى، وتغيّر ما يُطلب من
`sonaiso`: لا خمسةَ إصلاحات، بل مرحلةٌ واحدةٌ تفتح اثنتَي عشرة، وأربعةٌ دونها.

**والموضعُ يُشتقّ ولا يُنسخ.** رقمُ السطر يُبحث عنه في الملفّ عند التشغيل،
فإن تحرّك السطرُ ظهر ذلك إنذارًا. وموضعٌ مكتوبٌ بيدٍ يشيخ صامتًا.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
PKG = VENDOR / "src" / "taaqqul_slot_geometry"
sys.path.insert(0, str(VENDOR / "src"))

sys.path.insert(0, str(ROOT / "scripts"))
import tautology as TAUT  # noqa: E402

PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
REG = PKG / "runtime" / "native_stage_registry.py"
RUNNER = PKG / "runtime" / "corpus_runner.py"

#: حالاتُ بنود (ج) — **مغلقة**. و`DONE` ليست منها: الإعلانُ استيفاءُ ما
#: نملك، لا زوالُ العيب. ومن وسم بندًا هنا `DONE` فقد ادّعى مسَّ المصدر.
C_STATUSES = ("DECLARED", "NOT_CHOSEN")

#: أيُّ أسرةِ سببٍ يُغلقها أيُّ باب — **بيتٌ واحد**. كانت مكتوبةً هنا
#: وهناك، والنسختان تشيخان متفرّقتَين. والأبوابُ تستوردها من الأعلى.
DOOR_OF_FAMILY = {
    "NOT_EMITTED_BY_RUNNER": "C5",
    "NOT_CONSTRUCTED_IN_SOURCE": "C5",
    "NOT_OPENED": "C1",
}

#: أساسُ التباين — **مغلق**. وثالثةَ لهما: إمّا يُقاس بالعضويّة، وإمّا
#: بالتصميم. و`ASSUMED` ليست أساسًا، وهي التي يصطادها سمُّ القاعدة التاسعة.
DISJOINTNESS_BASIS = ("BY_MEMBERSHIP", "BY_DESIGN")

#: حواملُ `PRE_WEIGHT` الأربعة، ولكلٍّ `PR` يشحنه ورموزٌ يَعِد بها القانون.
#: القائمةُ مغلقةٌ، والرموزُ تُستورد حيّةً — لا يُبحث عن اسمٍ في نصّ.
PRE_WEIGHT_PRS = {
    "PR-10": ("taaqqul_slot_geometry.weight.pre_weight",
              ("WeightCarrierBase", "PathCandidate", "SyllableCandidate",
               "SyllableSequenceCandidate", "WeightReadinessCandidate",
               "PreWeightSurface")),
    "PR-11": ("taaqqul_slot_geometry.weight.path_gate",
              ("PreWeightPathGate", "PathGateVerdict", "PathGateProof",
               "PathGateState")),
    "PR-12": ("taaqqul_slot_geometry.weight.mu_chain",
              ("MuStepResult", "MuStepState", "OmegaGovernanceState")),
    "PR-13": ("taaqqul_slot_geometry.weight.weight_fit",
              ("weigh", "WeightFitCandidate", "WeightFitResult",
               "WeightFitState")),
}

#: قوانينُ `PRE_WEIGHT` الثلاثة — تُعدّ أسطرُها، ولا يُنقل عددٌ بيد.
PRE_WEIGHT_LAWS = ("docs/20_PRE_WEIGHT_LICENSING_LAW.md",
                   "docs/22_PRE_WEIGHT_PATH_GATE_LAW.md",
                   "docs/23_PRE_WEIGHT_CHAIN_OPERATIONS_LAW.md")


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


# ── البوّابة ────────────────────────────────────────────────────────────
def gate_vendor() -> dict:
    head = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    st = subprocess.run(["git", "-C", str(VENDOR), "status", "--porcelain"],
                        capture_output=True, text=True, check=False)
    return {"vendor_head": head.stdout.strip(),
            "porcelain_lines": len([x for x in st.stdout.splitlines() if x]),
            "passes": head.stdout.strip() == PIN and not st.stdout.strip()}


# ── المواضع — تُشتقّ ولا تُكتب ─────────────────────────────────────────
def locate(path: Path, needle: str, nth: int = 1) -> dict:
    """يردّ موضعَ الرمز مشتقًّا من الملفّ. والغيابُ إنذارٌ لا صفرٌ صامت."""
    lines = path.read_text(encoding="utf-8").splitlines()
    hits = [i for i, ln in enumerate(lines, 1) if needle in ln]
    if len(hits) < nth:
        raise Blocked(
            f"OWNER_ALERT: SYMBOL_NOT_FOUND — {needle!r} في "
            f"{path.name} (وُجد {len(hits)}، طُلب {nth}). "
            "الموضعُ يُشتقّ ولا يُفترض.")
    line = hits[nth - 1]
    return {"file": str(path.relative_to(ROOT)), "line": line,
            "symbol": needle, "occurrences": len(hits),
            "text": lines[line - 1].strip()[:120]}


def resolves(loc: dict) -> bool:
    """`G_LOCATION_RESOLVES` — الرمزُ موجودٌ في الملفّ والسطر المذكورَين."""
    lines = (ROOT / loc["file"]).read_text(encoding="utf-8").splitlines()
    return 0 < loc["line"] <= len(lines) and loc["symbol"] in lines[loc["line"] - 1]


def false_flag_lines() -> list[int]:
    """أسطرُ `runtime_implemented=False` — بالتحليل النحويّ لا بالبحث النصّيّ."""
    tree = ast.parse(REG.read_text(encoding="utf-8"))
    out = []
    for node in ast.walk(tree):
        if isinstance(node, ast.keyword) and node.arg == "runtime_implemented":
            v = node.value
            if isinstance(v, ast.Constant) and v.value is False:
                out.append(v.lineno)
    return sorted(out)


# ── الحقلُ الجامع — مشتقٌّ من السجلّ ────────────────────────────────────
def joint_field() -> dict:
    from taaqqul_slot_geometry.runtime.native_stage_registry import (
        get_native_stage_registry,
    )
    specs = list(get_native_stage_registry())
    false_ = [s for s in specs if not s.runtime_implemented]
    names = [getattr(s, "stage_id", None) or getattr(s, "name", None)
             for s in false_]
    blocked = blocked_by_c1()
    reach = reachable_on_a_content_token(specs)
    return {
        "stages_total": len(specs),
        "runtime_implemented_true": len(specs) - len(false_),
        "runtime_implemented_false": len(false_),
        "names_of_false": names,
        "stages_not_opened_today": blocked["stages_not_opened_today"],
        "stages_C1_would_open": blocked["stages_C1_would_open"],
        "stages_still_closed_after_C1":
            blocked["stages_still_closed_after_C1"],
        "stages_not_opened_names": blocked["names"],
        "reachable_on_a_content_token": reach,
        "reading": ("تعقُّل مكتوبٌ إلا مرحلتين، وإحداهما تُغلق اثنتَي عشرة. "
                    "فليست خمسةَ إصلاحاتٍ تُطلب من sonaiso، بل مرحلةٌ واحدةٌ "
                    "تفتح اثنتَي عشرة، وأربعةٌ دونها."),
        "command": ("python -c \"from taaqqul_slot_geometry.runtime."
                    "native_stage_registry import get_native_stage_registry "
                    "as G; s=list(G()); print(len(s), "
                    "sum(1 for x in s if x.runtime_implemented))\""),
    }


def blocked_by_c1() -> dict:
    """المُغلَقُ اليومَ، وما يفتحه `C1` منه — وهما رقمان لا رقم.

    الاسمُ السابق `stages_blocked_by_C1 = 12` كان يعدّ في `C1` ما لا تفتحه:
    `ANSWER_AUDIT` بين الاثنتَي عشرةَ وهي محجوبةٌ **بنفسها**
    (`runtime_implemented=False`)، فلا يفتحها فتحُ سلفِها. فيُشطر العدد:
    اثنتا عشرةَ مُغلَقةٌ اليوم، تفتح `C1` منها إحدى عشرة، وتبقى واحدةٌ
    مسمّاة. والرقمان يُشتقّان: الحالُ من تشغيل، والتنفيذُ من السجلّ.
    """
    from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus
    from taaqqul_slot_geometry.runtime.native_stage_registry import (
        get_native_stage_registry,
    )
    impl = {(getattr(s, "stage_id", None) or getattr(s, "name", None)):
            s.runtime_implemented for s in get_native_stage_registry()}
    res = run_native_corpus("probe", ("مَاتَ",))
    recs = [r for t in res.token_results for r in t.records]
    closed = sorted({r.stage_id for r in recs
                     if str(getattr(r.transition_state, "value",
                                    r.transition_state)) == "NOT_OPENED"})
    still = sorted(k for k in closed if not impl.get(k, True))
    return {"count": len(closed), "names": closed,
            "stages_not_opened_today": len(closed),
            "stages_C1_would_open": len(closed) - len(still),
            "stages_still_closed_after_C1": still,
            "command": "python -c \"from taaqqul_slot_geometry.runtime."
                       "corpus_runner import run_native_corpus as R; "
                       "r=R('probe',('مَاتَ',)); "
                       "print(sum(1 for t in r.token_results for x in t.records "
                       "if x.transition_state.value=='NOT_OPENED'))\""}


def reachable_on_a_content_token(specs) -> dict:
    """`14/16` — والخصمانِ يُسمّيان، فنصفُ تعليلٍ يجعل القارئَ يحسب خمسةَ عشر.

    وهنا فخٌّ يُعلَن: `runtime_implemented=True` عددُها **أربعَ عشرةَ**
    كذلك، وهي **مجموعةٌ أخرى**. تلك تُسقط `PRE_WEIGHT` وتُبقي
    `NON_CONTENT_FORMAL_ROUTE`؛ وهذه تُسقط `NON_CONTENT_FORMAL_ROUTE`
    (لا تنطبق على مسار محتوًى) وتُبقي `PRE_WEIGHT` (تُنفَّذ إن فُتحت).
    فرقمان متساويان بعضويّتين مختلفتين — ولولا التسميةُ لقُرئا واحدًا.
    """
    from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus
    res = run_native_corpus("probe", ("مَاتَ",))
    state = {r.stage_id: str(getattr(r.transition_state, "value",
                                     r.transition_state))
             for t in res.token_results for r in t.records}
    names = [(getattr(s, "stage_id", None) or getattr(s, "name", None))
             for s in specs]
    impl = {(getattr(s, "stage_id", None) or getattr(s, "name", None)):
            s.runtime_implemented for s in specs}
    never = sorted(k for k in names if not impl[k] and k != "PRE_WEIGHT_CAPACITY_AUDIT")
    not_applicable = sorted(k for k in names
                            if state.get(k) == "NOT_APPLICABLE")
    reachable = [k for k in names
                 if k not in never and k not in not_applicable]
    also_14 = sorted(k for k in names if impl[k])
    return {
        "value": f"{len(reachable)}/{len(names)}",
        "deduction_1_never_implemented": never,
        "deduction_2_not_applicable_on_a_content_path": not_applicable,
        "arithmetic": (f"{len(names)} − {len(never)} − "
                       f"{len(not_applicable)} = {len(reachable)}"),
        "collision_warning": {
            "runtime_implemented_true_is_also": len(also_14),
            "but_a_different_set": True,
            "only_in_reachable": sorted(set(reachable) - set(also_14)),
            "only_in_runtime_implemented_true": sorted(set(also_14)
                                                       - set(reachable)),
            "note": "رقمان متساويان بعضويّتين مختلفتين — يُسمّى كلٌّ بمقامه",
        },
        "command": "python3 scripts/build_upstream.py",
    }


def c5_cells() -> dict:
    """`C5` من مصدرٍ واحد — و`EntryBoundary` **داخلَه** جزءًا مسمًّى لا بابًا.

    خرج الرقمُ في وثيقتين مختلفًا: `42` في الأبواب و`35` في الأعلى — لأنّ
    الأعلى كان يحمله **مكتوبًا بيد**. فيُشتقّ هنا من `cells.csv`، وتُطبع
    الأسرتان معًا دائمًا فلا يظهر أحدهما وحدَه فيُقرأ كلًّا.

    وموضعُ `EntryBoundary`: داخلَ `C5`، لأنّ تعريفَ الباب نفسِه يذكرها مع
    الحوامل. وهي أسرةُ سببٍ متمايزةٌ (`NOT_CONSTRUCTED_IN_SOURCE`) فتبقى
    مفردةً بعددها — جزءٌ يُسمّى، لا بابٌ خامس.
    """
    p = ROOT / "output" / "nazila_result" / "cells.csv"
    if not p.is_file():
        return {"cells_C5_total": "UNMEASURED",
                "reason": "CELLS_ABSENT — شغّل scripts/build_nazila_outputs.py",
                "command": "python3 scripts/build_nazila_outputs.py"}
    import csv as _csv
    with p.open(encoding="utf-8", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    fam = {}
    for r in rows:
        if r["status"] == "NOT_AVAILABLE":
            fam[r["reason_family"]] = fam.get(r["reason_family"], 0) + 1
    emitted = fam.get("NOT_EMITTED_BY_RUNNER", 0)
    entry = fam.get("NOT_CONSTRUCTED_IN_SOURCE", 0)
    return {
        "cells_runner_does_not_consult": f"{emitted}/{len(rows)}",
        "cells_runner_does_not_consult_denominator": "خاناتُ وثيقة النازلة",
        "cells_entry_boundary_not_constructed": f"{entry}/{len(rows)}",
        "cells_entry_boundary_not_constructed_denominator":
            "خاناتُ وثيقة النازلة",
        "cells_C5_total": f"{emitted + entry}/{len(rows)}",
        "cells_C5_total_denominator": "خاناتُ وثيقة النازلة",
        "entry_boundary_placement": "INSIDE_C5_AS_A_NAMED_PART",
        "entry_boundary_is_a_fifth_door": False,
        "command": "python3 scripts/build_upstream.py  (يجمع من cells.csv)",
    }


# ── القياسات، كلٌّ بأمره ────────────────────────────────────────────────
def probe_json() -> dict | None:
    p = ROOT / "inspection" / "nazila" / "02_path_classifier.json"
    return json.loads(p.read_text(encoding="utf-8")) if p.is_file() else None


def c2_measure() -> dict:
    """`C2` — رقمان بمقامين، ويُسمّى مقامُ كلٍّ في حقلٍ بجانبه."""
    from taaqqul_slot_geometry.runtime.native_stage_registry import (
        classify_token_paths,
    )
    src = REG.read_text(encoding="utf-8")
    block = src.split("mapping: dict", 1)[1]
    keys = re.findall(r'^\s{8}"([^"]+)":', block, re.M)
    marked = re.compile(r"[ً-ْٰ۟-ۭ]")
    vocalized = [k for k in keys if marked.search(k)]
    # المشكولُ يُقرأ من مخرَج المِسبار بأسماء حقوله كما هي — لا بأسماءٍ
    # مُخمَّنة. وأوّلُ محاولةٍ خمّنت `inventory_hit_marked` فخرجت
    # `UNMEASURED` وهي **مقيسةٌ فعلًا**: صفرٌ نظيفٌ يُشبه القياس، وهو
    # العيبُ نفسُه الذي وقع في `stage_transition_state` من قبل.
    inv = (probe_json() or {}).get("classified_by_the_closed_inventory", {})
    marked = ("UNMEASURED" if "marked_corpus_forms_total" not in inv else
              f'{inv["marked_corpus_forms_classified_by_inventory"]}/'
              f'{inv["marked_corpus_forms_total"]}')
    hit_unmarked = sum(1 for k in keys if classify_token_paths(k))
    return {
        "registry_keys": len(keys),
        "vocalized_keys": len(vocalized),
        "inventory_hit_unmarked": f"{hit_unmarked}/{len(keys)}",
        "inventory_hit_unmarked_denominator": "مفاتيحُ الجرد",
        "inventory_hit_marked": marked,
        "inventory_hit_marked_denominator":
            "صورُ المصحف المشكولةُ لتلك المفاتيح",
        "inventory_hit_marked_source":
            "inspection/nazila/02_path_classifier.json"
            " · classified_by_the_closed_inventory",
        "finding": ("المرحلةُ الوحيدةُ المنفَّذة تصيب على السطح المجرَّد "
                    "وتخطئ على المشكول — والعلّةُ في مفاتيح الجرد."),
        "command": "python3 scripts/probe_path_classifier.py",
    }


def c3_measure() -> dict:
    """`C3` مقيَّدًا — والعددُ يبقى، ودعوى العبور تُوسَم ولا تُمحى (`R1`).

    **ما كان.** ثلاثةُ أزواجٍ تُستفتى فتردّ `True ×3`، فقُرئ ذلك دليلًا
    على أنّ `startswith("ال")` يعبر خطوطًا ممنوعة.

    **وما هو.** الأزواجُ الثلاثةُ مأخوذةٌ من السجلّ، ثمّ سُئل عنها
    السجلّ — فتردّ `True` بحكم الأخذ لا بحكم الواقع: `TAUTOLOGY`.
    وأمّا **أنّ هذا التصنيفَ بالرسم هو `Grapheme → FunctionalLetter`
    بعينِه** فليس في الشيفرة ما يدلّ عليه: `NOT_DERIVABLE`.

    **وما بقي دليلًا** — وهو وحدَه ما يُرفع إلى المصدر: قاعدةٌ تُصنّف
    بالرسم الإملائيّ، وتمسّ ١٢٫٩٪ من الجرد. والعددُ مقيسٌ وسليم.

    والدعوى تُقيَّد لا تُمحى: تبقى مكتوبةً موسومةً بحالها.
    """
    from taaqqul_slot_geometry.core.forbidden_lines import CANONICAL_REGISTRY
    crossed = [("Grapheme", "FunctionalLetter"),
               ("Orthography", "Pronunciation"),
               ("Matching", "Meaning")]
    queried = {f"{a}→{b}": bool(CANONICAL_REGISTRY.is_forbidden_direct(a, b))
               for a, b in crossed}
    p = ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv"
    if not p.is_file():
        reach = {"corpus_words_matching": "UNMEASURED",
                 "corpus_words": "UNMEASURED",
                 "reason": "CORPUS_ABSENT — ولا يُقاس مدًى على جردٍ غائب"}
    else:
        import csv as _csv
        hit = tot = 0
        strip = re.compile(r"[ً-ْٰ۟-ۭ]")
        with p.open(encoding="utf-8", newline="") as fh:
            for row in _csv.DictReader(fh):
                tot += 1
                if strip.sub("", row.get("Word") or "").startswith("ال"):
                    hit += 1
        reach = {"corpus_words_matching": hit, "corpus_words": tot,
                 "percent": round(100 * hit / tot, 1)}
    rule_source = "runtime/native_stage_registry.py"
    return {
        **reach,
        # ── ما بقي دليلًا · وهذا وحدَه ما يُرفع إلى المصدر ────────────
        "what_remains_evidence": {
            "claim": "قاعدةٌ تُصنّف بالرسم الإملائيّ، وتمسّ "
                     f'{reach.get("percent", "UNMEASURED")}٪ من الجرد',
            "matched": reach.get("corpus_words_matching"),
            "denominator": reach.get("corpus_words"),
            "denominator_note": "كلماتُ جرد المحور صفر",
            "input_drawn_from": rule_source,
            "status": TAUT.EVIDENCE,
            "raise_to_source": True,
        },
        # ── الدعوى مقيَّدةً · ولا تُحذف ─────────────────────────────────
        "crossing_claim": {
            "was": "startswith(\"ال\") ⟶ JamidPath يعبر خطوطًا ممنوعة "
                   "— crosses: True ×3",
            "crosses_queried": queried,
            "all_three_forbidden": all(queried.values()),
            "query_used": "CANONICAL_REGISTRY.is_forbidden_direct(a, b)",
            "input_drawn_from": "CANONICAL_REGISTRY.lines",
            "crosses": TAUT.TAUTOLOGY,
            "crosses_why": "الأزواجُ الثلاثةُ من السجلّ، فتردّ True بحكم "
                           "الأخذ لا بحكم الواقع.",
            "mapping": "NOT_DERIVABLE",
            "mapping_why": 'أنّ startswith("ال") هو '
                           "Grapheme→FunctionalLetter ليس في الشيفرة ما "
                           "يدلّ عليه: لا Grapheme ولا FunctionalLetter "
                           "اسمُ طبقةٍ ولا مرحلة.",
            "status": "OWNER_RULING_REQUIRED",
            "withdrawn": False,
            "retained_because": "الدعوى تُقيَّد لا تُمحى.",
            "raise_to_source": False,
        },
        "note": "العددُ سعةٌ مقيسة، ودعوى العبور موقوفةٌ على حكم المالك.",
        "command": "python3 scripts/build_upstream.py  (يستفتي السجلَّ حيًّا)",
    }


def pre_weight_state() -> dict:
    """حالُ `PRE_WEIGHT` مقيسةً — بناءُ الحوامل شيءٌ، ووصلُها بالمشغّل آخر.

    **ما كان مكتوبًا.** «`PRE_WEIGHT_CAPACITY_AUDIT` غيرُ منفَّذة» — وهو
    وصفٌ يُقرأ: لا قانونَ ولا حاملَ ولا اختبار. والمقيسُ خلافُه: القوانينُ
    الثلاثةُ مصادَقة، والحواملُ الأربعةُ مشحونةٌ برموزها، واختباراتُها
    تمرّ. والذي لم يقع شيءٌ واحد: `corpus_runner` لا يستورد من `weight/`
    حرفًا، والراية في السجلّ `runtime_implemented=False`.

    فالوصفُ يُصحَّح إلى ما هو: **مبنيّةُ الحوامل، غيرُ موصولةٍ بالمشغّل**.
    والفرقُ ليس لفظيًّا: الأوّلُ يُقدّر عملًا لم يُعمل، والثاني يُسمّي
    الفجوةَ الباقيةَ وحدَها — وهي وصلةٌ لا بناء.
    """
    import importlib
    shipped: dict = {}
    for pr, (mod, syms) in PRE_WEIGHT_PRS.items():
        try:
            m = importlib.import_module(mod)
        except Exception as exc:                       # يُبلَّغ ولا يُنهي
            shipped[pr] = {"module": mod, "importable": False,
                           "error": type(exc).__name__, "missing": list(syms)}
            continue
        missing = [s for s in syms if not hasattr(m, s)]
        shipped[pr] = {"module": mod, "importable": True,
                       "symbols_promised": len(syms),
                       "missing": missing, "shipped": not missing}
    laws = {}
    for rel in PRE_WEIGHT_LAWS:
        p = VENDOR / rel
        laws[rel] = (len(p.read_text(encoding="utf-8").splitlines())
                     if p.is_file() else "ABSENT")
    # الوصلةُ الغائبةُ تُقاس بالتحليل النحويّ لا بالبحث النصّيّ
    # (`NO_TEXTUAL_GUARD`): أيُّ استيرادٍ في المشغّل يمسّ `weight`؟
    tree = ast.parse(RUNNER.read_text(encoding="utf-8"))
    mods = []
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and n.module:
            mods.append(n.module)
        elif isinstance(n, ast.Import):
            mods += [a.name for a in n.names]
    touching = sorted(m for m in mods if ".weight" in f".{m}")
    from taaqqul_slot_geometry.runtime.native_stage_registry import (
        get_native_stage_registry,
    )
    flag = {(getattr(s, "stage_id", None) or getattr(s, "name", None)):
            s.runtime_implemented for s in get_native_stage_registry()}
    return {
        "laws_ratified": laws,
        "prs_shipped": shipped,
        "prs_shipped_count":
            f'{sum(1 for v in shipped.values() if v.get("shipped"))}/'
            f'{len(PRE_WEIGHT_PRS)}',
        "prs_shipped_denominator": "PR-10..PR-13 — ما يَعِد به قانونُ docs/20",
        "carrier_tests": carrier_tests(),
        "runner_imports_touching_weight": touching,
        "runner_is_wired_to_carriers": bool(touching),
        "stage_runtime_implemented":
            flag.get("PRE_WEIGHT_CAPACITY_AUDIT", "STAGE_ABSENT"),
        "reading": "القانونُ مصادَقٌ والحواملُ مشحونةٌ واختباراتُها تمرّ — "
                   "والمشغّلُ لا يستوردها. فالفجوةُ وصلةٌ، لا بناء.",
        "supersedes_description": "«غيرُ منفَّذة»",
        "superseded_because": "الوصفُ الأوّلُ يُقرأ نفيًا للبناء كلِّه، "
                              "وهو مقيسٌ موجودًا.",
        "command": ".venv-taaqol/bin/python scripts/build_upstream.py",
    }


def carrier_tests() -> dict:
    """اختباراتُ الحواملِ — تُشغَّل، ولا يُنقل عددٌ من جولةٍ سابقة.

    والمقامُ يُشتقّ: ملفُّ اختبارٍ يستورد أحدَ الحوامل الأربعةِ **ويحمل
    اسمَه**. ولولا قيدُ الاسم لدخل كلُّ ما يستورد حاملًا عرَضًا — وذلك
    مقامٌ آخر، فيُذكر بجانبه ولا يُخلط به.
    """
    tests_dir = VENDOR / "tests"
    if not tests_dir.is_dir():
        return {"passed": "UNMEASURED", "reason": "TESTS_DIR_ABSENT"}
    stems = [mod.rsplit(".", 1)[-1] for mod, _ in PRE_WEIGHT_PRS.values()]
    targets = {mod for mod, _ in PRE_WEIGHT_PRS.values()}
    direct, importing = [], []
    for p in sorted(tests_dir.glob("test_*.py")):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        mods = []
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom) and n.module:
                mods.append(n.module)
            elif isinstance(n, ast.Import):
                mods += [a.name for a in n.names]
        if not any(m in targets for m in mods):
            continue
        importing.append(p.name)
        if any(s in p.stem for s in stems):
            direct.append(p.name)
    if not direct:
        return {"passed": "UNMEASURED", "reason": "NO_DIRECT_TEST_FILE"}
    env = dict(os.environ, PYTHONPATH=str(VENDOR / "src"))
    r = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", *[f"tests/{n}" for n in direct]],
        cwd=str(VENDOR), env=env, capture_output=True, text=True, check=False)
    tail = [ln for ln in r.stdout.splitlines() if " passed" in ln or
            " failed" in ln or " error" in ln]
    m = re.search(r"(\d+) passed", tail[-1] if tail else "")
    return {"files_direct": direct,
            "files_direct_denominator":
                "ملفُّ اختبارٍ يستورد حاملًا ويحمل اسمَه",
            "files_importing_a_carrier": len(importing),
            "files_importing_a_carrier_denominator":
                "مقامٌ أوسع — يُذكر ولا يُخلط بالأوّل",
            "passed": int(m.group(1)) if m else "UNMEASURED",
            "failed": r.returncode != 0,
            "summary": tail[-1] if tail else "NO_SUMMARY_LINE",
            "command": f'PYTHONPATH=src python -m pytest -q '
                       f'{" ".join("tests/" + n for n in direct)}'}


def shared_cause() -> dict:
    """`SHARED_CAUSE` — تُسمّى العلّةُ الواحدة، ولا يُدمج عدٌّ بعدّ.

    **الواقعة.** `C1` و`C5` علّتُهما واحدةٌ بعينها: المشغّلُ لا يصل إلى
    ما بُني. ومن اتّحاد العلّة انزلق القولُ إلى اتّحاد الأثر، فكاد
    يُجمع `17` و`42` عدًّا واحدًا.

    **والقاعدةُ التاسعة** (`SHARED_CAUSE_IS_NOT_SHARED_EFFECT`): اتّحادُ
    العلّة لا يُثبت اتّحادَ الأثر. والتباينُ يُقاس — بالعضويّة إن كان
    الحقلُ يحتمل، وبالتصميم إن كان لا يحتمل.

    **وهنا الحقلُ لا يحتمل**: `reason_family` حقلٌ واحدٌ لكلّ خانة، فلا
    خانةَ تحمل أسرتين. فالأساسُ `BY_DESIGN`. والعضويّةُ تُقاس فوقه
    تعضيدًا لا أساسًا — ولو كانت هي الأساسَ لكان `∩ = 0` خبرًا عن هذا
    التشغيل وحدَه، وهو خبرٌ عن البنية.
    """
    p = ROOT / "output" / "nazila_result" / "cells.csv"
    if not p.is_file():
        return {"status": "UNMEASURED",
                "reason": "CELLS_ABSENT — شغّل scripts/build_nazila_outputs.py"}
    import csv as _csv
    with p.open(encoding="utf-8", newline="") as fh:
        rows = list(_csv.DictReader(fh))
    c1, c5, seen = set(), set(), {}
    for r in rows:
        k = (r["section"], r["field"])
        seen[k] = seen.get(k, 0) + 1
        if r["status"] != "NOT_AVAILABLE":
            continue
        door = DOOR_OF_FAMILY.get(r["reason_family"])
        if door == "C1":
            c1.add(k)
        elif door == "C5":
            c5.add(k)
    duplicated = sorted(k for k, n in seen.items() if n > 1)
    return {
        "id": "SHARED_CAUSE_RUNNER_NOT_WIRED",
        "doors": ["C1", "C5"],
        "cause": "المشغّلُ لا يصل إلى ما بُني — لا يستورد الحوامل، "
                 "ولا يفتح المرحلةَ التي تستدعيها.",
        "cause_is_one": True,
        # ── والأثرُ يُقاس، ولا يُشتقّ من اتّحاد العلّة ──────────────
        "effect_C1_cells": len(c1),
        "effect_C5_cells": len(c5),
        "effect_intersection": len(c1 & c5),
        "effect_union": len(c1 | c5),
        "effect_sum_if_merged": len(c1) + len(c5),
        "merged": False,
        "not_merged_because": "SHARED_CAUSE_IS_NOT_SHARED_EFFECT — "
                              "اتّحادُ العلّة لا يُثبت اتّحادَ الأثر.",
        # ── أساسُ التباين · واحدٌ من قائمةٍ مغلقة ────────────────────
        "disjointness_basis": "BY_DESIGN",
        "disjointness_basis_why":
            "reason_family حقلٌ واحدٌ لكلّ خانة، فلا خانةَ تحمل أسرتين. "
            "والحقلُ لا يحتمل العضويّةَ المزدوجة أصلًا.",
        "key_is_unique": not duplicated,
        "duplicated_keys": duplicated[:5],
        "membership_check_intersection": len(c1 & c5),
        "membership_check_is_the_basis": False,
        "membership_check_note":
            "تعضيدٌ لا أساس: ∩ = 0 خبرٌ عن هذا التشغيل، والتصميمُ خبرٌ "
            "عن البنية. ولو تعارضا لكان التصميمُ هو المتَّهَم.",
        "sections_C1": sorted({k[0] for k in c1}),
        "sections_C5": sorted({k[0] for k in c5}),
        "sections_shared": sorted({k[0] for k in c1} & {k[0] for k in c5}),
        "ruled_by": "DR_HUSSEIN",
        "command": ".venv-taaqol/bin/python scripts/build_upstream.py",
    }


def c5_measure() -> dict:
    src = RUNNER.read_text(encoding="utf-8")
    probes = {"gamma": "gamma", "ClosureState": "ClosureState",
              "TransitionState": "core.transition_state",
              "forbidden_lines": "forbidden_lines",
              "EntryBoundary": "EntryBoundary"}
    imports = {k: (v in src) for k, v in probes.items()}
    lines = [i for i, ln in enumerate(src.splitlines(), 1)
             if ln.startswith(("import ", "from "))]
    return {"imports": imports, "none_present": not any(imports.values()),
            "import_lines_in_runner": lines,
            **c5_cells(),
            "command": "grep -nE '^(import|from) ' "
                       "vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime/"
                       "corpus_runner.py"}


# ── البنود ─────────────────────────────────────────────────────────────
def build_items(joint: dict) -> list[dict]:
    false_lines = false_flag_lines()
    if len(false_lines) != 2:
        raise Blocked(f"OWNER_ALERT: EXPECTED_TWO_FALSE_FLAGS — "
                      f"وُجد {len(false_lines)} في {REG.name}")
    c1_line, c4_line = false_lines
    blocked = blocked_by_c1()
    shared = shared_cause()
    return [
        {"ident": "C1", "status": "DECLARED",
         # الوصفُ صُحِّح بحكم المالك: البناءُ مقيسٌ موجودًا، والغائبُ
         # الوصلة. و«غيرُ منفَّذة» تبقى مسجّلةً في `superseded_title`
         # — الدعوى تُقيَّد لا تُمحى.
         "title": "PRE_WEIGHT مبنيّةُ الحوامل، غيرُ موصولةٍ بالمشغّل",
         "superseded_title": "PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة",
         "superseded_by": "DR_HUSSEIN — بعد قياسِ القانون والحوامل "
                          "والاختبارات، وقياسِ غياب الوصلة وحدَه.",
         "location": {"file": str(REG.relative_to(ROOT)), "line": c1_line,
                      "symbol": "runtime_implemented", "occurrences": 1,
                      "text": "runtime_implemented=False"},
         "shared_cause": shared,
         "measure": {"stages_closed_per_token": blocked["count"],
                     "stages_closed_names": blocked["names"],
                     "pre_weight_state": pre_weight_state(),
                     "command": blocked["command"]}},
        {"ident": "C2", "status": "DECLARED",
         "title": "مفاتيحُ classify_token_paths غيرُ مشكولة",
         "location": locate(REG, "def classify_token_paths"),
         "location_secondary": locate(REG, "mapping: dict"),
         "measure": c2_measure()},
        {"ident": "C3", "status": "DECLARED",
         "title": 'startswith("ال") ⟶ JamidPath يعبر خطوطًا ممنوعة',
         "location": locate(REG, 'token.startswith("ال")'),
         "measure": c3_measure()},
        {"ident": "C4", "status": "DECLARED",
         "title": "ANSWER_AUDIT غيرُ منفَّذة",
         "location": {"file": str(REG.relative_to(ROOT)), "line": c4_line,
                      "symbol": "runtime_implemented", "occurrences": 1,
                      "text": "runtime_implemented=False"},
         "measure": {"seals_issued": 0,
                     "seals_issued_denominator": "أختامٌ صدرت في أيّ تشغيل",
                     "not_opened_by_C1": True,
                     "note": "لا تُفتح بفتح C1 — فهي runtime_implemented=False",
                     "command": blocked["command"]}},
        {"ident": "C5", "status": "DECLARED",
         "title": "corpus_runner لا يستشير الحوامل ولا سجلَّ الخطوط",
         "location": locate(RUNNER, "from taaqqul_slot_geometry"),
         "shared_cause": shared,
         "measure": c5_measure()},
        {"ident": "C_PATH", "status": "NOT_CHOSEN",
         "title": "المسلكُ المختار لبنود (ج)",
         "location": None,
         "measure": {
             "paths": ["ج-١ تُقاس وتُعلن", "ج-٢ بلاغٌ إلى المصدر",
                       "ج-٣ فرعٌ مُعلَنٌ بـpin ثانٍ"],
             "chosen": None, "currently": "ج-١ يجري",
             "paths_measured_ready": ["C1", "C2", "C3", "C5"],
             "C4_not_a_request": True,
             "AUTHORITY_TO_SEND": "OWNER", "SENT": "NO",
             "command": "—"}},
    ]


# ── الحرّاس ────────────────────────────────────────────────────────────
NUMERIC = re.compile(r"^-?\d+(\.\d+)?$")


def numeric_fields(measure: dict) -> list[str]:
    """كلُّ حقلٍ قيمتُه عددٌ أو نسبةٌ `a/b` — وهو ما يلزمه أمر."""
    out = []
    for k, v in measure.items():
        if k.endswith(("_denominator", "command")) or k == "note":
            continue
        if isinstance(v, bool):
            continue
        if isinstance(v, (int, float)) or (
                isinstance(v, str) and re.fullmatch(r"\d+/\d+", v)):
            out.append(k)
    return out


def tautology_rows(items: list[dict]) -> list[str]:
    """`G_EVIDENCE_IS_NOT_TAUTOLOGY` على بنود (ج) — بمصدرِ المدخل.

    يُجمَع كلُّ حقلٍ فرعيٍّ يحمل `input_drawn_from` و`status`، ويُقابَل
    وسمُه بالمشتقِّ من مصدره. ويبلّغ ولا يموت.
    """
    rows = []
    for i in items:
        m = i.get("measure") or {}
        for key, sub in m.items():
            if isinstance(sub, dict) and "input_drawn_from" in sub:
                rows.append({"query_id": f'{i.get("ident", "?")}.{key}',
                             "source": key, "target": "—",
                             "input_drawn_from": sub["input_drawn_from"],
                             # الوسمُ المعنيُّ هو وسمُ الاستفتاء نفسِه
                             # (`crosses`) حيث وُجد؛ و`status` هناك يقول
                             # لمن الحكمُ لا ما نوعُ الجواب.
                             "status": sub.get("crosses", sub.get("status"))})
    g = TAUT.evidence_is_not_tautology(rows)
    return g["mislabelled"] + g["unclassified"]


def shared_cause_rows(items: list[dict]) -> list[str]:
    """`G_SHARED_CAUSE_NOT_MERGED` — سمُّ القاعدة التاسعة، ذو ثلاثة أوجه.

    يُجمَع كلُّ بندٍ يعلن `shared_cause`، ثمّ:

    1. **الدمجُ يُصطاد**: `merged=True` مخالفةٌ صريحة، وكذلك عددٌ واحدٌ
       يساوي مجموعَ الأثرين — وهو الدمجُ حين يُنكَر.
    2. **الأساسُ يُسمّى**: `disjointness_basis` من القائمة المغلقة، وإلّا
       فالتباينُ مفترَضٌ لا مقيس — و`ASSUMED` تسقط هنا.
    3. **الأساسُ يُطابق ما يحتمله الحقل**: من قال `BY_MEMBERSHIP` وحقلُه
       لا يحتمل ازدواجًا (`key_is_unique`) فقد بنى خبرًا عن البنية على
       تشغيلٍ واحد؛ ومن قال `BY_DESIGN` وحقلُه يحتمل فقد ادّعى استحالةً
       لا يملكها.

    ويُبلّغ ولا يموت: بندٌ بلا حقلٍ يُسمّى `<ident>:NO_<FIELD>`.
    """
    out: list[str] = []
    for i in items:
        sc = i.get("shared_cause")
        if not isinstance(sc, dict):
            continue
        ident = i.get("ident", "?")
        if sc.get("status") == "UNMEASURED":
            out.append(f"{ident}:UNMEASURED")
            continue
        if sc.get("merged"):
            out.append(f"{ident}:MERGED")
        a, b = sc.get("effect_C1_cells"), sc.get("effect_C5_cells")
        u = sc.get("effect_union")
        if isinstance(a, int) and isinstance(b, int) and u == a + b \
                and sc.get("effect_intersection") != 0:
            out.append(f"{ident}:UNION_EQUALS_SUM_WITHOUT_DISJOINTNESS")
        basis = sc.get("disjointness_basis")
        if basis not in DISJOINTNESS_BASIS:
            out.append(f"{ident}:BASIS_NOT_IN_CLOSED_LIST({basis})")
            continue
        uniq = sc.get("key_is_unique")
        if uniq is None:
            out.append(f"{ident}:NO_KEY_IS_UNIQUE")
        elif basis == "BY_DESIGN" and uniq is not True:
            out.append(f"{ident}:BY_DESIGN_BUT_FIELD_ADMITS_BOTH")
        elif basis == "BY_MEMBERSHIP" and uniq is True:
            out.append(f"{ident}:BY_MEMBERSHIP_BUT_FIELD_FORBIDS_BOTH")
    return out


def guard(items: list[dict], joint: dict) -> dict:
    f: dict = {}
    # `GUARD_MUST_REPORT_NOT_DIE` — كلُّ حقلٍ يُقرأ بـ`get`. وبندٌ ناقصٌ
    # يُبلَّغ باسمه، ولا يرفع استثناءً يُنهي الحرّاسَ الباقية فتُقرأ سليمةً
    # وهي لم تُشغَّل. اصطاده test_every_guard_survives_a_missing_subject.
    f["G_EVERY_NUMBER_HAS_A_COMMAND"] = [
        f'{i.get("ident", "?")}.{k}' for i in items
        for k in numeric_fields(i.get("measure") or {})
        if not (i.get("measure") or {}).get("command")]
    f["G_LOCATION_RESOLVES"] = [
        i.get("ident", "?") for i in items
        if i.get("location") and not resolves(i["location"])]
    # غيابُ `C3` يُبلَّغ ولا يُسقط الحارسَ بـ`StopIteration`. وحارسٌ يموت
    # حين يغيب موضوعُه ليس حارسًا: الاستثناءُ يُنهي الفحصَ كلَّه فتُقرأ
    # البقيّةُ سليمةً وهي لم تُفحص. اصطاده سمُّ `G_NO_DONE_IN_C`.
    c3 = next((i.get("measure") for i in items
               if i.get("ident") == "C3"), None)
    # `R1` — `G_FORBIDDEN_LINES_QUERIED` كان يعدّ الاستفتاءَ دليلًا، وهو
    # خطأٌ مقرٌّ به (`REVIEWER_WITHDRAWN_1`). فصار يشهد بما يملك: **أنّ
    # النداءَ وقع حيًّا**، لا أنّ جوابَه شهادة. وأمّا الوسمُ فيتولّاه
    # `G_EVIDENCE_IS_NOT_TAUTOLOGY` بمصدرِ المدخل لا بالجواب.
    f["G_FORBIDDEN_LINES_QUERIED"] = (
        ["C3:ABSENT"] if c3 is None
        else [] if (c3.get("crossing_claim") or {}).get("query_used")
        else ["C3:NO_LIVE_QUERY"])
    f["G_EVIDENCE_IS_NOT_TAUTOLOGY"] = tautology_rows(items)
    f["G_SHARED_CAUSE_NOT_MERGED"] = shared_cause_rows(items)
    ratios = [f'{i.get("ident", "?")}.{k}' for i in items
              for k, v in (i.get("measure") or {}).items()
              if isinstance(v, str) and re.fullmatch(r"\d+/\d+", v)
              and f"{k}_denominator" not in (i.get("measure") or {})]
    f["G_DENOMINATOR_NAMED"] = ratios
    f["G_JOINT_FIELD_PRESENT"] = (
        [] if joint.get("stages_total") == 16 else ["JOINT"])
    # حقلٌ ناقصٌ يُبلَّغ ولا يرفع `KeyError`. والعلّةُ واحدةٌ في الموضعين:
    # استثناءٌ داخل الحارس يُنهي الفحصَ كلَّه، فتُقرأ بقيّةُ الحرّاس سليمةً
    # وهي لم تُشغَّل. والحارسُ يُبلّغ ولا يموت.
    f["G_NO_DONE_IN_C"] = [i.get("ident", "?") for i in items
                           if i.get("status") not in C_STATUSES]
    return f


def recount(doc: str, items: list[dict]) -> dict:
    body = doc.split("## البنود", 1)[-1].split("\n## ", 1)[0]
    rows = [ln for ln in body.splitlines()
            if ln.startswith("| `") and not ln.startswith("| `البند")]
    return {"rows": len(rows), "items": len(items),
            "closes": len(rows) == len(items)}


def render(items: list[dict], joint: dict, g: dict, gate: dict) -> str:
    o = ["# بنودُ ما خرج عن الولاية — تُقاس وتُعلَن، ولا تُلمس", "",
         "```text", "VENDOR_IS_FROZEN = TRUE",
         f'VENDOR_HEAD = {gate["vendor_head"]}',
         f'VENDOR_PORCELAIN_LINES = {gate["porcelain_lines"]}',
         "CLAIM_PROJECT_FINISHED = NO", "```", "",
         "## الحقلُ الجامع — يُقرأ قبل البنود", "", "```text",
         f'stages_total               {joint["stages_total"]}',
         f'runtime_implemented = True {joint["runtime_implemented_true"]}/'
         f'{joint["stages_total"]}',
         f'runtime_implemented = False {joint["runtime_implemented_false"]}/'
         f'{joint["stages_total"]}   '
         f'{" · ".join(joint["names_of_false"])}',
         f'stages_not_opened_today    {joint["stages_not_opened_today"]}',
         f'stages_C1_would_open       {joint["stages_C1_would_open"]}',
         f'still_closed_after_C1      '
         f'{" · ".join(joint["stages_still_closed_after_C1"])}',
         f'reachable_on_a_content_token '
         f'{joint["reachable_on_a_content_token"]["value"]}   '
         f'({joint["reachable_on_a_content_token"]["arithmetic"]})',
         "```", "", joint["reading"], "",
         "## البنود", "",
         "| البند | العنوان | الحال | الموضع |", "|---|---|---|---|"]
    for i in items:
        loc = (f'`{Path(i["location"]["file"]).name}:{i["location"]["line"]}`'
               if i["location"] else "—")
        o.append(f'| `{i["ident"]}` | {i["title"]} | `{i["status"]}` | '
                 f'{loc} |')
    o.append("")
    for i in items:
        o += [f'### `{i["ident"]}` · {i["title"]}', ""]
        if i["location"]:
            L = i["location"]
            o += [f'**الموضع**: `{L["file"]}:{L["line"]}` — '
                  f'`{L["text"]}`', ""]
        if i.get("superseded_title"):
            o += [f'**العنوانُ السابق**: «{i["superseded_title"]}» — '
                  f'{i["superseded_by"]} والدعوى تُقيَّد لا تُمحى.', ""]
        sc = i.get("shared_cause")
        if isinstance(sc, dict) and sc.get("id"):
            o += [f'**علّةٌ مشتركة** `{sc["id"]}` مع '
                  f'{" · ".join(d for d in sc["doors"] if d != i["ident"])} '
                  f'— {sc["cause"]}', "",
                  "```text",
                  f'C1 {sc["effect_C1_cells"]} خانة  ·  '
                  f'C5 {sc["effect_C5_cells"]} خانة  ·  '
                  f'∩ {sc["effect_intersection"]}  ·  '
                  f'∪ {sc["effect_union"]}',
                  f'MERGED = {str(sc["merged"]).upper()}   '
                  f'({sc["effect_C1_cells"]} + {sc["effect_C5_cells"]} = '
                  f'{sc["effect_sum_if_merged"]} — ولا يُكتب عددًا)',
                  f'DISJOINTNESS_BASIS = {sc["disjointness_basis"]}',
                  f'MEMBERSHIP_IS_THE_BASIS = '
                  f'{str(sc["membership_check_is_the_basis"]).upper()}',
                  "```", "",
                  sc["not_merged_because"], "",
                  f'**أساسُ التباين**: {sc["disjointness_basis_why"]}', "",
                  f'**والعضويّة**: {sc["membership_check_note"]}', ""]
        o += ["```json",
              json.dumps(i["measure"], ensure_ascii=False, indent=1),
              "```", ""]
    o += ["## الحرّاس", "", "| الحارس | مخالفات |", "|---|---|"]
    for k, v in g.items():
        o.append(f'| `{k}` | `{v if v else "لا شيء"}` |')
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/upstream")
    a = ap.parse_args()

    gate = gate_vendor()
    if not gate["passes"]:
        print(f"BLOCKED_AT_VENDOR: {json.dumps(gate, ensure_ascii=False)}")
        return 2

    joint = joint_field()
    items = build_items(joint)
    g = guard(items, joint)
    hard = {k: v for k, v in g.items() if v}
    if hard:
        print("OWNER_ALERT: " + json.dumps(hard, ensure_ascii=False))
        return 3

    doc = render(items, joint, g, gate)
    rc = recount(doc, items)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "00_upstream.json").write_text(json.dumps(
        {"gate": gate, "joint_field": joint, "items": items},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "03_upstream.md").write_text(doc, encoding="utf-8")
    (out / "01_ledger.json").write_text(json.dumps(
        {"items": [{"ident": i["ident"], "status": i["status"]}
                   for i in items],
         "by_status": {s: sum(1 for i in items if i["status"] == s)
                       for s in C_STATUSES},
         "guards": g, "recount_from_report": rc},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print(f'STAGES        {joint["runtime_implemented_true"]}/'
          f'{joint["stages_total"]} منفَّذة · '
          f'{joint["runtime_implemented_false"]} لا  '
          f'({" · ".join(joint["names_of_false"])})')
    print(f'NOT_OPENED    {joint["stages_not_opened_today"]} · '
          f'C1 تفتح {joint["stages_C1_would_open"]} · '
          f'تبقى {joint["stages_still_closed_after_C1"]}')
    r = joint["reachable_on_a_content_token"]
    print(f'REACHABLE     {r["value"]}   {r["arithmetic"]}')
    print(f'  والتصادم: runtime_implemented=True عددُها '
          f'{r["collision_warning"]["runtime_implemented_true_is_also"]} '
          f'ومجموعتُها أخرى — '
          f'{r["collision_warning"]["only_in_reachable"]} مقابل '
          f'{r["collision_warning"]["only_in_runtime_implemented_true"]}')
    print(f'ITEMS         {len(items)} · DECLARED '
          f'{sum(1 for i in items if i["status"] == "DECLARED")} · '
          f'NOT_CHOSEN {sum(1 for i in items if i["status"] == "NOT_CHOSEN")}')
    for k, v in g.items():
        print(f'  {k:32} {v if v else "PASS"}')
    print(f'RECOUNT       {rc["rows"]}/{rc["items"]} يقفل {rc["closes"]}')
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
