#!/usr/bin/env python3
"""`A1` · `A2` · `A3` · `A4` — القياسُ البعديّ، بجردٍ ثلاثيٍّ يقفل.

    PYTHONPATH=src .venv-taaqol/bin/python scripts/measure_tanween_after.py

**والجردُ ثلاثةٌ لا اثنان**، والفرقُ بين أوّلِه وثانيه جوهريّ:

* **يتغيّر** — تعديلُ سلوك.
* **يُصادَق كما هو** — مصادقةٌ على سلوكٍ قائمٍ لم يكن مصادَقًا. لا يتغيّر
  منه صفٌّ واحد، ويُوسَم `RATIFIED_UNCHANGED` لا `MODIFIED`. وخلطُه
  بالأوّل في عدٍّ واحدٍ يُوهم عملًا لم يقع.
* **موقوف** — لا يُنفَّذ منه صفٌّ واحد، ولو بدا حكمُه بيّنًا.

**والمقارنةُ صفًّا صفًّا**، لا بالعدد: صفٌّ تغيّر خارجَ النطاق يُسمّى
بموضعه ونصَّيه. ومقارنةٌ بالعدد وحدَه تمرّ على تغييرَين متعادلَين.
"""
from __future__ import annotations

import argparse
import collections
import csv
import hashlib
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import measure_tanween as MT  # noqa: E402

#: نقطةُ الرجوع — **داخلَ الشجرة**، أو حيث يقول المتغيّر.
#:
#: كانت `/home/claude/probe` مكتوبًا في الشيفرة: مسارٌ مطلقٌ في بيتِ
#: حاويةٍ زائلة. ولازمُه أنّ «قبلُ» — وهي الطرفُ الذي يُقاس به أثرُ
#: التغيير كلِّه — تموت بموت الحاوية، ولا تُقرأ على آلةٍ أخرى بحال.
#: وهذا `B11` بعينه (المسارات المطلقة ⟶ متغيّرات بيئة) في موضعٍ فاته.
#:
#: والحارسُ لم يكن يسكت: كان يرفع `NO_ROLLBACK_SNAPSHOT` — فالعيبُ في
#: الحمل لا في الإبلاغ.
BEFORE_DIR = Path(os.environ.get("ASLOT_TANWEEN_BEFORE",
                                 ROOT / ".tanween_before"))
A1 = ROOT / "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv"
A2 = ROOT / "reports/axis_2_mabniyat_operators/AXIS_2_TOKENS.csv"
A3 = ROOT / "reports/axis_3_syllables/AXIS_3_SYLLABLES.csv"
A4 = ROOT / "reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv"
WORDS = ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv"

#: الجردُ الثلاثيُّ — مشتقٌّ من الأزواج، لا مكتوبٌ بعددٍ.
CHANGES = {("FATH", "ALIF"), ("FATH", "ALIF_MAQSURA"),
           ("FATH", "TAA_MARBUTA")}
RATIFIED_UNCHANGED = {("DAMM", "SOUND_LETTER"), ("KASR", "SOUND_LETTER"),
                      ("KASR", "HAMZA"), ("DAMM", "HAMZA")}
PENDING = {"P1": {("FATH", "HAMZA")},
           "P2": {("DAMM", "TAA_MARBUTA"), ("KASR", "TAA_MARBUTA")}}
#: `P3` ليس زوجًا بل **موقعًا**: تنوينُ فتحٍ على ألفٍ حاملُه ليس آخِرَ
#: الرسم. فيُفرَز بالموقع لا بالزوج، وإلا ابتلعه `FATH×ALIF`.
P3_POSITION = "ON_PENULT_FINAL_BARE"

#: **أعمدةُ وسمٍ موضعيّ لا حكم.** `DW:n` رقمٌ تسلسليٌّ يُسنَد بترتيب
#: المرور على سطوح السجلّ (`axis2_registry.py:205`)، فتغيّرُ سطحٍ واحدٍ
#: يُعيد ترقيمَ ما بعده. فحركتُه ليست تغيُّرَ حكم — لكنّها **عيبٌ في
#: ذاته**: مُعرِّفٌ يُعيد تسميةَ نفسِه ليس مُعرِّفًا. ويُرفع إلى المالك
#: بندًا مستقلًّا، ولا يُطوى بأنّه «وسمٌ فقط».
POSITIONAL_LABEL_COLUMNS = {"Matched_Entry_Ids"}


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def key(r: dict) -> tuple:
    return (r["Sura_No"], r["Verse_No"], r["Word_No"])


def rows(p: Path) -> dict:
    with p.open(encoding="utf-8", newline="") as fh:
        return {key(r): r for r in csv.DictReader(fh)}


def before_path(rel: str) -> Path:
    return BEFORE_DIR / rel.replace("/", "_")


def bucket_of(word: str) -> str:
    """يردّ اسمَ الصنف الثلاثيّ لكلمةٍ — أو `NOT_TANWEENED`."""
    c = MT.classify(word)
    if c is None or c.get("kind") == "UNCLASSIFIED_SHAPE":
        return "NOT_TANWEENED"
    pair = (c["kind"], c["shape"])
    if c["position"] == P3_POSITION:
        return "PENDING_P3"
    if pair in CHANGES:
        return "CHANGES"
    if pair in RATIFIED_UNCHANGED:
        return "RATIFIED_UNCHANGED"
    for tag, pairs in PENDING.items():
        if pair in pairs:
            return f"PENDING_{tag}"
    return "ORPHAN"


# ───────────────────────────────────────────────── A1 · الأثرُ محدودًا
def a1() -> dict:
    old, new = rows(before_path(str(A1.relative_to(ROOT)))), rows(A1)
    src = rows(WORDS)
    tally: collections.Counter = collections.Counter()
    changed_by_bucket: collections.Counter = collections.Counter()
    out_of_scope: list[dict] = []
    unchanged_in_scope: list[dict] = []

    for k, w in src.items():
        b = bucket_of(w["Word"])
        tally[b] += 1
        o, n = old.get(k), new.get(k)
        if o is None or n is None:
            continue
        moved = o != n
        if moved:
            changed_by_bucket[b] += 1
            if b != "CHANGES":
                out_of_scope.append({
                    "position": ":".join(k), "word": w["Word"], "bucket": b,
                    "was": o.get("Normalized_Word"),
                    "now": n.get("Normalized_Word")})
        elif b == "CHANGES":
            unchanged_in_scope.append({"position": ":".join(k),
                                       "word": w["Word"]})

    rows_changed = sum(1 for k in new if old.get(k) != new.get(k))
    expected = tally["CHANGES"]
    pending_total = sum(v for b, v in tally.items() if b.startswith("PENDING"))
    return {
        "buckets": dict(sorted(tally.items())),
        "changes_expected": expected,
        "ratified_unchanged": tally["RATIFIED_UNCHANGED"],
        "pending_total": pending_total,
        "pending_split": {b: v for b, v in sorted(tally.items())
                          if b.startswith("PENDING")},
        "three_way_sum": expected + tally["RATIFIED_UNCHANGED"]
        + pending_total,
        "tanweened_total": sum(v for b, v in tally.items()
                               if b != "NOT_TANWEENED"),
        "orphans": tally.get("ORPHAN", 0),
        "rows_changed_measured": rows_changed,
        "rows_changed_denominator": "صفوفُ AXIS_1 المختلفةُ عن نقطة الرجوع",
        "changed_by_bucket": dict(sorted(changed_by_bucket.items())),
        "out_of_scope_changes": out_of_scope,
        "in_scope_not_changed": unchanged_in_scope,
        "command": "PYTHONPATH=src .venv-taaqol/bin/python "
                   "scripts/measure_tanween_after.py",
    }


# ──────────────────────────────────────────── A2 · المحاور الثلاثة
def transition(path: Path, col: str) -> dict:
    old, new = rows(before_path(str(path.relative_to(ROOT)))), rows(path)
    grid: collections.Counter = collections.Counter()
    for k, n in new.items():
        o = old.get(k)
        if o is None:
            grid[("ABSENT_BEFORE", n.get(col, ""))] += 1
            continue
        grid[(o.get(col, ""), n.get(col, ""))] += 1
    for k in old:
        if k not in new:
            grid[(old[k].get(col, ""), "ABSENT_AFTER")] += 1
    moved = sum(v for (a, b), v in grid.items() if a != b)
    return {
        "column": col,
        "matrix": {f"{a}⟶{b}": v for (a, b), v in sorted(grid.items())},
        "rows": sum(grid.values()),
        "rows_before": len(old), "rows_after": len(new),
        "moved": moved,
        "closes": sum(grid.values()) == max(len(old), len(new)),
        "before": dict(collections.Counter(
            o.get(col, "") for o in old.values())),
        "after": dict(collections.Counter(
            n.get(col, "") for n in new.values())),
    }


def columns_moved(path: Path) -> dict:
    """كلُّ عمودٍ وكم صفًّا تحرّك فيه — فحركةٌ في عمودٍ لا تُخفيها سكونُ آخر."""
    old, new = rows(before_path(str(path.relative_to(ROOT)))), rows(path)
    cols = list(next(iter(new.values())).keys()) if new else []
    out = {}
    for c in cols:
        n = sum(1 for k in new if (old.get(k) or {}).get(c) != new[k].get(c))
        if n:
            out[c] = n
    return {"moved_columns": out,
            "untouched_columns": [c for c in cols if c not in out],
            "denominator": len(new),
            "note": "عمودُ الحكم قد يسكن وتتحرّك البنيةُ تحته — "
                    "و«تحرّك 0» على عمودٍ واحدٍ ليس خبرًا عن المحور."}


def bounded_across_axes() -> dict:
    """`G_CHANGE_IS_BOUNDED` على المحاور الأربعة، لا على الأوّل وحدَه.

    فحدُّ التغيير لا يُثبَت في المحور الذي وقع فيه فقط: صفٌّ خارج النطاق
    قد يتحرّك في محورٍ لاحقٍ بأثرٍ غيرِ مقصود، والفحصُ على محورٍ واحدٍ
    يمرّ عليه.
    """
    src = rows(WORDS)
    out = {}
    for axis, path in (("axis1", A1), ("axis2", A2), ("axis3", A3),
                       ("axis4", A4)):
        old, new = rows(before_path(str(path.relative_to(ROOT)))), rows(path)
        moved = {k for k in new if (old.get(k) or {}) != new[k]}
        by: collections.Counter = collections.Counter()
        offenders = []
        oos_cols: collections.Counter = collections.Counter()
        # **الأمثلةُ تُرتَّب قبل أن تُقتطع.** كان المرورُ على `moved`
        # وهي مجموعة، فترتيبُها ترتيبُ التلبيد ويتغيّر بتغيّر
        # `PYTHONHASHSEED` — أي في كلّ تشغيلٍ جديد. فالأعدادُ كانت ثابتةً
        # (تُشتقّ من المجموعة كلِّها) و**العشرةُ المسمّاةُ تتبدّل**: مثالٌ
        # يُساق شاهدًا ولا يجده القارئُ حين يُعيد التشغيل ليس شاهدًا.
        # واصطاده مقابلةُ الشجرتين — لا حارسٌ.
        for k in sorted(moved):
            w = src.get(k)
            b = bucket_of(w["Word"]) if w else "NOT_IN_CORPUS"
            by[b] += 1
            if b == "CHANGES":
                continue
            cols = sorted(c for c in new[k]
                          if (old.get(k) or {}).get(c) != new[k].get(c))
            for c in cols:
                oos_cols[c] += 1
            if len(offenders) < 10:
                offenders.append({"position": ":".join(k),
                                  "word": (w or {}).get("Word"), "bucket": b,
                                  "columns": cols,
                                  "was": {c: (old.get(k) or {}).get(c)
                                          for c in cols},
                                  "now": {c: new[k].get(c) for c in cols}})
        oos = sum(v for b, v in by.items() if b != "CHANGES")
        judging = sorted(set(oos_cols) - POSITIONAL_LABEL_COLUMNS)
        out[axis] = {"rows_moved": len(moved),
                     "by_bucket": dict(sorted(by.items())),
                     "out_of_scope": oos,
                     "out_of_scope_columns": dict(sorted(oos_cols.items())),
                     "out_of_scope_judging_columns": judging,
                     "label_only": bool(oos) and not judging,
                     "named": offenders,
                     "denominator": len(new)}
    return out


def a3_extra_consonant() -> dict:
    """`B3` — أزال الإصلاحُ الصامتَ الزائد؟ يُقاس ولا يُدَّعى.

    الصامتُ الزائدُ هو الألفُ الساكنةُ التي كانت تُصدَر عن حاملِ تنوين
    الفتح. ويُقاس بمقابلةِ عدد الوحدات في المحور الثالث قبلَ وبعدُ على
    صفوف `FATH×ALIF` وحدَها.
    """
    old, new = rows(before_path(str(A3.relative_to(ROOT)))), rows(A3)
    src = rows(WORDS)
    scope = [k for k, w in src.items() if bucket_of(w["Word"]) == "CHANGES"]
    def cons(r):
        v = (r or {}).get("Consonant_Count", "")
        return int(v) if str(v).lstrip("-").isdigit() else None
    dropped = same = 0
    delta_total = 0
    per: collections.Counter = collections.Counter()
    for k in scope:
        a, b = cons(old.get(k)), cons(new.get(k))
        if a is None or b is None:
            continue
        d = b - a
        delta_total += d
        per[d] += 1
        if d < 0:
            dropped += 1
        elif d == 0:
            same += 1
    v_old = collections.Counter(old[k].get("Verdict") for k in scope
                                if k in old)
    v_new = collections.Counter(new[k].get("Verdict") for k in scope
                                if k in new)
    # الفرقُ يُشتقّ ولا يُلاحَظ: ٣٬١٥٢ = ٣٬٠٥٩ ألفًا + ٩٣ مقصورة. والتاءُ
    # المربوطة (٥٠٧) تنقلب ولا تُحذف، فلا ينقص بها صامت — وهذا هو
    # `G_TWO_MECHANISMS` ظاهرًا في العدد.
    src_b = collections.Counter()
    for k in scope:
        c = MT.classify(src[k]["Word"])
        src_b[(c["kind"], c["shape"])] += 1
    delete_pairs = {("FATH", "ALIF"), ("FATH", "ALIF_MAQSURA")}
    expected_drop = sum(v for kk, v in src_b.items() if kk in delete_pairs)
    return {
        "scope": len(scope),
        "scope_denominator": "صفوفُ الأشكال الثلاثة المتغيّرة",
        "scope_split": {f"{a}×{b}": v for (a, b), v in sorted(src_b.items())},
        "expected_drop_derived": expected_drop,
        "expected_drop_arithmetic": " + ".join(
            f"{a}×{b}={v}" for (a, b), v in sorted(src_b.items())
            if (a, b) in delete_pairs) + f" = {expected_drop}",
        "drop_matches_derivation": None,
        "consonants_dropped_in": dropped,
        "consonants_unchanged_in": same,
        "consonant_delta_total": delta_total,
        "delta_histogram": dict(sorted(per.items())),
        "axis3_verdict_before": dict(v_old),
        "axis3_verdict_after": dict(v_new),
        "left_accept": v_old.get("ACCEPT", 0) - v_new.get("ACCEPT", 0),
        "closed": None,
        "closed_note": "لا يُقال «B3 أُغلق» — الحكمُ للمالك بعد قراءة "
                       "هذه الأعداد. والأداةُ تقيس ولا تقفل.",
        "what_moved": "الصامتُ الزائدُ زال · والحكمُ لم يتحرّك: صفرٌ خرج "
                      "من ACCEPT. وهما خبران لا خبرٌ واحد.",
    }


def a4_u_tanween() -> dict:
    """`B2` — كم صفًّا يرفع `U_TANWEEN` بعد التطبيق؟ يُقاس ويُعرض."""
    old, new = rows(before_path(str(A1.relative_to(ROOT)))), rows(A1)
    def carries(d):
        return sum(1 for r in d.values()
                   if "U_TANWEEN" in (r.get("Owner_Decision_Classes") or "")
                   .split("|"))
    return {
        "u_tanween_words_before": carries(old),
        "u_tanween_words_after": carries(new),
        "denominator": "كلماتٌ يرفع فيها الصنف — لا أحداث",
        "still_raised": carries(new),
        "verdict": None,
        "verdict_note": "لا يُحذف الصنفُ ولا يُبقى بحكم الأداة. "
                        "OWNER_PENDING — وهو السؤالُ الرابع.",
        "status": "OWNER_PENDING",
        "decided_by_tool": False,
    }


# ───────────────────────────────────────────────────────────── الحرّاس
def guards(a: dict, dn: dict, b3: dict) -> list[dict]:
    g = [{
        "guard": "G_CHANGE_IS_BOUNDED",
        "denominator": a["tanweened_total"],
        "expected": a["changes_expected"],
        "measured": a["rows_changed_measured"],
        "out_of_scope_changes": len(a["out_of_scope_changes"]),
        "named": a["out_of_scope_changes"][:10],
        "passes": (a["rows_changed_measured"] == a["changes_expected"]
                   and not a["out_of_scope_changes"]),
        "note": "المقارنةُ صفًّا صفًّا لا بالعدد: تغييران متعادلان "
                "يمرّان على العدّ ولا يمرّان على المقابلة.",
    }, {
        "guard": "G_CHANGE_IS_BOUNDED_ALL_AXES",
        "denominator": sum(v["denominator"] for v in a["across_axes"].values()),
        "per_axis": {ax: {"moved": v["rows_moved"],
                          "out_of_scope": v["out_of_scope"]}
                     for ax, v in a["across_axes"].items()},
        "named": [x for v in a["across_axes"].values() for x in v["named"]],
        "out_of_scope_columns": {ax: v["out_of_scope_columns"]
                                 for ax, v in a["across_axes"].items()
                                 if v["out_of_scope_columns"]},
        "judging_columns_moved": {ax: v["out_of_scope_judging_columns"]
                                  for ax, v in a["across_axes"].items()
                                  if v["out_of_scope_judging_columns"]},
        "passes": all(not v["out_of_scope_judging_columns"]
                      for v in a["across_axes"].values()),
        "note": "حدُّ التغيير يُثبَت في المحاور الأربعة — لا في الأوّل "
                "وحدَه. ولا يُعدّ خرقًا إلا تحرُّكُ عمودٍ **يحكم**؛ "
                "والوسمُ الموضعيُّ يُسمّى ويُرفع بندًا مستقلًّا.",
    }, {
        "guard": "G_RATIFIED_UNCHANGED",
        "denominator": a["ratified_unchanged"],
        "changed": a["changed_by_bucket"].get("RATIFIED_UNCHANGED", 0),
        "label": "RATIFIED_UNCHANGED — لا MODIFIED",
        "passes": not a["changed_by_bucket"].get("RATIFIED_UNCHANGED"),
        "note": "مصادقةٌ على سلوكٍ قائم — لا تُعدّ عملًا، ولا تُجمع مع "
                "المتغيّر في رقمٍ واحد.",
    }, {
        "guard": "G_PENDING_UNTOUCHED",
        "denominator": a["pending_total"],
        "split": a["pending_split"],
        "changed": sum(v for b, v in a["changed_by_bucket"].items()
                       if b.startswith("PENDING")),
        "passes": not any(b.startswith("PENDING")
                          for b in a["changed_by_bucket"]),
        "note": "لا يُنفَّذ منها صفٌّ واحد ولو بدا حكمُه بيّنًا.",
    }, {
        "guard": "G_THREE_WAY_CLOSES",
        "denominator": a["tanweened_total"],
        "arithmetic": f'{a["changes_expected"]} + {a["ratified_unchanged"]}'
                      f' + {a["pending_total"]} = {a["three_way_sum"]}',
        "orphans": a["orphans"],
        "passes": (a["three_way_sum"] == a["tanweened_total"]
                   and not a["orphans"]),
    }, {
        "guard": "G_NO_RULE_WIDENING",
        "denominator": 3,
        "table": sorted(f"{k}⟶{v}" for k, v in table_rows().items()),
        "passes": len(table_rows()) == 3,
        "note": "الجدولُ مغلقٌ بثلاثة أسطر — وزيادةٌ فيه هي التوسيعُ بعينه.",
    }, {
        "guard": "G_TWO_MECHANISMS",
        "denominator": 2,
        "mechanisms": sorted(set(table_rows().values())),
        "passes": sorted(set(table_rows().values())) ==
                  ["DELETE_CARRIER", "TURN_TO_OPEN_TAA"],
        "note": "الحذفُ والانقلابُ إجراءان متمايزان في الشيفرة.",
    }]
    g.append({
        "guard": "G_DROP_IS_DERIVED",
        "denominator": b3["scope"],
        "measured": b3["consonants_dropped_in"],
        "derived": b3["expected_drop_derived"],
        "arithmetic": b3["expected_drop_arithmetic"],
        "passes": bool(b3["drop_matches_derivation"]),
        "note": "الصوامتُ الناقصةُ = صفوفُ الحذف بعينها. والتاءُ تنقلب "
                "ولا تُحذف، فلا تُعدّ فيها — وهو الفرقُ بين الإجراءَين "
                "ظاهرًا في العدد.",
    })
    for axis, d in dn.items():
        g.append({"guard": f"G_MATRIX_CLOSES[{axis}]",
                  "denominator": d["rows"],
                  "rows_before": d["rows_before"],
                  "rows_after": d["rows_after"],
                  "moved": d["moved"],
                  "passes": d["closes"]})
    return g


def table_rows() -> dict:
    from aslot.axes.axis1_normalization import TANWEEN_UNFOLD_TABLE
    return dict(TANWEEN_UNFOLD_TABLE)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/tanween")
    a = ap.parse_args()

    if not before_path(str(A1.relative_to(ROOT))).is_file():
        raise Blocked("OWNER_ALERT: NO_ROLLBACK_SNAPSHOT — نقطةُ الرجوع "
                      "غائبةٌ، ولا يُقاس فرقٌ بلا «قبلُ»")

    res = a1()
    res["across_axes"] = bounded_across_axes()
    # عمودُ الحكم وحدَه يقول «تحرّك 0» فيُقرأ «لم يقع شيءٌ في المحاور»،
    # وهو باطل: الحركةُ وقعت في أعمدةٍ أخرى. فتُمسَح الأعمدةُ كلُّها،
    # وتُبنى مصفوفةُ الحكم إلى جانبها لا بدلًا منها.
    dn = {"axis2": transition(A2, "Eligibility"),
          "axis3": transition(A3, "Verdict"),
          "axis4": transition(A4, "Verdict")}
    for axis, path in (("axis2", A2), ("axis3", A3), ("axis4", A4)):
        dn[axis]["columns_moved"] = columns_moved(path)
    b3 = a3_extra_consonant()
    b3["drop_matches_derivation"] = (
        b3["consonants_dropped_in"] == b3["expected_drop_derived"])
    b2 = a4_u_tanween()
    g = guards(res, dn, b3)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "02_after.json").write_text(json.dumps(
        {"task": "A1_BOUNDED_CHANGE", **res,
         "source_sha256": {
             rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
             for rel in ("src/aslot/axes/axis1_normalization.py",
                         "src/aslot/constants.py")},
         "guards": g, "all_guards_pass": all(x["passes"] for x in g)},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "03_downstream.json").write_text(json.dumps(
        {"task": "A2_DOWNSTREAM", **dn}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (out / "04_b2_b3.json").write_text(json.dumps(
        {"task": "A3_A4", "B3": b3, "B2": b2}, ensure_ascii=False, indent=1),
        encoding="utf-8")

    print(f'A1 يتغيّر {res["changes_expected"]} · مصادَقٌ كما هو '
          f'{res["ratified_unchanged"]} · موقوفٌ {res["pending_total"]} '
          f'{res["pending_split"]}')
    print(f'   المجموع {res["three_way_sum"]} / المنوَّن '
          f'{res["tanweened_total"]} · يتامى {res["orphans"]}')
    print(f'   المقيسُ متغيّرًا في المحور الأوّل: '
          f'{res["rows_changed_measured"]} · بالصنف '
          f'{res["changed_by_bucket"]}')
    for axis, d in dn.items():
        print(f'A2 {axis:6} {d["column"]:14} تحرّك {d["moved"]:6} · '
              f'يقفل {d["closes"]}')
        for kk, v in sorted(d["matrix"].items(), key=lambda kv: -kv[1])[:4]:
            if kk.split("⟶")[0] != kk.split("⟶")[1]:
                print(f'          {kk} {v}')
        cm = d["columns_moved"]["moved_columns"]
        print(f'          أعمدةٌ تحرّكت: '
              f'{" · ".join(f"{k}={v}" for k, v in sorted(cm.items()))}'
              or "          لا عمود")
    print(f'A3 B3 — نطاقٌ {b3["scope"]} · صفوفٌ نقص صامتُها '
          f'{b3["consonants_dropped_in"]} · مجموعُ الفرق '
          f'{b3["consonant_delta_total"]} · خرج من ACCEPT '
          f'{b3["left_accept"]}  ⟶ لا يُقال «أُغلق»')
    print(f'A4 B2 — U_TANWEEN قبلُ {b2["u_tanween_words_before"]} · '
          f'بعدُ {b2["u_tanween_words_after"]} · OWNER_PENDING')
    for x in g:
        print(f'   {x["guard"]:26} {"PASS" if x["passes"] else "FALLS"} '
              f'/{x["denominator"]}')
    if not all(x["passes"] for x in g):
        raise Blocked("GUARD_FALLS — ويُوقَف كلُّ شيء")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
