"""مرساةُ الأثر — T-3، ولا تعتمد على شيء.

الفصلُ عن `taaqol.py` مقصود: المرساةُ **حسابٌ خالص** من الموضع والمحور، ولا
تحتاج حاملًا ولا مستودعًا. ولو بُنيت داخل جسر تعقُّل لصار كلُّ محورٍ في
السلسلة يستورد المستودعَ ليكتب رقمًا يعرفه بنفسه — وذلك اعتمادٌ بلا علّة،
ويجعل غيابَ المستودع يُسقط محاورَ لا شأن لها به.

    المحور صفر ──► aslot/axis0/1:1:1
    المحور الأول ──► aslot/axis1/1:1:1  أبوه  aslot/axis0/1:1:1
    ...

والشرطُ الذي تحمله: أن تكون **مُعادَ البناء**. فلا وقتَ فيها ولا عدّاد ولا
عشوائيّ، والصفُّ نفسُه على جهازٍ آخر يعطي المرساةَ نفسَها. وذلك ما يجعلها
أثرًا يُتحقَّق منه لا رقمًا يُطبع (docs/123 — الحالةُ إسقاط).
"""

from __future__ import annotations

ANCHOR_PREFIX = "aslot"


def anchor(axis: int, sura: int, verse: int, word: int, segment: int = 0) -> str:
    """مرساةُ أثرٍ حتميّة لصفٍّ واحد."""
    tail = f"{sura}:{verse}:{word}" + (f":{segment}" if segment else "")
    return f"{ANCHOR_PREFIX}/axis{axis}/{tail}"


def parent_anchor(axis: int, sura: int, verse: int, word: int,
                  segment: int = 0) -> str:
    """مرساةُ الصفّ في المحور السابق — بها تتّصل السلسلة ٠→١→٢→٣→٤.

    والمحور صفر جذرُ السلسلة، فمرساتُه أبٌ لنفسه ليبقى الحقلُ مملوءًا دائمًا:
    حقلٌ فارغ يعني `TRACE_MISSING` عند تعقُّل، وذلك حكمٌ على الصفّ لا وصفٌ
    لجذر السلسلة.
    """
    return anchor(max(axis - 1, 0), sura, verse, word, segment)


__all__ = ["ANCHOR_PREFIX", "anchor", "parent_anchor"]
