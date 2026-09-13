#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAAQOL_MAT_MALIK_CURRENT_EXECUTIVE_REPORT — guard test.

A round-agnostic current/latest executive report: neutral baseline (structure only, FINAL_ANSWER=NO) +
vertical derivation (latest accepted chain state, discovered at runtime). FINAL_ANSWER_TEXT appears only in
the vertical section when the latest FINAL_ANSWER=YES. SOURCE_OF_FINAL_ANSWER attributes the answer to the
vertical chain, not the neutral generator. Report name carries no fixed round number.
"""
import importlib.util
import json
import re
import pathlib

ROOT = pathlib.Path("/Users/husseinhiyassat/hokom")
OUT = ROOT / "output" / "taaqol_maqam_foundation_generated"
STEM = "TAAQOL_MAT_MALIK_CURRENT_EXECUTIVE_REPORT"
J = OUT / f"{STEM}.json"
MD = OUT / f"{STEM}.md"
HTML = OUT / f"{STEM}.html"
GEN = ROOT / "scripts" / "taaqol_maqam_foundation" / "mat_malik_current_executive_report.py"
NEUTRAL_GEN = ROOT / "scripts" / "neutral_sentence_report_generator.py"
SENTENCE = "مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ، فَأَرَادَ وَارِثُهُ طَرْدَهَا، فَتَحَاكَمَا"


def _mod(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_all_files_exist():
    for p in (J, MD, HTML):
        assert p.exists() and p.stat().st_size > 0, p.name


def test_neutral_generator_gives_no_final_answer():
    ng = _mod(NEUTRAL_GEN, "neutral_gen_chk")
    d = ng.build_report(SENTENCE)
    assert d["FINAL_ANSWER"] == "NO"
    assert d["DOMAIN_DECISION"] == "NO"
    assert d["HUKM"] == "NO"
    assert d["FACT_ACCEPTED_COUNT"] == 0
    assert d["verdict"] == "DEFER_STRUCTURAL_ONLY"


def test_report_has_two_sections_and_source_declaration():
    j = json.loads(J.read_text(encoding="utf-8"))
    assert "NEUTRAL_BASELINE_OUTPUT" in j
    assert "TAAQOL_VERTICAL_DERIVATION" in j
    assert j["SOURCE_OF_FINAL_ANSWER"] == "TAAQOL_VERTICAL_CHAIN_NOT_NEUTRAL_GENERATOR"
    for t in (MD.read_text(encoding="utf-8"), HTML.read_text(encoding="utf-8")):
        assert "NEUTRAL_BASELINE_OUTPUT" in t
        assert "TAAQOL_VERTICAL_DERIVATION" in t
        assert "TAAQOL_VERTICAL_CHAIN_NOT_NEUTRAL_GENERATOR" in t


def test_neutral_baseline_is_structural_only():
    nb = json.loads(J.read_text(encoding="utf-8"))["NEUTRAL_BASELINE_OUTPUT"]
    assert nb["FINAL_ANSWER"] == "NO"
    assert nb["DOMAIN_DECISION"] == "NO"
    assert nb["HUKM"] == "NO"
    assert nb["FACT_ACCEPTED_COUNT"] == 0
    assert nb["VERDICT"] == "DEFER_STRUCTURAL_ONLY"
    assert nb["produces_final_answer"] == "NO"
    # the neutral baseline block must NOT carry a final-answer text
    assert "FINAL_ANSWER_TEXT" not in nb


def test_vertical_reflects_latest_and_answer_text_only_here():
    j = json.loads(J.read_text(encoding="utf-8"))
    v = j["TAAQOL_VERTICAL_DERIVATION"]
    for k in ("FINAL_MANAT", "NS1_ACCEPTED", "TANZIL", "FINAL_HUKM", "FINAL_ANSWER", "SCOPE",
              "JUDICIAL_OUTCOME_PRODUCED", "FULL_TAAQOL_PROJECT_CLOSED"):
        assert k in v, k
    # if the latest accepted state has FINAL_ANSWER=YES, the text must appear in the vertical section only
    if v["FINAL_ANSWER"] == "YES":
        assert "FINAL_ANSWER_TEXT" in v and v["FINAL_ANSWER_TEXT"]
        html = HTML.read_text(encoding="utf-8")
        snippet = v["FINAL_ANSWER_TEXT"][:40]
        i_vert = html.find("TAAQOL_VERTICAL_DERIVATION")
        i_neut = html.find("NEUTRAL_BASELINE_OUTPUT")
        assert i_neut != -1 and i_vert != -1 and i_neut < i_vert
        pos = html.find(snippet)
        assert pos != -1 and pos > i_vert, "FINAL_ANSWER_TEXT must be inside the vertical section only"
        # and must not appear before the vertical section (i.e., not in neutral baseline)
        assert html.find(snippet, i_neut, i_vert) == -1


def test_vertical_state_discovered_at_runtime_matches_latest_artifacts():
    m = _mod(GEN, "cur_exec_chk")
    v = m.vertical_derivation()
    # the discovered final-answer artifact should be the highest-numbered one on disk
    ans_files = sorted(OUT.glob("TAAQOL_MAT_MALIK_FINAL_ANSWER_*.json"))
    if ans_files:
        latest = max(ans_files, key=lambda p: int(re.search(r"_(\d+)\.json$", p.name).group(1)))
        assert v["source_artifacts"]["final_answer"] == latest.name


def test_report_name_has_no_fixed_round_number():
    for p in (J, MD, HTML):
        assert not re.search(r"[Rr]ound\s*\d+", p.name)
        assert not re.search(r"_(5[0-9]|4[0-9])\b", p.name)  # no _44.._59 round suffixes in the name
    # title inside the report must not fix a round number either
    j = json.loads(J.read_text(encoding="utf-8"))
    assert j["REPORT"] == STEM
    assert "Round53" not in HTML.read_text(encoding="utf-8")
    assert "Round58" not in HTML.read_text(encoding="utf-8")


def test_guards():
    g = json.loads(J.read_text(encoding="utf-8"))["guards"]
    assert g["NEUTRAL_GENERATOR_PRODUCES_FINAL_ANSWER"] == "NO"
    assert g["FINAL_ANSWER_SOURCE_IS_VERTICAL_CHAIN"] == "YES"
    assert g["NEUTRAL_BASELINE_IS_STRUCTURAL_ONLY"] == "YES"
    assert g["REPORT_NAME_HAS_FIXED_ROUND_NUMBER"] == "NO"
    assert g["VERTICAL_STATE_DISCOVERED_AT_RUNTIME"] == "YES"
    assert g["PRIOR_ARTIFACTS_UNCHANGED"] == "YES"
