"""الوقوف الدستوري: ``STOP / OWNER_ALERT / NO_INFERENCE``.

كان هذا النصّ مكرّرًا حرفيًّا في خمسة ملفات، وكلُّ نسخةٍ تصوغه بطريقتها.
وتوحيدُه ليس تجميلًا: صيغةُ الإنذار **جزءٌ من العقد** مع المالك، فينبغي أن
تكون واحدةً لا تتفرّع.

القاعدة التي يمثّلها هذا الملف — عند ثغرةٍ دستورية:
    لا تُنشئ قاعدة ، ولا تُضِف استثناءً ، ولا تختر بين بدائل نيابةً عن المالك.
"""

from __future__ import annotations


class OwnerAlert(SystemExit):
    """وقوفٌ يستدعي حكم المالك. يرث SystemExit ليقف التنفيذ برمز خروجٍ غير صفر."""

    def __init__(self, cause: str, ruling: str = "BLOCK", **detail: object):
        self.cause = cause
        self.ruling = ruling
        self.detail = detail
        lines = ["STOP / OWNER_ALERT / NO_INFERENCE", f"  السبب = {cause}"]
        for key, value in detail.items():
            lines.append(f"  {key} = {value}")
        lines.append(f"  الحكم = {ruling}")
        super().__init__("\n".join(lines))


def owner_alert(cause: str, ruling: str = "BLOCK", **detail: object) -> OwnerAlert:
    """يبني الإنذار دون رفعه — ليقرأ موضعُ الاستدعاء ``raise owner_alert(...)``."""
    return OwnerAlert(cause, ruling, **detail)
