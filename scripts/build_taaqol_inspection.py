#!/usr/bin/env python3
"""مولّدُ تقرير الفحص الدستوريّ — أسلوط × تعقُّل.

`RULE_OWNER = DR_HUSSEIN` · `MEASURED_NOT_PRESET`

    python3 scripts/build_taaqol_inspection.py --out taaqol_inspection.html \
        --f1-dir inspection/runs/f1 --f2-dir inspection/runs/f2 \
        --f3-dir inspection/runs/f3 --operators-csv <ملف> \
        --engine-commit <sha> --taaqol-commit <sha> \
        --mark-order-cmd 'python3 -m aslot.tools.mark_order --check'

**بمَ يختلف عن المسوَّدة التي أرسلها المالك.** التصميمُ تصميمُه: رقاقةُ سندٍ
على كلّ رقم، وحاشيةُ قانونٍ بجوار كلّ فصل، وعرضان — عرضُ المالك وعرضُ
المهندس — وبوّابةُ ترتيب العلامات تفشل مغلقة، والإثباتُ الموجَب قبل نفي
الإخفاق، و`P4` مبنيٌّ فيه فلا يُسنِد صنفَ بقيّةٍ من عنده.

والفرقُ أنّ ثلاثة أقسامٍ كانت `UNMEASURED` في المسوّدة **صارت مقيسة**، لأنّ
`T-1` و`T-3` منفَّذتان في المحرّك فعلًا:

    جردُ الرفض المسمّى   ← يُقرأ من أعمدة الحكم في المخرجات
    الأثرُ والمرساة      ← يُعاد بناؤه ويُقابَل، لا يُعدّ فقط
    تغطيةُ العوامل (F2)  ← تُقاس بمطابقة كلّ عاملٍ في شاهده

وطبعُ `UNMEASURED` لما هو مقيسٌ فعلًا **دعوى معكوسة**: كما أنّ الصفرَ في
موضع المجهول دعوى، فالمجهولُ في موضع المقيس تهوينٌ من الحجّة.

ولم يُعَد طبعُ نصوص المسوّدة العربية هنا: إعادةُ طبع سطحٍ مشكولٍ هي بعينها
ما تمنعه قاعدةُ المالك. والنصّان يُقرآن من ملفّيهما، ويمرّان على البوّابة.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import json
import os
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

UNMEASURED = "UNMEASURED"
ABSENT = "SOURCE_ABSENT"

# ── الحواملُ الدستوريّة، تُعرض كاملةً ولو كانت أصفارًا ────────────────────
CLOSURE_STATES = [
    ("MINIMALLY_CLOSED", "مغلقٌ أدنى غلق", "accept"),
    ("PERFORATED_CLOSED", "مغلقٌ مثقوب — أُغلق وبقيّةٌ ظاهرة", "accept"),
    ("OPEN", "مفتوح — خانةٌ لازمةٌ فارغة", "defer"),
    ("BLOCKED", "محجوب — بقيّةٌ حاجبة", "block"),
    ("INVALID", "باطل — نقصٌ في الهويّة أو الأثر أو الحدّ", "block"),
    ("FORBIDDEN_LEAP", "قفزةٌ ممنوعة — تجاوزُ الطبقة المُعلَنة", "block"),
]
TRANSITION_STATES = [
    ("APPROVED", "أُذن بالانتقال"), ("DEFERRED", "تأجيل — لا دليلَ بعد"),
    ("BLOCKED", "حجب — بقيّةٌ حاجبة"),
    ("REJECTED", "ردّ — ترقيةُ رتبةٍ خارج بوّابة"),
    ("FORBIDDEN_LEAP", "خطٌّ مستقيمٌ مسجَّل"),
]
RANKS = ["ZERO", "TRACE", "CANDIDATE", "HYPOTHESIS", "LICENSED", "STRONG",
         "CERTIFICATE"]
RESIDUAL_KINDS = [
    ("BLOCKING", "حاجبة", "ZERO"),
    ("HIDDEN_FORBIDDEN", "مخفيّة — خرقٌ قاتل", "ZERO"),
    ("DEFERRABLE", "مؤجَّلة", "HYPOTHESIS"),
    ("NON_BLOCKING", "غيرُ حاجبة", "— لا قيد"),
    ("EXPLANATORY", "تفسيريّة", "— لا قيد"),
]
FORBIDDEN_LINES = [
    ("Signifier", "WordForm", "MorphologicalRealisationGate", "المحور ٤ — التقشير"),
    ("WordForm", "Meaning", "SignificationGate", "لم يُفتح"),
    ("Root", "LexicalMeaning", "DerivationGate", "CL-16"),
    ("Weight", "Agency", "RelationRoleGate", "الصرف ≠ النحو"),
    ("Pattern", "SyntaxRole", "RelationRoleGate", "المحور ٢"),
    ("Relation", "Ifādah", "IfadahGate", "لم يُفتح"),
    ("Evidence", "Certainty", "RankLattice (no auto-promote)", "الرتبة"),
    ("HarakaMark", "CaseFunction", "HarakaFunctionGate", "المحور ٣/٤"),
]
VERTICAL_NOT_OPENED = [
    ("MufradDalalahClosure", "دلالةُ المفرد"), ("RelationClosure", "غلقُ العلاقة"),
    ("IfadahCandidate", "الإفادة"), ("HukmCandidate", "الحكم"),
    ("ManatCandidate", "المناط"), ("TanzilCandidate", "التنزيل"),
    ("AnswerAudit", "تدقيقُ الجواب"),
]
ENTRY_BOUNDARY = [
    ("declared_entry_kind", "VOCALIZED_ARABIC_TEXT", "نصٌّ عربيٌّ مشكول"),
    ("representation_status", "REPRESENTATIONAL", "تمثيلٌ لا أصل"),
    ("ontological_status", "NOT_AN_ONTOLOGICAL_ORIGIN", "ليس مصدرًا وجوديًّا"),
    ("sound_status", "NOT_A_SOUND", "ليس صوتًا"),
    ("meaning_status", "NOT_A_MEANING", "ليس معنًى"),
    ("prior_trace_status", "PRIOR_TRACE_PRESERVED", "الأثرُ السابقُ محفوظ"),
    ("produces_only", "TextTraceCandidate", "لا يُنتج إلا مرشَّحَ أثرٍ نصّيّ"),
]
AXIS_FILES = {
    0: ("QURAN_WORDS.csv", "بناءُ النصّ"),
    1: ("AXIS_1_NORMALIZATION.csv", "التطبيع"),
    2: ("AXIS_2_TOKENS.csv", "العواملُ والمبنيّات"),
    3: ("AXIS_3_SYLLABLES.csv", "المقاطعُ الصوتيّة"),
    4: ("AXIS_4_PEEL_TO_STEM.csv", "التقشير"),
}
VERDICT_COLUMNS = ("Normalization_Status", "Stop_Reason", "Closed_Form_Proof",
                   "Eligibility", "Next_Route", "Verdict", "Block_Reason",
                   "Termination")


# ── القياس ───────────────────────────────────────────────────────────────
def sha256_of(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    try:
        return sha256_of(path.read_bytes())
    except OSError:
        return ABSENT


def text_stats(text: str) -> dict:
    toks = text.split()
    return {"chars": len(text), "tokens": len(toks), "unique": len(set(toks)),
            "sha256": sha256_of(text.encode("utf-8"))}


def read_rows(path: Path | None) -> list[dict] | None:
    if path is None or not path.exists():
        return None
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


def load_run(run_dir: Path | None) -> dict:
    out = {"dir": str(run_dir) if run_dir else ABSENT, "axes": {}}
    for idx, (fname, label) in AXIS_FILES.items():
        rows = None
        if run_dir:
            for cand in (run_dir / f"axis{idx}" / fname, run_dir / fname):
                if cand.exists():
                    rows = read_rows(cand)
                    break
        anchored = recon = UNMEASURED
        if rows is not None:
            from aslot.trace import anchor, parent_anchor
            anchored = sum(1 for r in rows if (r.get("Trace_Anchor") or "").strip())
            recon = 0
            for r in rows:
                try:
                    pos = (int(r["Sura_No"]), int(r["Verse_No"]), int(r["Word_No"]))
                except (KeyError, ValueError):
                    continue
                if (r.get("Trace_Anchor") == anchor(idx, *pos)
                        and r.get("Parent_Anchor") == parent_anchor(idx, *pos)):
                    recon += 1
        out["axes"][idx] = {
            "label": label, "file": fname,
            "rows": len(rows) if rows is not None else UNMEASURED,
            "verdicts": dict(Counter((r.get("Verdict") or "").strip() for r in rows
                                     if (r.get("Verdict") or "").strip()))
            if rows else UNMEASURED,
            "trace_anchors": anchored, "reconstructed": recon, "_rows": rows,
        }
    return out


def failure_inventory(runs: list[dict]) -> dict:
    """جردُ الرفض — **مقيسٌ ومقسومٌ**، لا خلطَ فيه.

    وحكمُ المالك في المرفوع إليه: «`٩ شذوذ` جردٌ مختلط». والخلطُ أن يُجمع في
    عمودٍ واحد ما أُعلن اسمًا في التاكسونومية وما لم يُعلن. فالقسمةُ هنا
    ثلاثٌ، ومرجعُها `ASLOT_REFUSALS` المُعلَنة في الجسر — لا تصنيفٌ من عندي:

        WITNESSED    مُعلَنٌ وله شاهدٌ في هذه الجولة
        UNWITNESSED  مُعلَنٌ ولا شاهدَ له هنا — إعلانٌ لا خرق
        UNDECLARED   ظهر في مخرجٍ ولم يُعلَن — **خرقٌ يُسمّى**، لا يُبتلع
    """
    seen: Counter = Counter()
    for run in runs:
        for axis in run["axes"].values():
            for row in axis["_rows"] or []:
                for col in VERDICT_COLUMNS:
                    value = (row.get(col) or "").strip()
                    if value:
                        seen[value.split("@")[0].split(":")[0]] += 1
    try:
        from aslot.taaqol import ASLOT_REFUSALS
        declared = set(ASLOT_REFUSALS)
    except Exception:
        return {"status": UNMEASURED, "counts": dict(seen)}
    return {
        "status": "MEASURED",
        "declared": len(declared),
        "witnessed": {k: v for k, v in seen.items() if k in declared},
        "unwitnessed": sorted(declared - set(seen)),
        "undeclared": {k: v for k, v in seen.items() if k not in declared},
    }


def trace_totals(runs: list[dict]) -> dict:
    """الأثر — **مقيس**: يُعاد بناءُ كلّ مرساةٍ من موضعها وتُقابَل."""
    rows = anchored = recon = 0
    any_measured = False
    for run in runs:
        for axis in run["axes"].values():
            if axis["rows"] == UNMEASURED:
                continue
            any_measured = True
            rows += axis["rows"]
            anchored += axis["trace_anchors"]
            recon += axis["reconstructed"]
    if not any_measured:
        return dict.fromkeys(("rows", "anchored", "without", "reconstructed"), UNMEASURED)
    return {"rows": rows, "anchored": anchored, "without": rows - anchored,
            "reconstructed": recon}


def load_operators(path: Path | None) -> dict:
    if path is None or not path.exists():
        return {"status": ABSENT, "path": str(path) if path else "—",
                "count": UNMEASURED, "with_example": UNMEASURED,
                "sha256": ABSENT, "rows": None, "example_column": UNMEASURED}
    rows = read_rows(path)
    cols = list(rows[0].keys()) if rows else []
    col = next((c for c in cols if c.strip().lower() == "example_vocalized"), None)
    return {
        "status": "LOADED", "path": str(path), "count": len(rows),
        "with_example": sum(1 for r in rows if col and (r.get(col) or "").strip()),
        "unique_operators": len({(r.get("Operator") or "").strip() for r in rows
                                 if (r.get("Operator") or "").strip()}),
        "example_column": col or "MISSING:Example_Vocalized",
        "sha256": sha256_file(path), "rows": rows,
    }


def operator_coverage(operators: dict, run: dict, input_path: Path | None) -> dict:
    """تغطيةُ المحور الثاني لكلّ عاملٍ **في شاهده هو** — لا في المجموع.

    ولا يُقرأ منها ترخيص: `LICENSE_GRANTED = NO` قائمٌ حتى يعتمد المالكُ
    الجدول. وإنّما تسأل سؤالًا واحدًا: هل رأى المحورُ الثاني العاملَ حيث هو؟

    **ولمَ في شاهده لا في المجموع.** لو قُوبل العاملُ بمجموع ما ثبت في النصّ
    كلِّه لصار العددُ أكبرَ وأضعف: عاملٌ ثبت في سطرِ غيره لا يُثبت أنّ سطرَه
    هو رُئي. فيُعاد بناءُ الموضع: يُطابَق نصُّ كلِّ شاهدٍ بسطره في المدخل،
    فيُعرف رقمُ آيته، ثمّ يُبحث العاملُ في صفوف تلك الآية وحدها.

    وثلاثةُ مخارجَ لا اثنان، لأنّ **الحرفَ المتّصل ليس توكنًا قائمًا**:
    فـ«بِ» في «بِزَيْدٍ» لا تظهر صفًّا، والمحورُ الثاني جردُ كلماتٍ تامّةٍ
    مغلقة. وعدُّ ذلك «إخفاقًا» خلطٌ، وعدُّه «نجاحًا» دعوى — فيُسمّى
    `NOT_A_STANDALONE_TOKEN` ويُترك لحكم المالك.
    """
    rows = run["axes"][2]["_rows"]
    if not operators.get("rows") or rows is None:
        return {"status": UNMEASURED}
    from aslot.axes.axis1_normalization import normalize_token

    verses: dict[str, str] = {}
    if input_path and input_path.is_file():
        for line in input_path.read_text(encoding="utf-8").splitlines():
            parts = line.split("|")
            if len(parts) >= 3:
                verses["|".join(parts[2:]).strip()] = parts[1]

    by_verse: dict[str, list[dict]] = {}
    for row in rows:
        by_verse.setdefault(row.get("Verse_No", ""), []).append(row)

    out = Counter()
    for entry in operators["rows"]:
        surface = (entry.get("Operator") or "").strip()
        example = (entry.get("Example_Vocalized") or "").strip()
        if not surface:
            continue
        verse = verses.get(example)
        if verse is None:
            out["WITNESS_NOT_LOCATED"] += 1
            continue
        try:
            norm = normalize_token(surface).normalized
        except Exception:
            out["NOT_NORMALIZABLE"] += 1
            continue
        here = by_verse.get(verse, [])
        same = [r for r in here
                if (r.get("Normalized_Word") or "").strip() == norm]
        if any((r.get("Closed_Form_Proof") or "").strip() == "PROVEN"
               for r in same):
            out["PROVEN_IN_ITS_OWN_WITNESS"] += 1
        elif same:
            out["PRESENT_BUT_NOT_PROVEN"] += 1
        else:
            out["NOT_A_STANDALONE_TOKEN"] += 1
    return {"status": "MEASURED", "buckets": dict(out), "total": sum(out.values())}


def mark_order_gate(cmd: str | None, files: list[Path]) -> dict:
    if not cmd:
        return {"verified": False, "reason": "لم يُمرَّر --mark-order-cmd",
                "deviations": UNMEASURED, "scanned": UNMEASURED}
    devs = scanned = 0
    for f in files:
        if not f.exists():
            return {"verified": False, "reason": f"ملفٌّ غائب: {f.name}",
                    "deviations": UNMEASURED, "scanned": UNMEASURED}
        try:
            root = Path(__file__).resolve().parents[1]
            env = {**os.environ, "PYTHONPATH": str(root / "src")}
            res = subprocess.run([*cmd.split(), str(f)], capture_output=True,
                                 text=True, timeout=120, check=False,
                                 cwd=str(root), env=env)
        except Exception as exc:
            return {"verified": False, "reason": f"تعذّر التشغيل: {exc}",
                    "deviations": UNMEASURED, "scanned": UNMEASURED}
        if res.returncode != 0:
            return {"verified": False, "reason": f"رجع {res.returncode} على {f.name}",
                    "deviations": UNMEASURED, "scanned": UNMEASURED}
        # تُقرأ الخلاصةُ المُعلَنة، ولا تُستنبط بعدِّ البادئات: «DEVIATIONS 0»
        # تبدأ بـ«DEVIATION» أيضًا، فعدُّ البادئة يقلب صفرًا إلى واحد. وهذه
        # هي الواقعةُ نفسُها في صورةٍ ثالثة: فحصٌ يفشل لعلّةٍ خاطئة.
        summary = {ln.split()[0]: ln.split()[1] for ln in res.stdout.splitlines()
                   if ln.split()[:1] and ln.split()[0] in ("SCANNED", "DEVIATIONS")
                   and len(ln.split()) > 1}
        if {"SCANNED", "DEVIATIONS"} - set(summary):
            return {"verified": False,
                    "reason": f"لم تُعلَن خلاصةُ البوّابة على {f.name}",
                    "deviations": UNMEASURED, "scanned": UNMEASURED}
        scanned += int(summary["SCANNED"])
        devs += int(summary["DEVIATIONS"])
    return {"verified": devs == 0 and scanned > 0,
            "reason": ("مقابَلٌ بترتيب العلامات" if scanned else
                       "لم يُفحص سطحٌ واحد — والصفرُ في مخرجٍ فارغٍ ليس سلامة"),
            "deviations": devs, "scanned": scanned}


def carry_ledger(run: dict) -> list[dict]:
    """دفترُ الحمل — كلُّ صفٍّ لم ينتقل إلى المحور التالي **يُسمّى سببُه**.

    والعلّةُ حكمُ المالك في المرفوع إليه: «`1 skipped` … تخطٍّ صامتٌ بلا سبب».
    والتخطّي الصامت لا يُعالَج بطبع رقمِه، بل بإغلاق الدفتر: `دخل = خرج +
    مسمَّى`، فإن بقيت بقيّةٌ بلا اسمٍ ظهرت في العمود الأخير ولم تُبتلَع.
    """
    out: list[dict] = []
    for src, dst in ((0, 1), (1, 2), (2, 3), (3, 4)):
        a, b = run["axes"][src], run["axes"][dst]
        if a["_rows"] is None or b["_rows"] is None:
            out.append({"edge": f"{src} → {dst}", "into": UNMEASURED,
                        "carried": UNMEASURED, "named": {}, "unnamed": UNMEASURED})
            continue

        def key(row: dict) -> tuple:
            return (row.get("Sura_No"), row.get("Verse_No"), row.get("Word_No"))

        kept = {key(r) for r in b["_rows"]}
        dropped = [r for r in a["_rows"] if key(r) not in kept]
        named: Counter = Counter()
        unnamed = 0
        for row in dropped:
            reason = next((row[c].strip() for c in VERDICT_COLUMNS
                           if (row.get(c) or "").strip()), "")
            if reason:
                named[reason.split("@")[0]] += 1
            else:
                unnamed += 1
        out.append({"edge": f"{src} → {dst}", "into": len(a["_rows"]),
                    "carried": len(b["_rows"]), "named": dict(named),
                    "unnamed": unnamed})
    return out


def owner_classes_of(run_dir: Path | None) -> dict:
    """أصنافُ قرار المالك، مقيسةً من مقاييس المحور الأول لهذه الجولة."""
    if run_dir is None:
        return {}
    path = run_dir / "axis1" / "AXIS_1_MEASURES.json"
    if not path.is_file():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data.get("owner_decision_classes", {})


def positive_assertions(run: dict, expected_rows) -> list[dict]:
    """الإثباتُ الموجَب: لا يُقرأ صفرُ إخفاقٍ قبل إثبات الجريان."""
    axes_run = sum(1 for a in run["axes"].values() if a["rows"] != UNMEASURED)
    got0 = run["axes"][0]["rows"]
    anchored = run["axes"][0]["trace_anchors"]
    return [
        {"name": "axes_run == 5", "got": axes_run, "want": 5, "ok": axes_run == 5,
         "why": "مخرجٌ خالٍ من المحاور يعطي صفرَ إخفاقاتٍ أيضًا. الصفرُ لا يُقرأ "
                "قبل إثبات الجريان."},
        {"name": "rows(axis0) == tokens(fixture)", "got": got0, "want": expected_rows,
         "ok": got0 == expected_rows,
         "why": "عددُ صفوف المحور صفر يجب أن يطابق عددَ توكنات المثبَّت، وإلا فقد "
                "سقط شيءٌ صامتًا."},
        {"name": "rows_without_anchor == 0", "got": anchored, "want": got0,
         "ok": anchored != UNMEASURED and anchored == got0,
         "why": "Γ خطوة ٢ ترفض كلَّ صفٍّ بلا مرساةِ أثر."},
    ]


# ── التصيير ──────────────────────────────────────────────────────────────
CSS = """
:root{--paper:#F6F2E9;--ink:#191D25;--muted:#5F6672;--rule:#DED6C4;--rule-2:#EFE9DC;
--indigo:#233252;--accept:#2E5D42;--defer:#95670E;--block:#8C2E2A;--idle:#767C86;
--mono:ui-monospace,SFMono-Regular,"SF Mono",Menlo,Consolas,monospace;
--naskh:"Amiri","Scheherazade New","Noto Naskh Arabic",
  "Traditional Arabic","Times New Roman",serif;}
*{box-sizing:border-box}html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--paper);color:var(--ink);font-family:var(--naskh);
font-size:17px;line-height:1.85;font-feature-settings:"kern" 1}
.page{max-width:1080px;margin:0 auto;padding:32px 24px 96px}
.sec{display:grid;grid-template-columns:1fr 172px;gap:28px;
border-top:1px solid var(--rule);padding:34px 0 6px;align-items:start}
.sec>.body{min-width:0}
.gloss{font-family:var(--mono);font-size:11.5px;line-height:1.75;color:var(--muted);
border-inline-start:2px solid var(--rule);padding-inline-start:10px;position:sticky;top:16px}
.gloss b{display:block;color:var(--indigo);font-weight:600;margin-bottom:3px}
@media(max-width:820px){.sec{grid-template-columns:1fr}.gloss{position:static;
border-inline-start:0;border-top:1px solid var(--rule);padding:8px 0 0;margin-top:12px}}
h1{font-size:34px;line-height:1.35;margin:0 0 6px;font-weight:700;letter-spacing:-.01em}
h2{font-size:23px;margin:0 0 14px;font-weight:700;color:var(--indigo)}
h3{font-size:17px;margin:22px 0 8px;font-weight:700}
p{margin:0 0 12px;max-width:74ch}.lede{color:var(--muted);max-width:70ch}
.seal{border:2px solid var(--indigo);background:#fff;padding:22px 24px;margin:24px 0 8px}
.seal .verdict{font-size:27px;font-weight:700;color:var(--indigo);margin-bottom:10px}
.seal dl{display:grid;grid-template-columns:auto 1fr;gap:4px 14px;margin:0;font-size:15.5px}
.seal dt{font-weight:700;color:var(--indigo)}.seal dd{margin:0;color:var(--ink)}
.p{font-family:var(--mono);font-size:10.5px;padding:1px 6px;border-radius:2px;
vertical-align:2px;white-space:nowrap;border:1px solid transparent}
.p-m{background:#E4EDE6;color:var(--accept);border-color:#C6DACB}
.p-u{background:#F0EBE0;color:var(--muted);border-color:var(--rule)}
.p-o{background:#EDE9F2;color:var(--indigo);border-color:#D6CEE2}
.num{font-family:var(--mono);font-variant-numeric:tabular-nums;font-weight:600}
.big{font-size:30px;line-height:1.1;display:block;font-family:var(--mono);
font-variant-numeric:tabular-nums}
.tiles{display:flex;flex-wrap:wrap;gap:10px;margin:14px 0}
.tile{flex:1 1 152px;border:1px solid var(--rule);background:#fff;padding:12px 14px}
.tile .lbl{font-size:13px;color:var(--muted);display:block;margin-top:4px}
table{border-collapse:collapse;width:100%;margin:12px 0 4px;font-size:14.5px;background:#fff}
th,td{border:1px solid var(--rule-2);padding:7px 10px;text-align:start;vertical-align:top}
th{background:#F0EBDF;font-weight:700;color:var(--indigo);font-size:13.5px}
td.n{font-family:var(--mono);font-variant-numeric:tabular-nums;text-align:end;white-space:nowrap}
td.code,th.code{font-family:var(--mono);font-size:12.5px}
tbody tr:nth-child(even){background:#FCFAF6}
.v{font-weight:700}.v-accept{color:var(--accept)}.v-defer{color:var(--defer)}
.v-block{color:var(--block)}.v-idle{color:var(--idle)}
.dot{display:inline-block;width:8px;height:8px;border-radius:50%;margin-inline-end:6px;vertical-align:1px}
.d-accept{background:var(--accept)}.d-defer{background:var(--defer)}
.d-block{background:var(--block)}.d-idle{background:var(--idle)}
.ar{font-size:19px;line-height:2.15}
.kv{font-family:var(--mono);font-size:12.5px;background:#fff;border:1px solid var(--rule);
padding:12px 14px;white-space:pre-wrap;overflow-x:auto;direction:ltr;text-align:left;
line-height:1.8;margin:12px 0}
.eng{display:none}body[data-view="eng"] .eng{display:revert}
body[data-view="eng"] .own{display:none}
.own.note{color:var(--muted);font-size:15px;border-inline-start:2px solid var(--rule);
padding-inline-start:12px;margin:10px 0 14px;max-width:66ch}
.switch{display:flex;gap:0;border:1px solid var(--indigo);width:max-content;margin:18px 0 0}
.switch button{font-family:inherit;font-size:14.5px;padding:7px 18px;border:0;
background:#fff;color:var(--indigo);cursor:pointer}
.switch button[aria-pressed="true"]{background:var(--indigo);color:#fff}
.switch button:focus-visible{outline:2px solid var(--defer);outline-offset:-4px}
.warn{border:1px solid var(--block);background:#FBF2F1;padding:14px 16px;margin:14px 0}
.warn b{color:var(--block)}
.ok-box{border:1px solid var(--accept);background:#F1F6F2;padding:14px 16px;margin:14px 0}
.meta{color:var(--muted);font-size:13.5px}
footer{border-top:1px solid var(--rule);margin-top:40px;padding-top:18px;
  color:var(--muted);font-size:13.5px}
@media print{body{background:#fff}.switch{display:none}.gloss{position:static}
.eng{display:revert!important}.own{display:none!important}}
"""

E = html.escape


def chip(kind: str) -> str:
    return {"M": '<span class="p p-m">مقيس</span>',
            "U": '<span class="p p-u">غير مقيس</span>',
            "O": '<span class="p p-o">من المالك</span>'}[kind]


def n(value, kind="M") -> str:
    if value in (UNMEASURED, ABSENT, None):
        return f'<span class="num v-idle">—</span> {chip("U")}'
    return f'<span class="num">{E(str(value))}</span> {chip(kind)}'


def sec(title, gloss_title, gloss_body, body) -> str:
    return (f'<section class="sec"><div class="body"><h2>{title}</h2>{body}</div>'
            f'<aside class="gloss"><b>{gloss_title}</b>{gloss_body}</aside></section>')


def _ledger_table(ledger: list[dict]) -> str:
    """يطبع الدفتر مغلقًا: دخل = حُمل + مسمًّى + بلا اسم."""
    rows = []
    for e in ledger:
        named = (" · ".join(f'{k} {v:,}' for k, v in
                            sorted(e["named"].items(), key=lambda kv: -kv[1]))
                 or "—")
        closes = (e["into"] != UNMEASURED
                  and e["into"] == e["carried"] + sum(e["named"].values())
                  + e["unnamed"])
        rows.append(
            f'<tr><td class="code">{E(e["edge"])}</td>'
            f'<td class="n">{n(e["into"])}</td>'
            f'<td class="n">{n(e["carried"])}</td>'
            f'<td class="code">{E(named)}</td>'
            f'<td class="n">{n(e["unnamed"])}</td>'
            f'<td class="v {"v-accept" if closes else "v-block"}">'
            f'{"يُغلق" if closes else "لا يُغلق"}</td></tr>')
    return ('<table><thead><tr><th>الحافّة</th><th class="n">دخل</th>'
            '<th class="n">حُمل</th><th>أسبابُ عدم الحمل</th>'
            '<th class="n">بلا اسم</th><th>الدفتر</th></tr></thead>'
            f'<tbody>{"".join(rows)}</tbody></table>')


def render(c: dict) -> str:
    P: list[str] = []
    P.append("""<header><h1>تقريرُ الفحص الدستوريّ</h1>
<p class="lede">ثلاثةُ مثبَّتاتٍ مرَّت على محاور أسلوط الخمسة، مقروءةً بأحكام
تعقُّل. وكلُّ رقمٍ هنا يحمل سندَه — <span class="p p-m">مقيس</span> أو
<span class="p p-u">غير مقيس</span> — ولا رقمَ بلا سند.</p>
<div class="switch" role="group" aria-label="اختيار العرض">
<button type="button" data-v="owner" aria-pressed="true">عرضُ المالك</button>
<button type="button" data-v="eng" aria-pressed="false">عرضُ المهندس</button>
</div></header>""")
    v = c["verdict"]
    P.append(f"""<div class="seal"><div class="verdict">الحكم: {E(v['label'])}</div>
<dl><dt>السبب</dt><dd>{E(v['sabab'])}</dd><dt>الشرط</dt><dd>{E(v['shart'])}</dd>
<dt>المانع</dt><dd>{E(v['mani'])}</dd></dl></div>
<p class="meta">{E(c['stamp'])}</p>""")

    kv = "\n".join(f"{k:<26}= {vv}" for k, vv in c["run_stamp"].items())
    P.append(sec("بصمةُ التشغيل", "إعادةُ الإنتاج",
                 "دليلٌ لا يُعاد بناؤه على جهازٍ آخر ليس دليلًا.<br>docs/123 · docs/128",
                 f'<p class="own note">من أعاد التشغيل بهذه الأرقام نفسِها وجب أن '
                 f'يخرج بالنتائج نفسِها؛ فإن اختلفت فأحدُ الطرفين يقيس غيرَ ما يظنّ.'
                 f'</p><div class="kv">{E(kv)}</div>'))

    mo = c["mark_order"]
    P.append(sec("بوّابةُ ما قبل التشغيل — ترتيبُ العلامات", "قاعدةُ المالك",
                 "كلُّ سطحٍ مشكولٍ مكتوبٍ في ملفّ كودٍ أو اختبارٍ غيرُ موثوقٍ بطبعه، "
                 "وما لم يُنقَل من مصدره فهو دعوى.",
                 f'<p class="own note">النصُّ يكتب الشدّةَ قبل الحركة، واليدُ تعكسهما. '
                 f'فقبل أن يُقاس شيء، تُقابَل نصوصُ الاختبار بترتيب العلامات المعتمَد.</p>'
                 f'<div class="{"ok-box" if mo["verified"] else "warn"}">'
                 f'<b>MARK_ORDER_VERIFIED = {"YES" if mo["verified"] else "NO"}</b>'
                 f'&nbsp;— {E(mo["reason"])} · سطوحٌ مفحوصة: {n(mo["scanned"])}'
                 f' · مخالفات: {n(mo["deviations"])}</div>'))

    rows = "".join(f'<tr><td class="code">{E(k)}</td><td class="code">{E(val)}</td>'
                   f'<td>{E(ar)}</td></tr>' for k, val, ar in ENTRY_BOUNDARY)
    P.append(sec("حدُّ الدخول المُعلَن", "docs/15 §5",
                 "المدخلُ تمثيلٌ لا أصل، ولا صوت، ولا معنًى — ولا يُنتج إلا مرشَّحَ أثرٍ نصّيّ.",
                 f'<p class="own note">قبل أيّ حكم، يُعلن النظامُ ما هو مدخلُه وما ليس هو. '
                 f'كلُّ ما يخرج بعد ذلك محدودٌ بهذا الإقرار.</p>'
                 f'<table><thead><tr><th>الحقل</th><th>القيمة</th><th>بالعربيّة</th>'
                 f'</tr></thead><tbody>{rows}</tbody></table>'))

    fx = "".join(f'<tr><td class="code">{E(f["id"])}</td><td>{E(f["name"])}'
                 f'<div class="meta">{E(f["kind"])}</div></td>'
                 f'<td class="n">{n(f["stats"].get("tokens"))}</td>'
                 f'<td class="n">{n(f["stats"].get("unique"))}</td>'
                 f'<td class="code">{E(str(f["stats"].get("sha256", ABSENT))[:16])}</td>'
                 f'<td>{E(f["asks"])}</td></tr>' for f in c["fixtures"])
    P.append(sec("المثبَّتاتُ الثلاثة", "أصلُ الشاهد",
                 "الشاهدُ من النصّ لا من لوحة المفاتيح. وبصمةُ كلِّ مثبَّتٍ تُثبت أنه هو هو.",
                 f'<p class="own note">ثلاثةُ نصوصٍ اختُبر عليها النظام: أطولُ آيةٍ في '
                 f'المصحف، وجدولُ العوامل الذي كتبتَه أنت، وقصّةٌ نثريّةٌ حديثةٌ من خارج '
                 f'النصّ القرآنيّ — ليُعرف ما يصنع النظامُ حين يخرج عمّا دُرِّب عليه.</p>'
                 f'<table><thead><tr><th>#</th><th>المثبَّت</th><th class="n">توكنات</th>'
                 f'<th class="n">فريدة</th><th>البصمة</th><th>ما يسأل عنه</th></tr></thead>'
                 f'<tbody>{fx}</tbody></table>'))

    for f in c["fixtures"]:
        run = f["run"]
        def _verdicts(a: dict) -> str:
            if a["verdicts"] == UNMEASURED:
                return "—"
            return json.dumps(a["verdicts"], ensure_ascii=False)

        rws = "".join(f'<tr><td class="n">{i}</td><td>{E(a["label"])}</td>'
                      f'<td class="code">{E(a["file"])}</td>'
                      f'<td class="n">{n(a["rows"])}</td>'
                      f'<td class="n">{n(a["trace_anchors"])}</td>'
                      f'<td class="n">{n(a["reconstructed"])}</td>'
                      f'<td class="code">{E(_verdicts(a))}</td>'
                      f'</tr>' for i, a in run["axes"].items())
        ch = "".join(f'<tr><td class="code">{E(x["name"])}</td>'
                     f'<td class="n">{n(x["got"])}</td>'
                     f'<td class="n">{E(str(x["want"]))}</td>'
                     f'<td class="v {"v-accept" if x["ok"] else "v-block"}">'
                     f'{"مُثبَت" if x["ok"] else "غيرُ مُثبَت"}</td>'
                     f'<td class="meta">{E(x["why"])}</td></tr>' for x in f["checks"])
        P.append(sec(f'{E(f["id"])} — المحاورُ الخمسة', "الإثباتُ الموجَب",
                     "كلُّ تحقّقٍ يُثبت عددًا موجَبًا قبل أن ينفيَ الإخفاق. "
                     "صفرُ إخفاقاتٍ في مخرجٍ فارغٍ ليس سلامة.",
                     f'<p class="own note">لكلِّ نصٍّ خمسُ مراحل. والجدولُ يبيّن كم صفًّا '
                     f'دخل كلَّ مرحلة، وكم منها يحمل مرساةَ أثر، وكم مرساةٍ أُعيد بناؤها '
                     f'من موضعها فطابقت.</p>'
                     f'<table><thead><tr><th class="n">المحور</th><th>الاسم</th>'
                     f'<th>الملفّ</th><th class="n">صفوف</th><th class="n">بمرساة</th>'
                     f'<th class="n">أُعيد بناؤها</th><th>توزيعُ الأحكام</th></tr></thead>'
                     f'<tbody>{rws}</tbody></table>'
                     f'<h3>قبل أن يُقرأ أيُّ صفر</h3>'
                     f'<table><thead><tr><th>الشرط</th><th class="n">الواقع</th>'
                     f'<th class="n">المتوقَّع</th><th>الحال</th><th>لِمَ يلزم</th>'
                     f'</tr></thead><tbody>{ch}</tbody></table>'
                     f'<h3>دفترُ الحمل — لا تخطٍّ صامت</h3>'
                     f'{_ledger_table(f["ledger"])}'))

    op, cov = c["operators"], c["coverage"]
    _COV = {
        "PROVEN_IN_ITS_OWN_WITNESS": "ثبت في شاهده هو",
        "PRESENT_BUT_NOT_PROVEN": "ظهر توكنًا ولم يثبت",
        "NOT_A_STANDALONE_TOKEN": "ليس توكنًا قائمًا — حرفٌ متّصلٌ أو مركَّب",
        "NOT_NORMALIZABLE": "تعذّر تطبيعُه",
        "WITNESS_NOT_LOCATED": "لم يُعثر على سطر شاهده في المدخل",
    }
    cov_html = ('<table><tbody>' + "".join(
        f'<tr><th>{E(ar)}</th><td class="code">{E(k)}</td>'
        f'<td class="n">{n(cov["buckets"].get(k, 0))}</td></tr>'
        for k, ar in _COV.items()) + '</tbody></table>'
        if cov.get("status") == "MEASURED" else
        f'<p class="meta">{UNMEASURED}</p>')
    P.append(sec("F2 — جدولُ العوامل وتغطيتُه", "التصريح",
                 "قراءةُ الجدول ليست تصديقًا له. LICENSE_GRANTED = NO قائمٌ حتى يعتمده المالك.",
                 f'<p class="own note">هل يمسك المحورُ الثاني كلَّ عاملٍ من عواملك؟ '
                 f'الجوابُ عددٌ لا انطباع. وقراءةُ الجدول لا ترفع الترخيص: يبقى '
                 f'<span class="code">LICENSE_GRANTED = NO</span> حتى تعتمده أنت.</p>'
                 f'<table><tbody>'
                 f'<tr><th>الحال</th><td class="code">{E(op["status"])}</td></tr>'
                 f'<tr><th>المسار</th><td class="code">{E(op["path"])}</td></tr>'
                 f'<tr><th>صفوف</th><td class="n">{n(op["count"], "O")}</td></tr>'
                 f'<tr><th>عوامل فريدة</th>'
                 f'<td class="n">{n(op.get("unique_operators"), "O")}</td></tr>'
                 f'<tr><th>ذواتُ شاهدٍ مشكول</th>'
                 f'<td class="n">{n(op["with_example"], "O")}</td></tr>'
                 f'<tr><th>البصمة</th><td class="code">{E(str(op["sha256"])[:32])}</td></tr>'
                 f'<tr><th>الترخيص</th><td class="code">LICENSE_GRANTED = NO</td></tr>'
                 f'</tbody></table><h3>التغطية</h3>{cov_html}'))

    rws = "".join(f'<tr><td><span class="dot d-{cls}"></span>'
                  f'<span class="code">{E(code)}</span></td><td>{E(ar)}</td>'
                  + "".join(f'<td class="n">{n(UNMEASURED)}</td>' for _ in c["fixtures"])
                  + "</tr>" for code, ar, cls in CLOSURE_STATES)
    P.append(sec("أحكامُ الغلق الستّة", "Γ · docs/03",
                 "الترتيبُ حاملٌ للحكم: الرفضُ عند الخطوة k يقطع ما بعدها. ستّةُ أحكامٍ لا اثنان.",
                 '<p class="own note">النظامُ لا يقول «نعم» و«لا» فقط، بل ستّةَ أشياء. '
                 'و<b>Γ لم يُشغَّل بعد على الصفوف</b> — وهو T-5 الموقوفُ على حكمك، '
                 'فتُطبع الستّةُ أصفارًا صريحةً لا صمتًا.</p>'
                 '<table><thead><tr><th>الحكم</th><th>معناه</th>'
                 + "".join(f'<th class="n">{E(f["id"])}</th>' for f in c["fixtures"])
                 + f'</tr></thead><tbody>{rws}</tbody></table>'))

    fi = c["failure_inventory"]
    if fi.get("status") == "MEASURED":
        rws = "".join(
            f'<tr><td class="code">{E(k)}</td><td class="n">{n(v)}</td>'
            f'<td class="v v-accept">WITNESSED</td></tr>'
            for k, v in sorted(fi["witnessed"].items(), key=lambda kv: -kv[1]))
        rws += "".join(
            f'<tr><td class="code">{E(k)}</td><td class="n">{n(0)}</td>'
            f'<td class="v v-idle">UNWITNESSED</td></tr>' for k in fi["unwitnessed"])
        rws += "".join(
            f'<tr><td class="code">{E(k)}</td><td class="n">{n(v)}</td>'
            f'<td class="v v-block">UNDECLARED</td></tr>'
            for k, v in sorted(fi["undeclared"].items(), key=lambda kv: -kv[1]))
        undeclared = (f'<div class="warn"><b>UNDECLARED = '
                      f'{len(fi["undeclared"])}</b> — قيمةُ حكمٍ ظهرت في مخرجٍ '
                      f'ولم تُعلَن في <span class="code">ASLOT_REFUSALS</span>. '
                      f'تُطبع باسمها ولا تُبتلع.</div>'
                      if fi["undeclared"] else
                      '<div class="ok-box"><b>UNDECLARED = 0</b> — لا قيمةَ حكمٍ '
                      'خارج التاكسونومية المُعلَنة.</div>')
        summary = (f'<p class="meta">مُعلَنٌ {fi["declared"]} · بشاهدٍ هنا '
                   f'{len(fi["witnessed"])} · بلا شاهدٍ هنا '
                   f'{len(fi["unwitnessed"])} · غيرُ مُعلَن '
                   f'{len(fi["undeclared"])}</p>')
    else:
        rws, undeclared, summary = (
            f'<tr><td colspan="3" class="meta">{UNMEASURED}</td></tr>', "", "")
    P.append(sec("جردُ الرفض المسمّى", "docs/04 · التاكسونومية",
                 "لا رفضَ بلا اسم، ولا اسمَ بلا شاهد. "
                 "والمُعلَنُ بلا شاهدٍ إعلانٌ، والمشهودُ بلا إعلانٍ خرق — ولا يُخلطان.",
                 '<p class="own note">حين يمتنع النظام، يقول لماذا باسمٍ من قائمةٍ '
                 'مغلقة — لا برسالةٍ حرّة. والجردُ <b>مستخرَجٌ من هذه الجولة نفسِها</b> '
                 'ومقسومٌ ثلاثًا، فلا يُجمع المُعلَنُ وغيرُ المُعلَن في عمودٍ واحد.</p>'
                 + summary + undeclared +
                 '<table><thead><tr><th>الرمز</th><th class="n">شواهد</th>'
                 f'<th>الحال</th></tr></thead><tbody>{rws}</tbody></table>'))

    rws = "".join(f'<tr><td class="code">{E(k)}</td><td>{E(ar)}</td>'
                  f'<td class="code">{E(cap)}</td><td class="n">{n(UNMEASURED)}</td></tr>'
                  for k, ar, cap in RESIDUAL_KINDS)
    owner = "".join(f'<tr><td class="code">{E(k)}</td><td class="n">{n(v, "O")}</td>'
                    f'<td class="v v-defer">بانتظار حكمك</td></tr>'
                    for k, v in c["owner_classes"].items())
    P.append(sec("البقايا وسقوفُ الرتب", "docs/06 · Γ خطوة ٦–٧",
                 "البقيّةُ المخفيّة خرقٌ قاتلٌ يُفحص قبل الحاجبة. والسقفُ يُنزل ولا يرفع.",
                 f'<p class="own note">أخطرُ البقايا المخفيّة: خللٌ لا يشكو منه المحورُ '
                 f'التالي فيمرّ صامتًا. ولذلك يُفحص قبل ما يحجب صراحةً.</p>'
                 f'<table><thead><tr><th>الصنف</th><th>معناه</th><th>سقفُ الرتبة</th>'
                 f'<th class="n">العدد</th></tr></thead><tbody>{rws}</tbody></table>'
                 f'<h3>أصنافُ قرار المالك — بلا صنفِ بقيّةٍ بعد</h3>'
                 f'<table><thead><tr><th>الصنف</th><th class="n">كلمات</th>'
                 f'<th>الحال</th></tr></thead><tbody>{owner}</tbody></table>'
                 f'<div class="warn"><b>P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED</b> — '
                 f'لا يُسنِد المولِّدُ صنفَ بقيّةٍ واحدًا من عنده. الخانةُ تبقى فارغةً '
                 f'حتى تملأها أنت.</div>'))

    rws = "".join(f'<tr><td class="code">{E(r)}</td><td class="n">{n(UNMEASURED)}</td></tr>'
                  for r in RANKS)
    P.append(sec("الرتبةُ وعدمُ الترقية", "docs/05 · docs/11 §8",
                 "OutputRank ≤ meet(Evidence, Identity, Gate, ResidualCeiling). "
                 "لا ترقيةَ خارج بوّابة.",
                 f'<p class="own note">لكلّ نتيجةٍ رتبةٌ تقول كم تستحقّ أن يُعتمد عليها. '
                 f'و<b>لا رتبةَ محمولةٌ في مخرجات المحاور بعد</b> — وهو T-7.</p>'
                 f'<table><thead><tr><th>الرتبة</th><th class="n">صفوف</th></tr></thead>'
                 f'<tbody>{rws}</tbody></table>'
                 f'<div class="ok-box"><b>NO_PROMOTION = YES</b> — مقيسٌ خارج هذا '
                 f'التقرير بـ<span class="code">scripts/transition_matrix.py</span> '
                 f'على كامل النصّ: لا صفَّ صعد من تأجيلٍ أو حجبٍ إلى قبول.</div>'))

    tr = c["trace"]
    P.append(sec("الأثر", "Γ خطوة ٢ · docs/07",
                 "لا مخرجَ بلا أثر. والمرساةُ حتميّةٌ تُشتقّ من موضعها، فتُعاد وتُقابَل.",
                 f'<p class="own note">كلُّ صفٍّ يحمل مرساةً تدلّ على موضعه، وسلسلةً تصله '
                 f'بالمحور السابق. والمرساةُ محسوبةٌ من الموضع لا مولَّدةٌ عشوائيًّا — '
                 f'ولذلك <b>أُعيد بناؤها هنا وقُوبلت</b>، ولم يُكتفَ بعدّها.</p>'
                 f'<div class="tiles">'
                 f'<div class="tile"><span class="big">{n(tr["rows"])}</span>'
                 f'<span class="lbl">صفوفٌ كلّيّة</span></div>'
                 f'<div class="tile"><span class="big">{n(tr["anchored"])}</span>'
                 f'<span class="lbl">بمرساة</span></div>'
                 f'<div class="tile"><span class="big">{n(tr["without"])}</span>'
                 f'<span class="lbl">بلا مرساة</span></div>'
                 f'<div class="tile"><span class="big">{n(tr["reconstructed"])}</span>'
                 f'<span class="lbl">أُعيد بناؤها وطوبقت</span></div></div>'))

    rws = "".join(f'<tr><td class="code">{E(s)} → {E(t)}</td>'
                  f'<td class="code">{E(g)}</td><td>{E(w)}</td>'
                  f'<td class="n">{n(UNMEASURED)}</td></tr>'
                  for s, t, g, w in FORBIDDEN_LINES)
    P.append(sec("الخطوطُ المستقيمةُ الممنوعة", "docs/04 · docs/10",
                 "الخطُّ يبقى ممنوعًا حتى تُفتح بوّابتُه المسمّاة. "
                 "والتسجيلُ يمنع الادّعاء ولا يرفع المنع.",
                 f'<p class="own note">قفزاتٌ يقع فيها كلُّ نظامٍ لغويٍّ إن تُرك. '
                 f'والنظامُ يعرفها بأسمائها؛ و<b>السجلُّ لم يُستشَر في زمن التشغيل</b> — '
                 f'وهو T-6.</p>'
                 f'<table><thead><tr><th>الخطّ</th><th>البوّابةُ اللازمة</th>'
                 f'<th>موضعُه</th><th class="n">اشتعل</th></tr></thead>'
                 f'<tbody>{rws}</tbody></table>'))

    rws = "".join(f'<tr><td class="code">{E(k)}</td><td>{E(ar)}</td>'
                  f'<td class="n">{n(0)}</td></tr>' for k, ar in TRANSITION_STATES)
    P.append(sec("بوّاباتُ الانتقال", "docs/08",
                 "حكمُ البوّابة عن الحركة، وحكمُ الغلق عن الرسم. لا يُدمجان.",
                 f'<p class="own note">الانتقالُ بين المحاور ليس استدعاءً بل بوّابة. '
                 f'وحتى اليوم <b>لم تُركَّب</b>، والانتقالُ استدعاءٌ مباشر — والصفرُ هنا '
                 f'<b>مقيسٌ لا مجهول</b>: عُدَّت البوّابات فكانت صفرًا.</p>'
                 f'<table><thead><tr><th>الحكم</th><th>معناه</th>'
                 f'<th class="n">العدد</th></tr></thead><tbody>{rws}</tbody></table>'))

    rws = "".join(f'<tr><td class="code">{E(k)}</td><td>{E(ar)}</td>'
                  f'<td class="v v-idle"><span class="dot d-idle"></span>NOT_OPENED</td>'
                  f'</tr>' for k, ar in VERTICAL_NOT_OPENED)
    P.append(sec("ما لم يُفتح — بالتصريح لا بالعجز", "docs/46",
                 "تعقُّل نفسُه لا يشغّل هذه الطبقات على نصّ. "
                 "أعمقُ ما نُفِّذ عنده: PATH_CLASSIFICATION.",
                 f'<p class="own note">هذا التقريرُ لا يقول ما تعنيه الجملة، ولا يحكم '
                 f'عليها، ولا ينزّل حكمًا على واقعة. والنظامُ الذي يسكت عمّا لم يفعله '
                 f'يُوهم أنه فعله.</p>'
                 f'<table><thead><tr><th>الطبقة</th><th>بالعربيّة</th><th>الحال</th>'
                 f'</tr></thead><tbody>{rws}</tbody></table>'
                 f'<div class="kv">ROOT_PROVEN = NO   ·   STEM_PROOF = NOT_CLAIMED   ·   '
                 f'WEIGH_CALLED = NO\nIFADAH = NOT_OPENED   ·   HUKM = NOT_OPENED   ·   '
                 f'TANZIL = NOT_OPENED</div>'))

    rws = "".join(f'<tr><td class="n">{i}</td><td>{E(t)}</td><td>{E(w)}</td></tr>'
                  for i, (t, w) in enumerate(c["owner_pending"], 1))
    P.append(sec("الموقوفُ على حكمك", "STOP · OWNER_ALERT · NO_INFERENCE",
                 "عند الفجوة الدستوريّة: لا تُصنع قاعدة، ولا يُضاف استثناء، "
                 "ولا يُختار بين البدائل نيابةً عن المالك.",
                 f'<p class="own note">مواضعُ توقّف فيها النظامُ عمدًا لأن الحكمَ فيها '
                 f'لك لا له.</p><table><thead><tr><th class="n">#</th><th>القرار</th>'
                 f'<th>ما يفتحه</th></tr></thead><tbody>{rws}</tbody></table>'))

    P.append(sec("ما لم يُقس في هذا التقرير", "MEASURED_NOT_PRESET",
                 "الاعترافُ ليس دعوى. والصفرُ في موضع المجهول دعوى — "
                 "والمجهولُ في موضع المقيس تهوينٌ من الحجّة.",
                 f'<p class="own note">كلُّ ما يلي غيرُ مقيسٍ في هذه النسخة، ويُطبع '
                 f'«غير مقيس» لا صفرًا.</p>'
                 f'<div class="kv">{E(chr(10).join(c["unmeasured"]))}</div>'))

    P.append(f"""<footer><p>وُلِّد بـ <span class="code">scripts/build_taaqol_inspection.py</span>
· RULE_OWNER = DR_HUSSEIN · MEASURED_NOT_PRESET</p>
<p>{E(c['footer_note'])}</p></footer>""")

    return (f'<!doctype html>\n<html lang="ar" dir="rtl"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>تقريرُ الفحص الدستوريّ — أسلوط × تعقُّل</title>'
            f'<style>{CSS}</style></head><body data-view="owner"><div class="page">'
            + "\n".join(P) + """</div><script>
document.querySelectorAll('.switch button').forEach(function(b){
  b.addEventListener('click',function(){
    document.body.dataset.view=b.dataset.v;
    document.querySelectorAll('.switch button').forEach(function(x){
      x.setAttribute('aria-pressed', String(x===b));});
  });
});
</script></body></html>""")


# ── التجميع ──────────────────────────────────────────────────────────────
#: ما هو **حقًّا** غيرُ مقيسٍ في هذه النسخة. ولا يُكتب هنا ما قِيس.
UNMEASURED_NOTES = [
    "أحكامُ الغلق الستّة على الصفوف — Γ لم يُشغَّل (T-5)",
    "أعدادُ الرتب على الصفوف — لا رتبةَ محمولةٌ في المخرجات (T-7)",
    "اشتعالُ الخطوط المستقيمة — السجلُّ لا يُستشار في زمن التشغيل (T-6)",
    "صنفُ البقيّة لكلّ صنفٍ من أصناف المالك السبعة — حكمُك (T-4)",
    "أثرُ Γ في تقشير «كَتَبَ» — الحكمُ لم يتغيّر لأنّ Γ لم يُشغَّل",
]

FIXTURES = [
    ("F1", "أطولُ آيةٍ في المصحف — البقرة ٢٨٢", "نصٌّ قرآنيّ · من MASAQ",
     "هل يمسك النظامُ نصًّا هو مصدرُ قواعده؟"),
    ("F2", "شواهدُ جدول العوامل", "مشتقٌّ من عمود Example_Vocalized",
     "هل يرى المحورُ الثاني كلَّ عاملٍ في شاهده؟"),
    ("F3", "قصّةٌ نثريّةٌ حديثة", "خارجُ النصّ القرآنيّ",
     "ماذا يصنع حين يخرج عمّا بُني عليه؟"),
]


def git_sha(root: Path) -> str:
    try:
        out = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                             capture_output=True, text=True, timeout=30,
                             check=False)
    except Exception:
        return UNMEASURED
    return out.stdout.strip() or UNMEASURED


def build(args: argparse.Namespace) -> dict:
    root = Path(__file__).resolve().parents[1]
    dirs = {"F1": args.f1_dir, "F2": args.f2_dir, "F3": args.f3_dir}
    texts = {"F1": args.f1_text, "F2": args.f2_text, "F3": args.f3_text}

    fixtures = []
    for fid, name, kind, asks in FIXTURES:
        run_dir = Path(dirs[fid]) if dirs[fid] else None
        run = load_run(run_dir)
        src = Path(texts[fid]) if texts[fid] else None
        stats = (text_stats(src.read_text(encoding="utf-8"))
                 if src and src.is_file() else {})
        fixtures.append({
            "id": fid, "name": name, "kind": kind, "asks": asks,
            "run": run, "stats": stats, "source": str(src) if src else ABSENT,
            "checks": positive_assertions(run, stats.get("tokens", UNMEASURED)),
            "ledger": carry_ledger(run),
            "owner_classes": owner_classes_of(run_dir),
        })

    runs = [f["run"] for f in fixtures]
    operators = load_operators(Path(args.operators_csv)
                               if args.operators_csv else None)
    f2 = next(f for f in fixtures if f["id"] == "F2")
    coverage = operator_coverage(
        operators, f2["run"],
        Path(args.f2_text) if args.f2_text else None)

    gate_files = [Path(p) for p in (args.f1_text, args.f2_text, args.f3_text)
                  if p]
    mark_order = mark_order_gate(args.mark_order_cmd, gate_files)

    merged: Counter = Counter()
    for f in fixtures:
        merged.update(f["owner_classes"])

    # الحكم: القبولُ دعوى كالحجب. فلا يُختم بقبولٍ ما لم يمرّ كلُّ موجَبٍ
    # وتُغلق دفاترُ الحمل الاثنا عشر وتُقفل بوّابةُ ترتيب العلامات.
    all_positive = all(x["ok"] for f in fixtures for x in f["checks"])
    ledgers_close = all(
        e["into"] != UNMEASURED
        and e["into"] == e["carried"] + sum(e["named"].values()) + e["unnamed"]
        for f in fixtures for e in f["ledger"])
    ok = all_positive and ledgers_close and mark_order["verified"]

    verdict = {
        "label": "ACCEPT_WITH_DECLARED_GAPS" if ok else "BLOCK",
        "sabab": ("خمسةُ محاورَ جرت على ثلاثة مثبَّتات، وكلُّ صفٍّ يحمل مرساةً "
                  "أُعيد بناؤها من موضعها فطابقت"),
        "shart": ("كلُّ موجَبٍ مرّ قبل أن يُقرأ نفي، ودفاترُ الحمل مغلقة، "
                  "وبوّابةُ ترتيب العلامات مقفلة"),
        "mani": ("لا مانعَ في المقيس. والفجوةُ فوق T-3 مُعلَنةٌ لا مستورة: "
                 "Γ والرتبةُ والخطوطُ والبوّاباتُ موقوفةٌ على حكمك"),
    } if ok else {
        "label": "BLOCK",
        "sabab": "جرت الجولةُ وأخرجت صفوفًا",
        "shart": "غيرُ محقَّق — انظر ما لم يمرّ أدناه",
        "mani": ("إثباتٌ موجَبٌ سقط، أو دفترُ حملٍ لم يُغلق، أو بوّابةُ ترتيب "
                 "العلامات لم تُقفل. ولا يُختم بقبولٍ فوق ذلك"),
    }

    engine = args.engine_commit or git_sha(root)
    return {
        "verdict": verdict,
        "stamp": (f"وُلِّد من جولةٍ فعليّة · محرّك {engine[:12]} · "
                  f"تعقُّل {(args.taaqol_commit or UNMEASURED)[:12]}"),
        "run_stamp": {
            "ENGINE_COMMIT": engine,
            "TAAQOL_COMMIT": args.taaqol_commit or UNMEASURED,
            "PYTHON": ".".join(map(str, sys.version_info[:3])),
            "MARK_ORDER_VERIFIED": "YES" if mark_order["verified"] else "NO",
            "OPERATORS_SHA256": str(operators["sha256"])[:32],
            "LICENSE_GRANTED": "NO",
            "RULE_OWNER": "DR_HUSSEIN",
        },
        "mark_order": mark_order,
        "fixtures": fixtures,
        "operators": operators,
        "coverage": coverage,
        "failure_inventory": failure_inventory(runs),
        "trace": trace_totals(runs),
        "owner_classes": dict(sorted(merged.items(), key=lambda kv: -kv[1])),
        "owner_pending": [
            ("T-4 · صنفُ البقيّة للأصناف السبعة", "سقوفَ الرتب كلَّها"),
            ("T-4 · عيبُ التنوين: حاجبٌ أم مؤجَّلٌ ظاهر", "فحصَ البقيّة المخفيّة"),
            ("T-5 · Γ يغيّر الأحكام", "أحكامَ الغلق الستّة"),
            ("T-6 · الخطوطُ تُنزل تقشيرَ «كَتَبَ»", "المنعَ في زمن التشغيل"),
            ("T-7 · بوّاباتُ الانتقال بين المحاور", "حكمَ الحركة"),
            ("اعتمادُ السجلّين", "رفعَ LICENSE_GRANTED"),
            ("آ خارجَ «أل»", "توسيعَ N10.2 أو حصرَها"),
        ],
        "unmeasured": UNMEASURED_NOTES,
        "footer_note": ("قراءةُ جدولٍ ليست اعتمادًا له، وتشغيلُ محورٍ ليس "
                        "إثباتَ جذر. وما فوق T-3 موقوفٌ على حكم المالك."),
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", default="taaqol_inspection.html")
    for fixture in ("f1", "f2", "f3"):
        p.add_argument(f"--{fixture}-dir")
    p.add_argument("--f1-text", default="inspection/ayat.txt")
    p.add_argument("--f2-text", default="inspection/runs/f2/input.txt")
    p.add_argument("--f3-text", default="inspection/story.txt")
    p.add_argument("--operators-csv")
    p.add_argument("--engine-commit")
    p.add_argument("--taaqol-commit")
    p.add_argument("--mark-order-cmd")
    args = p.parse_args(argv)

    context = build(args)
    out = Path(args.out)
    out.write_text(render(context), encoding="utf-8")

    v = context["verdict"]
    print(f"VERDICT = {v['label']}")
    print(f"MARK_ORDER_VERIFIED = "
          f"{'YES' if context['mark_order']['verified'] else 'NO'}"
          f"   ({context['mark_order']['scanned']} سطحًا · "
          f"{context['mark_order']['deviations']} مخالفة)")
    for f in context["fixtures"]:
        rows = {i: a["rows"] for i, a in f["run"]["axes"].items()}
        bad = [x["name"] for x in f["checks"] if not x["ok"]]
        print(f"{f['id']}  محاور {rows}   موجَبٌ ساقط: {bad or '—'}")
    tr = context["trace"]
    print(f"TRACE  صفوف {tr['rows']} · بمرساة {tr['anchored']} · "
          f"بلا مرساة {tr['without']} · أُعيد بناؤها {tr['reconstructed']}")
    fi = context["failure_inventory"]
    if fi.get("status") == "MEASURED":
        print(f"REFUSALS  مُعلَن {fi['declared']} · بشاهد {len(fi['witnessed'])}"
              f" · بلا شاهد {len(fi['unwitnessed'])}"
              f" · غيرُ مُعلَن {len(fi['undeclared'])}"
              + (f"  ⚠ {sorted(fi['undeclared'])}" if fi["undeclared"] else ""))
    print(f"→ {out}")
    return 0 if v["label"] != "BLOCK" else 1


if __name__ == "__main__":
    raise SystemExit(main())
