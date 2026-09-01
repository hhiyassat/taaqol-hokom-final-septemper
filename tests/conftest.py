"""تجهيزات مشتركة.

``MASAQ.csv`` مدخلٌ ثقيل قد لا يكون حاضرًا (مستبعَدٌ من git بسياسة U1)،
فالاختباراتُ المعتمدة عليه **تُتخطّى صراحةً** ولا تُخفق. تخطٍّ معلنٌ أصدق من
نجاحٍ وهميّ على جردٍ فارغ.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from aslot.axes.axis2_registry import Registry
from aslot.axes.axis4_peeling import build_internal_corpus_witness_set
from aslot.policy import OwnerPolicy

ROOT = Path(__file__).resolve().parents[1]
MASAQ = ROOT / "data" / "MASAQ.csv"
AXIS1_CSV = ROOT / "reports" / "axis_1_normalization" / "AXIS_1_NORMALIZATION.csv"


@pytest.fixture(scope="session")
def policy() -> OwnerPolicy:
    return OwnerPolicy.load(ROOT / "data" / "axis_1_owner_policy.json")


@pytest.fixture(scope="session")
def registry(policy) -> Registry:
    if not MASAQ.exists():
        pytest.skip("data/MASAQ.csv غير موجود — لا يُبنى جردٌ شاهد")
    return Registry.from_masaq_witness(MASAQ, policy)


@pytest.fixture(scope="session")
def witness() -> set:
    if not AXIS1_CSV.exists():
        pytest.skip("مخرج المحور الأول غير موجود — شغّل  aslot all  أولًا")
    return build_internal_corpus_witness_set(AXIS1_CSV)
