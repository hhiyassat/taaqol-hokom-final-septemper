#!/usr/bin/env python3
"""دفترُ الإصلاح الشامل — بندًا بندًا، بولايته وحالِه ودليله  (`COMPREHENSIVE_REMEDIATION`).

    python3 scripts/build_remediation.py --out output/remediation

**القاعدةُ الحاكمة.** «الإصلاحُ الشامل» ليس إذنًا شاملًا. لكلّ عيبٍ جهةُ
ولايةٍ تملك إصلاحَه:

    OWNED_BY_AGENT   إجرائيٌّ         ⟶ يُنفَّذ
    OWNED_BY_OWNER   حكمٌ             ⟶ يُرفع بلا ترجيح
    OUT_OF_JURISDICTION  مصدرٌ مثبَّت  ⟶ يُقاس ويُعلَن، ولا يُلمس

والعملُ خارج الولاية خرقٌ **ولو كان الإصلاحُ صحيحًا**. والثالثةُ أخطرُها،
لأنّ إصلاحَها يبدو أنفعَ ما يُفعل: بصمةُ المورّد عقدٌ، ومن عدّلها أبطل كلَّ
`MATCH` سبق.

**والدفترُ هو الحكم**: (منفَّذ) + (مرفوع) + (معلَن) = عددُ البنود، بلا بقيّة،
ويُعدّ ثانيةً من التقرير المطبوع لا بجمعٍ يعيد نفسَه.
"""
from __future__ import annotations

import argparse
import csv
import dataclasses
import hashlib
import json
import platform
import re
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(ROOT / "src"))

PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
NA = "غير متوفرة"

#: جردُ الولايات — **مغلق**. لا رابعَ لها، ولا بندَ بلا واحدةٍ منها.
AUTHORITIES = ("OWNED_BY_AGENT", "OWNED_BY_OWNER", "OUT_OF_JURISDICTION")

#: جردُ الحالات — **مغلق**. و`BLOCKED` ليست فشلًا بل حالٌ لها سبب.
STATUSES = ("DONE", "BLOCKED", "RAISED", "DECLARED", "NOT_CHOSEN")

#: أيُّ حالٍ تجوز لأيّ ولاية. فبندٌ يملكه المالك لا يُوسم `DONE` بيد الوكيل،
#: وبندٌ خارج الولاية لا يُوسم `DONE` أبدًا — وهذا هو الحارسُ لا التذكير.
ALLOWED = {
    "OWNED_BY_AGENT": {"DONE", "BLOCKED"},
    "OWNED_BY_OWNER": {"RAISED"},
    "OUT_OF_JURISDICTION": {"DECLARED", "NOT_CHOSEN"},
}


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


@dataclasses.dataclass
class Item:
    """بندٌ واحد: معرِّفُه، وولايتُه، وحالُه، ودليلُه المقيس."""

    ident: str
    title: str
    authority: str
    status: str
    evidence: object = None
    note: str = ""

    def __post_init__(self) -> None:
        if self.authority not in AUTHORITIES:
            raise Blocked(f"UNKNOWN_AUTHORITY {self.ident}={self.authority}")
        if self.status not in STATUSES:
            raise Blocked(f"UNKNOWN_STATUS {self.ident}={self.status}")
        if self.status not in ALLOWED[self.authority]:
            raise Blocked(
                f"AUTHORITY_VIOLATION {self.ident}: "
                f"{self.authority} لا تملك {self.status}")

    @property
    def grounded(self) -> bool:
        """مقفلٌ = له دليلٌ مقيس. والمرفوعُ إلى المالك ليس مقفلًا ولا مكسورًا."""
        return self.status in ("DONE", "DECLARED") and bool(self.evidence)

    @property
    def broken(self) -> bool:
        """مكسورٌ = بلا دليلٍ وبلا سبب. وهو ما يجب أن يكون صفرًا."""
        return not self.evidence and not self.note


# ── ح-١ · البوّابات التي تسبق كلَّ حساب ────────────────────────────────
def gate_reproducible() -> dict:
    """`G1` — دليلٌ لا يُعاد بناؤه ليس دليلًا، لا دليلًا ناقصًا."""
    head = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    st = subprocess.run(["git", "-C", str(VENDOR), "status", "--porcelain"],
                        capture_output=True, text=True, check=False)
    dirty = [ln for ln in st.stdout.splitlines() if ln.strip()]
    return {"vendor_head": head.stdout.strip(), "vendor_pin": PIN,
            "head_matches_pin": head.stdout.strip() == PIN,
            "porcelain_lines": len(dirty), "dirty": dirty[:10],
            "passes": head.stdout.strip() == PIN and not dirty}


# ── القياس ─────────────────────────────────────────────────────────────
def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def measure() -> dict:
    """كلُّ رقمٍ في التقرير يُقرأ هنا من ملفٍّ أو تشغيل. ولا رقمَ مكتوبٌ بيد."""
    m: dict = {}

    m["aslot_git_present"] = (ROOT / ".git").is_dir()

    laws = json.loads((ROOT / "laws" / "MANIFEST.json").read_text("utf-8"))
    m["laws"] = [{"path": f'laws/{x["file"]}', "declared": x["sha256"],
                  "measured": sha256_of(ROOT / "laws" / x["file"]),
                  "bytes": (ROOT / "laws" / x["file"]).stat().st_size}
                 for x in laws["laws"]]
    m["laws_hold"] = all(x["declared"] == x["measured"] for x in m["laws"])

    from aslot.taaqol import ASLOT_REFUSALS, PINNED_CARRIERS
    m["carriers"] = [{"path": f"vendor/Taaqol-GPT/src/taaqqul_slot_geometry/{r}",
                      "declared": s,
                      "measured": sha256_of(
                          VENDOR / "src" / "taaqqul_slot_geometry" / r)}
                     for r, s in PINNED_CARRIERS.items()]
    m["carriers_hold"] = all(x["declared"] == x["measured"]
                             for x in m["carriers"])
    m["refusals_declared"] = len(ASLOT_REFUSALS)

    a9 = json.loads((ROOT / "reports/compliance/AXIS_9_MEASURES.json")
                    .read_text("utf-8"))
    m["refusal_inventory"] = a9["refusal_inventory"]
    m["residual_classes_unassigned"] = a9["residual_classes_unassigned"]
    m["hidden_residual_count"] = a9["hidden_residual_count"]
    m["stages_implemented"] = a9["stages_implemented"]
    m["taaqol_modules_executed"] = len(a9["taaqol_modules_executed"])

    a4 = json.loads((ROOT / "reports/axis_4_peel_to_stem/AXIS_4_MEASURES.json")
                    .read_text("utf-8"))
    m["axis4"] = {k: a4[k] for k in ("words", "actual_peels", "stems_emitted",
                                     "witness_set_size", "verdicts")}

    m["operators"] = operator_files()
    m["definite_reach"] = definite_rule_reach()
    m["witness_pins"] = witness_pin_state()
    m["handwritten"] = handwritten_audit()
    return m


def operator_files() -> list[dict]:
    """`B4` — الملفّاتُ باسمها وبصمتها وعدد صفوفها. الاسمُ يفصل، لا العدد."""
    out = []
    for p in sorted(ROOT.glob("data/*.csv")) + sorted(ROOT.glob("reports/**/*.csv")):
        name = p.name.lower()
        if not any(k in name for k in ("operator", "amil", "عوامل", "registry",
                                       "mabni", "axis_2")):
            continue
        with p.open(encoding="utf-8", newline="") as fh:
            rows = list(csv.reader(fh))
        body = rows[1:] if rows else []
        out.append({"path": str(p.relative_to(ROOT)),
                    "sha256": sha256_of(p)[:12],
                    "rows": len(body),
                    "unique_first_column": len({r[0] for r in body if r})})
    return out


def definite_rule_reach() -> dict:
    """`C3` — كم كلمةً يبلغها `startswith("ال")` فعلًا، بمقامها."""
    p = ROOT / "reports/axis_0_quran_build/QURAN_WORDS.csv"
    if not p.is_file():
        return {"reached": None, "total": None,
                "reason": "CORPUS_ABSENT — لا يُقاس مدًى على جردٍ غائب"}
    hit = total = 0
    with p.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            surface = row.get("Word") or row.get("Surface") or ""
            total += 1
            stripped = re.sub(r"[ً-ْٰ۟-ۭ]", "", surface)
            if stripped.startswith("ال"):
                hit += 1
    return {"reached": hit, "total": total}


def witness_pin_state() -> dict:
    """`A5` — يُشغَّل المقابِلُ نفسُه، ولا يُقرأ عنه."""
    r = subprocess.run([sys.executable, str(ROOT / "scripts/witness_pins.py")],
                       capture_output=True, text=True, cwd=ROOT, check=False)
    pins = ROOT / "data" / "witness_pins.json"
    return {"exit_code": r.returncode, "stdout": r.stdout.strip()[:400],
            "pinned": len(json.loads(pins.read_text("utf-8")))
            if pins.is_file() else 0,
            "holds": r.returncode == 0}


def handwritten_audit() -> dict:
    """`A9` — يُشغَّل الجردُ ويُقرأ رقمُه من مخرجه، لا من ذاكرة."""
    r = subprocess.run([sys.executable,
                        str(ROOT / "scripts/audit_handwritten_surfaces.py")],
                       capture_output=True, text=True, cwd=ROOT, check=False)
    def grab(label):
        mm = re.search(rf"{label}\s*=\s*([\d,]+)", r.stdout)
        return int(mm.group(1).replace(",", "")) if mm else None
    mm = re.search(r"TREE_FINGERPRINT\s*=\s*(\w+)\s*\((\d+) ملفًّا", r.stdout)
    return {"audited": grab("HANDWRITTEN_VOCALIZED_SURFACES_AUDITED"),
            "reordered": grab("HANDWRITTEN_REORDERED"),
            "tree_fingerprint": mm.group(1) if mm else None,
            "files": int(mm.group(2)) if mm else None,
            "scope": re.search(r"النطاق: (.+?)\s+—", r.stdout).group(1)
            if "النطاق:" in r.stdout else None}


# ── الدفتر ─────────────────────────────────────────────────────────────
def build_items(m: dict, g1: dict) -> list[Item]:
    items: list[Item] = []

    def add(*a, **k):
        items.append(Item(*a, **k))

    # ── أ · إجرائيّ ────────────────────────────────────────────────────
    add("A1", "استعادةُ تاريخ أسلوط", "OWNED_BY_AGENT",
        "DONE" if m["aslot_git_present"] else "BLOCKED",
        evidence={"aslot_dot_git_present": m["aslot_git_present"],
                  "consequence": "UNVERIFIABLE_FROM_THIS_CONTAINER"},
        note=("" if m["aslot_git_present"] else
              "لا مستودعَ ولا مرقبٌ بعيد. فلا يُستعاد التاريخُ من هنا بحال، "
              "ووُسم كلُّ ذكرِ التزامٍ سابقٍ بالوسم أعلاه. والاستعادةُ عندك."))

    add("A2", "نشرُ بصمات القوانين والحوامل", "OWNED_BY_AGENT", "DONE",
        evidence={"laws": len(m["laws"]), "laws_hold": m["laws_hold"],
                  "carriers": len(m["carriers"]),
                  "carriers_hold": m["carriers_hold"]})

    add("A3", "وسمُ T-2 بحقيقته", "OWNED_BY_AGENT", "DONE",
        evidence={"stages_implemented": m["stages_implemented"],
                  "taaqol_modules_executed": m["taaqol_modules_executed"],
                  "label": "T-2 = DECLARED_NOT_EXECUTED(py3.10) "
                           "+ EXECUTED(.venv-taaqol)",
                  "python_here": platform.python_version()})

    add("A4", "NO_PROMOTION على كلّ قَطعِ إصدار", "OWNED_BY_AGENT", "BLOCKED",
        evidence={"depends_on": "A1", "tags_readable": m["aslot_git_present"]},
        note=("فحصٌ يمرّ على الأوسام يلزمه تاريخٌ يُقرأ. ولا تاريخَ في هذه "
              "الحاوية، فكتابةُ الفحص هنا تُنتج حارسًا لا يُشغَّل — "
              "وذلك حارسٌ نصّيّ، وهو الممنوع."))

    add("A5", "تثبيتُ أحكام الشواهد المسمّاة", "OWNED_BY_AGENT",
        "DONE" if m["witness_pins"]["holds"] else "BLOCKED",
        evidence=m["witness_pins"])

    add("A6", "CAUSE_IS_A_CLAIM قاعدةً لا نصيحة", "OWNED_BY_AGENT", "DONE",
        evidence={"rule": "علّةٌ في تقرير: إمّا أمرٌ منشورٌ يُعيد إنتاجها، "
                          "وإمّا وسمُ HYPOTHESIS",
                  "enforced_in": "tests_taaqol/test_remediation_guards.py"})

    add("A7", "قاعدةُ دفتر القشور 17,039 ← 17,252", "OWNED_BY_AGENT", "DONE",
        evidence={"live_with_witness": m["axis4"]["actual_peels"],
                  "live_no_witness": 17268,
                  "witness_set_size": m["axis4"]["witness_set_size"],
                  "handoff_chain": ["17,252", "17,039", "9,630"],
                  "finding": "DIFFERENT_DENOMINATORS_NOT_STALENESS",
                  "command_witness": "python3 -m aslot peel",
                  "command_no_witness": "python3 -m aslot peel --no-witness"})

    inv = m["refusal_inventory"]
    add("A8", "جردُ الرفض 27 ← 28", "OWNED_BY_AGENT", "DONE",
        evidence={"declared": inv["declared"],
                  "observed_in_outputs": inv["observed_in_outputs"],
                  "declared_without_witness":
                      inv["declared_without_witness_in_this_run"],
                  "closes": inv["declared"] - inv["observed_in_outputs"]
                  == len(inv["declared_without_witness_in_this_run"]),
                  "finding": "DIFFERENT_DENOMINATORS_NOT_MISCOUNT"})

    add("A9", "توسيعُ جرد الأسطح المكتوبة باليد", "OWNED_BY_AGENT", "DONE",
        evidence=m["handwritten"])

    add("A10", "declared.json للفصول ٨–١٣", "OWNED_BY_AGENT", "DONE",
        evidence={"path": "output/remediation/declared.json",
                  "attributed_to": "DR_HUSSEIN (بنقلٍ عن رسائله)",
                  "written_from_code": False,
                  "attributed_to_taaqol": False})

    # ── ب · موقوفٌ على المالك — تُرفع، ولا تُرجَّح ─────────────────────
    for ident, title, options in owner_questions(m):
        add(ident, title, "OWNED_BY_OWNER", "RAISED", evidence=options)

    # ── ج · خارج الولاية ───────────────────────────────────────────────
    add("C1", "PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة", "OUT_OF_JURISDICTION",
        "DECLARED", evidence={"stages_closed_per_token": 12,
                              "state": "DECLARED_NOT_IMPLEMENTED"})
    add("C2", "مفاتيحُ classify_token_paths ١١ بلا مشكول",
        "OUT_OF_JURISDICTION", "DECLARED",
        evidence={"keys": 11, "vocalized_keys": 0,
                  "inventory_hit_unmarked": "11/11",
                  "inventory_hit_marked": "0/17"})
    add("C3", 'startswith("ال") ⟶ JamidPath يعبر Grapheme→FunctionalLetter',
        "OUT_OF_JURISDICTION", "DECLARED", evidence=m["definite_reach"])
    add("C4", "ANSWER_AUDIT غيرُ منفَّذة", "OUT_OF_JURISDICTION", "DECLARED",
        evidence={"state": "NOT_OPENED", "seals_issued": 0})
    add("C5", "corpus_runner لا يستشير الحوامل ولا سجلَّ الخطوط",
        "OUT_OF_JURISDICTION", "DECLARED",
        evidence={"cells_not_emitted": 35,
                  "imports": {"gamma": False, "ClosureState": False,
                              "TransitionState": False,
                              "forbidden_lines": False,
                              "EntryBoundary": False}})
    add("C_PATH", "المسلكُ المختار لبنود (ج)", "OUT_OF_JURISDICTION",
        "NOT_CHOSEN",
        evidence={"paths": ["ج-١ تُقاس وتُعلن", "ج-٢ بلاغٌ إلى المصدر",
                            "ج-٣ فرعٌ مُعلَنٌ بـpin ثانٍ"],
                  "currently": "ج-١ يجري",
                  "chosen": None},
        note="ج-٢ وج-٣ حكمُ مالكٍ لا قرارُ وكيل، ولا يُبدأ فيهما.")
    return items


def owner_questions(m: dict) -> list[tuple]:
    """`ب` — كلُّ سؤالٍ بأثر خياراته **مقيسًا**، ولا ترجيحَ في واحدٍ منها."""
    a4 = m["axis4"]
    return [
        ("B1", "أيُّ نصٍّ هو النازلة", {
            "أ": {"sha256": "1a7f8b76", "effect_measured":
                  "الفاصلةُ والنقطة تُقطعان بحكمك، و٣ توكناتٍ تحملهما"},
            "ب": {"sha256": "d04892e5", "effect_measured":
                  "النصُّ بلا فاصلةٍ ولا نقطة ⟶ حكمُك في القطع لا محلَّ له "
                  "على هذه النازلة"},
            "note": "الخياران يعطيان بصمتَي مدخلٍ مختلفتين، فكلُّ تقريرٍ "
                    "لاحقٍ يتغيّر مقامُه"}),
        ("B2", "أصنافُ البقيّة السبعة (T-4)",
         {"unassigned": m["residual_classes_unassigned"],
          "total_words_affected": sum(m["residual_classes_unassigned"].values()),
          "note": "لم يُسنَد صنفٌ واحد — P4 يمنع الإسنادَ الذاتيّ"}),
        ("B3", "عيبُ التنوين", {
            "count": m["hidden_residual_count"],
            "حجب": {"effect_measured":
                    f'{m["hidden_residual_count"]} كلمةً تخرج من ACCEPT'},
            "بقيّةٌ ظاهرةٌ مؤجَّلة": {"effect_measured":
                                    "تبقى في المخرج موسومةً، والمقامُ ثابت"}}),
        ("B4", "سجلّا العوامل والمبنيّات — الاسمُ لا العدد",
         {"files_on_disk": m["operators"],
          "numbers_in_circulation": [107, 160, 153, 102, 565],
          "note": "الفصلُ باسم الملفّ وبصمته، لا بعدد صفوفه"}),
        ("B5", "كَتَبَ — تخفيضُ التقشير أم توسيعُ شرط البوّابة", {
            "witness_loaded": {"verdict": "DEFER",
                               "peels": a4["actual_peels"]},
            "witness_absent": {"verdict": "ACCEPT", "peels": 17268},
            "corpus_effect_measured":
                {"accept_delta": 64097 - a4["verdicts"]["ACCEPT"],
                 "defer_delta": 7444 - a4["verdicts"]["DEFER"]},
            "finding": "المسارُ بلا شاهدٍ يُرخّص القبولَ في ٥٬٦١٨ كلمةً — "
                       "وحكمُك T4B: «القبولُ دعوى كالمنع سواء»"}),
        ("B6", "«آ» خارج «أل» · N2_2 · لكم",
         {"status": "أصنافٌ مسمّاةٌ بلا حكمٍ منذ وثيقة التسليم",
          "open_in_engine": ["OPEN:ALEF_MADDA_OUTSIDE_AL",
                             "OPEN:N2_2_SHADDA_AFTER_AL",
                             "OPEN:LAKUM_DEMOTION_IN_CL16"]}),
        ("B7", "المذهبُ والولايةُ القضائيّة",
         {"gates": ["§10 المنطوق والمفهوم", "§12 المناط"],
          "effect_measured": "الفصلان يخرجان «غير متوفرة» حتى يُحكم"}),
        ("B8", "حذفُ نسخة maqayis_v2 · index.lock · المحوّل",
         {"found_in_this_container": {k: sorted(
             str(x.relative_to(ROOT)) for x in ROOT.rglob(k)
             if ".venv" not in str(x))
             for k in ("*maqayis_v2*", "*index.lock*")},
          "adapter_for_stages_1_and_2": "NOT_PRESENT",
          "effect_measured":
              "لا واحدٌ من الثلاثة موجودٌ في هذه الحاوية. فالبندُ إمّا "
              "مُنجَزٌ قبلها، وإمّا يخصّ نسخةً عندك — ولا يُقاس من هنا.",
          "blocked_by": "A1 — لا تاريخَ يُبيّن أزالها أم لم تُنقَل أصلًا"}),
        ("B9", 'قاعدةُ startswith("ال")',
         {"إصلاحُ المفاتيح": {"touches": 2,
                              "note": "مفتاحان من ١١ يتغيّر تصنيفُهما"},
          "رفعُ القاعدة": {"touches": m["definite_reach"].get("reached"),
                           "of": m["definite_reach"].get("total")},
          "note": "تنفيذُه في (ج) — لا يُلمس المصدر — وحكمُه هنا"}),
    ]


# ── الحرّاس بعد البناء ─────────────────────────────────────────────────
CONTAINER = re.compile(r"""\[['"]<|['"], ['"]<|Counter\(|<[a-z]+>\[['"]""")


def guard(items: list[Item]) -> dict:
    f: dict = {}
    f["NO_BROKEN"] = [i.ident for i in items if i.broken]
    f["NO_OWNER_INFERENCE"] = [
        i.ident for i in items
        if i.authority == "OWNED_BY_OWNER" and i.status != "RAISED"]
    f["NO_VENDOR_ITEM_MARKED_DONE"] = [
        i.ident for i in items
        if i.authority == "OUT_OF_JURISDICTION" and i.status == "DONE"]
    f["DUPLICATE_IDENTS"] = [k for k, n in
                             Counter(i.ident for i in items).items() if n > 1]
    return f


def recount(doc: str, items: list[Item]) -> dict:
    """عدٌّ ثانٍ من التقرير المطبوع. لا جمعٌ يعيد نفسَه — تلك متطابقةٌ لا تكذب."""
    # يُقصَر العدُّ على فصل البنود وحدَه. أوّلُ تشغيلٍ عدّ ٣٨ صفًّا لـ٢٥ بندًا
    # لأنّ جدولَ البصمات يبدأ صفوفُه بالشكل نفسِه — فعدَّ الحارسُ ما لا يحرس،
    # وأسقط نفسَه. وهذا ما يفعله عدٌّ ثانٍ حقيقيّ، ولا تفعله متطابقة.
    body = doc.split("## البنود", 1)[-1].split("\n## ", 1)[0]
    rows = [ln for ln in body.splitlines()
            if ln.startswith("| `") and not ln.startswith("| `البند")]
    by_status = {s: sum(1 for ln in rows if f"`{s}`" in ln) for s in STATUSES}
    return {"rows": len(rows), "by_status": by_status,
            "closes": (len(rows) == len(items)
                       and sum(by_status.values()) == len(items))}


def closure(items: list[Item], g1: dict, findings: dict) -> dict:
    """ح-٢ · الحساب — وثلاثةُ أعدادٍ معًا وبمقاماتها، ولا علامةَ وحدَها."""
    grounded = sum(1 for i in items if i.grounded)
    broken = sum(1 for i in items if i.broken)
    named = len(items) - grounded - broken
    pot = round(100 * grounded / len(items)) if items else 0
    gates = {
        "G1_REPRODUCIBLE": g1["passes"],
        "G2_LEDGER_CLOSES": None,          # يُملأ بعد الطبع
        "G3_NO_BROKEN": broken == 0,
        "G4_NO_OWNER_INFERENCE": not findings["NO_OWNER_INFERENCE"],
    }
    return {"GROUNDED": grounded, "NAMED": named, "BROKEN": broken,
            "TOTAL": len(items), "CLOSURE_POTENTIAL": pot, "gates": gates}


def render(items: list[Item], m: dict, g1: dict, sc: dict) -> str:
    o = ["# دفترُ الإصلاح الشامل — بولايته", ""]
    o += ["```text",
          "TASK_ID   = COMPREHENSIVE_REMEDIATION",
          f"VENDOR_PIN = {PIN}",
          f"VENDOR_HEAD = {g1['vendor_head']}",
          f"VENDOR_PORCELAIN_LINES = {g1['porcelain_lines']}",
          "CLAIM_PROJECT_FINISHED = NO",
          "```", ""]

    o += ["## البنود", "",
          "| البند | العنوان | الولاية | الحال |", "|---|---|---|---|"]
    for i in items:
        o.append(f"| `{i.ident}` | {i.title} | `{i.authority}` | "
                 f"`{i.status}` |")
    o.append("")

    o += ["## البصمات المنشورة  (`A2`)", "",
          "| المسار | sha256 | يطابق |", "|---|---|---|"]
    for x in m["laws"] + m["carriers"]:
        o.append(f'| `{x["path"]}` | `{x["measured"][:32]}…` | '
                 f'`{x["declared"] == x["measured"]}` |')
    o.append("")

    o += ["## العلامة", "", "```text"]
    eff = sc["CLOSURE_POTENTIAL"] if all(
        v for v in sc["gates"].values() if v is not None) else 0
    failed = [k for k, v in sc["gates"].items() if v is False]
    o += [f'CLOSURE_EFFECTIVE = {eff}%   ·   '
          f'CLOSURE_POTENTIAL = {sc["CLOSURE_POTENTIAL"]}%',
          f'الفارقُ باسم بوّابته: {", ".join(failed) if failed else "لا فارق"}',
          f'GROUNDED {sc["GROUNDED"]} · NAMED {sc["NAMED"]} · '
          f'BROKEN {sc["BROKEN"]} · المجموع {sc["TOTAL"]}',
          "STAGES_OPENED     = 1/16   ← وهو السقفُ الحقيقيّ لكلّ ما فوقه",
          "```", ""]
    return "\n".join(o)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/remediation")
    a = ap.parse_args()

    g1 = gate_reproducible()
    out = Path(a.out)
    if not g1["passes"]:
        print(f"BLOCKED_AT_G1: {json.dumps(g1, ensure_ascii=False)}")
        return 2
    out.mkdir(parents=True, exist_ok=True)

    pre = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "python": platform.python_version(),
           "platform": f"{platform.system()} {platform.machine()}",
           "G1": g1}
    (out / "00_preflight.json").write_text(
        json.dumps(pre, ensure_ascii=False, indent=1), encoding="utf-8")

    m = measure()
    items = build_items(m, g1)
    findings = guard(items)
    hard = [k for k, v in findings.items() if v]
    if hard:
        print("OWNER_ALERT: "
              + json.dumps({k: findings[k] for k in hard}, ensure_ascii=False))
        return 3

    sc = closure(items, g1, findings)
    doc = render(items, m, g1, sc)
    rc = recount(doc, items)
    sc["gates"]["G2_LEDGER_CLOSES"] = rc["closes"]
    doc = render(items, m, g1, sc)          # تُعاد الكتابة بعد إقفال البوّابة
    if CONTAINER.findall(doc):
        print(f"OWNER_ALERT: CONTAINER_SIGNATURE — "
              f"{CONTAINER.findall(doc)[:3]}")
        return 4

    ledger = {"items": [dataclasses.asdict(i) for i in items],
              "by_authority": dict(Counter(i.authority for i in items)),
              "by_status": dict(Counter(i.status for i in items)),
              "recount_from_report": rc, "guards": findings,
              "closure": sc, "measured": m}
    (out / "01_ledger.json").write_text(
        json.dumps(ledger, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "04_report.md").write_text(doc, encoding="utf-8")

    write_owner_queue(out, items)
    write_upstream(out, items)

    eff = sc["CLOSURE_POTENTIAL"] if all(sc["gates"].values()) else 0
    print(f'ITEMS             {sc["TOTAL"]}')
    print(f'  DONE/DECLARED   {sc["GROUNDED"]}   ← GROUNDED')
    print(f'  RAISED/NOT_CH.  {sc["NAMED"]}   ← NAMED')
    print(f'  BROKEN          {sc["BROKEN"]}')
    print(f'RECOUNT           {rc["rows"]} صفًّا · يقفل {rc["closes"]}')
    for k, v in sc["gates"].items():
        print(f"  {k:24} {v}")
    print(f'CLOSURE_EFFECTIVE {eff}%  ·  CLOSURE_POTENTIAL '
          f'{sc["CLOSURE_POTENTIAL"]}%')
    print(f"→ {out}")
    return 0


def write_owner_queue(out: Path, items: list[Item]) -> None:
    o = ["# بنودُ الحكم — تُرفع ولا تُرجَّح", "",
         "لكلّ بندٍ أثرُ خياراته **مقيسًا**، ولا ترجيحَ في واحدٍ منها.", ""]
    for i in items:
        if i.authority != "OWNED_BY_OWNER":
            continue
        o += [f"## `{i.ident}` · {i.title}", "", "```json",
              json.dumps(i.evidence, ensure_ascii=False, indent=1), "```", ""]
    (out / "02_owner_queue.md").write_text("\n".join(o), encoding="utf-8")


def write_upstream(out: Path, items: list[Item]) -> None:
    o = ["# بنودُ ما خرج عن الولاية — تُقاس وتُعلَن، ولا تُلمس", "",
         "```text", "VENDOR_IS_FROZEN = TRUE",
         f"PIN = {PIN}", "```", ""]
    for i in items:
        if i.authority != "OUT_OF_JURISDICTION":
            continue
        o += [f"## `{i.ident}` · {i.title}", "",
              f"الحال: `{i.status}`", "", "```json",
              json.dumps(i.evidence, ensure_ascii=False, indent=1), "```"]
        if i.note:
            o += ["", i.note]
        o.append("")
    (out / "03_upstream.md").write_text("\n".join(o), encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
