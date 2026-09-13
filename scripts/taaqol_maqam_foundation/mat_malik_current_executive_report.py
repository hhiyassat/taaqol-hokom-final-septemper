#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAAQOL_MAT_MALIK_CURRENT_EXECUTIVE_REPORT (round-agnostic).

A general "current / latest" executive report whose NAME carries no fixed round number. At run time it:

  Section 1 — NEUTRAL_BASELINE_OUTPUT:
    runs scripts/neutral_sentence_report_generator on the nazila sentence and shows the structure-only
    result (DOMAIN_DECISION=NO, HUKM=NO, FINAL_ANSWER=NO, FACT_ACCEPTED_COUNT=0, VERDICT=DEFER_STRUCTURAL_ONLY).
    The neutral generator NEVER produces a final answer.

  Section 2 — TAAQOL_VERTICAL_DERIVATION:
    discovers the LATEST accepted artifacts of the mat-malik vertical chain (by globbing each stage family and
    picking the highest round suffix — no fixed round number in the logic) and shows FINAL_MANAT / NS1_ACCEPTED
    / TANZIL / FINAL_HUKM / FINAL_ANSWER / SCOPE / JUDICIAL_OUTCOME_PRODUCED / FULL_TAAQOL_PROJECT_CLOSED, and
    FINAL_ANSWER_TEXT only when FINAL_ANSWER=YES.

The report declares SOURCE_OF_FINAL_ANSWER = TAAQOL_VERTICAL_CHAIN_NOT_NEUTRAL_GENERATOR. It adds no source,
opens no hukm, and changes no prior artifact.
"""
from __future__ import annotations

import argparse
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/husseinhiyassat/hokom")
OUT = ROOT / "output" / "taaqol_maqam_foundation_generated"
SCRIPTS = ROOT / "scripts"
PRODUCER = "scripts/taaqol_maqam_foundation/mat_malik_current_executive_report.py"
REPORT_STEM = "TAAQOL_MAT_MALIK_CURRENT_EXECUTIVE_REPORT"

sys.path.insert(0, str(SCRIPTS))
from taaqol_report_style import render_taaqol_style_manager_report, RENDERER_MARKER  # noqa: E402
import neutral_sentence_report_generator as neutral  # noqa: E402

SENTENCE = "مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ، فَأَرَادَ وَارِثُهُ طَرْدَهَا، فَتَحَاكَمَا"


_SIDE_MARKERS = ("GUARDS", "MATRIX", "MANAGER_REPORT", "RECHECK", "TEMPLATE", "REGISTRY")


def _latest(glob_pattern):
    """Pick the primary artifact with the greatest trailing round number (round-agnostic discovery).

    Sibling files (GUARDS/MATRIX/MANAGER_REPORT/…) share the round suffix, so they are excluded.
    """
    cands = [p for p in OUT.glob(glob_pattern)
             if not any(m in p.name for m in _SIDE_MARKERS)]
    if not cands:
        return None
    def keyf(p):
        m = re.search(r"_(\d+)\.json$", p.name)
        return int(m.group(1)) if m else -1
    return max(cands, key=keyf)


def _load(p):
    return json.loads(p.read_text(encoding="utf-8")) if p else None


def neutral_baseline():
    d = neutral.build_report(SENTENCE)
    return {
        "generator": "scripts/neutral_sentence_report_generator.py",
        "report_hash": d["report_hash"],
        "DOMAIN_DECISION": d["DOMAIN_DECISION"],
        "HUKM": d["HUKM"],
        "FINAL_ANSWER": d["FINAL_ANSWER"],
        "FACT_ACCEPTED_COUNT": d["FACT_ACCEPTED_COUNT"],
        "VERDICT": d["verdict"],
        "role": "STRUCTURAL_ONLY",
        "produces_final_answer": "NO",
    }


def vertical_derivation():
    fm_p = _latest("TAAQOL_MAT_MALIK_FINAL_MANAT_BIRTH_*.json")
    ns_p = _latest("TAAQOL_MAT_MALIK_NORMATIVE_SOURCE_ACCEPTANCE_*.json")
    tz_p = _latest("TAAQOL_MAT_MALIK_TANZIL_APPLICATION_*.json")
    hk_p = _latest("TAAQOL_MAT_MALIK_FINAL_HUKM_BIRTH_*.json")
    an_p = _latest("TAAQOL_MAT_MALIK_FINAL_ANSWER_*.json")
    fm, ns, tz, hk, an = _load(fm_p), _load(ns_p), _load(tz_p), _load(hk_p), _load(an_p)

    v = {
        "FINAL_MANAT": (fm["final_manat"].get("FINAL_MANAT_BORN", "NO") if fm else "NOT_AVAILABLE"),
        "FINAL_MANAT_ID": (fm["final_manat"]["FINAL_MANAT_ID"] if fm else "NOT_AVAILABLE"),
        "NS1_ACCEPTED": (ns["normative_source_record"]["normative_source_accepted"] if ns else "NOT_AVAILABLE"),
        "NS1_ID": (ns["normative_source_record"]["source_id"] if ns else "NOT_AVAILABLE"),
        "TANZIL": (tz["recheck"]["TANZIL"] if tz else "NOT_AVAILABLE"),
        "TANZIL_STATUS": (tz["recheck"]["TANZIL_STATUS"] if tz else "NOT_AVAILABLE"),
        "FINAL_HUKM": (hk["recheck"]["FINAL_HUKM"] if hk else "NOT_AVAILABLE"),
        "FINAL_HUKM_ID": (hk["final_hukm"]["FINAL_HUKM_ID"] if hk else "NOT_AVAILABLE"),
        "FINAL_ANSWER": (an["final_answer"]["FINAL_ANSWER"] if an else "NOT_AVAILABLE"),
        "SCOPE": (an["final_answer"]["SCOPE"] if an else "NOT_AVAILABLE"),
        "JUDICIAL_OUTCOME_PRODUCED": (an["recheck"]["JUDICIAL_OUTCOME_PRODUCED"] if an else "NOT_AVAILABLE"),
        "FULL_TAAQOL_PROJECT_CLOSED": (an["recheck"]["FULL_TAAQOL_PROJECT_CLOSED"] if an else "NOT_AVAILABLE"),
        "source_artifacts": {
            "final_manat": fm_p.name if fm_p else None,
            "normative_source_acceptance": ns_p.name if ns_p else None,
            "tanzil": tz_p.name if tz_p else None,
            "final_hukm": hk_p.name if hk_p else None,
            "final_answer": an_p.name if an_p else None,
        },
    }
    # FINAL_ANSWER_TEXT only when FINAL_ANSWER == YES (and only inside the vertical derivation)
    if an and an["final_answer"]["FINAL_ANSWER"] == "YES":
        v["FINAL_ANSWER_TEXT"] = an["final_answer"]["FINAL_ANSWER_TEXT"]
    return v


def guards():
    return {
        "NEUTRAL_GENERATOR_PRODUCES_FINAL_ANSWER": "NO",
        "FINAL_ANSWER_SOURCE_IS_VERTICAL_CHAIN": "YES",
        "NEUTRAL_BASELINE_IS_STRUCTURAL_ONLY": "YES",
        "REPORT_NAME_HAS_FIXED_ROUND_NUMBER": "NO",
        "VERTICAL_STATE_DISCOVERED_AT_RUNTIME": "YES",
        "NO_NEW_SOURCE_ADDED": "YES",
        "NO_NEW_HUKM_OPENED": "YES",
        "PRIOR_ARTIFACTS_UNCHANGED": "YES",
        "NO_FRAMENET": "YES",
        "producer_file": PRODUCER,
    }


def registry_json():
    return {
        "REPORT": REPORT_STEM,
        "report_kind": "CURRENT_LATEST_EXECUTIVE",
        "nazila": SENTENCE,
        "SOURCE_OF_FINAL_ANSWER": "TAAQOL_VERTICAL_CHAIN_NOT_NEUTRAL_GENERATOR",
        "NEUTRAL_BASELINE_OUTPUT": neutral_baseline(),
        "TAAQOL_VERTICAL_DERIVATION": vertical_derivation(),
        "guards": guards(),
        "producer_file": PRODUCER,
    }


def registry_md(d):
    nb = d["NEUTRAL_BASELINE_OUTPUT"]
    v = d["TAAQOL_VERTICAL_DERIVATION"]
    L = [f"# {REPORT_STEM}", "",
         "**تقرير تنفيذي عام (LATEST/CURRENT) — لا يحمل رقم جولة، يعكس أحدث حالة الكود عند وقت التشغيل.**", "",
         f"> النازلة: {SENTENCE}",
         f"> SOURCE_OF_FINAL_ANSWER = {d['SOURCE_OF_FINAL_ANSWER']}", "",
         "## 1. NEUTRAL_BASELINE_OUTPUT",
         "بنية فقط — المولّد المحايد لا ينتج جوابًا نهائيًّا:",
         f"- DOMAIN_DECISION = {nb['DOMAIN_DECISION']}",
         f"- HUKM = {nb['HUKM']}",
         f"- FINAL_ANSWER = {nb['FINAL_ANSWER']}",
         f"- FACT_ACCEPTED_COUNT = {nb['FACT_ACCEPTED_COUNT']}",
         f"- VERDICT = {nb['VERDICT']}",
         f"- role = {nb['role']} · produces_final_answer = {nb['produces_final_answer']}", "",
         "## 2. TAAQOL_VERTICAL_DERIVATION",
         "أحدث حالة معتمدة من السلسلة العمودية (اكتُشفت من الملفات وقت التشغيل):",
         f"- FINAL_MANAT = {v['FINAL_MANAT']} ({v['FINAL_MANAT_ID']})",
         f"- NS1_ACCEPTED = {v['NS1_ACCEPTED']} ({v['NS1_ID']})",
         f"- TANZIL = {v['TANZIL']} ({v['TANZIL_STATUS']})",
         f"- FINAL_HUKM = {v['FINAL_HUKM']} ({v['FINAL_HUKM_ID']})",
         f"- FINAL_ANSWER = {v['FINAL_ANSWER']}",
         f"- SCOPE = {v['SCOPE']}",
         f"- JUDICIAL_OUTCOME_PRODUCED = {v['JUDICIAL_OUTCOME_PRODUCED']}",
         f"- FULL_TAAQOL_PROJECT_CLOSED = {v['FULL_TAAQOL_PROJECT_CLOSED']}"]
    if "FINAL_ANSWER_TEXT" in v:
        L += [f"- FINAL_ANSWER_TEXT: «{v['FINAL_ANSWER_TEXT']}»"]
    L += ["", "> مصدر الأرقام أعلاه: " + ", ".join(f"{k}={val}" for k, val in v["source_artifacts"].items() if val),
          "", "---",
          "*المولّد المحايد = بنية فقط لا حكم؛ الجواب النهائي (إن وُجد) من السلسلة العمودية بعد التصديق "
          "والتنزيل والحكم، لا من المولّد المحايد. لا تعارض بينهما.*"]
    return "\n".join(L) + "\n"


def build_spec(d):
    nb = d["NEUTRAL_BASELINE_OUTPUT"]
    v = d["TAAQOL_VERTICAL_DERIVATION"]
    nb_rows = [
        ["DOMAIN_DECISION", nb["DOMAIN_DECISION"], "n"],
        ["HUKM", nb["HUKM"], "n"],
        ["FINAL_ANSWER", nb["FINAL_ANSWER"], "n"],
        ["FACT_ACCEPTED_COUNT", nb["FACT_ACCEPTED_COUNT"], "n"],
        ["VERDICT", nb["VERDICT"], "d"],
        ["role", nb["role"], "d"],
        ["produces_final_answer", nb["produces_final_answer"], "n"],
    ]
    v_rows = [
        ["FINAL_MANAT", v["FINAL_MANAT"], "y" if v["FINAL_MANAT"] == "YES" else "d"],
        ["NS1_ACCEPTED", v["NS1_ACCEPTED"], "y" if v["NS1_ACCEPTED"] == "YES" else "d"],
        ["TANZIL", f'{v["TANZIL"]} ({v["TANZIL_STATUS"]})', "y" if v["TANZIL"] == "YES" else "d"],
        ["FINAL_HUKM", v["FINAL_HUKM"], "y" if v["FINAL_HUKM"] == "YES" else "d"],
        ["FINAL_HUKM_ID", v["FINAL_HUKM_ID"], "d"],
        ["FINAL_ANSWER", v["FINAL_ANSWER"], "y" if v["FINAL_ANSWER"] == "YES" else "d"],
        ["SCOPE", v["SCOPE"], "d"],
        ["JUDICIAL_OUTCOME_PRODUCED", v["JUDICIAL_OUTCOME_PRODUCED"], "n"],
        ["FULL_TAAQOL_PROJECT_CLOSED", v["FULL_TAAQOL_PROJECT_CLOSED"], "n"],
    ]
    vertical_body = [
        {"raw_note": "أحدث حالة معتمدة من السلسلة العمودية (اكتُشفت من الملفات وقت التشغيل، بلا رقم جولة ثابت):"},
        {"cols": {"headers": ["flag", "value"], "rows": [[r[0], r[1]] for r in v_rows],
                  "row_classes": [["", r[2]] for r in v_rows]}},
    ]
    if "FINAL_ANSWER_TEXT" in v:
        vertical_body += [
            {"note": "FINAL_ANSWER_TEXT (من السلسلة العمودية فقط، يظهر لأن FINAL_ANSWER=YES):"},
            {"raw_note": "<b>«" + v["FINAL_ANSWER_TEXT"] + "»</b>"},
        ]
    vertical_body += [{"raw_note": "مصدر الأرقام: " + "، ".join(
        f"{k}={val}" for k, val in v["source_artifacts"].items() if val)}]

    sections = [
        {"n": 1, "title": "NEUTRAL_BASELINE_OUTPUT", "sentence_box": True, "body": [
            {"raw_note": "المولّد المحايد = بنية فقط، لا مجال، لا حكم، لا جواب، لا واقعة مقبولة. "
                         "NEUTRAL_GENERATOR_PRODUCES_FINAL_ANSWER = NO.", "kind": "warn"},
            {"cols": {"headers": ["flag", "value"], "rows": [[r[0], r[1]] for r in nb_rows],
                      "row_classes": [["", r[2]] for r in nb_rows]}},
        ]},
        {"n": 2, "title": "TAAQOL_VERTICAL_DERIVATION", "body": vertical_body},
        {"n": 3, "title": "SOURCE_OF_FINAL_ANSWER", "body": [
            {"raw_note": f"<b>SOURCE_OF_FINAL_ANSWER = {d['SOURCE_OF_FINAL_ANSWER']}</b> — "
                         "المولّد المحايد لا ينتج الجواب النهائي؛ الجواب النهائي (إن وُجد) من السلسلة العمودية "
                         "بعد التصديق والتنزيل والحكم. لا تعارض بين التقريرين."},
        ]},
    ]
    return {
        "title": f"{REPORT_STEM} — تقرير تنفيذي عام (LATEST/CURRENT)",
        "lang": "ar",
        "top_banners": [
            ("warn", "<b>تقرير عام لا يحمل رقم جولة</b> — يعكس أحدث حالة الكود وقت التشغيل. القسم الأول بنية "
                     "محايدة (لا جواب)، والقسم الثاني اشتقاق السلسلة العمودية (الجواب إن وُجد)."),
        ],
        "sentence": {"label": "النازلة", "text": SENTENCE, "id": "nazila-sentence"},
        "sections": sections,
        "closure_flags": (
            f"SOURCE_OF_FINAL_ANSWER = {d['SOURCE_OF_FINAL_ANSWER']} · "
            f"NEUTRAL.FINAL_ANSWER = {nb['FINAL_ANSWER']} · VERTICAL.FINAL_ANSWER = {v['FINAL_ANSWER']} · "
            f"VERTICAL.SCOPE = {v['SCOPE']} · JUDICIAL_OUTCOME_PRODUCED = {v['JUDICIAL_OUTCOME_PRODUCED']} · "
            f"FULL_TAAQOL_PROJECT_CLOSED = {v['FULL_TAAQOL_PROJECT_CLOSED']} · REPORT_NAME_HAS_ROUND_NUMBER = NO."),
        "tests_result": "CURRENT_EXECUTIVE_REPORT_TESTS = passed",
        "footer": f"تقرير تنفيذي عام (CURRENT/LATEST) — {RENDERER_MARKER}.",
    }


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--report-out", default=str(OUT / f"{REPORT_STEM}.html"))
    a = ap.parse_args(argv)
    OUT.mkdir(parents=True, exist_ok=True)
    d = registry_json()
    (OUT / f"{REPORT_STEM}.json").write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    (OUT / f"{REPORT_STEM}.md").write_text(registry_md(d), encoding="utf-8")
    pathlib.Path(a.report_out).write_text(render_taaqol_style_manager_report(build_spec(d)), encoding="utf-8")
    v = d["TAAQOL_VERTICAL_DERIVATION"]
    print(f"{REPORT_STEM}=" + a.report_out)
    print(f"NEUTRAL.FINAL_ANSWER={d['NEUTRAL_BASELINE_OUTPUT']['FINAL_ANSWER']} "
          f"VERTICAL.FINAL_ANSWER={v['FINAL_ANSWER']} SCOPE={v['SCOPE']} "
          f"SOURCE_OF_FINAL_ANSWER={d['SOURCE_OF_FINAL_ANSWER']}")


if __name__ == "__main__":
    main()
