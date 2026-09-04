"""يسمّم حرّاسَ الإصلاح الشامل، ويُثبت سقوطَ كلّ واحدٍ منها  (`§د`).

**القاعدةُ التي تحكم هذا الملفّ.** `NO_TEXTUAL_GUARD`: لا حارسَ يفحص ورودَ
اسمٍ في نصّ — يُشغَّل أو لا يُعدّ. فكلُّ اختبارٍ هنا يستورد المولّد، يُفسد ما
يحرسه الحارس، ويُطالب بالسقوط. وحارسٌ لم يُرَ ساقطًا ليس حارسًا بل سطرٌ يمرّ.

**و`CAUSE_IS_A_CLAIM` (`A6`).** ثلاثةُ تعليلاتٍ باطلةٍ سُحبت في ثلاث جولات،
ولا واحدةَ منها أوقفها إجراء. فالقاعدةُ هنا إجراءٌ: علّةٌ في تقريرٍ إمّا لها
أمرٌ منشورٌ يُعيد إنتاجها، وإمّا تُوسم `HYPOTHESIS`.
"""
from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "build_remediation.py"
OUT = ROOT / "output" / "remediation"
VENDOR = ROOT / "vendor" / "Taaqol-GPT"


def load():
    sys.path.insert(0, str(ROOT / "src"))
    spec = importlib.util.spec_from_file_location("brem", GEN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["brem"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return load()


@pytest.fixture(scope="module")
def ledger():
    p = OUT / "01_ledger.json"
    if not p.is_file():
        pytest.skip(f"لم يُشغَّل المولّد بعدُ: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


# ── VENDOR_UNTOUCHED — البوّابةُ الحاسمة ────────────────────────────────
def test_vendor_is_byte_for_byte_clean():
    """`G1` — دليلٌ لا يُعاد بناؤه ليس دليلًا ناقصًا، بل ليس دليلًا."""
    head = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    st = subprocess.run(["git", "-C", str(VENDOR), "status", "--porcelain"],
                        capture_output=True, text=True, check=False)
    assert head.stdout.strip() == "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
    assert st.stdout.strip() == "", f"vendor مُلوَّث: {st.stdout[:300]}"


def test_the_g1_gate_falls_on_a_dirty_or_moved_vendor(mod, monkeypatch):
    """سمٌّ على البوّابة: بصمةٌ أخرى ⟶ لا تمرّ، ولا يُكتب حرف."""
    monkeypatch.setattr(mod, "PIN", "0" * 40)
    assert mod.gate_reproducible()["passes"] is False


def test_a_blocked_g1_writes_nothing(tmp_path):
    """والوقوفُ صمتٌ: يُشغَّل المولّد فعلًا ببصمةٍ مسمومة، ولا مجلَّدَ يُكتب."""
    poisoned = tmp_path / "poisoned.py"
    src = GEN.read_text(encoding="utf-8")
    assert 'PIN = "3cccdded' in src
    poisoned.write_text(src.replace("3cccdded7951ba71b3cb2a8b9b477f3fb3d91095",
                                    "0" * 40), encoding="utf-8")
    dest = tmp_path / "out"
    r = subprocess.run([sys.executable, str(poisoned), "--out", str(dest)],
                       capture_output=True, text=True, cwd=ROOT, check=False,
                       env={**__import__("os").environ,
                            "PYTHONPATH": str(ROOT / "src")})
    assert r.returncode == 2, r.stdout + r.stderr
    assert "BLOCKED_AT_G1" in r.stdout
    assert not dest.exists()


# ── NO_OWNER_INFERENCE — لا بندَ من (ب) يُحسم ──────────────────────────
def test_an_owner_item_cannot_be_marked_done(mod):
    """أخطرُ خرقٍ: أن يحسم الوكيلُ حكمًا. فيُرفض عند البناء لا عند المراجعة."""
    with pytest.raises(mod.Blocked) as e:
        mod.Item("Bx", "سؤالُ مالك", "OWNED_BY_OWNER", "DONE", evidence={"a": 1})
    assert "AUTHORITY_VIOLATION" in str(e.value)


def test_an_owner_item_may_only_be_raised(mod):
    assert mod.Item("Bx", "س", "OWNED_BY_OWNER", "RAISED",
                    evidence={"a": 1}).status == "RAISED"


def test_no_owner_item_was_decided_in_the_real_ledger(ledger):
    assert ledger["guards"]["NO_OWNER_INFERENCE"] == []
    raised = [i for i in ledger["items"] if i["authority"] == "OWNED_BY_OWNER"]
    assert raised, "لا بندَ مالكٍ أصلًا — والدفترُ يعلن تسعة"
    assert {i["status"] for i in raised} == {"RAISED"}


def test_every_owner_item_carries_a_measured_effect_for_its_options(ledger):
    """«أثرُ كلّ خيارٍ مقيسًا» — فسؤالٌ بلا أثرٍ مقيسٍ ترجيحٌ مؤجَّل."""
    thin = [i["ident"] for i in ledger["items"]
            if i["authority"] == "OWNED_BY_OWNER"
            and len(json.dumps(i["evidence"], ensure_ascii=False)) < 60]
    assert thin == [], f"بنودٌ بلا أثرٍ مقيس: {thin}"


# ── VENDOR ITEMS — لا يُلمس ولا يُوسم منفَّذًا ──────────────────────────
def test_an_out_of_jurisdiction_item_cannot_be_marked_done(mod):
    """`ج` تُقاس وتُعلن. ووسمُها `DONE` يعني أنّ المصدرَ مُسّ."""
    with pytest.raises(mod.Blocked):
        mod.Item("Cx", "عيبٌ في تعقُّل", "OUT_OF_JURISDICTION", "DONE",
                 evidence={"a": 1})


def test_no_upstream_path_was_chosen_by_the_agent(ledger):
    """ج-٢ وج-٣ حكمُ مالك. فيبقى المسلكُ `NOT_CHOSEN` حتى يَحكم."""
    path = next(i for i in ledger["items"] if i["ident"] == "C_PATH")
    assert path["status"] == "NOT_CHOSEN"
    assert path["evidence"]["chosen"] is None


def test_an_unknown_authority_or_status_is_refused(mod):
    with pytest.raises(mod.Blocked):
        mod.Item("X", "ع", "OWNED_BY_ME", "DONE", evidence={"a": 1})
    with pytest.raises(mod.Blocked):
        mod.Item("X", "ع", "OWNED_BY_AGENT", "ALMOST_DONE", evidence={"a": 1})


# ── LEDGER_CLOSES — عدٌّ ثانٍ، لا متطابقة ──────────────────────────────
def test_the_recount_is_scoped_and_not_a_tautology(mod, ledger):
    """سمٌّ حقيقيّ: يُحذف صفٌّ من التقرير المطبوع، فيسقط الإقفال.

    وأوّلُ تشغيلٍ لهذا العدّ أسقط نفسَه: عدَّ ٣٨ صفًّا لخمسةٍ وعشرين بندًا
    لأنّ جدولَ البصمات يبدأ صفوفُه بالشكل نفسِه. وذلك ما يفعله عدٌّ ثانٍ،
    ولا تفعله `x + (n − x) == n`.
    """
    items = [mod.Item(f"Z{i}", "ع", "OWNED_BY_AGENT", "DONE", evidence={"a": i})
             for i in range(4)]
    doc = mod.render(items, {"laws": [], "carriers": []},
                     {"vendor_head": "x", "porcelain_lines": 0},
                     mod.closure(items, {"passes": True},
                                 {"NO_OWNER_INFERENCE": []}))
    assert mod.recount(doc, items)["closes"] is True
    dropped = "\n".join(ln for ln in doc.splitlines()
                        if not ln.startswith("| `Z1`"))
    assert mod.recount(dropped, items)["closes"] is False


def test_the_real_ledger_closes_by_the_second_count(ledger):
    rc = ledger["recount_from_report"]
    assert rc["rows"] == len(ledger["items"])
    assert rc["closes"] is True
    assert sum(rc["by_status"].values()) == len(ledger["items"])


def test_no_item_is_broken(ledger):
    """`G3` — بندٌ بلا دليلٍ وبلا سبب يُقرأ إنجازًا وهو فراغ."""
    assert ledger["guards"]["NO_BROKEN"] == []
    assert ledger["closure"]["BROKEN"] == 0


def test_grounded_plus_named_plus_broken_equals_total(ledger):
    c = ledger["closure"]
    assert c["GROUNDED"] + c["NAMED"] + c["BROKEN"] == c["TOTAL"]
    assert c["TOTAL"] == len(ledger["items"])


# ── DENOMINATOR_IS_PINNED — مانعُ التلاعب ──────────────────────────────
def test_the_score_is_never_printed_alone(ledger):
    """علامةٌ وحدَها هي الرقمُ الواحدُ بمقامين الذي نلاحقه."""
    doc = (OUT / "04_report.md").read_text(encoding="utf-8")
    assert "CLOSURE_EFFECTIVE" in doc and "CLOSURE_POTENTIAL" in doc
    assert "GROUNDED" in doc and "BROKEN" in doc and "STAGES_OPENED" in doc


def test_a_failed_gate_zeroes_the_effective_score(mod):
    """`CLOSURE_EFFECTIVE = 0` إن سقطت واحدة — لا خصمٌ ولا تقريب."""
    items = [mod.Item("Z", "ع", "OWNED_BY_AGENT", "DONE", evidence={"a": 1})]
    sc = mod.closure(items, {"passes": False}, {"NO_OWNER_INFERENCE": []})
    assert sc["gates"]["G1_REPRODUCIBLE"] is False
    doc = mod.render(items, {"laws": [], "carriers": []},
                     {"vendor_head": "x", "porcelain_lines": 0}, sc)
    assert "CLOSURE_EFFECTIVE = 0%" in doc
    assert "G1_REPRODUCIBLE" in doc


def test_moving_an_item_between_families_cannot_silently_raise_the_score(mod):
    """`DENOMINATOR_IS_PINNED` — المقامُ عددُ البنود كلِّها، لا المقفلةَ منها.

    فنقلُ بندٍ من ولايةٍ إلى أخرى يغيّر البسطَ ولا يمسّ المقام، فلا ترتفع
    العلامةُ بإعادة تسميةٍ. وهذا هو السمُّ: بندٌ واحدٌ يُنقل، والمقامُ يثبت.
    """
    before = [mod.Item("Z0", "ع", "OWNED_BY_AGENT", "DONE", evidence={"a": 1}),
              mod.Item("Z1", "س", "OWNED_BY_OWNER", "RAISED", evidence={"b": 1})]
    after = [mod.Item("Z0", "ع", "OWNED_BY_AGENT", "DONE", evidence={"a": 1}),
             mod.Item("Z1", "س", "OUT_OF_JURISDICTION", "NOT_CHOSEN",
                      evidence={"b": 1}, note="مسلكٌ لم يُختر")]
    g = {"NO_OWNER_INFERENCE": []}
    a = mod.closure(before, {"passes": True}, g)
    b = mod.closure(after, {"passes": True}, g)
    assert a["TOTAL"] == b["TOTAL"] == 2
    assert a["CLOSURE_POTENTIAL"] == b["CLOSURE_POTENTIAL"] == 50


# ── CAUSE_IS_A_CLAIM  (`A6`) ───────────────────────────────────────────
def test_every_measured_number_in_the_ledger_has_a_command(ledger):
    """`٤` من معايير القبول: كلُّ رقمٍ له أمرٌ يُعيد إنتاجه.

    ويُفحص على البنود التي تدّعي رقمًا من تشغيلٍ خارجيّ — لا على كلّ حقل،
    وإلا صار الحارسُ شكليًّا يمرّ بأيّ نصّ.
    """
    a7 = next(i for i in ledger["items"] if i["ident"] == "A7")
    assert a7["evidence"]["command_witness"].startswith("python3 -m aslot")
    assert "--no-witness" in a7["evidence"]["command_no_witness"]


def test_the_two_peel_numbers_are_named_by_denominator_not_by_age(ledger):
    """`A7` — الفرقُ مقامان لا قِدَم. والدعوى تُسمّى بعلّتها المقيسة."""
    a7 = next(i for i in ledger["items"] if i["ident"] == "A7")
    e = a7["evidence"]
    assert e["finding"] == "DIFFERENT_DENOMINATORS_NOT_STALENESS"
    assert e["live_with_witness"] != e["live_no_witness"]
    assert e["witness_set_size"] > 0


def test_the_refusal_ledger_closes_by_its_own_arithmetic(ledger):
    """`A8` — ثلاثون مُعلَنًا وسبعةٌ وعشرون مشهودًا، والفرقُ ثلاثةٌ مسمّاة."""
    a8 = next(i for i in ledger["items"] if i["ident"] == "A8")
    e = a8["evidence"]
    assert e["closes"] is True
    assert (e["declared"] - e["observed_in_outputs"]
            == len(e["declared_without_witness"]))


def test_witness_pins_hold_and_are_executed_not_read(ledger):
    """`A5` — يُشغَّل المقابِلُ ويُقرأ رقمُ خروجه، لا يُقرأ عنه في نصّ."""
    w = next(i for i in ledger["items"] if i["ident"] == "A5")["evidence"]
    assert w["exit_code"] == 0
    assert w["holds"] is True
    assert w["pinned"] >= 9


def test_a_changed_witness_verdict_is_caught(mod):
    """سمٌّ على تثبيت الشواهد: يُبدَّل حكمٌ مثبَّت، فيُطالَب المقابِلُ بردّه."""
    spec = importlib.util.spec_from_file_location(
        "wp", ROOT / "scripts" / "witness_pins.py")
    wp = importlib.util.module_from_spec(spec)
    sys.modules["wp"] = wp
    spec.loader.exec_module(wp)
    pinned = json.loads((ROOT / "data" / "witness_pins.json")
                        .read_text(encoding="utf-8"))
    live = json.loads(json.dumps(pinned))
    live["كَبَائِرَ"]["with_declared_witness"]["verdict"] = "ACCEPT"
    drift = wp.compare(live, pinned)
    assert any("كَبَائِرَ" in d for d in drift), drift
    assert wp.compare(pinned, pinned) == []


def test_an_unpinned_named_witness_is_caught(mod):
    """وشاهدٌ يُضاف ولا يُثبَّت يُكشف — وإلا اتّسع الجردُ بلا حراسة."""
    spec = importlib.util.spec_from_file_location(
        "wp2", ROOT / "scripts" / "witness_pins.py")
    wp = importlib.util.module_from_spec(spec)
    sys.modules["wp2"] = wp
    spec.loader.exec_module(wp)
    pinned = json.loads((ROOT / "data" / "witness_pins.json")
                        .read_text(encoding="utf-8"))
    live = {**pinned, "شاهدٌ جديد": {"with_declared_witness": {}}}
    assert any("UNPINNED_WITNESS" in d for d in wp.compare(live, pinned))


# ── الطبقةُ المُعلَنة لا تختلط بالمقيسة  (`A10`) ────────────────────────
def test_the_declared_layer_claims_neither_code_nor_taaqol():
    p = OUT / "declared.json"
    if not p.is_file():
        pytest.skip("declared.json غيرُ موجود")
    d = json.loads(p.read_text(encoding="utf-8"))
    assert d["written_from_code"] is False
    assert d["attributed_to_taaqol"] is False
    assert d["author"] == "DR_HUSSEIN"
    assert d["status_of_every_field_below"] == "AWAITING_OWNER_RATIFICATION"


def test_the_report_never_claims_the_project_is_finished():
    doc = (OUT / "04_report.md").read_text(encoding="utf-8")
    assert "CLAIM_PROJECT_FINISHED = NO" in doc
