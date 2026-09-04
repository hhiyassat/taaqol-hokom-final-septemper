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


# ── القواعدُ التسع ────────────────────────────────────────────────────
def test_every_rule_has_a_poison_or_is_marked_unpoisoned(be):
    # تسعٌ: سبعٌ منذ E4، والثامنةُ من جولة التنوين (نُقلت إلى بيتها من
    # `build_state`)، والتاسعةُ من جولة العلّة المشتركة.
    assert len(be.RULES) == 9
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


def test_the_rules_document_lists_every_rule():
    doc = (EX / "01_rules.md").read_text(encoding="utf-8")
    import importlib.util as _i
    assert len(re.findall(r"^## `", doc, re.M)) == 9
    assert "GUARD_MUST_REPORT_NOT_DIE" in doc
    assert "COUNT_IS_NOT_MEMBERSHIP" in doc
    assert "UNPOISONED" in doc


# ── الفهرس — ولا تُدمج ─────────────────────────────────────────────────
#: `E1` — جردٌ مُثبَّتٌ بالمسار، لا عددٌ أدنى. `len(idx) >= 5` كان يمرّ
#: بعد حذفِ دفترٍ ما دام سادسٌ قد أُضيف؛ فالعددُ لا يحرس الهُويّة.
PINNED_LEDGERS = {
    "container": (
        "output/remediation/01_ledger.json",
        "output/upstream/01_ledger.json",
        "output/doors/02_ledger.json",
    ),
    "device": (
        "hokom/output/b83/02_ledger.json",
        "hokom/output/tail/03_report.md",
        "hokom/output/nazila_result/"
        "TAAQOL_NAZILA_CODE_VS_REFERENCE_TWO_COLUMN.csv",
    ),
}


def test_the_index_lists_every_pinned_ledger_by_path():
    """`E1` — بالمسارِ لا بالعدد: يُحذف دفترٌ ⟶ يسقط، ولو زِيد غيرُه."""
    idx = json.loads((EX / "02_ledger.json").read_text(
        encoding="utf-8"))["index"]
    seen = {(x.get("machine"), x.get("ledger")) for x in idx}
    missing = sorted(f"{m}:{rel}" for m, rels in PINNED_LEDGERS.items()
                     for rel in rels if (m, rel) not in seen)
    assert not missing, missing
    for x in idx:
        assert x.get("denominator") or x.get("state")
        assert x.get("machine") in ("container", "device")


def test_poison_a_deleted_ledger_falls_even_when_another_is_added():
    """السمُّ: يُحذف دفترٌ ويُزاد سواه — العددُ يمرّ، والجردُ يسقط."""
    idx = [{"machine": m, "ledger": rel}
           for m, rels in PINNED_LEDGERS.items() for rel in rels]
    poisoned = idx[1:] + [{"machine": "container", "ledger": "output/x.json"}]
    assert len(poisoned) >= 5  # العددُ يمرّ
    seen = {(x["machine"], x["ledger"]) for x in poisoned}
    missing = [f"{m}:{rel}" for m, rels in PINNED_LEDGERS.items()
               for rel in rels if (m, rel) not in seen]
    assert missing == ["container:output/remediation/01_ledger.json"]


def test_no_merged_number_across_denominators(be):
    """السمُّ: يُدسّ دفترٌ عددُه مجموعُ الباقين ⟶ يلزم أن يُلتقط."""
    idx = [{"ledger": "a", "count": 3}, {"ledger": "b", "count": 4}]
    assert be.no_merge(idx) == []
    leaked = [*idx, {"ledger": "merged", "count": 7}]
    assert "merged" in be.no_merge(leaked)


def test_count_is_not_membership_in_both_directions(be):
    """`COUNT_IS_NOT_MEMBERSHIP` — سمٌّ ذو جهتَين، ووقعت المخالفةُ في كلٍّ.

    **الجهةُ الأولى — تساوٍ بلا اتّحاد.** عددان متساويان ومجموعتان
    مختلفتان: يُتَّهم البريءُ ويُبرَّأ المدموج (سمُّ `no_merge` أدناه).

    **والجهةُ الثانية — اختلافٌ بلا افتراق.** عددان مختلفان ومادّةٌ
    واحدة: `55/160` من عمودٍ اختلف شكلُه ولم يضع منه صفّ. ولو اكتُفي
    بالجهة الأولى لمرّ الخطأُ الثاني — وقد مرّ فعلًا حتّى قيس.
    """
    # الجهةُ الثانية: أعدادٌ مختلفةٌ ومادّةٌ متّحدة
    plain = ["مررت بزيد", "سرت من البيت", "الماء في الكوز"]
    voc = ["مَرَرْتُ بِزَيْدٍ", "سِرْتُ مِنَ الْبَيْتِ", "الْمَاءُ فِي الْكُوزِ"]
    marks = "".join(chr(c) for c in range(0x64B, 0x653))
    strip = lambda s: "".join(ch for ch in s if ch not in marks)
    differing = sum(1 for a, b in zip(plain, voc) if a != b)
    assert differing == 3, "الأعدادُ تختلف"
    lost = [a for a, b in zip(plain, voc) if a and not b]
    assert lost == [], "ولا شيءَ ضاع — والمادّةُ واحدة"
    assert all(strip(b) == a for a, b in zip(plain, voc)), \
        "غيرُ المشكولِ مشتقٌّ بحذف الحركات، لا معلومةٌ مستقلّة"

    # والجهةُ الأولى، بالسمّ القائم
    test_rule7_equal_numbers_may_be_different_sets_face_one(be)


def test_rule7_equal_numbers_may_be_different_sets_face_one(be):
    """`E4` — سمُّ القاعدةِ السابعة، بوجهَيها، تشغيلًا لا نصًّا.

    **الوجهُ الأوّل — تساوٍ بلا اتّحاد.** ثلاثةُ دفاترَ لا دمجَ بينها،
    وصادف عددُ أحدِها مجموعَ الآخرَين ⟶ يتّهمه الحارس، وهو بريء.

    **والوجهُ الثاني — دمجٌ بلا تساوٍ.** دفترٌ جامعٌ فعلًا، لكنّه أسقط
    بندًا مكرَّرًا فلم يصادف المجموعَ ⟶ يمرّ، وهو مدموج.

    فالعددُ ظلُّ المجموعة لا هي، وهذا الحارسُ يقيس ظلًّا.
    """
    innocent = [{"ledger": "a", "count": 2}, {"ledger": "b", "count": 3},
                {"ledger": "c-innocent", "count": 5}]
    assert be.no_merge(innocent) == ["c-innocent"]   # اتّهامٌ بلا دمج

    merged = [{"ledger": "a", "count": 2}, {"ledger": "b", "count": 3},
              {"ledger": "d-merged", "count": 4}]   # جمع a+b ثمّ أسقط مكرَّرًا
    assert be.no_merge(merged) == []                # دمجٌ بلا اتّهام


def test_rule7_is_in_the_rules_document_with_a_real_poison(be):
    r = be.RULES["COUNT_IS_NOT_MEMBERSHIP"]
    assert r["former_name"] == "EQUAL_NUMBERS_MAY_BE_DIFFERENT_SETS"
    assert "في الجهتين" in r["rule"]
    assert "الجهةُ الثانية" in r["incident"]
    path, _, test = r["poison"].partition("::")
    f = ROOT / path
    assert f.is_file() and f"def {test}(" in f.read_text(encoding="utf-8")


def test_no_merge_is_labelled_a_numeric_coincidence_check(be):
    """`E2` — الوسمُ يقول ما يفعله الحارس، لا ما نتمنّاه."""
    assert be.NO_MERGE_KIND == "NUMERIC_COINCIDENCE_CHECK"
    g = json.loads((EX / "02_ledger.json").read_text(
        encoding="utf-8"))["guards"]
    keys = [k for k in g if k.startswith("G_NO_LEDGER_MERGE")]
    assert keys == ["G_NO_LEDGER_MERGE[NUMERIC_COINCIDENCE_CHECK]"]
    assert not any("STRUCTURAL" in k for k in g)


def test_e3_the_repeat_is_derived_not_written(be):
    """`E3` — ٢٩٩ = ٢٩٢ + حقولُ حدّ الدخول، اشتقاقًا من الصنف حيًّا."""
    page = (NAZ / "nazila_result.html").read_text(encoding="utf-8")
    d = be.repeat_is_entry_boundary(page)
    assert d["data_attributes"] == d["data_cells"] + d["data_repeated"]
    assert d["repeat_identity"] == "ENTRY_BOUNDARY_FIELDS"
    assert d["data_repeated"] == d["entry_boundary_fields"]
    assert d["repeat_mismatch"] == []


def test_poison_e3_falls_when_a_foreign_pair_repeats(be):
    """السمُّ: يُكرَّر زوجٌ ليس من حقول حدّ الدخول ⟶ يُسمَّى المخالف."""
    page = (NAZ / "nazila_result.html").read_text(encoding="utf-8")
    injected = page + (
        '<td data-section="4. مصفوفة المراحل الست عشرة" '
        'data-field="stage_id">x</td>' * 2)
    d = be.repeat_is_entry_boundary(injected)
    assert d["repeat_identity"] == "MISMATCH"
    assert d["repeat_mismatch"]


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
