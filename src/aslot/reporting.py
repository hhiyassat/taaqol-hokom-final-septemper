"""بنّاء التقرير — كتلُ ``key=value`` وجداولٌ وقوائم فحص.

كانت كل وحدةٍ تبني تقريرها بـ ``L.append(f"...")`` ومحاذاةٍ يدوية بأرقامٍ
سحرية (``{k:36s} = {v:>7,}``). فاختلفت العروض بين المحاور بلا سبب، وصار
تعديلُ شكل التقرير خمسةَ تعديلات.

هنا صياغةٌ واحدة: المحاذاة تُحسب من أطول مفتاح، والأرقام تُنسَّق بفاصلة
الآلاف دائمًا، ولا يكتب أيُّ محورٍ محرفَ تنسيقٍ بيده.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence

from .checks import CheckSuite

RULE = "=" * 72


class Report:
    def __init__(self, title: str):
        self._lines: list[str] = [RULE, title, RULE, ""]

    # -- لبنات ----------------------------------------------------------
    def text(self, *lines: str) -> Report:
        self._lines.extend(lines)
        return self

    def blank(self) -> Report:
        self._lines.append("")
        return self

    def heading(self, title: str, level: int = 2) -> Report:
        self._lines.extend(["", f"{'#' * level} {title}"])
        return self

    def kv(self, pairs: Mapping[str, object] | Sequence[tuple[str, object]],
           *, fence: bool = True) -> Report:
        """كتلة ``key = value`` بمحاذاةٍ محسوبة لا مقدَّرة."""
        items = list(pairs.items() if isinstance(pairs, Mapping) else pairs)
        if not items:
            return self
        width = max(len(str(k)) for k, _ in items)
        if fence:
            self._lines.append("```")
        for key, value in items:
            self._lines.append(f"{key!s:<{width}} = {_fmt(value)}")
        if fence:
            self._lines.append("```")
        return self

    def counts(self, pairs: Mapping[str, int] | Sequence[tuple[str, int]],
               *, fence: bool = True, note: Mapping[str, str] | None = None
               ) -> Report:
        """أعدادٌ محاذاةً إلى اليمين — للتوزيعات والهستوغرامات."""
        items = list(pairs.items() if isinstance(pairs, Mapping) else pairs)
        if not items:
            return self
        kw = max(len(str(k)) for k, _ in items)
        vw = max(len(f"{int(v):,}") for _, v in items)
        if fence:
            self._lines.append("```")
        for key, value in items:
            suffix = (note or {}).get(str(key), "")
            self._lines.append(
                f"{key!s:<{kw}} = {int(value):>{vw},}"
                + (f"   {suffix}" if suffix else ""))
        if fence:
            self._lines.append("```")
        return self

    def checks(self, suite: CheckSuite) -> Report:
        """يعرض الأصناف الثلاثة بدلالاتها المتمايزة لا كقائمةٍ واحدة."""
        for items, title in (
            (suite.checks, "الفحوص الذاتية (التزام المحرّك)"),
            (suite.poisons, "السموم (مدخلاتٌ يجب أن تُرفض)"),
        ):
            if not items:
                continue
            passed = sum(1 for c in items if c.passed)
            self.heading(f"{title}: {passed}/{len(items)}")
            width = max(len(c.name) for c in items)
            for c in items:
                self._lines.append(f"  [{c.label}] {c.name:<{width}}  {c.detail}")
        if suite.defects:
            self.heading("عيوب المدخل المقيسة — حالة البيانات لا حالة المحرّك")
            self._lines.append(
                "  الحكم في جميعها DEFER: تُسجَّل ولا تُعالَج، ولا يُخترع رقمٌ ولا تُدرَج كلمة.")
            width = max(len(d.name) for d in suite.defects)
            for d in suite.defects:
                self._lines.append(
                    f"  [{d.label}] {d.name:<{width}} = {d.count:>6,}   {d.note}")
                if d.samples:
                    self._lines.append(f"          نماذج: {d.samples}")
        return self

    def proves(self, proves: Iterable[str], does_not_prove: Iterable[str],
               algebra: Iterable[str] = ()) -> Report:
        """ما يثبته المحور وما لا يثبته — قسمٌ إلزاميّ في كل تقرير.

        وجودُه شرطٌ لا زينة: تقريرٌ يذكر ما أُنجز ولا يذكر ما لم يُنجز
        يُقرأ دعوى أوسعَ من الحجّة.
        """
        self.heading("ما يثبته هذا المحور وما لا يثبته")
        for line in proves:
            self._lines.append(f"  يثبت    : {line}")
        for line in does_not_prove:
            self._lines.append(f"  لا يثبت : {line}")
        for line in algebra:
            self._lines.append(f"  جبر     : {line}")
        return self

    def render(self) -> str:
        return "\n".join(self._lines)

    def __str__(self) -> str:  # pragma: no cover - راحةٌ عند الطباعة
        return self.render()


def _fmt(value: object) -> str:
    if isinstance(value, bool):
        return "YES" if value else "NO"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)
