"""سمومُ `TANWEEN_UNFOLD_APPLY` — أوّلُ تغييرِ سلوكٍ في هذا العمل.

وحارسُ التطابق `G_IDENTICAL` لا يصلح هنا، ويحلّ محلَّه أضيقُ منه:
`G_CHANGE_IS_BOUNDED`. وكلُّ حارسٍ يُسقَط بيدٍ هنا، والسمُّ تشغيلٌ لا نصّ.
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
T = ROOT / "output" / "tanween"


def load(name: str, rel: str):
    for extra in ("src", "scripts"):
        sys.path.insert(0, str(ROOT / extra))
    spec = importlib.util.spec_from_file_location(name, ROOT / rel)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


MT = load("mt_t", "scripts/measure_tanween.py")
MA = load("ma_t", "scripts/measure_tanween_after.py")

sys.path.insert(0, str(ROOT / "src"))
from aslot.axes.axis1_normalization import (  # noqa: E402
    TANWEEN_UNFOLD_TABLE,
    OwnerPolicy,
    normalize_token,
)

POLICY = OwnerPolicy.load(ROOT / "data" / "axis_1_owner_policy.json")


def norm(word: str) -> str:
    return normalize_token(word, (1, 1, 1), POLICY).normalized


# ═════════════════════════ الأشكالُ الثلاثة — تُنفَّذ ═══════════════════
@pytest.mark.parametrize("word,expected", [
    ("مَرَضَاً", "مَرَضَنْ"),      # ألفٌ ⟶ تُحذف
    ("هُدَىً", "هُدَنْ"),          # مقصورةٌ ⟶ تُحذف
    ("بَعُوضَةً", "بَعُوْضَتَنْ"),  # تاءٌ مربوطة ⟶ ت مفتوحة
])
def test_the_three_ratified_shapes_unfold(word, expected):
    assert norm(word) == expected


def test_the_deletion_removes_a_letter_and_the_flip_does_not():
    """`G_TWO_MECHANISMS` — الفرقُ في المخرَج لا في الكلام."""
    def letters(s):
        return [c for c in s if c not in MT.MARKS]
    assert len(letters(norm("مَرَضَاً"))) == len(letters("مَرَضَاً"))  # ا⟶ن
    flipped = letters(norm("بَعُوضَةً"))
    assert "ة" not in flipped and "ت" in flipped
    assert "ا" not in letters(norm("مَرَضَاً"))[-2:]


# ═══════════════════════════ الموقوفُ — لا يُنفَّذ ══════════════════════
@pytest.mark.parametrize("word", [
    "مَاءً",      # P1 — همزةٌ بتنوين فتح
    "غِشَاوَةٌ",   # P2 — ة مع الضمّ
    "بِسُورَةٍ",   # P2 — ة مع الكسر
    "سَوِيًّا",    # P3 — ON_PENULT_FINAL_BARE
])
def test_pending_shapes_are_untouched(word):
    """`G_PENDING_UNTOUCHED` — ولا يُنفَّذ منها صفٌّ ولو بدا حكمُه بيّنًا."""
    out = norm(word)
    letters = [c for c in out if c not in MT.MARKS]
    if "ة" in word:
        assert "ة" in letters, "التاءُ المربوطة لم تُقلب — وهي موقوفة"
    if word == "سَوِيًّا":
        assert "ا" in letters, "الألفُ لم تُحذف — والموقعُ موقوف"


@pytest.mark.parametrize("word", ["عَذَابٌ", "شَيْءٍ"])
def test_ratified_unchanged_shapes_still_expand_as_before(word):
    """`G_RATIFIED_UNCHANGED` — مصادقةٌ على سلوكٍ قائم، لا تعديل."""
    out = norm(word)
    assert out.endswith("نْ")
    assert [c for c in out if c not in MT.MARKS][:-1] == \
           [c for c in word if c not in MT.MARKS]


# ══════════════════════ سمومُ الجدول — التوسيعُ يُلتقَط ═════════════════
def test_the_table_is_closed_at_three_rows():
    assert len(TANWEEN_UNFOLD_TABLE) == 3
    assert sorted(TANWEEN_UNFOLD_TABLE) == sorted(["ا", "ى", "ة"])
    assert sorted(set(TANWEEN_UNFOLD_TABLE.values())) == [
        "DELETE_CARRIER", "TURN_TO_OPEN_TAA"]


def test_poison_a_fourth_row_in_the_table_is_caught():
    """السمُّ: يُدسّ شكلٌ رابعٌ في جدول القاعدة ⟶ يسقط `G_NO_RULE_WIDENING`."""
    widened = {**TANWEEN_UNFOLD_TABLE, "ء": "DELETE_CARRIER"}
    assert len(widened) == 4
    guard = len(widened) == 3
    assert not guard, "جدولٌ بأربعة أسطرٍ يجب أن يُسقط الحارس"


def test_poison_a_hamza_would_change_if_the_table_were_widened(monkeypatch):
    """والسمُّ تشغيلٌ لا نصّ: يُوسَّع الجدولُ فعلًا ⟶ يتغيّر صفٌّ موقوف."""
    import aslot.axes.axis1_normalization as A1
    before = norm("مَاءً")
    monkeypatch.setitem(A1.TANWEEN_UNFOLD_TABLE, "ء", "DELETE_CARRIER")
    after = normalize_token("مَاءً", (1, 1, 1), POLICY).normalized
    assert after != before, "التوسيعُ يغيّر موقوفًا — وهذا ما يمنعه الجدول"


def test_poison_the_flip_done_by_deletion_breaks_the_taa(monkeypatch):
    """`G_TWO_MECHANISMS` — لو نُفِّذ الانقلابُ بالحذف لخرجت التاءُ خطأً."""
    import aslot.axes.axis1_normalization as A1
    correct = norm("بَعُوضَةً")
    monkeypatch.setitem(A1.TANWEEN_UNFOLD_TABLE, "ة", "DELETE_CARRIER")
    wrong = normalize_token("بَعُوضَةً", (1, 1, 1), POLICY).normalized
    assert wrong != correct
    assert "ت" not in [c for c in wrong if c not in MT.MARKS]


def test_poison_the_deletion_done_by_flipping_breaks_the_alif(monkeypatch):
    """والعكسُ كذلك: لو نُفِّذ الحذفُ انقلابًا لخرجت الألفُ تاءً."""
    import aslot.axes.axis1_normalization as A1
    correct = norm("مَرَضَاً")
    monkeypatch.setitem(A1.TANWEEN_UNFOLD_TABLE, "ا", "TURN_TO_OPEN_TAA")
    wrong = normalize_token("مَرَضَاً", (1, 1, 1), POLICY).normalized
    assert wrong != correct and "ت" in wrong


def test_the_rule_requires_the_carrier_to_be_the_final_rasm_letter():
    """شرطُ `is_last` هو ما يُجمِّد `P3` — يُسقَط ويُرى الأثر."""
    import aslot.axes.axis1_normalization as A1
    src = Path(A1.__file__).read_text(encoding="utf-8")
    body = src.split("def _tanween_unfold(")[1].split("\n    def ")[0]
    assert "ctx.is_last" in body
    assert "FATHATAN" in body


# ═══════════════════════ الجردُ الثلاثيُّ — يقفل ════════════════════════
@pytest.fixture(scope="module")
def after():
    p = T / "02_after.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل measure_tanween_after بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


def test_the_three_way_inventory_closes(after):
    assert after["changes_expected"] == 3659
    assert after["ratified_unchanged"] == 4417
    assert after["pending_total"] == 818
    assert after["three_way_sum"] == after["tanweened_total"] == 8894
    assert after["orphans"] == 0


def test_exactly_the_expected_rows_changed(after):
    assert after["rows_changed_measured"] == 3659
    assert after["out_of_scope_changes"] == []
    assert after["changed_by_bucket"] == {"CHANGES": 3659}


def test_no_pending_row_moved_in_any_axis(after):
    for axis, v in after["across_axes"].items():
        for b in v["by_bucket"]:
            assert not b.startswith("PENDING"), f"{axis}: {b}"


def test_poison_change_is_bounded_falls_on_one_out_of_scope_row():
    """السمُّ: يُدسّ صفٌّ خارج النطاق في قائمة المتغيّر ⟶ يسقط."""
    a = {"tanweened_total": 8894, "changes_expected": 3659,
         "rows_changed_measured": 3660,
         "out_of_scope_changes": [{"position": "1:1:1", "bucket": "PENDING_P2"}],
         "ratified_unchanged": 4417, "pending_total": 818,
         "pending_split": {}, "three_way_sum": 8894, "orphans": 0,
         "changed_by_bucket": {"CHANGES": 3659, "PENDING_P2": 1},
         "across_axes": {"axis1": {"denominator": 1, "rows_moved": 1,
                                   "out_of_scope": 1, "named": [],
                                   "out_of_scope_columns": {"Verdict": 1},
                                   "out_of_scope_judging_columns": ["Verdict"],
                                   "by_bucket": {}}}}
    g = MA.guards(a, {}, {"scope": 0, "consonants_dropped_in": 0,
                          "expected_drop_derived": 0,
                          "expected_drop_arithmetic": "",
                          "drop_matches_derivation": True})
    bounded = next(x for x in g if x["guard"] == "G_CHANGE_IS_BOUNDED")
    assert not bounded["passes"]
    allax = next(x for x in g
                 if x["guard"] == "G_CHANGE_IS_BOUNDED_ALL_AXES")
    assert not allax["passes"]


def test_poison_pending_untouched_falls_when_a_pending_row_moves():
    a = {"tanweened_total": 8894, "changes_expected": 3659,
         "rows_changed_measured": 3659, "out_of_scope_changes": [],
         "ratified_unchanged": 4417, "pending_total": 818,
         "pending_split": {"PENDING_P2": 735},
         "three_way_sum": 8894, "orphans": 0,
         "changed_by_bucket": {"CHANGES": 3659, "PENDING_P2": 3},
         "across_axes": {}}
    g = MA.guards(a, {}, {"scope": 0, "consonants_dropped_in": 0,
                          "expected_drop_derived": 0,
                          "expected_drop_arithmetic": "",
                          "drop_matches_derivation": True})
    x = next(y for y in g if y["guard"] == "G_PENDING_UNTOUCHED")
    assert not x["passes"] and x["changed"] == 3


def test_poison_three_way_falls_on_an_orphan_pair():
    a = {"tanweened_total": 8894, "changes_expected": 3659,
         "rows_changed_measured": 3659, "out_of_scope_changes": [],
         "ratified_unchanged": 4417, "pending_total": 800,
         "pending_split": {}, "three_way_sum": 8876, "orphans": 18,
         "changed_by_bucket": {}, "across_axes": {}}
    g = MA.guards(a, {}, {"scope": 0, "consonants_dropped_in": 0,
                          "expected_drop_derived": 0,
                          "expected_drop_arithmetic": "",
                          "drop_matches_derivation": True})
    x = next(y for y in g if y["guard"] == "G_THREE_WAY_CLOSES")
    assert not x["passes"]


def test_poison_drop_is_derived_falls_when_the_count_is_not_the_delete_rows():
    a = {"tanweened_total": 1, "changes_expected": 1,
         "rows_changed_measured": 1, "out_of_scope_changes": [],
         "ratified_unchanged": 0, "pending_total": 0, "pending_split": {},
         "three_way_sum": 1, "orphans": 0, "changed_by_bucket": {},
         "across_axes": {}}
    g = MA.guards(a, {}, {"scope": 10, "consonants_dropped_in": 7,
                          "expected_drop_derived": 5,
                          "expected_drop_arithmetic": "x=5",
                          "drop_matches_derivation": False})
    x = next(y for y in g if y["guard"] == "G_DROP_IS_DERIVED")
    assert not x["passes"]


# ══════════════════════════ B3 · B2 — مقيسان لا محسومان ═══════════════
@pytest.fixture(scope="module")
def bb():
    return json.loads((T / "04_b2_b3.json").read_text(encoding="utf-8"))


def test_b3_is_measured_and_not_declared_closed(bb):
    b3 = bb["B3"]
    assert b3["consonants_dropped_in"] == 3152
    assert b3["expected_drop_derived"] == 3152
    assert b3["drop_matches_derivation"] is True
    assert b3["closed"] is None, "لا يُقال «أُغلق» — الحكمُ للمالك"
    assert b3["left_accept"] == 0


def test_b3_reports_both_facts_not_one(bb):
    """الصامتُ زال · والحكمُ لم يتحرّك — خبران لا خبر."""
    assert "زال" in bb["B3"]["what_moved"]
    assert "لم يتحرّك" in bb["B3"]["what_moved"]


def test_b2_is_presented_not_decided(bb):
    b2 = bb["B2"]
    assert b2["verdict"] is None
    assert b2["decided_by_tool"] is False
    assert b2["status"] == "OWNER_PENDING"
    assert b2["u_tanween_words_after"] == 8894


# ═══════════════════════ الموقوفُ — منشورٌ بأعيانه ═════════════════════
@pytest.fixture(scope="module")
def pend():
    return json.loads((T / "05_pending.json").read_text(encoding="utf-8"))


def test_pending_totals_and_zero_executed(pend):
    assert pend["total"] == 818 and pend["executed_total"] == 0
    assert pend["P1"]["count"] == 82
    assert pend["P2"]["count"] == 735
    assert pend["P3"]["count"] == 1
    for tag in ("P1", "P2", "P3"):
        assert pend[tag]["executed_rows"] == 0


def test_the_single_word_is_printed_letter_by_letter(pend):
    """«ولا تُطوى بحكم العدد»."""
    w = pend["P3"]["the_word"][0]
    assert w["position"] == "19:43:13"
    assert len(w["spelling"]) == len(w["word"])
    for c in w["spelling"]:
        assert c["codepoint"].startswith("U+") and c["name"] != "UNNAMED"
    assert any(c["name"] == "ARABIC FATHATAN" for c in w["spelling"])
    assert w["spelling"][-1]["name"] == "ARABIC LETTER ALEF"


def test_p1_records_the_owners_own_note(pend):
    assert "لم يُفسَّر" in pend["P1"]["owner_note"]
    assert pend["P1"]["measured_now"]


# ═════════════════════════ ما لم يتحرّك — يُثبَت ═══════════════════════
def test_the_nazila_score_did_not_drift():
    """`G_SCORE_DID_NOT_DRIFT` — التغييرُ في أسلوط لا في تعقُّل."""
    sc = json.loads((ROOT / "output/nazila_result/scores.json")
                    .read_text(encoding="utf-8"))
    assert sc["CLOSURE_POTENTIAL"] == 70.9
    assert sc["STAGES_OPENED"] == "1/16"
    assert sc["GROUNDED"] == 207 and sc["CELLS_TOTAL"] == 292


def test_the_vendor_is_untouched_and_pinned():
    B = load("btr", "scripts/build_tanween_report.py")
    g = B.vendor_gate()
    assert g["untouched"] and g["matches_pin"]


def test_the_positional_id_finding_is_raised_not_folded(after):
    g = next(x for x in after["guards"]
             if x["guard"] == "G_CHANGE_IS_BOUNDED_ALL_AXES")
    assert g["passes"]
    assert "Matched_Entry_Ids" in g["out_of_scope_columns"]["axis2"]
    assert not g["judging_columns_moved"]
    doc = (T / "06_report.md").read_text(encoding="utf-8")
    assert "POSITIONAL_ENTRY_ID" in doc and "OWNER_PENDING" in doc


def test_the_byte_identity_baseline_records_why_it_was_superseded():
    """`G_IDENTICAL` سقط — والسقوطُ دليلٌ لا خلل، ويُسجَّل بسببه.

    وكان يُقرأ من `baseline_superseded_by` وهو حقلٌ واحدٌ يُكتب فوق
    سابقه — فأوّلُ جولةٍ تالية تمحو واقعةَ التنوين ويسقط هذا الفحص على
    جولةٍ لا شأنَ لها به. فيُقرأ الآن من `supersessions` **بمهمّته**،
    والسوابقُ تبقى مكتوبةً.
    """
    ev = json.loads((ROOT / "output/max/byte_identity_evidence.json")
                    .read_text(encoding="utf-8"))
    hist = ev["supersessions"]
    s = next((x for x in hist if x.get("task") == "TANWEEN_UNFOLD_APPLY"), None)
    assert s is not None, [x.get("task") for x in hist]
    assert "N-TANWEEN-UNFOLD" in s["reason"]
    assert 0 < s["count"] <= s["of"]
    # وواقعةُ التنوين حرّكت المحاورَ الأربعةَ، لا ملفَّ مقاييسَ وحدَه
    assert s["count"] >= 10
    assert ev["differing_between_runs"] == [], "إعادةُ الإنتاج هي الباقية"
    assert ev["runs"] == 2
    # والتاريخُ يُراكم: الأخيرُ هو ذيلُ القائمة، والحقلُ القديمُ مرآتُه
    assert ev["baseline_superseded_by"] == hist[-1]


# ═════════════════ Q1 · Q2 · والشاهدُ الإيجابيّ ═══════════════════════
@pytest.fixture(scope="module")
def qz():
    p = T / "07_q1_q2.json"
    if not p.is_file():
        pytest.skip("لم يُشغَّل measure_q1_q2 بعدُ")
    return json.loads(p.read_text(encoding="utf-8"))


def test_q1_source_is_read_from_the_code_not_guessed(qz):
    q = qz["Q1"]
    assert q["answer"].startswith("MATCHED_ENTRIES")
    c = q["code_evidence"]
    assert c["entries_are_fetched_by_ids"] is True
    assert c["word_class_from_entries"] and c["operator_role_from_entries"]
    assert c["sites"]["word_class"] and c["sites"]["operator_role"]


def test_q1_corrects_the_earlier_reading(qz):
    """«يُسجَّل ولا يُستعمل» — باطل، والتصحيحُ مسجَّل لا مطويّ."""
    q = qz["Q1"]
    assert "باطل" in q["so_the_earlier_reading_is_corrected"]
    assert q["row_evidence"]["of_which_word_class_moved"] == 0
    assert q["row_evidence"]["of_which_operator_role_moved"] == 0
    assert q["row_evidence"]["rows_where_ids_moved"] == 664


def test_q2_source_is_the_normalized_word(qz):
    q = qz["Q2"]
    assert q["answer"].startswith("NORMALIZED_WORD")
    assert q["code_evidence"]["argument_is_normalized"] is True
    assert any('Normalized_Word' in ln
               for ln in q["code_evidence"]["call_sites"])


def test_q2_silence_is_a_true_report_not_a_structural_blank(qz):
    """والنطاقُ ليس كلَّه فارغًا: 1,904 صفًّا فيها madd=PROVEN قبلَ وبعدُ."""
    b = qz["Q2"]["row_evidence"]["before"]
    a = qz["Q2"]["row_evidence"]["after"]
    assert b == a, "لم يتحرّك شيء — وهو الخبر"
    proven = sum(v for k, v in b.items() if "madd=PROVEN" in k)
    assert proven > 0, "لو كان النطاقُ كلُّه فارغًا لما قال السكونُ شيئًا"
    assert qz["Q2"]["row_evidence"]["rows_moved"] == 0


def test_the_reconstruction_witness_is_positive_evidence(qz):
    w = qz["reconstruction_witness"]
    assert w["rows_moved"] == 0
    assert w["structure_moved"] == 3152
    assert w["values_after"]["YES"] == 74661
    assert "يُحسَب" in w["why_it_is_positive_evidence"]


def test_the_witness_and_the_two_questions_are_in_the_report(qz):
    doc = (T / "06_report.md").read_text(encoding="utf-8")
    assert "Reconstruction_Verified" in doc
    assert "MATCHED_ENTRIES" in doc and "NORMALIZED_WORD" in doc
    assert "POSITIONAL_ENTRY_ID" in doc
