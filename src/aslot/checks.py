"""حزمة الفحوص: الفحص الذاتي والسمّ وعيب المدخل — بثلاث دلالاتٍ متمايزة.

كانت المحاور الخمسة تكرّر الدالّة نفسها (``add(name, ok, detail)``) وتخلط
ثلاثة أشياء مختلفة تحت راية «اختبار»:

* **الفحص الذاتي** يقيس التزام المحرّك بقاعدةٍ مسمّاة. إخفاقُه عيبُ كود.
* **السمّ** مدخلٌ *يجب أن يُرفض*؛ نجاحُه أن يُرفض فعلًا. إخفاقُه ثغرةُ قبول.
* **عيب المدخل** واقعةٌ في البيانات لا في المحرّك. حكمُه DEFER، ولا يُسقط جولة.

وخلطُ الثالث بالأوّلين هو ما جعل جولةَ المحور صفرًا تشير إلى خطأٍ ليس فيها.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

SELF_CHECK = "SELF_CHECK"
POISON = "POISON"
INPUT_DEFECT = "INPUT_DEFECT"


@dataclass
class Check:
    name: str
    passed: bool
    detail: str = ""
    kind: str = SELF_CHECK

    @property
    def label(self) -> str:
        return "PASS" if self.passed else "FAIL"


@dataclass
class Defect:
    """عيبُ مدخلٍ مقيس: يُسجَّل ولا يُعالَج ولا يُرقَّع."""

    name: str
    count: int
    note: str = ""
    samples: list = field(default_factory=list)

    @property
    def label(self) -> str:
        return "DEFER" if self.count else "CLEAR"


class CheckSuite:
    """يجمع فحوصَ محورٍ واحد. يُبنى مرّةً ويُقرأ من التقرير ومن pytest معًا."""

    def __init__(self, axis: str):
        self.axis = axis
        self.checks: list[Check] = []
        self.poisons: list[Check] = []
        self.defects: list[Defect] = []

    # -- التسجيل --------------------------------------------------------
    def check(self, name: str, passed: object, detail: object = "") -> None:
        self.checks.append(Check(name, bool(passed), str(detail), SELF_CHECK))

    def poison(self, name: str, rejected: object, detail: object = "") -> None:
        """السمّ ينجح حين **يُرفض** المدخل. مرّر نتيجة الرفض لا نتيجة القبول."""
        self.poisons.append(Check(name, bool(rejected), str(detail), POISON))

    def defect(self, name: str, count: int, note: str = "", samples=()) -> None:
        self.defects.append(Defect(name, int(count), note, list(samples)[:8]))

    # -- القراءة --------------------------------------------------------
    @property
    def all_checks(self) -> list[Check]:
        return self.checks + self.poisons

    @property
    def failures(self) -> list[Check]:
        return [c for c in self.all_checks if not c.passed]

    @property
    def ok(self) -> bool:
        return not self.failures

    def score(self, kind: str = SELF_CHECK) -> tuple[int, int]:
        items = self.checks if kind == SELF_CHECK else self.poisons
        return sum(1 for c in items if c.passed), len(items)

    def as_dict(self) -> dict:
        return {
            "self_checks": {c.name: c.passed for c in self.checks},
            "poisons": {c.name: c.passed for c in self.poisons},
            "input_defects": {d.name: d.count for d in self.defects},
        }


def rejects(call: Callable[[], object]) -> tuple[bool, str]:
    """يشغّل استدعاءً يُنتظر منه الرفض، ويعيد (رُفض؟ ، السبب).

    يوحّد نمط ``try / except SystemExit`` الذي كان مكرّرًا في كل سمّ.
    """
    try:
        call()
    except SystemExit as exc:
        return True, str(exc).splitlines()[1].strip() if "\n" in str(exc) else "رُفض"
    except Exception as exc:
        return True, f"{type(exc).__name__}: {exc}"
    return False, "قُبل وهو يجب أن يُرفض"
