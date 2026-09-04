"""سمومُ `X1..X7` وحارسُ السقف — كلُّ طريقٍ محرَّمةٍ تُسلَك ويُثبت ردُّها.

**لماذا سبعةٌ بأعيانها.** ليست تحذيراتٍ عامّة: كلُّ واحدةٍ منها وقعت مرّةً
في هذا العمل أو كادت. فطريقٌ محرَّمةٌ بلا سُمٍّ يُثبت ردَّها ليست محرَّمةً،
بل مذكورة.

**و`G10 CEILING_IS_DERIVED`.** السقفُ مشتقٌّ من `cells.csv` لا مكتوبٌ بيد:
يُبدَّل تصنيفُ خانةٍ واحدة ويُشترط تغيُّرُ السقف. فسقفٌ لا يتحرّك بتغيُّر
مصدره ثابتٌ مطبوعٌ يُقرأ قياسًا، وهو دعوى.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
CLOSURE = ROOT / "output" / "closure"
NAZILA = ROOT / "output" / "nazila_result"
REMED = ROOT / "output" / "remediation"


def load(name: str, rel: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def bc():
    return load("bclo", "scripts/build_closure.py")


@pytest.fixture(scope="module")
def bno():
    sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))
    return load("bno2", "scripts/build_nazila_outputs.py")


@pytest.fixture(scope="module")
def brem():
    sys.path.insert(0, str(ROOT / "src"))
    return load("brem2", "scripts/build_remediation.py")


@pytest.fixture(scope="module")
def ceiling():
    p = CLOSURE / "00_ceiling.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل مولّدُ الإغلاق بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def scores():
    return json.loads((NAZILA / "scores.json").read_text(encoding="utf-8"))


def write_cells(path: Path, rows: list[dict]) -> Path:
    cols = ["section", "field", "status", "value", "source", "reason",
            "reason_family"]
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=cols)
        w.writeheader()
        for r in rows:
            w.writerow({c: r.get(c, "") for c in cols})
    return path


def cell(status="FROM_CODE", family="", reason=""):
    return {"section": "س", "field": "ح", "status": status, "value": "1",
            "source": "عدٌّ", "reason": reason, "reason_family": family}


# ── G10 · السقفُ مشتقٌّ لا مكتوب ────────────────────────────────────────
def test_the_ceiling_is_derived_from_the_cells_file(bc, tmp_path):
    """السمُّ: يُبدَّل تصنيفُ خانةٍ واحدة، فيلزم أن يتحرّك السقف."""
    base = [cell() for _ in range(3)] + [
        cell("NOT_AVAILABLE", "NOT_EMITTED_BY_RUNNER", "NOT_EMITTED_BY_RUNNER"),
        cell("NOT_AVAILABLE", "HUMAN_DECLARED_ONLY", "HUMAN_DECLARED_ONLY")]
    a = bc.derive_ceiling(write_cells(tmp_path / "a.csv", base))

    moved = [dict(r) for r in base]
    moved[3] = cell("NOT_AVAILABLE", "HUMAN_DECLARED_ONLY",
                    "HUMAN_DECLARED_ONLY")
    b = bc.derive_ceiling(write_cells(tmp_path / "b.csv", moved))

    assert a["absolute_ceiling_percent"] != b["absolute_ceiling_percent"], (
        "السقفُ لم يتحرّك بتغيُّر مصدره — فهو مكتوبٌ لا مشتقّ")
    assert a["never_closable_by_code"]["cells"] == 1
    assert b["never_closable_by_code"]["cells"] == 2


def test_an_unknown_reason_family_stops_the_derivation(bc, tmp_path):
    """أسرةٌ خارج الجرد المغلق لا تُنسب إلى مالكٍ بالتخمين — بل توقف."""
    rows = [cell(), cell("NOT_AVAILABLE", "SOMETHING_NEW", "SOMETHING_NEW")]
    with pytest.raises(bc.Blocked) as e:
        bc.derive_ceiling(write_cells(tmp_path / "x.csv", rows))
    assert "UNKNOWN_REASON_FAMILY" in str(e.value)


def test_an_empty_cells_file_stops_instead_of_scoring_zero(bc, tmp_path):
    """جردٌ فارغٌ يقف. وقسمةٌ على صفرٍ أهونُ من سقفٍ من لا شيء."""
    with pytest.raises(bc.Blocked):
        bc.derive_ceiling(write_cells(tmp_path / "e.csv", []))


def test_the_real_ceilings_match_the_owner_stated_figures(ceiling):
    """السقوفُ الأربعةُ مشتقّةٌ، وتُقابَل بما أعلنه المالك — فإن خالفت أُعلن."""
    steps = {s["step"]: s for s in ceiling["ceilings"]}
    assert steps["TODAY"]["grounded"] == 207
    assert steps["+C5"]["grounded"] == 242
    assert steps["+C5_ENTRY_BOUNDARY"]["grounded"] == 249
    assert steps["+C1"]["grounded"] == 266
    assert ceiling["never_closable_by_code"]["cells"] == 26
    assert ceiling["owned_by_this_tool"] == 0


def test_nothing_in_the_not_available_set_is_ours(ceiling):
    """`ما تملك الأداةُ إغلاقَه = صفر` — وهو جوهرُ التقرير كلِّه."""
    owners = set(ceiling["not_available_by_owner"])
    assert owners <= {"SONAISO", "HUMAN", "DR_HUSSEIN"}
    assert "OWNED_BY_AGENT" not in owners
    assert sum(ceiling["not_available_by_owner"].values()) == 85


# ── X1 · نقلُ خانةٍ بين أسر الأسباب ────────────────────────────────────
def test_x1_a_family_move_is_reported_against_the_previous_round(bno):
    class C:
        def __init__(self, reason=""):
            self.reason, self.value = reason, (None if reason else 1)
            self.section = self.field = self.source = "x"

        @property
        def from_code(self):
            return not self.reason

    cells = [C("HUMAN_DECLARED_ONLY"), C("HUMAN_DECLARED_ONLY")]
    g = {"G1_REPRODUCIBLE": True, "G2_LEDGER_CLOSES": True,
         "G3_NO_BROKEN": True, "G4_NO_OWNER_INFERENCE": True,
         "G5_HTML_CSV_AGREE": True, "_broken": [], "_owner_cells_decided": []}
    prev = {"not_available_by_reason": {"NOT_OPENED:HUKM": 2}}
    moves = bno.score(cells, g, prev)["reason_family_moves_vs_previous_round"]
    assert moves["NOT_OPENED:HUKM"] == {"previous_round": 2, "this_round": 0}
    assert moves["HUMAN_DECLARED_ONLY"] == {"previous_round": 0,
                                            "this_round": 2}


def test_x1_did_not_happen_this_round(scores):
    assert scores["reason_family_moves_vs_previous_round"] == {}


# ── X2 · نثرٌ بشريٌّ في خانةٍ يُدَّعى أنّها من الكود ─────────────────────
HUMAN_PROSE_MARKS = ("يجب", "ينبغي", "الراجح", "الأظهر", "generated by",
                     "code constants", "يُستنتج", "الأقرب")


def test_x2_no_from_code_cell_carries_human_prose():
    """`G9` — «من الكود» لفظًا لا معنًى: ثابتٌ نصّيٌّ يحمل تحليلًا بشريًّا."""
    with (NAZILA / "cells.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    bad = [r["field"] for r in rows if r["status"] == "FROM_CODE"
           and any(w in r["value"] for w in HUMAN_PROSE_MARKS)]
    assert bad == [], f"خاناتٌ تحمل نثرًا بشريًّا وتُعدّ من الكود: {bad}"


def test_x2_the_guard_catches_a_planted_prose_cell():
    """وسمٌّ على الحارس: تُدسّ خانةٌ بنثرٍ بشريّ، فيلزم أن تُلتقط."""
    planted = [{"status": "FROM_CODE", "field": "مدسوسة",
                "value": "الراجح أنّ الحكم كذا"}]
    caught = [r["field"] for r in planted if r["status"] == "FROM_CODE"
              and any(w in r["value"] for w in HUMAN_PROSE_MARKS)]
    assert caught == ["مدسوسة"]


# ── X3 · حذفُ عمودٍ أو خانةٍ لفراغها ───────────────────────────────────
def test_x3_dropping_empty_columns_shrinks_the_denominator(bno):
    with (NAZILA / "records.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    kept = [c for c in rows[0] if {r[c] for r in rows} != {bno.EMPTY}]
    assert len(rows[0]) == 24
    assert len(kept) == 21, "حذفُ الفارغ يُنزل المقامَ من ٢٤ إلى ٢١"


# ── X4 · صفرٌ مشتقٌّ من مرحلةٍ لم تُفتح ────────────────────────────────
def test_x4_no_cell_from_a_closed_stage_carries_a_value():
    """`RELATION_CLOSED_COUNT = 0` كان يُقرأ «قِيس فكان صفرًا» ولم يُقس."""
    with (NAZILA / "cells.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    offending = [r["field"] for r in rows
                 if r["reason_family"] == "NOT_OPENED" and r["value"]]
    assert offending == [], offending
    closed = [r for r in rows if r["reason_family"] == "NOT_OPENED"]
    assert len(closed) == 17
    assert all(r["status"] == "NOT_AVAILABLE" for r in closed)


def test_x4_relation_closed_count_is_named_not_zeroed():
    with (NAZILA / "cells.csv").open(encoding="utf-8", newline="") as fh:
        rows = {r["field"]: r for r in csv.DictReader(fh)}
    r = rows["RELATION_CLOSED_COUNT"]
    assert r["status"] == "NOT_AVAILABLE"
    assert r["reason"] == "NOT_OPENED:RELATION_CLOSURE"
    assert r["value"] == ""


# ── X5 · لَفُّ المشغّل ──────────────────────────────────────────────────
def test_x5_the_vendor_is_untouched_and_the_gate_falls_if_it_is_not(bc,
                                                                    monkeypatch):
    assert bc.gate_g1()["passes"] is True
    monkeypatch.setattr(bc, "PIN", "0" * 40)
    assert bc.gate_g1()["passes"] is False


# ── X6 · جمعُ العلامات أو متوسّطُها ────────────────────────────────────
def test_x6_the_three_scores_have_three_different_denominators(scores,
                                                               ceiling):
    remed = json.loads((REMED / "01_ledger.json").read_text(encoding="utf-8"))
    denominators = {scores["CELLS_TOTAL"], remed["closure"]["TOTAL"], 16}
    assert len(denominators) == 3, "مقامان تساويا — فالفصلُ لم يعد قائمًا"
    report = (CLOSURE / "03_report.md").read_text(encoding="utf-8")
    assert "لا تُجمع العلامتان ولا يُؤخذ متوسّطهما" in report
    assert str(scores["CELLS_TOTAL"]) in report
    assert str(remed["closure"]["TOTAL"]) in report


def test_x6_the_two_ledgers_report_at_the_same_precision(scores):
    """تقريبان مختلفان يجعلان الفرقَ يُقرأ قياسًا وهو تقريب."""
    remed = json.loads((REMED / "01_ledger.json").read_text(encoding="utf-8"))
    for v in (scores["CLOSURE_POTENTIAL"],
              remed["closure"]["CLOSURE_POTENTIAL"]):
        assert round(v, 1) == v


# ── X7 · بندُ (ج) يُعدّ منفَّذًا لأنّه أُعلن ────────────────────────────
def test_x7_declaring_is_not_repairing(brem):
    with pytest.raises(brem.Blocked) as e:
        brem.Item("Cx", "عيبٌ في المصدر", "OUT_OF_JURISDICTION", "DONE",
                  evidence={"a": 1})
    assert "AUTHORITY_VIOLATION" in str(e.value)


def test_x7_the_report_separates_declared_from_repaired():
    remed = json.loads((REMED / "01_ledger.json").read_text(encoding="utf-8"))
    out = [i for i in remed["items"]
           if i["authority"] == "OUT_OF_JURISDICTION"]
    assert out and {i["status"] for i in out} <= {"DECLARED", "NOT_CHOSEN"}
    assert not any(i["status"] == "DONE" for i in out)


def test_every_forbidden_path_is_named_with_its_guard(bc):
    """الجردُ مغلقٌ سبعةً، ولكلٍّ حارسٌ مسمًّى — لا واحدةَ بلا حارس."""
    assert sorted(bc.FORBIDDEN_PATHS) == ["X1", "X2", "X3", "X4", "X5",
                                          "X6", "X7"]
    assert all(guard for _, guard in bc.FORBIDDEN_PATHS.values())


# ── G5 · بنيويٌّ لا نصّيّ ───────────────────────────────────────────────
def test_g5_holds_and_is_structural(scores, bno):
    assert scores["gates"]["G5_HTML_CSV_AGREE"] is True
    assert scores["html_csv_missing"] == []


def test_g5_catches_a_cell_that_has_no_row_in_the_page(bno):
    """سمٌّ: خانةٌ لا صفَّ لها في الصفحة، ولو ورد اسمُها في شرح."""
    class C:
        def __init__(self, section, field):
            self.section, self.field = section, field
            self.value, self.source, self.reason = 1, "عدٌّ", ""

        @property
        def from_code(self):
            return True

    cells = [C("س", "موجودة"), C("س", "غائبة")]
    page = ('<tr data-section="س" data-field="موجودة"></tr>'
            '<p>وذكرُ «غائبة» في شرحٍ لا يجعلها خانة.</p>')
    missing = bno.html_csv_disagreement(page, cells)
    assert missing == ["س/غائبة"]


# ── المعيارُ الخامس · العلامةُ لم ترتفع، ويُقال صراحةً ─────────────────
def test_the_nazila_score_did_not_rise(scores):
    assert scores["GROUNDED"] == 207
    assert scores["CELLS_TOTAL"] == 292
    assert scores["CLOSURE_POTENTIAL"] == 70.9


def test_the_report_says_the_score_was_not_improved():
    report = (CLOSURE / "03_report.md").read_text(encoding="utf-8")
    assert "لم تُحسَّن علامةُ هذه الوثيقة، ولا تُحسَّن" in report
    assert "ما تملك الأداةُ إغلاقَه = 0" in report


def test_every_closure_item_declares_zero_effect_on_the_nazila_score():
    its = json.loads((CLOSURE / "02_items.json")
                     .read_text(encoding="utf-8"))["items"]
    assert its
    for i in its:
        assert "صفر" in i["effect_on_nazila_score"], i["ident"]


def test_the_b5_transition_matrix_closes_without_remainder():
    t = json.loads((CLOSURE / "transition_b5.json").read_text(encoding="utf-8"))
    assert t["closes"] is True
    assert t["net"] == 0
    assert sum(t["with_declared_witness"].values()) == t["denominator"]
    assert sum(t["without_witness"].values()) == t["denominator"]
    assert t["raised_not_decided"] is True
