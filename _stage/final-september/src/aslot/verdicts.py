"""الأحكام الثلاثة ومعادلات الجبر — قائمة مغلقة يشترك فيها كل المحاور.

    ACCEPT = CAUSE_PRESENT AND ALL_CONDITIONS_SATISFIED AND NO_PREVENTER_PRESENT
    DEFER  = أيُّ واقعةٍ غير محسومة
    BLOCK  = غياب السبب ، أو سقوط شرط ، أو حضور مانع

والفرق بين DEFER وBLOCK ليس في الشدّة بل في **نوع المعرفة**:
BLOCK دعوى بأن المانع قائم ، وDEFER اعترافٌ بأن الحجّة ناقصة.
وخلطُهما يحوّل الجهلَ إلى حكم.
"""

from __future__ import annotations

from dataclasses import dataclass

ACCEPT = "ACCEPT"
DEFER = "DEFER"
BLOCK = "BLOCK"

VERDICTS = (ACCEPT, DEFER, BLOCK)


@dataclass(frozen=True)
class Ruling:
    """حكمٌ واحد بسببه المسمّى. لا حكمَ بلا اسمٍ لسببه."""

    verdict: str
    reason: str = ""

    def __post_init__(self) -> None:
        if self.verdict not in VERDICTS:
            raise ValueError(f"حكمٌ خارج القائمة المغلقة: {self.verdict!r}")


def decide(cause_present: bool, conditions_satisfied: bool,
           preventer_present: bool, *, unresolved: bool = False,
           reason: str = "") -> Ruling:
    """المبدأ الحاكم مكتوبًا مرّةً واحدة بدل أن يُعاد بناؤه في كل محور."""
    if unresolved:
        return Ruling(DEFER, reason or "UNRESOLVED")
    if not cause_present:
        return Ruling(BLOCK, reason or "CAUSE_ABSENT")
    if not conditions_satisfied:
        return Ruling(BLOCK, reason or "CONDITION_FAILED")
    if preventer_present:
        return Ruling(BLOCK, reason or "PREVENTER_PRESENT")
    return Ruling(ACCEPT, reason)
