#!/usr/bin/env python3
"""شهادةُ `G_BYTE_IDENTICAL` — تُشغَّل مرّتَين، ولا تُكتب بيد.

    PYTHONPATH=src .venv-taaqol/bin/python scripts/build_byte_identity.py \
        --task TANWEEN_UNFOLD_APPLY --reason "N-TANWEEN-UNFOLD — ..."

**ما كان.** الشهادةُ تُكتب يدًا بعد كلّ جولةِ تغيير: بصماتٌ تُنسخ، وعددُ
تشغيلاتٍ يُكتب `2`، وتاريخٌ يُطبع. وشهادةٌ مكتوبةٌ بيدٍ تشهد بما لم ترَ —
وهي `MEASURED_NOT_PRESET` مقلوبةً على نفسها.

**وما هو.** السلسلةُ تُشغَّل **مرّتَين فعلًا**، وتُقابَل بصماتُ التشغيلَين
(وهذه هي إعادةُ الإنتاج)، ثمّ تُقابَل بالأساس السابق (وهذا هو أثرُ
التغيير). والسقوطُ على الأساس القديم **دليلٌ لا خلل** — فيُسجَّل بسببه.

**والتاريخُ يُراكم ولا يُمحى.** كان `baseline_superseded_by` حقلًا واحدًا
يُكتب فوق سابقه، فتُمحى واقعةُ الجولة الماضية بواقعة الحاضرة. فصار
`supersessions` قائمةً: كلُّ جولةٍ سطرٌ باسمها وسببها وما تحرّك فيها —
والأخيرةُ تُقرأ من ذيلها، والسوابقُ تبقى.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
EV = ROOT / "output" / "max" / "byte_identity_evidence.json"
CMD = ["-m", "aslot", "all", "--quiet"]


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def axis_files() -> list[str]:
    """المقامُ مُعلَن: كلُّ ملفٍّ تحت `reports/axis_*` — لا الجداولُ وحدَها."""
    out = []
    for d in sorted((ROOT / "reports").glob("axis_*")):
        for p in sorted(d.rglob("*")):
            if p.is_file():
                out.append(str(p.relative_to(ROOT)))
    return out


def hashes(rels: list[str]) -> dict:
    return {r: hashlib.sha256((ROOT / r).read_bytes()).hexdigest()
            for r in rels}


def run_chain() -> int:
    env = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    r = subprocess.run([sys.executable, *CMD], cwd=str(ROOT), env=env,
                       capture_output=True, text=True, check=False)
    return r.returncode


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--task", required=True,
                    help="اسمُ الجولة التي أوجبت تجديدَ الأساس")
    ap.add_argument("--reason", required=True,
                    help="سببُ التجديد — ويُقرأ، فلا يُختصر برمز")
    ap.add_argument("--out", default=str(EV.relative_to(ROOT)))
    a = ap.parse_args()

    prev = json.loads(EV.read_text(encoding="utf-8")) if EV.is_file() else {}
    before = prev.get("sha256", {})

    # ── تشغيلان فعليّان · وإعادةُ الإنتاج تُقاس بينهما ──────────────
    rc1 = run_chain()
    if rc1 != 0:
        raise Blocked(f"OWNER_ALERT: CHAIN_FAILED — خرج {rc1} في التشغيل الأوّل")
    rels = axis_files()
    first = hashes(rels)
    rc2 = run_chain()
    if rc2 != 0:
        raise Blocked(f"OWNER_ALERT: CHAIN_FAILED — خرج {rc2} في التشغيل الثاني")
    if axis_files() != rels:
        raise Blocked("OWNER_ALERT: FILE_SET_MOVED_BETWEEN_RUNS — "
                      "المقامُ نفسُه تغيّر بين تشغيلَين")
    second = hashes(rels)
    between = sorted(k for k in rels if first[k] != second[k])

    # ── وأثرُ التغيير يُقاس بالأساس السابق ─────────────────────────
    moved = sorted(k for k in rels if k in before and before[k] != second[k])
    added = sorted(set(rels) - set(before))
    dropped = sorted(set(before) - set(rels))

    supersessions = list(prev.get("supersessions") or [])
    # ترقيةُ الشكل القديم — حقلٌ واحدٌ يصير أوّلَ سطرٍ في التاريخ
    old = prev.get("baseline_superseded_by")
    if old and not any(s.get("task") == old.get("task") for s in supersessions):
        supersessions.append(old)

    # **ولا يُسجَّل تجديدٌ لم يقع.** جولةٌ لم تُحرّك ملفًّا واحدًا لم
    # تُجدّد أساسًا — وتسجيلُها سطرًا في التاريخ يجعل الجردَ يشهد
    # بوقائعَ لم تقع، ويُضخّم عددَ التغييرات في كلّ قراءةٍ تالية.
    # فتُعلَن ولا تُكتب.
    if not moved and not added and not dropped:
        doc = dict(prev)
        doc.update({"utc": datetime.now(timezone.utc).isoformat(
            timespec="seconds"), "exit_code": rc2,
            "runs_are_measured_not_declared": True,
            "differing_between_runs": between, "sha256": second,
            "supersessions": supersessions})
        if supersessions:
            doc["baseline_superseded_by"] = supersessions[-1]
        (ROOT / a.out).write_text(
            json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")
        print(f'RUNS        2 · خرج {rc2} · مقامٌ {len(rels)} ملفًّا')
        print(f'REPRODUCIBLE {"نعم" if not between else "لا — " + str(between)}')
        print(f'VS_BASELINE  تحرّك 0/{len(rels)} — '
              f'فلا تجديدَ يُسجَّل ({a.task} لم تمسّ محورًا)')
        print(f'SUPERSESSIONS {len(supersessions)} · بلا زيادة')
        print(f"→ {ROOT / a.out}")
        return 0 if not between else 5

    supersessions.append({
        "task": a.task,
        "reason": a.reason,
        "files_that_moved_vs_previous_baseline": moved,
        "files_added": added,
        "files_dropped": dropped,
        "count": len(moved),
        "of": len(rels),
        "note": "سقوطُ G_BYTE_IDENTICAL على الأساس القديم هو **الدليلُ** على "
                "وقوع التغيير، لا خللٌ يُكتم. والخاصّةُ المحفوظةُ هي إعادةُ "
                "الإنتاج: تشغيلان بعد التغيير متطابقان بايتةً بايتة.",
        "previous_utc": prev.get("utc"),
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    })

    doc = {
        "command": "PYTHONPATH=src .venv-taaqol/bin/python -m aslot all --quiet",
        "runs": 2,
        "runs_are_measured_not_declared": True,
        "utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "exit_code": rc2,
        "denominator": len(rels),
        "denominator_note": "كلُّ ملفٍّ تحت reports/axis_* — لا الجداولُ "
                            "الخمسةُ وحدَها",
        "differing_between_runs": between,
        # يبقى للمتوافق: آخرُ سطرٍ في التاريخ
        "baseline_superseded_by": supersessions[-1],
        "supersessions": supersessions,
        "sha256": second,
    }
    (ROOT / a.out).write_text(
        json.dumps(doc, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f'RUNS        2 · خرج {rc2} · مقامٌ {len(rels)} ملفًّا')
    print(f'REPRODUCIBLE {"نعم" if not between else "لا — " + str(between)}')
    print(f'VS_BASELINE  تحرّك {len(moved)}/{len(rels)}' +
          (f'  ·  {" · ".join(moved)}' if moved else ""))
    print(f'SUPERSESSIONS {len(supersessions)} · آخرُها {a.task}')
    print(f"→ {ROOT / a.out}")
    return 0 if not between else 5


if __name__ == "__main__":
    raise SystemExit(main())
