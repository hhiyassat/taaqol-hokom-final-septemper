#!/usr/bin/env python3
"""`05_pending.json` · `06_report.md` — الموقوفُ بأعيانه، والجامع.

    PYTHONPATH=src .venv-taaqol/bin/python scripts/build_tanween_report.py

**والكلمةُ الواحدةُ تُطبع حرفًا حرفًا.** لا تُطوى بحكم العدد: كلمةٌ
واحدةٌ شكلٌ خامسٌ حتى يُحكم فيها.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
import unicodedata
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import measure_tanween as MT  # noqa: E402
import measure_tanween_after as MA  # noqa: E402

PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
WORDS = ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv"
A1 = ROOT / "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv"


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def read(rel: str) -> dict:
    p = ROOT / rel
    if not p.is_file():
        raise Blocked(f"OWNER_ALERT: ABSENT — {rel}")
    return json.loads(p.read_text(encoding="utf-8"))


def vendor_gate() -> dict:
    def git(*a):
        return subprocess.run(["git", "-C", str(VENDOR), *a],
                              capture_output=True, text=True,
                              check=False).stdout.strip()
    head = git("rev-parse", "HEAD")
    dirty = [x for x in git("status", "--porcelain").splitlines() if x]
    return {"vendor_head": head, "porcelain_lines": len(dirty),
            "untouched": not dirty, "matches_pin": head == PIN}


def spell(word: str) -> list[dict]:
    """حرفًا حرفًا — بالنقطة والاسم، لا بالصورة وحدَها."""
    return [{"i": i, "char": ch, "codepoint": f"U+{ord(ch):04X}",
             "name": unicodedata.name(ch, "UNNAMED"),
             "is_mark": ch in MT.MARKS}
            for i, ch in enumerate(word)]


def pending() -> dict:
    with WORDS.open(encoding="utf-8", newline="") as fh:
        src = list(csv.DictReader(fh))
    norm = {MA.key(r): r for r in csv.DictReader(
        A1.open(encoding="utf-8", newline=""))}

    groups: dict[str, list] = {"P1": [], "P2": [], "P3": []}
    for r in src:
        b = MA.bucket_of(r["Word"])
        if not b.startswith("PENDING"):
            continue
        tag = b.split("_")[1]
        k = MA.key(r)
        c = MT.classify(r["Word"])
        groups[tag].append({
            "position": ":".join(k), "word": r["Word"],
            "rasm": c["rasm"], "kind": c["kind"], "shape": c["shape"],
            "tanween_position": c["position"],
            "normalized_now": (norm.get(k) or {}).get("Normalized_Word"),
        })

    p1 = {"id": "P1", "title": "همزةٌ بتنوين فتح",
          "count": len(groups["P1"]),
          "owner_note": "مثالا المالك مَاءً · دُعَاءً كلتاهما FATHATAN؛ "
                        "والحركةُ المكتوبةُ في البروميت ضمّةٌ والتنوينُ "
                        "فتح — والفرقُ لم يُفسَّر.",
          "measured_now": [x for x in groups["P1"]
                           if x["position"] in ("2:22:11", "2:171:11")],
          "first_five": groups["P1"][:5],
          "status": "OWNER_PENDING", "executed_rows": 0}
    p2 = {"id": "P2", "title": "تاءٌ مربوطةٌ مع الضمّ والكسر",
          "count": len(groups["P2"]),
          "owner_note": "الانقلابُ مصادَقٌ في الفتح وحدَه · ولا يُقاس عليه",
          "first_five": groups["P2"][:5],
          "status": "OWNER_PENDING", "executed_rows": 0}
    p3 = {"id": "P3", "title": "الكلمةُ الواحدة · ON_PENULT_FINAL_BARE",
          "count": len(groups["P3"]),
          "owner_note": "آليّةٌ ثالثةٌ لا الحذفُ ولا الانقلاب: تنوينُها "
                        "على ما قبلَ الأخير، والأخيرُ عارٍ.",
          "the_word": [{**x, "spelling": spell(x["word"])}
                       for x in groups["P3"]],
          "status": "OWNER_PENDING", "executed_rows": 0,
          "not_folded_by_count": "كلمةٌ واحدةٌ شكلٌ خامسٌ حتى يُحكم فيها"}
    return {"task": "PENDING_818", "P1": p1, "P2": p2, "P3": p3,
            "total": p1["count"] + p2["count"] + p3["count"],
            "executed_total": 0,
            "rule": "لا يُنفَّذ منها صفٌّ واحد ولو بدا حكمُه بيّنًا"}


def nazila() -> dict:
    sc = read("output/nazila_result/scores.json")
    with (ROOT / "output/nazila_result/records.csv").open(
            encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))[1:]
    return {"records": f"{len(rows)}×{len(rows[0])}",
            "record_cells": sum(len(r) for r in rows),
            "score": sc["CLOSURE_POTENTIAL"], "grounded": sc["GROUNDED"],
            "total": sc["CELLS_TOTAL"], "stages": sc["STAGES_OPENED"],
            "fingerprint": sc["content_fingerprint"]}


def render(before, after, dn, bb, pend, naz, gate, qq, q1, q2) -> str:
    a = after
    o = ["# `TANWEEN_UNFOLD_APPLY` — بسطُ التنوين، بجردٍ ثلاثيٍّ يقفل", "",
         "```text",
         f'NAZILA_RECORDS {naz["records"]} ({naz["record_cells"]} خانة) · '
         f'NAZILA_SCORE {naz["score"]}% ({naz["grounded"]}/{naz["total"]}) · '
         f'STAGES_OPENED {naz["stages"]}',
         f'VENDOR_HEAD {gate["vendor_head"]} · '
         f'porcelain {gate["porcelain_lines"]} · '
         f'MATCHES_PIN {str(gate["matches_pin"]).upper()}',
         "VENDOR_UNTOUCHED = TRUE · NO_COMMIT = TRUE · "
         "CLAIM_PROJECT_FINISHED = NO",
         "```", "",
         "## الجردُ الثلاثيُّ — بعدٍّ ثانٍ من المخرَج", "",
         "| الصنف | العدد | الحال |", "|---|---|---|",
         f'| **يتغيّر** | {a["changes_expected"]} | تعديلُ سلوك · '
         f'مقيسٌ متغيّرًا {a["rows_changed_measured"]} |',
         f'| **يُصادَق كما هو** | {a["ratified_unchanged"]} | '
         "`RATIFIED_UNCHANGED` — لا `MODIFIED` · تغيّر منها **صفر** |",
         f'| **موقوف** | {a["pending_total"]} | '
         f'{" · ".join(f"{k.split(chr(95))[1]} {v}" for k, v in a["pending_split"].items())}'
         " · نُفِّذ منها **صفر** |",
         f'| **المجموع** | **{a["three_way_sum"]}** | '
         f'والمنوَّنُ {a["tanweened_total"]} · يتامى {a["orphans"]} |', "",
         "**والفرقُ بين الأوّلَين جوهريّ.** الأوّلُ تعديلُ سلوك، والثاني "
         "مصادقةٌ على سلوكٍ قائمٍ لم يكن مصادَقًا. فلا يُجمعان في عدٍّ "
         "واحدٍ يُوهم عملًا لم يقع.", "",
         "## الآليّتان — متمايزتان في الشيفرة", "",
         "| الشكل | الإجراء | مثال |", "|---|---|---|"]
    for letter, act in sorted(MA.table_rows().items()):
        ex = {"ا": "مَرَضَاً ⟶ مَرَضَنْ", "ى": "هُدَىً ⟶ هُدَنْ",
              "ة": "بَعُوضَةً ⟶ بَعُوْضَتَنْ"}.get(letter, "")
        o.append(f'| `{letter}` | `{act}` | {ex} |')
    o += ["", "والفرقُ ظاهرٌ في العدد لا في الكلام: نقص الصامتُ في "
          f'{bb["B3"]["consonants_dropped_in"]} صفًّا وهي صفوفُ الحذف '
          f'({bb["B3"]["expected_drop_arithmetic"]})؛ '
          f'و{bb["B3"]["scope_split"].get("FATH×TAA_MARBUTA", 0)} صفَّ '
          "تاءٍ لم ينقص صامتُها لأنّها تنقلب ولا تُحذف.", "",
          "## أثرُ المحاور الثلاثة", "",
          "| المحور | عمودُ الحكم | تحرّك | أعمدةٌ تحرّكت |",
          "|---|---|---|---|"]
    for ax, d in dn.items():
        cm = d["columns_moved"]["moved_columns"]
        o.append(f'| `{ax}` | `{d["column"]}` | **{d["moved"]}** | '
                 f'{" · ".join(f"{k}={v}" for k, v in sorted(cm.items()))} |')
    o += ["", "**وعمودُ الحكم سكن، والبنيةُ تحته تحرّكت.** «تحرّك 0» على "
          "عمودٍ واحدٍ ليس خبرًا عن المحور — ولذلك يُمسَح كلُّ عمود.", "",
          "## `B3` — يُقاس ولا يُقال «أُغلق»", "", "```text",
          f'النطاق                {bb["B3"]["scope"]} صفًّا (الأشكالُ الثلاثة)',
          f'نقص الصامتُ في        {bb["B3"]["consonants_dropped_in"]} صفًّا · '
          f'مجموعُ الفرق {bb["B3"]["consonant_delta_total"]}',
          f'المشتقُّ المنتظَر      {bb["B3"]["expected_drop_arithmetic"]} · '
          f'يطابق {bb["B3"]["drop_matches_derivation"]}',
          f'خرج من ACCEPT         {bb["B3"]["left_accept"]}',
          f'CLOSED                {bb["B3"]["closed"]}',
          "```", "",
          f'**{bb["B3"]["what_moved"]}** '
          f'{bb["B3"]["closed_note"]}', "",
          "## الشاهدُ الإيجابيّ — `Reconstruction_Verified`", "", "```text",
          f'العمود                 {qq["column"]}',
          f'تحرّك                  {qq["rows_moved"]} من {qq["denominator"]}',
          f'والبنيةُ تحرّكت في      {qq["structure_moved"]}',
          f'القيمُ بعدُ             {qq["values_after"]}',
          "```", "",
          f'**{qq["reading"]}** {qq["why_it_is_positive_evidence"]}', "",
          "## `Q1` · `Q2` — مصدرُ عمودَين، مقروءًا من الشيفرة", "", "```text",
          f'Q1  {q1["question"]}',
          f'    {q1["answer"]}',
          f'    الوسمُ تحرّك في {q1["row_evidence"]["rows_where_ids_moved"]} '
          f'صفًّا · والصنفُ {q1["row_evidence"]["of_which_word_class_moved"]}'
          f' · والدورُ {q1["row_evidence"]["of_which_operator_role_moved"]}',
          f'Q2  {q2["question"]}',
          f'    {q2["answer"]}',
          f'    النطاق {q2["row_evidence"]["scope"]} · تحرّك '
          f'{q2["row_evidence"]["rows_moved"]}',
          "```", "",
          f'**{q1["resolution"]}** {q1["so_the_earlier_reading_is_corrected"]}',
          "", f'**{q2["resolution"]}**', "",
          "## `B2` — يُقاس ويُعرض", "", "```text",
          f'U_TANWEEN قبلُ  {bb["B2"]["u_tanween_words_before"]} كلمة',
          f'U_TANWEEN بعدُ  {bb["B2"]["u_tanween_words_after"]} كلمة  '
          f'({bb["B2"]["denominator"]})',
          f'VERDICT         {bb["B2"]["verdict"]}',
          f'STATUS          {bb["B2"]["status"]} · '
          f'decided_by_tool={bb["B2"]["decided_by_tool"]}',
          "```", "",
          f'{bb["B2"]["verdict_note"]} والصنفُ ما زال يُرفع في كلّ منوَّن: '
          "المصادقةُ في ثلاثة أشكالٍ لا تُخرج الصنفَ من أصناف القرار، "
          "لأنّ سياسةَ المحور الأوّل ما زالت تعدّه غيرَ مصادَق.", "",
          "## الموقوفُ — ثلاثةٌ تنتظر", "",
          "| # | العنوان | العدد | نُفِّذ |", "|---|---|---|---|"]
    for tag in ("P1", "P2", "P3"):
        x = pend[tag]
        o.append(f'| `{x["id"]}` | {x["title"]} | {x["count"]} | '
                 f'**{x["executed_rows"]}** |')
    w = pend["P3"]["the_word"][0] if pend["P3"]["the_word"] else None
    if w:
        o += ["", "### `P3` — الكلمةُ الواحدة، حرفًا حرفًا", "", "```text",
              f'الموضع    {w["position"]}',
              f'النصّ      {w["word"]}',
              f'الرسم      {w["rasm"]}',
              f'الموقع     {w["tanween_position"]}',
              f'المخرَجُ الآن {w["normalized_now"]}', ""]
        for c in w["spelling"]:
            o.append(f'  [{c["i"]:2}] {c["char"]}  {c["codepoint"]}  '
                     f'{"علامة" if c["is_mark"] else "حرف "}  {c["name"]}')
        o += ["```", "", pend["P3"]["not_folded_by_count"] + ".", ""]

    o += ["## الحرّاس", "", "| الحارس | المقام | النتيجة |", "|---|---|---|"]
    for g in after["guards"]:
        o.append(f'| `{g["guard"]}` | {g["denominator"]} | '
                 f'{"PASS" if g["passes"] else "FALLS"} |')

    rb = before["rollback_point"]
    o += ["", "## نقطةُ الرجوع", "", "```text",
          f'ملفّاتُ المحاور المبصومة  {len(rb["axis_outputs"])}',
          f'ملفّا المصدر              '
          f'{" · ".join(rb["source_files"])}',
          f'شرطُ الشجرة النظيفة       '
          f'{rb["clean_tree_precondition"]["measured"]} — '
          f'passes={rb["clean_tree_precondition"]["passes"]}',
          f'والرجوعُ                  '
          f'{rb["clean_tree_precondition"]["restore_command"]}',
          "```", "",
          "**والشرطُ لم يتحقّق حرفيًّا، ولم أُسقطه.** أُعيد الأمرُ بعد "
          "بلاغِ الوقف بصيغةِ `APPLY`، فمضيتُ بحكمِ إعادةِ الأمر لا "
          "بتأويلي: `waived_by = OWNER (re-issued as APPLY)`. ولا شيءَ من "
          "الأحدَ عشرَ تحت `src/`، والملفّان المتغيّران كانا نظيفَين في "
          "git ومتطابقَين بايتةً بايتة مع شجرتك.", "",
          "## بندٌ جديدٌ يُرفع", "", "```text",
          "POSITIONAL_ENTRY_ID   DW:n رقمٌ تسلسليٌّ يُسنَد بترتيب المرور",
          "                      (axis2_registry.py:205)، فتغيُّرُ سطحٍ",
          "                      واحدٍ يُعيد ترقيمَ ما بعده.",
          "المقيس                662 صفَّ «إِلَّا» تحرّك فيها Matched_Entry_Ids",
          "                      وحدَه (DW:37 ⟶ DW:36)، ولا عمودَ حكمٍ معها.",
          "القراءة               مُعرِّفٌ يُعيد تسميةَ نفسِه ليس مُعرِّفًا.",
          "الحال                 OWNER_PENDING — ولم يُطوَ بأنّه «وسمٌ فقط»",
          "```", "",
          "```text", "CLAIM_PROJECT_FINISHED = NO", "```", ""]
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/tanween")
    a = ap.parse_args()

    gate = vendor_gate()
    if not gate["untouched"] or not gate["matches_pin"]:
        raise Blocked(f"BLOCKED_AT_VENDOR: {gate}")

    before = read("output/tanween/00_before.json")
    after = read("output/tanween/02_after.json")
    dn = read("output/tanween/03_downstream.json")
    dn.pop("task", None)
    bb = read("output/tanween/04_b2_b3.json")
    pend = pending()
    naz = nazila()

    qz = json.loads((ROOT / "output/tanween/07_q1_q2.json").read_text(
        encoding="utf-8")) if (ROOT / "output/tanween/07_q1_q2.json").is_file() else {}
    if not qz:
        raise Blocked("OWNER_ALERT: Q1_Q2_NOT_MEASURED — شغّل "
                      "scripts/measure_q1_q2.py قبل الجامع")
    qq, q1, q2 = qz["reconstruction_witness"], qz["Q1"], qz["Q2"]
    doc = render(before, after, dn, bb, pend, naz, gate, qq, q1, q2)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "05_pending.json").write_text(
        json.dumps(pend, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "06_report.md").write_text(
        doc, encoding="utf-8")

    print(f'PENDING {pend["total"]} · نُفِّذ {pend["executed_total"]} · '
          f'P1 {pend["P1"]["count"]} · P2 {pend["P2"]["count"]} · '
          f'P3 {pend["P3"]["count"]}')
    if pend["P3"]["the_word"]:
        w = pend["P3"]["the_word"][0]
        print(f'   P3  {w["position"]}  {w["word"]}  ⟶  '
              f'{w["normalized_now"]}  ({len(w["spelling"])} محرفًا)')
    print(f'NAZILA {naz["records"]} · {naz["score"]}% · {naz["stages"]}')
    print(f"→ {out}/06_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
