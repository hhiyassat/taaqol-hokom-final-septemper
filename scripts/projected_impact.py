#!/usr/bin/env python3
"""`T5.3` — أثرُ الإسناد قبل وقوعه: مصفوفةُ انتقالٍ لكلّ سيناريو.

    .venv-taaqol/bin/python scripts/projected_impact.py

**ولا إسنادَ هنا.** الأصنافُ السبعةُ تُعرَض على الأربعةِ القابلةِ للإسناد
عرضًا، ويُقاس أثرُ كلٍّ منها. وأيُّها يُختار حكمُ المالك — `B2` —
و`P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED`.

**والسقفُ يُستفتى حيًّا** من `ResidualPolicy.rank_cap`، لا يُكتب. والأعدادُ
تُقرأ من `output/max/01_b2_measures.json` المقيس، لا تُقدَّر.

**ومقامان لا مقام**: «كلماتٌ تحمل الصنف» و«أحكامُ المحور الرابع عليها».
والصنفُ الواحد يظهر في المحورَين بعددَين قد يتساويان وقد لا — وتساويهما
لا يجعلهما مجموعةً واحدة (`EQUAL_NUMBERS_MAY_BE_DIFFERENT_SETS`).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))

from taaqqul_slot_geometry import ResidualKind, ResidualPolicy  # noqa: E402

MEASURES = ROOT / "output" / "max" / "01_b2_measures.json"
ASSIGN = ROOT / "data" / "residual_kind_assignment.json"
ASSIGNABLE = ("BLOCKING", "DEFERRABLE", "NON_BLOCKING", "EXPLANATORY")

#: ما تصير إليه رتبةُ المخرَج تحت كلِّ سقف. والسقفُ يُستفتى، وهذا هو
#: **قراءتُه** لا اختراعُه: `ZERO` يصفّر، و`HYPOTHESIS` يقف عند فرضيّة،
#: و`CERTIFICATE` لا يخفض شيئًا فوقه.
READING = {
    "ZERO": ("يُصفَّر", "لا حكمَ يخرج من كلمةٍ تحمل هذا الصنف"),
    "HYPOTHESIS": ("يقف عند فرضيّة", "ACCEPT لا يبقى ACCEPT — يصير فرضيّة"),
    "CERTIFICATE": ("لا يُخفَض", "الصنفُ لا يمسّ الرتبةَ ألبتّة"),
}


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def ceilings() -> dict:
    return {k.name: ResidualPolicy.rank_cap(k).name for k in ResidualKind}


def load() -> dict:
    if not MEASURES.is_file():
        raise Blocked(f"OWNER_ALERT: MEASURES_ABSENT — {MEASURES}")
    return json.loads(MEASURES.read_text(encoding="utf-8"))


def scenarios(m: dict, caps: dict) -> list[dict]:
    per = m["M2_reach"]["per_class"]
    out = []
    for cls, d in per.items():
        a4 = d.get("axis4_verdicts") or {}
        accepts = a4.get("ACCEPT", 0)
        defers = a4.get("DEFER", 0)
        blocks = a4.get("BLOCK", 0)
        for kind in ASSIGNABLE:
            cap = caps[kind]
            word, gloss = READING[cap]
            if cap == "ZERO":
                after = {"ACCEPT": 0, "DEFER": 0,
                         "BLOCK": accepts + defers + blocks}
                moved = accepts + defers
            elif cap == "HYPOTHESIS":
                after = {"ACCEPT": 0, "DEFER": defers + accepts,
                         "BLOCK": blocks}
                moved = accepts
            else:
                after = {"ACCEPT": accepts, "DEFER": defers, "BLOCK": blocks}
                moved = 0
            out.append({
                "class": cls, "kind": kind, "rank_cap": cap,
                "reading": word, "gloss": gloss,
                "members": d.get("members"),
                "before": {"ACCEPT": accepts, "DEFER": defers,
                           "BLOCK": blocks},
                "after": after,
                "verdicts_that_move": moved,
                "denominator": "أحكامُ المحور الرابع على كلمات هذا الصنف",
            })
    return out


def guards(rows: list[dict], caps: dict, m: dict) -> list[dict]:
    g = []

    assign = json.loads(ASSIGN.read_text(encoding="utf-8"))["assignments"]
    chosen = sorted(k for k, v in assign.items() if v is not None)
    g.append({"guard": "G_NO_ASSIGNMENT", "denominator": len(assign),
              "chosen": chosen, "passes": not chosen,
              "note": "إسنادٌ واحدٌ مملوءٌ من عندي نقضٌ لـ P4."})

    live = ceilings()
    off = sorted(k for k in caps if caps[k] != live.get(k))
    g.append({"guard": "G_CEILING_IS_LIVE", "denominator": len(caps),
              "drifted": off, "passes": not off,
              "note": "السقفُ يُستفتى في كلّ تشغيل، ولا يُخزَّن."})

    per = m["M2_reach"]["per_class"]
    bad = sorted(r["class"] for r in rows
                 if sum(r["before"].values()) != sum(r["after"].values()))
    g.append({"guard": "G_TOTALS_PRESERVED", "denominator": len(rows),
              "broken": sorted(set(bad)), "passes": not bad,
              "note": "الانتقالُ ينقل ولا يخلق: مجموعُ قبلُ = مجموعُ بعدُ."})

    missing = sorted(set(per) - {r["class"] for r in rows})
    g.append({"guard": "G_EVERY_CLASS_PROJECTED",
              "denominator": len(per), "missing": missing,
              "passes": not missing})
    return g


def render(rows: list[dict], caps: dict, g: list[dict], m: dict) -> str:
    o = ["# `T5.3` — أثرُ الإسناد قبل وقوعه", "", "```text",
         "TASK_ID = MAX_EXECUTABLE · T5.3",
         "P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED = TRUE",
         "ASSIGNMENTS_FILLED = 0/7   ←  الاختيارُ حكمُ المالك (B2)",
         "SHADOW_ONLY = TRUE   ←  لا يدخل هذا المخرَجُ قرارًا في أسلوط",
         "```", "",
         "## السقوفُ — مستفتاةً حيًّا", "",
         "| الصنفُ الدستوريّ | السقف | قراءتُه | يُسنَد؟ |", "|---|---|---|---|"]
    for k, cap in caps.items():
        word, gloss = READING[cap]
        yes = "نعم" if k in ASSIGNABLE else "**لا** — يُكتشف ولا يُختار"
        o.append(f"| `{k}` | `{cap}` | {word} — {gloss} | {yes} |")
    o += ["", "**ثلاثةُ مآلاتٍ لا خمسة.** `NON_BLOCKING` و`EXPLANATORY` "
          "يشتركان في سقفٍ واحد، و`BLOCKING` و`HIDDEN_FORBIDDEN` كذلك. "
          "فاختيارُ المالك بين أربعةِ أسماءٍ يقع على **ثلاثةِ آثار**.", ""]

    o += ["## مصفوفةُ الانتقال — لكلّ صنفٍ في كلّ سيناريو", "",
          "| الصنف | الكلمات | لو أُسند | السقف | ACCEPT قبلُ ⟶ بعدُ | "
          "DEFER | BLOCK | أحكامٌ تتحرّك |", "|---|---|---|---|---|---|---|---|"]
    for r in rows:
        b, a = r["before"], r["after"]
        o.append(f'| `{r["class"]}` | {r["members"]} | `{r["kind"]}` | '
                 f'`{r["rank_cap"]}` | {b["ACCEPT"]} ⟶ {a["ACCEPT"]} | '
                 f'{b["DEFER"]} ⟶ {a["DEFER"]} | '
                 f'{b["BLOCK"]} ⟶ {a["BLOCK"]} | **{r["verdicts_that_move"]}** |')

    words = sum(d.get("members") or 0
                for d in m["M2_reach"]["per_class"].values())
    events = sum(d.get("events") or 0
                 for d in m["M2_reach"]["per_class"].values())
    o += ["", "**والمقامُ**: أحكامُ المحور الرابع على كلماتِ ذلك الصنف "
          "وحدَها. ولا تُجمع الصفوفُ: كلمةٌ قد تحمل صنفَين، فمجموعُ "
          "العمودِ ليس عددَ كلماتٍ متمايزة.", "",
          f"**وعمودُ «الكلمات» بمقام الكلمات** ({words}) لا بمقام الأحداث "
          f"({events}). والثاني هو ما يُطبع في `output/doors` و"
          "`output/remediation`، وكلاهما مقيس؛ والفرقُ مواضعُ حرفٍ زائدة "
          "على كلماتٍ معدودةٍ أصلًا، مشروحٌ في "
          "`output/bound/02_class_count.json`.", "",
          "## الحرّاس", "", "| الحارس | المقام | النتيجة |", "|---|---|---|"]
    for x in g:
        o.append(f'| `{x["guard"]}` | {x["denominator"]} | '
                 f'{"PASS" if x["passes"] else "FALLS"} |')

    o += ["", "## ما لا يُقاس هنا", "",
          "- **أثرُ الصنف على المحور الأوّل والثاني** — الصنفُ يُصدَر في "
          "الأوّل، فحكمُ الأوّل عليه سابقٌ على السقف.",
          "- **تراكبُ الأصناف** — كلمةٌ تحمل صنفَين تحتها سقفان، "
          "و`meet` هو الحاكم؛ ولا يُقاس التراكبُ قبل أن يُسنَد صنفٌ واحد.",
          "- **الرتبةُ الفعليّة** — هذه المصفوفةُ تقرأ السقفَ لا الرتبةَ "
          "الممنوحة؛ والرتبةُ من `meet` بأربعةِ مدخلات، وثلاثةٌ منها "
          "خارجَ هذا القياس.", ""]
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="reports/gamma_shadow")
    a = ap.parse_args()

    m = load()
    caps = ceilings()
    rows = scenarios(m, caps)
    g = guards(rows, caps, m)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "PROJECTED_IMPACT.md").write_text(render(rows, caps, g, m),
                                             encoding="utf-8")
    (out / "PROJECTED_IMPACT.json").write_text(
        json.dumps({"task": "T5_3_PROJECTED_IMPACT", "ceilings": caps,
                    "scenarios": rows, "guards": g,
                    "all_guards_pass": all(x["passes"] for x in g)},
                   ensure_ascii=False, indent=1), encoding="utf-8")

    classes = sorted({r["class"] for r in rows})
    print(f"T5.3 سيناريوهاتٌ {len(rows)} = {len(classes)} صنفًا × "
          f"{len(ASSIGNABLE)} إسنادات")
    print(f'    السقوف: {caps}')
    biggest = max(rows, key=lambda r: r["verdicts_that_move"])
    print(f'    أكبرُ أثرٍ ممكن: {biggest["class"]} تحت '
          f'{biggest["kind"]} ⟶ {biggest["verdicts_that_move"]} حكمًا')
    for x in g:
        print(f'    {x["guard"]:24} {"PASS" if x["passes"] else "FALLS"} '
              f'/{x["denominator"]}')
    if not all(x["passes"] for x in g):
        raise Blocked("GUARD_FALLS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
