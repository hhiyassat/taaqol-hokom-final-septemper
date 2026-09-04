"""سمومُ جولة `MAX_EXECUTABLE` — `T-5` و`T-6` و`T-7`.

كلُّ حارسٍ يُسقَط بيدٍ هنا. وحارسٌ لم يُسقَط يُوسَم `UNPOISONED` ولا يُعدّ
ممتحَنًا. والسمُّ تشغيلٌ لا نصّ: يُحذف موضوعُ الحارسِ أو يُقلَب، ثمّ
يُطالَب ببلاغٍ لا انهيار.
"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def load(name: str, rel: str):
    sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))
    sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT"))
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


FS = load("forbidden_shadow", "scripts/forbidden_shadow.py")
GS = load("gate_shadow", "scripts/gate_shadow.py")
GA = load("gamma_over_axes", "scripts/gamma_over_axes.py")


# ------------------------------------------------------------------ T-5 · Γ
def test_gate_blocks_while_any_assignment_is_null():
    g = GA.gate({"assignments": {"A": None, "B": "BLOCKING"}})
    assert g["state"] == "BLOCKED_AWAITING_B2"
    assert g["pending"] == ["A"]


def test_poison_gate_would_open_if_a_null_were_read_as_a_kind():
    """السمّ: لو عُدَّ `null` إسنادًا لفُتح الطريقُ بأصنافٍ غيرِ مسنَدة."""
    full = {"assignments": {"A": "BLOCKING", "B": "DEFERRABLE"}}
    assert GA.gate(full)["state"] == "READY"
    with_null = {"assignments": {"A": "BLOCKING", "B": None}}
    assert GA.gate(with_null)["state"] != "READY"


def test_poison_hidden_forbidden_may_not_be_assigned():
    g = GA.gate({"assignments": {"A": "HIDDEN_FORBIDDEN"}})
    assert g["state"] == "BLOCKED_INVALID_KIND"
    assert g["hidden_forbidden_chosen"] == ["A"]


def test_poison_kind_outside_the_four_is_refused():
    g = GA.gate({"assignments": {"A": "SOMETHING_ELSE"}})
    assert g["state"] == "BLOCKED_INVALID_KIND"
    assert g["invalid"] == ["A=SOMETHING_ELSE"]


def test_gamma_writes_no_file_while_blocked(tmp_path):
    assert not (ROOT / "reports" / "gamma_shadow").exists() or not list(
        (ROOT / "reports" / "gamma_shadow").glob("AXIS_*_GAMMA.csv"))


def test_the_real_assignment_file_is_still_all_null():
    """لا يُسنَد صنفٌ من عندي: `P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED`."""
    data = json.loads((ROOT / "data" / "residual_kind_assignment.json")
                      .read_text(encoding="utf-8"))
    assert set(data["assignments"].values()) == {None}


# ------------------------------------------------------- T-6 · الخطوطُ الممنوعة
@pytest.fixture(scope="module")
def t6(tmp_path_factory):
    return FS.build(tmp_path_factory.mktemp("t6"))


def test_t6_all_guards_pass(t6):
    assert t6["all_guards_pass"], t6["guards"]


def test_poison_forbidden_queried_falls_when_an_answer_is_flipped():
    """السمّ: يُقلَب جوابٌ في المخرَج ولا يُقلَب النداء — فيبلّغ الحارس."""
    reg = FS.LiveRegistry(FS.CANONICAL_REGISTRY)
    rows = FS.q3_stage_graph(reg)
    assert FS.g_forbidden_queried(rows, reg)["passes"]
    rows[0]["answer"] = not rows[0]["answer"]
    g = FS.g_forbidden_queried(rows, reg)
    assert not g["passes"] and g["mismatched"]


def test_poison_forbidden_queried_falls_on_a_row_never_called():
    """السمّ: صفٌّ كُتب جوابُه بلا نداء — لا يمرّ."""
    reg = FS.LiveRegistry(FS.CANONICAL_REGISTRY)
    rows = FS.q3_stage_graph(reg)
    rows.append({"query_id": "FAKE", "source": "Candidate",
                 "target": "Certificate", "call": "is_forbidden_direct",
                 "answer": True, "status": "EVIDENCE"})
    g = FS.g_forbidden_queried(rows, reg)
    assert not g["passes"] and g["unbacked"] == ["FAKE:Candidate->Certificate"]


def test_poison_tautology_declared_falls_when_a_self_query_is_called_evidence():
    reg = FS.LiveRegistry(FS.CANONICAL_REGISTRY)
    rows = FS.q1_self_layer_leaps(reg)
    assert FS.g_tautology_declared(rows)["passes"]
    rows[0]["status"] = "EVIDENCE"
    g = FS.g_tautology_declared(rows)
    assert not g["passes"] and g["mislabelled"]


def test_poison_shadow_only_falls_when_an_axis_file_changes():
    before = {"a.csv": "aaaa", "b.csv": "bbbb"}
    after = {"a.csv": "aaaa", "b.csv": "cccc"}
    g = FS.g_shadow_only(before, after)
    assert not g["passes"] and g["changed"] == ["b.csv"]


def test_t6_reports_the_expected_katab_event_as_absent(t6, tmp_path_factory):
    """المتوقَّعُ لم يقع: تُقاس الواقعةُ ولا تُفترَض."""
    reg = FS.LiveRegistry(FS.CANONICAL_REGISTRY)
    rows = FS.q5_axis4_peel(reg)
    k = [r for r in rows if r["query_id"] == "Q5k"]
    assert k and k[0]["status"] == "EXPECTED_EVENT_ABSENT"
    assert k[0]["events_in_data"] == 0


def test_t6_never_calls_the_axis_to_layer_mapping_derivable():
    reg = FS.LiveRegistry(FS.CANONICAL_REGISTRY)
    for r in FS.q5_axis4_peel(reg):
        assert r["mapping_authority"] == "OWNER_RULING_REQUIRED"


# --------------------------------------------------------------- T-7 · البوّابة
@pytest.fixture(scope="module")
def t7(tmp_path_factory):
    return GS.build(tmp_path_factory.mktemp("t7"))


def test_t7_all_guards_pass(t7):
    assert t7["all_guards_pass"], t7["guards"]


def test_poison_rank_from_meet_falls_on_an_approved_disagreement():
    rows = [{"state": "APPROVED", "agrees": False, "origin": "o",
             "target_layer": "L", "evidence_rank": "STRONG",
             "residual_kind": "NONE", "granted_rank": "LICENSED",
             "meet_independent": "TRACE"}]
    g = GS.g_rank_from_meet(rows)
    assert not g["passes"] and g["disagreements_on_approved"]


def test_poison_rank_from_meet_falls_when_a_short_circuit_raises_rank():
    """السمّ: قطعٌ يمنح أعلى ممّا يمنحه الـ`meet` — نقضٌ للقانون."""
    rows = [{"state": "FORBIDDEN_LEAP", "agrees": False, "origin": "o",
             "target_layer": "CERTIFICATE", "evidence_rank": "STRONG",
             "residual_kind": "NONE", "granted_rank": "STRONG",
             "meet_independent": "TRACE"}]
    g = GS.g_rank_from_meet(rows)
    assert not g["passes"] and g["short_circuit_raised_rank"]


def test_short_circuit_below_the_meet_is_not_a_disagreement():
    """وهذا هو الواقعُ المقيس: القاطعُ يخفض ولا يرفع — فلا يسقط الحارس."""
    rows = [{"state": "FORBIDDEN_LEAP", "agrees": False, "origin": "o",
             "target_layer": "CERTIFICATE", "evidence_rank": "STRONG",
             "residual_kind": "NONE", "granted_rank": "ZERO",
             "meet_independent": "TRACE"}]
    assert GS.g_rank_from_meet(rows)["passes"]


def test_poison_gate_queried_falls_on_an_empty_state():
    rows = [{"origin": "o", "target_layer": "L", "state": "",
             "status": "MEASURED"}]
    g = GS.g_gate_queried(rows)
    assert not g["passes"] and g["empty_state"]


def test_poison_no_certificate_falls_if_a_certificate_were_granted():
    rows = [{"origin": "o", "target_layer": "CERTIFICATE",
             "evidence_rank": "CERTIFICATE", "granted_rank": "CERTIFICATE"}]
    g = GS.g_no_certificate(rows)
    assert not g["passes"] and g["hits"]


def test_t7_carrier_comes_from_the_vendor_not_from_here():
    assert GS.FIXTURES == "tests.test_transition_gate"
    mod = GS.fixtures()
    assert mod.__file__.replace("\\", "/").endswith(
        "vendor/Taaqol-GPT/tests/test_transition_gate.py")


# ------------------------------------------------------- T5.3 · أثرُ الإسناد
PI = load("projected_impact", "scripts/projected_impact.py")
BM = load("build_max", "scripts/build_max.py")


def test_projected_impact_assigns_nothing():
    """`P4` — الأثرُ يُعرَض، والاختيارُ لا يُتّخذ."""
    d = json.loads((ROOT / "reports/gamma_shadow/PROJECTED_IMPACT.json")
                   .read_text(encoding="utf-8"))
    assert d["all_guards_pass"]
    g = next(x for x in d["guards"] if x["guard"] == "G_NO_ASSIGNMENT")
    assert g["chosen"] == [] and g["passes"]


def test_poison_no_assignment_falls_if_one_were_chosen(tmp_path, monkeypatch):
    """السمّ: يُملأ إسنادٌ واحد ⟶ يسقط الحارس."""
    f = tmp_path / "a.json"
    f.write_text(json.dumps({"assignments": {"A": "BLOCKING", "B": None}}),
                 encoding="utf-8")
    monkeypatch.setattr(PI, "ASSIGN", f)
    m = json.loads((ROOT / "output/max/01_b2_measures.json")
                   .read_text(encoding="utf-8"))
    caps = PI.ceilings()
    g = PI.guards(PI.scenarios(m, caps), caps, m)
    bad = next(x for x in g if x["guard"] == "G_NO_ASSIGNMENT")
    assert not bad["passes"] and bad["chosen"] == ["A"]


def test_poison_ceiling_is_live_falls_on_a_stored_ceiling():
    m = json.loads((ROOT / "output/max/01_b2_measures.json")
                   .read_text(encoding="utf-8"))
    caps = dict(PI.ceilings())
    caps["BLOCKING"] = "CERTIFICATE"          # سقفٌ مخزَّنٌ لا مستفتًى
    g = PI.guards(PI.scenarios(m, caps), caps, m)
    live = next(x for x in g if x["guard"] == "G_CEILING_IS_LIVE")
    assert not live["passes"] and live["drifted"] == ["BLOCKING"]


def test_poison_totals_preserved_falls_when_a_transition_creates_a_verdict():
    rows = [{"class": "X", "before": {"ACCEPT": 5, "DEFER": 0, "BLOCK": 0},
             "after": {"ACCEPT": 0, "DEFER": 0, "BLOCK": 6}}]
    m = {"M2_reach": {"per_class": {"X": {}}}}
    g = PI.guards(rows, PI.ceilings(), m)
    tot = next(x for x in g if x["guard"] == "G_TOTALS_PRESERVED")
    assert not tot["passes"] and tot["broken"] == ["X"]


# ------------------------------------------------------ G_BYTE_IDENTICAL
def test_byte_identical_passes_over_every_axis_file():
    g = BM.byte_identical()
    assert g["state"] == "MEASURED" and g["passes"]
    assert g["compared"] == g["denominator"] == len(BM.AXES)
    assert g["runs"] == 2, "شهادةٌ بلا تشغيلٍ ثانٍ ليست شهادة"


def test_poison_byte_identical_falls_when_a_hash_drifts(tmp_path):
    """السمّ: تُبدَّل بصمةُ ملفٍّ في الشهادة ⟶ الحارسُ نفسُه يُسمّي المختلف."""
    ev = json.loads((ROOT / "output/max/byte_identity_evidence.json")
                    .read_text(encoding="utf-8"))
    victim = sorted(ev["sha256"])[0]
    ev["sha256"][victim] = "0" * 64
    f = tmp_path / "ev.json"
    f.write_text(json.dumps(ev), encoding="utf-8")
    g = BM.byte_identical(f)                       # الحارسُ يُشغَّل، لا يُحاكى
    assert not g["passes"] and g["differing"] == [victim]


def test_poison_byte_identical_falls_when_the_evidence_is_absent(tmp_path):
    """السمّ: لا شهادةَ تشغيلٍ ثانٍ ⟶ لا يمرّ صامتًا، بل يُعلن غيابَه."""
    g = BM.byte_identical(tmp_path / "nothing.json")
    assert not g["passes"]
    assert g["state"] == "NOT_AVAILABLE:NO_SECOND_RUN_RECORDED"


def test_poison_byte_identical_falls_on_a_file_missing_from_the_evidence(tmp_path):
    """السمّ: يُحذف ملفٌّ من الشهادة ⟶ يُسمّى الغائب، ولا يُعدّ مطابقًا."""
    ev = json.loads((ROOT / "output/max/byte_identity_evidence.json")
                    .read_text(encoding="utf-8"))
    dropped = sorted(ev["sha256"])[0]
    del ev["sha256"][dropped]
    f = tmp_path / "ev.json"
    f.write_text(json.dumps(ev), encoding="utf-8")
    g = BM.byte_identical(f)
    assert not g["passes"] and g["not_in_evidence"] == [dropped]


def test_the_evidence_names_the_command_that_produced_it():
    ev = json.loads((ROOT / "output/max/byte_identity_evidence.json")
                    .read_text(encoding="utf-8"))
    assert "aslot all" in ev["command"] and ev["exit_code"] == 0
    assert ev["denominator"] == len(ev["sha256"]) == len(BM.AXES)


# -------------------------------------------------------------- التقرير
def test_the_nazila_header_is_at_the_head_not_the_tail():
    """«ويُطبع في صدر كلّ تقرير، لا في ذيله»."""
    doc = (ROOT / "output/max/03_report.md").read_text(encoding="utf-8")
    head = doc.split("## ", 1)[0]
    for key in ("NAZILA_REGENERATED", "NAZILA_SCORE", "AXIS_BYTE_IDENTITY",
                "VENDOR_UNTOUCHED", "CLAIM_PROJECT_FINISHED"):
        assert key in head, key


def test_every_edit_names_a_poison_that_exists():
    for k, e in BM.EDITS.items():
        path, _, test = e["poison"].partition("::")
        f = ROOT / path
        assert f.is_file(), f"{k}: {path}"
        assert f"def {test}(" in f.read_text(encoding="utf-8"), f"{k}: {test}"


# ---------------------------------- الشهادةُ تُشغَّل، ولا تُكتب بيد
def test_the_byte_identity_evidence_is_produced_by_a_script_not_by_hand():
    """`MEASURED_NOT_PRESET` على الشهادة نفسِها.

    شهادةٌ تقول «تشغيلان» وقد كُتبت بيدٍ تشهد بما لم ترَ. فالمنتِجُ
    موجودٌ، والشهادةُ تحمل وسمَ أنّ التشغيلَين قِيسا لا أُعلنا.
    """
    p = ROOT / "scripts/build_byte_identity.py"
    assert p.is_file(), "لا منتِجَ للشهادة — فهي مكتوبةٌ بيد"
    ev = json.loads((ROOT / "output/max/byte_identity_evidence.json")
                    .read_text(encoding="utf-8"))
    assert ev.get("runs_are_measured_not_declared") is True
    assert ev["differing_between_runs"] == []


def test_the_supersession_history_accumulates_and_is_not_overwritten():
    """التاريخُ يُراكم — وحقلٌ واحدٌ يُكتب فوق سابقه يمحو واقعةً بواقعة."""
    ev = json.loads((ROOT / "output/max/byte_identity_evidence.json")
                    .read_text(encoding="utf-8"))
    hist = ev["supersessions"]
    tasks = [x["task"] for x in hist]
    assert len(tasks) == len(set(tasks)), tasks
    assert "TANWEEN_UNFOLD_APPLY" in tasks, "واقعةُ التنوين لا تُمحى"
    assert ev["baseline_superseded_by"] == hist[-1]
    for x in hist:
        assert x["reason"] and 0 <= x["count"] <= x["of"]


def test_the_absolute_path_is_gone_from_the_axis_one_measures():
    """`B11` في موضعه الفائت: مسارٌ مطلقٌ يجعل ملفَّ المقاييس تابعًا للآلة."""
    m = json.loads((ROOT / "reports/axis_1_normalization/AXIS_1_MEASURES.json")
                   .read_text(encoding="utf-8"))
    src = m["policy_source"]
    assert not src.startswith("/"), src
    assert not src.startswith("OUTSIDE_TREE:"), src
    assert (ROOT / src).is_file(), src


def test_the_named_examples_are_ordered_so_a_reader_can_find_them(tmp_path):
    """مثالٌ يُساق شاهدًا يجب أن يجده القارئُ حين يُعيد التشغيل.

    كان المرورُ على مجموعةٍ، فترتيبُها ترتيبُ التلبيد ويتبدّل بتبدّل
    `PYTHONHASHSEED` — والأعدادُ ثابتةٌ والعشرةُ المسمّاةُ تتبدّل.
    """
    import subprocess
    import sys
    p = ROOT / "output/tanween/02_after.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل measure_tanween_after بعدُ")
    named = json.loads(p.read_text(encoding="utf-8"))["across_axes"]["axis2"]["named"]
    pos = [x["position"] for x in named]
    # الترتيبُ ترتيبُ المفتاح `(سورة، آية، كلمة)` نصًّا — لا ترتيبُ
    # السلسلة الموصولة بـ`:`. فـ`('10','3','20')` قبل `('10','32','8')`،
    # و`"10:3:20"` بعد `"10:32:8"`. والمقابلةُ بالمفتاح لا بالسلسلة.
    keys = [tuple(x.split(":")) for x in pos]
    assert keys == sorted(keys), "الأمثلةُ غيرُ مرتّبة — تتبدّل بين تشغيلَين"
    # ويُشغَّل بذرةٌ أخرى فعلًا، ولا يُكتفى بالترتيب دعوى
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONHASHSEED="1")
    r = subprocess.run([sys.executable, "scripts/measure_tanween_after.py",
                        "--out", str(tmp_path)],
                       cwd=str(ROOT), env=env, capture_output=True, text=True)
    other = tmp_path / "02_after.json"
    if r.returncode != 0 or not other.is_file():
        pytest.skip(f"لم يُشغَّل بالبذرة الأخرى: {r.stderr[-200:]}")
    pos2 = [x["position"] for x in
            json.loads(other.read_text(encoding="utf-8"))
            ["across_axes"]["axis2"]["named"]]
    assert pos == pos2, "الأمثلةُ تبدّلت بتبدّل PYTHONHASHSEED"


def test_no_poison_is_bound_to_one_named_environment():
    """`B11` رابعةً: سمٌّ يُشغّل بيئةً باسمها لا يُشغَّل إلا لمن يملكها.

    وأثرُه أخطرُ من مسارٍ في تقرير: مالكُ القاعدة لا يستطيع تشغيلَ سمِّها،
    فيقرأ حكمًا لا يملك التحقّقَ منه. والمفسِّرُ يُؤخذ من `sys.executable`
    — وهو الذي يُشغَّل الآن، فيصدق على كلّ بيئة.
    """
    import ast
    bad = []
    for p in sorted((ROOT / "tests_taaqol").glob("test_*.py")):
        tree = ast.parse(p.read_text(encoding="utf-8"))
        for n in ast.walk(tree):
            # سلاسلُ الشرح مستثناةٌ: الأمرُ المنشورُ يُكتب باسم البيئة
            # ليُنسخ ويُشغَّل، وذلك وصفٌ لا تشغيل.
            if isinstance(n, ast.Constant) and isinstance(n.value, str) \
                    and ".venv" in n.value and "/bin/" in n.value:
                bad.append(f"{p.name}:{n.lineno}")
    assert not bad, bad


def test_a_round_that_moved_nothing_records_no_supersession():
    """تجديدٌ لم يقع لا يُسجَّل — وإلا شهد الجردُ بوقائعَ لم تقع."""
    ev = json.loads((ROOT / "output/max/byte_identity_evidence.json")
                    .read_text(encoding="utf-8"))
    for s in ev["supersessions"]:
        assert s["count"] > 0, s["task"]
