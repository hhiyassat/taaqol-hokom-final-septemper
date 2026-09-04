#!/usr/bin/env python3
"""يبني `TAAQOL_NAZILA_MATRIX` ببنية المرجع، ومحتوًى من الكود وحدَه.

    .venv-taaqol/bin/python scripts/build_nazila_matrix.py \\
        --text inspection/case.txt \\
        --reference inspection/TAAQOL_NAZILA_MATRIX.md \\
        --out output/nazila_from_code

**القاعدة.** كلُّ خانةٍ إمّا قيمةٌ مشتقّةٌ من تشغيلٍ أو من مصدر تعقُّل، وإمّا
«غير متوفرة» ومعها رمزُ سببٍ من جردٍ مغلق. لا خانةَ فارغة، ولا خانةَ مملوءةٌ
من نثرٍ بشريّ، ولا خانةَ محذوفة. والفصلُ الذي يخرج كلُّه «غير متوفرة» يُطبع
كذلك — خلوُّه هو الخبر.

**والدفترُ هو الحكم**: مملوءٌ من الكود + «غير متوفرة» = عددُ الخانات، بلا
بقيّة. فإن لم يقفل فثمّة خانةٌ لم تُصنَّف.

**ولا يُنقل سطرٌ من وثيقة المرجع إلى خانة.** المرجعُ يُقرأ لبنيته — أسماءِ
فصوله وأعمدته — لا لمحتواه. وقراءةُ البنية مقابلةٌ لا نقل.
"""
from __future__ import annotations

import argparse
import dataclasses
import enum
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))

PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
MIN_PY = (3, 11)
NA = "غير متوفرة"
MIN_COPY_LEN = 40   # دون هذا الطول لا يدلّ التطابقُ على نقل

#: جردُ أسباب عدم التوفّر — **مغلق**. رمزٌ خارجه يُرفض بإنذار مالك.
REASONS = frozenset({
    "NOT_OPENED",                 # يُلحق بها اسمُ المرحلة
    "NOT_EMITTED_BY_RUNNER",
    "NOT_CONSTRUCTED_IN_SOURCE",
    "HUMAN_DECLARED_ONLY",
    "OWNER_DECISION",
})

STAGES = ("PATH_CLASSIFICATION", "PRE_WEIGHT_CAPACITY_AUDIT", "DAL_ONLY",
          "VERBAL_MADLUL", "DAL_MADLUL_BINDING", "CONTRACTABLE_UNIT",
          "RELATION", "FORMAL_SHAPE", "MUFRAD_DALALAH", "RELATION_CLOSURE",
          "IFADAH", "HUKM", "MANAT", "TANZIL", "ANSWER_AUDIT",
          "NON_CONTENT_FORMAL_ROUTE")


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


@dataclasses.dataclass
class Cell:
    """خانةٌ واحدة: اسمُها، ومصدرُها، وحالُها. لا ثالثَ لهما."""

    section: str
    field: str
    value: object = None
    source: str = ""
    reason: str = ""

    @property
    def from_code(self) -> bool:
        return not self.reason

    def rendered(self) -> str:
        if self.reason:
            return f"{NA} · `{self.reason}`"
        v = self.value
        # قاموسٌ في خانةٍ يخرج `{'k': n}` — تمثيلُ بايثون، لا قياس. ولا
        # يُصلَح بالطبع بل بالبناء: يُفرَد كلُّ مفتاحٍ سطرًا. فيُرفض هنا
        # كي لا يمرّ ثانيةً صامتًا.
        if isinstance(v, dict):
            raise Blocked(f"DICT_IN_CELL {self.section} · {self.field} — "
                          "التوزيعُ يُفرَد أسطرًا، ولا يُطبع قاموسًا")
        # قائمةٌ مقيسةٌ فارغة ليست غيابًا: المشغّلُ أصدر السجلَّ ولم يضع فيه
        # شيئًا. وطبعُها شرطةً يُقرأ نقصًا، فتُسمّى حالُها باسمها.
        if isinstance(v, (list, tuple)):
            return (" · ".join(f"`{x}`" for x in v) if v
                    else "`EMPTY_IN_RECORD`")
        return f"`{v}`" if isinstance(v, (int, float)) or (
            isinstance(v, str) and " " not in v) else str(v)


# ── الحرّاس التي تسبق الكتابة ────────────────────────────────────────────
def preflight() -> dict:
    """بايثون · بصمةُ التثبيت · الاستيراد. فشلُ أيٍّ منها يقف بلا كتابة."""
    out: dict = {"python": platform.python_version(),
                 "platform": f"{platform.system()} {platform.machine()}",
                 "utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    out["python_ok"] = sys.version_info[:2] >= MIN_PY
    head = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    out["vendor_head"] = head.stdout.strip()
    out["vendor_pin"] = PIN
    out["pin_matches"] = out["vendor_head"] == PIN
    try:
        from taaqqul_slot_geometry.runtime.corpus_runner import (  # noqa: F401
            run_native_corpus,
        )
        out["import_ok"] = True
        out["import_error"] = ""
    except Exception as exc:
        out["import_ok"] = False
        out["import_error"] = f"{type(exc).__name__}: {exc}"
    out["verdict"] = ("PASS" if out["python_ok"] and out["pin_matches"]
                      and out["import_ok"] else "BLOCKED")
    return out


# ── القياس ──────────────────────────────────────────────────────────────
def to_plain(value):
    """تعدادٌ قيمتُه عدد يُؤخذ باسمه — فالقيمةُ العدديّة لا تُسمّي."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_plain(getattr(value, f.name))
                for f in dataclasses.fields(value)}
    if isinstance(value, enum.Enum):
        return value.name if isinstance(value.value, int) else value.value
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_plain(v) for v in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def measure(text: str, corpus_id: str) -> dict:
    from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus
    res = run_native_corpus(corpus_id, tuple(text.split()))
    plain = to_plain(res)
    flat = [r for t in plain["token_results"] for r in t["records"]]
    return {"run": plain, "flat": flat,
            "tokens": [{"token_id": t["token_id"], "surface": t["surface"],
                        "path": t["paths"][0]["path_id"],
                        "confidence": t["paths"][0]["confidence"]}
                       for t in plain["token_results"]]}


def source_facts() -> dict:
    """ما يُقرأ من مصدر تعقُّل مباشرةً — تعداداتٌ وحقولٌ وقواعدُ وخطوط."""
    from taaqqul_slot_geometry.core.closure_state import ClosureState
    from taaqqul_slot_geometry.core.failure_taxonomy import FailureCode
    from taaqqul_slot_geometry.core.forbidden_lines import (
        CANONICAL_REGISTRY,
        ForbiddenLine,
    )
    from taaqqul_slot_geometry.core.rank_lattice import Rank
    from taaqqul_slot_geometry.core.slot_graph import EntryBoundary
    from taaqqul_slot_geometry.core.transition_state import TransitionState
    from taaqqul_slot_geometry.runtime import corpus_runner as cr
    from taaqqul_slot_geometry.runtime import execution_record as er
    from taaqqul_slot_geometry.runtime.execution_record import (
        StageExecutionRecord,
        StageTransitionState,
    )

    rules = re.findall(r"# (Rule \d+): (.+)",
                       Path(er.__file__).read_text(encoding="utf-8"))
    runner_src = Path(cr.__file__).read_text(encoding="utf-8")
    lines = getattr(CANONICAL_REGISTRY, "lines", None)
    return {
        "Rank": [r.name for r in Rank],
        "ClosureState": [c.value for c in ClosureState],
        "TransitionState": [t.value for t in TransitionState],
        "StageTransitionState": [s.value for s in StageTransitionState],
        "FailureCode_total": len(list(FailureCode)),
        "record_fields": list(StageExecutionRecord.__dataclass_fields__),
        "entry_boundary_fields": list(EntryBoundary.__dataclass_fields__),
        "rules": rules,
        "forbidden_line_fields": list(ForbiddenLine.__dataclass_fields__),
        "forbidden_lines": [to_plain(x) for x in lines],
        "forbidden_failure_codes": sorted(
            {to_plain(x.failure_code) for x in lines}),
        "runner_imports": {name: (probe in runner_src) for name, probe in (
            ("gamma", "gamma"),
            ("ClosureState", "ClosureState"),
            ("TransitionState", "core.transition_state"),
            ("forbidden_lines", "forbidden_lines"),
            ("EntryBoundary", "EntryBoundary"))},
    }


# ── دفترُ الخانات ───────────────────────────────────────────────────────
def build_cells(text: str, sha: str, corpus_id: str, m: dict, s: dict,
                pre: dict) -> list[Cell]:
    flat, toks = m["flat"], m["tokens"]
    states = Counter(r["transition_state"] for r in flat)
    per_stage = {}
    for r in flat:
        per_stage.setdefault(r["stage_id"], Counter())[r["transition_state"]] += 1
    hints = Counter(h for r in flat for h in r["remediation_hints"])
    resid = Counter(x for r in flat for x in r["residuals_after"])
    ranks = Counter(f'{r["rank_before"]}->{r["rank_after"]}' for r in flat)
    executed = [k for k, v in per_stage.items() if "EXECUTED" in v]

    C: list[Cell] = []

    def code(sec, field, value, src):
        C.append(Cell(sec, field, value, source=src))

    def na(sec, field, reason):
        C.append(Cell(sec, field, reason=reason))

    # ── رأس الوثيقة ─────────────────────────────────────────────────────
    H = "رأس الوثيقة"
    code(H, "INPUT_TEXT", text, "الملفّ")
    code(H, "INPUT_SHA256", sha, "hashlib")
    code(H, "CORPUS_ID", corpus_id, "الوسيط")
    code(H, "RUN_ID", m["run"]["run_id"], "run_native_corpus")
    code(H, "STAGE_COVERAGE", f"{len(per_stage)}/{len(STAGES)}", "عدُّ المراحل")
    code(H, "RUNTIME_EXECUTION", f"{len(executed)}/{len(STAGES)} EXECUTED",
         "عدُّ الحالات")
    code(H, "MEASURED_RECORDS",
         f"{len(flat)} = {len(toks)} × {len(per_stage)}", "عدُّ السجلّات")
    code(H, "FINAL_HUKM",
         " · ".join(sorted(per_stage.get("HUKM", {}))) or "—", "حالُ HUKM")
    code(H, "FINAL_TANZIL",
         " · ".join(sorted(per_stage.get("TANZIL", {}))) or "—", "حالُ TANZIL")
    code(H, "VENDOR_HEAD", pre["vendor_head"], "git rev-parse")
    for f in ("DOCUMENT_LABEL", "LAYER_RULE", "NO_LAYER_MIXING", "REPRODUCES"):
        na(H, f, "HUMAN_DECLARED_ONLY")

    # ── 0 حدّ الدخول ────────────────────────────────────────────────────
    S0 = "0. حدّ الدخول المعلن"
    for f in s["entry_boundary_fields"]:
        na(S0, f, "NOT_CONSTRUCTED_IN_SOURCE")

    # ── 1 بطاقة النازلة ─────────────────────────────────────────────────
    S1 = "1. بطاقة النازلة"
    code(S1, "عدد التوكنات المقيسة", len(toks), "len(text.split())")
    for f in ("نوع المدخل", "طبيعة النص", "محل النزاع الظاهر",
              "ما يجوز إنتاجه الآن", "ما لا يجوز إنتاجه الآن"):
        na(S1, f, "HUMAN_DECLARED_ONLY")

    # ── 2 بصمة القياس ───────────────────────────────────────────────────
    S2 = "2. بصمة القياس"
    code(S2, "taaqol_commit", pre["vendor_head"], "git rev-parse")
    code(S2, "pin_matches", pre["pin_matches"], "مقابلةُ التثبيت")
    code(S2, "sha256(INPUT_TEXT)", sha, "hashlib")
    code(S2, "python", pre["python"], "platform")
    code(S2, "platform", pre["platform"], "platform")
    code(S2, "utc_timestamp", pre["utc"], "datetime")
    code(S2, "corpus_id", corpus_id, "الوسيط")
    code(S2, "run_id", m["run"]["run_id"], "run_native_corpus")
    code(S2, "runner", "runtime.corpus_runner.run_native_corpus", "الاستيراد")
    na(S2, "MEASURED_BY", "HUMAN_DECLARED_ONLY")

    # ── 3 الجرد المغلق ──────────────────────────────────────────────────
    S3 = "3. الجرد المغلق المستعمل"
    for name in ("Rank", "ClosureState", "TransitionState",
                 "StageTransitionState"):
        code(S3, name, s[name], "سردُ أعضاء التعداد")
    code(S3, "FailureCode (الجرد كلُّه)", s["FailureCode_total"],
         "len(list(FailureCode))")
    code(S3, "FailureCode المستعمل في الخطوط", s["forbidden_failure_codes"],
         "ForbiddenLine.failure_code")

    # ── 4 المراحل الستّ عشرة ────────────────────────────────────────────
    S4 = "4. مصفوفة المراحل الست عشرة"
    first = m["run"]["token_results"][0]["records"]
    for i, st in enumerate(STAGES, 1):
        rec = next((r for r in first if r["stage_id"] == st), None)
        if rec is None:
            na(S4, f"{i}. {st}", "NOT_EMITTED_BY_RUNNER")
            continue
        code(S4, f"{i}. {st} · StageTransitionState",
             rec["transition_state"], "السجلّ")
        code(S4, f"{i}. {st} · الرتبة",
             f'{rec["rank_before"]}->{rec["rank_after"]}', "السجلّ")
        code(S4, f"{i}. {st} · hint",
             rec["remediation_hints"] or "—", "السجلّ")
        code(S4, f"{i}. {st} · residuals_after",
             rec["residuals_after"] or "—", "السجلّ")
        na(S4, f"{i}. {st} · ClosureState", "NOT_EMITTED_BY_RUNNER")
        na(S4, f"{i}. {st} · TransitionState", "NOT_EMITTED_BY_RUNNER")

    # ── 4.b شكل السجلّ وقواعده ──────────────────────────────────────────
    S4B = "4.b شكل سجل التنفيذ وقواعده"
    code(S4B, "حقولُ StageExecutionRecord", s["record_fields"],
         "__dataclass_fields__")
    for num, txt in s["rules"]:
        code(S4B, num, txt, "تعليقاتُ execution_record.py")

    # ── 5 الأثر والأدلّة ────────────────────────────────────────────────
    S5 = "5. سجل الأثر والأدلة"
    code(S5, "evidence_refs (عيّنة)", first[0]["evidence_refs"], "السجلّ")
    code(S5, "trace_entry_id (عيّنة)", first[0]["trace_entry_id"], "السجلّ")
    code(S5, "trace_parent_ids (عيّنة)", first[0]["trace_parent_ids"], "السجلّ")
    code(S5, "سجلّاتٌ بمرجع أثر",
         sum(1 for r in flat if r["trace_entry_id"]), "عدٌّ")
    na(S5, "سقفُ الرتبة لكلّ دليل", "NOT_EMITTED_BY_RUNNER")

    # ── 6 البقايا المقيسة ───────────────────────────────────────────────
    S6 = "6. البقايا المقيسة"
    for k, v in sorted(hints.items()):
        code(S6, f"hint · {k}", v, "عدٌّ من remediation_hints")
    for k, v in sorted(resid.items()):
        code(S6, f"residual · {k}", v, "عدٌّ من residuals_after")
    code(S6, "TOTAL_STAGE_RECORDS", len(flat), "عدٌّ")
    code(S6, "EMPTY_RESIDUAL_ROWS",
         sum(1 for r in flat if not r["residuals_after"]), "عدٌّ")
    na(S6, "HIDDEN_RESIDUALS", "NOT_EMITTED_BY_RUNNER")

    # ── 7 فجوة القانون والمشغّل ─────────────────────────────────────────
    S7 = "7. فجوة القانون والمشغّل"
    for name, imported in s["runner_imports"].items():
        code(S7, f"corpus_runner يستورد {name}", imported,
             "فحصُ مصدر المشغّل")
    na(S7, "حكم الوثيقة", "HUMAN_DECLARED_ONLY")

    # ── 8 الألفاظ ───────────────────────────────────────────────────────
    S8 = "8. مصفوفة الألفاظ: ما يجوز وما لا يجوز"
    for t in toks:
        code(S8, f'{t["token_id"]} · اللفظ', t["surface"], "التوكنات")
        code(S8, f'{t["token_id"]} · path_id', t["path"],
             "classify_token_paths")
        code(S8, f'{t["token_id"]} · confidence', t["confidence"],
             "classify_token_paths")
        na(S8, f'{t["token_id"]} · إفادة لغوية محتملة',
           "NOT_OPENED:VERBAL_MADLUL")
        na(S8, f'{t["token_id"]} · ما لا يجوز أخذه منه وحده',
           "HUMAN_DECLARED_ONLY")

    # ── 9 العلاقات ──────────────────────────────────────────────────────
    S9 = "9. العلاقات اللغوية والحدود"
    # كان هنا `RELATION_CLOSED_COUNT = 0` و`NO_ADJACENT_PAIR_CLOSURE = True`
    # مأخوذَين من أنّ المرحلة لم تُفتح — وذلك صفرٌ مُعَدٌّ لا مقيس، والقاعدةُ
    # `MEASURED_NOT_PRESET`: ما لم يُقَس لا يُطبع صفرًا. ومرحلةٌ لم تُفتح
    # لا تُنتج عددَ إغلاقاتٍ يساوي صفرًا، بل لا تُنتج عددًا أصلًا. وحالُ
    # المرحلة نفسُها مقيسةٌ فتُطبع، والاستنتاجُ منها للمالك.
    code(S9, "حالُ RELATION_CLOSURE",
         sorted(per_stage.get("RELATION_CLOSURE", {})) or "—", "السجلّ")
    na(S9, "RELATION_CLOSED_COUNT", "NOT_OPENED:RELATION_CLOSURE")
    na(S9, "NO_ADJACENT_PAIR_CLOSURE", "NOT_OPENED:RELATION_CLOSURE")
    na(S9, "صفوفُ العلاقات", "NOT_OPENED:RELATION")

    # ── 10 المنطوق والمفهوم ─────────────────────────────────────────────
    S10 = "10. المنطوق والمفهوم"
    for f in ("المنطوق", "مفهوم الموافقة", "مفهوم المخالفة"):
        na(S10, f, "NOT_OPENED:MUFRAD_DALALAH")

    # ── 11 الخطوط الممنوعة ──────────────────────────────────────────────
    S11 = "11. الخطوط المستقيمة الممنوعة"
    code(S11, "عدد الخطوط في السجل", len(s["forbidden_lines"]),
         "CANONICAL_REGISTRY")
    code(S11, "حقولُ كلّ خطّ", s["forbidden_line_fields"],
         "__dataclass_fields__")
    # الزوجُ (مصدر ⟶ هدف) لا يُعرِّف خطًّا: يتكرّر الزوجُ الواحد بجسرَين
    # مختلفَين. فيُعدّ الفرقُ ولا يُطوى، وإلا قُرئ عددُ الخطوط عددَ الأزواج.
    pairs = [(x["source"], x["target"]) for x in s["forbidden_lines"]]
    code(S11, "أزواجٌ (مصدر ⟶ هدف) متمايزة",
         f"{len(set(pairs))}/{len(pairs)}", "عدٌّ")
    for i, ln in enumerate(s["forbidden_lines"]):
        dup = pairs.count((ln["source"], ln["target"])) > 1
        tag = f' #{i}' if dup else ""
        code(S11, f'{ln["source"]} -> {ln["target"]}{tag}',
             f'{ln["failure_code"]} · {ln["required_bridge"]}',
             "CANONICAL_REGISTRY")
    na(S11, "هل اشتعلت في runner؟", "NOT_EMITTED_BY_RUNNER")

    # ── 12 المناط ───────────────────────────────────────────────────────
    na("12. مصفوفة المناط: أسئلة المالك", "أسئلةُ المناط", "NOT_OPENED:MANAT")

    # ── 12.b الغموض اللغويّ ─────────────────────────────────────────────
    na("12.b سجل الغموض اللغوي الموقوف على المالك", "مواضعُ الغموض",
       "OWNER_DECISION")

    # ── 13 التنزيل ──────────────────────────────────────────────────────
    S13 = "13. التنزيل وما سُحب"
    code(S13, "حالُ HUKM", sorted(per_stage.get("HUKM", {})) or "—", "السجلّ")
    code(S13, "حالُ TANZIL", sorted(per_stage.get("TANZIL", {})) or "—",
         "السجلّ")
    na(S13, "الدعاوى وأسبابُها", "HUMAN_DECLARED_ONLY")

    # ── 14 الحكم النهائي ────────────────────────────────────────────────
    S14 = "14. الحكم النهائي على الوثيقة"
    # التوزيعُ ليس خانةً واحدة. طُبع أوّلَ مرّةٍ `{'k': n}` — وهو تمثيلُ
    # بايثون لا قياس، وهو العيبُ نفسُه الذي وُجد في مولّد الطبقات الثلاث.
    # فيُفرَد كلُّ مفتاحٍ سطرًا باسمه ومقامِه، ويُمنع القاموسُ في `rendered`.
    for label, counter in (("STATE", states), ("HINT", hints),
                           ("RESIDUAL", resid), ("RANK", ranks)):
        if not counter:
            na(S14, f"{label}·—", "NOT_EMITTED_BY_RUNNER")
            continue
        for key, n in sorted(counter.items()):
            code(S14, f"{label}·{key}", f"{n}/{len(flat)}", "عدٌّ")
    code(S14, "CLAIM_PROJECT_FINISHED", "NO", "ثابتٌ في المولّد")
    for f in ("سبب", "شروط", "مانع"):
        na(S14, f, "HUMAN_DECLARED_ONLY")
    return C


# ── الحرّاس بعد البناء ──────────────────────────────────────────────────
def guard(cells: list[Cell], reference: Path, given: str = "") -> dict:
    """كلُّ حارسٍ يُسمّى، ويُطبع ما وجده — لا يُكتفى بمروره."""
    findings: dict = {}
    findings["COPIED_FROM_REFERENCE"] = copied_from_reference(
        cells, reference, given)
    findings["NO_EMPTY_CELL"] = [
        f"{c.section}/{c.field}" for c in cells
        if not c.reason and (c.value is None or c.value == "")]
    findings["REASON_IN_INVENTORY"] = [
        f"{c.section}/{c.field}={c.reason}" for c in cells
        if c.reason and c.reason.split(":")[0] not in REASONS]
    findings["NOT_OPENED_NAMES_A_STAGE"] = [
        c.reason for c in cells
        if c.reason.startswith("NOT_OPENED:") and c.reason[11:] not in STAGES]
    ref_heads = re.findall(r"^## (.+)$", reference.read_text(encoding="utf-8"),
                           re.M) if reference.is_file() else []
    ours = [s for s in dict.fromkeys(c.section for c in cells)
            if s != "رأس الوثيقة"]
    findings["SECTION_COUNT"] = {
        "reference": len(ref_heads), "generated": len(ours),
        "declared_in_prompt": 14,
        "note": ("المقيسُ هو الحاكم: عناوينُ المرجع تُعدّ ولا تُفترض"
                 if len(ref_heads) != 14 else "")}
    findings["FIELD_NAMES_MATCH"] = {
        "missing_here": [h for h in ref_heads if h not in ours],
        "extra_here": [o for o in ours if o not in ref_heads]}
    return findings


CONTAINER = re.compile(r"""\[['"]<|['"], ['"]<|Counter\(|\{'|<[a-z]+>\[['"]""")


def recount(doc: str, cells: list[Cell]) -> dict:
    """يعدّ الخانات من الوثيقة المطبوعة ثانيةً، ويقابلها بدفتر البناء.

    وهذا لا يُترك في جوف ``main``: فحصٌ لا يُستدعى وحدَه لا يُسمَّم، وحارسٌ
    لا يُسمَّم لا يُعرف أحيٌّ هو أم سطر. وقد كان هنا ``filled + (total -
    filled) == total`` — متطابقةٌ لا تكذب، تمرّ ولو ضاع نصفُ الأسطر.
    """
    rows = [ln for ln in doc.splitlines()
            if ln.startswith("| `") and not ln.startswith("| `الخانة")]
    na = [ln for ln in rows if NA in ln]
    filled = sum(1 for c in cells if c.from_code)
    return {"rows": len(rows), "not_available": len(na),
            "from_code": len(rows) - len(na),
            "closes": (len(rows) == len(cells)
                       and len(na) == len(cells) - filled
                       and len(rows) - len(na) == filled)}


def copied_from_reference(cells: list[Cell], reference: Path,
                          given: str) -> list[str]:
    """يردّ أسماءَ الخانات التي تطابق قيمتُها نصَّ المرجع حرفيًّا.

    «لا تنقل سطرًا من وثيقة المرجع إلى خانةٍ ولو كان صحيحًا». والمدخلُ
    يُستثنى باشتقاقه لا باسمه: نصُّ النازلة وبصمتُه يردان في المرجع لأنّ
    المالك وحّد أساسَ القياس على جملة الوثيقة، وهما يُقرآن من الملفّ
    ويُحسبان بـ`hashlib`. واستثناءٌ بقائمة أسماءٍ يُوسَّع كلّما سقط الحارس.
    """
    if not reference.is_file():
        return []
    text = reference.read_text(encoding="utf-8")
    exempt = {given, hashlib.sha256(given.encode()).hexdigest()}
    return [c.field for c in cells
            if isinstance(c.value, str) and len(c.value) > MIN_COPY_LEN
            and c.value in text and c.value not in exempt]


def render(cells: list[Cell], head: dict) -> str:
    out = [f"# {head['title']}", ""]
    out.append("```text")
    out.append("GENERATED_BY        = scripts/build_nazila_matrix.py")
    out.append("CONTENT_SOURCE      = CODE_ONLY")
    out.append("CLAIM_PROJECT_FINISHED = NO")
    out.append("```")
    out.append("")
    for section in dict.fromkeys(c.section for c in cells):
        rows = [c for c in cells if c.section == section]
        filled = sum(1 for c in rows if c.from_code)
        out.append(f"## {section}")
        out.append("")
        out.append(f"*من الكود {filled} · {NA} {len(rows) - filled}*")
        out.append("")
        out.append("| الخانة | القيمة | المصدر |")
        out.append("|---|---|---|")
        for c in rows:
            src = c.source if c.from_code else "—"
            out.append(f"| `{c.field}` | {c.rendered()} | {src} |")
        out.append("")
    return "\n".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text", default="inspection/case.txt")
    ap.add_argument("--reference", default="inspection/TAAQOL_NAZILA_MATRIX.md")
    ap.add_argument("--corpus-id", default="nazila")
    ap.add_argument("--out", default="output/nazila_from_code")
    a = ap.parse_args()

    pre = preflight()
    out = Path(a.out)
    if pre["verdict"] == "BLOCKED":
        print(f"BLOCKED_AT_PREFLIGHT: {json.dumps(pre, ensure_ascii=False)}")
        return 2
    out.mkdir(parents=True, exist_ok=True)
    (out / "00_preflight.json").write_text(
        json.dumps(pre, ensure_ascii=False, indent=1), encoding="utf-8")

    text = Path(a.text).read_text(encoding="utf-8").strip()
    sha = hashlib.sha256(text.encode()).hexdigest()
    m = measure(text, a.corpus_id)
    s = source_facts()
    (out / "01_run.json").write_text(
        json.dumps(m["run"], ensure_ascii=False, indent=1), encoding="utf-8")

    cells = build_cells(text, sha, a.corpus_id, m, s, pre)
    doc = render(cells, {"title": "مصفوفة تعقّل للنازلة — محتوًى من الكود وحدَه"})
    findings = guard(cells, Path(a.reference), text)
    hard = [k for k in ("NO_EMPTY_CELL", "REASON_IN_INVENTORY",
                        "NOT_OPENED_NAMES_A_STAGE",
                        "COPIED_FROM_REFERENCE") if findings[k]]
    if hard:
        print("OWNER_ALERT: "
              + json.dumps({k: findings[k] for k in hard}, ensure_ascii=False))
        return 3

    by_reason = Counter(c.reason for c in cells if c.reason)
    filled = sum(1 for c in cells if c.from_code)
    # الدفترُ يُقفل بعدٍّ ثانٍ من الوثيقة المطبوعة، لا بجمعٍ يعيد نفسَه.
    # كان هنا `filled + (total - filled) == total` — وهي متطابقةٌ لا تكذب
    # أبدًا، فتمرّ وإن ضاع نصفُ الخانات. والعدُّ الثاني يقرأ الأسطر:
    # كلُّ سطرٍ في جدولٍ هو خانة، وكلُّ سطرٍ فيه «غير متوفرة» له سببٌ.
    rc = recount(doc, cells)
    manifest = {
        "input_sha256": sha, "corpus_id": a.corpus_id,
        "cells_total": len(cells),
        "cells_from_code": filled,
        "cells_not_available": len(cells) - filled,
        "recount_from_document": rc,
        "ledger_closes": rc["closes"],
        "not_available_by_reason": dict(sorted(by_reason.items())),
        "guards": findings,
        "cells": [dataclasses.asdict(c) for c in cells],
    }
    (out / "02_field_manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    hits = CONTAINER.findall(doc)
    if hits:
        print(f"OWNER_ALERT: CONTAINER_SIGNATURE — {hits[:3]}")
        return 4
    (out / "03_matrix.md").write_text(doc, encoding="utf-8")

    print(f"CELLS_TOTAL        {len(cells)}")
    print(f"FROM_CODE          {filled}")
    print(f"NOT_AVAILABLE      {len(cells) - filled}")
    print(f"LEDGER_CLOSES      {manifest['ledger_closes']}")
    for r, n in sorted(by_reason.items()):
        print(f"   {r:34} {n}")
    sc = findings["SECTION_COUNT"]
    print(f"SECTION_COUNT      مرجع {sc['reference']} · مولَّد {sc['generated']}"
          f" · مذكورٌ في الأمر {sc['declared_in_prompt']}")
    fm = findings["FIELD_NAMES_MATCH"]
    print(f"FIELD_NAMES_MATCH  ناقصٌ هنا {len(fm['missing_here'])}"
          f" · زائدٌ هنا {len(fm['extra_here'])}")
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
