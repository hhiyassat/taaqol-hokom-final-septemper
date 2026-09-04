"""يسمّم حرّاسَ مخرجات النازلة، ويُثبت سقوطَها — وكلُّها تشغيلٌ لا نصّ.

**العيبُ الذي وُضعت له.** طُبعت العلامةُ `٥٢٪` في تقريرٍ عن النازلة، وهي
علامةُ **دفتر الإصلاح** — مقامُها خمسةٌ وعشرون بندًا، ومقامُ النازلة
اثنتان وتسعون ومئتان خانة. فهما رقمان بمقامين، عُرضا كواحد. والحارسُ هنا
يفصل المقامَين فصلًا لا يُلبَس.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import re
import sys
from collections import Counter
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "build_nazila_outputs.py"
OUT = ROOT / "output" / "nazila_result"
REMED = ROOT / "output" / "remediation" / "01_ledger.json"


def load():
    sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))
    spec = importlib.util.spec_from_file_location("bno", GEN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bno"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return load()


@pytest.fixture(scope="module")
def scores():
    p = OUT / "scores.json"
    if not p.is_file():
        pytest.skip(f"لم يُشغَّل المولّد بعدُ: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def records():
    p = OUT / "records.csv"
    if not p.is_file():
        pytest.skip("records.csv غيرُ موجود")
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def cells():
    with (OUT / "cells.csv").open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


@pytest.fixture(scope="module")
def page():
    return (OUT / "nazila_result.html").read_text(encoding="utf-8")


# ── المقامان لا يختلطان ────────────────────────────────────────────────
def test_the_nazila_score_is_not_the_remediation_score(scores):
    """`٧١٪` مقامُها خاناتُ الوثيقة، و`٥٢٪` مقامُها بنودُ الدفتر."""
    assert scores["CELLS_TOTAL"] == 292
    if REMED.is_file():
        r = json.loads(REMED.read_text(encoding="utf-8"))["closure"]
        assert r["TOTAL"] != scores["CELLS_TOTAL"]
        assert r["CLOSURE_POTENTIAL"] != scores["CLOSURE_POTENTIAL"]


def test_the_score_is_never_printed_without_its_denominator(page):
    """علامةٌ وحدَها هي الرقمُ الواحدُ بمقامين الذي نلاحقه."""
    for token in ("CLOSURE_EFFECTIVE", "CLOSURE_POTENTIAL", "GROUNDED",
                  "NAMED", "BROKEN", "STAGES_OPENED"):
        assert token in page, token
    assert "/292" in page and "1<small>/16</small>" in page


def test_the_denominator_note_names_the_other_ledger(scores):
    assert "output/remediation" in scores["denominator_note"]


# ── records.csv — لا عمودَ يُحذف لفراغه ────────────────────────────────
def test_records_carry_every_field_by_name(records, mod):
    """أربعةٌ وعشرون حقلًا بأسمائها من `StageExecutionRecord`، بلا نقص."""
    sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))
    from taaqqul_slot_geometry.runtime.execution_record import (
        StageExecutionRecord,
    )
    declared = list(StageExecutionRecord.__dataclass_fields__)
    assert list(records[0]) == declared
    assert len(declared) == 24


def test_records_are_sixteen_stages_by_ten_tokens(records):
    assert len(records) == 160
    assert len({r["stage_id"] for r in records}) == 16
    assert len({r["token_id"] for r in records}) == 10
    pairs = Counter((r["token_id"], r["stage_id"]) for r in records)
    assert set(pairs.values()) == {1}, "خليّةٌ مكرّرةٌ أو ناقصة"


def test_an_empty_field_is_named_not_blanked(records, mod):
    """`EMPTY_IN_RECORD` لا خانةٌ بيضاء: الفراغُ المقيس خبرٌ، لا نقص."""
    empty_cols = {"span_id", "failure_code", "residuals_before"}
    for col in empty_cols:
        assert {r[col] for r in records} == {mod.EMPTY}
    assert not any(v == "" for r in records for v in r.values())


def test_dropping_an_empty_column_would_be_caught(records, mod):
    """سمٌّ: تُحذف الأعمدةُ الفارغةُ كلَّها، فيسقط عدُّ الأعمدة."""
    kept = [c for c in records[0] if {r[c] for r in records} != {mod.EMPTY}]
    assert len(kept) < len(records[0])
    assert len(kept) == 21, "ثلاثةُ أعمدةٍ فارغةٌ كلَّها — وتُطبع مع ذلك"


# ── cells.csv ──────────────────────────────────────────────────────────
def test_cells_close_by_status(cells, scores):
    by = Counter(r["status"] for r in cells)
    assert len(cells) == scores["CELLS_TOTAL"] == 292
    assert by["FROM_CODE"] == scores["GROUNDED"]
    assert by["NOT_AVAILABLE"] == scores["NAMED"]
    assert by["FROM_CODE"] + by["NOT_AVAILABLE"] == len(cells)


def test_every_not_available_cell_names_a_family_from_the_closed_five(cells):
    fams = {r["reason_family"] for r in cells if r["status"] == "NOT_AVAILABLE"}
    assert fams <= {"NOT_OPENED", "NOT_EMITTED_BY_RUNNER",
                    "NOT_CONSTRUCTED_IN_SOURCE", "HUMAN_DECLARED_ONLY",
                    "OWNER_DECISION"}
    assert all(r["reason"] for r in cells if r["status"] == "NOT_AVAILABLE")


def test_no_from_code_cell_is_blank(cells):
    """`BROKEN = 0` — خانةٌ مقيسةٌ بلا قيمةٍ تُقرأ صفرًا وهي فراغ."""
    blank = [r["field"] for r in cells
             if r["status"] == "FROM_CODE" and r["value"] == ""]
    assert blank == [], blank


# ── الإقفالُ بعدٍّ ثانٍ من الملفَّين المكتوبَين ──────────────────────────
def test_the_ledger_closes_by_recounting_the_written_files(scores):
    rc = scores["recount_from_written_files"]
    assert rc["records_csv_rows"] == 160
    assert rc["records_csv_columns"] == 24
    assert rc["cells_csv_rows"] == scores["CELLS_TOTAL"]
    assert rc["closes"] is True


def test_a_failed_gate_zeroes_the_effective_score(mod):
    """سمٌّ على البوّابات: تسقط واحدةٌ ⟶ `CLOSURE_EFFECTIVE = 0`، لا خصم."""
    class C:
        def __init__(self, reason=""):
            self.reason, self.value = reason, (None if reason else 1)
            self.section = self.field = self.source = "x"

        @property
        def from_code(self):
            return not self.reason

    cells = [C(), C(), C("OWNER_DECISION"), C("NOT_EMITTED_BY_RUNNER")]
    good = {"G1_REPRODUCIBLE": True, "G2_LEDGER_CLOSES": True,
            "G3_NO_BROKEN": True, "G4_NO_OWNER_INFERENCE": True,
            "_broken": [], "_owner_cells_decided": []}
    bad = {**good, "G1_REPRODUCIBLE": False}
    assert mod.score(cells, good, None)["CLOSURE_EFFECTIVE"] == 50
    poisoned = mod.score(cells, bad, None)
    assert poisoned["CLOSURE_EFFECTIVE"] == 0
    assert poisoned["CLOSURE_POTENTIAL"] == 50
    assert poisoned["failed_gates"] == ["G1_REPRODUCIBLE"]


def test_a_broken_cell_is_counted_and_not_absorbed_into_named(mod):
    """المكسورُ لا يُبتلع في `NAMED`: الثلاثةُ أعدادٍ منفصلةٌ ومقامُها واحد."""
    class C:
        def __init__(self, reason="", value=1):
            self.reason, self.value = reason, value
            self.section = self.field = self.source = "x"

        @property
        def from_code(self):
            return not self.reason

    cells = [C(), C("OWNER_DECISION", None), C(value=None)]
    g = {"G1_REPRODUCIBLE": True, "G2_LEDGER_CLOSES": True,
         "G3_NO_BROKEN": False, "G4_NO_OWNER_INFERENCE": True,
         "_broken": ["x/x"], "_owner_cells_decided": []}
    s = mod.score(cells, g, None)
    assert s["BROKEN"] == 1
    assert s["GROUNDED"] + s["NAMED"] + s["BROKEN"] == s["CELLS_TOTAL"] == 3
    assert s["CLOSURE_EFFECTIVE"] == 0


# ── ح-٥ · مانعُ التلاعب بالمقام ────────────────────────────────────────
def test_reason_family_moves_are_reported_against_the_previous_round(mod):
    """نقلُ خانةٍ بين أسر الأسباب يرفع العلامةَ بلا عمل، فيُقابَل ويُعلَن."""
    class C:
        def __init__(self, reason=""):
            self.reason, self.value = reason, (None if reason else 1)
            self.section = self.field = self.source = "x"

        @property
        def from_code(self):
            return not self.reason

    cells = [C("HUMAN_DECLARED_ONLY"), C("NOT_OPENED:HUKM")]
    g = {"G1_REPRODUCIBLE": True, "G2_LEDGER_CLOSES": True,
         "G3_NO_BROKEN": True, "G4_NO_OWNER_INFERENCE": True,
         "_broken": [], "_owner_cells_decided": []}
    prev = {"not_available_by_reason": {"HUMAN_DECLARED_ONLY": 2}}
    moves = mod.score(cells, g, prev)["reason_family_moves_vs_previous_round"]
    assert moves["HUMAN_DECLARED_ONLY"] == {"previous_round": 2,
                                            "this_round": 1}
    assert moves["NOT_OPENED:HUKM"] == {"previous_round": 0, "this_round": 1}
    assert mod.score(cells, g, {"not_available_by_reason":
                                {"HUMAN_DECLARED_ONLY": 1,
                                 "NOT_OPENED:HUKM": 1}}
                     )["reason_family_moves_vs_previous_round"] == {}


def test_this_round_moved_nothing_between_families(scores):
    """والمقيسُ اليوم: لا انتقال. وخلوُّ الحقل خبرٌ كامتلائه."""
    assert scores["reason_family_moves_vs_previous_round"] == {}


# ── الصفحة ─────────────────────────────────────────────────────────────
CONTAINER = re.compile(r"""\[['"]<|['"], ['"]<|Counter\(|\{'|<[a-z]+>\[['"]""")


def test_the_page_has_no_python_container_repr(page):
    assert CONTAINER.findall(page) == []


def test_the_page_has_twelve_sections_and_a_complete_matrix(page):
    assert len(re.findall(r"<h2>", page)) == 12
    assert len(re.findall(r'<td class="s-', page)) == 160


def test_the_matrix_prints_every_stage_and_no_row_is_elided(page, mod):
    for n, stage in enumerate(mod.STAGES, 1):
        assert f"{n}. {stage}" in page, stage


def test_the_page_records_that_the_runtime_does_not_know_its_own_commit(page):
    """التثبيتُ خارجيّ. والمشغّلُ يكتب `UNKNOWN_COMMIT_SHA` في سجلّاته كلِّها."""
    assert "UNKNOWN_COMMIT_SHA" in page
    assert "git rev-parse" in page


def test_one_of_declares_multiplicity_instead_of_choosing(mod):
    """حقلٌ باختلافٍ لا يُختار منه واحد — يُعلَن التعدّد. وذلك سمُّ الدالّة."""
    same = [{"f": "A"}, {"f": "A"}]
    diff = [{"f": "A"}, {"f": "B"}]
    assert mod.one_of(same, "f") == "A"
    out = mod.one_of(diff, "f")
    assert out.startswith("MULTIPLE:2") and "A" in out and "B" in out


def test_the_page_never_claims_the_project_is_finished(page):
    assert "CLAIM_PROJECT_FINISHED = NO" in page
