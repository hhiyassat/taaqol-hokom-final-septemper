#!/usr/bin/env python3
"""`T-5` مبنيًّا فارغًا، فاشلًا مغلقًا — وظلٌّ لا حكم  (`T5.2`).

    .venv-taaqol/bin/python scripts/gamma_over_axes.py

**الغرض.** أن يصير حكمُ `B2` **تشغيلًا لا مشروعًا**: الهيكلُ مبنيٌّ اليوم،
فإذا أسند المالكُ الأصنافَ السبعةَ شُغّل في دقائق. وحتى ذلك **يقف مغلقًا**
ولا يكتب ملفًّا واحدًا: تشغيلُ Γ بأصنافٍ غيرِ مسنَدةٍ يعطي أحكامًا لا معنى
لها — وحكمٌ بلا معنًى أسوأُ من لا حكم، لأنّه يُقرأ حكمًا.

**وظلٌّ لا حكم.** لا يُبدَّل عمودُ `Verdict` في مخرجات المحاور، ولا يدخل
مخرَجُ Γ أيَّ قرارٍ في أسلوط. فهو قياسٌ **لما سيقع**، لا وقوعُه.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))

ASSIGN = ROOT / "data" / "residual_kind_assignment.json"
OUT = ROOT / "reports" / "gamma_shadow"
ASSIGNABLE = ("BLOCKING", "DEFERRABLE", "NON_BLOCKING", "EXPLANATORY")


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


def read_assignment() -> dict:
    if not ASSIGN.is_file():
        raise Blocked(f"OWNER_ALERT: ASSIGNMENT_ABSENT — {ASSIGN}")
    return json.loads(ASSIGN.read_text(encoding="utf-8"))


def gate(a: dict) -> dict:
    """يقف مغلقًا ما دام صنفٌ واحدٌ `null`. ولا يُكتب ملفٌّ واحد."""
    assigns = a.get("assignments") or {}
    pending = sorted(k for k, v in assigns.items() if v is None)
    invalid = sorted(f"{k}={v}" for k, v in assigns.items()
                     if v is not None and v not in ASSIGNABLE)
    hidden = sorted(k for k, v in assigns.items()
                    if v == "HIDDEN_FORBIDDEN")
    return {
        "classes": len(assigns),
        "pending": pending,
        "invalid": invalid,
        "hidden_forbidden_chosen": hidden,
        "state": ("BLOCKED_AWAITING_B2" if pending
                  else "BLOCKED_INVALID_KIND" if invalid or hidden
                  else "READY"),
        "note": ("HIDDEN_FORBIDDEN مرفوضٌ إسنادًا: يُكتشف ولا يُختار."
                 if hidden else ""),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="reports/gamma_shadow")
    a = ap.parse_args()

    assignment = read_assignment()
    g = gate(assignment)

    if g["state"] != "READY":
        print(f'{g["state"]}')
        if g["pending"]:
            print(f'  أصنافٌ بلا إسناد {len(g["pending"])}/{g["classes"]}: '
                  f'{" · ".join(g["pending"])}')
        if g["invalid"]:
            print(f'  إسنادٌ خارج الأربعة: {g["invalid"]}')
        if g["hidden_forbidden_chosen"]:
            print(f'  {g["note"]}')
        print("  ولم يُكتب ملفٌّ واحد — وتشغيلُ Γ بأصنافٍ غيرِ مسنَدةٍ "
              "يعطي أحكامًا لا معنى لها.")
        wrote = sorted(p.name for p in (ROOT / a.out).glob("AXIS_*_GAMMA.csv")) \
            if (ROOT / a.out).is_dir() else []
        print(f"  ملفّاتُ Γ الموجودة: {wrote or 'لا شيء'}")
        return 3

    print("READY — والإسنادُ مكتمل. ويُبنى الظلُّ الآن.")
    print("  (لم يُبلَغ هذا الطريقُ بعدُ: B2 موقوف.)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
