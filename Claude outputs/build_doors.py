#!/usr/bin/env python3
"""الأبوابُ على ثلاثة محاور — لا يسقط بابٌ لأنّه لا يمسّ الأوّل  (`DOORS_REBUILD`).

    .venv-taaqol/bin/python scripts/build_doors.py --out output/doors

**العيبُ المقيس.** الجدولُ السابق حمل `cells` وحدَه، فسقط منه `C2` و`C3`
و`C4` — وثلاثتُها `cells = 0`. وقائمةٌ مرتَّبةٌ بأثر العلامة تُخفي عملًا لا
أثرَ له في العلامة وله أثرٌ في **الصحّة**. و`C2` أبلغُ مثال: المرحلةُ
الوحيدةُ المنفَّذة تصيب على المدخل المعيب وتخطئ على السليم، ولا يظهر ذلك
في `70.9%` ولا في `91.1%` بحال.

**وعيبٌ ثانٍ: المعيارُ كان مطبَّقًا على (ج) وحدَها.** `B2` و`B1` كلاهما
`cells = 0` ولم يسقطا. فلو كان العمودُ حاكمًا لسقطا معهما — وذلك تحيّزٌ في
البناء لا في النيّة، ونتيجتُه أنّ عيوبَ المصدر تُختصر بأثرها الرقميّ
وعيوبَ المالك لا تُختصر.

**ولا يُترك محورٌ فارغًا بشرطة.** الفراغُ يُسمّى: `NO_EFFECT_MEASURED` إن
قِيس فلم يظهر أثر، و`UNMEASURED` إن لم يُقس. والفرقُ بينهما هو الفرقُ بين
خبرٍ ودعوى.

**ولا يُغيّر هذا العملُ علامةً واحدة.** الأبوابُ توصيفٌ لمن يملك ماذا، لا
فتحٌ لبابٍ منها.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))
PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"

#: قيمُ المحور الفارغ — **مغلقة**. وشرطةٌ ليست منها.
EMPTY_AXIS = ("NO_EFFECT_MEASURED", "UNMEASURED")

#: أيُّ أسرةِ سببٍ يُغلقها أيُّ باب. ومنها يُشتقّ عمودُ `cells`.
DOOR_OF_FAMILY = {
    "NOT_EMITTED_BY_RUNNER": "C5",
    "NOT_CONSTRUCTED_IN_SOURCE": "C5",
    "NOT_OPENED": "C1",
}

#: بابٌ حُسم فيُشطب من الجدول ويُسجَّل في الذيل. والحكمُ للمالك لا للأداة.
RETIRED = {"B1": {"decided": "(أ) 1a7f8b76", "by": "DR_HUSSEIN",
                  "effect": "لم يعد بابًا — هويّةُ المدخل ثبتت"}}


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


def gate_vendor() -> dict:
    head = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    st = subprocess.run(["git", "-C", str(VENDOR), "status", "--porcelain"],
                        capture_output=True, text=True, check=False)
    return {"vendor_head": head.stdout.strip(),
            "porcelain_lines": len([x for x in st.stdout.splitlines() if x]),
            "passes": head.stdout.strip() == PIN and not st.stdout.strip()}


# ── المحور الأوّل · cells — مشتقٌّ من cells.csv ─────────────────────────
def cells_by_door(cells_csv: Path) -> dict:
    if not cells_csv.is_file():
        raise Blocked(f"OWNER_ALERT: CELLS_ABSENT — {cells_csv}")
    with cells_csv.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    per: Counter = Counter()
    for r in rows:
        if r["status"] != "NOT_AVAILABLE":
            continue
        door = DOOR_OF_FAMILY.get(r["reason_family"])
        if door:
            per[door] += 1
    return {"per_door": dict(per), "cells_total": len(rows),
            "grounded": sum(1 for r in rows if r["status"] == "FROM_CODE")}


# ── المحور الثالث · ceiling — مشتقٌّ من السجلّ ──────────────────────────
def ceiling_axis() -> dict:
    """أيُّ المراحل تُفتح بفتح كلّ باب — من السجلّ، لا من وصف."""
    from taaqqul_slot_geometry.runtime.native_stage_registry import (
        get_native_stage_registry,
    )
    specs = list(get_native_stage_registry())
    total = len(specs)
    impl = [s for s in specs if s.runtime_implemented]
    never = [getattr(s, "stage_id", None) or getattr(s, "name", None)
             for s in specs if not s.runtime_implemented]
    return {"stages_total": total, "implemented": len(impl),
            "not_implemented": never,
            "today": "1/16",
            "after_C1": f"{len(impl)}/{total}",
            "after_C4": "16/16",
            "note": ("C4 لا تُفتح بفتح C1: هي `runtime_implemented=False` "
                     "مثلها. فسقفُ فتح C1 هو أربعَ عشرةَ لا ستَّ عشرة.")}


# ── الأبواب ────────────────────────────────────────────────────────────
def build_doors(up: dict, cells: dict, ceil: dict) -> list[dict]:
    """كلُّ بندٍ من `03_upstream` يظهر بابًا، ويُقاس بالمحاور الثلاثة كلِّها."""
    m = {i["ident"]: i for i in up["items"]}
    per = cells["per_door"]
    tot = cells["cells_total"]
    c5 = per.get("C5", 0)
    c1 = per.get("C1", 0)

    def axis(v):
        """محورٌ لا يُترك شرطةً: قيمةٌ، أو اسمُ فراغه."""
        if v in (None, "", [], {}):
            raise Blocked("OWNER_ALERT: BLANK_AXIS — الفراغُ يُسمّى")
        return v

    doors = [
        {"door": "C5", "owner": "SONAISO",
         "title": m["C5"]["title"],
         "cells": axis(f"{c5}/{tot}"),
         "cells_denominator": "خاناتُ وثيقة النازلة",
         "correctness": axis(m["C5"]["measure"]["imports"]),
         "correctness_command": m["C5"]["measure"]["command"],
         "ceiling": axis("NO_EFFECT_MEASURED"),
         "ceiling_note": "الاستشارةُ لا تفتح مرحلةً — تملأ حقولًا",
         "cost": axis("تغييرٌ في بنية المشغّل — UNMEASURED كلفةً"),
         "location": m["C5"]["location"]},
        {"door": "C1", "owner": "SONAISO",
         "title": m["C1"]["title"],
         "cells": axis(f"{c1}/{tot}"),
         "cells_denominator": "خاناتُ وثيقة النازلة",
         "correctness": axis(
             {"stages_closed_per_token":
              m["C1"]["measure"]["stages_closed_per_token"]}),
         "correctness_command": m["C1"]["measure"]["command"],
         "ceiling": axis(f'{ceil["today"]} ⟶ {ceil["after_C1"]}'),
         "ceiling_note": ceil["note"],
         "cost": axis("سطرٌ في مرحلةٍ واحدة يفتح اثنتَي عشرة — "
                      "تقديرٌ من قراءة المصدر، لا قياس"),
         "location": m["C1"]["location"]},
        {"door": "C2", "owner": "SONAISO",
         "title": m["C2"]["title"],
         "cells": axis(f"0/{tot}"),
         "cells_denominator": "خاناتُ وثيقة النازلة",
         "correctness": axis(
             {"inventory_hit_unmarked":
              m["C2"]["measure"]["inventory_hit_unmarked"],
              "inventory_hit_marked":
              m["C2"]["measure"]["inventory_hit_marked"]}),
         "correctness_command": m["C2"]["measure"]["command"],
         "ceiling": axis("NO_EFFECT_MEASURED"),
         "ceiling_note": "التصنيفُ لا يفتح مرحلةً",
         "cost": axis("UNMEASURED"),
         "location": m["C2"]["location"],
         "why_it_was_dropped": ("cells = 0 — وأثرُه في الصحّة لا في العدد: "
                                "يصيب على المعيب ويخطئ على السليم")},
        {"door": "C3", "owner": "SONAISO",
         "title": m["C3"]["title"],
         "cells": axis(f"0/{tot}"),
         "cells_denominator": "خاناتُ وثيقة النازلة",
         "correctness": axis(
             {"corpus_words_matching":
              m["C3"]["measure"]["corpus_words_matching"],
              "corpus_words": m["C3"]["measure"]["corpus_words"],
              "percent": m["C3"]["measure"]["percent"],
              "crosses": m["C3"]["measure"]["crosses_queried"]}),
         "correctness_command": m["C3"]["measure"]["command"],
         "ceiling": axis("NO_EFFECT_MEASURED"),
         "ceiling_note": "القاعدةُ لا تفتح مرحلةً",
         "cost": axis("UNMEASURED"),
         "location": m["C3"]["location"],
         "also": "تنفيذُه في (ج) وحكمُه في (ب) — وهو B9"},
        {"door": "C4", "owner": "SONAISO",
         "title": m["C4"]["title"],
         "cells": axis(f"0/{tot}"),
         "cells_denominator": "خاناتُ وثيقة النازلة",
         "correctness": axis({"seals_issued":
                              m["C4"]["measure"]["seals_issued"]}),
         "correctness_command": m["C4"]["measure"]["command"],
         "ceiling": axis(f'{ceil["after_C1"]} ⟶ {ceil["after_C4"]}'),
         "ceiling_note": "لا تُفتح بفتح C1 — فهي runtime_implemented=False",
         "cost": axis("UNMEASURED"),
         "location": m["C4"]["location"],
         "not_a_request": True},
        {"door": "B2", "owner": "DR_HUSSEIN",
         "title": "أصنافُ البقيّة السبعة (T-4)",
         "cells": axis(f"0/{tot}"),
         "cells_denominator": "خاناتُ وثيقة النازلة",
         "correctness": axis(residual_classes()),
         "correctness_command": "python3 -m aslot compliance",
         "ceiling": axis("NO_EFFECT_MEASURED"),
         "ceiling_note": "لا يمسّ مراحلَ تعقُّل — يفتح T-5 في أسلوط",
         "cost": axis("سبعةُ قراراتٍ صغيرة — تقديرٌ من عدد الأصناف، لا قياس"),
         "location": None},
    ]
    for d in doors:
        for k in ("cells", "correctness", "ceiling", "cost"):
            v = d[k]
            if isinstance(v, str) and v.strip() in ("-", "—", ""):
                raise Blocked(f"OWNER_ALERT: BLANK_AXIS {d['door']}.{k}")
    return doors


def residual_classes() -> dict:
    p = ROOT / "reports/compliance/AXIS_9_MEASURES.json"
    if not p.is_file():
        return {"words_affected": "UNMEASURED",
                "reason": "AXIS_9_ABSENT — شغّل  aslot compliance"}
    d = json.loads(p.read_text(encoding="utf-8"))["residual_classes_unassigned"]
    return {"classes": len(d), "words_affected": sum(d.values()),
            "words_affected_denominator": "كلماتُ الجرد المتأثّرة",
            "by_class": d}


# ── الحرّاس ────────────────────────────────────────────────────────────
def guard(doors: list[dict], up: dict, cells: dict) -> dict:
    f: dict = {}
    names = {d["door"] for d in doors}
    upstream = {i["ident"] for i in up["items"] if i["ident"] != "C_PATH"}
    f["G_ALL_UPSTREAM_PRESENT"] = sorted(upstream - names)
    f["G_NO_AXIS_BLANK"] = [
        f'{d["door"]}.{k}' for d in doors for k in
        ("cells", "correctness", "ceiling", "cost")
        if d[k] in (None, "", "-", "—")]
    f["G_NO_BIAS"] = [
        d["door"] for d in doors
        if not all(d.get(k) is not None for k in
                   ("cells", "correctness", "ceiling", "cost"))]
    f["G_B1_RETIRED"] = ["B1"] if "B1" in names else []
    f["G_DOORS_DERIVED"] = [
        d["door"] for d in doors
        if not str(d["cells"]).endswith(f'/{cells["cells_total"]}')]
    return f


def recount(doc: str, doors: list[dict]) -> dict:
    body = doc.split("## الأبواب", 1)[-1].split("\n## ", 1)[0]
    rows = [ln for ln in body.splitlines()
            if ln.startswith("| `") and not ln.startswith("| `الباب")]
    return {"rows": len(rows), "doors": len(doors),
            "closes": len(rows) == len(doors)}


def fmt(v) -> str:
    if isinstance(v, dict):
        return " · ".join(f"{k}={v[k]}" for k in list(v)[:4])
    return str(v)


def render(doors: list[dict], cells: dict, ceil: dict, g: dict,
           gate: dict) -> str:
    o = ["# الأبواب — ثلاثةُ محاورَ لا واحد", "", "```text",
         'ما تملك الأداةُ إغلاقَه = 0',
         f'GROUNDED {cells["grounded"]}/{cells["cells_total"]} خانة · '
         f'STAGES_OPENED 1/16',
         f'VENDOR_HEAD = {gate["vendor_head"]} · '
         f'porcelain {gate["porcelain_lines"]}',
         "CLAIM_PROJECT_FINISHED = NO", "```", "",
         "**ولا يُغيّر هذا الجدولُ علامةً واحدة.** الأبوابُ توصيفٌ لمن يملك "
         "ماذا، لا فتحٌ لبابٍ منها.", "",
         "## الأبواب", "",
         "| الباب | المالك | cells | correctness | ceiling | cost |",
         "|---|---|---|---|---|---|"]
    for d in doors:
        o.append(f'| `{d["door"]}` | {d["owner"]} | `{d["cells"]}` | '
                 f'{fmt(d["correctness"])} | `{d["ceiling"]}` | '
                 f'{d["cost"]} |')
    o.append("")
    for d in doors:
        o += [f'### `{d["door"]}` · {d["title"]}', ""]
        if d.get("location"):
            L = d["location"]
            o.append(f'**الموضع**: `{L["file"]}:{L["line"]}`')
        if d.get("why_it_was_dropped"):
            o.append(f'**لماذا سقط من الجدول السابق**: {d["why_it_was_dropped"]}')
        o += ["", "```json",
              json.dumps({k: d[k] for k in
                          ("cells", "cells_denominator", "correctness",
                           "correctness_command", "ceiling", "ceiling_note",
                           "cost")},
                         ensure_ascii=False, indent=1), "```", ""]
    o += ["## الحرّاس", "", "| الحارس | مخالفات |", "|---|---|"]
    for k, v in g.items():
        o.append(f'| `{k}` | `{v if v else "لا شيء"}` |')
    o += ["", "## ذيلٌ — بابٌ حُسم فشُطب", ""]
    for k, v in RETIRED.items():
        o.append(f'* `{k}` — حُسم `{v["decided"]}` بحكم {v["by"]}. '
                 f'{v["effect"]}')
    return "\n".join(o) + "\n"


def upstream_report(doors: list[dict]) -> str:
    o = ["# بلاغُ ج-٢ — مصوغٌ وغيرُ مرسَل", "", "```text",
         "RECIPIENT = sonaiso/Taaqol-GPT",
         "SENT = NO", "AUTHORITY_TO_SEND = OWNER",
         f"VENDOR_PIN = {PIN}", "```", "",
         "لا يُقترح إصلاحٌ بعينه: يُعرض العيبُ وقياسُه، والحلُّ لصاحب "
         "المستودع. و`C4` ليست في هذا البلاغ — هي إعلانُ حدٍّ لا طلبُ "
         "تغيير.", ""]
    for d in doors:
        if d["door"] not in ("C1", "C2", "C3", "C5"):
            continue
        L = d.get("location")
        o += [f'## {d["door"]} · {d["title"]}', ""]
        if L:
            o.append(f'**الموضع**: `{L["file"]}:{L["line"]}` — `{L["text"]}`')
        o += ["", f'**القياس** (`{d["correctness_command"]}`):', "", "```json",
              json.dumps(d["correctness"], ensure_ascii=False, indent=1),
              "```", "",
              "**ما لا يُدَّعى**: لم يُقترح تغييرٌ بعينه، ولم يُقس أثرُ أيّ "
              "إصلاحٍ على بقيّة المشغّل.", ""]
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--upstream", default="output/upstream/00_upstream.json")
    ap.add_argument("--cells", default="output/nazila_result/cells.csv")
    ap.add_argument("--out", default="output/doors")
    a = ap.parse_args()

    gate = gate_vendor()
    if not gate["passes"]:
        print(f"BLOCKED_AT_VENDOR: {json.dumps(gate, ensure_ascii=False)}")
        return 2
    up_p = ROOT / a.upstream
    if not up_p.is_file():
        print(f"OWNER_ALERT: UPSTREAM_ABSENT — {up_p}. "
              "شغّل scripts/build_upstream.py أوّلًا: الأبوابُ تُشتقّ منه.")
        return 3
    up = json.loads(up_p.read_text(encoding="utf-8"))

    cells = cells_by_door(ROOT / a.cells)
    ceil = ceiling_axis()
    doors = build_doors(up, cells, ceil)
    g = guard(doors, up, cells)
    hard = {k: v for k, v in g.items() if v}
    if hard:
        print("OWNER_ALERT: " + json.dumps(hard, ensure_ascii=False))
        return 4

    doc = render(doors, cells, ceil, g, gate)
    rc = recount(doc, doors)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "00_doors.json").write_text(json.dumps(
        {"gate": gate, "cells": cells, "ceiling": ceil, "doors": doors,
         "retired": RETIRED}, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "01_doors.md").write_text(doc, encoding="utf-8")
    (out / "upstream_report.md").write_text(upstream_report(doors),
                                            encoding="utf-8")
    (out / "02_ledger.json").write_text(json.dumps(
        {"doors": [{"door": d["door"], "owner": d["owner"]} for d in doors],
         "by_owner": dict(Counter(d["owner"] for d in doors)),
         "guards": g, "recount_from_report": rc,
         "retired": RETIRED, "SENT": "NO"},
        ensure_ascii=False, indent=1), encoding="utf-8")

    print(f'DOORS      {len(doors)} · ' +
          " · ".join(f'{d["door"]}({d["cells"]})' for d in doors))
    for k, v in g.items():
        print(f'  {k:26} {v if v else "PASS"}')
    print(f'RECOUNT    {rc["rows"]}/{rc["doors"]} يقفل {rc["closes"]}')
    print(f'RETIRED    {list(RETIRED)}  ·  SENT NO')
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
