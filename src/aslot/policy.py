"""سياسة المالك للأصناف التي لا سند نصّيّ لها.

العقد الذي يمثّله هذا الملف:

* لكل صنفٍ **معالجة** (``treatment``) و**تصديق** (``ratified``).
* ``ratified = false`` معناه: المعالجة مؤقّتة تُمضي القياس، وحالةُ الكلمة
  تُرفع إلى ``NORMALIZED_OWNER_DECISION_REQUIRED``. أي أن المحرّك **يعمل
  ويعترف** بدل أن يقف أو يدّعي.
* ``treatment = OWNER_DECISION_REQUIRED`` معناه: لا سطحَ يُنتج أصلًا، تقف الكلمة.
* صنفٌ لا سياسة له = ثغرةٌ دستورية ⇒ ``OwnerAlert``، لا افتراضَ ولا تخطٍّ صامت.

فالسياسة **بياناتٌ لا كود**: تصديقُ حكمٍ تغييرُ ``false`` إلى ``true`` في JSON،
لا تعديلُ سطرٍ في محرّك.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .errors import owner_alert
from .fileio import read_json, require_file

OWNER_DECISION_REQUIRED = "OWNER_DECISION_REQUIRED"

DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[2] / "data" / "axis_1_owner_policy.json"
)


@dataclass(frozen=True)
class PolicyEntry:
    name: str
    treatment: str
    ratified: bool
    rule_text_source: str = ""
    note: str = ""

    @property
    def stops(self) -> bool:
        return self.treatment == OWNER_DECISION_REQUIRED


class OwnerPolicy:
    """سجلّ سياسةٍ محمَّل. لا يُعدَّل وقت التشغيل بحال."""

    def __init__(self, entries: dict[str, PolicyEntry], source: Path | None = None):
        self._entries = entries
        self.source = source

    @classmethod
    def load(cls, path: Path | str | None = None) -> OwnerPolicy:
        path = Path(path) if path else DEFAULT_POLICY_PATH
        require_file(path, what="ملف سياسة المالك",
                     remedy="لا يُفترض حكمٌ في غياب الملف")
        raw = read_json(path)
        if not isinstance(raw, dict):
            raise owner_alert("ملف السياسة ليس كائنًا", المسار=path)
        entries = {
            key: PolicyEntry(
                name=key,
                treatment=value["treatment"],
                ratified=bool(value.get("ratified", False)),
                rule_text_source=value.get("rule_text_source", ""),
                note=value.get("note", ""),
            )
            for key, value in raw.items()
            if not key.startswith("_") and isinstance(value, dict)
        }
        return cls(entries, path)

    def __getitem__(self, name: str) -> PolicyEntry:
        try:
            return self._entries[name]
        except KeyError:
            raise owner_alert("صنفٌ لا سياسة له", الصنف=name) from None

    def __contains__(self, name: str) -> bool:
        return name in self._entries

    def __iter__(self):
        return iter(self._entries.values())

    def __len__(self) -> int:
        return len(self._entries)

    @property
    def unratified(self) -> list[PolicyEntry]:
        return [e for e in self._entries.values() if not e.ratified]
