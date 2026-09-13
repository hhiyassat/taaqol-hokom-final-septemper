#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT — guard test.

The runtime manager report is the actual executive output: it does NOT use the neutral generator, shows no
neutral baseline, presents the latest accepted vertical state (FINAL_ANSWER=YES + FINAL_ANSWER_TEXT),
auto-discovers the latest artifacts (no fixed round number), and its name carries no round number. Bounds:
JUDICIAL_OUTCOME_PRODUCED=NO, SCOPE=FNM1_ONLY, FULL_TAAQOL_PROJECT_CLOSED=NO.
"""
import importlib.util
import json
import re
import pathlib

ROOT = pathlib.Path("/Users/husseinhiyassat/hokom")
OUT = ROOT / "output" / "taaqol_maqam_foundation_generated"
STEM = "TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT"
J = OUT / f"{STEM}.json"
MD = OUT / f"{STEM}.md"
HTML = OUT / f"{STEM}.html"
GEN = ROOT / "scripts" / "taaqol_maqam_foundation" / "mat_malik_runtime_manager_report.py"


def _mod():
    spec = importlib.util.spec_from_file_location("runtime_mgr_chk", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_all_files_exist():
    for p in (J, MD, HTML):
        assert p.exists() and p.stat().st_size > 0, p.name


def test_no_neutral_baseline_in_report():
    for p in (J, MD, HTML):
        t = p.read_text(encoding="utf-8")
        assert "NEUTRAL_BASELINE_OUTPUT" not in t, p.name
        assert "DEFER_STRUCTURAL_ONLY" not in t, p.name


def test_generator_does_not_use_neutral_generator():
    src = GEN.read_text(encoding="utf-8")
    assert "import neutral_sentence_report_generator" not in src
    assert "neutral_sentence_report_generator" not in src.replace("does NOT use the neutral", "")
    g = json.loads(J.read_text(encoding="utf-8"))["guards"]
    assert g["USES_NEUTRAL_GENERATOR"] == "NO"
    assert g["SHOWS_NEUTRAL_BASELINE"] == "NO"


def test_final_answer_yes_and_text_present():
    st = json.loads(J.read_text(encoding="utf-8"))["state"]
    assert st["FINAL_ANSWER"] == "YES"
    assert st["FINAL_ANSWER_STATUS"] == "ACCEPTED"
    assert st["FINAL_ANSWER_TEXT"] and "مجلس الحكم المختص" in st["FINAL_ANSWER_TEXT"]
    html = HTML.read_text(encoding="utf-8")
    assert "مجلس الحكم المختص" in html   # the actual answer text is shown to the manager


def test_full_vertical_state_shown():
    st = json.loads(J.read_text(encoding="utf-8"))["state"]
    assert st["FINAL_MANAT"] == "YES"
    assert st["NORMATIVE_SOURCE_ACCEPTED"] == "YES"
    assert st["NORMATIVE_SOURCE_ID"] == "NS1_OWNER_RATIFIED_NO_EXPULSION_BEFORE_ADJUDICATION_RULE"
    assert st["TANZIL"] == "YES"
    assert st["FINAL_HUKM"] == "YES"


def test_constraints_preserved():
    st = json.loads(J.read_text(encoding="utf-8"))["state"]
    assert st["SCOPE"] == "FNM1_ONLY"
    assert st["JUDICIAL_OUTCOME_PRODUCED"] == "NO"
    assert st["FULL_TAAQOL_PROJECT_CLOSED"] == "NO"
    b = json.loads(J.read_text(encoding="utf-8"))["boundary_flags"]
    for k in ("IS_GENERAL_FATWA", "IS_JUDICIAL_ORDER", "DECIDES_OWNERSHIP", "DECIDES_ESTATE_DIVISION",
              "DECIDES_SISTER_FINAL_RIGHT", "GENERALIZES_BEYOND_FNM1"):
        assert b[k] == "NO", k


def test_latest_state_discovered_at_runtime():
    m = _mod()
    st = m.discover_state()
    ans = sorted(OUT.glob("TAAQOL_MAT_MALIK_FINAL_ANSWER_*.json"))
    ans = [p for p in ans if not any(x in p.name for x in ("GUARDS", "MATRIX", "MANAGER_REPORT", "RECHECK"))]
    if ans:
        latest = max(ans, key=lambda p: int(re.search(r"_(\d+)\.json$", p.name).group(1)))
        assert st["source_artifacts"]["final_answer"] == latest.name


def test_report_name_has_no_fixed_round_number():
    for p in (J, MD, HTML):
        assert not re.search(r"[Rr]ound\s*\d+", p.name)
        assert not re.search(r"_(4[0-9]|5[0-9])\b", p.name)
    assert json.loads(J.read_text(encoding="utf-8"))["REPORT"] == STEM


def test_report_topology_14_h2():
    t = HTML.read_text(encoding="utf-8")
    numbered = re.findall(r"<h2>(\d+)\.\s", t)
    assert numbered == [str(i) for i in range(1, 15)], numbered
    assert t.count("<h2") == 14
