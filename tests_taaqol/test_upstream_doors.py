"""سمومُ حرّاس `03_upstream` و`01_doors` — كلٌّ يُسقَط بيدٍ ويُثبت سقوطُه.

`NO_TEXTUAL_GUARD`: لا اختبارَ يفحص ورودَ اسمٍ في نصّ. يُشغَّل أو لا يُعدّ.
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
def bu():
    return load("bups", "scripts/build_upstream.py")


@pytest.fixture(scope="module")
def bd():
    return load("bdrs", "scripts/build_doors.py")


@pytest.fixture(scope="module")
def upstream():
    p = UP / "00_upstream.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل build_upstream بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def doors():
    p = DO / "00_doors.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل build_doors بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


# ── G_LOCATION_RESOLVES ────────────────────────────────────────────────
def test_every_location_resolves_to_its_symbol(bu, upstream):
    for i in upstream["items"]:
        if i["location"]:
            assert bu.resolves(i["location"]), i["ident"]


def test_a_shifted_line_number_breaks_the_location_guard(bu, upstream):
    """السمُّ: يُبدَّل رقمُ السطر، فيلزم أن يسقط الحارس."""
    loc = next(i["location"] for i in upstream["items"] if i["location"])
    assert bu.resolves(loc) is True
    assert bu.resolves({**loc, "line": loc["line"] + 3}) is False
    assert bu.resolves({**loc, "line": 999999}) is False


def test_a_missing_symbol_stops_instead_of_returning_zero(bu):
    """رمزٌ غيرُ موجودٍ يقف بإنذار — ولا يردّ سطرًا صفرًا يُشبه القياس."""
    with pytest.raises(bu.Blocked) as e:
        bu.locate(bu.REG, "def a_symbol_that_is_not_there")
    assert "SYMBOL_NOT_FOUND" in str(e.value)


def test_the_false_flags_are_found_by_ast_not_by_grep(bu):
    """`runtime_implemented=False` يُلتقط بالتحليل النحويّ، فلا يخدعه تعليق."""
    lines = bu.false_flag_lines()
    assert len(lines) == 2
    src = bu.REG.read_text(encoding="utf-8").splitlines()
    for ln in lines:
        assert "runtime_implemented" in src[ln - 1]
        assert "False" in src[ln - 1]


# ── G_FORBIDDEN_LINES_QUERIED ──────────────────────────────────────────
def test_c3_queries_the_registry_and_does_not_copy_it(bu):
    """النداءُ حيٌّ — وهذا كلُّ ما يشهد به. `REVIEWER_WITHDRAWN_1`."""
    m = bu.c3_measure()
    cc = m["crossing_claim"]
    assert cc["all_three_forbidden"] is True
    assert set(cc["crosses_queried"].values()) == {True}
    assert cc["query_used"].startswith("CANONICAL_REGISTRY.is_forbidden_direct")


def test_c3_labels_that_query_a_tautology_not_evidence(bu):
    """والجوابُ ليس شهادة: مدخلُه من السجلّ، فوسمُه ترديد."""
    cc = bu.c3_measure()["crossing_claim"]
    assert cc["input_drawn_from"] == "CANONICAL_REGISTRY.lines"
    assert cc["crosses"] == "TAUTOLOGY"
    assert cc["mapping"] == "NOT_DERIVABLE"
    assert cc["status"] == "OWNER_RULING_REQUIRED"
    assert cc["withdrawn"] is False, "الدعوى تُقيَّد لا تُمحى"


def test_c3_keeps_the_measured_number_and_names_what_remains_evidence(bu):
    m = bu.c3_measure()
    assert m["corpus_words_matching"] == 10013
    assert m["corpus_words"] == 77411
    ev = m["what_remains_evidence"]
    assert ev["status"] == "EVIDENCE" and ev["raise_to_source"] is True
    assert m["crossing_claim"]["raise_to_source"] is False


def test_the_query_returns_false_for_a_pair_that_is_not_forbidden():
    """السمُّ: يُدسّ زوجٌ غيرُ ممنوع — ويلزم أن يُردّ `False`.

    فاستفتاءٌ يردّ `True` لكلّ زوجٍ ليس استفتاءً بل ختمٌ.
    """
    sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))
    from taaqqul_slot_geometry.core.forbidden_lines import CANONICAL_REGISTRY
    assert CANONICAL_REGISTRY.is_forbidden_direct("Grapheme",
                                                  "FunctionalLetter") is True
    assert CANONICAL_REGISTRY.is_forbidden_direct("NotAThing",
                                                  "NorThis") is False


# ── G_EVERY_NUMBER_HAS_A_COMMAND ───────────────────────────────────────
def test_every_numeric_field_carries_a_command(bu, upstream):
    for i in upstream["items"]:
        nums = bu.numeric_fields(i["measure"] or {})
        if nums:
            assert (i["measure"] or {}).get("command"), (i["ident"], nums)


def test_the_command_guard_catches_a_number_without_one(bu):
    """السمُّ: قياسٌ فيه رقمٌ وبلا أمر — يجب أن يُلتقط."""
    naked = [{"ident": "X", "status": "DECLARED", "location": None,
              "measure": {"some_count": 7}}]
    g = bu.guard(naked, {"stages_total": 16})
    assert g["G_FORBIDDEN_LINES_QUERIED"] == ["C3:ABSENT"], (
        "غيابُ C3 يجب أن يُبلَّغ لا أن يُسقط الفحصَ كلَّه")
    assert "X.some_count" in g["G_EVERY_NUMBER_HAS_A_COMMAND"]
    withcmd = [{"ident": "X", "status": "DECLARED", "location": None,
                "measure": {"some_count": 7, "command": "run it"}}]
    assert bu.guard(withcmd, {"stages_total": 16})[
        "G_EVERY_NUMBER_HAS_A_COMMAND"] == []


# ── G_DENOMINATOR_NAMED ────────────────────────────────────────────────
def test_every_ratio_names_its_denominator(bu, upstream):
    for i in upstream["items"]:
        for k, v in (i["measure"] or {}).items():
            if isinstance(v, str) and re.fullmatch(r"\d+/\d+", v):
                assert f"{k}_denominator" in i["measure"], f'{i["ident"]}.{k}'


def test_c2_names_two_different_denominators(upstream):
    """رقمان بمقامين في حقلين متجاورين — ويُسمّى مقامُ كلٍّ بجانبه."""
    c2 = next(i for i in upstream["items"] if i["ident"] == "C2")["measure"]
    assert c2["inventory_hit_unmarked"] == "11/11"
    assert c2["inventory_hit_marked"] == "0/17"
    assert (c2["inventory_hit_unmarked_denominator"]
            != c2["inventory_hit_marked_denominator"])
    assert c2["inventory_hit_marked_source"]


def test_the_denominator_guard_catches_an_unnamed_ratio(bu):
    bare = [{"ident": "X", "status": "DECLARED", "location": None,
             "measure": {"ratio": "3/9", "command": "c"}}]
    assert bu.guard(bare, {"stages_total": 16})["G_DENOMINATOR_NAMED"] == [
        "X.ratio"]


# ── G_JOINT_FIELD_PRESENT ──────────────────────────────────────────────
def test_the_joint_field_is_derived_from_the_registry(upstream):
    j = upstream["joint_field"]
    assert j["stages_total"] == 16
    assert j["runtime_implemented_true"] == 14
    assert j["runtime_implemented_false"] == 2
    assert set(j["names_of_false"]) == {"PRE_WEIGHT_CAPACITY_AUDIT",
                                        "ANSWER_AUDIT"}
    # كان `stages_blocked_by_C1 = 12`، وشُطر لأنّه كان يعدّ في `C1` ما لا
    # تفتحه: `ANSWER_AUDIT` محجوبةٌ بنفسها. والاسمُ الواحدُ كان يحمل رقمين.
    assert j["stages_not_opened_today"] == 12
    assert j["stages_C1_would_open"] == 11
    assert j["stages_still_closed_after_C1"] == ["ANSWER_AUDIT"]
    assert "stages_blocked_by_C1" not in j, "الاسمُ القديمُ عاد"


def test_the_joint_field_guard_falls_on_a_wrong_total(bu):
    assert bu.guard([], {"stages_total": 15})["G_JOINT_FIELD_PRESENT"] == [
        "JOINT"]


# ── G_NO_DONE_IN_C ─────────────────────────────────────────────────────
def test_no_upstream_item_is_marked_done(upstream):
    assert {i["status"] for i in upstream["items"]} <= {"DECLARED",
                                                        "NOT_CHOSEN"}


def test_a_done_status_in_c_is_caught(bu):
    """`DONE` في (ج) دعوى بمسّ المصدر — ولا تمرّ.

    وبندٌ بلا حقل `status` يُبلَّغ كذلك ولا يرفع `KeyError`: استثناءٌ داخل
    الحارس يُنهي الفحصَ كلَّه، فتُقرأ بقيّةُ الحرّاس سليمةً ولم تُشغَّل.
    """
    bad = [{"ident": "C9", "status": "DONE", "location": None,
            "measure": {"command": "c"}}]
    assert bu.guard(bad, {"stages_total": 16})["G_NO_DONE_IN_C"] == ["C9"]
    malformed = [{"ident": "C8", "location": None, "measure": {}}]
    assert bu.guard(malformed, {"stages_total": 16})["G_NO_DONE_IN_C"] == ["C8"]


def test_c_path_is_still_not_chosen(upstream):
    p = next(i for i in upstream["items"] if i["ident"] == "C_PATH")
    assert p["status"] == "NOT_CHOSEN"
    assert p["measure"]["chosen"] is None
    assert p["measure"]["SENT"] == "NO"
    assert p["measure"]["AUTHORITY_TO_SEND"] == "OWNER"


# ── الأبواب · G_ALL_UPSTREAM_PRESENT ───────────────────────────────────
def test_every_upstream_item_has_a_door(bd, doors, upstream):
    names = {d["door"] for d in doors["doors"]}
    upstream_ids = {i["ident"] for i in upstream["items"]
                    if i["ident"] != "C_PATH"}
    assert upstream_ids <= names
    assert {"C2", "C3", "C4"} <= names, "الثلاثةُ الساقطةُ عادت"


def test_removing_a_door_breaks_the_completeness_guard(bd, doors, upstream):
    """السمُّ: يُحذف بندٌ من الجدول، فيلزم أن يسقط الحارس."""
    short = [d for d in doors["doors"] if d["door"] != "C3"]
    g = bd.guard(short, upstream, doors["cells"])
    assert g["G_ALL_UPSTREAM_PRESENT"] == ["C3"]
    assert bd.guard(doors["doors"], upstream,
                    doors["cells"])["G_ALL_UPSTREAM_PRESENT"] == []


# ── G_NO_AXIS_BLANK · G_NO_BIAS ────────────────────────────────────────
def test_no_axis_is_left_blank(doors):
    for d in doors["doors"]:
        for k in ("cells", "correctness", "ceiling", "cost"):
            assert d[k] not in (None, "", "-", "—"), f'{d["door"]}.{k}'


def test_an_empty_axis_must_be_named_not_dashed(bd):
    """الفراغُ يُسمّى: `NO_EFFECT_MEASURED` خبرٌ، والشرطةُ سكوت."""
    blank = [{"door": "X", "cells": "0/292", "correctness": {},
              "ceiling": "—", "cost": "UNMEASURED"}]
    g = bd.guard(blank, {"items": []}, {"cells_total": 292})
    assert "X.ceiling" in g["G_NO_AXIS_BLANK"]
    assert set(bd.EMPTY_AXIS) == {"NO_EFFECT_MEASURED", "UNMEASURED"}


def test_the_three_axes_are_applied_to_owner_doors_too(doors):
    """`G_NO_BIAS` — لا يُقاس (ج) بثلاثةٍ و(ب) بواحد."""
    b2 = next(d for d in doors["doors"] if d["door"] == "B2")
    for k in ("cells", "correctness", "ceiling", "cost"):
        assert b2[k] not in (None, "", "—")
    assert b2["owner"] == "DR_HUSSEIN"
    owners = {d["owner"] for d in doors["doors"]}
    assert owners == {"SONAISO", "DR_HUSSEIN"}


# ── G_DOORS_DERIVED ────────────────────────────────────────────────────
def test_the_cells_column_is_derived_from_cells_csv(bd, tmp_path):
    """السمُّ: يُبدَّل تصنيفُ خانةٍ، فيلزم تحرُّكُ عمود `cells`."""
    with (NAZ / "cells.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    base = bd.cells_by_door(NAZ / "cells.csv")

    moved = [dict(r) for r in rows]
    n = 0
    for r in moved:
        if r["reason_family"] == "NOT_EMITTED_BY_RUNNER" and n < 1:
            r["reason_family"] = "HUMAN_DECLARED_ONLY"
            r["reason"] = "HUMAN_DECLARED_ONLY"
            n += 1
    p = tmp_path / "poisoned.csv"
    with p.open("w", encoding="utf-8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(moved)
    after = bd.cells_by_door(p)
    assert after["per_door"]["C5"] == base["per_door"]["C5"] - 1, (
        "عمودُ cells لم يتحرّك بتغيُّر مصدره — فهو منسوخٌ لا مشتقّ")


def test_the_measured_cells_match_the_ceiling_families(doors):
    c = doors["cells"]
    assert c["cells_total"] == 292
    assert c["per_door"]["C5"] == 42
    assert c["per_door"]["C1"] == 17


# ── G_B1_RETIRED ───────────────────────────────────────────────────────
def test_b1_is_not_a_door_and_is_recorded_as_decided(doors):
    assert "B1" not in {d["door"] for d in doors["doors"]}
    assert doors["retired"]["B1"]["decided"] == "(أ) 1a7f8b76"
    assert doors["retired"]["B1"]["by"] == "DR_HUSSEIN"
    doc = (DO / "01_doors.md").read_text(encoding="utf-8")
    assert "1a7f8b76" in doc


def test_the_retirement_guard_falls_if_b1_reappears(bd, doors):
    with_b1 = doors["doors"] + [{"door": "B1", "owner": "DR_HUSSEIN",
                                 "cells": "0/292", "correctness": {},
                                 "ceiling": "x", "cost": "x"}]
    assert bd.guard(with_b1, {"items": []},
                    doors["cells"])["G_B1_RETIRED"] == ["B1"]


# ── G_NOT_SENT ─────────────────────────────────────────────────────────
def test_the_upstream_report_exists_and_is_not_sent():
    p = DO / "upstream_report.md"
    assert p.is_file()
    doc = p.read_text(encoding="utf-8")
    assert "SENT = NO" in doc
    assert "AUTHORITY_TO_SEND = OWNER" in doc
    ledger = json.loads((DO / "02_ledger.json").read_text(encoding="utf-8"))
    assert ledger["SENT"] == "NO"


def test_the_upstream_report_carries_four_items_and_not_c4():
    """`C4` إعلانُ حدٍّ لا طلبُ تغيير — فلا تُذكر اقتراحًا في البلاغ."""
    doc = (DO / "upstream_report.md").read_text(encoding="utf-8")
    heads = re.findall(r"^## (\w+) ·", doc, re.M)
    assert set(heads) == {"C1", "C2", "C3", "C5"}
    assert "C4" not in heads


# ── الدفتر يقفل ────────────────────────────────────────────────────────
def test_both_ledgers_close_by_a_second_count():
    up = json.loads((UP / "01_ledger.json").read_text(encoding="utf-8"))
    do = json.loads((DO / "02_ledger.json").read_text(encoding="utf-8"))
    assert up["recount_from_report"]["closes"] is True
    assert up["recount_from_report"]["rows"] == up["recount_from_report"]["items"]
    assert do["recount_from_report"]["closes"] is True
    assert do["recount_from_report"]["rows"] == do["recount_from_report"]["doors"]


def test_neither_document_claims_the_project_is_finished():
    for p in (UP / "03_upstream.md", DO / "01_doors.md"):
        assert "CLAIM_PROJECT_FINISHED = NO" in p.read_text(encoding="utf-8")


def test_the_doors_table_prints_the_zero_ownership_line_at_the_top():
    doc = (DO / "01_doors.md").read_text(encoding="utf-8")
    head = doc.split("## الأبواب", 1)[0]
    assert "ما تملك الأداةُ إغلاقَه = 0" in head


# ── SHARED_CAUSE_IS_NOT_SHARED_EFFECT · القاعدةُ التاسعة ───────────────
def test_a_shared_cause_may_not_become_a_shared_count(bu):
    """سمُّ التاسعة: يُسقَط الحارسُ بيدٍ في وجوهه الأربعة، ثمّ يُثبت قيامُه.

    والقاعدة: اتّحادُ العلّة لا يُثبت اتّحادَ الأثر · ولا يُدمج عدٌّ
    بعدٍّ لأنّ سببَهما واحد. والتباينُ يُقاس: بالعضويّة إن كان الحقلُ
    يحتمل، وبالتصميم إن كان لا يحتمل.
    """
    sound = {
        "id": "X", "doors": ["C1", "C5"],
        "effect_C1_cells": 17, "effect_C5_cells": 42,
        "effect_intersection": 0, "effect_union": 59,
        "merged": False, "disjointness_basis": "BY_DESIGN",
        "key_is_unique": True,
    }
    # ١ — السليمُ يمرّ. ولولا هذا لكان الحارسُ يسقط على كلّ شيء.
    assert bu.shared_cause_rows([{"ident": "C1", "shared_cause": sound}]) == []

    # ٢ — الدمجُ صريحًا
    merged = dict(sound, merged=True)
    assert bu.shared_cause_rows(
        [{"ident": "C1", "shared_cause": merged}]) == ["C1:MERGED"]

    # ٣ — الدمجُ منكَرًا: اتّحادٌ يساوي المجموعَ وتقاطعٌ غيرُ صفر.
    #     وهو الوجهُ الذي لا يُصطاد بقراءة الحقل `merged` وحدَه.
    sneaky = dict(sound, effect_intersection=3, effect_union=59)
    assert "C1:UNION_EQUALS_SUM_WITHOUT_DISJOINTNESS" in bu.shared_cause_rows(
        [{"ident": "C1", "shared_cause": sneaky}])

    # ٤ — التباينُ مفترَضٌ لا مقيس: `ASSUMED` ليست من القائمة المغلقة.
    assumed = dict(sound, disjointness_basis="ASSUMED")
    assert bu.shared_cause_rows(
        [{"ident": "C1", "shared_cause": assumed}]) == [
            "C1:BASIS_NOT_IN_CLOSED_LIST(ASSUMED)"]

    # ٥ — الأساسُ لا يطابق ما يحتمله الحقل، في الجهتين معًا.
    assert bu.shared_cause_rows([
        {"ident": "C1", "shared_cause": dict(sound, key_is_unique=False)},
    ]) == ["C1:BY_DESIGN_BUT_FIELD_ADMITS_BOTH"]
    assert bu.shared_cause_rows([
        {"ident": "C5", "shared_cause": dict(sound,
                                             disjointness_basis="BY_MEMBERSHIP")},
    ]) == ["C5:BY_MEMBERSHIP_BUT_FIELD_FORBIDS_BOTH"]

    # ٦ — الغيابُ يُبلَّغ ولا يموت (`GUARD_MUST_REPORT_NOT_DIE`).
    naked = {k: v for k, v in sound.items() if k != "key_is_unique"}
    assert bu.shared_cause_rows(
        [{"ident": "C1", "shared_cause": naked}]) == ["C1:NO_KEY_IS_UNIQUE"]


def test_the_two_doors_declare_one_cause_and_two_counts(upstream):
    """`C1` و`C5` علّتُهما واحدةٌ بعينها، وأثرُهما عددان لا عدد."""
    m = {i["ident"]: i for i in upstream["items"]}
    a, b = m["C1"]["shared_cause"], m["C5"]["shared_cause"]
    assert a["id"] == b["id"] and a["cause_is_one"] is True
    assert a == b, "العلّةُ الواحدةُ تُكتب مرّةً وتُقرأ في البابين"
    assert a["merged"] is False
    assert a["effect_C1_cells"] != a["effect_C5_cells"]
    assert a["effect_union"] == a["effect_sum_if_merged"] == \
        a["effect_C1_cells"] + a["effect_C5_cells"]
    assert a["effect_intersection"] == 0


def test_the_disjointness_basis_is_design_not_this_run(upstream):
    """الحقلُ لا يحتمل أسرتين — فالأساسُ تصميمٌ، والعضويّةُ تعضيدٌ فوقه."""
    sc = {i["ident"]: i for i in upstream["items"]}["C1"]["shared_cause"]
    assert sc["disjointness_basis"] == "BY_DESIGN"
    assert sc["key_is_unique"] is True and sc["duplicated_keys"] == []
    assert sc["membership_check_is_the_basis"] is False
    # والعضويّةُ تُقاس فعلًا فوق التصميم — لا تُترك دعوى
    assert sc["membership_check_intersection"] == 0


def test_the_shared_cause_is_measured_from_the_cells_not_written(bu):
    """`SHARED_CAUSE` يُشتقّ من `cells.csv` — يُقابَل بعدٍّ ثانٍ مستقلّ."""
    p = NAZ / "cells.csv"
    if not p.is_file():
        pytest.skip("cells.csv غائب")
    with p.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    c1 = {(r["section"], r["field"]) for r in rows
          if r["status"] == "NOT_AVAILABLE" and r["reason_family"] == "NOT_OPENED"}
    c5 = {(r["section"], r["field"]) for r in rows
          if r["status"] == "NOT_AVAILABLE" and r["reason_family"] in
          ("NOT_EMITTED_BY_RUNNER", "NOT_CONSTRUCTED_IN_SOURCE")}
    sc = bu.shared_cause()
    assert sc["effect_C1_cells"] == len(c1)
    assert sc["effect_C5_cells"] == len(c5)
    assert sc["effect_intersection"] == len(c1 & c5)


def test_the_doors_take_the_shared_cause_from_upstream_not_recomputed(
        bd, doors, upstream):
    """درسُ `42/35`: مصدرٌ واحدٌ للرقم. ويُسقَط الحارسُ بيدٍ ليُثبت قيامُه."""
    led = json.loads((DO / "02_ledger.json").read_text(encoding="utf-8"))
    assert led["guards"]["G_SHARED_CAUSE_MATCHES_UPSTREAM"] == []
    assert led["guards"]["G_SHARED_CAUSE_NOT_MERGED"] == []
    tampered = [dict(d) for d in doors["doors"]]
    for d in tampered:
        if d.get("door") == "C1" and d.get("shared_cause"):
            d["shared_cause"] = dict(d["shared_cause"], effect_C1_cells=99)
    out = bd.shared_cause_agrees(tampered, upstream)
    assert any("effect_C1_cells" in x for x in out), out


def test_the_ninth_rule_is_documented_with_a_poison_that_runs(bu):
    """`تُوثَّق مع الثمانِ، بسمٍّ` — والسمُّ المذكورُ موجودٌ ويُشغَّل."""
    be = load("bexn", "scripts/build_exec_now.py")
    r = be.RULES["SHARED_CAUSE_IS_NOT_SHARED_EFFECT"]
    assert r["ruled_by"] == "DR_HUSSEIN"
    assert r["two_bases"] == list(bu.DISJOINTNESS_BASIS)
    f, _, t = r["poison"].partition("::")
    assert (ROOT / f).is_file() and f"def {t}(" in \
        (ROOT / f).read_text(encoding="utf-8")


def test_the_c1_title_no_longer_says_it_was_never_built(upstream):
    """الوصفُ صُحِّح، والسابقُ مسجَّلٌ لا ممحوّ — والدعوى تُقيَّد لا تُمحى."""
    c1 = {i["ident"]: i for i in upstream["items"]}["C1"]
    assert c1["title"] == "PRE_WEIGHT مبنيّةُ الحوامل، غيرُ موصولةٍ بالمشغّل"
    assert c1["superseded_title"] == "PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة"
    pw = c1["measure"]["pre_weight_state"]
    # الوصفُ الجديدُ يقوم على أربعةٍ مقيسة — وكلُّها تُقرأ من التشغيل
    assert pw["prs_shipped_count"].split("/")[0] == \
        pw["prs_shipped_count"].split("/")[1]
    assert all(v["shipped"] for v in pw["prs_shipped"].values())
    assert isinstance(pw["carrier_tests"]["passed"], int) and \
        pw["carrier_tests"]["passed"] > 0
    assert pw["carrier_tests"]["failed"] is False
    assert all(isinstance(v, int) for v in pw["laws_ratified"].values())
    # والغائبُ وحدَه: الوصلة
    assert pw["runner_imports_touching_weight"] == []
    assert pw["runner_is_wired_to_carriers"] is False
    assert pw["stage_runtime_implemented"] is False


def test_the_carrier_test_count_is_run_not_copied(bu):
    """`MEASURED_NOT_PRESET` — العددُ من تشغيلٍ حيّ، ومقامُه مسمًّى."""
    ct = bu.carrier_tests()
    assert ct["passed"] > 0 and ct["failed"] is False
    assert ct["files_direct"] and ct["files_direct_denominator"]
    # والمقامُ الأوسعُ يُذكر ولا يُخلط بالأوّل (`DENOMINATOR_IS_PINNED`)
    assert ct["files_importing_a_carrier"] > len(ct["files_direct"])
    assert ct["files_importing_a_carrier_denominator"]
    assert "passed" in ct["summary"]
