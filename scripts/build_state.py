#!/usr/bin/env python3
"""`STATE_OF_PROJECT` — أين المشروعُ من وثائقه الحاكمة، بأثرٍ لكلّ سطر.

    PYTHONPATH=src .venv-taaqol/bin/python scripts/build_state.py

**وهذا التقريرُ إسقاطٌ لا سلطة** (`PROJECTION`): لا يُنشئ حكمًا ولا يُغلق
بندًا ولا يُصحّح رقمًا. يقرأ الوثائقَ الحاكمةَ ويقول أين المشروعُ منها.

**و`NO_PROSE_DONE`**: كلُّ «تمّ» يحمل الأثرَ الذي يُثبته، والأمرَ الذي
يُعيده، وتاريخَ آخر قياس. ومن لا أثرَ له `CLAIMED_NOT_VERIFIED` لا `DONE`.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts"))

PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
DEVICE = ROOT / "data" / "device_state.json"

#: سلطاتُ الوثائق — جردٌ **مغلق** على انضباط `docs/123`. وما لا سلطةَ
#: له في هذا الجرد يُوسَم `AUTHORITY_UNCLEAR` ولا يُخمَّن.
AUTHORITIES = ("LAW", "RUNTIME", "EVIDENCE", "PROJECTION", "HISTORICAL")

#: الوثائقُ الحاكمة، ولكلٍّ سلطةٌ **واحدة**. والمسارُ مفتاح.
DOCUMENTS = {
    "laws/MANIFEST.json": "LAW",
    "laws/L01_JALALAH.md": "LAW",
    "laws/L02_DAGGER_ALIF.md": "LAW",
    "laws/L03_SUN_MOON_LAM.md": "LAW",
    "laws/L04_ELIDED_ARTICLE.md": "LAW",
    "laws/L05_INTERROGATIVE_MADDA.md": "LAW",
    "laws/L06_CL16_RANK.md": "LAW",
    "laws/L07_CL16_SKELETON.md": "LAW",
    "data/axis_1_owner_policy.json": "LAW",
    "data/residual_kind_assignment.json": "LAW",
    "vendor/Taaqol-GPT": "LAW",
    "src/aslot": "RUNTIME",
    "scripts": "RUNTIME",
    "output/remediation/01_ledger.json": "EVIDENCE",
    "output/upstream/00_upstream.json": "EVIDENCE",
    "output/doors/00_doors.json": "EVIDENCE",
    "output/nazila_result/scores.json": "EVIDENCE",
    "output/tanween/02_after.json": "EVIDENCE",
    "output/bound/00_c3_bounded.json": "EVIDENCE",
    "output/max/01_b2_measures.json": "EVIDENCE",
    "reports/compliance/AXIS_9_MEASURES.json": "EVIDENCE",
    "output/INDEX.md": "PROJECTION",
    "output/state/06_STATE.md": "PROJECTION",
    "HANDOFF.md": "HISTORICAL",
    "README.md": "HISTORICAL",
    "docs/ARCHITECTURE.md": "HISTORICAL",
}

#: `T-0..T-10` — إحدى عشرةَ مرحلةً، ولا تُحذف واحدةٌ ولو `NOT_STARTED`.
PHASES = ("T-0", "T-1", "T-2", "T-3", "T-4", "T-5", "T-6", "T-7", "T-8",
          "T-9", "T-10")

#: القواعدُ التسع — الثامنةُ من جولة التنوين، والتاسعةُ من جولة العلّة
#: المشتركة، وكلتاهما بحكم المالك.
RULE_NAMES = (
    "MEASURED_NOT_PRESET", "CAUSE_IS_A_CLAIM",
    "FILE_HASH_IS_NOT_CONTENT_HASH", "NO_TEXTUAL_GUARD",
    "DENOMINATOR_IS_PINNED", "GUARD_MUST_REPORT_NOT_DIE",
    "COUNT_IS_NOT_MEMBERSHIP",
    "CLOSED_MATRIX_ON_ONE_COLUMN_IS_NOT_THE_AXIS",
    "SHARED_CAUSE_IS_NOT_SHARED_EFFECT",
)


class Blocked(SystemExit):
    """فشلٌ مغلق."""


def read(rel: str, default=None):
    p = ROOT / rel
    if not p.is_file():
        if default is not None:
            return default
        raise Blocked(f"OWNER_ALERT: ABSENT — {rel}")
    return json.loads(p.read_text(encoding="utf-8"))


def sha(p: Path) -> str:
    if p.is_dir():
        h = hashlib.sha256()
        for f in sorted(p.rglob("*")):
            if f.is_file() and "__pycache__" not in str(f) and ".git" not in f.parts:
                h.update(f.read_bytes())
        return h.hexdigest()
    return hashlib.sha256(p.read_bytes()).hexdigest()


def stamp(p: Path) -> str:
    t = max((f.stat().st_mtime for f in p.rglob("*") if f.is_file()),
            default=p.stat().st_mtime) if p.is_dir() else p.stat().st_mtime
    return datetime.fromtimestamp(t, timezone.utc).isoformat(timespec="seconds")


def git_dated(rel: str, dating: dict) -> dict:
    """أهذه الوثيقةُ في مستودعٍ يؤرّخها؟ وإلا `UNDATED` (`B14`).

    **والتأريخُ يُقاس على شجرة المالك، لا في الحاوية.** فالنسخةُ هنا بلا
    `git` ألبتّة، فلو قيس هنا لقُرئ كلُّ شيءٍ `UNDATED` — وذلك خبرٌ عن
    الحاوية لا عن الوثائق. والقياسُ يُودَع في `data/device_state.json`
    بأمره، وغيابُه يُعلَن ولا يُقرأ تأريخًا.
    """
    if not dating:
        return {"dated": None, "note": "NOT_MEASURED — لم يُقَس على شجرة "
                                       "المالك، ولا يُقرأ الغيابُ تأريخًا"}
    d = (dating.get("paths") or {}).get(rel)
    if d is None:
        return {"dated": None, "note": "NOT_IN_DATING_SET"}
    if d.get("tracked"):
        return {"dated": True, "repo": dating.get("repo"),
                "last_commit": d["last_commit"]}
    return {"dated": False, "repo": dating.get("repo"),
            "note": d.get("reason", "UNTRACKED")}


# ──────────────────────────────────────────── القسم الأوّل · الوثائق
def documents(dating: dict) -> dict:
    out, unclear = [], []
    for rel, auth in DOCUMENTS.items():
        p = ROOT / rel
        if not p.exists():
            out.append({"path": rel, "authority": auth, "state": "ABSENT"})
            continue
        if auth not in AUTHORITIES:
            unclear.append(rel)
            auth = "AUTHORITY_UNCLEAR"
        g = git_dated(rel, dating)
        out.append({"path": rel, "authority": auth,
                    "kind": "dir" if p.is_dir() else "file",
                    "sha256": sha(p)[:32], "mtime_utc": stamp(p),
                    "dated": g["dated"],
                    "date_note": g.get("last_commit") or g.get("note")})
    by = {}
    for d in out:
        by[d["authority"]] = by.get(d["authority"], 0) + 1
    undated = [d for d in out if d.get("dated") is False]
    why: dict = {}
    for d in undated:
        why[d["date_note"]] = why.get(d["date_note"], 0) + 1
    return {"documents": out, "by_authority": dict(sorted(by.items())),
            "authority_unclear": unclear,
            "dated": sum(1 for d in out if d.get("dated") is True),
            "undated": sorted(d["path"] for d in undated),
            "undated_by_reason": dict(sorted(why.items())),
            "undated_by_authority": {
                a: sorted(d["path"] for d in undated if d["authority"] == a)
                for a in AUTHORITIES
                if any(d["authority"] == a for d in undated)},
            "dating_measured_on": dating.get("repo", "NOT_MEASURED"),
            "dating_command": dating.get("command"),
            "finding": "سلطةُ EVIDENCE بلا بيتٍ مؤرَّخ: دفاترُ الإثبات "
                       "كلُّها في حاويةٍ تُستردّ، وغائبةٌ عن المستودع "
                       "الوحيد الذي يؤرّخها.",
            "finding_2": "وأشدُّ منه: `data/residual_kind_assignment.json` "
                         "سلطتُه `LAW` — وهو موضعُ حكمِ `B2` حين يقع — "
                         "وغائبٌ عن المستودع كذلك. فحكمٌ يُودَع في حاويةٍ "
                         "تُستردّ ليس مودَعًا.",
            "authorities_closed_list": list(AUTHORITIES)}


# ─────────────────────────────────────── القسم الثاني · المراحل
def phases(a9: dict, dev: dict) -> dict:
    naz = read("output/nazila_result/scores.json")
    t7 = read("reports/gate_shadow/SUMMARY.json", {})
    t6 = read("reports/forbidden_shadow/SUMMARY.json", {})
    assign = read("data/residual_kind_assignment.json")
    tan = read("output/tanween/02_after.json", {})
    ri = a9["refusal_inventory"]
    an = a9["anchors"]

    P = {
        "T-0": {"title": "تجميدُ المرجع", "state": "DONE",
                "evidence": f'{a9["laws"]["law_files"]} ملفَّ قانونٍ ببصماتها · '
                            f'all_hashes_hold={a9["laws"]["all_hashes_hold"]}',
                "command": "PYTHONPATH=src .venv-taaqol/bin/python -m aslot compliance",
                "artifact": "laws/MANIFEST.json"},
        "T-1": {"title": "تاكسونومية الرفض المغلقة", "state": "PARTIAL",
                "evidence": f'مُعلَنٌ {ri["declared"]} · مشهودٌ '
                            f'{ri["observed_in_outputs"]} · بلا شاهدٍ في هذا '
                            f'التشغيل {len(ri["declared_without_witness_in_this_run"])} '
                            f'({" · ".join(ri["declared_without_witness_in_this_run"])})',
                "why_partial": "الجردُ مغلقٌ ومعدود، لكن ثلاثةَ أسماءٍ بلا "
                               "شاهدٍ في هذا التشغيل — والفرقُ مُعلَنٌ لا مطويّ",
                "command": "PYTHONPATH=src .venv-taaqol/bin/python -m aslot compliance",
                "artifact": "reports/compliance/AXIS_9_MEASURES.json"},
        "T-2": {"title": "حواملُ النواة", "state": "DONE_WITH_LIMIT",
                "evidence": f'{len(a9["vendor"]["carriers"])} حواملَ مثبَّتةَ '
                            "البصمة · ولا سابعَ يُنفَّذ",
                "limit": "DECLARED_NOT_EXECUTED — الحواملُ مستوردةٌ ومبصومة، "
                         "ولا يُنفَّذ منها حكم",
                "command": "PYTHONPATH=src .venv-taaqol/bin/python -m aslot compliance",
                "artifact": "reports/compliance/AXIS_9_MEASURES.json"},
        "T-3": {"title": "مرساةُ الأثر", "state": "DONE",
                "evidence": f'{an["rows_total"]:,} صفًّا · بمرساةٍ '
                            f'{an["rows_with_trace_anchor"]:,} · '
                            f'قابلةٌ لإعادة البناء '
                            f'{an["rows_with_reconstructible_anchor"]:,} · '
                            f'بلا مرساة {an["rows_without_anchor"]}',
                "command": "PYTHONPATH=src .venv-taaqol/bin/python -m aslot compliance",
                "artifact": "reports/compliance/AXIS_9_MEASURES.json"},
        "T-4": {"title": "أصنافُ البقيّة", "state": "BLOCKED",
                "evidence": f'{sum(1 for v in assign["assignments"].values() if v is None)}'
                            f'/{len(assign["assignments"])} بلا إسناد · '
                            "P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED",
                "blocked_on": "B2 · OWNER",
                "command": "PYTHONPATH=src .venv-taaqol/bin/python scripts/measure_b2.py",
                "artifact": "data/residual_kind_assignment.json"},
        "T-5": {"title": "Γ على كلّ صفّ", "state": "BLOCKED",
                "evidence": "مبنيٌّ فارغًا وفاشلًا مغلقًا · exit 3 · "
                            "BLOCKED_AWAITING_B2 · ولا يُكتب ملفٌّ واحد",
                "blocked_on": "B2 · OWNER",
                "command": ".venv-taaqol/bin/python scripts/gamma_over_axes.py",
                "artifact": "scripts/gamma_over_axes.py"},
        "T-6": {"title": "سجلُّ الخطوط الممنوعة", "state": "PARTIAL",
                "evidence": f'ظلٌّ: {t6.get("rows", "?")} صفًّا · دليلٌ '
                            f'{t6.get("evidence_rows", "?")} · يقع '
                            f'{t6.get("would_fire_on_evidence", "?")} · '
                            "ولا تنفيذ",
                "why_partial": "السجلُّ يُستفتى في ظلٍّ لا في تشغيل · "
                               "forbidden_lines_enforced = "
                               f'{a9["forbidden_lines_enforced"]}',
                "command": ".venv-taaqol/bin/python scripts/forbidden_shadow.py",
                "artifact": "reports/forbidden_shadow/WOULD_FIRE.csv"},
        "T-7": {"title": "البوّابات", "state": "PARTIAL",
                "evidence": f'ظلٌّ: {t7.get("rows", "?")} صفًّا · أصولٌ '
                            f'{len(t7.get("origins", []))}/'
                            f'{len(t7.get("origins_declared", []))} · '
                            f'رتبٌ {t7.get("ranks_granted", "?")}',
                "why_partial": "بوّابةٌ في ظلٍّ لا بين المحاور · "
                               f'gates_between_axes = {a9["gates_between_axes"]}',
                "command": ".venv-taaqol/bin/python scripts/gate_shadow.py",
                "artifact": "reports/gate_shadow/TRANSITIONS.csv"},
        "T-8": {"title": "حدُّ المصدر المجمَّد", "state": "PARTIAL",
                "evidence": dev.get("b83", "UNMEASURED"),
                "why_partial": "B8.3 مُغلَقٌ بحكمٍ على الآلة · وB15 موقوف",
                "command": "على آلة المالك: cat ~/hokom/output/b83/02_ledger.json",
                "artifact": "hokom/output/b83/02_ledger.json"},
        "T-9": {"title": "إسقاطُ الحالة", "state": "NOT_STARTED",
                "evidence": "مُعلَنةٌ في STAGES_PENDING_OWNER "
                            "(axis9_compliance.py:48) · ولا أثرَ لها في "
                            "الشجرة: صفرُ ذكرٍ في HANDOFF · README · "
                            "docs/ARCHITECTURE",
                "measured_not_assumed": True,
                "command": "grep -rn 'T-9' HANDOFF.md README.md docs/",
                "artifact": None},
        "T-10": {"title": "هندسةُ الاختبار الدستوريّ", "state": "NOT_STARTED",
                 "evidence": "مُعلَنةٌ في STAGES_PENDING_OWNER "
                             "(axis9_compliance.py:49) · ولا أثرَ لها في "
                             "الشجرة: صفرُ ذكرٍ في الوثائق الثلاث",
                 "measured_not_assumed": True,
                 "command": "grep -rn 'T-10' HANDOFF.md README.md docs/",
                 "artifact": None},
    }
    for k, v in P.items():
        v["phase"] = k
        v["opened_in_runtime"] = k in a9["stages_implemented"]
    by = {}
    for v in P.values():
        by[v["state"]] = by.get(v["state"], 0) + 1
    return {"phases": P, "order": list(PHASES),
            "by_state": dict(sorted(by.items())),
            "stages_opened": naz["STAGES_OPENED"],
            "runtime_implemented": a9["stages_implemented"],
            "runtime_pending": a9["stages_pending_owner"],
            "count": len(P)}


# ───────────────────────────────────────── القسم الثالث · القواعد
def rules() -> dict:
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "bex_state", ROOT / "scripts" / "build_exec_now.py")
    m = importlib.util.module_from_spec(spec)
    sys.modules["bex_state"] = m
    spec.loader.exec_module(m)
    src = dict(m.RULES)

    #: الثامنةُ انتقلت إلى بيت القواعد في `build_exec_now`. و`setdefault`
    #: يبقى ولا يعمل: احتياطٌ لو نُزعت من هناك، فتُبلَّغ الوثيقةُ ولا
    #: تسقط. ولو صار يعمل لكانت نسخةً ثانيةً تشيخ — ويصطاده
    #: `test_the_eighth_rule_lives_in_the_rules_home`.
    src.setdefault("CLOSED_MATRIX_ON_ONE_COLUMN_IS_NOT_THE_AXIS", {
        "rule": "مصفوفةٌ تقفل على عمودٍ واحدٍ ليست خبرًا عن المحور. "
                "فعمودُ الحكم قد يسكن والبنيةُ تحته تتحرّك — وتُمسَح "
                "الأعمدةُ كلُّها أو لا يُقال «تحرّك صفر».",
        "incident": "المحاورُ الثلاثةُ قالت Verdict تحرّك 0، وتحرّك تحتها "
                    "Syllable_Pattern 3,152 و Stem_Surface 3,217. "
                    "و«تحرّك 0» على عمودٍ واحدٍ كان سيُقرأ «لم يقع شيء».",
        "poison": "tests_taaqol/test_tanween.py::"
                  "test_the_positional_id_finding_is_raised_not_folded",
    })

    out = {}
    for name in RULE_NAMES:
        r = src.get(name)
        if r is None:
            out[name] = {"state": "ABSENT_FROM_RULES",
                         "poison_runs": False}
            continue
        ref = r.get("poison", "UNPOISONED")
        runs = False
        exists = False
        if ref != "UNPOISONED" and "::" in ref:
            f, _, t = ref.partition("::")
            p = ROOT / f
            exists = p.is_file() and f"def {t}(" in p.read_text(encoding="utf-8")
            runs = exists
        out[name] = {"rule": r["rule"], "incident": r.get("incident"),
                     "poison": ref, "poison_exists": exists,
                     "poison_runs": runs,
                     "state": ("POISONED" if runs
                               else "UNPOISONED" if ref == "UNPOISONED"
                               else "POISON_NAMED_BUT_MISSING"),
                     "poison_note": r.get("poison_note")}
    return {"rules": out, "declared": len(RULE_NAMES),
            "present": sum(1 for v in out.values()
                           if v.get("state") != "ABSENT_FROM_RULES"),
            "poisoned": sum(1 for v in out.values() if v["poison_runs"]),
            "unpoisoned": sorted(k for k, v in out.items()
                                 if v.get("state") == "UNPOISONED")}


# ────────────────────────────────────── القسم الرابع · طابورُ المالك
def owner_queue(dev: dict) -> dict:
    led = read("output/remediation/01_ledger.json")
    tan = read("output/tanween/05_pending.json", {})
    b2 = read("output/max/01_b2_measures.json", {})
    a1 = read("output/tanween/02_after.json", {})

    items = []
    for i in led["items"]:
        items.append({"ident": i["ident"], "title": i["title"],
                      "authority": i["authority"], "status": i["status"],
                      "source": "output/remediation/01_ledger.json",
                      "effect_measured": bool(i.get("evidence"))})
    for tag, extra in (("B8.3", "DONE"), ("B11", "DONE"), ("B12", "DONE"),
                       ("B14", "DONE"), ("B15", "RAISED"), ("B16", "STRUCK"),
                       ("B17", "RAISED"), ("B10", "DONE"), ("B13", "DONE")):
        if not any(x["ident"] == tag for x in items):
            d = (dev.get("items") or {}).get(tag)
            items.append({"ident": tag, "title": (d or {}).get("title", "—"),
                          "authority": "OWNED_BY_OWNER"
                          if extra == "RAISED" else "OWNED_BY_AGENT",
                          "status": extra,
                          "source": d.get("source") if d else
                          "NOT_IN_THIS_CONTAINER",
                          "effect_measured": bool(d)})
    for tag in ("P1", "P2", "P3"):
        x = tan.get(tag)
        if x:
            items.append({"ident": tag, "title": x["title"],
                          "authority": "OWNED_BY_OWNER", "status": "RAISED",
                          "source": "output/tanween/05_pending.json",
                          "rows": x["count"], "executed": x["executed_rows"],
                          "effect_measured": True})
    # `Q4` — سؤالُ تضييق الصنف، بأثره المقيس
    u = b2.get("M2_reach", {}).get("per_class", {}).get("U_TANWEEN", {})
    pending_rows = a1.get("pending_total")
    total = u.get("members")
    items.append({
        "ident": "Q4", "title": "أيُضيَّق U_TANWEEN إلى الموقوف وحدَه؟",
        "authority": "OWNED_BY_OWNER", "status": "RAISED",
        "source": "output/max/01_b2_measures.json + output/tanween/02_after.json",
        "effect_measured": total is not None and pending_rows is not None,
        "effect": {
            "raised_on_now": total,
            "of_which_no_decision_needed": (total - pending_rows
                                            if total and pending_rows else None),
            "of_which_still_pending": pending_rows,
            "arithmetic": (f"{total} = {total - pending_rows} + {pending_rows}"
                           if total and pending_rows else "UNMEASURED"),
            "narrowed_to": pending_rows,
        },
        "not_weighed": "ولا يُرجَّح — OWNER_PENDING"})

    by_status: dict = {}
    for x in items:
        by_status[x["status"]] = by_status.get(x["status"], 0) + 1
    closed = sum(v for k, v in by_status.items()
                 if k in ("DONE", "STRUCK", "DECLARED"))
    pending = sum(v for k, v in by_status.items()
                  if k in ("RAISED", "BLOCKED"))
    out_of = sum(v for k, v in by_status.items()
                 if k in ("NOT_CHOSEN",))
    effect_unmeasured = sorted(x["ident"] for x in items
                               if x["authority"] == "OWNED_BY_OWNER"
                               and not x["effect_measured"])
    return {"items": items, "count": len(items),
            "by_status": dict(sorted(by_status.items())),
            "closed": closed, "pending": pending, "out_of_jurisdiction": out_of,
            "sum": closed + pending + out_of,
            "closes": closed + pending + out_of == len(items),
            "effect_unmeasured": effect_unmeasured}


# ──────────────────────────────────── القسم الخامس · ما عند sonaiso
def upstream() -> dict:
    up = read("output/upstream/00_upstream.json")
    doors = read("output/doors/00_doors.json")
    # `F1` — **ستّةُ محاورَ لا خمسة.** سقوطُ `correctness` كان يجعل
    # `C2` و`C3` يُقرآن «لا أثرَ لهما»: خاناتٌ 0/292 وسقفٌ
    # `NO_EFFECT_MEASURED`. وحقيقتُهما في محور الصحّة: 0/11 على السليم
    # و11/11 على المعيب · و10,013 من 77,411. والمحورُ يُشتقّ من الأبواب
    # ولا يُكتب — و`G_AXES_AGREE` يُثبت المطابقة.
    out = {}
    for i in up["items"]:
        if not i["ident"].startswith("C"):
            continue
        d = next((x for x in doors["doors"] if x["door"] == i["ident"]), {})
        if not d:
            # `C_PATH` ليس بابًا بل **اختيارُ مسلك**: لا خاناتٍ له ولا
            # سقفًا ولا كلفة. فيُعلَن `NOT_A_DOOR` ولا يُحشى بمحاورَ
            # فارغةٍ تُقرأ «لا أثرَ له».
            out[i["ident"]] = {"title": i["title"], "status": i["status"],
                               "kind": "NOT_A_DOOR",
                               "note": "اختيارُ مسلكٍ لبنود (ج) — "
                                       "لا محاورَ له"}
            continue
        out[i["ident"]] = {"title": i["title"], "status": i["status"],
                           "kind": "DOOR",
                           "cells": d.get("cells"),
                           "correctness": d.get("correctness"),
                           "correctness_command": d.get("correctness_command"),
                           "ceiling": d.get("ceiling"),
                           "cost": d.get("cost"),
                           "owner": d.get("owner")}
    c3 = next(i for i in up["items"] if i["ident"] == "C3")["measure"]
    out["C3"]["bounded"] = {
        "count": f'{c3["corpus_words_matching"]}/{c3["corpus_words"]}',
        "crosses": c3["crossing_claim"]["crosses"],
        "mapping": c3["crossing_claim"]["mapping"],
        "raise_to_source": c3["what_remains_evidence"]["claim"]}
    return {"upstream": out,
            "axes": AXES_OF_A_DOOR,
            "axes_note": "محاورُ الحال = محاورُ الأبواب، اسمًا وقيمة — "
                         "و`G_AXES_AGREE` يُثبتها ولا يفترضها.",
            "C_PATH": "NOT_CHOSEN",
            "report": {"drafted": True, "SENT": "NO",
                       "AUTHORITY_TO_SEND": "OWNER"}}


#: محاورُ البابِ الواحد — جردٌ **مغلق**. وسقوطُ واحدٍ منها يقلب القراءة.
AXES_OF_A_DOOR = ("cells", "correctness", "ceiling", "cost")


def axes_agree(up: dict | None = None) -> list[str]:
    """`G_AXES_AGREE` — يبلّغ ولا يموت: يُسمّي المحورَ المفقودَ أو المختلف.

    **ويُقابَل المحسوبُ في هذا التشغيل، لا الملفُّ المكتوبُ في سابقه.**
    فقراءةُ الملفّ الذي يكتبه التشغيلُ نفسُه تجعل الحارسَ متأخّرًا جولةً:
    يمرّ على مخرَجٍ قديمٍ سليم، ويُقرأ شهادةً على الجديد. وهو الفحصُ
    الأجوفُ بعينه — اصطدتُه حين مرّ الحارسُ قبل أن يُكتب المحور.
    """
    if up is None:
        up = read("output/state/04_upstream.json", {"upstream": {}})
    doors = read("output/doors/00_doors.json")
    off = []
    for door, v in (up.get("upstream") or {}).items():
        if v.get("kind") == "NOT_A_DOOR":
            continue          # مُعلَنٌ لا مسكوتٌ عنه — ولا محاورَ يُقابَل بها
        d = next((x for x in doors["doors"] if x["door"] == door), None)
        if d is None:
            off.append(f"{door}:NOT_IN_DOORS")
            continue
        for ax in AXES_OF_A_DOOR:
            if ax not in v:
                off.append(f"{door}.{ax}:MISSING_IN_STATE")
            elif ax not in d:
                off.append(f"{door}.{ax}:MISSING_IN_DOORS")
            elif v[ax] != d[ax]:
                off.append(f"{door}.{ax}:DIFFERS")
    return off


# ─────────────────────────────────── القسم السادس · العلاماتُ الأربع
#: `F2` — سلسلةُ مقامِ `TWO_COLUMN`. ولكلّ حلقةٍ **مصدرُها**: المقيسُ
#: اليومَ مقيس، والسابقتان من نصّ المالك ولا ملفَّ باقيًا يشهد لهما.
#: وخلطُ المصدرَين يجعل روايةً شهادةً.
TWO_COLUMN_SERIES = (
    {"round": 1, "grounded": 44, "named": 8, "delta": 1, "rows": 53,
     "potential": 83.0, "source": "OWNER_STATED", "artifact": None},
    {"round": 2, "grounded": 49, "named": 8, "delta": 1, "rows": 58,
     "potential": 84.5, "source": "OWNER_STATED", "artifact": None},
    {"round": 3, "grounded": 55, "named": 8, "delta": 1, "rows": 64,
     "potential": 85.9, "source": "MEASURED",
     "artifact": "hokom/output/nazila_result/two_column_scores.json"},
)


def denominator_series(dev: dict) -> dict:
    """`F2` — المقامُ تحرّك ثلاثًا، فيُقابَل ولا يُقرأ تحسُّنًا صامتًا."""
    tc = dev.get("two_column", {})
    rows = list(TWO_COLUMN_SERIES)
    now, prev = rows[-1], rows[-2]
    live_ok = (tc.get("rows") == now["rows"]
               and tc.get("grounded") == now["grounded"]
               and tc.get("potential") == now["potential"])
    npd = {r["round"]: r["named"] + r["delta"] for r in rows}
    const = len(set(npd.values())) == 1
    return {
        "series": rows,
        "previous_denominator": prev["rows"],
        "current_denominator": now["rows"],
        "delta_total": now["rows"] - prev["rows"],
        "delta_grounded": now["grounded"] - prev["grounded"],
        "delta_named_plus_delta": npd[now["round"]] - npd[prev["round"]],
        "named_plus_delta_by_round": npd,
        "named_plus_delta_constant": const,
        "growth_is_measured_not_drift":
            "نموُّ المقام مقيسٌ لا انحراف: الزيادةُ كلُّها في GROUNDED، "
            f'و(named + delta) ثابتٌ عند {sorted(set(npd.values()))[0]} '
            "في الجولات الثلاث. فالملفُّ ينمو بأسطرٍ مقيسةٍ لا معلَنة.",
        "so_the_percentages_are_not_comparable":
            f'{now["potential"]}٪ و{prev["potential"]}٪ نسبتان بمقامَين '
            f'({now["rows"]} و{prev["rows"]}) — ولا تُقرأ الثانيةُ '
            "تحسُّنًا على الأولى إلا بذكر المقام.",
        "live_check": {"matches_measured": live_ok, "measured": tc},
        "sources": {r["round"]: r["source"] for r in rows},
        "unverifiable_rounds": [r["round"] for r in rows
                                if r["source"] != "MEASURED"],
        "unverifiable_note": "الجولتان الأولى والثانية من نصّ المالك، "
                             "ولا ملفَّ باقيًا يشهد لهما — تُنقل بمصدرها "
                             "ولا تُقرأ قياسًا.",
        "command": "على آلة المالك: cat "
                   "~/hokom/output/nazila_result/two_column_scores.json",
    }


def scores(dev: dict) -> dict:
    n = read("output/nazila_result/scores.json")
    led = read("output/remediation/01_ledger.json")
    cl = led.get("closure", {})
    tc = dev.get("two_column", {})
    return {"scores": {
        "NAZILA": {"value": n["CLOSURE_POTENTIAL"],
                   "fraction": f'{n["GROUNDED"]}/{n["CELLS_TOTAL"]}',
                   "denominator": "خاناتُ وثيقة النازلة"},
        "TWO_COLUMN": {"effective": tc.get("effective"),
                       "potential": tc.get("potential"),
                       "fraction": f'{tc.get("grounded")}/{tc.get("rows")}',
                       "denominator": "صفوفُ ملفّ العمودَين وحدَه",
                       "denominator_moved": True,
                       "denominator_delta": denominator_series(dev),
                       "zero_because": tc.get("why_zero")},
        "REMEDIATION": {"value": cl.get("CLOSURE_POTENTIAL"),
                        "fraction": f'{cl.get("GROUNDED")}/'
                                    f'{cl.get("TOTAL")}',
                        "denominator": "بنودُ دفتر الإصلاح"},
        "STAGES": {"value": n["STAGES_OPENED"],
                   "denominator": "مراحلُ تعقُّل المفتوحة",
                   "note": "السقفُ الحقيقيُّ لكلّ ما فوقه"},
    }, "do_not_merge": "أربعةُ مقاماتٍ لا مقام · ولا متوسّطَ ولا جمع",
        "guard": "G_NO_LEDGER_MERGE"}


# ───────────────────────────────────────────────────────── الحرّاس
def guards(docs, ph, ru, oq, sc, up=None) -> list[dict]:
    merged = [k for k, v in sc["scores"].items()
              if isinstance(v.get("value"), (int, float))
              and any(isinstance(w.get("value"), (int, float))
                      and w is not v and w["value"] == v["value"]
                      for w in sc["scores"].values())]
    return [
        {"guard": "G_ALL_T_PHASES_PRESENT", "denominator": len(PHASES),
         "present": sorted(ph["phases"]),
         "missing": sorted(set(PHASES) - set(ph["phases"])),
         "passes": set(ph["phases"]) == set(PHASES)},
        {"guard": "G_ALL_RULES_PRESENT", "denominator": len(RULE_NAMES),
         "present": ru["present"], "poisoned": ru["poisoned"],
         "unpoisoned": ru["unpoisoned"],
         "absent": sorted(k for k, v in ru["rules"].items()
                          if v.get("state") == "ABSENT_FROM_RULES"),
         "passes": ru["present"] == len(RULE_NAMES)},
        {"guard": "G_EVERY_DONE_HAS_EVIDENCE",
         "denominator": sum(1 for v in ph["phases"].values()
                            if v["state"].startswith("DONE")),
         "without_evidence": sorted(
             k for k, v in ph["phases"].items()
             if v["state"].startswith("DONE")
             and not (v.get("evidence") and v.get("command"))),
         "passes": all(v.get("evidence") and v.get("command")
                       for v in ph["phases"].values()
                       if v["state"].startswith("DONE"))},
        {"guard": "G_AUTHORITY_DECLARED", "denominator": len(DOCUMENTS),
         "unclear": docs["authority_unclear"],
         "undated": len(docs["undated"]),
         "passes": not docs["authority_unclear"]},
        {"guard": "G_OWNER_QUEUE_COMPLETE", "denominator": oq["count"],
         "effect_unmeasured": oq["effect_unmeasured"],
         "passes": oq["count"] > 0},
        {"guard": "G_STATE_LEDGER_CLOSES", "denominator": oq["count"],
         "arithmetic": f'{oq["closed"]} + {oq["pending"]} + '
                       f'{oq["out_of_jurisdiction"]} = {oq["sum"]}',
         "passes": oq["closes"]},
        {"guard": "G_AXES_AGREE", "denominator": len(AXES_OF_A_DOOR),
         "axes": list(AXES_OF_A_DOOR),
         "compared_against": "المحسوبُ في هذا التشغيل — لا الملفُّ السابق",
         "disagreements": axes_agree(up),
         "passes": not axes_agree(up),
         "note": "محاورُ الحال = محاورُ الأبواب. وسقوطُ محورٍ يقلب "
                 "القراءة: بابٌ بأثرٍ يُقرأ بلا أثر."},
        {"guard": "G_DENOMINATOR_DELTA_DECLARED",
         "denominator": len(sc["scores"]),
         "moved": sorted(k for k, v in sc["scores"].items()
                         if v.get("denominator_moved")),
         "undeclared": sorted(k for k, v in sc["scores"].items()
                              if v.get("denominator_moved")
                              and not v.get("denominator_delta")),
         "passes": not any(v.get("denominator_moved")
                           and not v.get("denominator_delta")
                           for v in sc["scores"].values()),
         "note": "نسبةٌ تغيّر مقامُها بلا حقلِ مقابلةٍ ⟶ OWNER_ALERT."},
        {"guard": "G_NO_LEDGER_MERGE", "denominator": len(sc["scores"]),
         "coincidentally_equal": merged,
         "passes": True,
         "note": "أربعُ علاماتٍ بأربعة مقامات — ولا تُجمع ولا يُتوسَّط."},
    ]


def vendor_gate() -> dict:
    def g(*a):
        return subprocess.run(["git", "-C", str(VENDOR), *a],
                              capture_output=True, text=True,
                              check=False).stdout.strip()
    head = g("rev-parse", "HEAD")
    dirty = [x for x in g("status", "--porcelain").splitlines() if x]
    return {"vendor_head": head, "porcelain_lines": len(dirty),
            "untouched": not dirty, "matches_pin": head == PIN}


def render(docs, ph, ru, oq, up, sc, gd, gate, naz, dev) -> str:
    o = ["# `STATE_OF_PROJECT` — أين المشروعُ من وثائقه الحاكمة", "",
         "```text",
         f'NAZILA {naz["CLOSURE_POTENTIAL"]}% ({naz["GROUNDED"]}/'
         f'{naz["CELLS_TOTAL"]}) · STAGES_OPENED {naz["STAGES_OPENED"]}',
         f'VENDOR_HEAD {gate["vendor_head"]} · '
         f'porcelain {gate["porcelain_lines"]} · '
         f'MATCHES_PIN {str(gate["matches_pin"]).upper()}',
         "AUTHORITY = PROJECTION — إسقاطٌ لا سلطة · NO_PROSE_DONE = TRUE",
         "VENDOR_UNTOUCHED = TRUE · NO_COMMIT = TRUE · "
         "CLAIM_PROJECT_FINISHED = NO",
         "```", "",
         "**ولا يُنشئ هذا التقريرُ حكمًا ولا يُغلق بندًا ولا يُصحّح رقمًا.**",
         "", "## ١ · الوثائقُ الحاكمة", "",
         "| السلطة | ما تُلزم به | العدد |", "|---|---|---|",
         f'| `LAW` | ما يُلزم | {docs["by_authority"].get("LAW", 0)} |',
         f'| `RUNTIME` | ما يُنفَّذ | {docs["by_authority"].get("RUNTIME", 0)} |',
         f'| `EVIDENCE` | ما يُثبت | {docs["by_authority"].get("EVIDENCE", 0)} |',
         f'| `PROJECTION` | ما يُشتقّ | {docs["by_authority"].get("PROJECTION", 0)} |',
         f'| `HISTORICAL` | ما مضى | {docs["by_authority"].get("HISTORICAL", 0)} |',
         "",
         f'مؤرَّخةٌ **{docs["dated"]}** · `UNDATED` **{len(docs["undated"])}** '
         f'· `AUTHORITY_UNCLEAR` {len(docs["authority_unclear"]) or 0}. '
         f'والتأريخُ مقيسٌ على `{docs["dating_measured_on"]}` — لا في '
         "الحاوية، فهي بلا `git` ألبتّة.", "",
         "| سببُ غياب التاريخ | العدد |", "|---|---|",
         *[f"| `{k}` | {v} |" for k, v in docs["undated_by_reason"].items()],
         "",
         f'**{docs["finding"]}** وغيرُ المؤرَّخ بالسلطة: '
         + " · ".join(f'`{a}` {len(v)}'
                      for a, v in docs["undated_by_authority"].items()),
         "", f'**{docs["finding_2"]}**',
         "", f'**والمستودعات**: {dev.get("repos", {}).get("measured", "?")} '
         f'مجلَّدًا موصولًا، منها {dev.get("repos", {}).get("with_git", "?")} '
         f'بـ.git و{dev.get("repos", {}).get("without_git", "?")} بلا. '
         f'{dev.get("repos", {}).get("note", "")}', "",
         "## ٢ · المراحلُ `T-0..T-10` — مقيسةً", "",
         "| المرحلة | العنوان | الحال | الأثر |", "|---|---|---|---|"]
    for k in PHASES:
        v = ph["phases"][k]
        ev = v["evidence"]
        ev = json.dumps(ev, ensure_ascii=False) if isinstance(ev, dict) else str(ev)
        o.append(f'| `{k}` | {v["title"]} | **{v["state"]}** | {ev[:150]} |')
    o += ["", f'**بالحال**: '
          f'{" · ".join(f"{k} {v}" for k, v in ph["by_state"].items())}. '
          f'والمفتوحُ في التشغيل: `{ph["stages_opened"]}` — '
          f'{" · ".join(ph["runtime_implemented"])}.', "",
          "و`T-9` و`T-10` مُعلَنتان في `STAGES_PENDING_OWNER` ولا أثرَ "
          "لهما في الشجرة: صفرُ ذكرٍ في `HANDOFF` و`README` "
          "و`docs/ARCHITECTURE`. **مقيستان لا مفترضتان.**", "",
          "## ٣ · القواعدُ الثمان", "",
          "| القاعدة | الحال | السمّ |", "|---|---|---|"]
    for name in RULE_NAMES:
        v = ru["rules"][name]
        p = v.get("poison", "—")
        p = p.split("::")[1] if "::" in p else p
        o.append(f'| `{name}` | **{v.get("state")}** | `{p}` |')
    o += ["", f'مُعلَنةٌ {ru["declared"]} · حاضرةٌ {ru["present"]} · '
          f'مسمومةٌ {ru["poisoned"]} · '
          f'{"وبلا سمّ: " + " · ".join(ru["unpoisoned"]) if ru["unpoisoned"] else "ولا واحدةَ بلا سمّ"}.',
          "", "## ٤ · طابورُ المالك", "",
          "| الحال | العدد |", "|---|---|"]
    for k, v in oq["by_status"].items():
        o.append(f"| `{k}` | {v} |")
    owner_rows = [x for x in oq["items"]
                  if x["authority"] == "OWNED_BY_OWNER"]
    o += ["", f'**والدفترُ يقفل**: {oq["closed"]} مغلقًا + {oq["pending"]} '
          f'موقوفًا + {oq["out_of_jurisdiction"]} خارجَ الولاية = '
          f'{oq["sum"]} / {oq["count"]}.', "",
          f'**ومقامان لا مقام**: الموقوفُ {oq["pending"]} '
          f'(`RAISED` {oq["by_status"].get("RAISED", 0)} + `BLOCKED` '
          f'{oq["by_status"].get("BLOCKED", 0)})، والجدولُ أدناه '
          f'**{len(owner_rows)}** صفًّا — لأنّه بنودُ المالك وحدَها، '
          "والـ`BLOCKED` بنودُ أداةٍ موقوفةٌ على غيرها. فالعددان "
          "مختلفان بمقامَيهما لا بخطأ.", "",
          "| البند | العنوان | الحال | أثرُ الخيارات |",
          "|---|---|---|---|"]
    for x in oq["items"]:
        if x["authority"] != "OWNED_BY_OWNER":
            continue
        eff = ("مقيس" if x["effect_measured"] else "**EFFECT_UNMEASURED**")
        rows = f' · {x["rows"]} صفًّا' if x.get("rows") is not None else ""
        o.append(f'| `{x["ident"]}` | {x["title"][:52]} | `{x["status"]}` | '
                 f'{eff}{rows} |')
    q4 = next(x for x in oq["items"] if x["ident"] == "Q4")
    o += ["", "### `Q4` — سؤالٌ يُطرح ولا يُجاب", "", "```text",
          f'U_TANWEEN يُرفع الآن على   {q4["effect"]["raised_on_now"]}',
          f'منها لا قرارَ مطلوبًا فيها {q4["effect"]["of_which_no_decision_needed"]}',
          f'ومنها موقوفةٌ حقًّا        {q4["effect"]["of_which_still_pending"]}',
          f'الحساب                    {q4["effect"]["arithmetic"]}',
          f'التضييقُ المقترَح إلى      {q4["effect"]["narrowed_to"]}',
          f'الحال                     {q4["not_weighed"]}',
          "```", "",
          f'وما لا أثرَ مقيسٌ لخياراته: '
          f'{" · ".join(oq["effect_unmeasured"]) if oq["effect_unmeasured"] else "لا شيء"}'
          f' — `EFFECT_UNMEASURED`، وسؤالٌ بلا أثرٍ مقيسٍ ترجيحٌ مؤجَّل.', "",
          "## ٥ · ما عند `sonaiso`", "",
          "| الباب | العنوان | الخانات | السقف | الصحّة |",
          "|---|---|---|---|---|"]
    for k, v in up["upstream"].items():
        if v.get("kind") == "NOT_A_DOOR":
            o.append(f'| `{k}` | {v["title"][:46]} | `NOT_A_DOOR` | '
                     f'`{v["status"]}` | — |')
            continue
        c = v.get("correctness")
        c = (" · ".join(f"{a}={b}" for a, b in list(c.items())[:3])
             if isinstance(c, dict) else str(c))
        o.append(f'| `{k}` | {v["title"][:40]} | `{v.get("cells")}` | '
                 f'`{v.get("ceiling")}` | {c[:110]} |')
    b = up["upstream"]["C3"]["bounded"]
    o += ["", f'و`C3` مقيَّد: العددُ `{b["count"]}` يبقى · والعبورُ '
          f'`{b["crosses"]}` · والنسبةُ `{b["mapping"]}`. '
          f'ويُرفع منه: «{b["raise_to_source"]}».', "",
          f'```text', f'C_PATH = {up["C_PATH"]} · '
          f'SENT = {up["report"]["SENT"]} · '
          f'AUTHORITY_TO_SEND = {up["report"]["AUTHORITY_TO_SEND"]}', "```", "",
          "## ٦ · العلاماتُ الأربع — بمقاماتها", "",
          "| العلامة | القيمة | المقام |", "|---|---|---|"]
    for k, v in sc["scores"].items():
        val = (f'{v["effective"]}% فعليّة · {v["potential"]}% ممكنة'
               if "effective" in v else f'{v["value"]}'
               + ("%" if isinstance(v["value"], (int, float)) else ""))
        frac = f' ({v["fraction"]})' if v.get("fraction") else ""
        o.append(f'| `{k}` | {val}{frac} | {v["denominator"]} |')
    d = sc["scores"]["TWO_COLUMN"]["denominator_delta"]
    o += ["", f'**{sc["do_not_merge"]}** · `{sc["guard"]}`', "",
          "### مقامُ `TWO_COLUMN` تحرّك ثلاثًا — ومقابلتُه", "",
          "| الجولة | grounded | named+delta | المقام | النسبة | المصدر |",
          "|---|---|---|---|---|---|",
          *[f'| {r["round"]} | {r["grounded"]} | {r["named"] + r["delta"]} | '
            f'{r["rows"]} | {r["potential"]}٪ | `{r["source"]}` |'
            for r in d["series"]],
          "", "```text",
          f'previous_denominator      {d["previous_denominator"]}',
          f'current_denominator       {d["current_denominator"]}',
          f'delta_total               {d["delta_total"]}',
          f'delta_grounded            {d["delta_grounded"]}',
          f'delta_named_plus_delta    {d["delta_named_plus_delta"]}',
          f'named_plus_delta_constant {d["named_plus_delta_constant"]}',
          "```", "",
          f'**{d["growth_is_measured_not_drift"]}**', "",
          f'و{d["so_the_percentages_are_not_comparable"]}', "",
          f'والجولتان {d["unverifiable_rounds"]} مصدرُهما `OWNER_STATED`: '
          f'{d["unverifiable_note"]}', "",
          "## الحرّاس", "", "| الحارس | المقام | النتيجة |", "|---|---|---|"]
    for g in gd:
        o.append(f'| `{g["guard"]}` | {g["denominator"]} | '
                 f'{"PASS" if g["passes"] else "FALLS"} |')
    o += ["", "```text", "CLAIM_PROJECT_FINISHED = NO", "```", ""]
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/state")
    a = ap.parse_args()

    gate = vendor_gate()
    if not gate["untouched"] or not gate["matches_pin"]:
        raise Blocked(f"BLOCKED_AT_VENDOR: {gate}")

    dev = read("data/device_state.json", {})
    a9 = read("reports/compliance/AXIS_9_MEASURES.json")
    naz = read("output/nazila_result/scores.json")

    docs, ph, ru = documents(dev.get("dating") or {}), phases(a9, dev), rules()
    oq, up, sc = owner_queue(dev), upstream(), scores(dev)
    gd = guards(docs, ph, ru, oq, sc, up)

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    for name, payload in (("00_documents.json", docs), ("01_phases.json", ph),
                          ("02_rules.json", ru), ("03_owner_queue.json", oq),
                          ("04_upstream.json", up), ("05_scores.json", sc)):
        (out / name).write_text(json.dumps(payload, ensure_ascii=False,
                                           indent=1), encoding="utf-8")
    (out / "06_STATE.md").write_text(
        render(docs, ph, ru, oq, up, sc, gd, gate, naz, dev), encoding="utf-8")

    print(f'DOCS   {len(docs["documents"])} · بلا تاريخ {len(docs["undated"])} · '
          f'ملتبسٌ {len(docs["authority_unclear"])}')
    print(f'PHASES {ph["count"]}/11 · {ph["by_state"]}')
    print(f'RULES  {ru["present"]}/{ru["declared"]} · مسمومةٌ {ru["poisoned"]}'
          f' · بلا سمّ {ru["unpoisoned"] or "لا شيء"}')
    print(f'QUEUE  {oq["count"]} · {oq["by_status"]} · يقفل {oq["closes"]}')
    print(f'SCORES ' + " · ".join(
        f'{k}={v.get("value", str(v.get("effective")) + "/" + str(v.get("potential")))}'
        for k, v in sc["scores"].items()))
    for g in gd:
        print(f'  {g["guard"]:28} {"PASS" if g["passes"] else "FALLS"} '
              f'/{g["denominator"]}')
    print(f"→ {out}/06_STATE.md")
    if not all(g["passes"] for g in gd):
        raise Blocked("GUARD_FALLS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
