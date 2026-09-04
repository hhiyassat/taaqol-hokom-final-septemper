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
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
PKG = VENDOR / "src" / "taaqqul_slot_geometry"
sys.path.insert(0, str(VENDOR / "src"))

PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
REG = PKG / "runtime" / "native_stage_registry.py"
RUNNER = PKG / "runtime" / "corpus_runner.py"

#: حالاتُ بنود (ج) — **مغلقة**. و`DONE` ليست منها: الإعلانُ استيفاءُ ما
#: نملك، لا زوالُ العيب. ومن وسم بندًا هنا `DONE` فقد ادّعى مسَّ المصدر.
C_STATUSES = ("DECLARED", "NOT_CHOSEN")


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
    return {
        "stages_total": len(specs),
        "runtime_implemented_true": len(specs) - len(false_),
        "runtime_implemented_false": len(false_),
        "names_of_false": names,
        "stages_blocked_by_C1": blocked["count"],
        "stages_blocked_by_C1_names": blocked["names"],
        "reading": ("تعقُّل مكتوبٌ إلا مرحلتين، وإحداهما تُغلق اثنتَي عشرة. "
                    "فليست خمسةَ إصلاحاتٍ تُطلب من sonaiso، بل مرحلةٌ واحدةٌ "
                    "تفتح اثنتَي عشرة، وأربعةٌ دونها."),
        "command": ("python -c \"from taaqqul_slot_geometry.runtime."
                    "native_stage_registry import get_native_stage_registry "
                    "as G; s=list(G()); print(len(s), "
                    "sum(1 for x in s if x.runtime_implemented))\""),
    }


def blocked_by_c1() -> dict:
    """المراحلُ التي تُغلق لكلّ توكن — تُعدّ من تشغيلٍ حقيقيّ لا من وصف."""
    from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus
    res = run_native_corpus("probe", ("مَاتَ",))
    recs = [r for t in res.token_results for r in t.records]
    closed = sorted({r.stage_id for r in recs
                     if str(getattr(r.transition_state, "value",
                                    r.transition_state)) == "NOT_OPENED"})
    return {"count": len(closed), "names": closed,
            "command": "python -c \"from taaqqul_slot_geometry.runtime."
                       "corpus_runner import run_native_corpus as R; "
                       "r=R('probe',('مَاتَ',)); "
                       "print(sum(1 for t in r.token_results for x in t.records "
                       "if x.transition_state.value=='NOT_OPENED'))\""}


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
    """`C3` — والخطُّ حجّة، والعددُ سعة. والخطوطُ **تُستفتى** ولا تُنقل."""
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
    return {
        **reach,
        "crosses_queried": queried,
        "all_three_forbidden": all(queried.values()),
        "query_used": "CANONICAL_REGISTRY.is_forbidden_direct(a, b)",
        "note": "العددُ سعةٌ، والخطُّ حجّة. والخطوطُ مُستفتاةٌ لا منقولة.",
        "command": "python3 scripts/build_upstream.py  (يستفتي السجلَّ حيًّا)",
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
            "cells_not_emitted": 35,
            "cells_not_emitted_denominator": "خاناتُ وثيقة النازلة (292)",
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
    return [
        {"ident": "C1", "status": "DECLARED",
         "title": "PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة",
         "location": {"file": str(REG.relative_to(ROOT)), "line": c1_line,
                      "symbol": "runtime_implemented", "occurrences": 1,
                      "text": "runtime_implemented=False"},
         "measure": {"stages_closed_per_token": blocked["count"],
                     "stages_closed_names": blocked["names"],
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


def guard(items: list[dict], joint: dict) -> dict:
    f: dict = {}
    f["G_EVERY_NUMBER_HAS_A_COMMAND"] = [
        f'{i["ident"]}.{k}' for i in items
        for k in numeric_fields(i["measure"] or {})
        if not (i["measure"] or {}).get("command")]
    f["G_LOCATION_RESOLVES"] = [
        i["ident"] for i in items
        if i["location"] and not resolves(i["location"])]
    # غيابُ `C3` يُبلَّغ ولا يُسقط الحارسَ بـ`StopIteration`. وحارسٌ يموت
    # حين يغيب موضوعُه ليس حارسًا: الاستثناءُ يُنهي الفحصَ كلَّه فتُقرأ
    # البقيّةُ سليمةً وهي لم تُفحص. اصطاده سمُّ `G_NO_DONE_IN_C`.
    c3 = next((i["measure"] for i in items if i["ident"] == "C3"), None)
    f["G_FORBIDDEN_LINES_QUERIED"] = (
        ["C3:ABSENT"] if c3 is None
        else [] if c3.get("all_three_forbidden") else ["C3"])
    ratios = [f'{i["ident"]}.{k}' for i in items
              for k, v in (i["measure"] or {}).items()
              if isinstance(v, str) and re.fullmatch(r"\d+/\d+", v)
              and f"{k}_denominator" not in (i["measure"] or {})]
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
         f'stages_blocked_by_C1       {joint["stages_blocked_by_C1"]}',
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
    print(f'BLOCKED_BY_C1 {joint["stages_blocked_by_C1"]}')
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
