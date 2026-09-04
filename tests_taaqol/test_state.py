"""سمومُ `STATE_OF_PROJECT` — والتقريرُ إسقاطٌ لا سلطة.

فحارسُه لا يُثبت صحّةَ حكمٍ، بل **اكتمالَ الجرد**: مرحلةٌ لا تُحذف،
وقاعدةٌ لا تسقط، وبندُ مالكٍ لا يغيب، و«تمّ» لا يمرّ بلا أثر.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
S = ROOT / "output" / "state"


def load(name: str, rel: str):
    for extra in ("src", "scripts"):
        sys.path.insert(0, str(ROOT / extra))
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


BS = load("build_state", "scripts/build_state.py")


@pytest.fixture(scope="module")
def bs_rules_source() -> dict:
    """بيتُ القواعد نفسُه — يُقرأ من `build_exec_now`، لا من مخرَجٍ مكتوب."""
    return dict(load("bex_rules_home", "scripts/build_exec_now.py").RULES)


def j(name: str) -> dict:
    p = S / name
    if not p.is_file():
        pytest.skip("لم يُشغَّل build_state بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


# ═══════════════════════ الوثائقُ — سلطةٌ واحدةٌ لكلٍّ ═══════════════════
def test_every_document_has_exactly_one_declared_authority():
    d = j("00_documents.json")
    assert d["authority_unclear"] == []
    for x in d["documents"]:
        assert x["authority"] in d["authorities_closed_list"], x["path"]


def test_poison_an_authority_outside_the_closed_list_is_flagged(monkeypatch):
    """السمُّ: تُسنَد سلطةٌ ليست من الخمس ⟶ `AUTHORITY_UNCLEAR`."""
    monkeypatch.setitem(BS.DOCUMENTS, "README.md", "SOMETHING_ELSE")
    d = BS.documents({})
    assert "README.md" in d["authority_unclear"]
    row = next(x for x in d["documents"] if x["path"] == "README.md")
    assert row["authority"] == "AUTHORITY_UNCLEAR"


def test_dating_is_measured_on_the_owners_tree_not_the_container():
    """الحاويةُ بلا `git` — فقياسُ التأريخ فيها خبرٌ عنها لا عن الوثائق."""
    d = j("00_documents.json")
    assert d["dating_measured_on"] == "~/final-september"
    assert d["dating_command"]
    assert d["dated"] > 0, "لو قيس في الحاوية لكان صفرًا"


def test_poison_absent_dating_is_not_read_as_dated():
    """السمُّ: يُنزَع القياسُ ⟶ لا يُقرأ «مؤرَّخًا»، بل `NOT_MEASURED`."""
    g = BS.git_dated("README.md", {})
    assert g["dated"] is None and "NOT_MEASURED" in g["note"]


def test_the_evidence_authority_has_no_dated_home():
    """بندٌ يُرفع: دفاترُ الإثبات في حاويةٍ تُستردّ، وغائبةٌ عن المستودع."""
    d = j("00_documents.json")
    assert "EVIDENCE" in d["undated_by_authority"]
    assert len(d["undated_by_authority"]["EVIDENCE"]) >= 5
    assert "EVIDENCE" in d["finding"]


# ═══════════════════════ المراحل — إحدى عشرةَ لا تُحذف ═════════════════
def test_all_eleven_phases_are_present():
    p = j("01_phases.json")
    assert set(p["phases"]) == set(BS.PHASES) == set(p["order"])
    assert p["count"] == 11


def test_poison_a_deleted_phase_falls():
    """السمُّ: تُحذف مرحلةٌ ⟶ يسقط `G_ALL_T_PHASES_PRESENT`."""
    p = j("01_phases.json")
    ph = {"phases": {k: v for k, v in p["phases"].items() if k != "T-9"},
          "by_state": {}, "stages_opened": "1/16",
          "runtime_implemented": [], "count": 10}
    g = BS.guards({"authority_unclear": [], "undated": []}, ph,
                  {"present": 9, "poisoned": 9, "unpoisoned": [], "rules": {}},
                  {"count": 1, "closed": 1, "pending": 0,
                   "out_of_jurisdiction": 0, "sum": 1, "closes": True,
                   "effect_unmeasured": []},
                  {"scores": {}})
    x = next(y for y in g if y["guard"] == "G_ALL_T_PHASES_PRESENT")
    assert not x["passes"] and x["missing"] == ["T-9"]


def test_t9_and_t10_are_measured_not_assumed():
    p = j("01_phases.json")
    for k in ("T-9", "T-10"):
        v = p["phases"][k]
        assert v["state"] == "NOT_STARTED"
        assert v["measured_not_assumed"] is True
        assert v["command"].startswith("grep")
        assert v["artifact"] is None


def test_t9_and_t10_really_have_no_trace_in_the_tree():
    """والدعوى تُشغَّل: يُبحث عنهما فعلًا في الوثائق الثلاث."""
    hits = []
    for rel in ("HANDOFF.md", "README.md", "docs/ARCHITECTURE.md"):
        p = ROOT / rel
        if not p.is_file():
            continue
        text = p.read_text(encoding="utf-8")
        for token in ("T-9", "T-10"):
            if token in text:
                hits.append(f"{rel}:{token}")
    assert hits == [], f"وُجدت: {hits} — فالحالُ ليست NOT_STARTED"


def test_every_done_phase_carries_evidence_and_a_command():
    """`NO_PROSE_DONE` — «تمّ» بلا أثرٍ وأمرٍ ليس «تمّ»."""
    p = j("01_phases.json")
    for k, v in p["phases"].items():
        if v["state"].startswith("DONE"):
            assert v["evidence"], k
            assert v["command"], k
            assert v["artifact"], k


def test_poison_a_done_without_evidence_is_caught():
    """السمُّ: يُدسّ `DONE` بلا أثر ⟶ يسقط `G_EVERY_DONE_HAS_EVIDENCE`."""
    ph = {"phases": {"T-X": {"state": "DONE", "evidence": None,
                             "command": None}},
          "by_state": {}, "stages_opened": "", "runtime_implemented": [],
          "count": 1}
    g = BS.guards({"authority_unclear": [], "undated": []}, ph,
                  {"present": 9, "poisoned": 9, "unpoisoned": [], "rules": {}},
                  {"count": 1, "closed": 1, "pending": 0,
                   "out_of_jurisdiction": 0, "sum": 1, "closes": True,
                   "effect_unmeasured": []},
                  {"scores": {}})
    x = next(y for y in g if y["guard"] == "G_EVERY_DONE_HAS_EVIDENCE")
    assert not x["passes"] and x["without_evidence"] == ["T-X"]


# ═════════════════════════ القواعدُ التسع ═════════════════════════════
def test_all_nine_rules_are_present():
    r = j("02_rules.json")
    assert r["declared"] == 9 and r["present"] == 9
    assert set(r["rules"]) == set(BS.RULE_NAMES)


def test_rule_seven_was_widened_to_both_directions():
    """حكمُ المالك: الصيغةُ الأولى في جهةٍ واحدة، فوُسِّعت."""
    r = j("02_rules.json")["rules"]["COUNT_IS_NOT_MEMBERSHIP"]
    assert "في الجهتين" in r["rule"]
    assert r["poison_runs"] is True
    assert "EQUAL_NUMBERS_MAY_BE_DIFFERENT_SETS" not in \
        j("02_rules.json")["rules"]


def test_the_eighth_rule_came_from_the_tanween_round():
    r = j("02_rules.json")
    v = r["rules"]["CLOSED_MATRIX_ON_ONE_COLUMN_IS_NOT_THE_AXIS"]
    assert "3,152" in v["incident"] or "3152" in v["incident"]
    assert v["poison_runs"] is True


def test_the_eighth_rule_lives_in_the_rules_home(bs_rules_source):
    """بيتُ القواعد واحد — و`setdefault` في `build_state` احتياطٌ لا نسخة.

    ولو عاد يعمل لكانت نسختان تشيخان متفرّقتَين: نصٌّ هنا ونصٌّ هناك،
    وهو العيبُ نفسُه الذي فرّق `42` عن `35`.
    """
    assert "CLOSED_MATRIX_ON_ONE_COLUMN_IS_NOT_THE_AXIS" in bs_rules_source


def test_the_ninth_rule_came_from_the_shared_cause_round(bs_rules_source):
    """`SHARED_CAUSE_IS_NOT_SHARED_EFFECT` — بنصّ المالك، وبأساسَين مغلقَين."""
    v = j("02_rules.json")["rules"]["SHARED_CAUSE_IS_NOT_SHARED_EFFECT"]
    r = bs_rules_source["SHARED_CAUSE_IS_NOT_SHARED_EFFECT"]
    assert r["ruled_by"] == "DR_HUSSEIN"
    assert "اتّحادُ العلّة لا يُثبت اتّحادَ الأثر" in v["rule"]
    assert "بالعضويّة إن كان الحقلُ يحتمل" in v["rule"]
    assert r["two_bases"] == ["BY_MEMBERSHIP", "BY_DESIGN"]
    assert "17" in r["incident"] and "42" in r["incident"]
    assert v["poison_runs"] is True


def test_every_named_poison_actually_exists():
    """سمٌّ مذكورٌ لا وجودَ له أسوأُ من `UNPOISONED`."""
    r = j("02_rules.json")
    for name, v in r["rules"].items():
        if v["poison"] == "UNPOISONED":
            continue
        assert v["poison_exists"], f'{name}: {v["poison"]}'


def test_the_unpoisoned_rule_is_declared_not_hidden():
    r = j("02_rules.json")
    assert r["unpoisoned"] == ["FILE_HASH_IS_NOT_CONTENT_HASH"]
    assert r["rules"]["FILE_HASH_IS_NOT_CONTENT_HASH"]["poison_note"]


def test_poison_a_rule_dropped_from_the_table_is_caught(monkeypatch):
    import importlib.util as iu
    spec = iu.spec_from_file_location("bex_probe",
                                      ROOT / "scripts/build_exec_now.py")
    m = iu.module_from_spec(spec)
    sys.modules["bex_probe"] = m
    spec.loader.exec_module(m)
    monkeypatch.delitem(m.RULES, "NO_TEXTUAL_GUARD")
    assert "NO_TEXTUAL_GUARD" not in m.RULES
    # والحارسُ يقرأ الجردَ المُعلَن، فيُبلّغ الغياب
    assert "NO_TEXTUAL_GUARD" in BS.RULE_NAMES


# ══════════════════════ طابورُ المالك — يقفل ═══════════════════════════
def test_the_owner_queue_closes_by_a_second_count():
    q = j("03_owner_queue.json")
    assert q["closed"] + q["pending"] + q["out_of_jurisdiction"] == q["count"]
    assert q["closes"] is True
    assert sum(q["by_status"].values()) == q["count"]


def test_every_item_ever_raised_is_present():
    q = j("03_owner_queue.json")
    idents = {x["ident"] for x in q["items"]}
    for tag in ("B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9",
                "B8.3", "B10", "B11", "B12", "B13", "B14", "B15", "B16",
                "B17", "C1", "C2", "C3", "C4", "C5", "C_PATH",
                "P1", "P2", "P3", "Q4"):
        assert tag in idents, tag


def test_q4_is_asked_with_its_measured_effect_and_not_weighed():
    q = j("03_owner_queue.json")
    x = next(i for i in q["items"] if i["ident"] == "Q4")
    e = x["effect"]
    assert e["raised_on_now"] == 8894
    assert e["of_which_still_pending"] == 818
    assert e["of_which_no_decision_needed"] == 8076
    assert e["narrowed_to"] == 818
    assert x["status"] == "RAISED" and "لا يُرجَّح" in x["not_weighed"]


def test_poison_state_ledger_falls_when_a_status_escapes_the_three_classes():
    q = {"count": 3, "closed": 1, "pending": 1, "out_of_jurisdiction": 0,
         "sum": 2, "closes": False, "effect_unmeasured": []}
    g = BS.guards({"authority_unclear": [], "undated": []},
                  {"phases": {}, "by_state": {}, "stages_opened": "",
                   "runtime_implemented": [], "count": 0},
                  {"present": 9, "poisoned": 9, "unpoisoned": [], "rules": {}},
                  q, {"scores": {}})
    x = next(y for y in g if y["guard"] == "G_STATE_LEDGER_CLOSES")
    assert not x["passes"]


# ═════════════════════ العلاماتُ الأربع — لا تُجمع ═════════════════════
def test_the_four_scores_each_carry_their_own_denominator():
    s = j("05_scores.json")
    assert set(s["scores"]) == {"NAZILA", "TWO_COLUMN", "REMEDIATION",
                                "STAGES"}
    for k, v in s["scores"].items():
        assert v["denominator"], k
    assert s["guard"] == "G_NO_LEDGER_MERGE"


def test_the_two_column_score_is_the_measured_one_not_the_written_one():
    """`MEASURED_NOT_PRESET` — والمقيسُ ٦٤ صفًّا و٨٥٫٩٪، لا ٥٨ و٨٤٫٥٪."""
    s = j("05_scores.json")["scores"]["TWO_COLUMN"]
    assert s["potential"] == 85.9 and s["effective"] == 0
    assert s["fraction"] == "55/64"


def test_the_report_does_not_average_or_sum_the_scores():
    doc = (S / "06_STATE.md").read_text(encoding="utf-8")
    assert "لا مقام" in doc or "لا تُجمع" in doc
    assert "G_NO_LEDGER_MERGE" in doc


# ══════════════════════════ الإسقاطُ لا سلطة ═══════════════════════════
def test_this_report_declares_itself_a_projection():
    doc = (S / "06_STATE.md").read_text(encoding="utf-8")
    assert "AUTHORITY = PROJECTION" in doc
    assert "لا يُنشئ" in doc and "CLAIM_PROJECT_FINISHED = NO" in doc
    d = j("00_documents.json")
    row = next(x for x in d["documents"]
               if x["path"] == "output/state/06_STATE.md")
    assert row["authority"] == "PROJECTION"


def test_no_owner_item_was_decided_by_this_run():
    q = j("03_owner_queue.json")
    owned = [x for x in q["items"] if x["authority"] == "OWNED_BY_OWNER"]
    assert owned
    assert all(x["status"] in ("RAISED", "BLOCKED") for x in owned)


def test_no_residual_kind_was_assigned():
    d = json.loads((ROOT / "data/residual_kind_assignment.json")
                   .read_text(encoding="utf-8"))
    assert set(d["assignments"].values()) == {None}


def test_the_vendor_is_untouched_and_pinned():
    g = BS.vendor_gate()
    assert g["untouched"] and g["matches_pin"]


def test_the_nazila_score_did_not_drift():
    sc = json.loads((ROOT / "output/nazila_result/scores.json")
                    .read_text(encoding="utf-8"))
    assert sc["CLOSURE_POTENTIAL"] == 70.9 and sc["STAGES_OPENED"] == "1/16"


def test_no_printed_fraction_carries_a_none():
    """رقمٌ مطبوعٌ فيه `None` صفرٌ ميّتٌ في ثوبٍ آخر."""
    doc = (S / "06_STATE.md").read_text(encoding="utf-8")
    for line in doc.splitlines():
        if line.startswith("| `") and "None" in line:
            assert "C_PATH" in line, line
    s = j("05_scores.json")["scores"]
    for k, v in s.items():
        assert "None" not in str(v.get("fraction", "")), k


def test_the_law_authority_gap_is_raised_too():
    """ملفُّ الإسناد سلطتُه LAW وهو غائبٌ عن المستودع — بندٌ يُرفع."""
    d = j("00_documents.json")
    assert "LAW" in d["undated_by_authority"]
    assert "data/residual_kind_assignment.json" in d["undated_by_authority"]["LAW"]
    assert "B2" in d["finding_2"]
    doc = (S / "06_STATE.md").read_text(encoding="utf-8")
    assert "residual_kind_assignment.json" in doc


# ══════════════════════ F1 · G_AXES_AGREE ══════════════════════════════
def test_the_correctness_axis_is_present_in_the_state_report():
    """`F1` — ستّةُ محاورَ لا خمسة. وسقوطُ الصحّة يقلب قراءةَ C2 و C3."""
    u = j("04_upstream.json")
    assert u["axes"] == ["cells", "correctness", "ceiling", "cost"]
    for door in ("C1", "C2", "C3", "C4", "C5"):
        v = u["upstream"][door]
        assert v["kind"] == "DOOR"
        for ax in u["axes"]:
            assert ax in v, f"{door}.{ax}"
    assert u["upstream"]["C_PATH"]["kind"] == "NOT_A_DOOR"


def test_the_axes_match_the_doors_ledger_value_by_value():
    u = j("04_upstream.json")
    d = json.loads((ROOT / "output/doors/00_doors.json")
                   .read_text(encoding="utf-8"))
    for door, v in u["upstream"].items():
        if v.get("kind") == "NOT_A_DOOR":
            continue
        src = next(x for x in d["doors"] if x["door"] == door)
        for ax in u["axes"]:
            assert v[ax] == src[ax], f"{door}.{ax}"


def test_c2_and_c3_no_longer_read_as_having_no_effect():
    """الأثرُ الأوّلُ نفسُه: بابٌ بأثرٍ كان يُقرأ بلا أثر."""
    u = j("04_upstream.json")["upstream"]
    assert u["C2"]["correctness"]["inventory_hit_unmarked"] == "11/11"
    assert u["C2"]["correctness"]["inventory_hit_marked"] == "0/17"
    assert u["C3"]["correctness"]["corpus_words_matching"] == 10013
    assert u["C3"]["correctness"]["percent"] == 12.9


def test_poison_a_dropped_axis_is_caught():
    """السمُّ: يُحذف محورٌ من أحدهما ⟶ يسقط `G_AXES_AGREE`."""
    u = j("04_upstream.json")
    poisoned = {"upstream": {k: {a: b for a, b in v.items()
                                 if a != "correctness"}
                             for k, v in u["upstream"].items()}}
    off = BS.axes_agree(poisoned)
    assert off and all("correctness:MISSING_IN_STATE" in x for x in off)


def test_poison_a_changed_axis_value_is_caught():
    u = j("04_upstream.json")
    poisoned = json.loads(json.dumps(u))
    poisoned["upstream"]["C3"]["cells"] = "1/292"
    off = BS.axes_agree(poisoned)
    assert "C3.cells:DIFFERS" in off


def test_the_axes_guard_compares_this_run_not_the_previous_file():
    """الفحصُ الأجوف: حارسٌ يقرأ الملفَّ الذي يكتبه التشغيلُ نفسُه."""
    import inspect
    src = inspect.getsource(BS.axes_agree)
    assert "up: dict | None = None" in src
    assert "المحسوبُ في هذا التشغيل" in src or "لا الملفُّ" in src
    g = j("04_upstream.json")
    assert g  # الملفُّ مكتوب، والحارسُ لا يعتمد عليه


# ══════════════════ F2 · G_DENOMINATOR_DELTA_DECLARED ══════════════════
def test_the_two_column_denominator_series_is_declared():
    d = j("05_scores.json")["scores"]["TWO_COLUMN"]["denominator_delta"]
    assert d["previous_denominator"] == 58
    assert d["current_denominator"] == 64
    assert d["delta_total"] == 6 and d["delta_grounded"] == 6
    assert d["delta_named_plus_delta"] == 0
    assert d["named_plus_delta_constant"] is True


def test_the_growth_is_named_as_measured_not_drift():
    d = j("05_scores.json")["scores"]["TWO_COLUMN"]["denominator_delta"]
    assert "GROUNDED" in d["growth_is_measured_not_drift"]
    assert "مقامَين" in d["so_the_percentages_are_not_comparable"]


def test_the_unverifiable_rounds_carry_their_source():
    """`MEASURED_NOT_PRESET` — روايةٌ لا تُقرأ قياسًا."""
    d = j("05_scores.json")["scores"]["TWO_COLUMN"]["denominator_delta"]
    assert d["unverifiable_rounds"] == [1, 2]
    assert d["sources"]["3"] == "MEASURED"
    assert d["live_check"]["matches_measured"] is True
    for r in d["series"]:
        if r["source"] == "MEASURED":
            assert r["artifact"]
        else:
            assert r["artifact"] is None


def test_poison_a_moved_denominator_without_a_delta_field_falls():
    """السمُّ: يُبدَّل المقامُ بلا إعلان ⟶ يسقط."""
    sc = {"scores": {"X": {"denominator_moved": True}}}
    g = BS.guards({"authority_unclear": [], "undated": []},
                  {"phases": {}, "by_state": {}, "stages_opened": "",
                   "runtime_implemented": [], "count": 0},
                  {"present": 9, "poisoned": 9, "unpoisoned": [], "rules": {}},
                  {"count": 1, "closed": 1, "pending": 0,
                   "out_of_jurisdiction": 0, "sum": 1, "closes": True,
                   "effect_unmeasured": []},
                  sc, {"upstream": {}})
    x = next(y for y in g if y["guard"] == "G_DENOMINATOR_DELTA_DECLARED")
    assert not x["passes"] and x["undeclared"] == ["X"]


def test_the_owner_table_denominator_is_distinguished_from_pending():
    """`DENOMINATOR_IS_PINNED` — «١٧ موقوفًا» فوق جدولٍ من ١٥ صفًّا."""
    q = j("03_owner_queue.json")
    owner_rows = [x for x in q["items"] if x["authority"] == "OWNED_BY_OWNER"]
    assert len(owner_rows) != q["pending"], "لو تساويا لسقط معنى الاختبار"
    doc = (S / "06_STATE.md").read_text(encoding="utf-8")
    assert "ومقامان لا مقام" in doc
    assert f'**{len(owner_rows)}** صفًّا' in doc
