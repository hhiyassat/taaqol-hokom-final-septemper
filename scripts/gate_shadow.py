#!/usr/bin/env python3
"""`T-7` — ظلُّ البوّابة: ما **كانت ستقول** `TransitionGate` لو استُفتيت.

    .venv-taaqol/bin/python scripts/gate_shadow.py

**ظلٌّ لا حكم** (`G_SHADOW_ONLY`). لا يُبدَّل عمودُ `Verdict` في مخرجات
المحاور، ولا يُكتب خارجَ `reports/gate_shadow/`.

**والحاملُ ليس من لوحةِ المفاتيح.** رسومُ `SlotGraph` تُستورَد من فِخاخِ
اختباراتِ الـ vendor نفسِها (`tests/test_transition_gate.py`) — قراءةٌ لا
مَسّ: ولا تُعدَّل بايتةٌ فيه. فلو بنيتُ الحاملَ بيدي لكان الجوابُ جوابَ
شكلٍ اخترعتُه، لا جوابَ البوّابة.

**والرتبةُ من `meet` لا من العين** (`G_RANK_FROM_MEET`). تُحسَب
`RankLattice.meet(evidence_rank, identity_rank, gate_rank, ceiling)`
استقلالًا وتُقارَن بـ `granted_rank` الذي ردّته البوّابة؛ فإن افترقا سقط
الحارس. ولا يُكتب رقمُ رتبةٍ لم يخرج من نداءٍ حيّ (`G_GATE_QUERIED`).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import importlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))
sys.path.insert(0, str(VENDOR))

from taaqqul_slot_geometry import (  # noqa: E402
    EvidenceContract,
    GenerationSource,
    Layer,
    Rank,
    RankLattice,
    Residual,
    ResidualKind,
    ResidualPolicy,
    SlotGraph,
    TransitionGate,
)

AXES = (
    "reports/axis_0_quran_build/QURAN_WORDS.csv",
    "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv",
    "reports/axis_2_mabniyat_operators/AXIS_2_TOKENS.csv",
    "reports/axis_3_syllables/AXIS_3_SYLLABLES.csv",
    "reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv",
)
FIXTURES = "tests.test_transition_gate"


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def fixtures():
    """يُستورَد فَخُّ الـ vendor كما هو. غيابُه وقفٌ لا اختراع."""
    try:
        return importlib.import_module(FIXTURES)
    except Exception as exc:  # noqa: BLE001
        raise Blocked(
            f"OWNER_ALERT: VENDOR_FIXTURES_UNAVAILABLE — {FIXTURES}: {exc}\n"
            "ولا يُبنى الحاملُ باليد: شكلٌ اخترعتُه يعطي جوابًا اخترعتُه."
        ) from exc


def fingerprint(paths) -> dict:
    out = {}
    for rel in paths:
        p = ROOT / rel
        out[rel] = (hashlib.sha256(p.read_bytes()).hexdigest()[:16]
                    if p.is_file() else "ABSENT")
    return out


def residual_like_vendor(kind: ResidualKind) -> Residual:
    """بالشكلِ الذي يبني به الـ vendor فضلاتِه في اختباراتِه نفسِها.

    `tests/test_transition_gate.py:627` (`BLOCKING`, ظاهرة) و`:658`
    (`HIDDEN_FORBIDDEN`, مستورة) و`:949` (`DEFERRABLE`, ظاهرة). فالستر
    خاصّةُ `HIDDEN_FORBIDDEN` عندهم لا اختيارٌ منّي.
    """
    hidden = kind is ResidualKind.HIDDEN_FORBIDDEN
    return Residual(name=f"shadow-{kind.name.lower()}", kind=kind,
                    visible=not hidden)


def candidate_graph(fx, *, residuals=(), rank=Rank.CANDIDATE):
    """`R2` — الأصلُ الثالث `CANDIDATE`، بشكل الـ vendor لا بشكلٍ مخترَع.

    فَخُّ الـ vendor يبني أصلَين فقط. والثالثُ يُبنى هنا من **قِطَع الفَخّ
    نفسِها** (المركزُ والخانةُ والحدُّ والمخرَج)، ولا يُغيَّر منها شيء؛
    والمبدَّلُ حقلٌ واحدٌ مُعلَن: `generation_source`. و`entry_boundary`
    يُترك `None` لأنّ الحاملَ يرفضه لغير `DECLARED_ENTRY`
    (`slot_graph.py:486`) — فذلك حكمُ الحامل لا اختيارٌ منّي.
    """
    return SlotGraph(
        center=fx._center("CANDIDATE"),
        slots=(fx._filled_slot(),),
        boundary=fx._boundary(),
        residuals=residuals,
        rank=rank,
        output_boundary=fx._output_within(),
        generation_source=GenerationSource.CANDIDATE,
    )


def all_origins(fx) -> list[tuple]:
    """`G_ALL_ORIGINS` — أصلٌ لكلّ عضوٍ في `GenerationSource`، لا أقلّ.

    ورتبةُ الهُويّة تُؤخذ ممّا يبنيه كلُّ أصل، ولا تُساوى قسرًا: أصلٌ
    غيرُ `TRANSITION_VERDICT` يرفضه الحاملُ فوق `UNGATED_RANK_CEILING`،
    فتُختار له رتبةٌ يقبلها — وذلك حكمُ الحامل، مُعلَنًا.
    """
    return [
        ("DECLARED_ENTRY", fx._build_graph, Rank.TRACE),
        ("CANDIDATE", lambda **kw: candidate_graph(fx, **kw), Rank.CANDIDATE),
        ("TRANSITION_VERDICT", fx._gated_graph, Rank.HYPOTHESIS),
    ]


def g_all_origins(rows: list[dict]) -> dict:
    """عددُ الأصولِ في المخرَج = عددُ أعضاءِ `GenerationSource` — لا أقلّ.

    والسمُّ: يُحذف أصلٌ ⟶ يسقط. فدعوى «ولا `CERTIFICATE` بحال» مقيسةٌ على
    ثلثَين تُقرأ مطلقةً وهي ليست كذلك.
    """
    declared = sorted(g.name for g in GenerationSource)
    seen = sorted({r.get("origin") for r in rows if r.get("origin")})
    missing = sorted(set(declared) - set(seen))
    extra = sorted(set(seen) - set(declared))
    return {"guard": "G_ALL_ORIGINS", "denominator": len(declared),
            "declared": declared, "measured": seen,
            "missing": missing, "not_a_member": extra,
            "passes": not missing and not extra}


def sweep(fx) -> list[dict]:
    """كلُّ زوجِ (أصلِ الحامل × طبقةِ الهدف × رتبةِ البيّنة × فضلةٍ) يُستفتى حيًّا."""
    gate = fx._gate()
    rows: list[dict] = []
    origins = tuple(all_origins(fx))
    residual_cases = (("NONE", ()),)
    for kind in ResidualKind:
        try:
            residual_cases += ((kind.name, (residual_like_vendor(kind),)),)
        except Exception:  # noqa: BLE001  # هذا الصنف لا يُبنى بهذا الشكل
            residual_cases += ((kind.name, None),)

    for origin, make, identity_rank in origins:
        for target in Layer:
            for ev_rank in (None, Rank.TRACE, Rank.HYPOTHESIS,
                            Rank.LICENSED, Rank.STRONG, Rank.CERTIFICATE):
                for rk_name, residuals in residual_cases:
                    if residuals is None:
                        rows.append({
                            "origin": origin, "target_layer": target.name,
                            "evidence_rank": ev_rank.name if ev_rank else "ABSENT",
                            "residual_kind": rk_name,
                            "state": "", "failure_code": "",
                            "granted_rank": "", "meet_independent": "",
                            "agrees": "",
                            "status": "NOT_AVAILABLE:FIXTURE_CANNOT_BUILD_KIND",
                        })
                        continue
                    graph = make(residuals=residuals, rank=identity_rank)
                    ev = (EvidenceContract() if ev_rank is None
                          else EvidenceContract(
                              sources=(fx._evidence("s", ev_rank),)))
                    v = gate.decide(graph, target, ev)

                    ceiling = ResidualPolicy.evaluate(graph.residuals).ceiling
                    indep = (RankLattice.meet(ev.evidence_rank, graph.rank,
                                              gate.gate_rank, ceiling)
                             if ev.sources else None)
                    granted = getattr(v, "granted_rank", None)
                    rows.append({
                        "origin": origin,
                        "target_layer": target.name,
                        "evidence_rank": ev_rank.name if ev_rank else "ABSENT",
                        "residual_kind": rk_name,
                        "state": v.state.name,
                        "failure_code": (v.failure_code.name
                                         if v.failure_code else ""),
                        "granted_rank": (granted.name if granted is not None
                                         else ""),
                        "meet_independent": (indep.name if indep is not None
                                             else ""),
                        "agrees": ("" if granted is None or indep is None
                                   else granted is indep),
                        "status": "MEASURED",
                    })
    return rows


# --------------------------------------------------------------------- الحرّاس
def g_shadow_only(before: dict, after: dict) -> dict:
    changed = sorted(k for k in before if before.get(k) != after.get(k))
    return {"guard": "G_SHADOW_ONLY", "denominator": len(before),
            "changed": changed, "passes": not changed}


ORDER = tuple(r.name for r in Rank)


def g_rank_from_meet(rows: list[dict]) -> dict:
    """`meet` هو مانحُ الرتبةِ — بمقامَين، لا بمقامٍ واحد.

    **الأوّل: `APPROVED`.** هناك وحدَها تُمنح الرتبةُ بالـ`meet`، فيجب
    التطابقُ التامّ.

    **والثاني: القاطعُ قبلَ الـ`meet`.** `FORBIDDEN_LEAP` يربط في الخطوة
    الثانية، قبل الخطوةِ الخامسة؛ فالافتراقُ هناك ليس خللًا — هو ترتيبُ
    القانون. والمطلوبُ أن يكون المقطوعُ **دون** الـ`meet` لا فوقَه: قطعٌ
    يرفع رتبةً نقضٌ للقانون. وخلطُ المقامَين يُري الحارسَ ساقطًا وهو قائم.
    """
    approved = [r for r in rows if r.get("state") == "APPROVED"
                and r.get("agrees") != ""]
    off = sorted(f'{r["origin"]}/{r["target_layer"]}/{r["evidence_rank"]}/'
                 f'{r["residual_kind"]}: {r["granted_rank"]}≠'
                 f'{r["meet_independent"]}'
                 for r in approved if r.get("agrees") is not True)

    cut = [r for r in rows if r.get("state") in
           ("FORBIDDEN_LEAP", "BLOCKED", "REJECTED", "DEFERRED")
           and r.get("granted_rank") and r.get("meet_independent")]
    raised = sorted(
        f'{r["state"]}/{r["target_layer"]}: {r["granted_rank"]}>'
        f'{r["meet_independent"]}'
        for r in cut
        if ORDER.index(r["granted_rank"]) > ORDER.index(r["meet_independent"]))
    return {"guard": "G_RANK_FROM_MEET",
            "denominator_approved": len(approved),
            "denominator_short_circuit": len(cut),
            "of_rows": len(rows),
            "disagreements_on_approved": off,
            "short_circuit_raised_rank": raised,
            "passes": not off and not raised}


def g_gate_queried(rows: list[dict]) -> dict:
    """كلُّ صفٍّ حالتُه من نداءٍ حيّ: حالةٌ فارغةٌ بلا سببٍ مُسمًّى تُسقِط."""
    states = {"MEASURED"}
    bad = sorted(f'{r["origin"]}/{r["target_layer"]}'
                 for r in rows
                 if r.get("status") in states and not r.get("state"))
    unmeasured = [r for r in rows if r.get("status") not in states]
    return {"guard": "G_GATE_QUERIED", "denominator": len(rows),
            "measured": len(rows) - len(unmeasured),
            "not_available": sorted({r["status"] for r in unmeasured}),
            "empty_state": bad, "passes": not bad}


def g_no_certificate(rows: list[dict]) -> dict:
    """لا رتبةَ `CERTIFICATE` تُمنح من هذه البوّابة — قياسًا لا نقلًا."""
    hits = sorted(f'{r["origin"]}/{r["target_layer"]}/{r["evidence_rank"]}'
                  for r in rows if r.get("granted_rank") == "CERTIFICATE")
    granted = [r for r in rows if r.get("granted_rank")]
    return {"guard": "G_NO_CERTIFICATE_FROM_GATE",
            "denominator": len(granted), "hits": hits, "passes": not hits}


def build(out_dir: Path) -> dict:
    before = fingerprint(AXES)
    fx = fixtures()
    rows = sweep(fx)

    out_dir.mkdir(parents=True, exist_ok=True)
    cols = ["origin", "target_layer", "evidence_rank", "residual_kind",
            "state", "failure_code", "granted_rank", "meet_independent",
            "agrees", "status"]
    with (out_dir / "TRANSITIONS.csv").open("w", encoding="utf-8",
                                            newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})

    after = fingerprint(AXES)
    guards = [g_shadow_only(before, after), g_gate_queried(rows),
              g_rank_from_meet(rows), g_no_certificate(rows),
              g_all_origins(rows)]

    tally: dict[str, int] = {}
    codes: dict[str, int] = {}
    for r in rows:
        if r["state"]:
            tally[r["state"]] = tally.get(r["state"], 0) + 1
        if r["failure_code"]:
            codes[r["failure_code"]] = codes.get(r["failure_code"], 0) + 1
    return {
        "task": "T7_GATE_SHADOW",
        "carrier_source": f"vendor {FIXTURES} (read, never modified)",
        "rows": len(rows),
        "origins": sorted({r["origin"] for r in rows}),
        "origins_declared": sorted(g.name for g in GenerationSource),
        "states": dict(sorted(tally.items())),
        "failure_codes": dict(sorted(codes.items())),
        "ranks_granted": sorted({r["granted_rank"] for r in rows
                                 if r["granted_rank"]}),
        "guards": guards,
        "all_guards_pass": all(g["passes"] for g in guards),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="reports/gate_shadow")
    a = ap.parse_args()
    out_dir = ROOT / a.out
    res = build(out_dir)
    (out_dir / "SUMMARY.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    print(f'T7 صفوفٌ {res["rows"]} · الحاملُ من فَخِّ الـ vendor')
    print(f'    الحالات: {res["states"]}')
    print(f'    الرموز:  {res["failure_codes"]}')
    print(f'    الرتبُ الممنوحة: {res["ranks_granted"] or "لا شيء"}')
    for g in res["guards"]:
        den = g.get("denominator")
        if den is None:
            den = (f'{g.get("denominator_approved")}+'
                   f'{g.get("denominator_short_circuit")}')
        print(f'    {g["guard"]:26} {"PASS" if g["passes"] else "FALLS"} /{den}')
    if not res["all_guards_pass"]:
        raise Blocked("GUARD_FALLS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
