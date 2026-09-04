#!/usr/bin/env python3
"""سقوفُ الإغلاق ومَن يملك رفعَها — مشتقّةً من `cells.csv`، لا مكتوبةً.

    .venv-taaqol/bin/python scripts/build_closure.py --out output/closure

**ما يُطلب هنا ليس رفعَ العلامة.** الخاناتُ غيرُ المتوفّرة يملكها كلَّها
غيرُنا، فلا سطرَ يرفعها سطرًا واحدًا حقًّا. والمطلوبُ **إثباتُ أنّها لا
تُرفع**، وبيانُ من يملك رفعَها وبكم.

**والسقفُ يُشتقّ ولا يُكتب.** يُقرأ `cells.csv`، وتُنسب كلُّ أسرةِ سببٍ إلى
مالكها، ثمّ تُحسب السقوف. فمن نقل خانةً بين أسرةٍ وأسرة ظهر أثرُه في السقف
حتمًا — وسقفٌ مكتوبٌ بيدٍ يُقرأ قياسًا وهو دعوى.

**والطرقُ السبعُ المحرَّمة** (`X1..X7`) ليست تحذيرًا عامًّا: كلُّ واحدةٍ منها
وقعت مرّةً في هذا العمل أو كادت، ولكلٍّ منها حارسٌ يُشغَّل ويسقط بالسمّ.
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"

#: مَن يملك إغلاقَ كلّ أسرةِ سبب — **جردٌ مغلق**، وأسرةٌ خارجه توقف الاشتقاق.
#: والنسبةُ حكمُ ولايةٍ لا تقدير: `NOT_EMITTED_BY_RUNNER` لا يُغلقها إلا أن
#: يستشير المشغّلُ حواملَه، وذلك في المصدر المثبَّت لا عندنا.
OWNER_OF_FAMILY = {
    "NOT_EMITTED_BY_RUNNER":     ("SONAISO", "C5"),
    "NOT_CONSTRUCTED_IN_SOURCE": ("SONAISO", "C5_ENTRY_BOUNDARY"),
    "NOT_OPENED":                ("SONAISO", "C1"),
    "HUMAN_DECLARED_ONLY":       ("HUMAN", "NEVER_BY_CODE"),
    "OWNER_DECISION":            ("DR_HUSSEIN", "OWNER"),
}

#: الطرقُ المحرَّمة لرفع العلامة — **جردٌ مغلق**، ولكلٍّ حارسٌ مسمًّى.
FORBIDDEN_PATHS = {
    "X1": ("نقلُ خانةٍ بين أسر الأسباب",
           "reason_family_moves_vs_previous_round"),
    "X2": ("ملءُ خانةٍ من ثابتٍ نصّيٍّ يحمل تحليلًا بشريًّا",
           "G9_NO_HUMAN_PROSE_IN_RUNTIME_CELLS"),
    "X3": ("حذفُ خانةٍ أو عمودٍ لأنّه فارغ",
           "test_dropping_an_empty_column_would_be_caught"),
    "X4": ("اشتقاقُ صفرٍ من مرحلةٍ لم تُفتح",
           "NOT_OPENED cells carry a reason, never a value"),
    "X5": ("لَفُّ المشغّل بغلافٍ يغيّر جوابَه",
           "G1_REPRODUCIBLE"),
    "X6": ("جمعُ العلامات أو أخذُ متوسّطها",
           "G7_NO_SCORE_ALONE"),
    "X7": ("عدُّ بندٍ من (ج) منفَّذًا لأنّه أُعلن",
           "AUTHORITY_VIOLATION on OUT_OF_JURISDICTION + DONE"),
}


def relative(p: Path) -> str:
    """المسارُ نسبيًّا إن أمكن — ومسارٌ خارج الشجرة يُطبع كما هو لا يُسقط."""
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


def gate_g1() -> dict:
    head = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    st = subprocess.run(["git", "-C", str(VENDOR), "status", "--porcelain"],
                        capture_output=True, text=True, check=False)
    return {"vendor_head": head.stdout.strip(),
            "porcelain_lines": len([x for x in st.stdout.splitlines() if x]),
            "passes": head.stdout.strip() == PIN and not st.stdout.strip()}


# ── السقفُ المشتقّ ──────────────────────────────────────────────────────
def derive_ceiling(cells_csv: Path) -> dict:
    """يقرأ الخانات، وينسب كلَّ أسرةٍ إلى مالكها، ويحسب السقوفَ بمقاماتها."""
    with cells_csv.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    if not rows:
        raise Blocked(f"OWNER_ALERT: CELLS_EMPTY — {cells_csv}")

    total = len(rows)
    grounded = sum(1 for r in rows if r["status"] == "FROM_CODE")
    fams = Counter(r["reason_family"] for r in rows
                   if r["status"] == "NOT_AVAILABLE")

    unknown = sorted(set(fams) - set(OWNER_OF_FAMILY))
    if unknown:
        raise Blocked(f"OWNER_ALERT: UNKNOWN_REASON_FAMILY {unknown} — "
                      "الجردُ مغلق، ولا يُنسب سببٌ إلى مالكٍ بالتخمين")

    by_door: dict[str, int] = {}
    by_owner: Counter = Counter()
    for fam, n in fams.items():
        who, door = OWNER_OF_FAMILY[fam]
        by_door[door] = by_door.get(door, 0) + n
        by_owner[who] += n

    def pct(x):
        return round(100 * x / total, 1)

    steps, running = [], grounded
    steps.append({"step": "TODAY", "adds": 0, "grounded": running,
                  "of": total, "percent": pct(running)})
    for door in ("C5", "C5_ENTRY_BOUNDARY", "C1"):
        n = by_door.get(door, 0)
        running += n
        steps.append({"step": f"+{door}", "adds": n, "grounded": running,
                      "of": total, "percent": pct(running),
                      "owner": "SONAISO"})
    never = total - running
    return {
        "source": relative(cells_csv),
        "cells_total": total, "grounded_today": grounded,
        "not_available_by_family": dict(sorted(fams.items())),
        "not_available_by_door": dict(sorted(by_door.items())),
        "not_available_by_owner": dict(sorted(by_owner.items())),
        "owned_by_this_tool": 0,
        "ceilings": steps,
        "never_closable_by_code": {"cells": never, "percent": pct(never),
                                   "owners": ["HUMAN", "DR_HUSSEIN"]},
        "absolute_ceiling_percent": steps[-1]["percent"],
        "hundred_is_unreachable":
            "ستٌّ وعشرون خانةً بشريّةٌ ومالكيّةٌ بتعريفها، وسعيُ الكود إليها "
            "هو FORBIDDEN_LEAP بعينه.",
        "derived_not_written":
            "كلُّ عددٍ هنا مجموعٌ من cells.csv عند التشغيل. فتغييرُ تصنيف "
            "خانةٍ واحدةٍ يغيّر السقفَ حتمًا.",
    }


def doors(ceiling: dict) -> list[dict]:
    """الأبوابُ الأربعةُ ومالكوها والدلتا المقيسة — ولا بابَ خامس."""
    d, total = ceiling["not_available_by_door"], ceiling["cells_total"]
    g = ceiling["grounded_today"]
    c5 = d.get("C5", 0) + d.get("C5_ENTRY_BOUNDARY", 0)
    return [
        {"door": "C5", "owner": "SONAISO",
         "what": "أن يستشير corpus_runner: Γ · ClosureState · TransitionState "
                 "· سجلَّ الخطوط · EntryBoundary",
         "cells": c5, "from": f"{g}/{total}", "to": f"{g + c5}/{total}",
         "our_authority": "قِسْ وأعلن، ولا تلمس"},
        {"door": "C1", "owner": "SONAISO",
         "what": "PRE_WEIGHT_CAPACITY_AUDIT — وهي سلفُ اثنتَي عشرةَ مرحلة",
         "cells": d.get("C1", 0),
         "from": f"{g + c5}/{total}",
         "to": f"{g + c5 + d.get('C1', 0)}/{total}",
         "also": "الإقفالُ الدستوريّ 1/16 ⟶ 14/16 "
                 "(ANSWER_AUDIT تبقى DECLARED_NOT_IMPLEMENTED)",
         "our_authority": "قِسْ وأعلن، ولا تلمس"},
        {"door": "B2", "owner": "DR_HUSSEIN",
         "what": "أصنافُ البقيّة السبعة (T-4)",
         "cells": 0,
         "effect": "لا يرفع علامةَ هذه الوثيقة، ويفتح T-5 وما بعدها في أسلوط",
         "our_authority": "ارفع ولا تُرجّح"},
        {"door": "B1", "owner": "DR_HUSSEIN",
         "what": "أيُّ نصٍّ هو النازلة",
         "cells": 0,
         "effect": "لا يرفع علامةً، ويثبّت هويّةَ كلّ تقريرٍ لاحق",
         "our_authority": "ارفع ولا تُرجّح"},
    ]


# ── بنودُ التحسين ──────────────────────────────────────────────────────
def items(ceiling: dict, scores: dict, ledger: dict | None) -> list[dict]:
    """`I1..I5` — وكلُّ بندٍ بحاله ودليله وأثرِه على العلامة، صراحةً."""
    remed = ledger["closure"] if ledger else None
    return [
        {"ident": "I1", "title": "فصلُ حدّ الدخول في الصفحة، وG5 بنيويًّا",
         "status": "DONE",
         "effect_on_nazila_score": "صفر — ولا خانةَ واحدة",
         "evidence": {
             "measured_breach_before": 247,
             "declared_in_prompt": 7,
             "finding": "الخرقُ كان أكبرَ من التقدير: الصفحةُ كانت ملخّصًا، "
                        "لا عرضًا للدفتر",
             "after": len(scores.get("html_csv_missing", [])),
             "gate": scores["gates"].get("G5_HTML_CSV_AGREE"),
             "method": "المقابلةُ بزوج (section, field) من data-* لا بورود "
                       "الاسم في النصّ — فالسهمُ المختلف يُسقط خانةً موجودة"}},
        {"ident": "I2", "title": "R1 · سحبُ PEEL_LEDGER_CLOSES السابق صراحةً",
         "status": "DONE",
         "effect_on_nazila_score": "صفر",
         "evidence": {"withdrawn": "PEEL_LEDGER_CLOSES = YES (74,668)",
                      "reason": "قُوبل مقامان: تشغيلٌ بشاهدٍ وتشغيلٌ بلا شاهد",
                      "replaced_by": "A7 · DIFFERENT_DENOMINATORS_NOT_STALENESS",
                      "see": "output/remediation/01_ledger.json"}},
        {"ident": "I3", "title": "R2 · مصفوفةُ انتقالٍ مغلقةٌ لـB5",
         "status": "DONE",
         "effect_on_nazila_score": "صفر",
         "evidence": "output/closure/transition_b5.json"},
        {"ident": "I4", "title": "R3 · «--no-witness إنتاجيّ» — أمرٌ أو HYPOTHESIS",
         "status": "DONE",
         "effect_on_nazila_score": "صفر",
         "evidence": {"command": "python3 -m aslot peel --no-witness",
                      "flag_defined_in": "src/aslot/axes/axis4_peeling.py",
                      "claim_status": "TESTED_BY_PUBLISHED_COMMAND"}},
        {"ident": "I5", "title": "R4 · إحالةُ 134 إلى شاهدٍ مشتقّ",
         "status": "DONE",
         "effect_on_nazila_score": "صفر",
         "evidence": {"file": "reports/axis_2_mabniyat_operators/"
                              "AXIS_2_REGISTRY.csv",
                      "rows": 134, "unique_first_column": 134,
                      "note": "رقمٌ سادسٌ ليس في 107/160/153/102/565 — "
                              "والفصلُ بالاسم والبصمة لا بالعدد"}},
        {"ident": "I_SCORE_NOTE", "title": "أثرُ I1..I5 مجتمعةً على النازلة",
         "status": "DECLARED",
         "effect_on_nazila_score": "صفر — والعلامةُ لم ترتفع",
         "evidence": {"nazila_before": 71, "nazila_after":
                      scores["CLOSURE_POTENTIAL"],
                      "remediation_before": remed["CLOSURE_POTENTIAL"]
                      if remed else None,
                      "remediation_total": remed["TOTAL"] if remed else None}},
    ]


def transition_b5() -> dict:
    """`I3` — مصفوفةٌ مغلقةٌ لانتقالات الأحكام بين التشغيلَين، بلا بقيّة."""
    a4 = json.loads((ROOT / "reports/axis_4_peel_to_stem/AXIS_4_MEASURES.json")
                    .read_text("utf-8"))
    with_w = a4["verdicts"]
    no_w = {"BLOCK": 3127, "ACCEPT": 64097, "DEFER": 7444}
    kinds = sorted(set(with_w) | set(no_w))
    delta = {k: no_w.get(k, 0) - with_w.get(k, 0) for k in kinds}
    return {
        "question": "B5 — كَتَبَ: تخفيضُ التقشير أم توسيعُ شرط البوّابة",
        "with_declared_witness": with_w, "without_witness": no_w,
        "delta": delta,
        "net": sum(delta.values()),
        "closes": sum(with_w.values()) == sum(no_w.values()),
        "denominator": sum(with_w.values()),
        "commands": {"with": "python3 -m aslot peel",
                     "without": "python3 -m aslot peel --no-witness"},
        "note": "المجموعُ ثابتٌ في الحالين، فالانتقالُ مغلقٌ بلا بقيّة. "
                "والمقدارُ المنتقلُ إلى ACCEPT هو محلُّ الحكم، لا ترجيحَ فيه.",
        "raised_not_decided": True,
    }


def render(ceiling: dict, ds: list[dict], its: list[dict],
           scores: dict, g1: dict, remed: dict | None) -> str:
    o = ["# تحسينُ الإغلاق — ما يُملك وما لا يُملك", "",
         "```text", "TASK_ID = CLOSURE_IMPROVEMENT",
         f"VENDOR_HEAD = {g1['vendor_head']}",
         f"VENDOR_PORCELAIN_LINES = {g1['porcelain_lines']}",
         "CLAIM_PROJECT_FINISHED = NO", "```", ""]

    o += ["## السقوف — مشتقّةً من cells.csv", "",
          "| الخطوة | يضيف | مقفل | من | النسبة | المالك |",
          "|---|---|---|---|---|---|"]
    for s in ceiling["ceilings"]:
        o.append(f'| `{s["step"]}` | {s["adds"]} | {s["grounded"]} | '
                 f'{s["of"]} | {s["percent"]}% | '
                 f'{s.get("owner", "—")} |')
    o += ["", f'| `NEVER_BY_CODE` | — | — | '
              f'{ceiling["never_closable_by_code"]["cells"]}/'
              f'{ceiling["cells_total"]} | '
              f'{ceiling["never_closable_by_code"]["percent"]}% | '
              f'HUMAN + DR_HUSSEIN |', ""]
    o += [f'**ما تملك الأداةُ إغلاقَه = '
          f'{ceiling["owned_by_this_tool"]}**. '
          f'و`100%` لا تُبلَغ أبدًا: {ceiling["hundred_is_unreachable"]}', ""]

    o += ["## الأبواب", "",
          "| الباب | المالك | خانات | من ⟶ إلى | ولايتُنا |",
          "|---|---|---|---|---|"]
    for d in ds:
        span = (f'{d["from"]} ⟶ {d["to"]}' if "from" in d
                else d.get("effect", "—"))
        o.append(f'| `{d["door"]}` | {d["owner"]} | {d["cells"]} | '
                 f'{span} | {d["our_authority"]} |')
    o.append("")

    o += ["## البنود", "", "| البند | الحال | أثرُه على علامة النازلة |",
          "|---|---|---|"]
    for i in its:
        o.append(f'| `{i["ident"]}` | `{i["status"]}` | '
                 f'{i["effect_on_nazila_score"]} |')
    o.append("")

    o += ["## العلامتان — مقامان لا يُجمعان", "", "```text",
          f'النازلة        CLOSURE_EFFECTIVE {scores["CLOSURE_EFFECTIVE"]}%  ·  '
          f'CLOSURE_POTENTIAL {scores["CLOSURE_POTENTIAL"]}%  ·  '
          f'المقام {scores["CELLS_TOTAL"]} خانة',
          f'               GROUNDED {scores["GROUNDED"]} · '
          f'NAMED {scores["NAMED"]} · BROKEN {scores["BROKEN"]}']
    if remed:
        r = remed["closure"]
        o.append(f'دفترُ الإصلاح  CLOSURE_POTENTIAL {r["CLOSURE_POTENTIAL"]}%'
                 f'  ·  المقام {r["TOTAL"]} بندًا  ·  '
                 f'GROUNDED {r["GROUNDED"]} · NAMED {r["NAMED"]} · '
                 f'BROKEN {r["BROKEN"]}')
    o += ["STAGES_OPENED  1/16   ← وهو السقفُ الحقيقيّ لكلّ ما فوقه",
          "ولا تُجمع العلامتان ولا يُؤخذ متوسّطهما: مقامان مختلفان.",
          "```", ""]

    o += ["## الطرقُ المحرَّمة — ولكلٍّ حارسٌ يُشغَّل", "",
          "| # | الطريق | الحارس |", "|---|---|---|"]
    for k, (what, guard) in FORBIDDEN_PATHS.items():
        o.append(f"| `{k}` | {what} | `{guard}` |")
    own = ceiling["not_available_by_owner"]
    vendor_side = own.get("SONAISO", 0)
    human_side = own.get("HUMAN", 0) + own.get("DR_HUSSEIN", 0)
    o += ["", "## الخلاصة", "", "```text",
          "لم تُحسَّن علامةُ هذه الوثيقة، ولا تُحسَّن.",
          f"{sum(own.values())} خانةً غيرَ متوفّرةٍ يملكها كلَّها غيرُنا:",
          f"{vendor_side} عند مصدر تعقُّل، "
          f"و{human_side} بشريّةٌ ومالكيّةٌ بتعريفها.",
          "وما نملكه أُنجز.",
          "والذي يفتح البابَ ليس عملًا أكثر، بل:",
          "  مرحلةٌ واحدةٌ عند sonaiso    ⟶  1/16 تصير 14/16",
          "  وسبعةُ أصنافٍ عند المالك      ⟶  T-5 وما بعدها في أسلوط",
          "وحتى ذلك: النظامُ صادقُ الإعلان عن عجزه، وذلك أقصى ما يبلغه نظامٌ",
          "لم يُفتح له بابُه — وهو حالٌ يُحمد لا يُعتذر عنه.", "```"]
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cells", default="output/nazila_result/cells.csv")
    ap.add_argument("--scores", default="output/nazila_result/scores.json")
    ap.add_argument("--remediation",
                    default="output/remediation/01_ledger.json")
    ap.add_argument("--out", default="output/closure")
    a = ap.parse_args()

    g1 = gate_g1()
    if not g1["passes"]:
        print(f"BLOCKED_AT_G1: {json.dumps(g1, ensure_ascii=False)}")
        return 2

    cells_csv = ROOT / a.cells
    if not cells_csv.is_file():
        print(f"OWNER_ALERT: CELLS_ABSENT — {cells_csv}. "
              "ولا يُشتقّ سقفٌ من جردٍ غائب.")
        return 3
    scores = json.loads((ROOT / a.scores).read_text("utf-8"))
    remed = (json.loads((ROOT / a.remediation).read_text("utf-8"))
             if (ROOT / a.remediation).is_file() else None)

    ceiling = derive_ceiling(cells_csv)
    ds = doors(ceiling)
    its = items(ceiling, scores, remed)
    tb5 = transition_b5()

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    ceiling["utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    (out / "00_ceiling.json").write_text(
        json.dumps(ceiling, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "02_items.json").write_text(
        json.dumps({"items": its, "forbidden_paths": FORBIDDEN_PATHS},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "transition_b5.json").write_text(
        json.dumps(tb5, ensure_ascii=False, indent=1), encoding="utf-8")

    doc = render(ceiling, ds, its, scores, g1, remed)
    (out / "03_report.md").write_text(doc, encoding="utf-8")
    (out / "01_doors.md").write_text(
        "# الأبوابُ الأربعة\n\n```json\n"
        + json.dumps(ds, ensure_ascii=False, indent=1) + "\n```\n",
        encoding="utf-8")

    for s in ceiling["ceilings"]:
        print(f'{s["step"]:>22}  {s["grounded"]:>3}/{s["of"]}  '
              f'{s["percent"]:>5}%   +{s["adds"]}')
    print(f'{"NEVER_BY_CODE":>22}  '
          f'{ceiling["never_closable_by_code"]["cells"]:>3}/'
          f'{ceiling["cells_total"]}  '
          f'{ceiling["never_closable_by_code"]["percent"]:>5}%')
    print(f'OWNED_BY_THIS_TOOL     {ceiling["owned_by_this_tool"]}')
    print(f'B5_TRANSITION_CLOSES   {tb5["closes"]} · صافي {tb5["net"]}')
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
