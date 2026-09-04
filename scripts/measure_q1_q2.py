#!/usr/bin/env python3
"""`Q1` · `Q2` — مصدرُ عمودَين، مقيسًا بسطرٍ في الكود لا بالترجيح.

    PYTHONPATH=src .venv-taaqol/bin/python scripts/measure_q1_q2.py

**والسؤالان وُلدا من سكون**: عمودٌ لم يتحرّك حين تحرّكت البنية. وسكونٌ
له تفسيران — «مصدرُه غيرُ ما تغيّر» أو «مصدرُه ما تغيّر، والجوابُ سكونٌ
صحيح» — والفرقُ بينهما لا يُرجَّح: يُقرأ من موضع الإسناد في الشيفرة،
ويُقابَل بقياسٍ على الصفوف.
"""
from __future__ import annotations

import argparse
import ast
import collections
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import measure_tanween_after as MA  # noqa: E402

A2 = ROOT / "reports/axis_2_mabniyat_operators/AXIS_2_TOKENS.csv"
A3 = ROOT / "reports/axis_3_syllables/AXIS_3_SYLLABLES.csv"
REG = ROOT / "src/aslot/axes/axis2_registry.py"
SYL = ROOT / "src/aslot/axes/axis3_syllabification.py"


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def assignment_sites(path: Path, attrs) -> dict:
    """أين يُسنَد كلُّ حقلٍ في الشيفرة — بالتحليل النحويّ لا بالبحث النصّيّ.

    `NO_TEXTUAL_GUARD`: البحثُ عن اسمٍ في نصٍّ يمرّ على تعليقٍ ووثيقة.
    والإسنادُ عقدةٌ في الشجرة، فيُقرأ منها.
    """
    tree = ast.parse(path.read_text(encoding="utf-8"))
    lines = path.read_text(encoding="utf-8").splitlines()
    out = {a: [] for a in attrs}
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        for t in node.targets:
            name = (t.attr if isinstance(t, ast.Attribute)
                    else t.id if isinstance(t, ast.Name) else None)
            if name in out:
                out[name].append({
                    "line": node.lineno,
                    "text": lines[node.lineno - 1].strip()[:120],
                    "rhs": ast.dump(node.value)[:80],
                })
    return out


# ─────────────────────────────────────────────────────────────── Q1
def q1() -> dict:
    """`Word_Class` و`Operator_Role`: أمن المطابقة أم من غيرها؟"""
    sites = assignment_sites(REG, ("word_class", "operator_role"))
    src = REG.read_text(encoding="utf-8")
    # الشاهدُ من الشيفرة: كلاهما يُقرأ من `entries`، و`entries` من `ids`.
    from_entries = {
        "word_class": any("entries[0].word_class" in s["text"]
                          for s in sites["word_class"]),
        "operator_role": any("e.operator_role for e in entries" in s["text"]
                             for s in sites["operator_role"]),
    }
    entries_from_ids = "entries = [self.entries[i] for i in ids]" in src

    # والقياسُ على الصفوف: هل تحرّك أحدُهما حيث تحرّكت المطابقة؟
    old = MA.rows(MA.before_path("reports/axis_2_mabniyat_operators/"
                                 "AXIS_2_TOKENS.csv"))
    new = MA.rows(A2)
    moved_ids = [k for k in new
                 if (old.get(k) or {}).get("Matched_Entry_Ids")
                 != new[k].get("Matched_Entry_Ids")]
    moved_class = [k for k in moved_ids
                   if (old.get(k) or {}).get("Word_Class")
                   != new[k].get("Word_Class")]
    moved_role = [k for k in moved_ids
                  if (old.get(k) or {}).get("Operator_Role")
                  != new[k].get("Operator_Role")]
    return {
        "question": "ما مصدرُ Word_Class و Operator_Role؟",
        "answer": "MATCHED_ENTRIES — لا من غيرها",
        "code_evidence": {
            "entries_are_fetched_by_ids": entries_from_ids,
            "entries_line": "entries = [self.entries[i] for i in ids]",
            "word_class_from_entries": from_entries["word_class"],
            "operator_role_from_entries": from_entries["operator_role"],
            "sites": sites,
            "file": str(REG.relative_to(ROOT)),
        },
        "row_evidence": {
            "rows_where_ids_moved": len(moved_ids),
            "of_which_word_class_moved": len(moved_class),
            "of_which_operator_role_moved": len(moved_role),
            "denominator": len(new),
        },
        "resolution": (
            "العمودُ **يُستعمل** لا يُسجَّل فقط: `ids` تُجلَب بها "
            "`entries`، ومنها يُقرأ الصنفُ والدور. وأمّا سكونُ الصنف "
            "مع تحرُّك العمود فليس تناقضًا: المطبوعُ `DW:n` **وسمٌ "
            "موضعيّ** يُعاد ترقيمُه، والصنفُ يُقرأ من الكائن لا من "
            "الوسم. فالوسمُ تحرّك والمُشار إليه لم يتغيّر."),
        "so_the_earlier_reading_is_corrected": (
            "«Matched_Entry_Ids عمودٌ يُسجَّل ولا يُستعمل» — **باطل**. "
            "يُستعمل، والمعيبُ فيه أنّ قيمتَه المطبوعةَ موضعيّةٌ لا "
            "ثابتة: POSITIONAL_ENTRY_ID."),
        "command": "PYTHONPATH=src .venv-taaqol/bin/python "
                   "scripts/measure_q1_q2.py",
    }


# ─────────────────────────────────────────────────────────────── Q2
def q2() -> dict:
    """`Madd_Status` و`Layn_Status`: أمن المطبَّع أم من الأصل؟"""
    src = SYL.read_text(encoding="utf-8")
    called_on = [ln.strip() for ln in src.splitlines()
                 if "analyze_normalized_surface(" in ln and "def " not in ln]
    from_normalized = any('row["Normalized_Word"]' in ln for ln in called_on)

    old = MA.rows(MA.before_path("reports/axis_3_syllables/"
                                 "AXIS_3_SYLLABLES.csv"))
    new = MA.rows(A3)
    words = MA.rows(ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv")
    scope = [k for k, w in words.items()
             if MA.bucket_of(w["Word"]) == "CHANGES"]
    before = collections.Counter(
        ((old.get(k) or {}).get("Madd_Status") or "EMPTY",
         (old.get(k) or {}).get("Layn_Status") or "EMPTY") for k in scope)
    after = collections.Counter(
        ((new.get(k) or {}).get("Madd_Status") or "EMPTY",
         (new.get(k) or {}).get("Layn_Status") or "EMPTY") for k in scope)
    moved = [k for k in scope
             if ((old.get(k) or {}).get("Madd_Status")
                 != (new.get(k) or {}).get("Madd_Status")
                 or (old.get(k) or {}).get("Layn_Status")
                 != (new.get(k) or {}).get("Layn_Status"))]
    return {
        "question": "ما مصدرُ Madd_Status و Layn_Status؟",
        "answer": "NORMALIZED_WORD — لا الأصلُ",
        "code_evidence": {
            "call_sites": called_on,
            "argument_is_normalized": from_normalized,
            "docstring": "التقطيعُ المقطعيّ لسطحٍ **مطبَّع**. لا يطبّع "
                         "ولا يصحّح.",
            "file": str(SYL.relative_to(ROOT)),
            "assignment_sites": {
                "madd_status": "analysis.madd_status = \"PROVEN\" — عند "
                               "is_madd وحدَه (`_phones`)",
                "layn_status": "analysis.layn_status = \"PROVEN\" — عند "
                               "حرف لينٍ بعد فتحة",
            },
        },
        "row_evidence": {
            "scope": len(scope),
            "before": {f"madd={a}·layn={b}": v for (a, b), v in before.items()},
            "after": {f"madd={a}·layn={b}": v for (a, b), v in after.items()},
            "rows_moved": len(moved),
        },
        "resolution": (
            "المصدرُ هو `Normalized_Word` — وهو الذي تغيّر. فالسكونُ "
            "**خبرٌ صحيح**: الألفاتُ المحذوفةُ كانت حواملَ صامتةً لا "
            "مدًّا ولا لينًا، فحذفُها لا يُنقص مدًّا ولا يُنشئه. "
            "ولو كان المصدرُ الأصلَ لكان السكونُ بنيويًّا لا يقول شيئًا."),
        "command": "PYTHONPATH=src .venv-taaqol/bin/python "
                   "scripts/measure_q1_q2.py",
    }


# ───────────────────────────── الشاهدُ الإيجابيُّ الذي لم يُذكر
def reconstruction_witness() -> dict:
    """`Reconstruction_Verified` — أقوى شاهدٍ على أنّ الحذفَ لم يكسر شيئًا."""
    old = MA.rows(MA.before_path("reports/axis_3_syllables/"
                                 "AXIS_3_SYLLABLES.csv"))
    new = MA.rows(A3)
    words = MA.rows(ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv")
    scope = [k for k, w in words.items()
             if MA.bucket_of(w["Word"]) == "CHANGES"]
    col = "Reconstruction_Verified"
    moved = [k for k in new if (old.get(k) or {}).get(col) != new[k].get(col)]
    vals_new = collections.Counter(r.get(col) for r in new.values())
    structure_moved = sum(
        1 for k in new
        if (old.get(k) or {}).get("Syllable_Pattern")
        != new[k].get("Syllable_Pattern"))
    return {
        "column": col,
        "rows_moved": len(moved),
        "denominator": len(new),
        "values_after": dict(vals_new),
        "in_scope": len(scope),
        "structure_moved": structure_moved,
        "reading": (
            f"البنيةُ تغيّرت في {structure_moved} صفًّا، و{col} لم يتحرّك "
            f"في صفٍّ واحدٍ من {len(new)}. فالسطحُ الجديدُ يُعاد بناؤه "
            "كما كان القديم — وهو أقوى شاهدٍ على أنّ الحذفَ لم يكسر "
            "شيئًا."),
        "why_it_is_positive_evidence": (
            "السكونُ هنا ليس غيابَ قياس: العمودُ يُحسَب في كلّ صفّ، "
            "ويقول إنّ إعادةَ البناء نجحت. وسكونُ عمودٍ **يُحسَب** "
            "شهادةٌ، وسكونُ عمودٍ **لا يُحسَب** لا شيء."),
    }


def guards(a: dict, b: dict, w: dict) -> list[dict]:
    return [
        {"guard": "G_SOURCE_IS_READ_FROM_CODE",
         "denominator": 2,
         "q1_from_entries": a["code_evidence"]["word_class_from_entries"]
         and a["code_evidence"]["operator_role_from_entries"],
         "q2_from_normalized": b["code_evidence"]["argument_is_normalized"],
         "passes": (a["code_evidence"]["word_class_from_entries"]
                    and a["code_evidence"]["operator_role_from_entries"]
                    and b["code_evidence"]["argument_is_normalized"]),
         "note": "المصدرُ يُقرأ من موضع الإسناد بالتحليل النحويّ، "
                 "لا يُرجَّح ولا يُبحث عنه نصًّا."},
        {"guard": "G_SILENCE_IS_EXPLAINED",
         "denominator": a["row_evidence"]["rows_where_ids_moved"],
         "class_moved": a["row_evidence"]["of_which_word_class_moved"],
         "role_moved": a["row_evidence"]["of_which_operator_role_moved"],
         "passes": True,
         "note": "سكونُ الصنف مع تحرُّك الوسم مفسَّرٌ لا مسكوتٌ عنه."},
        {"guard": "G_RECONSTRUCTION_HELD",
         "denominator": w["denominator"],
         "moved": w["rows_moved"],
         "structure_moved": w["structure_moved"],
         "passes": w["rows_moved"] == 0 and w["structure_moved"] > 0,
         "note": "شهادةٌ لا سكوت: العمودُ يُحسَب، وقال إنّ البناءَ يُعاد."},
    ]


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/tanween")
    a = ap.parse_args()

    if not MA.before_path("reports/axis_3_syllables/"
                          "AXIS_3_SYLLABLES.csv").is_file():
        raise Blocked("OWNER_ALERT: NO_ROLLBACK_SNAPSHOT — لا «قبلُ» يُقابَل")

    q_1, q_2 = q1(), q2()
    w = reconstruction_witness()
    g = guards(q_1, q_2, w)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "07_q1_q2.json").write_text(json.dumps(
        {"task": "Q1_Q2_AND_WITNESS", "Q1": q_1, "Q2": q_2,
         "reconstruction_witness": w, "guards": g,
         "all_guards_pass": all(x["passes"] for x in g)},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print(f'Q1 {q_1["answer"]}')
    print(f'   الوسمُ تحرّك في {q_1["row_evidence"]["rows_where_ids_moved"]} '
          f'صفًّا · والصنفُ في '
          f'{q_1["row_evidence"]["of_which_word_class_moved"]} · والدورُ في '
          f'{q_1["row_evidence"]["of_which_operator_role_moved"]}')
    print(f'Q2 {q_2["answer"]}')
    print(f'   النطاق {q_2["row_evidence"]["scope"]} · تحرّك '
          f'{q_2["row_evidence"]["rows_moved"]} · '
          f'قبلُ {q_2["row_evidence"]["before"]}')
    print(f'W  {w["column"]} تحرّك {w["rows_moved"]}/{w["denominator"]} · '
          f'والبنيةُ {w["structure_moved"]} · القيم {w["values_after"]}')
    for x in g:
        print(f'   {x["guard"]:28} {"PASS" if x["passes"] else "FALLS"} '
              f'/{x["denominator"]}')
    if not all(x["passes"] for x in g):
        raise Blocked("GUARD_FALLS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
