#!/usr/bin/env python3
"""`G_EVIDENCE_IS_NOT_TAUTOLOGY` — تمييزُ الشهادةِ من الترديد بمصدرِ المدخل.

**القاعدة.** استفتاءٌ مصدرُ مدخلِه هو المُستفتَى نفسُه يُوسَم `TAUTOLOGY`
ولا يُعدّ دليلًا. فسؤالُ السجلِّ عن صفٍّ أُخذ من السجلّ يردّ `True` بحكم
الأخذ، لا بحكم الواقع.

**والحارسُ يقيس المصدرَ لا الجواب.** ولذلك سمُّه ذو وجهَين:

* زوجٌ من السجلّ ⟶ يلزم `TAUTOLOGY`، ولو كان الجوابُ `True`.
* زوجٌ من رسم المراحل ⟶ يلزم `EVIDENCE`، ولو كان الجوابُ `True` كذلك.

ووجهٌ واحدٌ يُوهم أنّ الحارسَ يقيس مصدرًا وهو يقيس جوابًا: لو اكتُفي
بالوجه الأوّل لمرّ حارسٌ يقول «كلُّ `True` ترديد» — وهو باطل.

**والجردُ مغلق.** مصدرٌ لا اسمَ له في `SOURCES` لا يُصنَّف تخمينًا، بل
يُوسَم `UNCLASSIFIED_SOURCE` ويُبلَّغ.
"""
from __future__ import annotations

#: الجردُ المغلقُ لمصادرِ المدخل. القيمةُ: أهو المُستفتَى نفسُه؟
SOURCES: dict[str, bool] = {
    # من داخل السجلّ — المُستفتَى نفسُه
    "CANONICAL_REGISTRY.lines": True,
    "CANONICAL_REGISTRY.term_transfers": True,
    "FORBIDDEN_STRAIGHT_LINES": True,
    # من خارجه — شهادة
    "get_native_stage_registry().allowed_successors": False,
    "Layer (enum)": False,
    "GenerationSource (enum)": False,
    "reports/axis_0_quran_build": False,
    "reports/axis_4_peel_to_stem": False,
    "runtime/native_stage_registry.py": False,
}

TAUTOLOGY = "TAUTOLOGY"
EVIDENCE = "EVIDENCE"
UNKNOWN = "UNCLASSIFIED_SOURCE"


def classify(source: str) -> str:
    """يُصنَّف بالمصدر وحدَه — ولا يُنظَر إلى الجواب ألبتّة."""
    if source not in SOURCES:
        return UNKNOWN
    return TAUTOLOGY if SOURCES[source] else EVIDENCE


def evidence_is_not_tautology(rows: list[dict]) -> dict:
    """`G_EVIDENCE_IS_NOT_TAUTOLOGY` — يبلّغ ولا يموت.

    كلُّ صفٍّ يحمل `input_drawn_from` و`status`؛ ويُقابَل الوسمُ المكتوبُ
    بالوسمِ المشتقِّ من المصدر. والمخالفُ يُسمّى، والمصدرُ المجهولُ يُسمّى
    كذلك — ولا يُخمَّن له تصنيف.
    """
    mislabelled: list[str] = []
    unclassified: list[str] = []
    considered = 0
    for r in rows:
        src = r.get("input_drawn_from")
        if src is None:
            continue
        considered += 1
        want = classify(src)
        got = r.get("status")
        ident = (f'{r.get("query_id", r.get("ident", "?"))}:'
                 f'{r.get("source", "?")}->{r.get("target", "?")}')
        if want == UNKNOWN:
            unclassified.append(f"{ident} [{src}]")
        elif got in (TAUTOLOGY, EVIDENCE) and got != want:
            mislabelled.append(f"{ident}: {got}≠{want}")
    return {
        "guard": "G_EVIDENCE_IS_NOT_TAUTOLOGY",
        "denominator": considered,
        "of_rows": len(rows),
        "mislabelled": sorted(mislabelled),
        "unclassified": sorted(unclassified),
        "measures": "مصدرَ المدخل — لا الجواب",
        "passes": not mislabelled and not unclassified,
    }


__all__ = ["SOURCES", "TAUTOLOGY", "EVIDENCE", "UNKNOWN", "classify",
           "evidence_is_not_tautology"]
