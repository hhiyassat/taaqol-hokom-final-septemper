#!/usr/bin/env python3
"""يثبّت حكمَ كلّ شاهدٍ مسمًّى، فلا يتغيّر صامتًا  (`A5`).

    python3 scripts/witness_pins.py --write     # يُنشئ التثبيت أوّلَ مرّة
    python3 scripts/witness_pins.py             # يقابل الحيَّ بالمثبَّت

**العلّة، واقعةً لا تحذيرًا.** `كَبَائِرَ` شاهدُ بوّابةٍ مسمًّى، وغيّر حكمَه
بين جولتَين ولم يوقفه إجراء: الفحوصُ التي تذكره تسأل عن **صنفه** لا عن
**حكمه**، فبقيت خضراءَ والحكمُ تحته يتحرّك. وشاهدٌ لا يُثبَّت حكمُه ليس
شاهدًا، بل اسمٌ في نصّ.

**وما يُثبَّت.** `verdict` و`termination` لكلّ سطحٍ مسمًّى، بشاهدٍ مُعلَن
(`SUITE_WITNESS`) وبلا شاهدٍ — لأنّ فرقَ الحالين هو ما تقيسه البوّابة.

**وحدُّ ما يدّعيه هذا الملفّ.** التثبيتُ **لقطةٌ لسلوك اليوم**، لا شهادةٌ
بصوابه. فلو كان حكمٌ منها خطأً، ثبّته هذا الملفّ خطأً — وفائدتُه أنّ
تغيُّرَه بعد ذلك يصير **حدثًا مرئيًّا** يقف عنده الإصدار، لا انجرافًا.
والتصحيحُ للمالك، ويُنفَّذ بإعادة التثبيت عن عمدٍ ومعه سببُه.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from aslot.axes.axis1_normalization import normalize_token  # noqa: E402
from aslot.axes.axis2_registry import Registry  # noqa: E402
from aslot.axes.axis4_peeling import SUITE_WITNESS, peel_to_stem  # noqa: E402
from aslot.policy import OwnerPolicy  # noqa: E402

PINS = ROOT / "data" / "witness_pins.json"
MASAQ = ROOT / "data" / "MASAQ.csv"
POLICY = ROOT / "data" / "axis_1_owner_policy.json"

#: الأسطحُ المسمّاةُ في فحوص المحور الرابع وسمومِه — تُجرَد هنا مرّةً
#: واحدة، فمن أضاف شاهدًا هناك ولم يُثبّته هنا كشفه حارسُ التغطية.
NAMED = ("بِسْمِ", "كَفَرُوا", "كَبَائِرَ", "كَتَبَ", "مَا", "مَاْ",
         "كِتَاْبُنْ", "وَلِلْكَافِرِينَ", "وَكِتَاْبُنْ")


def measure() -> dict:
    """يُشغّل التقشيرَ على كلّ شاهدٍ في الحالين، ويردّ الحكمَ كما خرج."""
    if not MASAQ.is_file():
        raise SystemExit(
            "OWNER_ALERT: MASAQ_ABSENT — لا يُبنى جردٌ شاهد، ولا يُثبَّت حكمٌ "
            "على جردٍ فارغ. وتثبيتٌ من لا شيءٍ أسوأُ من غياب التثبيت.")
    policy = OwnerPolicy.load(POLICY)
    registry = Registry.from_masaq_witness(MASAQ, policy)
    out: dict = {}
    for word in NAMED:
        row = {}
        for label, wit in (("with_declared_witness", SUITE_WITNESS),
                           ("without_witness", None)):
            r = peel_to_stem(normalize_token(word, None, policy).normalized,
                             registry, wit)
            row[label] = {"verdict": str(r.verdict),
                          "termination": str(r.termination)}
        out[word] = row
    return out


def compare(live: dict, pinned: dict) -> list[str]:
    """يردّ كلَّ اختلافٍ مسمًّى. والغيابُ اختلافٌ أيضًا، في الجهتين."""
    drift = []
    for word in sorted(set(live) | set(pinned)):
        if word not in pinned:
            drift.append(f"{word}: شاهدٌ حيٌّ غيرُ مثبَّت — UNPINNED_WITNESS")
            continue
        if word not in live:
            drift.append(f"{word}: شاهدٌ مثبَّتٌ لم يُقَس — WITNESS_DISAPPEARED")
            continue
        for label in sorted(set(live[word]) | set(pinned[word])):
            a, b = live[word].get(label), pinned[word].get(label)
            if a != b:
                drift.append(f"{word} · {label}: مثبَّت {b} ⟵ حيّ {a}")
    return drift


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--write", action="store_true",
                    help="يكتب التثبيتَ من التشغيل الحاليّ (فعلٌ مقصود)")
    a = ap.parse_args()

    live = measure()
    if a.write:
        PINS.write_text(json.dumps(live, ensure_ascii=False, indent=1),
                        encoding="utf-8")
        print(f"PINNED {len(live)} شاهدًا → {PINS}")
        print("وهذه لقطةُ سلوكِ اليوم، لا شهادةٌ بصوابه.")
        return 0

    if not PINS.is_file():
        print(f"OWNER_ALERT: PINS_ABSENT — {PINS} غيرُ موجود. "
              "شغّل --write مرّةً بعد مراجعة الأحكام.")
        return 2
    pinned = json.loads(PINS.read_text(encoding="utf-8"))
    drift = compare(live, pinned)
    if drift:
        print("BLOCKED: WITNESS_VERDICT_DRIFT")
        for line in drift:
            print(f"  {line}")
        return 3
    print(f"WITNESS_PINS_HOLD  {len(pinned)} شاهدًا · لا انحراف")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
