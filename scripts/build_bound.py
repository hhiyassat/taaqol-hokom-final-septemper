#!/usr/bin/env python3
"""`BOUND_AND_RECONCILE` — تقييدُ الترديد، والأصلُ الثالث، والعددُ المتغيّر.

    .venv-taaqol/bin/python scripts/build_bound.py

**ولا يرفع هذا العملُ علامةً، ولا يفتح مرحلة.** هو يمنع بلاغًا حجّتُه
ترديدٌ من أن يُرسَل، ويقيّد دعوى مقيسةً على ثلثَين، ويُعلن عددًا تغيّر
صامتًا — وثلاثتُها في وثائقَ مُصدَّرة.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

import tautology as TAUT  # noqa: E402

PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"

#: `R5` — خطآن للمراجع، يُسجَّلان بمصدرهما ولا يُنسبان إلى الأداة.
WITHDRAWN = {
    "REVIEWER_WITHDRAWN_1": {
        "source": "REVIEWER",
        "claim": "G_FORBIDDEN_LINES_QUERIED — الاستفتاءُ دليل",
        "verdict": "باطل",
        "why": "الاستفتاءُ عن صفوفِ السجلّ ترديد: الزوجُ مأخوذٌ من السجلّ "
               "ثمّ سُئل عنه السجلّ، فيردّ True بحكم الأخذ.",
        "proposed_poison": "زوجٌ غيرُ ممنوعٍ يردّ False",
        "proposed_poison_verdict": "يُثبت أنّ الدالّةَ تفرّق، لا أنّ "
                                   "الجوابَ شهادة — وهو وجهٌ واحد.",
        "replaced_by": "G_EVIDENCE_IS_NOT_TAUTOLOGY — يقيس مصدرَ المدخل "
                       "لا الجواب، وسمُّه ذو وجهَين.",
        "attributed_to_tool": False,
    },
    "REVIEWER_WITHDRAWN_2": {
        "source": "REVIEWER",
        "claim": "مميِّزُ M1: صوامتُ بعدُ > قبلُ",
        "verdict": "لا يميّز",
        "why": "يُطابق 8894/8894: الزيادةُ في التنوين كلِّه، لأنّ كلَّ "
               "تنوينٍ يُبسَط إلى نونٍ ساكنة فيزيد صامتًا حتمًا. "
               "والصامتُ الزائدُ المميِّزُ غيرُها.",
        "replaced_by": "المميِّزُ المقيس: تنوينُ فتحٍ على ألفٍ صامتة — "
                       "3059/5835، يقفل.",
        "attributed_to_tool": False,
    },
    # ── الثالثُ **دعويان لا واحدة**، ولكلٍّ مصدر ──────────────────────
    #
    # سُجّل أوّلًا بندًا واحدًا مصدرُه `TOOL`. وحكم المالكُ بشطره: «تصحيحُك
    # رفع نصفَ الخطأ إلى الأداة، ونصفُه لي».
    #
    # **والعلّةُ التي جمعتهما اسمٌ مشترك.** «`PRE_WEIGHT` غيرُ منفَّذة»
    # لفظٌ واحدٌ يحمل دعويَين: حقلًا في السجلّ نقلته الأداةُ كما هو —
    # وهو **صادق**؛ وتأويلًا لذلك الحقل بأنّ المرحلةَ غيرُ مكتوبةٍ عند
    # `sonaiso` — وهو **باطل**. فبطلانُ التأويل لا يمسّ صدقَ الحقل،
    # وصدقُ الحقل لا يُصحّح التأويل. ولمّا اشتركا في الاسم قُرئا واحدًا،
    # ونُسبا إلى جهةٍ واحدة.
    #
    # وأثرُهما مختلف: الحقلُ لم يكلّف شيئًا، والتأويلُ حمل تقديرَ كلفة
    # `ج-٣` ثلاثين جولة.
    "REVIEWER_WITHDRAWN_3A": {
        "source": "TOOL",
        "split_from": "REVIEWER_WITHDRAWN_3",
        "split_by": "DR_HUSSEIN — «دعويان لا واحدة، ولكلٍّ مصدر»",
        "claim": "C1 = «PRE_WEIGHT_CAPACITY_AUDIT غيرُ منفَّذة» عنوانًا "
                 "في 03_upstream",
        "verdict": "ناقصٌ لا كاذب",
        "field_is_true": True,
        "why": "الحقلُ مشتقٌّ من `runtime_implemented=False` في السجلّ، "
               "ونُقل كما هو. وعلّتُه أنّ اللفظَ يُقرأ نفيًا للبناء "
               "كلِّه — والبناءُ مقيسٌ موجودًا. فالعيبُ في سَعة اللفظ، "
               "لا في صدق الحقل.",
        "replaced_by": "«PRE_WEIGHT مبنيّةُ الحوامل، غيرُ موصولةٍ "
                       "بالمشغّل» — والحقلُ نفسُه يبقى مقيسًا في "
                       "C1.measure.pre_weight_state.stage_runtime_implemented",
        "cost": "لم يكلّف تقديرًا — العنوانُ وصفٌ لا ثمن",
        "attributed_to_tool": True,
    },
    "REVIEWER_WITHDRAWN_3B": {
        "source": "REVIEWER",
        "split_from": "REVIEWER_WITHDRAWN_3",
        "split_by": "DR_HUSSEIN — «دعويان لا واحدة، ولكلٍّ مصدر»",
        "claim": "PRE_WEIGHT غيرُ مكتوبةٍ عند sonaiso · تحتاج كتابةَ منطق",
        "verdict": "باطل",
        "why": "تأويلٌ للحقل لا يلزم منه: `runtime_implemented=False` "
               "خبرٌ عن **الوصل** لا عن **البناء**. والمقيس: القوانينُ "
               "الثلاثةُ مصادَقة، و PR-10..PR-13 مشحونةٌ برموزها، "
               "واختباراتُ الحواملِ 107 تمرّ.",
        "replaced_by": "الحالُ المقيسة في C1.measure.pre_weight_state — "
                       "PRs 4/4 · اختباراتٌ تمرّ · corpus_runner لا يستورد "
                       "من weight/ حرفًا. فالفجوةُ وصلةٌ لا بناء.",
        "held_for": "ثلاثون جولة",
        "cost": "بُني عليه تقديرُ كلفةِ ج-٣ — وهو الثمنُ الحقيقيّ للبند",
        "withdrawn_by": "DR_HUSSEIN — «قابلتُه فطابق حرفًا · "
                        "واعتراضُك في محلّه»",
        "consequence": "عنوانُ C1 صُحِّح، وتقديرُ كلفةِ ج-٣ يسقط معه — "
                       "ولا يُعاد تقديرُه من عندنا (C_PATH موقوف).",
        "attributed_to_tool": False,
    },
}

#: بنودٌ شُطرت — يُحفظ الأصلُ ولا يُمحى، فالشطرُ نفسُه واقعةٌ تُقرأ.
SPLIT_ORIGINS = {
    "REVIEWER_WITHDRAWN_3": {
        "was": "بندٌ واحدٌ مصدرُه TOOL",
        "became": ["REVIEWER_WITHDRAWN_3A", "REVIEWER_WITHDRAWN_3B"],
        "ruled_by": "DR_HUSSEIN",
        "why": "دعويان تشتركان في اسمٍ واحد: حقلٌ صادقٌ نقلته الأداة، "
               "وتأويلٌ باطلٌ للمراجع. والاسمُ المشترك جمعهما، فقُرئا "
               "دعوى واحدةً ونُسبا إلى جهةٍ واحدة.",
        "effect_on_attribution": "REVIEWER 2 · TOOL 1  ⟶  REVIEWER 3 · TOOL 1",
    },
}

#: `R6` — ادّعاءٌ بائدٌ يُسحب حيث ورد، ولا يُحذف.
OBSOLETE = {
    "claim": "تقشيرُ كَتَبَ ينزل عن ACCEPT بـT-6",
    "status": "SUPERSEDED",
    "superseded_by": "نزل بالفعل عند 2.9.0 بحكم المالك في T4B — "
                     "لا بـT-6، ولا بأثرِ الأداة.",
    "measured": {
        "katab_rows": None, "katab_peels": None,
        "root_proven_yes": None, "axis4_rows": None,
        "reading": "فلا واقعةَ تحت Signifier→WordForm — "
                   "EXPECTED_EVENT_ABSENT",
    },
    "deleted": False,
    "retained_because": "الدعوى تُقيَّد لا تُمحى.",
}

PATTERNS = (r"ينزل عن ACCEPT", r"كَتَبَ.*T-6", r"T-6.*كَتَبَ",
            r"تقشيرُ كَتَبَ")


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def read(rel: str) -> dict:
    p = ROOT / rel
    if not p.is_file():
        raise Blocked(f"OWNER_ALERT: ABSENT — {rel}")
    return json.loads(p.read_text(encoding="utf-8"))


def vendor_gate() -> dict:
    def git(*a):
        return subprocess.run(["git", "-C", str(VENDOR), *a],
                              capture_output=True, text=True,
                              check=False).stdout.strip()
    head = git("rev-parse", "HEAD")
    dirty = [ln for ln in git("status", "--porcelain").splitlines() if ln]
    return {"vendor_head": head, "porcelain_lines": len(dirty),
            "untouched": not dirty, "matches_pin": head == PIN}


def occurrences(patterns) -> list[dict]:
    """أين وردت الدعوى في هذه الشجرة — تُجرَد ولا تُفترَض."""
    import re
    rx = [re.compile(p) for p in patterns]
    out = []
    for p in sorted(ROOT.rglob("*")):
        # `output/bound/` هو **سجلُّ** الادّعاء لا الادّعاءُ قائمًا:
        # ورودُه فيه قيدٌ، فلو عُدَّ موضعًا لطالب الحارسُ بوسمِ الوسم.
        # والاستثناءُ يُعلَن ولا يُصمَت عنه.
        if p.suffix not in (".md", ".json") or ".venv" in str(p) \
                or "vendor/" in str(p) or "output/bound/" in str(p):
            continue
        try:
            lines = p.read_text(encoding="utf-8").splitlines()
        except (UnicodeDecodeError, OSError):
            continue
        for n, ln in enumerate(lines, 1):
            if any(r.search(ln) for r in rx):
                out.append({"file": str(p.relative_to(ROOT)), "line": n,
                            "text": ln.strip()[:110]})
    return out


# ────────────────────────────────────────────────────── R1 · تقييدُ `C3`
def c3_bounded() -> dict:
    up = read("output/upstream/00_upstream.json")
    doors = read("output/doors/00_doors.json")
    c3 = next(i for i in up["items"] if i["ident"] == "C3")["measure"]
    door = next(d for d in doors["doors"] if d["door"] == "C3")

    docs = {
        "output/upstream/00_upstream.json": {
            "count_retained": c3.get("corpus_words_matching"),
            "denominator": c3.get("corpus_words"),
            "crosses": c3["crossing_claim"]["crosses"],
            "mapping": c3["crossing_claim"]["mapping"],
            "status": c3["crossing_claim"]["status"],
            "withdrawn": c3["crossing_claim"]["withdrawn"],
        },
        "output/doors/00_doors.json": {
            "count_retained": door["correctness"]["corpus_words_matching"],
            "denominator": door["correctness"]["corpus_words"],
            "crosses": door["correctness"]["crosses"],
            "mapping": door["correctness"]["mapping"],
            "status": door["correctness"]["claim_status"],
            "withdrawn": door["correctness"]["claim_withdrawn"],
        },
        "output/doors/upstream_report.md": {
            "rendered_from": "output/doors/00_doors.json",
            "note": "التقريرُ يُصاغ من الدفتر، فقيدُه قيدُه.",
        },
    }
    # سمُّ الوجهَين — يُشغَّل هنا ويُطبع، لا يُوصَف.
    face_a = TAUT.classify("CANONICAL_REGISTRY.lines")
    face_b = TAUT.classify(
        "get_native_stage_registry().allowed_successors")
    return {
        "task": "R1_C3_BOUNDED",
        "count": {
            "matched": c3.get("corpus_words_matching"),
            "denominator": c3.get("corpus_words"),
            "percent": c3.get("percent"),
            "verdict": "مقيسٌ وسليم — يبقى",
        },
        "what_remains_evidence": c3["what_remains_evidence"],
        "crossing_claim": c3["crossing_claim"],
        "documents": docs,
        "guard": {
            "guard": "G_EVIDENCE_IS_NOT_TAUTOLOGY",
            "measures": "مصدرَ المدخل — لا الجواب",
            "face_a_registry_pair": face_a,
            "face_b_stage_graph_pair": face_b,
            "two_faces_differ": face_a != face_b,
            "poison": "tests_taaqol/test_bound.py::"
                      "test_poison_evidence_is_not_tautology_has_two_faces",
            "passes": face_a == TAUT.TAUTOLOGY and face_b == TAUT.EVIDENCE,
        },
        "report_to_sonaiso": {
            "raised": c3["what_remains_evidence"]["claim"],
            "not_raised": "دعوى العبور — ترديدٌ ونسبةٌ غيرُ مشتقّة",
            "SENT": "NO",
            "AUTHORITY_TO_SEND": "OWNER",
        },
    }


# ──────────────────────────────────────────────── R2 · الأصلُ الثالث
def origins() -> dict:
    t7 = read("reports/gate_shadow/SUMMARY.json")
    g = next(x for x in t7["guards"] if x["guard"] == "G_ALL_ORIGINS")
    rows = t7["rows"]
    declared = t7["origins_declared"]
    return {
        "task": "R2_ALL_ORIGINS",
        "was": {"rows": 288, "arithmetic": "288 = 2 × 4 × 6 × 6",
                "origins_measured": 2, "origins_declared": 3,
                "claim_read_as": "ولا CERTIFICATE بحال",
                "claim_actually_measured_on": "2/3 origins"},
        "now": {"rows": rows,
                "arithmetic": f"{rows} = {len(declared)} × 4 × 6 × 6",
                "origins_measured": len(t7["origins"]),
                "origins": t7["origins"],
                "origins_declared": declared},
        "resolution": "قِيس CANDIDATE — فالمقامُ تامٌّ ولا يحتاج التقييدُ "
                      "النصّيّ. والدعوى تُعمَّم أو تُنقض بالقياس لا بالكلام.",
        "certificate_granted_anywhere": [
            r for r in t7["ranks_granted"] if r == "CERTIFICATE"],
        "ranks_granted": t7["ranks_granted"],
        "verdict": ("الدعوى تصمد على المقام التامّ: لا رتبةَ CERTIFICATE "
                    "تُمنح من هذه البوّابة في أيٍّ من الأصول الثلاثة."
                    if "CERTIFICATE" not in t7["ranks_granted"]
                    else "الدعوى تُنقض: CERTIFICATE مُنحت."),
        "guard": g,
        "poison": "tests_taaqol/test_bound.py::"
                  "test_poison_all_origins_falls_when_one_is_dropped",
    }


# ─────────────────────────────────────────── R5 · R6 · السحبُ والقيد
def withdrawn() -> dict:
    a4 = ROOT / "reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv"
    import csv as _csv
    rows = katab = peels = proven = 0
    if a4.is_file():
        with a4.open(encoding="utf-8", newline="") as fh:
            for r in _csv.DictReader(fh):
                rows += 1
                pc = (r.get("Peel_Count") or "").strip()
                n = int(pc) if pc.lstrip("-").isdigit() else 0
                if (r.get("Root_Proven") or "").strip().upper() == "YES":
                    proven += 1
                if (r.get("Word") or "") == "كَتَبَ":
                    katab += 1
                    if n > 0:
                        peels += 1
    obs = json.loads(json.dumps(OBSOLETE, ensure_ascii=False))
    obs["measured"].update({"katab_rows": katab, "katab_peels": peels,
                            "root_proven_yes": proven, "axis4_rows": rows})
    sites = occurrences(PATTERNS)
    # `G_OBSOLETE_TAGGED_IN_PLACE` — كلُّ موضعٍ ورد فيه الادّعاءُ يحمل
    # الوسمَ عندَه، لا في دفترٍ بعيد. وجردٌ بلا وسمٍ في موضعه يترك
    # الادّعاءَ يُقرأ قائمًا.
    untagged = []
    for x in sites:
        body = (ROOT / x["file"]).read_text(encoding="utf-8").splitlines()
        near = "\n".join(body[max(0, x["line"] - 1):x["line"] + 5])
        if "SUPERSEDED" not in near:
            untagged.append(f'{x["file"]}:{x["line"]}')
    obs["occurrences_in_this_tree"] = sites
    obs["untagged_sites"] = sorted(untagged)
    obs["guard"] = {"guard": "G_OBSOLETE_TAGGED_IN_PLACE",
                    "denominator": len(sites),
                    "untagged": sorted(untagged),
                    "passes": not untagged,
                    "poison": "tests_taaqol/test_bound.py::"
                              "test_poison_an_untagged_site_is_caught"}
    obs["scan_excludes"] = ["vendor/", ".venv", "output/bound/ — سجلُّ "
                            "القيد نفسُه، وعدُّه موضعًا يطلب وسمَ الوسم"]
    obs["occurrences_note"] = (
        "جردٌ مقيس. وإن كان صفرًا فالادّعاءُ خارجَ هذه الشجرة "
        "(رسالةُ المراجع) — ويُسجَّل هنا ولا يُنسب إليها."
        if not sites else
        f"وُسم في {len(sites) - len(untagged)}/{len(sites)} موضعًا "
        "عند موضعه، ولم يُحذف منها شيء.")
    # `attribution_rule` كان يقول «الخطآن مصدرُهما REVIEWER» — وهو عددٌ
    # ووصفٌ مكتوبان بيد. فلمّا دخل ثالثٌ مصدرُه الأداةُ صار السطرُ الجامعُ
    # نفسُه دعوى باطلة. فيُشتقّ من الجدول: عددًا ومصادرَ.
    by_src: dict = {}
    for v in WITHDRAWN.values():
        by_src[v["source"]] = by_src.get(v["source"], 0) + 1
    return {"task": "R5_R6_WITHDRAWN", "reviewer_withdrawn": WITHDRAWN,
            "obsolete_claim": obs,
            "withdrawn_by_source": dict(sorted(by_src.items())),
            "split_origins": SPLIT_ORIGINS,
            "attribution_rule":
                "كلُّ سحبٍ يُسجَّل بمصدره: " +
                " · ".join(f"{k} {n}" for k, n in sorted(by_src.items())) +
                ". ولا يُنسب خطأُ المراجع إلى الأداة، ولا يُخفى خطأُ "
                "الأداة تحت اسم المراجع. والأداةُ سجّلتها ولم تمحُ منها "
                "شيئًا."}


# ─────────────────────────────────────────────────────────── التقرير
def render(naz, gate, c3, org, cc, wd, e5) -> str:
    o = ["# `BOUND_AND_RECONCILE` — تقييدُ الترديد، والأصلُ الثالث، "
         "والعددُ المتغيّر", "", "```text",
         f'NAZILA_REGENERATED = {naz["utc"]}',
         f'NAZILA_SCORE       = {naz["score"]}% ({naz["grounded"]}/'
         f'{naz["total"]})   ·   STAGES_OPENED = {naz["stages_opened"]}',
         f'NAZILA_HTML        = {naz["sections"]} فصلًا · '
         f'{naz["derivation"]} [{naz["repeat_identity"]}]',
         "```", "", "```text",
         "TASK_ID = BOUND_AND_RECONCILE",
         f'VENDOR_HEAD = {gate["vendor_head"]} · '
         f'porcelain {gate["porcelain_lines"]} · '
         f'MATCHES_PIN = {str(gate["matches_pin"]).upper()}',
         "VENDOR_UNTOUCHED = TRUE · NO_COMMIT = TRUE",
         "SCORE_RAISED = NO · STAGE_OPENED = NO",
         "CLAIM_PROJECT_FINISHED = NO",
         "```", "",
         "**ولا يرفع هذا العملُ علامةً، ولا يفتح مرحلة.**", "",

         "## `R1` — `C3` مقيَّدًا في الوثائق الثلاث", "",
         "| ما هو | القيمة | الحال |", "|---|---|---|",
         f'| العدد | `{c3["count"]["matched"]}/'
         f'{c3["count"]["denominator"]}` ({c3["count"]["percent"]}٪) | '
         "**يبقى** — مقيسٌ وسليم |",
         f'| ما بقي دليلًا | {c3["what_remains_evidence"]["claim"]} | '
         "`EVIDENCE` — وهذا وحدَه يُرفع |",
         f'| دعوى العبور | `crosses: True ×3` | '
         f'`{c3["crossing_claim"]["crosses"]}` |',
         f'| نسبةُ القاعدة إلى السطر | `startswith("ال")` ⟶ '
         f'`Grapheme→FunctionalLetter` | '
         f'`{c3["crossing_claim"]["mapping"]}` |',
         f'| الحكم | — | `{c3["crossing_claim"]["status"]}` |',
         f'| أمُحيت؟ | — | '
         f'**{"نعم" if c3["crossing_claim"]["withdrawn"] else "لا"}** — '
         "الدعوى تُقيَّد لا تُمحى |", "",
         "**والوثائقُ الثلاث**: `00_upstream.json` و`00_doors.json` "
         "و`upstream_report.md` — والثالثُ يُصاغ من الثاني فقيدُه قيدُه.",
         "", "**والحارسُ الجديد** `G_EVIDENCE_IS_NOT_TAUTOLOGY` يقيس "
         "**مصدرَ المدخل** لا الجواب، وسمُّه ذو وجهَين:", "",
         "| الوجه | المصدر | يلزم |", "|---|---|---|",
         f'| الأوّل | `CANONICAL_REGISTRY.lines` | '
         f'`{c3["guard"]["face_a_registry_pair"]}` |',
         f'| الثاني | `get_native_stage_registry().allowed_successors` | '
         f'`{c3["guard"]["face_b_stage_graph_pair"]}` |', "",
         "ووجهٌ واحدٌ يُوهم أنّ الحارسَ يقيس مصدرًا وهو يقيس جوابًا: لو "
         "اكتُفي بالأوّل لمرّ حارسٌ يقول «كلُّ `True` ترديد» — وهو باطل.",
         "", "```text",
         f'REPORT_TO_SONAISO  RAISED     = {c3["report_to_sonaiso"]["raised"]}',
         f'                   NOT_RAISED = '
         f'{c3["report_to_sonaiso"]["not_raised"]}',
         f'                   SENT = {c3["report_to_sonaiso"]["SENT"]} · '
         f'AUTHORITY_TO_SEND = '
         f'{c3["report_to_sonaiso"]["AUTHORITY_TO_SEND"]}',
         "```", "",

         "## `R2` — الأصلُ الثالثُ في `T-7`", "",
         "| | كان | صار |", "|---|---|---|",
         f'| الصفوف | {org["was"]["rows"]} | **{org["now"]["rows"]}** |',
         f'| الحساب | `{org["was"]["arithmetic"]}` | '
         f'`{org["now"]["arithmetic"]}` |',
         f'| الأصولُ المقيسة | {org["was"]["origins_measured"]}/'
         f'{org["was"]["origins_declared"]} | '
         f'**{org["now"]["origins_measured"]}/'
         f'{len(org["now"]["origins_declared"])}** |', "",
         f'**والقرار**: {org["resolution"]}', "", f'**والحكم**: '
         f'{org["verdict"]} والرتبُ الممنوحةُ كلُّها: '
         f'`{" · ".join(org["ranks_granted"])}`.', "",
         "و`CANDIDATE` بُني من **قِطَع فَخّ الـ vendor نفسِها**، ولم يُبدَّل "
         "منها إلا `generation_source`؛ و`entry_boundary` تُرك `None` لأنّ "
         "الحاملَ يرفضه لغير `DECLARED_ENTRY` — حكمُ الحامل لا اختيارٌ منّي.",
         "",

         "## `R3` — ٦٠ و٥٢: مقامان لا خطأ", "",
         "| المقام | المصدر | الصنف | المجموع |", "|---|---|---|---|",
         f'| **أحداث** (مواضعُ حرف) | `axis1_normalization.py:1233` | '
         f'{cc["detail"]["events"]} | {cc["totals"]["events"]} |',
         f'| **كلمات** | `axis1_normalization.py:224` — '
         f'`decision_classes` مجموعة | {cc["detail"]["words"]} | '
         f'{cc["totals"]["words"]} |', "",
         f'**والثمانيةُ لم تخرج.** لا كلمةَ واحدة. هي '
         f'{cc["detail"]["extra_events"]} **مواضعِ حرفٍ زائدة** على '
         f'{cc["detail"]["words_raising_it_more_than_once"]} كلماتٍ '
         "معدودةٍ أصلًا:", "",
         "| الموضع | الكلمة | يُرفع | الزائد |", "|---|---|---|---|"]
    for x in cc["detail"]["the_extra"]:
        o.append(f'| `{x["position"]}` | {x["word"]} | ×{x["raised"]} | '
                 f'+{x["extra"]} |')
    o += ["", f'**{cc["correction"]["ruling"]}**', "",

          "## `E5` — عددُ `INDEX.md` يُشتقّ", "",
          f'| كان | صار |', "|---|---|",
          f'| «خمسةُ مقاماتٍ لا مقام» مكتوبًا، والجدولُ فوقه '
          f'{e5["ledgers"]} | `len(idx)` — {e5["rendered"]} |', "",
          "والمفارقةُ في موضعها: السطرُ الذي حمل الرقمَ الميّت هو نفسُه "
          "الذي يقول «ولا رقمَ جامعٌ عبر المقامات».", "",

          "## `R5` — سحوبٌ تُسجَّل بمصادرها ولا تُمحى", "",
          "| # | المصدر | الدعوى | الحكم | ما حلّ محلَّها | تُنسَب للأداة؟ |",
          "|---|---|---|---|---|---|"]
    for k, v in wd["reviewer_withdrawn"].items():
        o.append(f'| `{k}` | `{v["source"]}` | {v["claim"]} | '
                 f'**{v["verdict"]}** | {v["replaced_by"]} | '
                 f'{"**نعم** — TOOL" if v["attributed_to_tool"] else "لا"} |')
    o += ["", wd["attribution_rule"]]
    for k, s in wd.get("split_origins", {}).items():
        o += ["", f'**`{k}` شُطر** بحكم {s["ruled_by"]}: {s["was"]} ⟶ '
                  f'{" · ".join(f"`{x}`" for x in s["became"])}.', "",
              s["why"], "", f'والإسناد: {s["effect_on_attribution"]}.']

    ob = wd["obsolete_claim"]
    m = ob["measured"]
    o += ["", "## `R6` — ادّعاءٌ بائدٌ يُسحب حيث ورد", "", "```text",
          f'CLAIM         {ob["claim"]}',
          f'STATUS        {ob["status"]}',
          f'SUPERSEDED_BY {ob["superseded_by"]}',
          f'MEASURED      كَتَبَ ورد {m["katab_rows"]} صفًّا · قشرَ في '
          f'{m["katab_peels"]} · Root_Proven=YES في {m["root_proven_yes"]} '
          f'من {m["axis4_rows"]}',
          f'READING       {m["reading"]}',
          f'DELETED       {str(ob["deleted"]).upper()} — '
          f'{ob["retained_because"]}',
          f'OCCURRENCES   {len(ob["occurrences_in_this_tree"])} في هذه الشجرة',
          "```", "", ob["occurrences_note"], ""]

    o += ["## الحرّاس", "", "| الحارس | من | النتيجة |", "|---|---|---|",
          f'| `G_EVIDENCE_IS_NOT_TAUTOLOGY` | R1 | '
          f'{"PASS" if c3["guard"]["passes"] else "FALLS"} |',
          f'| `G_ALL_ORIGINS` | R2 | '
          f'{"PASS" if org["guard"]["passes"] else "FALLS"} |']
    for x in cc["guards"]:
        o.append(f'| `{x["guard"]}` | R3 | '
                 f'{"PASS" if x["passes"] else "FALLS"} |')
    og = wd["obsolete_claim"]["guard"]
    o.append(f'| `{og["guard"]}` | R6 | '
             f'{"PASS" if og["passes"] else "FALLS"} |')
    o += [f'| `G_VENDOR` | — | '
          f'{"PASS" if gate["untouched"] and gate["matches_pin"] else "FALLS"} |',
          "", "```text", "CLAIM_PROJECT_FINISHED = NO", "```", ""]
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/bound")
    a = ap.parse_args()

    gate = vendor_gate()
    if not gate["untouched"]:
        raise Blocked(f"BLOCKED_AT_VENDOR: {gate}")

    c3 = c3_bounded()
    org = origins()
    cc = read("output/bound/02_class_count.json")
    wd = withdrawn()

    idx = read("output/exec_now/02_ledger.json")["index"]
    index_doc = (ROOT / "output" / "INDEX.md").read_text(encoding="utf-8")
    import re as _re
    rendered = _re.search(r"\*\*ولا رقمَ جامعٌ عبر المقامات\.\*\* (\S+)",
                          index_doc)
    e5 = {"ledgers": len(idx),
          "rendered": rendered.group(1) if rendered else "NOT_FOUND",
          "derived": bool(rendered) and rendered.group(1) == str(len(idx))}

    naz = dict(read("output/exec_now/00_corrections.json")["nazila"])
    naz["utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "00_c3_bounded.json").write_text(
        json.dumps(c3, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "01_origins.json").write_text(
        json.dumps(org, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "03_withdrawn.json").write_text(
        json.dumps({**wd, "E5": e5}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (out / "04_report.md").write_text(
        render(naz, gate, c3, org, cc, wd, e5), encoding="utf-8")

    print(f'R1 C3 عددٌ {c3["count"]["matched"]}/{c3["count"]["denominator"]} '
          f'يبقى · crosses={c3["crossing_claim"]["crosses"]} · '
          f'mapping={c3["crossing_claim"]["mapping"]} · '
          f'SENT={c3["report_to_sonaiso"]["SENT"]}')
    print(f'R2 صفوفٌ {org["was"]["rows"]} ⟶ {org["now"]["rows"]} · '
          f'أصولٌ {org["now"]["origins_measured"]}/'
          f'{len(org["now"]["origins_declared"])} · '
          f'CERTIFICATE {org["certificate_granted_anywhere"] or "لا شيء"}')
    print(f'R3 أحداثٌ {cc["totals"]["events"]} · '
          f'كلماتٌ {cc["totals"]["words"]} · '
          f'الثمانيةُ {cc["detail"]["extra_events"]} موضعًا على '
          f'{cc["detail"]["words_raising_it_more_than_once"]} كلمات')
    print(f'E5 دفاترُ {e5["ledgers"]} · مطبوعٌ {e5["rendered"]} · '
          f'مشتقّ {e5["derived"]}')
    print(f'R5 سحوبٌ {len(wd["reviewer_withdrawn"])} '
          f'({" · ".join(f"{k} {n}" for k, n in wd["withdrawn_by_source"].items())}) · '
          f'R6 مواضعُ الادّعاء '
          f'{len(wd["obsolete_claim"]["occurrences_in_this_tree"])}')
    for g in (c3["guard"], org["guard"], *cc["guards"],
              wd["obsolete_claim"]["guard"]):
        print(f'   {g["guard"]:28} {"PASS" if g["passes"] else "FALLS"}')
    ok = (c3["guard"]["passes"] and org["guard"]["passes"]
          and all(x["passes"] for x in cc["guards"]) and e5["derived"]
          and wd["obsolete_claim"]["guard"]["passes"])
    print(f"→ {out}/04_report.md")
    if not ok:
        raise Blocked("GUARD_FALLS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
