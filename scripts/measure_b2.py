#!/usr/bin/env python3
"""قياسٌ يفكّ `B2` — ولا يحكم فيه  (`MAX_EXECUTABLE` · `M1` `M2` `M3`).

    python3 scripts/measure_b2.py --out output/max

**ما يفعله ولا يفعله.** `B2` موقوفٌ لأنّ ثلاثةً من أصنافه السبعة لا سلوكَ
مقيسٌ لها، ورابعًا غيرُ متجانس. فيُقاس السلوكُ ويُرفع، **ولا يُسنَد صنفٌ
واحد**: `P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED` — خانةُ الاختيار تبقى
فارغةً، وسمٌّ يسقط إن مُلئت.

**والسقوفُ مُستفتاةٌ من `ResidualPolicy`** لا مكتوبة. ويُعلَن ما تكشفه
الاستفتاءُ نفسُه: `NON_BLOCKING` و`EXPLANATORY` سقفُهما واحد، فالفرقُ
بينهما وصفيٌّ لا رتبيّ، والمخرَجاتُ الرتبيّةُ ثلاثةٌ لا خمسة.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import unicodedata
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))

A1 = ROOT / "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv"
A2 = ROOT / "reports/axis_2_mabniyat_operators/AXIS_2_TOKENS.csv"
A3 = ROOT / "reports/axis_3_syllables/AXIS_3_SYLLABLES.csv"
A4 = ROOT / "reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv"

ALIF, FATHATAN = "ا", "ً"

#: الأصنافُ السبعة كما تُصدرها المحاور — جردٌ مغلق.
CLASSES = ("U_TANWEEN", "U_ALIF_FARIQA", "U_ALIF_MAQSURA",
           "U_N7_2_INTERNAL_AL", "U_ALEF_MADDA", "U_UNVOCALIZED_CARRIER",
           "U_MULTIWORD_CELL")

#: الأصنافُ التي يجوز للمالك إسنادُها. و`HIDDEN_FORBIDDEN` ليست منها:
#: تُكتشف ولا تُختار — فاختيارُها ادّعاءٌ بأنّ الخفاءَ مقصود.
ASSIGNABLE = ("BLOCKING", "DEFERRABLE", "NON_BLOCKING", "EXPLANATORY")


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


def rows(p: Path) -> list[dict]:
    if not p.is_file():
        raise Blocked(f"OWNER_ALERT: AXIS_OUTPUT_ABSENT — {p}. "
                      "شغّل  python3 -m aslot all  أوّلًا.")
    with p.open(encoding="utf-8", newline="") as fh:
        return list(csv.DictReader(fh))


def key(r: dict) -> tuple:
    return (r["Sura_No"], r["Verse_No"], r["Word_No"])


def consonants(surface: str) -> int:
    """عددُ الصوامت — حروفٌ بلا علاماتٍ تشكيليّة."""
    return sum(1 for c in surface
               if not unicodedata.combining(c) and c.strip())


# ── سقوفُ الرتب — مُستفتاةٌ من ResidualPolicy لا مكتوبة ─────────────────
def ceilings() -> dict:
    """يُستفتى `ResidualPolicy.rank_cap` حيًّا — لا `ceiling`.

    و`ceiling(residuals)` تأخذ **صفَّ بقايا** لا صنفًا، فتمريرُ الصنف إليها
    يرفع `AttributeError`. وأوّلُ كتابةٍ فعلت ذلك فخرجت السقوفُ كلُّها
    `UNMEASURED` — و**مرّ الحارس** لأنّه فحص أنّ الناتج قاموسٌ لا أنّ فيه
    قياسًا. فالحارسُ يفحص القيمَ الآن، لا الوعاء.
    """
    from taaqqul_slot_geometry.core.residual_policy import (
        ResidualKind,
        ResidualPolicy,
    )
    out = {}
    for k in ResidualKind:
        try:
            out[k.name] = ResidualPolicy.rank_cap(k).name
        except Exception as exc:
            out[k.name] = f"UNMEASURED:{type(exc).__name__}"
    distinct = sorted(set(out.values()))
    return {
        "ceilings": out,
        "queried_by": "ResidualPolicy.rank_cap(ResidualKind.X).name",
        "assignable_kinds": list(ASSIGNABLE),
        "hidden_forbidden_is_not_assignable": True,
        "hidden_forbidden_note": "تُكتشف ولا تُختار — واختيارُها ادّعاءٌ "
                                 "بأنّ الخفاءَ مقصود.",
        "distinct_rank_outcomes": distinct,
        "distinct_rank_outcomes_count": len(distinct),
        "kinds_count": len(out),
        "non_blocking_and_explanatory_share_a_ceiling":
            out.get("NON_BLOCKING") == out.get("EXPLANATORY"),
        "note": ("NON_BLOCKING و EXPLANATORY سقفُهما واحد — فالفرقُ وصفيٌّ "
                 f"لا رتبيّ، والمخرَجاتُ الرتبيّةُ {len(distinct)} لا "
                 f"{len(out)}."),
        "command": "python3 scripts/measure_b2.py",
    }


# ── M1 · شطرُ U_TANWEEN ────────────────────────────────────────────────
def m1_split(a1: list[dict], a3: list[dict]) -> dict:
    """شطرُ `U_TANWEEN` — والمميِّزُ المقترَح **لا يشطر**، فيُعلَن ذلك.

    اقتُرح أن يكون الشطرُ «مجموعُ الصوامت بعد التطبيع > قبله». والمقيس:
    ذلك صادقٌ على **الصنف كلِّه**، لأنّ كلَّ تنوينٍ يُبسَط إلى نونٍ ساكنة
    فيزيد صامتًا حتمًا. فهو خاصّةُ الصنف لا مميِّزَ داخلَه.

    والمميِّزُ الذي يشطر فعلًا هو **تنوينُ الفتح على ألفٍ صامتة**: هو الذي
    يولّد صامتًا زائدًا يقبله المحورُ الثالث بلا شكوى — وهو التعريفُ
    الحرفيُّ لـ`HIDDEN_FORBIDDEN`. والاثنان يُطبعان معًا فلا يُقرأ أحدُهما
    شطرًا وهو ليس به.
    """
    verdict3 = {key(r): r.get("Verdict") for r in a3}
    members = [r for r in a1
               if "U_TANWEEN" in (r.get("Owner_Decision_Classes") or "")]
    grew = [r for r in members
            if consonants(r["Normalized_Word"]) > consonants(r["Word"])]
    on_silent_alif = [r for r in members
                      if (ALIF + FATHATAN) in r["Word"]
                      or (FATHATAN + ALIF) in r["Word"]]
    rest = [r for r in members if r not in on_silent_alif]
    hidden = sum(1 for r in on_silent_alif
                 if verdict3.get(key(r)) == "ACCEPT")
    return {
        "U_TANWEEN_total": len(members),
        "proposed_discriminator": {
            "rule": "consonants(normalized) > consonants(raw)",
            "matches": len(grew),
            "of": len(members),
            "discriminates": len(grew) not in (0, len(members)),
            "finding": "لا يشطر: كلُّ تنوينٍ يُبسَط إلى نونٍ ساكنة فيزيد "
                       "صامتًا حتمًا. فهو خاصّةُ الصنف لا مميِّزَ داخلَه.",
        },
        "measured_discriminator": {
            "rule": "fathatan adjacent to a silent alif",
            "on_silent_alif": len(on_silent_alif),
            "on_silent_alif_denominator": "كلماتُ الصنف",
            "rest": len(rest),
            "rest_denominator": "كلماتُ الصنف",
            "closes": len(on_silent_alif) + len(rest) == len(members),
            "of_those_accepted_at_axis3": hidden,
            "of_those_accepted_at_axis3_denominator":
                "الكلماتُ التي عليها تنوينُ فتحٍ على ألفٍ صامتة",
            "why_this_one": "هو الذي يولّد صامتًا زائدًا يقبله المحورُ "
                            "الثالث بلا شكوى — وهو HIDDEN_FORBIDDEN حرفيًّا.",
        },
        "closes": len(on_silent_alif) + len(rest) == len(members),
        "raised_not_decided": True,
        "question": "أهما صنفان أم واحد — والحكمُ للمالك",
        "command": "python3 scripts/measure_b2.py",
    }


# ── M2 · الأصنافُ غيرُ المقيسة ─────────────────────────────────────────
def m2_reach(a1: list[dict], a2: list[dict], a3: list[dict],
             a4: list[dict]) -> dict:
    """لكلّ صنف: كم يبلغ كلَّ محور، وبأيّ حكم، وبأيّ سببِ حجب."""
    # الفصلُ بالفاصلة `|` — لا بالاحتواء. والاحتواءُ يجعل صنفًا يبتلع صنفًا
    # اسمُه بعضُ اسمِه. والعدُّ **بالكلمات**، ويُقابَل بعدّ **الأحداث** في
    # AXIS_1_MEASURES: كلمةٌ قد تحمل الصنفَ مرّتين، فيفترق المقامان.
    events = {}
    mp = ROOT / "reports/axis_1_normalization/AXIS_1_MEASURES.json"
    if mp.is_file():
        events = json.loads(mp.read_text(encoding="utf-8")).get(
            "owner_decision_classes", {})
    idx2 = {key(r): r for r in a2}
    idx3 = {key(r): r for r in a3}
    idx4 = {key(r): r for r in a4}
    out = {}
    for cls in CLASSES:
        members = [r for r in a1
                   if cls in (r.get("Owner_Decision_Classes") or "").split("|")]
        keys = [key(r) for r in members]
        v3 = Counter(idx3[k].get("Verdict") for k in keys if k in idx3)
        v4 = Counter(idx4[k].get("Verdict") for k in keys if k in idx4)
        blocks = Counter(idx3[k].get("Block_Reason") for k in keys
                         if k in idx3 and idx3[k].get("Block_Reason"))
        out[cls] = {
            "members": len(members),
            "members_denominator": "كلماتٌ تحمل الصنف",
            "events": events.get(cls, "UNMEASURED"),
            "events_denominator": "مرّاتُ إصدار الصنف — وكلمةٌ قد تحمله "
                                  "مرّتين",
            "words_and_events_agree": events.get(cls) == len(members),
            "reaches_axis2": sum(1 for k in keys if k in idx2),
            "reaches_axis3": sum(1 for k in keys if k in idx3),
            "reaches_axis4": sum(1 for k in keys if k in idx4),
            "reach_denominator": "كلماتُ الصنف",
            "axis3_verdicts": dict(v3.most_common()),
            "axis4_verdicts": dict(v4.most_common()),
            "axis3_block_reasons": dict(blocks.most_common()),
            "carries_into_a_later_axis":
                sum(1 for k in keys if k in idx4) > 0,
        }
    disagree = {k: {"events": v["events"], "words": v["members"]}
                for k, v in out.items() if not v["words_and_events_agree"]}
    return {"per_class": out,
            "classes_total": len(CLASSES),
            "classes_where_events_differ_from_words": disagree,
            "denominator_note": ("عدُّ الأحداث وعدُّ الكلمات مقامان. "
                                 "ويفترقان حيث تحمل كلمةٌ الصنفَ مرّتين — "
                                 "فلا يُعرض أحدُهما بلا اسمه."),
            "words_affected": sum(v["members"] for v in out.values()),
            "words_affected_denominator": "مجموعُ أعضاء الأصناف السبعة",
            "command": "python3 scripts/measure_b2.py"}


# ── M3 · جدولُ الأثر الرتبيّ — فارغَ الاختيار ──────────────────────────
def m3_impact(m2: dict, ceil: dict, a3: list[dict],
              a4: list[dict]) -> dict:
    """لكلّ صنفٍ أثرُ كلّ خيار — والاختيارُ يبقى `null`."""
    c = ceil.get("ceilings") or {}
    table = {}
    for cls, v in m2["per_class"].items():
        accepted3 = v["axis3_verdicts"].get("ACCEPT", 0)
        accepted4 = v["axis4_verdicts"].get("ACCEPT", 0)
        table[cls] = {
            "members": v["members"],
            "if_BLOCKING": {
                "rank_ceiling": c.get("BLOCKING", "UNMEASURED"),
                "rows_that_would_stop": v["members"],
                "rows_leaving_ACCEPT_at_axis3": accepted3,
                "rows_leaving_ACCEPT_at_axis4": accepted4},
            "if_DEFERRABLE": {
                "rank_ceiling": c.get("DEFERRABLE", "UNMEASURED"),
                "rows_that_would_proceed_under_a_ceiling": v["members"],
                "rows_leaving_ACCEPT": 0},
            "if_NON_BLOCKING": {
                "rank_ceiling": c.get("NON_BLOCKING", "UNMEASURED"),
                "rows_that_would_proceed_unconstrained": v["members"]},
            "if_EXPLANATORY": {
                "rank_ceiling": c.get("EXPLANATORY", "UNMEASURED"),
                "rows_that_would_proceed_unconstrained": v["members"],
                "same_ceiling_as_NON_BLOCKING":
                    ceil.get("non_blocking_and_explanatory_share_a_ceiling")},
            "CHOSEN": None,
        }
    return {"table": table,
            "chosen_count": sum(1 for v in table.values()
                                if v["CHOSEN"] is not None),
            "P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED": True,
            "why_empty": "الجدولُ يُملأ بالأثر، وخانةُ الاختيار تبقى "
                         "فارغةً — والإسنادُ حكمُ مالك.",
            "command": "python3 scripts/measure_b2.py"}


def guard(m1: dict, m2: dict, m3: dict, ceil: dict) -> dict:
    g: dict = {}
    g["G_NO_ASSIGNMENT"] = [
        k for k, v in (m3.get("table") or {}).items()
        if v.get("CHOSEN") is not None]
    g["G_EVERY_CLASS_MEASURED"] = [
        k for k in CLASSES if k not in (m2.get("per_class") or {})]
    g["G_M1_CLOSES"] = [] if m1.get("closes") else ["SPLIT_DOES_NOT_CLOSE"]
    # يفحص **القيمَ** لا الوعاء: قاموسٌ كلُّه UNMEASURED كان يمرّ.
    vals = (ceil.get("ceilings") or {})
    g["G_CEILINGS_QUERIED"] = (
        ["NOT_A_MAPPING"] if not isinstance(vals, dict) or not vals
        else [k for k, v in vals.items() if str(v).startswith("UNMEASURED")])
    g["G_HIDDEN_FORBIDDEN_NOT_ASSIGNABLE"] = (
        [] if "HIDDEN_FORBIDDEN" not in ASSIGNABLE else ["ASSIGNABLE"])
    return g


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/max")
    a = ap.parse_args()

    a1, a2, a3, a4 = rows(A1), rows(A2), rows(A3), rows(A4)
    ceil = ceilings()
    m1 = m1_split(a1, a3)
    m2 = m2_reach(a1, a2, a3, a4)
    m3 = m3_impact(m2, ceil, a3, a4)
    g = guard(m1, m2, m3, ceil)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "01_b2_measures.json").write_text(json.dumps(
        {"ceilings": ceil, "M1_tanween_split": m1, "M2_reach": m2,
         "M3_rank_impact": m3, "guards": g},
        ensure_ascii=False, indent=1), encoding="utf-8")

    pr, md = m1["proposed_discriminator"], m1["measured_discriminator"]
    print(f'M1  U_TANWEEN {m1["U_TANWEEN_total"]}')
    print(f'    المميِّزُ المقترَح: {pr["matches"]}/{pr["of"]} — '
          f'يشطر؟ {pr["discriminates"]}  ← خاصّةُ الصنف لا مميِّزَ داخلَه')
    print(f'    المميِّزُ المقيس:   على ألفٍ صامتة {md["on_silent_alif"]} · '
          f'الباقي {md["rest"]} · يقفل {md["closes"]}')
    print(f'    ومنها تبلغ الثالثَ ACCEPT {md["of_those_accepted_at_axis3"]}')
    print("M2  الصنف                    أعضاء  ⟶٢    ⟶٣    ⟶٤")
    for k, v in m2["per_class"].items():
        print(f'    {k:24} {v["members"]:>5}  {v["reaches_axis2"]:>5} '
              f'{v["reaches_axis3"]:>5} {v["reaches_axis4"]:>5}')
    print(f'M3  الاختياراتُ المملوءة {m3["chosen_count"]}  '
          f'(يجب أن تكون صفرًا)')
    print(f'CEIL {ceil.get("distinct_rank_outcomes")}  · '
          f'NON_BLOCKING==EXPLANATORY '
          f'{ceil.get("non_blocking_and_explanatory_share_a_ceiling")}')
    for k, v in g.items():
        print(f'  {k:36} {v if v else "PASS"}')
    print(f"→ {out}/01_b2_measures.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
