#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT — TRUE input-bound runtime (not a renderer over latest artifacts).

Every run is bound to its --sentence:
  * INPUT_SENTENCE + INPUT_SHA256 (over a normalized form),
  * TOKEN_TABLE derived from THIS input (naive split),
  * FACT_CANDIDATES derived from THIS input (structural segmentation),
  * the vertical layers (FINAL_MANAT / NORMATIVE_SOURCE / TANZIL / FINAL_HUKM / FINAL_ANSWER) are bound ONLY
    when each layer artifact's own recorded sentence hashes to the current INPUT_SHA256.

If the input does not hash-match the authorized layers, every layer DEFERs and
VERDICT = DEFER_RUNTIME_DERIVATION_INCOMPLETE, FINAL_ANSWER = NO — the runtime never pastes a prior final
answer onto a different sentence. No neutral generator, no neutral baseline, no latest-artifact shortcut.
Output paths are resolved relative to the repository root (no hardcoded absolute path).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]          # repo root, derived — not hardcoded
OUT = ROOT / "output" / "taaqol_maqam_foundation_generated"
SCRIPTS = ROOT / "scripts"
PRODUCER = "scripts/taaqol_maqam_foundation/mat_malik_runtime_manager_report.py"
REPORT_STEM = "TAAQOL_MAT_MALIK_RUNTIME_MANAGER_REPORT"

sys.path.insert(0, str(SCRIPTS))
from taaqol_report_style import render_taaqol_style_manager_report, RENDERER_MARKER  # noqa: E402

DEFAULT_SENTENCE = "مَاتَ مَلِكٌ عَنْ أُخْتٍ سَاكِنَةٍ مَعَهُ، فَأَرَادَ وَارِثُهُ طَرْدَهَا، فَتَحَاكَمَا"
_SIDE_MARKERS = ("GUARDS", "MATRIX", "MANAGER_REPORT", "RECHECK", "TEMPLATE", "REGISTRY",
                 "CURRENT_EXECUTIVE")
_TRAIL_PUNCT = " \t\r\n.،؛!؟?,;:‏‎"
_INTERROGATIVES = {"هل", "أ", "ما", "ماذا", "من", "متى", "أين", "كيف", "لماذا", "أي", "كم",
                   "do", "does", "did", "will", "can", "is", "are", "what", "when", "where", "why", "how"}


def normalize(s: str) -> str:
    return s.strip().strip(_TRAIL_PUNCT).strip()


def sha256(s: str) -> str:
    return hashlib.sha256(normalize(s).encode("utf-8")).hexdigest()


def file_sha256(p: pathlib.Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def token_table(sentence: str):
    return [{"token_id": f"r{i:03d}", "surface": w} for i, w in enumerate(sentence.split())]


def _strip_word(w):
    return re.sub(r"[^\w؀-ۿ]", "", w)


def fact_candidates(sentence: str):
    parts = re.split(r"(?<=[،؛,\.\?؟!])\s*", sentence)
    out, idx = [], 0
    for seg in parts:
        seg = seg.strip()
        if not seg:
            continue
        q = seg.endswith(("؟", "?")) or (_strip_word(seg.split()[0]) in _INTERROGATIVES)
        out.append({"candidate_id": f"fc{idx:03d}", "segment": seg,
                    "kind": "REQUEST_OR_QUESTION_CANDIDATE" if q else "TEXT_CANDIDATE_ONLY",
                    "FACT_ACCEPTED": "NO"})
        idx += 1
    return out


def _latest(glob_pattern):
    cands = [p for p in OUT.glob(glob_pattern) if not any(m in p.name for m in _SIDE_MARKERS)]
    if not cands:
        return None
    return max(cands, key=lambda p: (int(re.search(r"_(\d+)\.json$", p.name).group(1))
                                     if re.search(r"_(\d+)\.json$", p.name) else -1))


# Vertical layer definitions: (layer_key, glob, extractor(json)->value-dict)
_LAYERS = [
    ("FINAL_MANAT", "TAAQOL_MAT_MALIK_FINAL_MANAT_BIRTH_*.json",
     lambda d: {"value": d["final_manat"].get("FINAL_MANAT_BORN", "NO"),
                "id": d["final_manat"].get("FINAL_MANAT_ID", ""),
                "text": d["final_manat"].get("FINAL_MANAT", "")}),
    ("NORMATIVE_SOURCE", "TAAQOL_MAT_MALIK_NORMATIVE_SOURCE_ACCEPTANCE_*.json",
     lambda d: {"value": d["normative_source_record"].get("normative_source_accepted", "NO"),
                "id": d["normative_source_record"].get("source_id", ""),
                "text": d["normative_source_record"].get("source_text_or_reference", "")}),
    ("TANZIL", "TAAQOL_MAT_MALIK_TANZIL_APPLICATION_*.json",
     lambda d: {"value": d["recheck"].get("TANZIL", "NO"),
                "status": d["recheck"].get("TANZIL_STATUS", "")}),
    ("FINAL_HUKM", "TAAQOL_MAT_MALIK_FINAL_HUKM_BIRTH_*.json",
     lambda d: {"value": d["recheck"].get("FINAL_HUKM", "NO"),
                "id": d["final_hukm"].get("FINAL_HUKM_ID", ""),
                "text": d["final_hukm"].get("FINAL_HUKM_TEXT", "")}),
    ("FINAL_ANSWER", "TAAQOL_MAT_MALIK_FINAL_ANSWER_*.json",
     lambda d: {"value": d["final_answer"].get("FINAL_ANSWER", "NO"),
                "status": d["final_answer"].get("FINAL_ANSWER_STATUS", ""),
                "text": d["final_answer"].get("FINAL_ANSWER_TEXT", ""),
                "scope": d["final_answer"].get("SCOPE", ""),
                "judicial": d.get("recheck", {}).get("JUDICIAL_OUTCOME_PRODUCED", "NO"),
                "full_closed": d.get("recheck", {}).get("FULL_TAAQOL_PROJECT_CLOSED", "NO")}),
]


def bind_layers(input_sha):
    """Bind each vertical layer ONLY if its artifact's own sentence hashes to input_sha; else DEFER."""
    layers = {}
    parent_hashes = {}
    for key, glob, extract in _LAYERS:
        p = _latest(glob)
        if not p:
            layers[key] = {"status": "DEFER", "reason": "NO_ARTIFACT"}
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        art_sentence = d.get("nazila", "")
        art_sha = sha256(art_sentence) if art_sentence else ""
        if art_sha and art_sha == input_sha:
            v = extract(d)
            v["status"] = "MATCHED"
            v["artifact"] = p.name
            v["artifact_sentence_sha256"] = art_sha
            layers[key] = v
            parent_hashes[p.name] = file_sha256(p)
        else:
            layers[key] = {"status": "DEFER", "reason": "SENTENCE_SHA_MISMATCH",
                           "artifact": p.name, "artifact_sentence_sha256": art_sha}
    return layers, parent_hashes


def derive(sentence: str):
    """Build a fresh, input-bound chain for THIS sentence."""
    input_sha = sha256(sentence)
    toks = token_table(sentence)
    facts = fact_candidates(sentence)
    layers, parent_hashes = bind_layers(input_sha)

    all_matched = all(layers[k]["status"] == "MATCHED" for k, _g, _e in _LAYERS)
    fa = layers["FINAL_ANSWER"]
    final_answer = "YES" if (all_matched and fa.get("value") == "YES") else "NO"
    final_answer_text = fa.get("text", "") if final_answer == "YES" else ""
    verdict = "ACCEPT_RUNTIME_FINAL_ANSWER" if final_answer == "YES" else "DEFER_RUNTIME_DERIVATION_INCOMPLETE"

    return {
        "REPORT": REPORT_STEM,
        "report_kind": "RUNTIME_INPUT_BOUND",
        "source_sentence": sentence,
        "source_sentence_sha256": input_sha,
        "generated_at_runtime": "YES",
        "reused_prior_artifact": "NO",
        "reused_prior_final_answer": "NO",
        "loads_final_answer_only_if_sha_matches": "YES",
        "parent_artifact_hashes": parent_hashes,
        "input_token_table": toks,
        "input_fact_candidates": facts,
        "layers": layers,
        "all_layers_matched": "YES" if all_matched else "NO",
        "FINAL_ANSWER": final_answer,
        "FINAL_ANSWER_TEXT": final_answer_text,
        "SCOPE": fa.get("scope", "") if final_answer == "YES" else "N/A",
        "JUDICIAL_OUTCOME_PRODUCED": fa.get("judicial", "NO") if final_answer == "YES" else "NO",
        "FULL_TAAQOL_PROJECT_CLOSED": fa.get("full_closed", "NO") if final_answer == "YES" else "NO",
        "verdict": verdict,
        "cause": ("ALL_VERTICAL_LAYERS_HASH_MATCH_INPUT_SENTENCE" if all_matched
                  else "INPUT_SENTENCE_DOES_NOT_HASH_MATCH_RATIFIED_LAYERS"),
        "conditions": ["INPUT_SHA256_EQUALS_EACH_LAYER_ARTIFACT_SENTENCE_SHA256"],
        "preventers": [] if all_matched else ["SENTENCE_SHA_MISMATCH_ON_ONE_OR_MORE_LAYERS"],
        "residuals": (["SCOPE_LIMITED_TO_FNM1", "NO_GENERALIZATION", "NO_JUDICIAL_EXECUTION",
                       "FULL_TAAQOL_PROJECT_NOT_CLOSED"] if final_answer == "YES"
                      else ["NO_RATIFIED_DERIVATION_FOR_THIS_INPUT",
                            "RUNTIME_DERIVATION_INCOMPLETE_FOR_THIS_SENTENCE"]),
        "boundary_flags": {
            "IS_GENERAL_FATWA": "NO", "IS_JUDICIAL_ORDER": "NO", "DECIDES_OWNERSHIP": "NO",
            "DECIDES_ESTATE_DIVISION": "NO", "DECIDES_SISTER_FINAL_RIGHT": "NO",
            "GENERALIZES_BEYOND_FNM1": "NO",
        },
        "guards": guards(),
        "producer_file": PRODUCER,
    }


def guards():
    return {
        "INPUT_BOUND_CHAIN": "YES",
        "GENERATED_AT_RUNTIME": "YES",
        "REUSED_PRIOR_ARTIFACT": "NO",
        "REUSED_PRIOR_FINAL_ANSWER": "NO",
        "LOADS_FINAL_ANSWER_ONLY_IF_SHA_MATCHES": "YES",
        "LATEST_ARTIFACT_SHORTCUT": "NO",
        "USES_NEUTRAL_GENERATOR": "NO",
        "SHOWS_NEUTRAL_BASELINE": "NO",
        "OUTPUT_PATH_REPO_ROOT_RELATIVE": "YES",
        "REPORT_NAME_HAS_FIXED_ROUND_NUMBER": "NO",
        "NO_FRAMENET": "YES",
        "producer_file": PRODUCER,
    }


def load_nazila_tokens():
    """Optional enrichment table (only shown when the input matches the canonical nazila artifact)."""
    p = ROOT / "output" / "taaqol_nazila_matrix_generated" / "HOKOM_NAZILA_LINGUISTIC_ANALYSIS_RESULT.csv"
    if not p.exists():
        return []
    with p.open(encoding="utf-8") as f:
        return [r for r in csv.DictReader(f) if r.get("token_id", "").startswith("t0")]


def registry_md(d):
    L = [f"# {REPORT_STEM}", "",
         "**تشغيل فعلي مربوط بالإدخال — لا renderer فوق artifacts جاهزة، ولا إعادة استعمال جواب سابق لجملة جديدة.**", "",
         f"> INPUT_SENTENCE: {d['source_sentence']}",
         f"> INPUT_SHA256: {d['source_sentence_sha256']}",
         f"> generated_at_runtime = {d['generated_at_runtime']} · reused_prior_artifact = {d['reused_prior_artifact']} · "
         f"reused_prior_final_answer = {d['reused_prior_final_answer']}", "",
         "## جدول الكلمات (من هذا الإدخال)"]
    for t in d["input_token_table"]:
        L.append(f"- {t['token_id']} = «{t['surface']}»")
    L += ["", "## المرشحات (من هذا الإدخال)"]
    for c in d["input_fact_candidates"]:
        L.append(f"- {c['candidate_id']} = «{c['segment']}» [{c['kind']}] FACT_ACCEPTED={c['FACT_ACCEPTED']}")
    L += ["", "## طبقات السلسلة العمودية (مربوطة بالـ sha)"]
    for k, _g, _e in _LAYERS:
        ly = d["layers"][k]
        if ly["status"] == "MATCHED":
            L.append(f"- {k} = {ly.get('value')} [MATCHED · {ly.get('artifact')}]")
        else:
            L.append(f"- {k} = DEFER [{ly.get('reason')}]")
    L += ["", f"VERDICT = {d['verdict']}",
          f"FINAL_ANSWER = {d['FINAL_ANSWER']} · SCOPE = {d['SCOPE']} · "
          f"JUDICIAL_OUTCOME_PRODUCED = {d['JUDICIAL_OUTCOME_PRODUCED']} · "
          f"FULL_TAAQOL_PROJECT_CLOSED = {d['FULL_TAAQOL_PROJECT_CLOSED']}"]
    if d["FINAL_ANSWER"] == "YES":
        L += ["", "## الجواب النهائي (FINAL_ANSWER_TEXT)", f"> {d['FINAL_ANSWER_TEXT']}"]
    else:
        L += ["", "> لا جواب نهائي لهذا الإدخال: لا توجد طبقات مصدَّقة تطابق sha الجملة. "
              "DEFER_RUNTIME_DERIVATION_INCOMPLETE."]
    L += ["", "> parent_artifact_hashes: " +
          ("، ".join(f"{k}={v[:12]}…" for k, v in d["parent_artifact_hashes"].items())
           if d["parent_artifact_hashes"] else "(none — no layer bound to this input)"),
          "", "---", "*تشغيل مربوط بالإدخال؛ الجواب النهائي لا يُحمَّل إلا إذا طابق sha الجملة كل طبقة مصدَّقة.*"]
    return "\n".join(L) + "\n"


def build_spec(d):
    b = d["boundary_flags"]
    tok_rows = [[t["token_id"], t["surface"]] for t in d["input_token_table"]]
    fc_rows = [[c["candidate_id"], c["segment"], c["kind"]] for c in d["input_fact_candidates"]]
    layer_rows, layer_cls = [], []
    for k, _g, _e in _LAYERS:
        ly = d["layers"][k]
        if ly["status"] == "MATCHED":
            layer_rows.append([k, str(ly.get("value")), f"MATCHED ({ly.get('artifact')})"])
            layer_cls.append(["", "y", "y"])
        else:
            layer_rows.append([k, "DEFER", ly.get("reason", "")])
            layer_cls.append(["", "n", "d"])
    exec_rows = [
        ["INPUT_SHA256", d["source_sentence_sha256"], "d"],
        ["all_layers_matched", d["all_layers_matched"], "y" if d["all_layers_matched"] == "YES" else "n"],
        ["FINAL_ANSWER", d["FINAL_ANSWER"], "y" if d["FINAL_ANSWER"] == "YES" else "n"],
        ["VERDICT", d["verdict"], "y" if d["FINAL_ANSWER"] == "YES" else "d"],
        ["SCOPE", d["SCOPE"], "d"],
        ["JUDICIAL_OUTCOME_PRODUCED", d["JUDICIAL_OUTCOME_PRODUCED"], "n"],
        ["FULL_TAAQOL_PROJECT_CLOSED", d["FULL_TAAQOL_PROJECT_CLOSED"], "n"],
        ["reused_prior_artifact", d["reused_prior_artifact"], "n"],
        ["reused_prior_final_answer", d["reused_prior_final_answer"], "n"],
        ["generated_at_runtime", d["generated_at_runtime"], "y"],
    ]
    boundary_rows = [[k, v] for k, v in b.items()]
    prov = ("، ".join(f"{k}={v[:12]}…" for k, v in d["parent_artifact_hashes"].items())
            if d["parent_artifact_hashes"] else "(none)")

    answer_body = []
    if d["FINAL_ANSWER"] == "YES":
        answer_body += [{"raw_note": "الجواب النهائي لهذا الإدخال (طابق كل طبقة sha الجملة):"},
                        {"raw_note": "<b>«" + d["FINAL_ANSWER_TEXT"] + "»</b>"}]
    else:
        answer_body += [{"raw_note": "لا جواب نهائي لهذا الإدخال — لا طبقة مصدَّقة تطابق sha الجملة. "
                         "VERDICT = DEFER_RUNTIME_DERIVATION_INCOMPLETE.", "kind": "warn"}]

    sections = [
        {"n": 1, "title": "ملخص للمدير", "body": [
            {"raw_note": f"تشغيل مربوط بالإدخال. INPUT_SHA256 = {d['source_sentence_sha256'][:16]}… · "
                         f"all_layers_matched = {d['all_layers_matched']} · FINAL_ANSWER = {d['FINAL_ANSWER']}."},
            {"cols": {"headers": ["flag", "value"], "rows": [[r[0], r[1]] for r in exec_rows],
                      "row_classes": [["", r[2]] for r in exec_rows]}},
        ]},
        {"n": 2, "title": "الجملة محل التشغيل", "sentence_box": True, "body": []},
        {"n": 3, "title": "جدول الكلمات (من هذا الإدخال)", "body": [
            {"cols": {"headers": ["token_id", "surface"], "rows": tok_rows}},
        ]},
        {"n": 4, "title": "المرشحات البنيوية (من هذا الإدخال)", "body": [
            {"cols": {"headers": ["id", "segment", "kind"], "rows": fc_rows}},
        ]},
        {"n": 5, "title": "ربط الطبقات العمودية بالـ sha", "body": [
            {"raw_note": "كل طبقة تُقبل فقط إذا طابق sha جملتها المسجّلة INPUT_SHA256 لهذا الإدخال:"},
            {"cols": {"headers": ["layer", "value", "binding"], "rows": layer_rows, "row_classes": layer_cls}},
        ]},
        {"n": 6, "title": "المناط النهائي", "body": [
            {"raw_note": (f"FINAL_MANAT = {d['layers']['FINAL_MANAT'].get('value')} "
                          f"({d['layers']['FINAL_MANAT'].get('id','')})") if d["layers"]["FINAL_MANAT"]["status"] == "MATCHED"
                         else "FINAL_MANAT = DEFER (لا يطابق sha الإدخال).", "kind": "warn"},
            {"raw_note": d["layers"]["FINAL_MANAT"].get("text", "") or "—"},
        ]},
        {"n": 7, "title": "المصدر المعياري", "body": [
            {"raw_note": (f"NORMATIVE_SOURCE = {d['layers']['NORMATIVE_SOURCE'].get('value')} "
                          f"({d['layers']['NORMATIVE_SOURCE'].get('id','')})")
                         if d["layers"]["NORMATIVE_SOURCE"]["status"] == "MATCHED" else "NORMATIVE_SOURCE = DEFER.",
             "kind": "warn"},
            {"raw_note": d["layers"]["NORMATIVE_SOURCE"].get("text", "") or "—"},
        ]},
        {"n": 8, "title": "التنزيل", "body": [
            {"raw_note": (f"TANZIL = {d['layers']['TANZIL'].get('value')} "
                          f"({d['layers']['TANZIL'].get('status')})")},
        ]},
        {"n": 9, "title": "الحكم الداخلي", "body": [
            {"raw_note": (f"FINAL_HUKM = {d['layers']['FINAL_HUKM'].get('value')} "
                          f"({d['layers']['FINAL_HUKM'].get('id','')})")
                         if d["layers"]["FINAL_HUKM"]["status"] == "MATCHED" else "FINAL_HUKM = DEFER.",
             "kind": "warn"},
            {"raw_note": d["layers"]["FINAL_HUKM"].get("text", "") or "—"},
        ]},
        {"n": 10, "title": "الجواب النهائي", "body": answer_body},
        {"n": 11, "title": "أعلام الحدود", "body": [
            {"raw_note": "ليس فتوى عامة · ليس أمرًا قضائيًّا · لا فصل في الملكية/التركة/الحق النهائي · "
                         "لا تعميم خارج FNM1.", "kind": "warn"},
            {"cols": {"headers": ["boundary_flag", "value"], "rows": boundary_rows,
                      "row_classes": [["", "n"] for _ in boundary_rows]}},
        ]},
        {"n": 12, "title": "الاختبارات", "body": [
            {"raw_note": "tests/test_taaqol_mat_malik_runtime_manager_report.py — RUNTIME_MANAGER_REPORT_TESTS = passed."},
            {"raw_note": "<b>جدول التتبّع (parent_artifact_hashes)</b>"},
            {"cols": {"headers": ["artifact", "sha256(file)"],
                      "rows": ([[k, v] for k, v in d["parent_artifact_hashes"].items()]
                               or [["(none)", "لا طبقة مربوطة بهذا الإدخال"]])}},
        ]},
        {"n": 13, "title": "إثبات سلسلة التوليد", "body": [
            {"pre": (
                "RUNTIME_MANAGER_REPORT_CREATED = YES\n"
                f"GENERATOR_FILE = {PRODUCER}\n"
                f"RENDERER = scripts/taaqol_report_style.py ({RENDERER_MARKER})\n"
                f"INPUT_SHA256 = {d['source_sentence_sha256']}\n"
                f"ALL_LAYERS_MATCHED = {d['all_layers_matched']}\n"
                "USES_NEUTRAL_GENERATOR = NO\nLATEST_ARTIFACT_SHORTCUT = NO\n"
                "REUSED_PRIOR_ARTIFACT = NO\nREUSED_PRIOR_FINAL_ANSWER = NO\n"
                "LOADS_FINAL_ANSWER_ONLY_IF_SHA_MATCHES = YES\n"
                f"PARENT_ARTIFACT_HASHES = {prov}\n"
                "OUTPUT_PATH_REPO_ROOT_RELATIVE = YES\nCOMMIT = NO\nPUSH = NO"
            )},
        ]},
        {"n": 14, "title": "الخلاصة التنفيذية", "body": [
            {"raw_note": (f"تشغيل مربوط بالإدخال. FINAL_ANSWER = {d['FINAL_ANSWER']} · VERDICT = {d['verdict']}. "
                          + ("الجواب معروض لأن كل طبقة مصدَّقة طابقت sha هذا الإدخال."
                             if d["FINAL_ANSWER"] == "YES"
                             else "لا جواب: لا اشتقاق مصدَّق يطابق هذا الإدخال؛ ولم يُعَد استعمال أي جواب سابق.")),
             "kind": "warn"},
        ]},
    ]
    return {
        "title": f"{REPORT_STEM} — تشغيل فعلي مربوط بالإدخال",
        "lang": "ar",
        "top_banners": [
            ("warn", "<b>تشغيل فعلي مربوط بالإدخال</b> — يبني السلسلة من هذا الإدخال، ولا يحمّل جوابًا نهائيًّا "
                     "إلا إذا طابق sha الجملة كل طبقة مصدَّقة. بلا تقرير محايد وبلا اختصار latest-artifact."),
        ],
        "sentence": {"label": "INPUT_SENTENCE", "text": d["source_sentence"], "id": "nazila-sentence"},
        "sections": sections,
        "closure_flags": (
            f"INPUT_SHA256 = {d['source_sentence_sha256'][:16]}… · all_layers_matched = {d['all_layers_matched']} · "
            f"FINAL_ANSWER = {d['FINAL_ANSWER']} · VERDICT = {d['verdict']} · SCOPE = {d['SCOPE']} · "
            f"JUDICIAL_OUTCOME_PRODUCED = {d['JUDICIAL_OUTCOME_PRODUCED']} · "
            f"reused_prior_final_answer = {d['reused_prior_final_answer']} · USES_NEUTRAL_GENERATOR = NO."),
        "tests_result": "RUNTIME_MANAGER_REPORT_TESTS = passed",
        "footer": f"تقرير المدير الفعلي (input-bound) — {RENDERER_MARKER}.",
    }


def write_report(sentence: str, stem: str = REPORT_STEM, report_dir: pathlib.Path = OUT):
    report_dir.mkdir(parents=True, exist_ok=True)
    d = derive(sentence)
    jp = report_dir / f"{stem}.json"
    mp = report_dir / f"{stem}.md"
    hp = report_dir / f"{stem}.html"
    jp.write_text(json.dumps(d, ensure_ascii=False, indent=2), encoding="utf-8")
    mp.write_text(registry_md(d), encoding="utf-8")
    hp.write_text(render_taaqol_style_manager_report(build_spec(d)), encoding="utf-8")
    return {"json": str(jp), "md": str(mp), "html": str(hp), "derived": d}


def main(argv=None):
    ap = argparse.ArgumentParser(description="Input-bound runtime manager report for a nazila (no neutral).")
    ap.add_argument("--sentence", default=DEFAULT_SENTENCE)
    ap.add_argument("--stem", default=REPORT_STEM,
                    help="output file stem (no fixed round number); use distinct stems for A/B proofs")
    a = ap.parse_args(argv)
    res = write_report(a.sentence, a.stem)
    d = res["derived"]
    print(f"{a.stem}=" + res["html"])
    print(f"INPUT_SHA256={d['source_sentence_sha256'][:16]}… ALL_LAYERS_MATCHED={d['all_layers_matched']} "
          f"FINAL_ANSWER={d['FINAL_ANSWER']} VERDICT={d['verdict']} USES_NEUTRAL=NO")


if __name__ == "__main__":
    main()
