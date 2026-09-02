#!/usr/bin/env python3
"""يقيس ما يميّزه `classify_token_paths` وما لا يميّزه — بجردٍ مقروءٍ من مصدره.

    .venv-taaqol/bin/python scripts/probe_path_classifier.py

**لماذا هذا الملفّ.** قلتُ بعد أوّل تشغيل: «المصنِّفُ لا يميّز أصلًا». وذلك
نفيٌ عامٌّ بُني على أربعة نصوصٍ كلُّها مشكولةٌ بالكامل، فسحبه المالكُ بحقّ.
والنفيُ العامّ من شاهدٍ ضيّق هو الصنفُ الذي يمنعه هذا المشروع في المحرّك،
فلا يجوز أن أقع فيه في القول.

فبدل دعوى مصحَّحةٍ في رسالة، **مِسبارٌ يُعاد تشغيلُه**: يقرأ مفاتيحَ الجرد
من مصدر تعقُّل لا من يدي، ويقيس ثلاثة أشياء:

    ١  كم مفتاحًا في الجرد، وكم منها مشكول
    ٢  ماذا يُخرج على السطح المجرَّد، وماذا على المشكول
    ٣  هل تُصنَّف الكلمةُ نفسُها تصنيفين باختلاف الشكل

والثالثةُ أخطرُ من الأولى: مصنِّفٌ يسكت عن المشكول عجزٌ مُعلَن، ومصنِّفٌ
يعطي المشكولَ **جوابًا آخر** يمرّ صامتًا.
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = (ROOT / "vendor/Taaqol-GPT/src/taaqqul_slot_geometry/runtime"
            / "native_stage_registry.py")
sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))

#: أزواجٌ للفحص الثالث: المفتاحُ كما هو في الجرد، وهو مشكولًا.
#: والمشكولُ **منقولٌ من رسم المصحف** لا مطبوعٌ باجتهاد.
PAIRS = [("الذين", "الَّذِينَ"), ("الذي", "الَّذِي"),
         ("يا", "يَا"), ("إذا", "إِذَا")]


def registry_keys() -> list[str]:
    """يقرأ المفاتيحَ من مصدر تعقُّل — فلو زيدت ظهرت هنا بلا تعديل."""
    src = REGISTRY.read_text(encoding="utf-8")
    body = src.split("mapping: dict[str, tuple[PathEvidence, ...]] = {")[1]
    return re.findall(r'^\s{8}"([^"]+)":', body, re.M)


def vocalized(text: str) -> bool:
    return any(unicodedata.combining(c) for c in text)


def main() -> int:
    from taaqqul_slot_geometry.runtime.native_stage_registry import (
        classify_token_paths,
    )

    def top(surface: str) -> tuple[str, float]:
        p = classify_token_paths(surface)[0]
        return p.path_id.value, p.confidence

    keys = registry_keys()
    if not keys:
        raise SystemExit("OWNER_ALERT: لم تُقرأ مفاتيحُ الجرد — تغيّر المصدر؟")

    nazila = (ROOT / "inspection/case.txt").read_text(encoding="utf-8").split()
    bare = {k: top(k) for k in keys}
    on_nazila = {t: top(t) for t in nazila}
    disagree = [(b, v, top(b)[0], top(v)[0]) for b, v in PAIRS
                if top(b)[0] != top(v)[0]]

    out = {
        "registry_keys": len(keys),
        "registry_keys_vocalized": sum(1 for k in keys if vocalized(k)),
        "distinct_paths_on_bare_keys": sorted({p for p, _ in bare.values()}),
        "confidence_range_on_bare_keys":
            [min(c for _, c in bare.values()), max(c for _, c in bare.values())],
        "distinct_paths_on_nazila": sorted({p for p, _ in on_nazila.values()}),
        "nazila_tokens_vocalized": sum(1 for t in nazila if vocalized(t)),
        "same_word_two_answers": [
            {"bare": b, "vocalized": v, "path_bare": pb, "path_vocalized": pv}
            for b, v, pb, pv in disagree],
        "fallback_rules_in_source": [
            "exact match on the bare surface — 11 keys",
            "startswith('ال') → JamidPath 0.62",
            "otherwise → RootStemPath 0.55",
        ],
    }
    (ROOT / "inspection/nazila/02_path_classifier.json").write_text(
        json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"KEYS                {len(keys)} مفتاحًا · "
          f"مشكولٌ منها {out['registry_keys_vocalized']}")
    print(f"PATHS_ON_BARE       {len(out['distinct_paths_on_bare_keys'])} مساراتٍ "
          f"بثقةٍ {out['confidence_range_on_bare_keys'][0]}–"
          f"{out['confidence_range_on_bare_keys'][1]}   ← يميّز")
    print(f"PATHS_ON_NAZILA     {out['distinct_paths_on_nazila']}   "
          f"({out['nazila_tokens_vocalized']}/{len(nazila)} مشكولة)   ← لا يميّز")
    print(f"TWO_ANSWERS         {len(disagree)}/{len(PAIRS)} كلمةً تُصنَّف "
          f"تصنيفين باختلاف الشكل")
    for b, v, pb, pv in disagree:
        print(f"    {b:<8}{pb:<26} ↔  {v:<12}{pv}")
    print("→ inspection/nazila/02_path_classifier.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
