"""اختبارات pytest **مولَّدةٌ من نفس السويتات** التي يعرضها التقرير.

القاعدة التي تحكم هذا الملف: لا نسخةَ ثانية من المنطق. الفحصُ الذي يُطبع في
``AXIS_n_REPORT.txt`` هو نفسه الذي يُشغَّل هنا — فلا يمكن أن ينجح أحدهما
ويسكت الآخر، ولا أن يُنسى تحديثُ أحدهما عند تعديل قاعدة.
"""

from __future__ import annotations

import pytest

from aslot.axes import axis1_normalization, axis2_registry, axis3_syllabification, axis4_peeling


def _ids(checks):
    return [c.name for c in checks]


# ---------------------------------------------------------------------------
# سويتات لا تحتاج بيانات — تُشغَّل دائمًا
# ---------------------------------------------------------------------------

AXIS3_SUITE = axis3_syllabification.build_suite()


@pytest.mark.parametrize("check", AXIS3_SUITE.all_checks, ids=_ids(AXIS3_SUITE.all_checks))
def test_axis3(check):
    assert check.passed, f"{check.name}: {check.detail}"


# ---------------------------------------------------------------------------
# سويتات تحتاج السياسة
# ---------------------------------------------------------------------------

def _axis1_suite(policy):
    return axis1_normalization.build_suite(policy)


def test_axis1_suite_all_pass(policy):
    suite = _axis1_suite(policy)
    assert suite.ok, [f"{c.name}: {c.detail}" for c in suite.failures]


def test_axis1_suite_is_not_empty(policy):
    suite = _axis1_suite(policy)
    assert suite.score()[1] >= 10
    assert suite.score("POISON")[1] >= 8


# ---------------------------------------------------------------------------
# سويتات تحتاج جرد MASAQ — تُتخطّى إن غاب المدخل
# ---------------------------------------------------------------------------

def test_axis2_suite_all_pass(registry, policy):
    suite = axis2_registry.build_suite(registry, policy)
    assert suite.ok, [f"{c.name}: {c.detail}" for c in suite.failures]


def test_axis4_suite_all_pass(registry, policy, witness):
    suite = axis4_peeling.build_suite(registry, policy)
    assert suite.ok, [f"{c.name}: {c.detail}" for c in suite.failures]
