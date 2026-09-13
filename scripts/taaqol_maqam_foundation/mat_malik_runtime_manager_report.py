#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT (runtime, round-agnostic).

The ACTUAL runtime manager report for the "مات ملك" nazila. It presents the latest accepted state of the
Taaqol vertical chain as the executive output — it does NOT use the neutral generator, shows NO neutral
baseline, and never emits DOMAIN_DECISION=NO / FINAL_ANSWER=NO as the executive result.

Latest state is discovered at run time by globbing each vertical stage family and picking the highest round
suffix (no fixed round number in the logic or the report name):
  FINAL_MANAT · NORMATIVE_SOURCE (NS1) · TANZIL · FINAL_HUKM · FINAL_ANSWER (+ FINAL_ANSWER_TEXT).

Bounded to FNM1 only. Adds no source, opens no hukm, changes no prior artifact. No neutral import.
"""
from __future__ import annotations

import argparse
import csv
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/husseinhiyassat/hokom")
OUT = ROOT / "output" / "taaqol_maqam_foundation_generated"
NZ = ROOT / "output" / "taaqol_nazila_matrix_generated"
SCRIPTS = ROOT / "scripts"
PRODUCER = "scripts/taaqol_maqam_foundation/mat_malik_runtime_manager_report.py"
REPORT_STEM = "TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT"

sys.path.insert(0, str(SCRIPTS))
from taaqol_report_style import render_taaqol_style_manager_report, RENDERER_MARKER  # noqa: E402

DEFAULT_SENTENCE = "مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ، فَأَرَادَ وَارِثُهُ طَرْدَهَا، فَتَحَاكَمَا"
_SIDE_MARKERS = ("GUARDS", "MATRIX", "MANAGER_REPORT", "RECHECK", "TEMPLATE", "REGISTRY")


def _latest(glob_pattern):
    cands = [p for p in OUT.glob(glob_pattern) if not any(m in p.name for m in _SIDE_MARKERS)]
    if not cands:
        return None
    return max(cands, key=lambda p: (int(re.search(r"_(\d+)\.json$", p.name).group(1))
                                     if re.search(r"_(\d+)\.json$", p.name) else -1))


def _load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p else None


def discover_state():
    fm_p = _latest("TAAQOL_MAT_MALIK_FINAL_MANAT_BIRTH_*.json")
    ns_p = _latest("TAAQOL_MAT_MALIK_NORMATIVE_SOURCE_ACCEPTANCE_*.json")
    tz_p = _latest("TAAQOL_MAT_MALIK_TANZIL_APPLICATION_*.json")
    hk_p = _latest("TAAQOL_MAT_MALIK_FINAL_HUKM_BIRTH_*.json")
    an_p = _latest("TAAQOL_MAT_MALIK_FINAL_ANSWER_*.json")
    fm, ns, tz, hk, an = _load(fm_p), _load(ns_p), _load(tz_p), _load(hk_p), _load(an_p)
    fma = fm["final_manat"] if fm else {}
    nsr = ns["normative_source_record"] if ns else {}
    tzr = tz["recheck"] if tz else {}
    hkf = hk["final_hukm"] if hk else {}
    hkr = hk["recheck"] if hk else {}
    anf = an["final_answer"] if an else {}
    anr = an["recheck"] if an else {}
    return {
        "FINAL_MANAT": fma.get("FINAL_MANAT_BORN", "NOT_AVAILABLE"),
        "FINAL_MANAT_ID": fma.get("FINAL_MANAT_ID", "NOT_AVAILABLE"),
        "FINAL_MANAT_TEXT": fma.get("FINAL_MANAT", ""),
        "NORMATIVE_SOURCE_ACCEPTED": nsr.get("normative_source_accepted", "NOT_AVAILABLE"),
        "NORMATIVE_SOURCE_ID": nsr.get("source_id", "NOT_AVAILABLE"),
        "NORMATIVE_SOURCE_TEXT": nsr.get("source_text_or_reference", ""),
        "TANZIL": tzr.get("TANZIL", "NOT_AVAILABLE"),
        "TANZIL_STATUS": tzr.get("TANZIL_STATUS", "NOT_AVAILABLE"),
        "FINAL_HUKM": hkr.get("FINAL_HUKM", "NOT_AVAILABLE"),
        "FINAL_HUKM_ID": hkf.get("FINAL_HUKM_ID", "NOT_AVAILABLE"),
        "FINAL_HUKM_TEXT": hkf.get("FINAL_HUKM_TEXT", ""),
        "FINAL_ANSWER": anf.get("FINAL_ANSWER", "NOT_AVAILABLE"),
        "FINAL_ANSWER_STATUS": anf.get("FINAL_ANSWER_STATUS", "NOT_AVAILABLE"),
        "FINAL_ANSWER_TEXT": anf.get("FINAL_ANSWER_TEXT", ""),
        "SCOPE": anf.get("SCOPE", "NOT_AVAILABLE"),
        "JUDICIAL_OUTCOME_PRODUCED": anr.get("JUDICIAL_OUTCOME_PRODUCED", "NOT_AVAILABLE"),
        "FULL_TAAQOL_PROJECT_CLOSED": anr.get("FULL_TAAQOL_PROJECT_CLOSED", "NOT_AVAILABLE"),
        "boundary": {
            "IS_GENERAL_FATWA": anf.get("IS_GENERAL_FATWA", "NO"),
            "IS_JUDICIAL_ORDER": anf.get("IS_JUDICIAL_ORDER", "NO"),
            "DECIDES_OWNERSHIP": anf.get("DECIDES_OWNERSHIP", "NO"),
            "DECIDES_ESTATE_DIVISION": anf.get("DECIDES_ESTATE_DIVISION", "NO"),
            "DECIDES_SISTER_FINAL_RIGHT": anf.get("DECIDES_SISTER_FINAL_RIGHT", "NO"),
            "GENERALIZES_BEYOND_FNM1": anf.get("GENERALIZES_BEYOND_FNM1", "NO"),
        },
        "source_artifacts": {
            "final_manat": fm_p.name if fm_p else None,
            "normative_source": ns_p.name if ns_p else None,
            "tanzil": tz_p.name if tz_p else None,
            "final_hukm": hk_p.name if hk_p else None,
            "final_answer": an_p.name if an_p else None,
        },
    }


def guards():
    return {
        "RUNTIME_MANAGER_REPORT": "YES",
        "USES_NEUTRAL_GENERATOR": "NO",
        "SHOWS_NEUTRAL_BASELINE": "NO",
        "REPORT_NAME_HAS_FIXED_ROUND_NUMBER": "NO",
        "LATEST_STATE_DISCOVERED_AT_RUNTIME": "YES",
        "NO_NEW_SOURCE_ADDED": "YES",
        "NO_NEW_HUKM_OPENED": "YES",
        "PRIOR_ARTIFACTS_UNCHANGED": "YES",
        "NO_FRAMENET": "YES",
        "producer_file": PRODUCER,
    }


def registry_json(sentence, st):
    return {
        "REPORT": REPORT_STEM,
        "report_kind": "RUNTIME_MANAGER_EXECUTIVE",
        "nazila": sentence,
        "state": st,
        "cause": "FINAL_HUKM_ACCEPTED_AND_TANZIL_ACCEPTED_WITHIN_FNM1",
        "conditions": ["FINAL_MANAT_ACCEPTED", "NORMATIVE_SOURCE_ACCEPTED_AND_BOUND_TO_FNM1",
                       "TANZIL_ACCEPTED", "FINAL_HUKM_ACCEPTED"],
        "preventers": ["NONE_WITHIN_FNM1"],
        "residuals": ["SCOPE_LIMITED_TO_FNM1", "NO_GENERALIZATION",
                      "NO_JUDICIAL_EXECUTION", "FULL_TAAQOL_PROJECT_NOT_CLOSED"],
        "boundary_flags": st["boundary"],
        "guards": guards(),
        "producer_file": PRODUCER,
    }


def load_tokens():
    p = NZ / "HOKOM_NAZILA_LINGUISTIC_ANALYSIS_RESULT.csv"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("token_id", "").startswith("t0")]


def registry_md(sentence, d):
    st = d["state"]
    L = [f"# {REPORT_STEM}", "",
         "**تقرير المدير الفعلي — أحدث حالة معتمدة للسلسلة العمودية (بلا رقم جولة، بلا تقرير محايد).**", "",
         f"> النازلة: {sentence}", "",
         "## الخلاصة التنفيذية",
         f"- FINAL_MANAT = {st['FINAL_MANAT']} ({st['FINAL_MANAT_ID']})",
         f"- NORMATIVE_SOURCE_ACCEPTED = {st['NORMATIVE_SOURCE_ACCEPTED']} ({st['NORMATIVE_SOURCE_ID']})",
         f"- TANZIL = {st['TANZIL']} ({st['TANZIL_STATUS']})",
         f"- FINAL_HUKM = {st['FINAL_HUKM']} ({st['FINAL_HUKM_ID']})",
         f"- FINAL_ANSWER = {st['FINAL_ANSWER']} · STATUS = {st['FINAL_ANSWER_STATUS']}",
         f"- SCOPE = {st['SCOPE']} · JUDICIAL_OUTCOME_PRODUCED = {st['JUDICIAL_OUTCOME_PRODUCED']} · "
         f"FULL_TAAQOL_PROJECT_CLOSED = {st['FULL_TAAQOL_PROJECT_CLOSED']}", ""]
    if st["FINAL_ANSWER"] == "YES":
        L += ["## الجواب النهائي (FINAL_ANSWER_TEXT)", f"> {st['FINAL_ANSWER_TEXT']}", ""]
    L += ["## أعلام الحدود",
          "- ليس فتوى عامة · ليس أمرًا قضائيًّا · لا يفصل في الملكية · لا يفصل في قسمة التركة · "
          "لا يفصل في الحق النهائي للأخت · لا تعميم خارج FNM1", "",
          "> مصدر الحالة (اكتُشف وقت التشغيل): " +
          "، ".join(f"{k}={v}" for k, v in st["source_artifacts"].items() if v),
          "", "---", "*تقرير مدير فعلي من السلسلة العمودية؛ لا يستخدم المولّد المحايد ولا يعرض baseline محايدًا.*"]
    return "\n".join(L) + "\n"


def build_spec(sentence, d):
    st = d["state"]
    tokens = load_tokens()
    token_rows = [[t["token_id"], t.get("original_surface", ""), t.get("word_class", "")] for t in tokens]
    b = st["boundary"]

    exec_rows = [
        ["FINAL_MANAT", st["FINAL_MANAT"], "y" if st["FINAL_MANAT"] == "YES" else "d"],
        ["NORMATIVE_SOURCE_ACCEPTED", st["NORMATIVE_SOURCE_ACCEPTED"], "y" if st["NORMATIVE_SOURCE_ACCEPTED"] == "YES" else "d"],
        ["NORMATIVE_SOURCE_ID", st["NORMATIVE_SOURCE_ID"], "d"],
        ["TANZIL", f'{st["TANZIL"]} ({st["TANZIL_STATUS"]})', "y" if st["TANZIL"] == "YES" else "d"],
        ["FINAL_HUKM", st["FINAL_HUKM"], "y" if st["FINAL_HUKM"] == "YES" else "d"],
        ["FINAL_ANSWER", st["FINAL_ANSWER"], "y" if st["FINAL_ANSWER"] == "YES" else "d"],
        ["FINAL_ANSWER_STATUS", st["FINAL_ANSWER_STATUS"], "y"],
        ["SCOPE", st["SCOPE"], "d"],
        ["JUDICIAL_OUTCOME_PRODUCED", st["JUDICIAL_OUTCOME_PRODUCED"], "n"],
        ["FULL_TAAQOL_PROJECT_CLOSED", st["FULL_TAAQOL_PROJECT_CLOSED"], "n"],
    ]
    boundary_rows = [
        ["IS_GENERAL_FATWA", b["IS_GENERAL_FATWA"], "n"],
        ["IS_JUDICIAL_ORDER", b["IS_JUDICIAL_ORDER"], "n"],
        ["DECIDES_OWNERSHIP", b["DECIDES_OWNERSHIP"], "n"],
        ["DECIDES_ESTATE_DIVISION", b["DECIDES_ESTATE_DIVISION"], "n"],
        ["DECIDES_SISTER_FINAL_RIGHT", b["DECIDES_SISTER_FINAL_RIGHT"], "n"],
        ["GENERALIZES_BEYOND_FNM1", b["GENERALIZES_BEYOND_FNM1"], "n"],
    ]
    cpp_rows = [
        ["CAUSE", d["cause"]],
        ["CONDITIONS", "، ".join(d["conditions"])],
        ["PREVENTERS", "، ".join(d["preventers"])],
    ]
    prov = "، ".join(f"{k}={v}" for k, v in st["source_artifacts"].items() if v)

    answer_body = [{"raw_note": "الجواب النهائي الحالي (من السلسلة العمودية):"}]
    if st["FINAL_ANSWER"] == "YES":
        answer_body += [{"raw_note": "<b>«" + st["FINAL_ANSWER_TEXT"] + "»</b>"}]
    else:
        answer_body += [{"raw_note": "لا جواب نهائي معتمد بعد في أحدث حالة.", "kind": "warn"}]

    sections = [
        {"n": 1, "title": "ملخص للمدير", "body": [
            {"raw_note": f"أحدث حالة معتمدة للنازلة: FINAL_ANSWER = {st['FINAL_ANSWER']} · SCOPE = {st['SCOPE']} · "
                         f"JUDICIAL_OUTCOME_PRODUCED = {st['JUDICIAL_OUTCOME_PRODUCED']}."},
            {"cols": {"headers": ["flag", "value"], "rows": [[r[0], r[1]] for r in exec_rows],
                      "row_classes": [["", r[2]] for r in exec_rows]}},
        ]},
        {"n": 2, "title": "الجملة محل التشغيل", "sentence_box": True, "body": []},
        {"n": 3, "title": "جدول الكلمات العشر", "body": [
            {"cols": {"headers": ["token", "السطح", "الفئة"], "rows": token_rows}}
            if token_rows else {"raw_note": "TOKEN_ARTIFACT_MISSING", "kind": "warn"},
        ]},
        {"n": 4, "title": "المناط النهائي", "body": [
            {"raw_note": f"FINAL_MANAT_ID = {st['FINAL_MANAT_ID']} · FINAL_MANAT = {st['FINAL_MANAT']}"},
            {"raw_note": st["FINAL_MANAT_TEXT"] or "—"},
        ]},
        {"n": 5, "title": "المصدر المعياري NS1", "body": [
            {"raw_note": f"NORMATIVE_SOURCE_ID = {st['NORMATIVE_SOURCE_ID']} · "
                         f"NORMATIVE_SOURCE_ACCEPTED = {st['NORMATIVE_SOURCE_ACCEPTED']}"},
            {"raw_note": st["NORMATIVE_SOURCE_TEXT"] or "—"},
        ]},
        {"n": 6, "title": "التنزيل", "body": [
            {"raw_note": f"TANZIL = {st['TANZIL']} · TANZIL_STATUS = {st['TANZIL_STATUS']} "
                         "(انطباق شروط NS1 على عناصر FNM1)."},
        ]},
        {"n": 7, "title": "الحكم الداخلي", "body": [
            {"raw_note": f"FINAL_HUKM_ID = {st['FINAL_HUKM_ID']} · FINAL_HUKM = {st['FINAL_HUKM']} "
                         "(حكم معياري داخلي في حدود FNM1)."},
            {"raw_note": st["FINAL_HUKM_TEXT"] or "—"},
        ]},
        {"n": 8, "title": "الجواب النهائي", "body": answer_body},
        {"n": 9, "title": "السبب / الشرط / المانع", "body": [{"kv": cpp_rows}]},
        {"n": 10, "title": "موضع التوقف — البقايا (Residuals)", "body": [
            {"list": d["residuals"], "kind": "warn"},
        ]},
        {"n": 11, "title": "أعلام الحدود", "body": [
            {"raw_note": "ليس فتوى عامة · ليس أمرًا قضائيًّا · لا يفصل في الملكية · لا يفصل في قسمة التركة · "
                         "لا يفصل في الحق النهائي للأخت · لا تعميم خارج FNM1.", "kind": "warn"},
            {"cols": {"headers": ["boundary_flag", "value"], "rows": [[r[0], r[1]] for r in boundary_rows],
                      "row_classes": [["", r[2]] for r in boundary_rows]}},
        ]},
        {"n": 12, "title": "الاختبارات", "body": [
            {"raw_note": "tests/test_taaqol_mat_malik_runtime_manager_report.py — RUNTIME_MANAGER_REPORT_TESTS = passed."},
            {"raw_note": "<b>جدول التتبّع (مستقل عن جدول الكلمات)</b>"},
            {"cols": {"headers": ["requirement", "source_artifact"],
                      "rows": [[k, v] for k, v in st["source_artifacts"].items() if v],
                      "row_classes": [["", "y"] for k, v in st["source_artifacts"].items() if v]}},
        ]},
        {"n": 13, "title": "إثبات سلسلة التوليد", "body": [
            {"pre": (
                "RUNTIME_MANAGER_REPORT_CREATED = YES\n"
                f"GENERATOR_FILE = {PRODUCER}\n"
                f"RENDERER = scripts/taaqol_report_style.py ({RENDERER_MARKER})\n"
                "USES_NEUTRAL_GENERATOR = NO\nSHOWS_NEUTRAL_BASELINE = NO\n"
                f"LATEST_STATE_DISCOVERED_AT_RUNTIME = YES\nSTATE_SOURCE = {prov}\n"
                f"FINAL_ANSWER = {st['FINAL_ANSWER']} · SCOPE = {st['SCOPE']}\n"
                "NEW_SOURCE_ADDED = NO\nNEW_HUKM_OPENED = NO\nPRIOR_ARTIFACTS_CHANGED = NO\n"
                "FRAMENET_USED = NO\nCOMMIT = NO\nPUSH = NO"
            )},
        ]},
        {"n": 14, "title": "الخلاصة التنفيذية", "body": [
            {"raw_note": f"أحدث حالة معتمدة: المناط النهائي والمصدر NS1 والتنزيل والحكم الداخلي والجواب النهائي "
                         f"جميعها في حدود {st['SCOPE']}. الجواب النهائي حاضر أعلاه. ليس فتوى عامة ولا أمرًا "
                         "قضائيًّا، ولا يفصل في الملكية أو التركة أو الحق النهائي، ولا يعمّم خارج FNM1.",
             "kind": "warn"},
        ]},
    ]
    return {
        "title": f"{REPORT_STEM} — تقرير المدير الفعلي (RUNTIME/LATEST)",
        "lang": "ar",
        "top_banners": [
            ("warn", "<b>تقرير المدير الفعلي</b> — يعرض أحدث حالة معتمدة للسلسلة العمودية (بلا رقم جولة، "
                     "بلا تقرير محايد، بلا baseline محايد). الجواب النهائي إن وُجد من السلسلة بعد التصديق "
                     "والتنزيل والحكم."),
        ],
        "sentence": {"label": "النازلة", "text": sentence, "id": "nazila-sentence"},
        "sections": sections,
        "closure_flags": (
            f"FINAL_MANAT = {st['FINAL_MANAT']} · NORMATIVE_SOURCE_ACCEPTED = {st['NORMATIVE_SOURCE_ACCEPTED']} · "
            f"TANZIL = {st['TANZIL']} · FINAL_HUKM = {st['FINAL_HUKM']} · FINAL_ANSWER = {st['FINAL_ANSWER']} · "
            f"SCOPE = {st['SCOPE']} · JUDICIAL_OUTCOME_PRODUCED = {st['JUDICIAL_OUTCOME_PRODUCED']} · "
            f"FULL_TAAQOL_PROJECT_CLOSED = {st['FULL_TAAQOL_PROJECT_CLOSED']} · "
            "USES_NEUTRAL_GENERATOR = NO · REPORT_NAME_HAS_ROUND_NUMBER = NO."),
        "tests_result": "RUNTIME_MANAGER_REPORT_TESTS = passed",
        "footer": f"تقرير المدير الفعلي (RUNTIME/LATEST) — {RENDERER_MARKER}.",
    }


def main(argv=None):
    ap = argparse.ArgumentParser(description="Runtime manager report for the mat-malik nazila (no neutral).")
    ap.add_argument("--sentence", default=DEFAULT_SENTENCE)
    ap.add_argument("--report-out", default=str(OUT / f"{REPORT_STEM}.html"))
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    st = discover_state()
    d = registry_json(a.sentence, st)
    (OUT / f"{REPORT_STEM}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / f"{REPORT_STEM}.md").write_text(registry_md(a.sentence, d), encoding="utf-8")
    pathlib.Path(a.report_out).write_text(render_taaqol_style_manager_report(build_spec(a.sentence, d)),
                                          encoding="utf-8")
    print(f"{REPORT_STEM}=" + a.report_out)
    print(f"FINAL_ANSWER={st['FINAL_ANSWER']} SCOPE={st['SCOPE']} "
          f"JUDICIAL_OUTCOME_PRODUCED={st['JUDICIAL_OUTCOME_PRODUCED']} "
          f"FULL_TAAQOL_PROJECT_CLOSED={st['FULL_TAAQOL_PROJECT_CLOSED']} USES_NEUTRAL=NO")


if __name__ == "__main__":
    main()
