#!/usr/bin/env python3
"""`T-6` — ظلُّ الخطوط المستقيمة الممنوعة: ما **كان سيقع** لو استُفتي السجلّ.

    .venv-taaqol/bin/python scripts/forbidden_shadow.py

**ظلٌّ لا حكم** (`G_SHADOW_ONLY`). لا يُبدَّل عمودُ `Verdict` في مخرجات
المحاور، ولا يُكتب خارجَ `reports/forbidden_shadow/`. تُبصَم ملفّاتُ المحاور
الخمسةِ قبلَ التشغيل وبعدَه، ويُقارَن البصمُ.

**كلُّ جوابٍ من نداءٍ حيّ** (`G_FORBIDDEN_QUERIED`). لا يُكتب `True` في
عمود `answer` إلّا وقد ردّته `CANONICAL_REGISTRY` في هذا التشغيل. ويُحصى
عددُ النداءات فيُطابَق بعددِ الصفوف؛ فإن افترقا سقط الحارس.

**والسؤالُ الذي يجيب نفسَه يُسمّى** (`G_TAUTOLOGY_DECLARED`). صفٌّ مأخوذٌ
من السجلّ ثمّ يُسأل عنه السجلُّ ليس دليلًا — هو ترديد. تُوسم هذه الأسئلة
`TAUTOLOGY`، ولا تُعدّ في مقامِ الدليل. والدليلُ ما جاء من خارج السجلّ:
الرسمُ المُعلَن للمراحل، وطبقاتُ البوّابة، ومخرجاتُ المحاور.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))

from taaqqul_slot_geometry import Layer  # noqa: E402
from taaqqul_slot_geometry.core.forbidden_lines import (  # noqa: E402
    CANONICAL_REGISTRY,
)
from taaqqul_slot_geometry.runtime.native_stage_registry import (  # noqa: E402
    get_native_stage_registry,
)

AXES = (
    "reports/axis_0_quran_build/QURAN_WORDS.csv",
    "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv",
    "reports/axis_2_mabniyat_operators/AXIS_2_TOKENS.csv",
    "reports/axis_3_syllables/AXIS_3_SYLLABLES.csv",
    "reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv",
)
AXIS4 = ROOT / "reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv"


class Blocked(SystemExit):
    """فشلٌ مغلق."""


# ---------------------------------------------------------------- عدّادُ النداء
@dataclass
class LiveRegistry:
    """غلافُ عدٍّ لا يُغيّر سلوكًا: يمرّر النداءَ ويحصيه.

    ليس ترقيعًا للـ vendor — السجلُّ الأصلُ لا يُمَسّ، ولا يُستبدَل في
    أيّ موضعٍ من التشغيل. هذا الغلافُ يعيش في هذا الملفّ وحدَه ليُثبِت
    أنّ كلَّ خانةِ جوابٍ في المخرَج جاءت من نداءٍ وقع فعلًا.
    """

    inner: object
    calls: list = field(default_factory=list)

    def is_forbidden_direct(self, source: str, target: str) -> bool:
        ans = self.inner.is_forbidden_direct(source, target)
        self.calls.append(("is_forbidden_direct", source, target, ans))
        return ans

    def is_forbidden_term_transfer(self, term: str, src: str, tgt: str) -> bool:
        ans = self.inner.is_forbidden_term_transfer(term, src, tgt)
        self.calls.append(("is_forbidden_term_transfer", term, f"{src}->{tgt}", ans))
        return ans


# ------------------------------------------------------------------ الاستفتاءات
def q1_self_layer_leaps(reg: LiveRegistry) -> list[dict]:
    """كلُّ صفٍّ في السجلّ يُسأل عنه السجلُّ — ترديدٌ لا دليل."""
    out = []
    for row in CANONICAL_REGISTRY.lines:
        ans = reg.is_forbidden_direct(row.source, row.target)
        out.append({
            "query_id": "Q1",
            "surface": "LAYER_LEAP",
            "source": row.source,
            "target": row.target,
            "call": "is_forbidden_direct",
            "answer": ans,
            "input_drawn_from": "CANONICAL_REGISTRY.lines",
            "status": "TAUTOLOGY",
            "events_in_data": "",
            "mapping_authority": "",
            "note": "سؤالٌ مصدرُه السجلّ نفسُه: يجيب نفسَه ولا يشهد.",
        })
    return out


def q2_self_term_transfers(reg: LiveRegistry) -> list[dict]:
    """الاثنا عشر: `is_forbidden_term_transfer` هو سؤالُها، لا `is_forbidden_direct`."""
    out = []
    for row in CANONICAL_REGISTRY.term_transfers:
        yes = reg.is_forbidden_term_transfer(
            row.term, row.source_domain, row.target_domain)
        out.append({
            "query_id": "Q2a",
            "surface": "TERM_TRANSFER",
            "source": f"{row.term}@{row.source_domain}",
            "target": row.target_domain,
            "call": "is_forbidden_term_transfer",
            "answer": yes,
            "input_drawn_from": "CANONICAL_REGISTRY.term_transfers",
            "status": "TAUTOLOGY",
            "events_in_data": "",
            "mapping_authority": "",
            "note": "الاثنا عشر مأخوذةٌ من السجلّ فتردّ True بحكم الأخذ.",
        })
        wrong = reg.is_forbidden_direct(row.source_domain, row.target_domain)
        out.append({
            "query_id": "Q2b",
            "surface": "TERM_TRANSFER",
            "source": row.source_domain,
            "target": row.target_domain,
            "call": "is_forbidden_direct",
            "answer": wrong,
            "input_drawn_from": "CANONICAL_REGISTRY.term_transfers",
            "status": "WRONG_SURFACE",
            "events_in_data": "",
            "mapping_authority": "",
            "note": "سطحُ الطبقات لا يجيب عن نقلِ المصطلح — سؤالٌ في غير بابه.",
        })
    return out


def q3_stage_graph(reg: LiveRegistry) -> list[dict]:
    """الرسمُ المُعلَن للمراحل: مدخلٌ من خارج السجلّ — هذا هو الدليل."""
    specs = get_native_stage_registry()
    ids = {s.stage_id for s in specs}
    out = []
    for spec in specs:
        for succ in spec.allowed_successors:
            if succ not in ids:
                continue
            ans = reg.is_forbidden_direct(spec.stage_id, succ)
            out.append({
                "query_id": "Q3",
                "surface": "STAGE_EDGE",
                "source": spec.stage_id,
                "target": succ,
                "call": "is_forbidden_direct",
                "answer": ans,
                "input_drawn_from": "get_native_stage_registry().allowed_successors",
                "status": "EVIDENCE",
                "events_in_data": "",
                "mapping_authority": "CODE_DERIVED",
                "note": "",
            })
    return out


def q4_gate_layers(reg: LiveRegistry) -> list[dict]:
    """طبقاتُ البوّابةِ الأربع: كلُّ زوجٍ مرتَّبٍ منها يُسأل حيًّا."""
    names = [ly.name for ly in Layer]
    out = []
    for a in names:
        for b in names:
            if a == b:
                continue
            ans = reg.is_forbidden_direct(a, b)
            out.append({
                "query_id": "Q4",
                "surface": "GATE_LAYER_PAIR",
                "source": a,
                "target": b,
                "call": "is_forbidden_direct",
                "answer": ans,
                "input_drawn_from": "Layer (enum)",
                "status": "EVIDENCE",
                "events_in_data": "",
                "mapping_authority": "CODE_DERIVED",
                "note": "",
            })
    return out


def q5_axis4_peel(reg: LiveRegistry) -> list[dict]:
    """قشرُ المحورِ الرابع: العدُّ مقيس، والتسميةُ حكمُ المالك.

    السطرُ المتوقَّع `Signifier → WordForm` يُسأل عنه السجلُّ حيًّا؛ أمّا
    **أنّ قشرَ المحورِ الرابع هو هذا الانتقالُ بعينه** فليس في الشيفرة ما
    يدلّ عليه: لا `Signifier` ولا `WordForm` اسمُ طبقةٍ ولا مرحلة. فهي
    نسبةٌ لا تُستنبَط — `OWNER_RULING_REQUIRED`.
    """
    if not AXIS4.is_file():
        return [{
            "query_id": "Q5", "surface": "AXIS_4_PEEL",
            "source": "Signifier", "target": "WordForm",
            "call": "", "answer": "",
            "input_drawn_from": "reports/axis_4_peel_to_stem",
            "status": "NOT_AVAILABLE:AXIS_4_ABSENT",
            "events_in_data": "", "mapping_authority": "OWNER_RULING_REQUIRED",
            "note": "الملفُّ غيرُ موجود.",
        }]
    peels = 0
    katab_rows = 0
    katab_peels = 0
    root_proven = 0
    total = 0
    with AXIS4.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            total += 1
            pc = (r.get("Peel_Count") or "").strip()
            n = int(pc) if pc.lstrip("-").isdigit() else 0
            if n > 0:
                peels += 1
            if (r.get("Root_Proven") or "").strip().upper() == "YES":
                root_proven += 1
            if (r.get("Word") or "") == "كَتَبَ":
                katab_rows += 1
                if n > 0:
                    katab_peels += 1
    rows = []
    for src, tgt, ev, why in (
        ("Signifier", "WordForm", peels,
         f"قشرٌ وقع في {peels} من {total} صفًّا"),
        ("Root", "LexicalMeaning", root_proven,
         f"جذرٌ مُثبَتٌ في {root_proven} من {total} صفًّا"),
        ("WordForm", "Meaning", root_proven,
         "لا يبلغه إلّا ما ثبت جذرُه"),
    ):
        rows.append({
            "query_id": "Q5",
            "surface": "AXIS_4_PEEL",
            "source": src,
            "target": tgt,
            "call": "is_forbidden_direct",
            "answer": reg.is_forbidden_direct(src, tgt),
            "input_drawn_from": "CANONICAL_REGISTRY.lines + axis_4 counts",
            "status": "MAPPING_NOT_DERIVABLE",
            "events_in_data": ev,
            "mapping_authority": "OWNER_RULING_REQUIRED",
            "note": why,
        })
    rows.append({
        "query_id": "Q5k",
        "surface": "AXIS_4_PEEL",
        "source": "كَتَبَ",
        "target": "Signifier→WordForm",
        "call": "",
        "answer": "",
        "input_drawn_from": "reports/axis_4_peel_to_stem",
        "status": "EXPECTED_EVENT_ABSENT",
        "events_in_data": katab_peels,
        "mapping_authority": "OWNER_RULING_REQUIRED",
        "note": (f"«كَتَبَ» ورد {katab_rows} صفًّا، وقشرَ في {katab_peels}. "
                 "فلا واقعةَ تقع تحت هذا السطر."),
    })
    return rows


# --------------------------------------------------------------------- الحرّاس
def fingerprint(paths) -> dict:
    out = {}
    for rel in paths:
        p = ROOT / rel
        out[rel] = (hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                    if p.is_file() else "ABSENT")
    return out


def g_shadow_only(before: dict, after: dict) -> dict:
    """يبلّغ ولا يموت: يُقارن البصمَ ويسمّي المختلف."""
    changed = sorted(k for k in before if before.get(k) != after.get(k))
    return {"guard": "G_SHADOW_ONLY", "denominator": len(before),
            "changed": changed, "passes": not changed}


def g_forbidden_queried(rows: list[dict], reg: LiveRegistry) -> dict:
    """كلُّ جوابٍ من نداءٍ حيّ: تُطابَق أزواجُ (النداء، الجواب) بما وقع."""
    made = {(c[0], c[1], c[2]): c[3] for c in reg.calls}
    unbacked, mismatched = [], []
    for r in rows:
        if not r.get("call"):
            continue
        key = (r["call"], r["source"], r["target"])
        if r["query_id"] == "Q2a":
            row = next((t for t in CANONICAL_REGISTRY.term_transfers
                        if f"{t.term}@{t.source_domain}" == r["source"]
                        and t.target_domain == r["target"]), None)
            key = (r["call"], row.term,
                   f"{row.source_domain}->{row.target_domain}") if row else key
        if key not in made:
            unbacked.append(f'{r["query_id"]}:{r["source"]}->{r["target"]}')
        elif made[key] != r["answer"]:
            mismatched.append(f'{r["query_id"]}:{r["source"]}->{r["target"]}')
    answered = [r for r in rows if r.get("call")]
    return {"guard": "G_FORBIDDEN_QUERIED",
            "denominator": len(answered),
            "live_calls": len(reg.calls),
            "unbacked": unbacked, "mismatched": mismatched,
            "passes": not unbacked and not mismatched
            and len(reg.calls) == len(answered)}


def g_tautology_declared(rows: list[dict]) -> dict:
    """ما جاء مدخلُه من السجلّ لا يُوسَم دليلًا."""
    from_registry = {"CANONICAL_REGISTRY.lines",
                     "CANONICAL_REGISTRY.term_transfers"}
    wrong = sorted(f'{r["query_id"]}:{r["source"]}->{r["target"]}'
                   for r in rows
                   if r.get("input_drawn_from") in from_registry
                   and r.get("status") == "EVIDENCE")
    ev = [r for r in rows if r.get("status") == "EVIDENCE"]
    return {"guard": "G_TAUTOLOGY_DECLARED",
            "denominator": len(rows),
            "evidence_rows": len(ev),
            "tautology_rows": sum(1 for r in rows
                                  if r.get("status") == "TAUTOLOGY"),
            "mislabelled": wrong, "passes": not wrong}


# ----------------------------------------------------------------------- بناء
def build(out_dir: Path) -> dict:
    before = fingerprint(AXES)
    reg = LiveRegistry(CANONICAL_REGISTRY)
    rows = (q1_self_layer_leaps(reg) + q2_self_term_transfers(reg)
            + q3_stage_graph(reg) + q4_gate_layers(reg) + q5_axis4_peel(reg))

    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["query_id", "surface", "source", "target", "call", "answer",
            "input_drawn_from", "status", "events_in_data",
            "mapping_authority", "note"]
    with (out_dir / "WOULD_FIRE.csv").open("w", encoding="utf-8",
                                           newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    after = fingerprint(AXES)
    guards = [g_shadow_only(before, after), g_forbidden_queried(rows, reg),
              g_tautology_declared(rows)]

    fires = [r for r in rows if r.get("answer") is True
             and r.get("status") == "EVIDENCE"]
    return {
        "task": "T6_FORBIDDEN_SHADOW",
        "registry": {"layer_leap_rows": len(CANONICAL_REGISTRY.lines),
                     "term_transfer_rows": len(CANONICAL_REGISTRY.term_transfers)},
        "rows": len(rows),
        "evidence_rows": sum(1 for r in rows if r.get("status") == "EVIDENCE"),
        "would_fire_on_evidence": [f'{r["source"]}->{r["target"]}'
                                   for r in fires],
        "reach": {
            "gate_layers": len(list(Layer)),
            "layer_pairs_that_are_registry_rows": sum(
                1 for r in rows if r["query_id"] == "Q4" and r["answer"] is True),
            "stage_edges_checked": sum(1 for r in rows if r["query_id"] == "Q3"),
            "stage_edges_forbidden": sum(
                1 for r in rows if r["query_id"] == "Q3" and r["answer"] is True),
        },
        "guards": guards,
        "all_guards_pass": all(g["passes"] for g in guards),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="reports/forbidden_shadow")
    a = ap.parse_args()
    out_dir = ROOT / a.out
    res = build(out_dir)
    (out_dir / "SUMMARY.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    r = res["reach"]
    print(f'T6 صفوفٌ {res["rows"]} · منها دليلٌ {res["evidence_rows"]} · '
          f'ترديدٌ {res["guards"][2]["tautology_rows"]}')
    print(f'    السجلّ: طبقاتٌ {res["registry"]["layer_leap_rows"]} · '
          f'مصطلحاتٌ {res["registry"]["term_transfer_rows"]}')
    print(f'    مدى البوّابة: أزواجُ الطبقاتِ الممنوعة '
          f'{r["layer_pairs_that_are_registry_rows"]}/'
          f'{len(list(Layer)) * (len(list(Layer)) - 1)} '
          f'من {res["registry"]["layer_leap_rows"]} صفًّا')
    print(f'    حوافُّ المراحل: مفحوصةٌ {r["stage_edges_checked"]} · '
          f'ممنوعةٌ {r["stage_edges_forbidden"]}')
    print(f'    يقع فعلًا: {res["would_fire_on_evidence"] or "لا شيء"}')
    for g in res["guards"]:
        print(f'    {g["guard"]:22} {"PASS" if g["passes"] else "FALLS"} '
              f'/{g.get("denominator")}')
    if not res["all_guards_pass"]:
        raise Blocked("GUARD_FALLS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
