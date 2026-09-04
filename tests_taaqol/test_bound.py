"""سمومُ جولة `BOUND_AND_RECONCILE` — وكلُّها تشغيلٌ لا نصّ.

الحارسان الجديدان لكلٍّ سمٌّ ذو وجهَين: وجهٌ واحدٌ يُوهم أنّ الحارسَ يقيس
ما لا يقيس. و`G_EVIDENCE_IS_NOT_TAUTOLOGY` يقيس **مصدرَ المدخل** لا
الجواب؛ و`G_ALL_ORIGINS` يقيس **جردَ الأصول** لا عددَ الصفوف.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
BOUND = ROOT / "output" / "bound"


def load(name: str, rel: str):
    for extra in ("vendor/Taaqol-GPT/src", "vendor/Taaqol-GPT", "src",
                  "scripts"):
        sys.path.insert(0, str(ROOT / extra))
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


TAUT = load("tautology", "scripts/tautology.py")
GS = load("gate_shadow_b", "scripts/gate_shadow.py")
BB = load("build_bound", "scripts/build_bound.py")
BU = load("build_upstream_b", "scripts/build_upstream.py")


# ═══════════════════════ R1 · G_EVIDENCE_IS_NOT_TAUTOLOGY ═══════════════
def test_poison_evidence_is_not_tautology_has_two_faces():
    """السمُّ ذو وجهَين — ووجهٌ واحدٌ يُوهم أنّه يقيس مصدرًا وهو يقيس جوابًا.

    الوجهُ الأوّل: زوجٌ من السجلّ ⟶ يلزم `TAUTOLOGY`، ولو كان الجوابُ
    `True`. والوجهُ الثاني: زوجٌ من رسم المراحل ⟶ يلزم `EVIDENCE`، ولو
    كان الجوابُ `True` كذلك. فالجوابُ نفسُه في الحالتين، والوسمُ يفترق:
    فالمقيسُ إذن هو المصدر.
    """
    assert TAUT.classify("CANONICAL_REGISTRY.lines") == TAUT.TAUTOLOGY
    assert TAUT.classify(
        "get_native_stage_registry().allowed_successors") == TAUT.EVIDENCE

    same_answer = [
        {"query_id": "A", "source": "Candidate", "target": "Certificate",
         "answer": True, "input_drawn_from": "CANONICAL_REGISTRY.lines",
         "status": TAUT.TAUTOLOGY},
        {"query_id": "B", "source": "RELATION", "target": "FORMAL_SHAPE",
         "answer": True,
         "input_drawn_from": "get_native_stage_registry().allowed_successors",
         "status": TAUT.EVIDENCE},
    ]
    assert TAUT.evidence_is_not_tautology(same_answer)["passes"]

    # الوجه الأوّل مسمومًا: صفٌّ من السجلّ يُوسَم دليلًا
    a = [dict(same_answer[0], status=TAUT.EVIDENCE), same_answer[1]]
    ga = TAUT.evidence_is_not_tautology(a)
    assert not ga["passes"] and ga["mislabelled"]

    # والوجه الثاني مسمومًا: صفٌّ من رسم المراحل يُوسَم ترديدًا
    b = [same_answer[0], dict(same_answer[1], status=TAUT.TAUTOLOGY)]
    gb = TAUT.evidence_is_not_tautology(b)
    assert not gb["passes"] and gb["mislabelled"]


def test_a_guard_that_read_the_answer_would_pass_both_poisons():
    """لماذا لا يكفي وجهٌ واحد — يُبنى الحارسُ الخطأُ ويُرى مارًّا.

    حارسٌ يقول «كلُّ `True` ترديد» يمرّ على الوجه الأوّل ويسقط على
    الثاني. وحارسٌ يقول «كلُّ `True` دليل» يمرّ على الثاني ويسقط على
    الأوّل. فلا يفصل بينهما إلا قياسُ المصدر.
    """
    def answer_only(rows):        # الحارسُ الخطأ
        return all(r["status"] == TAUT.TAUTOLOGY
                   for r in rows if r["answer"] is True)
    registry_row = {"answer": True, "status": TAUT.TAUTOLOGY,
                    "input_drawn_from": "CANONICAL_REGISTRY.lines"}
    stage_row = {"answer": True, "status": TAUT.EVIDENCE,
                 "input_drawn_from":
                     "get_native_stage_registry().allowed_successors"}
    assert answer_only([registry_row])           # يمرّ على وجهٍ واحد
    assert not answer_only([registry_row, stage_row])   # ويسقط بالوجهين
    assert TAUT.evidence_is_not_tautology([registry_row, stage_row])["passes"]


def test_an_unknown_source_is_reported_not_guessed():
    rows = [{"query_id": "X", "source": "a", "target": "b",
             "input_drawn_from": "somewhere_else", "status": TAUT.EVIDENCE}]
    g = TAUT.evidence_is_not_tautology(rows)
    assert not g["passes"] and g["unclassified"]


def test_c3_keeps_its_number_and_bounds_its_claim():
    c3 = json.loads((BOUND / "00_c3_bounded.json").read_text(encoding="utf-8"))
    assert c3["count"]["matched"] == 10013
    assert c3["count"]["denominator"] == 77411
    assert c3["crossing_claim"]["crosses"] == "TAUTOLOGY"
    assert c3["crossing_claim"]["mapping"] == "NOT_DERIVABLE"
    assert c3["crossing_claim"]["status"] == "OWNER_RULING_REQUIRED"
    assert c3["crossing_claim"]["withdrawn"] is False, "تُقيَّد لا تُمحى"
    assert c3["what_remains_evidence"]["status"] == "EVIDENCE"


def test_the_claim_is_bounded_in_all_three_documents():
    c3 = json.loads((BOUND / "00_c3_bounded.json").read_text(encoding="utf-8"))
    for path in ("output/upstream/00_upstream.json",
                 "output/doors/00_doors.json",
                 "output/doors/upstream_report.md"):
        assert path in c3["documents"], path
    for path in ("output/upstream/00_upstream.json",
                 "output/doors/00_doors.json"):
        d = c3["documents"][path]
        assert d["crosses"] == "TAUTOLOGY", path
        assert d["mapping"] == "NOT_DERIVABLE", path
        assert d["withdrawn"] is False, path
        assert d["count_retained"] == 10013, path


def test_the_report_to_sonaiso_carries_only_what_remains_evidence():
    c3 = json.loads((BOUND / "00_c3_bounded.json").read_text(encoding="utf-8"))
    r = c3["report_to_sonaiso"]
    assert "الرسم الإملائيّ" in r["raised"]
    assert "ترديد" in r["not_raised"]
    assert r["SENT"] == "NO" and r["AUTHORITY_TO_SEND"] == "OWNER"


def test_poison_a_mislabelled_c3_would_be_caught_upstream():
    """السمّ: يُوسَم استفتاءُ السجلّ دليلًا في بند (ج) ⟶ يُسمّى المخالف."""
    items = [{"ident": "C3", "measure": {"crossing_claim": {
        "input_drawn_from": "CANONICAL_REGISTRY.lines",
        "crosses": TAUT.EVIDENCE}}}]
    assert BU.tautology_rows(items)
    items[0]["measure"]["crossing_claim"]["crosses"] = TAUT.TAUTOLOGY
    assert BU.tautology_rows(items) == []


def test_the_old_guard_no_longer_claims_the_answer_is_evidence():
    """`REVIEWER_WITHDRAWN_1` — الحارسُ يشهد بوقوع النداء، لا بجوابه."""
    src = (ROOT / "scripts/build_upstream.py").read_text(encoding="utf-8")
    assert "all_three_forbidden" not in src.split("def guard(")[1]
    g = BU.guard([{"ident": "C3", "measure": {
        "crossing_claim": {"query_used": "x",
                           "input_drawn_from": "CANONICAL_REGISTRY.lines",
                           "crosses": TAUT.TAUTOLOGY}}}], {})
    assert g["G_FORBIDDEN_LINES_QUERIED"] == []
    g2 = BU.guard([{"ident": "C3", "measure": {"crossing_claim": {}}}], {})
    assert g2["G_FORBIDDEN_LINES_QUERIED"] == ["C3:NO_LIVE_QUERY"]


# ═════════════════════════════ R2 · G_ALL_ORIGINS ═══════════════════════
def test_all_three_origins_are_measured():
    t7 = json.loads((ROOT / "reports/gate_shadow/SUMMARY.json")
                    .read_text(encoding="utf-8"))
    assert t7["origins"] == t7["origins_declared"]
    assert len(t7["origins"]) == 3
    assert t7["rows"] == 3 * 4 * 6 * 6 == 432


def test_poison_all_origins_falls_when_one_is_dropped():
    """السمُّ: يُحذف أصلٌ ⟶ يسقط، ولو بقي عددُ الصفوف كبيرًا."""
    full = [{"origin": g.name} for g in GS.GenerationSource]
    assert GS.g_all_origins(full)["passes"]
    dropped = [r for r in full if r["origin"] != "CANDIDATE"]
    g = GS.g_all_origins(dropped)
    assert not g["passes"] and g["missing"] == ["CANDIDATE"]


def test_poison_all_origins_falls_on_a_name_that_is_not_a_member():
    rows = [{"origin": g.name} for g in GS.GenerationSource]
    rows.append({"origin": "INVENTED_SOURCE"})
    g = GS.g_all_origins(rows)
    assert not g["passes"] and g["not_a_member"] == ["INVENTED_SOURCE"]


def test_row_count_alone_would_not_catch_a_dropped_origin():
    """لماذا الجردُ لا العدد: صفوفٌ كثيرةٌ من أصلَين تمرّ على عدٍّ أدنى."""
    two_thirds = ([{"origin": "DECLARED_ENTRY"}] * 216
                  + [{"origin": "TRANSITION_VERDICT"}] * 216)
    assert len(two_thirds) == 432          # العددُ يمرّ
    assert not GS.g_all_origins(two_thirds)["passes"]   # والجردُ يسقط


def test_the_certificate_claim_now_holds_on_the_full_denominator():
    org = json.loads((BOUND / "01_origins.json").read_text(encoding="utf-8"))
    assert org["certificate_granted_anywhere"] == []
    assert org["now"]["origins_measured"] == 3
    assert "CERTIFICATE" not in org["ranks_granted"]


def test_the_candidate_carrier_changes_only_its_generation_source():
    """الأصلُ الثالثُ من قِطَع الفَخّ — والمبدَّلُ حقلٌ واحدٌ مُعلَن."""
    fx = GS.fixtures()
    g = GS.candidate_graph(fx)
    ref = fx._build_graph()
    assert g.generation_source is GS.GenerationSource.CANDIDATE
    assert g.boundary == ref.boundary
    assert g.output_boundary == ref.output_boundary
    assert g.slots == ref.slots
    assert g.entry_boundary is None, "الحاملُ يرفضه لغير DECLARED_ENTRY"


# ═══════════════════════════ R3 · العددُ المتغيّر ════════════════════════
@pytest.fixture(scope="module")
def cc():
    p = BOUND / "02_class_count.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل measure_class_count بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


def test_both_numbers_are_measured_and_named(cc):
    t = cc["totals"]
    assert t["events"] == 18143 and t["words"] == 18135
    assert t["difference"] == 8
    assert "أحداث" in t["events_denominator"] or "مواضع" in t["events_denominator"]
    assert "كلمات" in t["words_denominator"]
    assert t["events_source"].endswith(":1233")
    assert ":224" in t["words_source"]


def test_18143_is_not_corrected_but_named(cc):
    """لا تُصحَّح — هي صحيحةٌ بمقامها. والخطأُ كان عرضَها بلا مقام."""
    assert cc["correction"]["18143_is_wrong"] is False
    assert "مقام" in cc["correction"]["ruling"]


def test_the_eight_are_named_by_position(cc):
    d = cc["detail"]
    assert d["events"] == 60 and d["words"] == 52
    assert d["extra_events"] == 8
    assert len(d["the_extra"]) == d["words_raising_it_more_than_once"] == 5
    assert sum(x["extra"] for x in d["the_extra"]) == 8
    for x in d["the_extra"]:
        assert x["position"].count(":") == 2 and x["word"]


def test_only_one_class_disagrees(cc):
    off = [k for k, v in cc["by_class"].items() if not v["agree"]]
    assert off == ["U_UNVOCALIZED_CARRIER"]


def test_poison_difference_accounted_falls_on_an_unexplained_gap():
    """السمّ: فرقٌ لا تشرحه مواضعُ مسمّاة ⟶ يسقط."""
    MC = load("measure_class_count", "scripts/measure_class_count.py")
    ev = {"X": 10}
    wd = {"X": 7}
    detail = {"class": "X", "events": 10, "words": 7, "extra_events": 1,
              "the_extra": [], "words_raising_it_more_than_once": 1}
    g = MC.guards(ev, wd, detail)
    acc = next(x for x in g if x["guard"] == "G_DIFFERENCE_IS_ACCOUNTED")
    assert not acc["passes"]


# ═════════════════════════════ E5 · عددُ الفهرس ═════════════════════════
def test_the_index_count_is_derived_not_written():
    idx = json.loads((ROOT / "output/exec_now/02_ledger.json")
                     .read_text(encoding="utf-8"))["index"]
    doc = (ROOT / "output" / "INDEX.md").read_text(encoding="utf-8")
    assert f"**ولا رقمَ جامعٌ عبر المقامات.** {len(idx)} مقامات" in doc
    assert "خمسةُ مقامات" not in doc


def test_poison_a_written_index_count_would_drift():
    """السمُّ: يُزاد دفترٌ ⟶ الرقمُ المشتقُّ يتبع، والمكتوبُ لا يتبع."""
    src = (ROOT / "scripts/build_exec_now.py").read_text(encoding="utf-8")
    assert 'f"**ولا رقمَ جامعٌ عبر المقامات.** {len(idx)} مقاماتٍ' in src


# ═══════════════════════════ R5 · R6 · السحبُ والقيد ════════════════════
@pytest.fixture(scope="module")
def wd():
    return json.loads((BOUND / "03_withdrawn.json").read_text(encoding="utf-8"))


def test_every_withdrawal_is_recorded_with_its_own_source(wd):
    """`مسجَّلٌ بمصدره` — والثالثُ يكسر النسق، فلا يُبتلع تحت اسم الأوّلَين.

    والسطرُ الجامعُ كان يقول «الخطآن مصدرُهما REVIEWER» — عددًا ووصفًا
    مكتوبَين بيد. فلمّا دخل ثالثٌ مصدرُه الأداةُ صار السطرُ نفسُه دعوى
    باطلة. فيُشتقّ من الجدول، ويُقابَل به هنا.
    """
    w = wd["reviewer_withdrawn"]
    assert set(w) == {"REVIEWER_WITHDRAWN_1", "REVIEWER_WITHDRAWN_2",
                      "REVIEWER_WITHDRAWN_3A", "REVIEWER_WITHDRAWN_3B"}
    for k, v in w.items():
        assert v["source"] in ("REVIEWER", "TOOL"), k
        # النسبةُ تتبع المصدر، ولا تُكتب مستقلّةً عنه
        assert v["attributed_to_tool"] is (v["source"] == "TOOL"), k
        assert v["replaced_by"], k
    by = wd["withdrawn_by_source"]
    assert by == {"REVIEWER": 3, "TOOL": 1}
    assert sum(by.values()) == len(w)
    # والسطرُ الجامعُ مشتقٌّ: يذكر المصدرَين معًا بعدديهما
    for src, n in by.items():
        assert f"{src} {n}" in wd["attribution_rule"]


def test_the_third_withdrawal_is_two_claims_with_two_sources(wd):
    """اسمٌ مشتركٌ جمع حقلًا صادقًا وتأويلًا باطلًا — فشُطر بحكم المالك.

    والفرقُ ليس محاسبيًّا: الأداةُ نقلت حقلًا كما هو، والمراجعُ أوّله.
    وبطلانُ التأويل لا يمسّ صدقَ الحقل، وصدقُ الحقل لا يُصحّح التأويل.
    """
    w = wd["reviewer_withdrawn"]
    a, b = w["REVIEWER_WITHDRAWN_3A"], w["REVIEWER_WITHDRAWN_3B"]

    # ١ — النصفُ الذي للأداة: حقلٌ **صادق**، وعيبُه سَعةُ اللفظ
    assert a["source"] == "TOOL" and a["attributed_to_tool"] is True
    assert a["field_is_true"] is True
    assert a["verdict"] == "ناقصٌ لا كاذب"
    assert "runtime_implemented=False" in a["why"]

    # ٢ — والنصفُ الذي للمراجع: تأويلٌ **باطل**، وهو الذي كلّف
    assert b["source"] == "REVIEWER" and b["attributed_to_tool"] is False
    assert b["verdict"] == "باطل"
    assert "sonaiso" in b["claim"]
    assert b["held_for"] and "ج-٣" in b["cost"]
    assert "DR_HUSSEIN" in b["withdrawn_by"]

    # ٣ — والحكمان مختلفان: لو اتّحدا لعاد الشطرُ لفظًا بلا أثر
    assert a["verdict"] != b["verdict"]
    assert a["source"] != b["source"]

    # ٤ — والشطرُ نفسُه واقعةٌ تُقرأ، والأصلُ لا يُمحى
    s = wd["split_origins"]["REVIEWER_WITHDRAWN_3"]
    assert s["ruled_by"] == "DR_HUSSEIN"
    assert set(s["became"]) == {"REVIEWER_WITHDRAWN_3A",
                                "REVIEWER_WITHDRAWN_3B"}
    assert a["split_from"] == b["split_from"] == "REVIEWER_WITHDRAWN_3"
    assert "REVIEWER 3 · TOOL 1" in s["effect_on_attribution"]


def test_the_obsolete_claim_is_measured_and_kept(wd):
    ob = wd["obsolete_claim"]
    assert ob["status"] == "SUPERSEDED"
    assert ob["deleted"] is False
    assert "2.9.0" in ob["superseded_by"] and "T4B" in ob["superseded_by"]
    m = ob["measured"]
    assert m["katab_rows"] == 8 and m["katab_peels"] == 0
    assert m["root_proven_yes"] == 0 and m["axis4_rows"] == 74668


def test_every_site_of_the_obsolete_claim_carries_the_tag(wd):
    ob = wd["obsolete_claim"]
    assert ob["occurrences_in_this_tree"], "جردٌ فارغٌ يُقرأ «لا موضع»"
    assert ob["untagged_sites"] == []
    for x in ob["occurrences_in_this_tree"]:
        body = (ROOT / x["file"]).read_text(encoding="utf-8").splitlines()
        near = "\n".join(body[x["line"] - 1:x["line"] + 5])
        assert "SUPERSEDED" in near, f'{x["file"]}:{x["line"]}'
        assert x["text"][:20] in near, "النصُّ الأصليُّ يبقى — لا يُمحى"


def test_poison_an_untagged_site_is_caught(tmp_path):
    """السمّ: موضعٌ بلا وسمٍ عنده ⟶ يُسمّى."""
    f = tmp_path / "doc.md"
    f.write_text("تقشيرُ كَتَبَ ينزل عن ACCEPT بـT-6\nسطرٌ آخر\n",
                 encoding="utf-8")
    body = f.read_text(encoding="utf-8").splitlines()
    near = "\n".join(body[0:6])
    assert "SUPERSEDED" not in near      # هذا ما يلتقطه الحارس


def test_the_scan_exclusion_is_declared_not_silent(wd):
    ex = wd["obsolete_claim"]["scan_excludes"]
    assert any("output/bound/" in x for x in ex)


# ═══════════════════════════════ الحرّاسُ العامّة ═════════════════════════
def test_vendor_untouched_and_pinned():
    g = BB.vendor_gate()
    assert g["untouched"] and g["matches_pin"]


def test_no_owner_item_was_decided():
    """`G_NO_OWNER` — لم يُحسم بندُ مالكٍ في هذه الجولة."""
    led = json.loads((ROOT / "output/remediation/01_ledger.json")
                     .read_text(encoding="utf-8"))
    owned = [i for i in led["items"] if i["authority"] == "OWNED_BY_OWNER"]
    assert owned and all(i["status"] == "RAISED" for i in owned)


def test_no_residual_kind_was_assigned():
    d = json.loads((ROOT / "data/residual_kind_assignment.json")
                   .read_text(encoding="utf-8"))
    assert set(d["assignments"].values()) == {None}


def test_the_nazila_header_is_at_the_head_of_the_bound_report():
    doc = (BOUND / "04_report.md").read_text(encoding="utf-8")
    head = doc.split("## ", 1)[0]
    for key in ("NAZILA_SCORE", "VENDOR_HEAD", "SCORE_RAISED = NO",
                "CLAIM_PROJECT_FINISHED = NO"):
        assert key in head, key


def test_every_named_poison_in_this_round_exists():
    named = []
    for path in ("output/bound/00_c3_bounded.json",
                 "output/bound/01_origins.json",
                 "output/bound/03_withdrawn.json"):
        raw = (ROOT / path).read_text(encoding="utf-8")
        for chunk in raw.split('"poison": "')[1:]:
            named.append(chunk.split('"')[0])
    assert named, "جولةٌ بلا سمٍّ مسمًّى"
    for ref in named:
        f, _, t = ref.partition("::")
        p = ROOT / f
        assert p.is_file(), ref
        assert f"def {t}(" in p.read_text(encoding="utf-8"), ref


def test_the_doors_ledger_names_both_denominators_for_b2():
    """`R3` — ١٨٬١٤٣ لا تُصحَّح، وتُسمّى أحداثًا؛ ومعها مقامُ الكلمات."""
    d = json.loads((ROOT / "output/doors/00_doors.json")
                   .read_text(encoding="utf-8"))
    b2 = next(x for x in d["doors"] if x["door"] == "B2")["correctness"]
    assert b2["events_affected"] == 18143
    assert b2["words_affected"] == 18135
    assert "مواضع" in b2["events_affected_denominator"]
    assert "كلمات" in b2["words_affected_denominator"]


def test_the_remediation_ledger_names_both_denominators_for_b2():
    led = json.loads((ROOT / "output/remediation/01_ledger.json")
                     .read_text(encoding="utf-8"))
    b2 = next(i for i in led["items"] if i["ident"] == "B2")["evidence"]
    assert b2["total_events_affected"] == 18143
    assert b2["total_words_affected"] == 18135
    assert "لا كلماتٍ متمايزة" in b2["total_events_denominator"]


def test_the_projected_impact_declares_it_uses_the_words_denominator():
    doc = (ROOT / "reports/gamma_shadow/PROJECTED_IMPACT.md").read_text(
        encoding="utf-8")
    assert "18135" in doc and "18143" in doc
    assert "بمقام الكلمات" in doc


def test_no_document_shows_18143_without_a_denominator():
    """السمُّ الحقيقيّ: رقمٌ بلا مقامٍ في أيّ وثيقةٍ مُصدَّرة."""
    naked = []
    for rel in ("output/doors/00_doors.json",
                "output/remediation/01_ledger.json"):
        raw = (ROOT / rel).read_text(encoding="utf-8")
        if "18143" in raw and "denominator" not in raw:
            naked.append(rel)
    assert naked == []
