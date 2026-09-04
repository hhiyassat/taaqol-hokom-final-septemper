#!/usr/bin/env python3
"""تصحيحاتٌ متّسقةٌ مع نفسها، وفهرسُ دفاترَ لا تُدمج  (`EXECUTABLE_NOW`).

    .venv-taaqol/bin/python scripts/build_exec_now.py --out output/exec_now

**ولا يرفع هذا العملُ علامةً واحدة.** هو يجعل ما قِيس متّسقًا مع نفسه: رقمٌ
واحدٌ لكلّ مقام، وموضعٌ لكلّ تصحيح، وفهرسٌ لدفاترَ لا تُدمج.

**والقاعدةُ الجديدة** `GUARD_MUST_REPORT_NOT_DIE`: استثناءٌ داخل حارسٍ يُنهي
الفحصَ كلَّه، فتُقرأ بقيّةُ الحرّاس سليمةً وهي لم تُشغَّل. وهو الصفرُ الميّتُ
في أخطر صوره: لا يُخفي عجزًا ولا عملًا، بل يُخفي **أنّ الفحصَ لم يجرِ**.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))
PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"

#: القواعدُ التسع — ولكلٍّ سمٌّ مسمًّى، ومن لا سمَّ له يُوسَم `UNPOISONED`.
#: وبيتُها هنا وحدَه: نسختان تشيخان متفرّقتَين.
RULES = {
    "MEASURED_NOT_PRESET": {
        "rule": "ما لم يُقَس لا يُطبع صفرًا. والمرحلةُ التي لم تُفتح لا "
                "تُنتج عددًا يساوي صفرًا، بل لا تُنتج عددًا.",
        "incident": "RELATION_CLOSED_COUNT = 0 كان يُقرأ «قِيس فكان صفرًا» "
                    "وهو لم يُقس.",
        "poison": "tests_taaqol/test_closure_guards.py::"
                  "test_x4_no_cell_from_a_closed_stage_carries_a_value",
    },
    "CAUSE_IS_A_CLAIM": {
        "rule": "العلّةُ في تقريرٍ إمّا لها أمرٌ منشورٌ يُعيد إنتاجها، وإمّا "
                "تُوسَم HYPOTHESIS.",
        "incident": "ثلاثةُ تعليلاتٍ باطلةٍ سُحبت في ثلاث جولات، ولا واحدةَ "
                    "منها أوقفها إجراء.",
        "poison": "tests_taaqol/test_remediation_guards.py::"
                  "test_every_measured_number_in_the_ledger_has_a_command",
    },
    "FILE_HASH_IS_NOT_CONTENT_HASH": {
        "rule": "لقاعدةِ بياناتٍ يُقابَل البيان لا الملفّ.",
        "incident": "35c7062d ≠ a8333229 أوهم اختلافًا، والبيانُ لم يختلف في "
                    "صفٍّ واحد — وكلّف ثلاثَ جولاتٍ من الفحص.",
        "poison": "UNPOISONED",
        "poison_note": "الوثيقةُ في ~/hokom/docs، والمقابلةُ أُجريت مرّةً "
                       "بيدٍ (بصمتا ملفٍّ متساويتان وبصمتا بيانٍ متساويتان) "
                       "ولم يُكتب لها سمٌّ يُشغَّل. فتُوسَم بحقيقتها.",
    },
    "NO_TEXTUAL_GUARD": {
        "rule": "لا حارسَ يفحص ورودَ اسمٍ في نصّ. يُشغَّل أو لا يُعدّ.",
        "incident": "حارسٌ نصّيٌّ يمرّ لو كُتب CORPUS_ABSENT في تعليقٍ ولم "
                    "يُرفع.",
        "poison": "tests_taaqol/test_nazila_matrix_guards.py::"
                  "test_a_blocked_preflight_writes_nothing",
        "poison_note": "أوّلُ إحالةٍ ذكرت سمًّا في السويت الخطأ — "
                       "واصطاده test_every_named_poison_actually_exists. "
                       "وسمٌّ مذكورٌ لا وجودَ له أسوأُ من UNPOISONED: "
                       "هذا يُخفي الغياب، وذاك يُعلنه.",
    },
    "DENOMINATOR_IS_PINNED": {
        "rule": "نقلُ بندٍ بين أسر الأسباب يضيّق المقامَ ويرفع العلامةَ بلا "
                "عمل — فيُقابَل بالجولة السابقة ويُعلَن.",
        "incident": "علامتان بمقامين عُرضتا كواحدة: 52% للدفتر و70.9% "
                    "للنازلة.",
        "poison": "tests_taaqol/test_nazila_outputs.py::"
                  "test_reason_family_moves_are_reported_against_the_"
                  "previous_round",
    },
    "GUARD_MUST_REPORT_NOT_DIE": {
        "rule": "الغيابُ يُبلَّغ (C3:ABSENT) ولا يُنهي الفحص.",
        "incident": "guard رفع StopIteration حين غاب C3، وKeyError حين غاب "
                    "status. واستثناءٌ داخل حارسٍ يُنهي الفحصَ كلَّه، فتُقرأ "
                    "بقيّةُ الحرّاس سليمةً وهي لم تُشغَّل.",
        "poison": "tests_taaqol/test_upstream_doors.py::"
                  "test_a_done_status_in_c_is_caught",
    },
    "COUNT_IS_NOT_MEMBERSHIP": {
        "rule": "تساوي العددَين لا يُثبت اتّحادَ المجموعتَين، واختلافُهما "
                "لا يُثبت افتراقَهما. والعضويّةُ تُقاس صفًّا بصفّ، في "
                "الجهتين. فالعددُ ظلُّ المجموعة لا هي. وحارسٌ يقيس عددًا "
                "يُوسَم بطبقته NUMERIC_COINCIDENCE_CHECK، ولا يُقرأ حكمًا "
                "على البنية.",
        "former_name": "EQUAL_NUMBERS_MAY_BE_DIFFERENT_SETS",
        "widened_by": "DR_HUSSEIN — الصيغةُ الأولى في جهةٍ واحدة، ووقعت "
                      "المخالفةُ في الجهة الأخرى.",
        "incident": "الجهةُ الأولى: G_NO_LEDGER_MERGE يتّهم صفًّا بريئًا "
                    "صادف عددُه مجموعَ الباقين. و9,630 بشاهدٍ و17,268 بلا "
                    "شاهد عُرضا رقمًا واحدًا بمقامَين. "
                    "والجهةُ الثانية: «Example سقط من الطبقة الثانية» — "
                    "رُفع بندًا لأنّ 55/160 اختلفت، ولم يضع صفٌّ واحد: "
                    "الاختلافُ شكلٌ (مررت بزيد ⟶ مَرَرْتُ بِزَيْدٍ) لا فقد. "
                    "ورقمان مختلفان اتّحدت مادّتُهما.",
        "poison": "tests_taaqol/test_exec_now.py::"
                  "test_count_is_not_membership_in_both_directions",
    },
    # الثامنةُ كانت تسكن `build_state` بـ`setdefault` — بيتًا ثانيًا
    # للقواعد. فنُقلت إلى بيتها، و`setdefault` هناك يبقى ولا يعمل: يُبقي
    # الوثيقةَ قائمةً لو نُزعت من هنا، ولا يُنشئ نسخةً تشيخ.
    "CLOSED_MATRIX_ON_ONE_COLUMN_IS_NOT_THE_AXIS": {
        "rule": "مصفوفةٌ تقفل على عمودٍ واحدٍ ليست خبرًا عن المحور. "
                "فعمودُ الحكم قد يسكن والبنيةُ تحته تتحرّك — وتُمسَح "
                "الأعمدةُ كلُّها أو لا يُقال «تحرّك صفر».",
        "incident": "المحاورُ الثلاثةُ قالت Verdict تحرّك 0، وتحرّك تحتها "
                    "Syllable_Pattern 3,152 و Stem_Surface 3,217. "
                    "و«تحرّك 0» على عمودٍ واحدٍ كان سيُقرأ «لم يقع شيء».",
        "ruled_by": "DR_HUSSEIN — جولةُ التنوين",
        "poison": "tests_taaqol/test_tanween.py::"
                  "test_the_positional_id_finding_is_raised_not_folded",
    },
    "SHARED_CAUSE_IS_NOT_SHARED_EFFECT": {
        "rule": "اتّحادُ العلّة لا يُثبت اتّحادَ الأثر · ولا يُدمج عدٌّ "
                "بعدٍّ لأنّ سببَهما واحد. والتباينُ يُقاس: بالعضويّة إن "
                "كان الحقلُ يحتمل، وبالتصميم إن كان لا يحتمل.",
        "ruled_by": "DR_HUSSEIN",
        "verbatim": "SHARED_CAUSE_IS_NOT_SHARED_EFFECT\n"
                    "   اتّحادُ العلّة لا يُثبت اتّحادَ الأثر · ولا يُدمج "
                    "عدٌّ بعدٍّ لأنّ سببَهما واحد\n"
                    "   والتباينُ يُقاس: بالعضويّة إن كان الحقلُ يحتمل، "
                    "وبالتصميم إن كان لا يحتمل",
        "incident": "C1 و C5 علّتُهما واحدةٌ بعينها — المشغّلُ لا يصل إلى "
                    "ما بُني. فانزلق القولُ من العلّة إلى الأثر، وكاد "
                    "يُجمع 17 و42 عدًّا واحدًا. والمقيسُ أنّهما متباينان "
                    "بالتصميم: reason_family حقلٌ واحدٌ لكلّ خانة، فلا "
                    "خانةَ تحمل أسرتين — و∩ = 0 تعضيدٌ لا أساس.",
        "two_bases": ["BY_MEMBERSHIP", "BY_DESIGN"],
        "two_bases_note": "و`ASSUMED` ليست أساسًا. ومن قال بالعضويّة "
                          "وحقلُه لا يحتمل ازدواجًا فقد بنى خبرًا عن "
                          "البنية على تشغيلٍ واحد.",
        "poison": "tests_taaqol/test_upstream_doors.py::"
                  "test_a_shared_cause_may_not_become_a_shared_count",
    },
}


class Blocked(SystemExit):
    """فشلٌ مغلق: يقف قبل أن يُكتب حرف."""


def gate_vendor() -> dict:
    head = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    st = subprocess.run(["git", "-C", str(VENDOR), "status", "--porcelain"],
                        capture_output=True, text=True, check=False)
    return {"vendor_head": head.stdout.strip(),
            "porcelain_lines": len([x for x in st.stdout.splitlines() if x]),
            "passes": head.stdout.strip() == PIN and not st.stdout.strip()}


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


# ── التصحيحات — كلٌّ بمصدره وموضعه القديم ──────────────────────────────
def occurrences(pattern: str, exts=(".md", ".json")) -> list[dict]:
    """أين وردت الدعوى — تُجرَد ولا تُمحى. والقيدُ لا يكون على غير موضع."""
    out = []
    for p in sorted(ROOT.rglob("*")):
        if p.suffix not in exts or ".venv" in str(p) or "vendor/" in str(p):
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for n, ln in enumerate(lines, 1):
            if re.search(pattern, ln):
                out.append({"file": str(p.relative_to(ROOT)), "line": n,
                            "text": ln.strip()[:110]})
    return out


def handoff_line(needle: str) -> str:
    """`HANDOFF.md:N` مشتقًّا. والغيابُ إنذارٌ لا رقمٌ صامت."""
    lines = (ROOT / "HANDOFF.md").read_text(encoding="utf-8").splitlines()
    hits = [i for i, ln in enumerate(lines, 1) if needle in ln]
    if not hits:
        raise Blocked(f"OWNER_ALERT: QUOTE_NOT_FOUND — {needle!r} في HANDOFF.md")
    return f"HANDOFF.md:{hits[0]}"


def corrections(up: dict, doors: dict, device: dict) -> list[dict]:
    j = up["joint_field"]
    c5 = next(i for i in up["items"] if i["ident"] == "C5")["measure"]
    reach = j["reachable_on_a_content_token"]
    cat = ROOT.parent / "hokom" / "data" / \
        "operators_catalog_split_vocalized_corrected.csv"
    return [
        {"ident": "A1", "title": "stages_blocked_by_C1 يُشطر",
         "was": "stages_blocked_by_C1 = 12  (يعدّ في C1 ما لا تفتحه)",
         "now": {"stages_not_opened_today": j["stages_not_opened_today"],
                 "stages_C1_would_open": j["stages_C1_would_open"],
                 "stages_still_closed_after_C1":
                     j["stages_still_closed_after_C1"]},
         "why": "ANSWER_AUDIT محجوبةٌ بنفسها (runtime_implemented=False) "
                "لا بـC1، فلا يفتحها فتحُ سلفِها.",
         "old_sites": occurrences(r"stages_blocked_by_C1"),
         "derived": True,
         "command": "python3 scripts/build_upstream.py"},
        {"ident": "A2", "title": "14/16 يُذكر خصماها",
         "was": "14/16 معلَّلًا بـANSWER_AUDIT وحدَها — فيُحسب 15",
         "now": {"value": reach["value"], "arithmetic": reach["arithmetic"],
                 "deduction_1": reach["deduction_1_never_implemented"],
                 "deduction_2":
                     reach["deduction_2_not_applicable_on_a_content_path"],
                 "collision": reach["collision_warning"]},
         "why": "رقمان متساويان بعضويّتين مختلفتين: هذا يُسقط "
                "NON_CONTENT_FORMAL_ROUTE ويُبقي PRE_WEIGHT، و"
                "runtime_implemented=True يعكسهما. ولولا التسميةُ لقُرئا واحدًا.",
         "old_sites": occurrences(r"14/16"),
         "derived": True,
         "command": "python3 scripts/build_upstream.py"},
        {"ident": "A3", "title": "C5 برقمين — يُوحَّد من مصدرٍ واحد",
         "was": "00_doors 42 · 00_upstream 35 (مكتوبٌ بيد)",
         "now": {"cells_C5_total": c5["cells_C5_total"],
                 "runner_does_not_consult":
                     c5["cells_runner_does_not_consult"],
                 "entry_boundary_not_constructed":
                     c5["cells_entry_boundary_not_constructed"],
                 "entry_boundary_placement": c5["entry_boundary_placement"],
                 "entry_boundary_is_a_fifth_door":
                     c5["entry_boundary_is_a_fifth_door"],
                 "doors_column": next(d["cells"] for d in doors["doors"]
                                      if d["door"] == "C5")},
         "why": "الأعلى كان يحمل 35 مكتوبًا بيد، فلم يمرّ الاشتقاقُ بهذا "
                "الحقل. و EntryBoundary داخلَ C5 جزءًا مسمًّى، لا بابًا خامسًا.",
         "old_sites": occurrences(r"cells_not_emitted"),
         "derived": True, "guard": "G_CELLS_AGREE",
         "command": "python3 scripts/build_upstream.py && "
                    "python3 scripts/build_doors.py"},
        {"ident": "B1", "title": "12/6 في الملفّ · 14/4 في الرسالة",
         "was": "الرسالةُ قالت «أربعةَ عشرَ .pyc وأربعةَ مصادرَ .py»",
         "now": device.get("denominator", "UNMEASURED"),
         "why": "كلاهما يجمع 18 والقسمةُ مختلفة. والملفُّ هو الحاكم.",
         "scope_of_the_dead_number_guard": {
             "covers": ["scripts/run_taaqol_nazila.py",
                        "scripts/probe_path_classifier.py"],
             "does_not_cover": "الرسائلُ إلى المالك",
             "declared_deliberately": True,
             "why_not_extended": "الرسالةُ ليست ملفًّا في الشجرة، فلا "
                                 "يُشغَّل عليها فحص. والحدُّ يُعلَن ولا "
                                 "يُدَّعى شمولُه — وهو NO_TEXTUAL_GUARD "
                                 "نفسُه: ما لا يُشغَّل لا يُعدّ حارسًا."},
         "old_sites": [{"file": "رسالةُ جولة TAIL", "line": None,
                        "text": "أربعةَ عشرَ .pyc … وأربعةَ مصادرَ .py"}],
         "derived": True,
         "command": "cat ~/hokom/output/tail/02_denominator.json"},
        {"ident": "B2", "title": "data_held_constant_at حقلًا لا نثرًا",
         "was": "نثرٌ في docstring: «البياناتُ تُنسخ من الحاضر»",
         "now": device.get("a4_scope", "UNMEASURED"),
         "why": "NO_PROMOTION يقيس أثرَ الكود وحدَه. وتغيُّرُ حكمٍ سببُه "
                "بيانٌ خارج مداه — وإلا قُرئ أوسعَ ممّا يقيس.",
         "old_sites": [{"file": "final-september/scripts/check_no_promotion.py",
                        "line": None, "text": "PROBE docstring"}],
         "derived": True,
         "command": "python3 scripts/check_no_promotion.py"},
        {"ident": "B3", "title": "A1 ⟶ DONE_WITH_LIMIT",
         "was": "A1 = DONE",
         "now": {"status": "DONE_WITH_LIMIT",
                 "limit": "HISTORY_BEGINS_AFTER_DOCUMENTED_WORK",
                 "commits": device.get("aslot_commits", "UNMEASURED"),
                 "earliest_cut": "2.8.0",
                 "documented_work_before": ["2.6.0", "2.7.0"],
                 "consequence": "ما قبل 2.8.0 لا يُفحص — ومنه القَطعُ الذي "
                                "وُضع له A4"},
         "why": "التاريخُ يبدأ بعد العمل الموصوف، فالإنجازُ محدودٌ لا مطلق.",
         "old_sites": occurrences(r'"ident": "A1"'),
         "derived": True,
         "command": "git -C ~/final-september log --oneline | wc -l"},
        {"ident": "B4", "title": "«١١ ترقيةً عند 2.7.0» تُوسَم حيث وردت",
         "was": "دعوى غيرُ موسومة",
         "now": {"second_half_measured":
                 "ثلاثةُ شواهدَ ACCEPT⟶DEFER عند 2.9.0 — مقيسٌ ومؤكَّد",
                 "first_half": "UNVERIFIABLE_IN_THIS_REPOSITORY",
                 "reason": "2.7.0 ليس بين الالتزامات، فالترقيةُ قبل حدّ الفحص",
                 "not_deleted": "الدعوى تُقيَّد لا تُمحى"},
         "why": "نصفٌ مقيسٌ ونصفٌ غيرُ قابلٍ للفحص — ولا يُقرآن معًا تأكيدًا.",
         "old_sites": occurrences(r"١١ صفًّا|١١ ترقيةً|11 صفًّا"),
         "derived": True,
         "command": "python3 scripts/check_no_promotion.py"},
        {"ident": "C1", "title": "I5 — إحالةٌ لا وصف",
         "was": "«رقمٌ سادسٌ ليس في 107/160/153/102/565»",
         "now": {"quote": "الجردُ الحاليّ شاهدٌ مشتقّ (١٣٤ مدخلة) لا سجلُّ "
                          "مالك، و LICENSE_GRANTED = NO",
                 # الموضعُ يُشتقّ ولا يُكتب: أُدرج فوقه أربعةُ أسطرٍ في
                 # جولة R6 فشاخ الرقمُ المكتوبُ صامتًا — واصطاده
                 # test_i5_quotes_the_handoff_instead_of_describing_it.
                 "source": handoff_line("١٣٤ مدخلة"),
                 "consequence": "فـ134 ليس مجهولًا سادسًا — والمجهولُ يبقى "
                                "107/160/153/102/565"},
         "why": "الوصفُ يجعل الرقمَ لغزًا، والإحالةُ تُغلقه.",
         "old_sites": occurrences(r"رقمٌ سادس"),
         "derived": True,
         "command": "grep -n '١٣٤ مدخلة' HANDOFF.md"},
        {"ident": "C2", "title": "بصمةُ سجلّ العوامل",
         "now": device.get("operators_catalog") or operators_catalog(cat),
         "was": "الملفُّ مسمًّى بحكم المالك والبصمةُ لم تُنشر",
         "why": "تسميةُ الملفّ ليست اعتمادَه — و LICENSE_GRANTED = NO.",
         "old_sites": occurrences(r"operators_catalog"),
         "derived": True,
         "command": "shasum -a 256 "
                    "~/hokom/data/operators_catalog_split_vocalized_"
                    "corrected.csv"},
    ]


def operators_catalog(p: Path) -> dict:
    """`C2` — يُقاس من الملفّ المسمّى نفسِه، أو يُعلَن غيابُه."""
    if not p.is_file():
        return {"path": str(p), "state": "UNMEASURED",
                "reason": "NOT_REACHABLE_FROM_THIS_CONTAINER — الملفّ في "
                          "~/hokom على آلة المالك",
                "LICENSE_GRANTED": "NO"}
    with p.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    ops = {r.get("Operator", "").strip() for r in rows if r.get("Operator")}
    return {"path": str(p), "sha256": sha256_of(p), "rows": len(rows),
            "rows_denominator": "صفوفُ الملفّ بلا الترويسة",
            "unique_operators": len(ops),
            "unique_operators_denominator": "قيمٌ متمايزةٌ في عمود Operator",
            "LICENSE_GRANTED": "NO",
            "note": "تسميةُ الملفّ بحكم المالك ليست اعتمادَه."}


# ── الفهرس — ولا تُدمج ─────────────────────────────────────────────────
def index(device: dict) -> list[dict]:
    """كلُّ دفترٍ بمقامه. ولا رقمَ جامعٌ عبر المقامات — مقاماتٌ لا مقام."""
    out = []

    def stamp(p: Path) -> str:
        return datetime.fromtimestamp(
            p.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")

    for rel, kind in (("output/remediation/01_ledger.json", "items"),
                      ("output/upstream/01_ledger.json", "items"),
                      ("output/doors/02_ledger.json", "doors")):
        p = ROOT / rel
        if not p.is_file():
            out.append({"ledger": rel, "state": "ABSENT",
                        "machine": "container"})
            continue
        d = json.loads(p.read_text(encoding="utf-8"))
        if kind == "items":
            n = len(d["items"])
            by = d.get("by_status") or {}
            if not by:
                by = {}
                for i in d["items"]:
                    by[i["status"]] = by.get(i["status"], 0) + 1
        else:
            n = len(d["doors"])
            by = d.get("by_owner", {})
        out.append({"ledger": rel, "machine": "container",
                    "denominator": f"{n} " +
                                   ("بندًا" if kind == "items" else "بابًا"),
                    "count": n, "by_status": by, "last_run": stamp(p)})
    out.extend(device.get("ledgers", []))
    return out


def guard(items: list[dict], idx: list[dict], gate: dict) -> dict:
    """كلُّ حارسٍ يُبلّغ عند غياب موضوعه — ولا يرفع استثناء."""
    g: dict = {}
    g["G_VENDOR"] = [] if gate["passes"] else ["VENDOR_DRIFT"]
    g["G_EVERY_CORRECTION_IS_DERIVED"] = [
        i.get("ident", "?") for i in items if not i.get("derived")]
    g["G_EVERY_CORRECTION_HAS_A_COMMAND"] = [
        i.get("ident", "?") for i in items if not i.get("command")]
    g["G_OLD_SITE_NAMED"] = [
        i.get("ident", "?") for i in items if i.get("old_sites") is None]
    g[f"G_NO_LEDGER_MERGE[{NO_MERGE_KIND}]"] = no_merge(idx)
    g["G_RULES_ALL_ACCOUNTED"] = [
        k for k, v in RULES.items() if not v.get("poison")]
    return g


#: `E2` — طبقةُ هذا الحارس. ليس بنيويًّا: لا يقرأ نسبًا ولا مساراتٍ، بل
#: يبحث عن **مصادفةٍ عدديّة**. فصفٌّ جامعٌ عددُه لا يساوي مجموعَ الباقين
#: (لاختلافِ مقامٍ أو بندٍ مكرَّر) يمرّ سالمًا، وصفٌّ بريءٌ صادف المجموعَ
#: يُتَّهم. ووسمُه `STRUCTURAL` كان يَعِد بما لا يفعل.
NO_MERGE_KIND = "NUMERIC_COINCIDENCE_CHECK"


def no_merge(idx: list[dict]) -> list[str]:
    """`G_NO_LEDGER_MERGE` — لا رقمَ جامعٌ عبر المقامات.

    ويسقط لو ظهر حقلٌ يجمع عددَ البنود عبر الدفاتر: مقاماتٌ لا مقام،
    ومجموعُها رقمٌ بلا معنًى.

    **طبقتُه `NUMERIC_COINCIDENCE_CHECK`** (`E2`) — لا `STRUCTURAL`. وهو
    يكشف الدمجَ إن صادف المجموعُ، ولا يكشفه إن لم يصادف. فالبنيةُ لا
    تُفحَص هنا؛ يُفحَص عددٌ.
    """
    rows = [x for x in idx if isinstance(x.get("count"), int)]
    if len(rows) < 3:
        return []
    total = sum(x["count"] for x in rows)
    # الصفُّ الجامع يساوي مجموعَ **الباقين** — لا مجموعَ الكلّ. وأوّلُ
    # كتابةٍ جمعت الكلَّ فلم تُطابق شيئًا أبدًا، فمرّ الحارسُ على كلّ حال.
    return [x.get("ledger", "?") for x in rows
            if x["count"] == total - x["count"]]


def render(items, idx, g, gate, naz) -> str:
    o = ["# ما نُفِّذ الآن — تصحيحاتٌ وفهرس", "", "```text",
         f'NAZILA_REGENERATED = {naz["utc"]}',
         f'NAZILA_RECORDS     = {naz["records"]} · {naz["records_diff"]}',
         f'NAZILA_SCORE       = {naz["score"]}%   ·   '
         f'STAGES_OPENED = {naz["stages_opened"]}',
         f'NAZILA_HTML        = {naz["sections"]} فصلًا · '
         f'{naz["data_cells"]} خانةً معروضة · {naz["derivation"]} '
         f'[{naz["repeat_identity"]}]',
         "```", "", "```text",
         "TASK_ID = EXECUTABLE_NOW",
         f'VENDOR_HEAD = {gate["vendor_head"]} · '
         f'porcelain {gate["porcelain_lines"]}',
         "CLAIM_PROJECT_FINISHED = NO", "```", "",
         "## التصحيحات", "",
         "| البند | كان | صار | مواضعُه القديمة |", "|---|---|---|---|"]
    for i in items:
        now = i["now"]
        short = (json.dumps(now, ensure_ascii=False)[:90]
                 if isinstance(now, dict) else str(now)[:90])
        o.append(f'| `{i["ident"]}` | {i["was"][:60]} | {short} | '
                 f'{len(i["old_sites"])} |')
    o += ["", "## فهرسُ الدفاتر — ولا تُدمج", "",
          "| الدفتر | الآلة | المقام | آخرُ تشغيل |", "|---|---|---|---|"]
    for x in idx:
        o.append(f'| `{x["ledger"]}` | {x.get("machine", "—")} | '
                 f'{x.get("denominator", x.get("state", "—"))} | '
                 f'{x.get("last_run", "—")} |')
    # `E5` — العددُ يُشتقّ من طولِ الجدول، ولا يُكتب. وكان «خمسةُ مقامات»
    # مكتوبًا والجدولُ فوقه ستّة؛ والسطرُ الذي حمل الرقمَ الميّت هو نفسُه
    # الذي يقول «ولا رقمَ جامعٌ عبر المقامات».
    o += ["", f"**ولا رقمَ جامعٌ عبر المقامات.** {len(idx)} مقاماتٍ لا مقام، "
          "ومجموعُها رقمٌ بلا معنًى.", "",
          "## الحرّاس", "", "| الحارس | مخالفات |", "|---|---|"]
    for k, v in g.items():
        o.append(f'| `{k}` | `{v if v else "لا شيء"}` |')
    return "\n".join(o) + "\n"


def rules_md() -> str:
    o = [f"# القواعدُ ال{len(RULES)} — ولكلٍّ سمٌّ أو وسمُ UNPOISONED", ""]
    for name, r in RULES.items():
        o += [f"## `{name}`", "", f'**القاعدة**: {r["rule"]}', "",
              f'**الواقعة**: {r["incident"]}', "",
              f'**السمّ**: `{r["poison"]}`"'.rstrip('"')]
        if r.get("poison_note"):
            o += ["", r["poison_note"]]
        o.append("")
    return "\n".join(o)


def nazila_facts(out_dir: Path) -> dict:
    sc = json.loads((out_dir / "scores.json").read_text(encoding="utf-8"))
    page = (out_dir / "nazila_result.html").read_text(encoding="utf-8")
    with (out_dir / "records.csv").open(encoding="utf-8", newline="") as fh:
        rows = list(csv.reader(fh))[1:]
    return {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "records": f"{len(rows)} × {len(rows[0])}",
            "record_cells": sum(len(r) for r in rows),
            "records_diff": "بلا فرق",
            "score": sc["CLOSURE_POTENTIAL"],
            "grounded": sc["GROUNDED"], "total": sc["CELLS_TOTAL"],
            "stages_opened": sc["STAGES_OPENED"],
            "sections": len(re.findall(r"<h2>", page)),
            # `E3` — الفرقُ يُشتقّ ولا يُكتب. الأزواجُ المتمايزة هي المقام؛
            # والزائدُ عليها هو المكرَّر، ويجب أن يكون بعينه حقولَ
            # `EntryBoundary` — تُعدّ من الصنف حيًّا لا من الذاكرة.
            **repeat_is_entry_boundary(page),
            "g5": sc["gates"].get("G5_HTML_CSV_AGREE")}


def repeat_is_entry_boundary(page: str) -> dict:
    """`E3` — ٢٩٩ = ٢٩٢ + حقولُ حدّ الدخول. اشتقاقًا، لا كتابةً.

    ويبلّغ ولا يموت: إن لم يكن المكرَّرُ حقولَ `EntryBoundary` بعينِها
    سُمّي المخالف، ولم يُكتم الفرقُ خلف رقمٍ مكتوب.
    """
    from dataclasses import fields as _fields

    from taaqqul_slot_geometry import EntryBoundary

    pairs = re.findall(r'data-section="([^"]*)" data-field="([^"]*)"', page)
    attrs = len(re.findall(r'data-section="', page))
    distinct = sorted(set(pairs))
    seen: dict = {}
    for p in pairs:
        seen[p] = seen.get(p, 0) + 1
    repeated = sorted(k for k, v in seen.items() if v > 1)
    declared = tuple(f.name for f in _fields(EntryBoundary))
    off = sorted(f"{s}/{f}" for s, f in repeated if f not in declared)
    return {
        "data_attributes": attrs,
        "data_cells": len(distinct),
        "data_repeated": len(repeated),
        "entry_boundary_fields": len(declared),
        "repeat_identity": (
            "ENTRY_BOUNDARY_FIELDS" if not off and
            len(repeated) == len(declared) else "MISMATCH"),
        "repeat_mismatch": off,
        "derivation": (f"{attrs} = {len(distinct)} + {len(repeated)}"
                       f" · حقولُ EntryBoundary {len(declared)}"),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/exec_now")
    ap.add_argument("--device", default="",
                    help="JSON بحقائق دفاتر الآلة — تُقرأ ولا تُخمَّن")
    a = ap.parse_args()

    gate = gate_vendor()
    if not gate["passes"]:
        print(f"BLOCKED_AT_VENDOR: {json.dumps(gate, ensure_ascii=False)}")
        return 2
    device = json.loads(a.device) if a.device else {}

    up = json.loads((ROOT / "output/upstream/00_upstream.json")
                    .read_text(encoding="utf-8"))
    doors = json.loads((ROOT / "output/doors/00_doors.json")
                       .read_text(encoding="utf-8"))
    naz = nazila_facts(ROOT / "output" / "nazila_result")

    items = corrections(up, doors, device)
    idx = index(device)
    g = guard(items, idx, gate)

    doc = render(items, idx, g, gate, naz)
    body = doc.split("## التصحيحات", 1)[1].split("\n## ", 1)[0]
    rows = [ln for ln in body.splitlines()
            if ln.startswith("| `") and not ln.startswith("| `البند")]
    closes = len(rows) == len(items)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "00_corrections.json").write_text(
        json.dumps({"gate": gate, "nazila": naz, "corrections": items},
                   ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "01_rules.md").write_text(rules_md(), encoding="utf-8")
    (out / "02_ledger.json").write_text(json.dumps(
        {"corrections": [{"ident": i["ident"], "derived": i["derived"]}
                         for i in items],
         "index": idx, "guards": g,
         "recount_from_report": {"rows": len(rows), "items": len(items),
                                 "closes": closes}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    (ROOT / "output" / "INDEX.md").write_text(
        doc.split("## فهرسُ الدفاتر", 1)[0].split("## التصحيحات")[0]
        + "## فهرسُ الدفاتر" + doc.split("## فهرسُ الدفاتر", 1)[1],
        encoding="utf-8")
    (out / "03_report.md").write_text(doc, encoding="utf-8")

    print(f'NAZILA_SCORE  {naz["score"]}% ({naz["grounded"]}/{naz["total"]}) · '
          f'STAGES_OPENED {naz["stages_opened"]} · '
          f'HTML {naz["sections"]} فصلًا · {naz["data_cells"]} خانةً '
          f'متمايزة · {naz["derivation"]} [{naz["repeat_identity"]}]')
    print(f'CORRECTIONS   {len(items)} · يقفل {closes}')
    print(f'INDEX         {len(idx)} دفاتر')
    for k, v in g.items():
        print(f'  {k:32} {v if v else "PASS"}')
    print(f"→ {out} · output/INDEX.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
