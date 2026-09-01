"""هيكل تشغيل المحور — ``main()`` واحدة بدل خمس.

كانت كل وحدةٍ تكرّر: بناء argparse ، والتحقّق من وجود المدخل ، وتشغيل
الفحوص ، وبناء التقرير ، وكتابة ``*_REPORT.txt`` و``*_MEASURES.json`` ،
واشتقاق رمز الخروج. خمسُ نسخٍ من الترتيب نفسه، وأيُّ تحسينٍ فيه خمسةُ تعديلات.

الآن يعرّف المحورُ ما يخصّه وحده — ``arguments`` و``execute`` و``report`` —
ويتولّى ``AxisRunner`` ما هو مشترك.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from .checks import CheckSuite
from .fileio import write_json, write_text
from .reporting import Report


class Axis:
    """عقد المحور. يرثه كل محورٍ ويملأ الثلاثة المطلوبة منه."""

    number: int = -1
    slug: str = ""
    title: str = ""
    module: str = ""
    default_output: str = ""

    # -- ما يعرّفه كل محور ------------------------------------------------
    def arguments(self, parser: argparse.ArgumentParser) -> None:
        """يضيف وسائط هذا المحور. المشتركة مضافةٌ سلفًا."""

    def execute(self, args: argparse.Namespace, out_dir: Path
                ) -> tuple[dict, CheckSuite]:
        """ينفّذ المحور ويعيد (القياسات ، حزمة الفحوص)."""
        raise NotImplementedError

    def report(self, measures: dict, suite: CheckSuite) -> Report:
        raise NotImplementedError

    # -- أسماء المخرجات ---------------------------------------------------
    @property
    def report_name(self) -> str:
        return f"AXIS_{self.number}_REPORT.txt"

    @property
    def measures_name(self) -> str:
        return f"AXIS_{self.number}_MEASURES.json"


class AxisRunner:
    def __init__(self, axis: Axis):
        self.axis = axis

    def parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            prog=f"aslot {self.axis.slug}", description=self.axis.title)
        parser.add_argument("--output-dir", default=self.axis.default_output,
                            help="مجلد مخرجات هذه الجولة")
        parser.add_argument("--quiet", action="store_true",
                            help="لا تطبع التقرير على الشاشة")
        self.axis.arguments(parser)
        return parser

    def run(self, argv: list[str] | None = None) -> int:
        args = self.parser().parse_args(argv)
        out_dir = Path(args.output_dir)
        out_dir.mkdir(parents=True, exist_ok=True)

        measures, suite = self.axis.execute(args, out_dir)
        measures = {"module": self.axis.module, "axis": self.axis.number,
                    **measures, **suite.as_dict()}

        report = self.axis.report(measures, suite).checks(suite).render()
        write_text(out_dir / self.axis.report_name, report)
        write_json(out_dir / self.axis.measures_name, measures)
        if not args.quiet:
            print(report)

        # رمز الخروج يعكس **التزام المحرّك** وحده.
        # عيوب المدخل حكمها DEFER ولا تُسقط الجولة (انظر checks.py).
        return 1 if suite.failures else 0
