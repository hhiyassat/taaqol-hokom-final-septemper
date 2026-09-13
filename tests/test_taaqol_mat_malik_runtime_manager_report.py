#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT — TRUE input-bound runtime guard test.

Proves the runtime is bound to its input (not a renderer over latest artifacts):
  - changing --sentence changes the token table and input_sha256;
  - the canonical sentence may reach FINAL_ANSWER=YES only because every layer artifact hashes to it;
  - an altered sentence CANNOT reuse the old FINAL_ANSWER_TEXT → DEFER_RUNTIME_DERIVATION_INCOMPLETE;
  - no layer is loaded as final answer unless its sentence_sha256 == current input_sha256;
  - output path is repo-root-relative (no hardcoded /Users path);
  - the neutral generator is not used and no neutral baseline appears.
"""
import importlib.util
import json
import pathlib
import re

ROOT = pathlib.Path("/Users/husseinhiyassat/hokom")
OUT = ROOT / "output" / "taaqol_maqam_foundation_generated"
STEM = "TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT"
GEN = ROOT / "scripts" / "taaqol_maqam_foundation" / "mat_malik_runtime_manager_report.py"

SENT_A = "مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ، فَأَرَادَ وَارِثُهُ طَرْدَهَا، فَتَحَاكَمَا"
SENT_B = "مَاتَ مَلِكٌ عَنْ أُخٍ سَاكِنٍَ مَعَهُ، فَأَرَادَ وِلَدَهُ طَرْدَهُ، فَتَحَاكَمَا"
ANSWER_SNIPPET = "لا يُنتَج أثر إخراج الأخت الساكنة من العين قبل نظر النزاع في مجلس الحكم المختص"


def _mod():
    spec = importlib.util.spec_from_file_location("rt_mgr", GEN)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m


def test_changing_sentence_changes_tokens_and_sha():
    m = _mod()
    da, db = m.derive(SENT_A), m.derive(SENT_B)
    assert da["source_sentence_sha256"] != db["source_sentence_sha256"]
    ta = [t["surface"] for t in da["input_token_table"]]
    tb = [t["surface"] for t in db["input_token_table"]]
    assert ta != tb


def test_canonical_sentence_reaches_final_answer_by_hash_match():
    m = _mod()
    d = m.derive(SENT_A)
    assert d["all_layers_matched"] == "YES"
    assert d["FINAL_ANSWER"] == "YES"
    assert d["verdict"] == "ACCEPT_RUNTIME_FINAL_ANSWER"
    assert ANSWER_SNIPPET in d["FINAL_ANSWER_TEXT"]
    # every bound layer proved its own sentence hashes to the input
    for k in ("FINAL_MANAT", "NORMATIVE_SOURCE", "TANZIL", "FINAL_HUKM", "FINAL_ANSWER"):
        ly = d["layers"][k]
        assert ly["status"] == "MATCHED"
        assert ly["artifact_sentence_sha256"] == d["source_sentence_sha256"]
    assert d["parent_artifact_hashes"], "matched run must record parent artifact hashes"


def test_altered_sentence_cannot_reuse_old_final_answer():
    m = _mod()
    d = m.derive(SENT_B)
    assert d["all_layers_matched"] == "NO"
    assert d["FINAL_ANSWER"] in ("NO", "DEFER")
    assert d["verdict"] == "DEFER_RUNTIME_DERIVATION_INCOMPLETE"
    assert d["FINAL_ANSWER_TEXT"] == ""            # no reuse of prior answer text
    assert ANSWER_SNIPPET not in json.dumps(d, ensure_ascii=False)
    assert d["parent_artifact_hashes"] == {}       # nothing loaded for a non-matching sentence


def test_no_layer_loaded_as_answer_unless_sha_matches():
    m = _mod()
    d = m.derive(SENT_B)
    for k, ly in d["layers"].items():
        if ly["status"] == "MATCHED":
            assert ly["artifact_sentence_sha256"] == d["source_sentence_sha256"]
        else:
            assert ly["status"] == "DEFER"


def test_report_output_path_repo_root_relative_not_hardcoded():
    src = GEN.read_text(encoding="utf-8")
    assert "/Users/husseinhiyassat/hokom" not in src
    m = _mod()
    # ROOT is derived from the file location (repo root), not a hardcoded absolute literal
    assert m.ROOT.name == "hokom" or (m.ROOT / "scripts").exists()


def test_neutral_generator_not_used_in_runtime():
    src = GEN.read_text(encoding="utf-8")
    assert "import neutral_sentence_report_generator" not in src
    assert "neutral_sentence_report_generator" not in src


def test_provenance_and_reuse_flags():
    m = _mod()
    d = m.derive(SENT_A)
    assert d["generated_at_runtime"] == "YES"
    assert d["reused_prior_artifact"] == "NO"
    assert d["reused_prior_final_answer"] == "NO"
    assert d["loads_final_answer_only_if_sha_matches"] == "YES"
    g = d["guards"]
    assert g["INPUT_BOUND_CHAIN"] == "YES"
    assert g["LATEST_ARTIFACT_SHORTCUT"] == "NO"
    assert g["USES_NEUTRAL_GENERATOR"] == "NO"
    assert g["OUTPUT_PATH_REPO_ROOT_RELATIVE"] == "YES"


def test_generated_report_files_have_no_neutral_baseline():
    m = _mod()
    m.main(["--sentence", SENT_A])
    for ext in ("json", "md", "html"):
        t = (OUT / f"{STEM}.{ext}").read_text(encoding="utf-8")
        assert "NEUTRAL_BASELINE_OUTPUT" not in t
        assert "DEFER_STRUCTURAL_ONLY" not in t


def test_report_topology_14_h2_for_canonical():
    m = _mod()
    m.main(["--sentence", SENT_A])
    t = (OUT / f"{STEM}.html").read_text(encoding="utf-8")
    numbered = re.findall(r"<h2>(\d+)\.\s", t)
    assert numbered == [str(i) for i in range(1, 15)], numbered
    assert t.count("<h2") == 14


# ---- HTML-level A/B divergence (fails if the render regresses to a cosmetic sentence swap) ----

def _write(stem, sentence):
    m = _mod()
    res = m.write_report(sentence, stem)
    return pathlib.Path(res["html"]).read_text(encoding="utf-8")


def test_html_ab_divergence_tokens_sha_answer():
    ha = _write(f"{STEM}_A_ORIGINAL", SENT_A)
    hb = _write(f"{STEM}_B_ALTERED", SENT_B)

    def sha(t):
        m = re.search(r"INPUT_SHA256</th><td[^>]*>([0-9a-f]{16,})", t)
        return m.group(1) if m else None
    def tokens(t):
        return re.findall(r"<tr><th>r\d{3}</th><td>([^<]+)</td></tr>", t)

    # distinct input hashes shown in HTML
    assert sha(ha) and sha(hb) and sha(ha) != sha(hb)
    # token tables shown and different
    assert tokens(ha) and tokens(hb) and tokens(ha) != tokens(hb)
    # B renders B's own words, NOT A's words
    for w in ("أُخٍ", "وِلَدَهُ", "طَرْدَهُ"):
        assert w in hb, w
    for w in ("أُخْتٍ", "وَارِثُهُ", "طَرْدَهَا"):
        assert w not in hb, w
    # A reaches YES; B defers and carries no prior answer text
    assert "ACCEPT_RUNTIME_FINAL_ANSWER" in ha
    assert "DEFER_RUNTIME_DERIVATION_INCOMPLETE" in hb
    assert "مجلس الحكم المختص" in ha            # A shows the real answer
    assert "مجلس الحكم المختص" not in hb        # B must NOT reuse the old answer text
    # both HTML expose the runtime provenance
    for t in (ha, hb):
        for k in ("INPUT_SHA256", "VERDICT", "reused_prior_final_answer", "reused_prior_artifact"):
            assert k in t, k
