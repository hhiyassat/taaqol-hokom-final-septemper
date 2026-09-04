#!/usr/bin/env python3
"""`R3` — ٦٠ و٥٢: مقامان لا خطأ. والثمانيةُ لم تخرج، بل عُدَّت مرّتين.

    PYTHONPATH=src .venv-taaqol/bin/python scripts/measure_class_count.py

**الواقعة.** `U_UNVOCALIZED_CARRIER` = ٦٠ في كلّ ما صُدِّر، و٥٢ في `T5.3`.
والمجموعُ ١٨٬١٤٣ ⟶ ١٨٬١٣٥. فتُقاس النسبتان ويُسمّى مقامُ كلٍّ.

**والمقيسُ.** كلاهما صحيحٌ بمقامه:

* ٦٠ = **أحداث**: `classes.update(cls for cls, _, _ in r.owner_decisions)`
  في `axis1_normalization.py:1233`. والصنفُ يُرفَع عند **موضع حرفٍ**
  (`self._decide("U_UNVOCALIZED_CARRIER", ctx.index, …)`)، فكلمةٌ فيها
  حاملان غيرُ مشكولَين ترفعه مرّتين.
* ٥٢ = **كلمات**: عمودُ `Owner_Decision_Classes` في الجدول، وهو
  `decision_classes` — و**هي مجموعةٌ** (`{cls for cls, _, _ in …}` في
  `:224`)، فتُسقط التكرارَ داخل الكلمة.

**والثمانيةُ.** لم تخرج كلمةٌ واحدة. هي ثمانيةُ **مواضعِ حرفٍ زائدة** على
خمس كلماتٍ معدودةٍ أصلًا. وتُسمّى بمواضعها.

**فلا تُصحَّح ١٨٬١٤٣.** هي مجموعُ الأحداث، وهو رقمٌ صحيحٌ بمقامه؛
و١٨٬١٣٥ مجموعُ الكلمات. والخطأُ الوحيدُ كان عرضَهما بلا مقام
(`DENOMINATOR_IS_PINNED`).
"""
from __future__ import annotations

import argparse
import collections
import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

WORDS = ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv"
A1_CSV = ROOT / "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv"
A1_MEASURES = ROOT / "reports/axis_1_normalization/AXIS_1_MEASURES.json"
POLICY = ROOT / "data" / "axis_1_owner_policy.json"


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def events_from_measures() -> dict:
    """مقامُ الأحداث — كما كُتب في `AXIS_1_MEASURES.json`."""
    if not A1_MEASURES.is_file():
        raise Blocked(f"OWNER_ALERT: ABSENT — {A1_MEASURES}")
    return json.loads(A1_MEASURES.read_text(encoding="utf-8"))[
        "owner_decision_classes"]


def words_from_table() -> dict:
    """مقامُ الكلمات — من عمود الجدول، بالفصل على `|` لا بالاحتواء."""
    if not A1_CSV.is_file():
        raise Blocked(f"OWNER_ALERT: ABSENT — {A1_CSV}")
    out: collections.Counter = collections.Counter()
    with A1_CSV.open(encoding="utf-8", newline="") as fh:
        for r in csv.DictReader(fh):
            for cls in (r.get("Owner_Decision_Classes") or "").split("|"):
                if cls.strip():
                    out[cls.strip()] += 1
    return dict(out)


def positions_per_word(cls: str) -> dict:
    """الثمانيةُ بأعيانها — تُشغَّل القاعدةُ نفسُها ويُعدّ **الموضع**.

    ولا يُحسب الفرقُ طرحًا ثمّ يُوصَف؛ يُقاس كلُّ موضعٍ من مصدره.
    """
    from aslot.axes.axis1_normalization import OwnerPolicy, normalize_token
    policy = OwnerPolicy.load(POLICY if POLICY.is_file() else None)
    per: dict[tuple, int] = {}
    surface: dict[tuple, str] = {}
    with WORDS.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            pos = (int(row["Sura_No"]), int(row["Verse_No"]),
                   int(row["Word_No"]))
            res = normalize_token(row["Word"], pos, policy)
            n = sum(1 for c, _, _ in res.owner_decisions if c == cls)
            if n:
                per[pos] = n
                surface[pos] = row["Word"]
    multi = sorted((p, n) for p, n in per.items() if n > 1)
    return {
        "class": cls,
        "events": sum(per.values()),
        "events_denominator": "مواضعُ حرفٍ يُرفع عندها الصنف",
        "words": len(per),
        "words_denominator": "كلماتٌ تحمل الصنف مرّةً فأكثر",
        "words_raising_it_more_than_once": len(multi),
        "extra_events": sum(n - 1 for _, n in multi),
        "the_extra": [{"position": ":".join(map(str, p)), "raised": n,
                       "extra": n - 1, "word": surface[p]}
                      for p, n in multi],
        "nothing_left": "لم تخرج كلمةٌ واحدة — الفرقُ مواضعُ حرفٍ زائدة "
                        "على كلماتٍ معدودةٍ أصلًا",
        "command": "PYTHONPATH=src .venv-taaqol/bin/python "
                   "scripts/measure_class_count.py",
    }


def guards(ev: dict, wd: dict, detail: dict) -> list[dict]:
    both = sorted(set(ev) | set(wd))
    disagree = sorted(k for k in both if ev.get(k) != wd.get(k))
    g = [{
        "guard": "G_BOTH_DENOMINATORS_NAMED",
        "denominator": len(both),
        "classes_where_they_differ": disagree,
        "passes": True,
        "note": "الاختلافُ ليس خللًا — هو مقامان. والحارسُ يُثبت أنّ "
                "كليهما مقيسٌ ومسمًّى، لا أنّهما متساويان.",
    }, {
        "guard": "G_DIFFERENCE_IS_ACCOUNTED",
        "denominator": sum(ev.values()),
        "events_total": sum(ev.values()),
        "words_total": sum(wd.values()),
        "difference": sum(ev.values()) - sum(wd.values()),
        "accounted_by": detail["extra_events"],
        "passes": (sum(ev.values()) - sum(wd.values())
                   == detail["extra_events"]),
        "note": "الفرقُ كلُّه مشروحٌ بمواضعَ مسمّاة — وفرقٌ بلا موضعٍ "
                "دعوى لا قياس.",
    }, {
        "guard": "G_DETAIL_AGREES_WITH_BOTH",
        "denominator": 2,
        "events_match": detail["events"] == ev.get(detail["class"]),
        "words_match": detail["words"] == wd.get(detail["class"]),
        "passes": (detail["events"] == ev.get(detail["class"])
                   and detail["words"] == wd.get(detail["class"])),
        "note": "التشغيلُ المستقلُّ يردّ العددَين نفسَيهما — وإلا فأحدُهما "
                "من مصدرٍ ثالثٍ مجهول.",
    }]
    return g


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/bound")
    ap.add_argument("--class", dest="cls", default="U_UNVOCALIZED_CARRIER")
    a = ap.parse_args()

    ev, wd = events_from_measures(), words_from_table()
    detail = positions_per_word(a.cls)
    g = guards(ev, wd, detail)

    res = {
        "task": "R3_CLASS_COUNT",
        "by_class": {k: {"events": ev.get(k), "words": wd.get(k),
                         "agree": ev.get(k) == wd.get(k)}
                     for k in sorted(set(ev) | set(wd))},
        "totals": {
            "events": sum(ev.values()),
            "events_denominator": "مواضعُ حرفٍ يُرفع عندها صنف · "
                                  "AXIS_1_MEASURES.owner_decision_classes",
            "events_source": "src/aslot/axes/axis1_normalization.py:1233",
            "words": sum(wd.values()),
            "words_denominator": "كلماتٌ تحمل الصنف · عمود "
                                 "Owner_Decision_Classes",
            "words_source": "src/aslot/axes/axis1_normalization.py:224 "
                            "(decision_classes مجموعةٌ فتُسقط التكرار)",
            "difference": sum(ev.values()) - sum(wd.values()),
        },
        "correction": {
            "18143_is_wrong": False,
            "ruling": "لا تُصحَّح 18,143 — هي مجموعُ الأحداث بمقامه. "
                      "و18,135 مجموعُ الكلمات. والخطأُ كان عرضَهما بلا "
                      "مقام، لا أحدَهما.",
            "where_18143_stands": "output/doors · output/remediation — "
                                  "وتُسمّى «أحداثًا» لا «كلماتٍ متأثّرة»",
            "where_18135_stands": "reports/gamma_shadow/PROJECTED_IMPACT — "
                                  "وهو مقامُ الكلمات",
        },
        "detail": detail,
        "guards": g,
        "all_guards_pass": all(x["passes"] for x in g),
    }
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "02_class_count.json").write_text(
        json.dumps(res, ensure_ascii=False, indent=1), encoding="utf-8")

    t = res["totals"]
    print(f'R3 أحداثٌ {t["events"]} · كلماتٌ {t["words"]} · '
          f'فرقٌ {t["difference"]}')
    print(f'   {detail["class"]}: أحداثٌ {detail["events"]} · '
          f'كلماتٌ {detail["words"]}')
    print(f'   والثمانيةُ لم تخرج: '
          f'{detail["words_raising_it_more_than_once"]} كلماتٍ ترفعه أكثرَ '
          f'من مرّة، بزيادةِ {detail["extra_events"]} موضعًا:')
    for x in detail["the_extra"]:
        print(f'     {x["position"]:12} × {x["raised"]}  '
              f'(+{x["extra"]})  {x["word"]}')
    for x in g:
        print(f'   {x["guard"]:26} {"PASS" if x["passes"] else "FALLS"} '
              f'/{x["denominator"]}')
    if not res["all_guards_pass"]:
        raise Blocked("GUARD_FALLS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
