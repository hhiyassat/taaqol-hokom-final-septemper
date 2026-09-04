"""سمومُ جولة `EXECUTABLE_NOW` — وكلُّها تشغيلٌ لا نصّ.

`GUARD_MUST_REPORT_NOT_DIE` هي القاعدةُ الجديدة، وهذه السمومُ تُثبتها:
يُحذف موضوعُ كلّ حارسٍ، ويُطالَب ببلاغٍ لا انهيار.
"""
from __future__ import annotations

import csv
import importlib.util
import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
EX = ROOT / "output" / "exec_now"
UP = ROOT / "output" / "upstream"
DO = ROOT / "output" / "doors"
NAZ = ROOT / "output" / "nazila_result"


def load(name: str, rel: str):
    sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def be():
    return load("bex", "scripts/build_exec_now.py")


@pytest.fixture(scope="module")
def bd():
    return load("bdr2", "scripts/build_doors.py")


@pytest.fixture(scope="module")
def bu():
    return load("bup2", "scripts/build_upstream.py")


@pytest.fixture(scope="module")
def upstream():
    p = UP / "00_upstream.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل build_upstream بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def doors():
    return json.loads((DO / "00_doors.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def corr():
    p = EX / "00_corrections.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل build_exec_now بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


# ── A1 · العددُ يُشطر ──────────────────────────────────────────────────
def test_the_closed_stages_are_split_from_what_c1_opens(upstream):
    """اثنتا عشرةَ مُغلَقة، تفتح `C1` منها إحدى عشرة، وتبقى `ANSWER_AUDIT`."""
    j = upstream["joint_field"]
    assert j["stages_not_opened_today"] == 12
    assert j["stages_C1_would_open"] == 11
    assert j["stages_still_closed_after_C1"] == ["ANSWER_AUDIT"]
    assert (j["stages_C1_would_open"]
            + len(j["stages_still_closed_after_C1"])
            == j["stages_not_opened_today"])


def test_the_split_is_derived_from_the_registry_not_written(bu):
    """السمُّ: تُشغَّل الدالّةُ نفسُها ويُقابَل ناتجُها بالسجلّ حيًّا."""
    b = bu.blocked_by_c1()
    from taaqqul_slot_geometry.runtime.native_stage_registry import (
        get_native_stage_registry,
    )
    impl = {(getattr(s, "stage_id", None) or getattr(s, "name", None)):
            s.runtime_implemented for s in get_native_stage_registry()}
    for name in b["stages_still_closed_after_C1"]:
        assert impl[name] is False, name
    for name in set(b["names"]) - set(b["stages_still_closed_after_C1"]):
        assert impl[name] is True, name


# ── A2 · الخصمان، والتصادم ─────────────────────────────────────────────
def test_the_ceiling_names_both_deductions(upstream):
    r = upstream["joint_field"]["reachable_on_a_content_token"]
    assert r["value"] == "14/16"
    assert r["deduction_1_never_implemented"] == ["ANSWER_AUDIT"]
    assert r["deduction_2_not_applicable_on_a_content_path"] == [
        "NON_CONTENT_FORMAL_ROUTE"]
    assert r["arithmetic"] == "16 − 1 − 1 = 14"


def test_the_two_fourteens_are_declared_as_different_sets(upstream):
    """رقمان متساويان بعضويّتين مختلفتين — ولولا التسميةُ لقُرئا واحدًا."""
    c = upstream["joint_field"]["reachable_on_a_content_token"][
        "collision_warning"]
    assert c["runtime_implemented_true_is_also"] == 14
    assert c["but_a_different_set"] is True
    assert c["only_in_reachable"] == ["PRE_WEIGHT_CAPACITY_AUDIT"]
    assert c["only_in_runtime_implemented_true"] == [
        "NON_CONTENT_FORMAL_ROUTE"]


# ── A3 · C5 من مصدرٍ واحد · G_CELLS_AGREE ──────────────────────────────
def test_c5_is_one_number_from_one_source(upstream, doors):
    u = next(i for i in upstream["items"] if i["ident"] == "C5")["measure"]
    d = next(x for x in doors["doors"] if x["door"] == "C5")
    assert u["cells_C5_total"] == d["cells"]
    assert u["cells_runner_does_not_consult"] == "35/292"
    assert u["cells_entry_boundary_not_constructed"] == "7/292"
    assert u["cells_C5_total"] == "42/292"


def test_entry_boundary_is_inside_c5_and_said_so(upstream):
    u = next(i for i in upstream["items"] if i["ident"] == "C5")["measure"]
    assert u["entry_boundary_placement"] == "INSIDE_C5_AS_A_NAMED_PART"
    assert u["entry_boundary_is_a_fifth_door"] is False


def test_cells_agree_falls_when_a_number_is_changed(bd, doors, upstream):
    """السمُّ: يُبدَّل رقمٌ في أحدهما ⟶ يسقط الحارس."""
    assert bd.cells_agree(doors["doors"], upstream) == []
    poisoned = [dict(d) for d in doors["doors"]]
    for d in poisoned:
        if d["door"] == "C5":
            d["cells"] = "41/292"
    out = bd.cells_agree(poisoned, upstream)
    assert out and "C5" in out[0]


def test_cells_agree_reports_absence_and_does_not_die(bd, doors):
    """`GUARD_MUST_REPORT_NOT_DIE` — أعلى غائبٌ يُبلَّغ ولا يرفع استثناء."""
    assert bd.cells_agree(doors["doors"], {}) == ["C5:NO_FIELD"]
    assert bd.cells_agree(doors["doors"], {"items": []}) == ["C5:NO_FIELD"]
    assert bd.cells_agree([{"door": "C5"}], {"items": [
        {"ident": "C5", "measure": {}}]}) == ["C5:NO_FIELD"]


def test_every_guard_survives_a_missing_subject(bd, bu, doors, upstream):
    """يُحذف موضوعُ كلّ حارسٍ — ويلزم بلاغٌ لا انهيار."""
    for payload in ([], [{}], [{"door": "X"}]):
        out = bd.guard(payload, {"items": []}, {"cells_total": 292})
        assert isinstance(out, dict)
    for payload in ([], [{}], [{"ident": "Z"}]):
        out = bu.guard(payload, {})
        assert isinstance(out, dict)
        assert out["G_FORBIDDEN_LINES_QUERIED"] == ["C3:ABSENT"]


# ── التصحيحات ──────────────────────────────────────────────────────────
def test_every_correction_is_derived_and_has_a_command(corr):
    for c in corr["corrections"]:
        assert c["derived"] is True, c["ident"]
        assert c["command"], c["ident"]


def test_every_correction_names_its_old_sites(corr):
    """موضعٌ قديمٌ لا يُشار إليه يبقى في وثيقةٍ صامتًا."""
    for c in corr["corrections"]:
        assert "old_sites" in c, c["ident"]
        assert isinstance(c["old_sites"], list)


def test_the_eleven_promotions_claim_is_tagged_where_it_appears(corr):
    """الدعوى تُقيَّد لا تُمحى — ومواضعُها تُجرَد."""
    b4 = next(c for c in corr["corrections"] if c["ident"] == "B4")
    assert b4["now"]["first_half"] == "UNVERIFIABLE_IN_THIS_REPOSITORY"
    assert b4["now"]["not_deleted"]
    assert b4["old_sites"], "لم يُجرَد موضعٌ واحد — والدعوى موجودةٌ فعلًا"
    files = {s["file"] for s in b4["old_sites"]}
    assert any(f.endswith(".md") for f in files)


def test_a1_is_done_with_limit_not_done(corr):
    b3 = next(c for c in corr["corrections"] if c["ident"] == "B3")
    assert b3["now"]["status"] == "DONE_WITH_LIMIT"
    assert b3["now"]["limit"] == "HISTORY_BEGINS_AFTER_DOCUMENTED_WORK"
    assert b3["now"]["earliest_cut"] == "2.8.0"
    assert b3["now"]["commits"] == 21


def test_i5_quotes_the_handoff_instead_of_describing_it(corr):
    c1 = next(c for c in corr["corrections"] if c["ident"] == "C1")
    assert "١٣٤ مدخلة" in c1["now"]["quote"]
    assert c1["now"]["source"].startswith("HANDOFF.md:")
    line = int(c1["now"]["source"].split(":")[1])
    text = (ROOT / "HANDOFF.md").read_text(encoding="utf-8").splitlines()
    assert "١٣٤ مدخلة" in text[line - 1], "الاقتباسُ لا يقع في سطره"


def test_the_operators_catalog_is_fingerprinted(corr):
    c2 = next(c for c in corr["corrections"] if c["ident"] == "C2")
    n = c2["now"]
    if n.get("state") == "UNMEASURED":
        pytest.skip("الملفُّ غيرُ مبلوغٍ من هذه الحاوية")
    assert len(n["sha256"]) == 64
    assert n["rows"] == 160 and n["unique_operators"] == 153
    assert n["LICENSE_GRANTED"] == "NO"
    assert n["rows_denominator"] and n["unique_operators_denominator"]


def test_the_denominator_correction_takes_the_file_as_governing(corr):
    b1 = next(c for c in corr["corrections"] if c["ident"] == "B1")
    fams = b1["now"]["BYTECODE_CACHE_and_SOURCE"]
    assert sum(fams.values()) == 18
    assert sorted(fams.values()) == [6, 12]
    assert b1["scope_of_the_dead_number_guard"][
        "declared_deliberately"] is True


# ── القواعدُ الستّ ─────────────────────────────────────────────────────
def test_six_rules_each_have_a_poison_or_are_marked_unpoisoned(be):
    assert len(be.RULES) == 6
    for name, r in be.RULES.items():
        assert r["poison"], name
        if r["poison"] == "UNPOISONED":
            assert r.get("poison_note"), name


def test_every_named_poison_actually_exists(be):
    """سمٌّ مذكورٌ ولا وجودَ له أسوأُ من `UNPOISONED` — فيُفحص وجودُه."""
    for name, r in be.RULES.items():
        p = r["poison"]
        if p == "UNPOISONED":
            continue
        path, _, test = p.partition("::")
        f = ROOT / path
        assert f.is_file(), f"{name}: {path}"
        assert f"def {test}(" in f.read_text(encoding="utf-8"), f"{name}: {test}"


def test_the_rules_document_lists_all_six():
    doc = (EX / "01_rules.md").read_text(encoding="utf-8")
    assert len(re.findall(r"^## `", doc, re.M)) == 6
    assert "GUARD_MUST_REPORT_NOT_DIE" in doc
    assert "UNPOISONED" in doc


# ── الفهرس — ولا تُدمج ─────────────────────────────────────────────────
def test_the_index_lists_every_ledger_with_its_denominator():
    idx = json.loads((EX / "02_ledger.json").read_text(
        encoding="utf-8"))["index"]
    assert len(idx) >= 5
    for x in idx:
        assert x.get("denominator") or x.get("state")
        assert x.get("machine") in ("container", "device")


def test_no_merged_number_across_denominators(be):
    """السمُّ: يُدسّ دفترٌ عددُه مجموعُ الباقين ⟶ يلزم أن يُلتقط."""
    idx = [{"ledger": "a", "count": 3}, {"ledger": "b", "count": 4}]
    assert be.no_merge(idx) == []
    leaked = [*idx, {"ledger": "merged", "count": 7}]
    assert "merged" in be.no_merge(leaked)


def test_the_index_document_says_the_ledgers_are_not_merged():
    doc = (ROOT / "output" / "INDEX.md").read_text(encoding="utf-8")
    assert "ولا رقمَ جامعٌ عبر المقامات" in doc
    assert "لا مقام" in doc


# ── النازلة — تُعاد في كلّ تشغيل ───────────────────────────────────────
def test_the_nazila_header_is_printed_at_the_top_not_the_bottom():
    doc = (EX / "03_report.md").read_text(encoding="utf-8")
    head = doc.split("## التصحيحات", 1)[0]
    for token in ("NAZILA_REGENERATED", "NAZILA_RECORDS", "NAZILA_SCORE",
                  "NAZILA_HTML", "STAGES_OPENED"):
        assert token in head, token


def test_the_score_did_not_drift(corr):
    """`70.9%` ثابتة — وارتفاعُها بلا فتحِ بابٍ خرقٌ لا إنجاز."""
    n = corr["nazila"]
    assert n["score"] == 70.9
    assert n["grounded"] == 207 and n["total"] == 292
    assert n["stages_opened"] == "1/16"


def test_the_record_cells_are_unchanged(corr):
    assert corr["nazila"]["record_cells"] == 3840
    assert corr["nazila"]["records"] == "160 × 24"


def test_the_page_shows_the_whole_ledger_not_a_summary(corr):
    """`G_HTML_IS_NOT_A_SUMMARY` — والسمةُ ليست الخانة."""
    n = corr["nazila"]
    assert n["data_cells"] == 292
    assert n["data_attributes"] == 299, (
        "خاناتُ حدّ الدخول تظهر مرّتين — والمقامُ خاناتٌ لا سمات")
    assert n["g5"] is True
    assert n["sections"] == 14


def test_g5_falls_if_a_cell_is_removed_from_the_page():
    """السمُّ: تُحذف خانةٌ من الصفحة ⟶ يسقط `G5`."""
    mod = load("bno3", "scripts/build_nazila_outputs.py")
    page = (NAZ / "nazila_result.html").read_text(encoding="utf-8")
    with (NAZ / "cells.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))

    class C:
        def __init__(self, r):
            self.section, self.field = r["section"], r["field"]
    cells = [C(r) for r in rows]
    assert mod.html_csv_disagreement(page, cells) == []

    def strip(row, times):
        out = page
        for _ in range(times):
            out = out.replace(
                f'data-section="{row["section"]}" '
                f'data-field="{row["field"]}"', "", 1)
        return out

    # خانةٌ تظهر مرّةً واحدة: حذفُها الواحد يُسقط الحارس.
    single = rows[-1]
    assert mod.html_csv_disagreement(strip(single, 1), cells) == [
        f'{single["section"]}/{single["field"]}']

    # وخانةُ حدّ الدخول تظهر مرّتين — في فصلها وفي الدفتر الكامل — فحذفُ
    # واحدةٍ لا يُسقطه، وحذفُ الاثنتين يُسقطه. وهذا هو الفرقُ بين 299 سمةً
    # و292 خانة، ولولاه لقُرئ العددان واحدًا.
    twice = next(r for r in rows if r["section"].startswith("0."))
    assert mod.html_csv_disagreement(strip(twice, 1), cells) == []
    assert mod.html_csv_disagreement(strip(twice, 2), cells) == [
        f'{twice["section"]}/{twice["field"]}']
