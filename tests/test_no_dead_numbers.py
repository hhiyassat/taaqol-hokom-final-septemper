"""شرحُ المولِّد لا يحمل عددًا يقيسه هو — وإلا مات صامتًا.

**الواقعة.** بقي في شرح ``run_taaqol_nazila.py`` عددان من قياسٍ سابق بعد أن
تغيّر القياس، فقال الشرحُ «سبعةُ مساراتٍ بثقةٍ ٠٫٥١–٠٫٩٦» والملفُّ يخرج غيرَ
ذلك. ورقمٌ في نثرٍ لا يُعاد حسابُه لا يُخطئ مرّةً ثمّ يُصحَّح: يبقى خطأً
كلَّما تغيّر القياس، ولا يشتكي منه أحد.

**ولمَ لا يكفي منعُ الأرقام.** العددُ الميّتُ الأوّل كان **كلمةً** لا رقمًا
(«سبعة»)، وحدُّه الثاني بأرقامٍ هنديّةٍ عشريّة. ففحصُ الأرقام وحدَه كان
سيمرّ على ما وقع فعلًا. فيُمنع الاثنان: رقمٌ خارج العلامات المائلة، وكلمةُ
عددٍ من قائمةٍ مغلقة.

**وحدُّ القاعدة مُعلَن.** ما بين علامتين مائلتين اسمٌ لا عدد
(``02_path_classifier.json`` ، ``P6_...``) فيُستثنى بالبنية لا بالاستثناء.
والقاعدةُ على هذين الملفّين وحدَهما: هما اللذان يكتبان أعدادَهما في JSON،
فالنثرُ فيهما يصف والملفُّ يعدّ. وسائرُ الوحدات تحمل أعدادًا مقيسةً في
شروحها عن قصد، وهي شواهدُ محرّكٍ لا مخرجاتُ تشغيل.
"""
from __future__ import annotations

import ast
import importlib.util
import re
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]

#: الملفّاتُ التي تكتب أعدادَها في JSON، فلا تقولها في نثرها.
GENERATORS = ("scripts/run_taaqol_nazila.py", "scripts/probe_path_classifier.py")

#: كلماتُ العدد من **الثلاثة فصاعدًا** — جردٌ مغلقٌ بصيغه التامّة.
#:
#: وحدُّه مقصود: الواحدُ والاثنان في العربية مبنيّان في الصيغة نفسِها
#: (المثنّى، والإفراد)، فمنعُهما منعُ نحوٍ لا منعُ عدّ — و«المقامان» ليست
#: دعوى قياس. أمّا «سبعةُ مسارات» فعدٌّ صريحٌ يموت بتغيّر القياس، وهو
#: الواقعةُ المسجَّلة. فالقاعدةُ تُسنّ على الصنف الذي وقع لا على ما لم يقع.
NUMBER_WORDS = frozenset({
    "ثلاث", "ثلاثة", "أربع", "أربعة", "خمس", "خمسة", "ست", "ستة", "ستّ",
    "ستّة", "سبع", "سبعة", "ثمان", "ثمانية", "تسع", "تسعة", "عشر", "عشرة",
    "عشرون", "عشرين", "مئة", "مائة", "ألف",
})

#: بادئاتٌ تُقشَّر قبل المطابقة — فالكلمةُ تُطابَق كلمةً لا سلسلةَ حروف.
#: ومطابقةُ السلاسل كانت تلتقط «ست» في «المستودع» و«اثن» في «الاثنان»،
#: وهو إخفاقٌ لعلّةٍ خاطئة: القاعدةُ تشكو من نصٍّ سليم.
PREFIXES = ("و", "ف", "ب", "ك", "ل", "ال")
MARKS = re.compile(r"[\u064B-\u0652\u0670]")
NON_LETTER = re.compile(r"[^\u0621-\u064A]+")

#: ما بين علامتين مائلتين اسمٌ لا عدد.
CODE_SPAN = re.compile(r"``[^`]*``|`[^`]*`")
DIGIT = re.compile(r"[0-9٠-٩]")


def prose_of(path: Path) -> str:
    doc = ast.get_docstring(ast.parse(path.read_text(encoding="utf-8")))
    return CODE_SPAN.sub(" ", doc or "")


def number_words_in(prose: str) -> list[str]:
    """يطابق كلمةً بكلمة بعد تجريد العلامات وقشر البادئات."""
    found = []
    for raw in NON_LETTER.split(MARKS.sub("", prose)):
        word = raw
        changed = True
        while changed and word:
            changed = False
            for pre in PREFIXES:
                if word.startswith(pre) and len(word) > len(pre) + 1:
                    word, changed = word[len(pre):], True
                    break
        if word in NUMBER_WORDS:
            found.append(word)
    return sorted(set(found))


@pytest.mark.parametrize("rel", GENERATORS)
def test_generator_prose_states_no_measured_number(rel: str) -> None:
    prose = prose_of(ROOT / rel)
    digits = sorted(set(DIGIT.findall(prose)))
    words = number_words_in(prose)
    assert not digits and not words, (
        f"{rel}: عددٌ في الشرح — أرقام {digits} · كلمات {words}. "
        f"الأعدادُ تُقرأ من JSON ولا تُكتب في النثر.")


def test_the_rule_would_have_caught_the_recorded_failure() -> None:
    """السمُّ: النصُّ الذي مرّ فعلًا يجب أن يسقط بهذه القاعدة.

    وقاعدةٌ لا تُختبر بالواقعة التي وُضعت لها قد تمرّ لعلّةٍ خاطئة.
    """
    dead = "سبعةُ مساراتٍ بثقةٍ ٠٫٥١–٠٫٩٦"
    cleaned = CODE_SPAN.sub(" ", dead)
    assert DIGIT.findall(cleaned), "الحدُّ الرقميُّ كان سيلتقطها"
    assert number_words_in(cleaned) == ["سبعة"], "وحدُّ الكلمات كذلك"

    # ولا تشكو من نثرٍ سليم: أسماءٌ فيها حروفُ عددٍ، ومثنًّى نحويّ.
    innocent = "المستودعُ والاثنان في المقامين، ويستورد `02_run.json`"
    assert not number_words_in(CODE_SPAN.sub(" ", innocent))


# ── سمُّ الصفر الميّت في المخرَج ────────────────────────────────────────────
#
# **نقدٌ مقبولٌ وقع على الصياغة الأولى.** كان هذان فحصين على **نصّ** الملفّ:
# يشترطان ورودَ الاسم ويمنعان `return {}`. وحارسٌ نصّيٌّ يمرّ لو كُتب
# `CORPUS_ABSENT` في تعليقٍ ولم يُرفع — فيُثبت وجودَ حرفٍ لا وقوعَ فعل.
# والدليلُ الحقيقيّ إخفاءُ الملفّ وتشغيلُ الدالّة، وقد كان يدويًّا خارج
# السويت. فنُقل إليها.
#
# **وحدُّ التشغيل مُعلَن**: `main()` في المِسبار يستورد تعقُّل، وبيئتُه غيرُ
# بيئة أسلوط. أمّا `corpus_forms` و`aslot_classes_for` فلا تستوردان منه
# شيئًا، فتُستدعيان هنا مباشرةً — والحارسان فيهما لا في `main`.
PROBE = ROOT / "scripts/probe_path_classifier.py"


def load_probe():
    spec = importlib.util.spec_from_file_location("_probe", PROBE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_corpus_absent_raises_instead_of_returning_empty(tmp_path) -> None:
    """يُخفى المصحفُ فعلًا، ويُشترط الوقوف — لا وجودُ الاسم في النصّ."""
    probe = load_probe()
    probe.CORPUS = tmp_path / "لا-وجود-له.csv"
    with pytest.raises(SystemExit) as err:
        probe.corpus_forms(["أن"])
    assert "CORPUS_ABSENT" in str(err.value)


def test_axis1_absent_raises_when_there_is_something_to_classify(tmp_path) -> None:
    """وغيابُ مخرج المحور الأوّل يقف **حين توجد صورٌ تنتظر صنفَها** فقط.

    فالوقوفُ بلا حاجةٍ تعطيلٌ، والمضيُّ مع الحاجة صفرٌ ميّت. والشرطُ هو
    الفرق.
    """
    probe = load_probe()
    probe.AXIS1 = tmp_path / "لا-وجود-له.csv"
    divergent = [{"bare": "ولا", "corpus_forms": {"ولا": {}, "وَلَا": {}}}]
    with pytest.raises(SystemExit) as err:
        probe.aslot_classes_for(divergent)
    assert "AXIS1_REPORT_ABSENT" in str(err.value)
    # ولا شيءَ ينتظر ⟵ لا وقوف.
    assert probe.aslot_classes_for([]) == {}


# ── سمُّ الحاوية المُقحَمة موضعَ نصّ ────────────────────────────────────────
#
# **واقعةٌ في مولّدٍ آخر، والصنفُ واحد.** كُتب `f"<tbody>{rows}</tbody>"`
# و`rows` قائمة، فطُبع تمثيلُها البايثونيّ داخل الجدول: أقواسٌ وفواصلُ
# وعلاماتُ اقتباس. والصفحةُ تبقى HTML صالحًا، والختمُ أسفلَها **صحيحٌ
# مقيس** — فالحسابُ سليم والعرضُ مكسور. ومن قرأ الختمَ لم يقرأ الجدول،
# ومن قرأ الجدولَ لم يفهمه.
#
# فيُفحص كلُّ HTML أولّده: لا توقيعَ لحاويةٍ بايثونيّة في مخرَج.
CONTAINER_SIGNATURE = re.compile(r"""\[['"]<|['"], ['"]<|<[a-z]+>\[['"]""")


@pytest.mark.parametrize(
    "rel", sorted(p.name for p in (ROOT / "inspection").glob("*.html")))
def test_rendered_html_has_no_python_container_repr(rel: str) -> None:
    page = (ROOT / "inspection" / rel).read_text(encoding="utf-8")
    hits = CONTAINER_SIGNATURE.findall(page)
    assert not hits, (
        f"{rel}: حاويةٌ بايثونيّة أُقحمت موضعَ نصّ — {hits[:2]}. "
        f'الصوابُ "".join(...) لا الحاوية نفسُها.')


def test_the_container_rule_catches_the_recorded_failure() -> None:
    """السمّ: المخرَجُ المكسورُ الذي وقع فعلًا يجب أن يسقط بهذه القاعدة."""
    broken = '<table><tbody>[\'<tr><td>1</td></tr>\', \'<tr><td>2</td></tr>\']</tbody>'
    assert CONTAINER_SIGNATURE.findall(broken)
    sound = '<table><tbody><tr><td>1</td></tr><tr><td>2</td></tr></tbody>'
    assert not CONTAINER_SIGNATURE.findall(sound)
