"""اختبارات وحدةٍ للنواة المشتركة — ما لا تغطّيه سويتات المحاور.

هذه الاختبارات تحرس **العقد** لا السلوك اللغويّ: صيغةَ الإنذار الدستوري،
ورفضَ الأرقام غير ASCII، ودلالةَ ``ratified``، وإغلاقَ قائمة الأحكام.
"""

from __future__ import annotations

import pytest

from aslot.checks import CheckSuite, rejects
from aslot.errors import OwnerAlert, owner_alert
from aslot.fileio import strict_int
from aslot.policy import OWNER_DECISION_REQUIRED
from aslot.reporting import Report
from aslot.verdicts import ACCEPT, BLOCK, DEFER, Ruling, decide


class TestOwnerAlert:
    def test_carries_the_three_line_contract(self):
        alert = owner_alert("سببٌ ما", الحقل="X")
        text = str(alert)
        assert text.startswith("STOP / OWNER_ALERT / NO_INFERENCE")
        assert "السبب = سببٌ ما" in text
        assert "الحكم = BLOCK" in text

    def test_is_a_system_exit_so_it_stops_the_run(self):
        assert issubclass(OwnerAlert, SystemExit)


class TestStrictInt:
    @pytest.mark.parametrize("raw", ["٢", "٢٣", "", "1 2", "12a", "١٠"])
    def test_rejects_anything_but_ascii_digits(self, raw):
        rejected, _ = rejects(lambda: strict_int(raw, field="X", row_no=1))
        assert rejected, f"قُبل {raw!r} وهو يجب أن يُرفض"

    @pytest.mark.parametrize("raw,expected", [("0", 0), ("42", 42), ("-7", -7)])
    def test_accepts_ascii_digits(self, raw, expected):
        assert strict_int(raw, field="X", row_no=1) == expected


class TestVerdicts:
    def test_closed_list(self):
        with pytest.raises(ValueError):
            Ruling("MAYBE")

    def test_accept_needs_all_three(self):
        assert decide(True, True, False).verdict == ACCEPT
        assert decide(False, True, False).verdict == BLOCK
        assert decide(True, False, False).verdict == BLOCK
        assert decide(True, True, True).verdict == BLOCK

    def test_unresolved_defers_regardless(self):
        """DEFER يسبق كلَّ شيء: الجهل لا يتحوّل إلى دعوى مانع."""
        assert decide(False, False, True, unresolved=True).verdict == DEFER


class TestPolicy:
    def test_unknown_class_is_a_constitutional_gap(self, policy):
        with pytest.raises(SystemExit):
            policy["U_DOES_NOT_EXIST"]

    def test_unratified_entries_are_listed(self, policy):
        assert policy.unratified, "يُتوقَّع وجود أصنافٍ تنتظر حكمًا"

    def test_stops_only_when_treatment_says_so(self, policy):
        for entry in policy:
            assert entry.stops == (entry.treatment == OWNER_DECISION_REQUIRED)


class TestCheckSuite:
    def test_separates_the_three_kinds(self):
        suite = CheckSuite("x")
        suite.check("C1", True)
        suite.poison("P1", True)
        suite.defect("D1", 5, "عيبُ مدخل")
        assert suite.score() == (1, 1)
        assert suite.score("POISON") == (1, 1)
        # عيب المدخل لا يُسقط الجولة
        assert suite.ok

    def test_a_failing_check_marks_the_suite(self):
        suite = CheckSuite("x")
        suite.check("C1", False, "لماذا")
        assert not suite.ok
        assert suite.failures[0].detail == "لماذا"


class TestReport:
    def test_alignment_is_computed_not_hardcoded(self):
        text = Report("t").kv({"A": 1, "LONGER_KEY": 2}).render()
        assert "A          = 1" in text
        assert "LONGER_KEY = 2" in text

    def test_counts_use_thousands_separator(self):
        assert "1,234" in Report("t").counts({"K": 1234}).render()
