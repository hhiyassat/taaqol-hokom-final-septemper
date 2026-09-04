"""يسمّم كلَّ حارسٍ في مولّد المصفوفة بالحالة التي وُضع لها، ويُثبت سقوطَه.

**لماذا التسميم.** حارسٌ لم يُرَ ساقطًا ليس حارسًا، بل سطرٌ يمرّ. وقد وقع
في هذا المستودع أن مرّ فحصٌ لأنّ ملفّه فارغ، ومرّ آخرُ لأنّ حقلًا لا وجودَ
له عُدَّ صفرًا. فلا يُقبل هنا حارسٌ إلا وقد أُسقط مرّةً بيدٍ.

**وكلُّ اختبارٍ ينفّذ.** لا يفحص نصَّ الملفّ ولا تعليقاته: يستورد المولّد،
يُفسد ما يحرسه الحارس، ويُطالب بالسقوط. فحارسٌ نصّيٌّ يمرّ لو كُتب اسمُه
في تعليقٍ ولم يُرفع — وتلك واقعةٌ سُجّلت على الوكيل، لا تُعاد.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
GEN = ROOT / "scripts" / "build_nazila_matrix.py"
VENV = ROOT / ".venv-taaqol" / "bin" / "python"
OUT = ROOT / "output" / "nazila_from_code"
REF = ROOT / "inspection" / "TAAQOL_NAZILA_MATRIX.md"
CASE = ROOT / "inspection" / "case.txt"


def load():
    """يستورد المولّد نفسَه — لا نسخةً منه ولا وصفًا له."""
    sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))
    spec = importlib.util.spec_from_file_location("bnm", GEN)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bnm"] = mod
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope="module")
def mod():
    return load()


@pytest.fixture(scope="module")
def manifest():
    p = OUT / "02_field_manifest.json"
    if not p.is_file():
        pytest.skip(f"لم يُشغَّل المولّد بعدُ: {p}")
    return json.loads(p.read_text(encoding="utf-8"))


# ── 1 · حارسُ القاموس في الخانة ──────────────────────────────────────────
def test_dict_in_cell_is_refused(mod):
    """توزيعٌ في خانةٍ واحدة يخرج `{'k': n}`. سُمّ الحارس بقاموسٍ حقيقيّ."""
    poisoned = mod.Cell("س", "ح", {"EXECUTED": 10}, "عدٌّ")
    with pytest.raises(mod.Blocked) as e:
        poisoned.rendered()
    assert "DICT_IN_CELL" in str(e.value)


def test_the_same_cell_without_a_dict_renders(mod):
    """وأنّ الحارس يسقط على القاموس وحدَه، لا على كلّ قيمة."""
    assert mod.Cell("س", "ح", "10/160", "عدٌّ").rendered() == "`10/160`"


# ── 2 · بصمةُ الحاويات في الوثيقة ────────────────────────────────────────
def test_container_signature_catches_a_python_repr(mod):
    """السمُّ نصُّ بايثون نفسُه الذي طُبع مرّةً في مولّد الطبقات الثلاث."""
    assert mod.CONTAINER.search("| `X` | {'DEFERRED': 10} | عدٌّ |")
    assert mod.CONTAINER.search("['<StageExecutionRecord object at 0x1>']")


def test_container_signature_does_not_catch_a_real_row(mod):
    """ولا يسقط على سطرٍ سليم — وإلا كان الحارس ضجيجًا لا قياسًا."""
    assert not mod.CONTAINER.search("| `STATE·EXECUTED` | `10/160` | عدٌّ |")


def test_the_written_document_carries_no_container_signature(mod):
    doc = OUT / "03_matrix.md"
    if not doc.is_file():
        pytest.skip("لم يُشغَّل المولّد بعدُ")
    assert mod.CONTAINER.findall(doc.read_text(encoding="utf-8")) == []


# ── 3 · حارسُ السبب من الجرد المغلق ──────────────────────────────────────
def test_a_reason_outside_the_closed_inventory_is_caught(mod):
    """سببٌ مخترَعٌ خارج الخمسة — وهو الطريقُ الذي يدخل منه الاختراع."""
    cells = [mod.Cell("س", "ح", None, "", "SOMETHING_I_MADE_UP")]
    assert guard_of(mod, cells)["REASON_IN_INVENTORY"]


def test_a_reason_inside_the_inventory_passes(mod):
    cells = [mod.Cell("س", "ح", None, "", "HUMAN_DECLARED_ONLY")]
    assert guard_of(mod, cells)["REASON_IN_INVENTORY"] == []


def test_not_opened_must_name_a_real_stage(mod):
    """`NOT_OPENED:` يُلحق بها اسمُ مرحلةٍ من الستّ عشرة، لا اسمٌ مختلق."""
    bad = [mod.Cell("س", "ح", None, "", "NOT_OPENED:NO_SUCH_STAGE")]
    good = [mod.Cell("س", "ح", None, "", "NOT_OPENED:HUKM")]
    assert guard_of(mod, bad)["NOT_OPENED_NAMES_A_STAGE"]
    assert guard_of(mod, good)["NOT_OPENED_NAMES_A_STAGE"] == []


# ── 4 · حارسُ الخانة الفارغة ─────────────────────────────────────────────
def test_an_empty_cell_without_a_reason_is_caught(mod):
    """خانةٌ بلا قيمةٍ وبلا سبب: أخطرُ حالٍ، لأنّها تُقرأ صفرًا مقيسًا."""
    assert guard_of(mod, [mod.Cell("س", "ح", "", "مصدر")])["NO_EMPTY_CELL"]
    assert guard_of(mod, [mod.Cell("س", "ح", None, "مصدر")])["NO_EMPTY_CELL"]


def test_a_zero_is_not_an_empty_cell(mod):
    """والصفرُ المقيس قيمةٌ، لا فراغ — وإلا حذف الحارسُ قياسًا صحيحًا."""
    assert guard_of(mod, [mod.Cell("س", "ح", 0, "عدٌّ")])["NO_EMPTY_CELL"] == []


# ── 5 · دفترُ الإقفال ────────────────────────────────────────────────────
def test_the_ledger_check_is_not_a_tautology(manifest):
    """الإقفالُ يُقاس بعدٍّ ثانٍ من الوثيقة، لا بجمعٍ يعيد نفسَه.

    كان المكتوبُ `filled + (total - filled) == total` — وهي صحيحةٌ أبدًا،
    تمرّ ولو ضاع نصفُ الخانات في الطبع. فالعدُّ الثاني هو الحكم.
    """
    r = manifest["recount_from_document"]
    assert r["rows"] == manifest["cells_total"]
    assert r["not_available"] == manifest["cells_not_available"]
    assert r["from_code"] == manifest["cells_from_code"]
    assert manifest["ledger_closes"] is True


def test_a_dropped_row_breaks_the_recount(mod):
    """سمٌّ على العدّ الثاني نفسِه: يُحذف سطرٌ من الوثيقة ويُطالَب بالسقوط.

    ويُستدعى `recount` الحقيقيّ، لا يُعاد حسابُه في الاختبار: فحسابٌ يُكرَّر
    هنا يُثبت الحسابَ لا الحارس. ولذلك أُخرج من جوف `main` ليُسمَّم.
    """
    cells = [mod.Cell("س", f"ح{i}", i, "عدٌّ") for i in range(3)]
    cells.append(mod.Cell("س", "ح3", None, "", "OWNER_DECISION"))
    doc = mod.render(cells, {"title": "ت"})
    assert mod.recount(doc, cells)["closes"] is True

    dropped = "\n".join(ln for ln in doc.splitlines()
                        if not ln.startswith("| `ح1`"))
    poisoned = mod.recount(dropped, cells)
    assert poisoned["closes"] is False
    assert poisoned["rows"] == len(cells) - 1


def test_a_swapped_reason_breaks_the_recount(mod):
    """وسمٌّ ثانٍ: تُطبع خانةٌ مقيسةٌ بوسم «غير متوفرة» فيختلّ المقامان."""
    cells = [mod.Cell("س", "ح0", 7, "عدٌّ"),
             mod.Cell("س", "ح1", None, "", "OWNER_DECISION")]
    doc = mod.render(cells, {"title": "ت"})
    swapped = doc.replace("| `ح0` | `7` |", f"| `ح0` | {mod.NA} · `x` |")
    assert mod.recount(swapped, cells)["closes"] is False


def test_every_not_available_row_carries_a_reason(manifest):
    """لا «غير متوفرة» عاريةً: كلُّ واحدةٍ باسم سببها من الخمسة."""
    naked = [c for c in manifest["cells"] if not c["reason"]
             and (c["value"] is None or c["value"] == "")]
    assert naked == []
    fams = {c["reason"].split(":")[0] for c in manifest["cells"] if c["reason"]}
    assert fams <= {"NOT_OPENED", "NOT_EMITTED_BY_RUNNER",
                    "NOT_CONSTRUCTED_IN_SOURCE", "HUMAN_DECLARED_ONLY",
                    "OWNER_DECISION"}


# ── 6 · حارسُ ما قبل الكتابة ─────────────────────────────────────────────
def test_preflight_blocks_on_a_wrong_pin(mod, monkeypatch):
    """سمٌّ على التثبيت: بصمةٌ غيرُ بصمة المورّد ⟶ BLOCKED قبل أيّ كتابة."""
    monkeypatch.setattr(mod, "PIN", "0" * 40)
    assert mod.preflight()["verdict"] == "BLOCKED"


def test_preflight_passes_on_the_real_pin(mod):
    """وأنّه يمرّ على الحقيقيّة — وإلا كان الحارس مانعًا مطلقًا لا فحصًا."""
    pre = mod.preflight()
    assert pre["pin_matches"] is True
    assert pre["import_ok"] is True
    assert pre["verdict"] == "PASS"


def test_a_blocked_preflight_writes_nothing(tmp_path):
    """والوقوفُ يعني ألّا يُكتب حرف. يُشغَّل المولّد فعلًا ببصمةٍ مسمومة."""
    poisoned = tmp_path / "poisoned.py"
    src = GEN.read_text(encoding="utf-8")
    pin = re.search(r'^PIN = "([0-9a-f]{40})"', src, re.M)
    assert pin, "PIN غيرُ موجودٍ بالشكل المتوقَّع — فالسمُّ لا يُركَّب"
    poisoned.write_text(src.replace(pin.group(1), "0" * 40), encoding="utf-8")
    dest = tmp_path / "out"
    r = subprocess.run(
        [str(VENV), str(poisoned), "--text", str(ROOT / "inspection/case.txt"),
         "--reference", str(ROOT / "inspection/TAAQOL_NAZILA_MATRIX.md"),
         "--out", str(dest)],
        capture_output=True, text=True, cwd=ROOT, check=False)
    assert r.returncode == 2, r.stdout + r.stderr
    assert "BLOCKED_AT_PREFLIGHT" in r.stdout
    assert not dest.exists(), "كُتب مجلَّدٌ بعد الوقوف — والوقوفُ يعني الصمت"


# ── 7 · عدُّ الأقسام: المقيسُ هو الحاكم ──────────────────────────────────
def test_section_count_is_measured_from_the_reference_not_assumed(manifest):
    """الأمرُ قال أربعةَ عشرَ قسمًا، والمرجعُ يحمل سبعةَ عشرَ عنوانًا.

    فالحارسُ لا يفرض الرقمَ المذكور: يعدّ عناوينَ المرجع، ويعدّ ما وُلّد،
    ويُعلن الخلافَ مع ما ذُكر في الأمر. وذلك نصُّ التعليمة: «فإن خالفك
    فالمقيسُ هو الحاكم — وأعلن الخلاف».
    """
    sc = manifest["guards"]["SECTION_COUNT"]
    assert sc["generated"] == sc["reference"]
    assert sc["declared_in_prompt"] == 14
    assert sc["reference"] != sc["declared_in_prompt"]
    assert sc["note"], "خُولف الرقمُ المذكور ولم يُعلَن الخلاف"


def test_no_reference_heading_is_missing_and_none_is_invented(manifest):
    f = manifest["guards"]["FIELD_NAMES_MATCH"]
    assert f["missing_here"] == []
    assert f["extra_here"] == []


# ── 8 · لا سطرَ منقولٌ من المرجع ─────────────────────────────────────────
def test_no_cell_value_is_copied_from_the_reference_document(manifest):
    """«لا تنقل سطرًا من وثيقة المرجع إلى خانةٍ ولو كان صحيحًا».

    فتُقابَل كلُّ قيمةٍ مقيسةٍ طويلةٍ بنصّ المرجع: وجودُها فيه حرفيًّا
    شبهةُ نقل. والقصيرةُ تُستثنى لأنّ التطابقَ فيها لا يدلّ.

    **والمدخلُ يُستثنى، لا باسمه بل باشتقاقه.** سقط هذا الاختبارُ أوّلَ
    مرّةٍ على `INPUT_TEXT` وبصمتِها، وهي ليست منقولةً من المرجع: تُقرأ من
    `case.txt` وتُحسب بـ`hashlib`، وإنّما وردت في المرجع لأنّ المالك وحّد
    أساسَ القياس على جملة الوثيقة. فالاستثناءُ محسوبٌ هنا من الملفّ
    والبصمة — لا قائمةَ أسماءٍ تُعفى، إذ القائمةُ تُوسَّع كلّما سقط الحارس.
    """
    if not REF.is_file():
        pytest.skip("المرجعُ غيرُ موجود")
    assert manifest["guards"]["COPIED_FROM_REFERENCE"] == []


def test_the_copy_guard_catches_a_real_transcription(mod):
    """وسمٌّ على الحارس نفسِه: سطرٌ مأخوذٌ من المرجع يجب أن يُلتقط.

    فحارسٌ لم يُرَ ساقطًا قد يكون استُثني حتى الخلوّ. يُؤخذ سطرٌ طويلٌ من
    المرجع، ويُدسّ خانةً، ويُستدعى `copied_from_reference` الحقيقيّ.
    """
    if not REF.is_file():
        pytest.skip("المرجعُ غيرُ موجود")
    given = CASE.read_text(encoding="utf-8").strip()
    stolen = next(ln.strip() for ln in REF.read_text(encoding="utf-8").splitlines()
                  if len(ln.strip()) > mod.MIN_COPY_LEN and given not in ln)
    cells = [mod.Cell("س", "منقولة", stolen, "المرجع")]
    assert mod.copied_from_reference(cells, REF, given) == ["منقولة"]


def test_the_copy_guard_exempts_the_input_by_derivation_not_by_name(mod):
    """والمدخلُ يُعفى لأنّه يُقرأ من الملفّ ويُحسب، لا لأنّ اسمَه استُثني.

    فتُسمّى الخانةُ اسمًا آخرَ غيرَ `INPUT_TEXT` وتبقى معفاةً، ثمّ يُغيَّر
    المدخلُ فيسقط الإعفاء — والإعفاءُ بالاشتقاق لا بقائمة أسماء.
    """
    if not REF.is_file():
        pytest.skip("المرجعُ غيرُ موجود")
    given = CASE.read_text(encoding="utf-8").strip()
    sha = hashlib.sha256(given.encode()).hexdigest()
    named_otherwise = [mod.Cell("س", "اسمٌ آخرُ تمامًا", given, "الملفّ"),
                       mod.Cell("س", "بصمةٌ باسمٍ آخر", sha, "hashlib")]
    assert mod.copied_from_reference(named_otherwise, REF, given) == []
    assert mod.copied_from_reference(named_otherwise, REF, "نصٌّ آخر") == [
        "اسمٌ آخرُ تمامًا", "بصمةٌ باسمٍ آخر"]


def test_the_generator_never_claims_the_project_is_finished():
    doc = OUT / "03_matrix.md"
    if not doc.is_file():
        pytest.skip("لم يُشغَّل المولّد بعدُ")
    assert "CLAIM_PROJECT_FINISHED = NO" in doc.read_text(encoding="utf-8")


def guard_of(mod, cells):
    """يشغّل الحارسَ نفسَه على خانةٍ مسمومة، بمرجعٍ غيرِ موجودٍ عمدًا."""
    return mod.guard(cells, Path("/nonexistent/reference.md"))
