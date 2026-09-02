"""قاعدة المالك ن٠-ج — لفظ الجلالة ممنوعٌ من كل إجراء.

نصُّ الحكم (2026-09-01):

    لفظ الجلالة يُمنع تصريفه وتحويله إلى مقاطع صوتية ولا أيّ إجراء.
    هو وحده واحد، ليس كمثله شيء.

وهو أختٌ لقاعدة الفواتح في الشكل — سطحٌ يخرج من كل المحاور ويُحفظ كما كُتب —
ويفارقها في أمرين:

* الفواتح تُعرف بالسطح **وموضعِه** (أوّلَ سورة)، ولفظ الجلالة يُعرف بالسطح وحده
  أينما وقع.
* الفواتح تخرج كاملةً، ولفظ الجلالة **تُقشَّر سابقتُه** بحكم المالك.

والفصل يقع **بالجرد لا بالتحليل**: لكل سطحٍ في القائمة سابقتُه وبقيّتُه مكتوبتان
صراحةً. ولو حُسب موضعُ القطع لاقتضى تطبيعَ لفظ الجلالة وتقطيعَه، وذلك عينُ ما
منعه الحكم. فالجردُ هنا ليس تسهيلًا بل **شرطُ صدق «ولا أيّ إجراء»**.

والقائمة مغلقة: ما ليس فيها ليس لفظ الجلالة ولو أشبهه رسمًا. فـ«اللَّهْوِ»
و«اللَّهَبِ» و«يُضْلِلْهُ» و«لَلْهُدَى» تشترك معه في الحروف وليست منه، ولو بُني
الحكم على تشابه الرسم لدخلت أربعتُها.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .constants import canonical_mark_order
from .errors import owner_alert
from .fileio import read_json, require_file

RULE_ID = "N0.J"

DEFAULT_PATH = Path(__file__).resolve().parents[2] / "data" / "lafz_al_jalalah.json"


@dataclass(frozen=True)
class JalalahEntry:
    """سطحٌ من القائمة: سابقتُه المفصولة بالجرد، وبقيّتُه المحفوظة كما كُتبت."""

    surface: str
    prefix: str
    preserved: str
    note: str = ""

    @property
    def has_prefix(self) -> bool:
        return bool(self.prefix)

    @property
    def segments(self) -> list[tuple[str, str]]:
        """(السطح ، الدور) بالترتيب. السابقة إن وُجدت، ثم لفظ الجلالة."""
        out = []
        if self.prefix:
            out.append((self.prefix, "PREFIX"))
        out.append((self.preserved, "LAFZ_AL_JALALAH"))
        return out


class JalalahRegistry:
    """قائمةٌ مغلقة تُحمَّل مرّةً ولا تُعدَّل وقت التشغيل."""

    def __init__(self, entries: dict[str, JalalahEntry], source: Path | None = None):
        self._entries = entries
        self.source = source

    @classmethod
    def load(cls, path: Path | str | None = None) -> JalalahRegistry:
        path = Path(path) if path else DEFAULT_PATH
        require_file(path, what="قائمة لفظ الجلالة",
                     remedy="لا يُستنبط لفظ الجلالة من الرسم في غياب القائمة")
        raw = read_json(path)
        if not isinstance(raw, dict) or "surfaces" not in raw:
            raise owner_alert("قائمة لفظ الجلالة بلا حقل surfaces", المسار=path)

        entries: dict[str, JalalahEntry] = {}
        for item in raw["surfaces"]:
            surface = item["surface"]
            prefix = item.get("prefix", "")
            preserved = item["preserved"]
            # حارسٌ بنيويّ: السابقة + البقيّة يجب أن تعيدا بناء السطح بالضبط.
            # وإلا فالقائمة نفسها تدّعي فصلًا لا يصدق على الرسم.
            if prefix + preserved != surface:
                raise owner_alert(
                    "مدخلةٌ في قائمة لفظ الجلالة لا تُعيد بناء سطحها",
                    السطح=surface, السابقة=prefix, البقيّة=preserved)
            surface = canonical_mark_order(surface)
            prefix = canonical_mark_order(prefix)
            preserved = canonical_mark_order(preserved)
            entries[surface] = JalalahEntry(surface, prefix, preserved,
                                            item.get("note", ""))
        return cls(entries, path)

    def get(self, surface: str) -> JalalahEntry | None:
        """مطابقةٌ تامّة بالسطح المشكول. لا تشابهَ ولا احتواء."""
        return self._entries.get(canonical_mark_order(surface.strip()))

    def __contains__(self, surface: str) -> bool:
        return canonical_mark_order(surface.strip()) in self._entries

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self):
        return iter(self._entries.values())

    @property
    def with_prefix(self) -> list[JalalahEntry]:
        return [e for e in self._entries.values() if e.has_prefix]


_DEFAULT: JalalahRegistry | None = None


def default_registry() -> JalalahRegistry:
    global _DEFAULT
    if _DEFAULT is None:
        _DEFAULT = JalalahRegistry.load()
    return _DEFAULT
