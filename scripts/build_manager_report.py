#!/usr/bin/env python3
"""تقريرُ المدير — كلمةً كلمة، بأسلوب تقرير `HOKOM` الذي أرسلتَه.

    python3 scripts/build_manager_report.py \\
        --out inspection/manager_report.html \\
        --f1-dir inspection/runs/f1 --f2-dir inspection/runs/f2 \\
        --f3-dir inspection/runs/f3 \\
        --operators-csv <ملف> --git-facts inspection/GIT_FACTS.json \\
        --mark-order-cmd 'python3 -m aslot.tools.mark_order --check'

**الفرقُ عن تقرير الفحص الدستوريّ.** ذاك يعرض البنية: أيُّ حاملٍ نُفّذ وأيُّه
موقوف. وهذا يعرض **الشغل**: الكلمةَ الواحدة، ماذا صار لها في كلّ محور، ولمَ
تأجّلت إن تأجّلت. والمديرُ لا يُقنعه هيكلٌ بلا صفوف.

وطبقةُ القياس **ليست مكرَّرةً هنا**: تُستورد من
``scripts/build_taaqol_inspection.py``. وتكرارُ القياس في مولّدين يفتح بابَ
اختلاف رقمين لنفس الشيء — وهو الصنفُ نفسُه الذي أفسد دعوى السجلّين.

**ثلاثُ خصالٍ نُقلت من تقريرك، لأنّها الأهمّ فيه:**

1. الهويّةُ **تُقرأ** من `git` ولا تُكتب. وهذه الحاويةُ ليست مستودعًا، فتُقرأ
   من ملفٍّ ولّده `git` على جهازك، وتُطبع بصمتُه — فمن أعاد التوليد قابَل.
2. عدّاداتُ النزاهةِ والعوائدُ **تُكتشف من بيانات التشغيل** لا من قائمةٍ
   ثابتة، ويُفصَّل ثلاثةً: مشهودٌ هنا · مُعلَنٌ بلا شاهدٍ هنا · **ظهر ولم
   يُعلَن**. والثالثُ خرقٌ يُسمّى.
3. **أعمدةٌ تنتجها المصدِّرات ولا يعرضها التقرير** تُجرد صراحةً. وهذا ما
   يجعل التقريرَ يتبع الشيفرة: عمودٌ يُضاف اليومَ يظهر هنا غدًا ولا يسقط
   في صمت.

وما لا يُدَّعى يُطبع كما هو: لا إفادةَ ولا حكمَ ولا تنزيل، ولا جذرَ مثبَتًا،
ولا Γ مشغَّلًا. `LICENSE_GRANTED = NO`.
"""
from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from build_taaqol_inspection import (
    ABSENT,
    AXIS_FILES,
    UNMEASURED,
    carry_ledger,
    failure_inventory,
    load_operators,
    load_run,
    mark_order_gate,
    operator_coverage,
    owner_classes_of,
    positive_assertions,
    sha256_of,
    text_stats,
    trace_totals,
)

E = html.escape

#: الأعمدةُ التي **يعرضها** هذا التقرير. وما عداها يُجرد في قسم الأعمدة
#: غير المعروضة — فالسكوتُ عن عمودٍ أخطرُ من عرضه.
SHOWN_COLUMNS = {
    0: {"Sura_No", "Verse_No", "Word_No", "Word", "Segment_Count"},
    1: {"Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
        "Normalization_Status", "Owner_Decision_Classes", "Rules_Applied",
        "Stop_Reason", "Elision_Points"},
    2: {"Sura_No", "Verse_No", "Word_No", "Closed_Form_Proof", "Eligibility",
        "Next_Route", "Word_Class"},
    3: {"Sura_No", "Verse_No", "Word_No", "Verdict", "Syllable_Pattern",
        "Block_Reason", "Reconstruction_Verified"},
    4: {"Sura_No", "Verse_No", "Word_No", "Verdict", "Termination",
        "Peel_Count", "Peeled_Prefixes", "Stem_Surface", "Root_Proven"},
}

#: مصطلحاتٌ تُترجم للعرض. وما لا ترجمةَ له يُعرض **باسمه الإنجليزيّ لا
#: مطويًّا** — كما فعل تقريرُك حين عرض `kana_khabar` باسمه.
GLOSS = {
    "STEM_NOT_FURTHER_PEELABLE": "جذعٌ لا يُقشَّر أكثر",
    "CLOSED_REMAINDER": "بقيّةٌ مغلقة",
    "DEFER_INITIAL_LETTER_MAY_BE_RADICAL": "الحرفُ الأوّل قد يكون أصليًّا",
    "DEFER_UNRESOLVED_CLOSURE": "غلقٌ غيرُ محسوم",
    "DEFER_VERBAL_OPERATOR_REGISTRY_TAG": "وسمُ سجلّ عاملٍ فعليّ",
    "DEFER_ELIDED_LETTER_NOT_RESTORABLE": "حرفٌ محذوفٌ لا يُستردّ",
    "DEFER_REMAINDER_STANDING_UNPROVEN": "قيامُ البقيّة غيرُ مُثبَت",
    "BLOCK_SYLLABLE_BOUNDARY_CROSSED": "قطعٌ يعبر حدَّ مقطع",
    "BLOCK_AXIS_3_REJECTED": "المحورُ الثالث ردّها",
    "BLOCK_EMPTY_REMAINDER": "بقيّةٌ فارغة",
    "EXCLUDED_LAFZ_AL_JALALAH": "لفظُ الجلالة — استثناءٌ بالجرد",
    "EXCLUDED_FAWATIH_AL_SUWAR": "فواتحُ السور",
    "IGNORED_NON_WORD_TOKEN": "ليست كلمة",
    "NORMALIZED": "طُبِّعت",
    "NORMALIZED_OWNER_DECISION_REQUIRED": "طُبِّعت — وفيها صنفُ حكمك",
    "ACCEPT": "قُبِلت", "BLOCK": "حُجبت", "DEFER": "أُجِّلت",
    "PROVEN": "مثبَتة", "NOT_MATCHED": "لم تُطابَق", "UNRESOLVED": "غيرُ محسومة",
    "CONTINUE": "تمضي", "STOP_CLOSED_FORM": "تقف — صورةٌ مغلقة",
    "SYLLABLE_WITHOUT_ONSET": "مقطعٌ بلا مُستهَلّ",
    "U_TANWEEN": "تنوين", "U_ALEF_MADDA": "ألفٌ ممدودة (آ)",
    "U_ALIF_MAQSURA": "ألفٌ مقصورة", "U_ALIF_FARIQA": "ألفٌ فارقة",
    "U_N7_2_INTERNAL_AL": "«أل» داخليّة", "U_UNVOCALIZED_CARRIER": "حاملٌ غيرُ مشكول",
    "U_MULTIWORD_CELL": "خليّةٌ فيها أكثرُ من كلمة",
}

#: ما لا يدّعيه هذا التقرير — يُطبع كاملًا، فالسكوتُ عنه إيهامٌ بفعله.
NOT_CLAIMED = [
    ("الإفادة", "IFADAH", "NOT_OPENED", "لم تُفتح الطبقة"),
    ("الحكم", "HUKM", "NOT_OPENED", "لم تُفتح الطبقة"),
    ("التنزيل", "TANZIL", "NOT_OPENED", "لم تُفتح الطبقة"),
    ("الجذر", "ROOT_PROVEN", "NO", "الجذعُ ليس جذرًا، والهيكلُ ليس دليلًا"),
    ("الوزن", "WEIGH_CALLED", "NO", "لم يُستدعَ"),
    ("غلقُ Γ", "GAMMA_RUN", "NO", "أداةُ حكم — موقوفةٌ (T-5)"),
    ("الرتبة", "RANK_CARRIED", "NO", "لا رتبةَ محمولةٌ في مخرج (T-7)"),
    ("الخطوطُ الممنوعة", "FORBIDDEN_LINES_ENFORCED", "NO",
     "السجلُّ لا يُستشار وقتَ التشغيل (T-6)"),
    ("ترخيصُ السجلّات", "LICENSE_GRANTED", "NO", "حتى تعتمدها أنت"),
]

FIXTURES = [
    ("F1", "أطولُ آيةٍ في المصحف — البقرة ٢٨٢", "نصٌّ قرآنيّ · من MASAQ"),
    ("F2", "شواهدُ جدول العوامل", "مشتقٌّ من عمود Example_Vocalized"),
    ("F3", "قصّةٌ نثريّةٌ حديثة", "خارجُ النصّ القرآنيّ"),
]


# ── قياسٌ إضافيّ: الصفّ الواحد ────────────────────────────────────────────
def word_rows(run: dict) -> list[dict]:
    """يصل المحاور الخمسة بمفتاح الموضع، فيخرج صفٌّ لكلّ كلمة.

    والوصلُ بالمفتاح لا بالترتيب: الترتيبُ ينكسر صامتًا حين يسقط صفّ،
    والمفتاحُ يُظهر السقوطَ عمودًا فارغًا يُسأل عنه.
    """
    by_axis: dict[int, dict[tuple, dict]] = {}
    for idx in AXIS_FILES:
        rows = run["axes"][idx]["_rows"] or []
        by_axis[idx] = {(r.get("Sura_No"), r.get("Verse_No"), r.get("Word_No")): r
                        for r in rows}
    out = []
    for key, a0 in by_axis[0].items():
        a1 = by_axis[1].get(key, {})
        a2 = by_axis[2].get(key, {})
        a3 = by_axis[3].get(key, {})
        a4 = by_axis[4].get(key, {})
        out.append({
            "key": key,
            "no": key[2],
            "word": a0.get("Word", ""),
            "normalized": a1.get("Normalized_Word", ""),
            "status": a1.get("Normalization_Status", ""),
            "rules": a1.get("Rules_Applied", ""),
            "classes": a1.get("Owner_Decision_Classes", ""),
            "stop": a1.get("Stop_Reason", ""),
            "elision": a1.get("Elision_Points", ""),
            "proof": a2.get("Closed_Form_Proof", ""),
            "route": a2.get("Next_Route", ""),
            "pattern": a3.get("Syllable_Pattern", ""),
            "a3_verdict": a3.get("Verdict", ""),
            "reconstructed": a3.get("Reconstruction_Verified", ""),
            "termination": a4.get("Termination", ""),
            "peels": a4.get("Peel_Count", ""),
            "prefixes": a4.get("Peeled_Prefixes", ""),
            "stem": a4.get("Stem_Surface", ""),
            "root_proven": a4.get("Root_Proven", ""),
            "carried": bool(a4),
        })
    return out


def unshown_columns(runs: list[dict]) -> dict:
    """أعمدةٌ خرجت من المصدِّرات ولا يعرضها هذا التقرير — تُجرد ولا تُطوى."""
    out: dict[int, list[str]] = {}
    for idx in AXIS_FILES:
        produced: set[str] = set()
        for run in runs:
            rows = run["axes"][idx]["_rows"]
            if rows:
                produced |= set(rows[0].keys())
        hidden = produced - SHOWN_COLUMNS.get(idx, set())
        # المرساةُ معروضةٌ مجمَّعةً في بطاقة الأثر، فلا تُعدّ مخفيّة.
        hidden -= {"Trace_Anchor", "Parent_Anchor"}
        if hidden:
            out[idx] = sorted(hidden)
    return out


def load_git_facts(path: Path | None) -> dict:
    """الهويّةُ **تُقرأ** — من مستودعٍ إن وُجد، وإلا من ملفٍّ ولّده `git`."""
    if path is None or not path.is_file():
        return {"status": ABSENT,
                "why": "لم يُمرَّر --git-facts، وهذه الحاويةُ ليست مستودعًا"}
    raw = path.read_bytes()
    data = json.loads(raw.decode("utf-8"))
    data["status"] = "READ"
    data["source"] = str(path)
    data["sha256"] = sha256_of(raw)
    return data


def residual_totals(fixtures: list[dict]) -> dict:
    merged: Counter = Counter()
    for f in fixtures:
        merged.update(f["owner_classes"])
    return dict(sorted(merged.items(), key=lambda kv: -kv[1]))


# ── التصيير — أسلوبُ تقرير المالك ────────────────────────────────────────
CSS = """
body{font-family:-apple-system,'Segoe UI','Noto Naskh Arabic',Tahoma;
  background:#f6f8fa;color:#1f2328;margin:0;padding:18px;line-height:1.8}
h1,h2,h3{color:#0b3d2e}
h1{font-size:26px;margin:0 0 6px}
.card{background:#fff;border:1px solid #d0d7de;border-radius:10px;
  padding:14px 16px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border:1px solid #d0d7de;padding:7px 9px;text-align:right;
  vertical-align:top}
th{background:#eaeef2}
tbody tr:nth-child(even){background:#fafbfc}
.banner{background:#0b3d2e;color:#fff;padding:12px 16px;border-radius:8px;
  font-weight:700;text-align:center;margin:10px 0}
.ok{background:#dafbe1;border:1px solid #1a7f37;border-radius:8px;
  padding:10px 14px;color:#0b3d2e}
.warn{background:#fff8c5;border:1px solid #d4a72c;border-radius:8px;
  padding:10px 14px}
.fail{background:#ffebe9;border:1px solid #cf222e;border-radius:8px;
  padding:10px 14px;color:#cf222e;font-weight:700}
.new{background:#ddf4ff;border:1px solid #0969da;border-radius:8px;
  padding:10px 14px;color:#0a3069}
.cert{color:#1a7f37;font-weight:700}
.defer{color:#9a6700;font-weight:700}
.bad{color:#cf222e;font-weight:700}
.k{color:#57606a}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#57606a;
  direction:ltr;unicode-bidi:embed}
.big{font-size:34px;font-weight:800;color:#0b3d2e}
.lbl{color:#57606a;font-size:13px}
.ar{font-size:17px;font-weight:700;color:#0a3069}
.arn{font-size:17px;font-weight:700;color:#1a7f37}
.tiny{font-size:11px}
.scroll{overflow-x:auto}
.kv{background:#f6f8fa;border:1px solid #d0d7de;border-radius:6px;padding:8px 10px}
@media print{body{background:#fff;padding:0}.card{break-inside:avoid}}
"""


def cell(value: str, gloss: bool = False) -> str:
    if not value:
        return '<span class="k">—</span>'
    if gloss and value in GLOSS:
        return (f'{E(GLOSS[value])}<div class="mono tiny">{E(value)}</div>')
    return f'<span class="mono">{E(value)}</span>'


def status_class(row: dict) -> str:
    term = row["termination"]
    if term.startswith("BLOCK"):
        return "bad"
    if term.startswith("DEFER"):
        return "defer"
    if term:
        return "cert"
    return "k"


def render(c: dict) -> str:
    P: list[str] = []
    f1 = c["fixtures"][0]
    tr, mo, git = c["trace"], c["mark_order"], c["git"]

    P.append("<h1>تقريرُ المدير — سلسلةُ أسلوط، كلمةً كلمة</h1>")
    P.append('<div class="banner">تطبيعٌ وحصرٌ وتقطيعٌ وتقشير — '
             'ولا إفادةَ ولا حُكمَ ولا تنزيل، ولا جذرَ مثبَتًا. '
             'الجذعُ ليس جذرًا، والهيكلُ ليس دليلًا.</div>')

    # المقامُ واحدٌ في كلّ اللوحة: **الآيةُ وحدَها**. وخلطُ مقامٍ بمقام —
    # كلماتُ الآية بجانب صفوف المثبَّتات الثلاثة — يجعل اللوحةَ تجمع ما لا
    # يُجمع، وهو الخطأ الذي لا يراه القارئ ويُصدّقه.
    t1 = f1["terms"]
    tiles = [
        (f1["stats"].get("tokens", 0), "كلمةً في الآية", "#0b3d2e"),
        (t1["accept"], "قُشِّرت إلى جذع", "#1a7f37"),
        (t1["defer"], "أُجِّلت بسببٍ مسمًّى", "#9a6700"),
        (t1["block"], "حُجبت بسببٍ مسمًّى", "#cf222e"),
        (t1["not_carried"], "استُثنيت قبل التقشير", "#57606a"),
    ]
    total = sum(v for v, _, _ in tiles[1:])
    P.append('<div class="card"><table><tr>' + "".join(
        f'<td style="text-align:center"><div class="big" style="color:{col}">'
        f'{v:,}</div><div class="lbl">{E(lbl)}</div></td>'
        for v, lbl, col in tiles) + "</tr></table>"
        f'<div class="{"ok" if total == f1["stats"].get("tokens") else "fail"}"'
        f' style="margin-top:8px">اللوحةُ تقفل: '
        f'{t1["accept"]} + {t1["defer"]} + {t1["block"]} + '
        f'{t1["not_carried"]} = <b>{total}</b> = عددُ كلمات الآية. '
        f'فلا كلمةَ خرجت من اللوحة بلا خانة.</div></div>')

    # ── المقامات، مُعلَنةً ───────────────────────────────────────────────
    rows = "".join(
        f'<tr><td class="mono">{E(f["id"])}</td><td>{E(f["name"])}</td>'
        f'<td class="mono">{f["stats"].get("tokens", "—")}</td>'
        f'<td class="mono">{len(f["rows"])}</td>'
        f'<td class="mono cert">{f["terms"]["accept"]}</td>'
        f'<td class="mono defer">{f["terms"]["defer"]}</td>'
        f'<td class="mono bad">{f["terms"]["block"]}</td>'
        f'<td class="mono k">{f["terms"]["not_carried"]}</td></tr>'
        for f in c["fixtures"])
    P.append('<div class="card"><h3>المقامات — مُعلَنةٌ لا مُجمَعة</h3>'
             '<p class="k">كلُّ نسبةٍ في هذا التقرير مقامُها مثبَّتٌ واحد، '
             'ولا يُجمع مقامان. واللوحةُ أعلاه مقامُها <b>F1</b> وحدَه.</p>'
             '<table><thead><tr><th>#</th><th>المثبَّت</th><th>توكنات</th>'
             '<th>صفوف</th><th>قُشِّرت</th><th>أُجِّلت</th><th>حُجبت</th>'
             f'<th>لم تُحمل</th></tr></thead><tbody>{rows}</tbody></table>'
             '</div>')

    # ── الهويّة ──────────────────────────────────────────────────────────
    if git["status"] == "READ":
        dirty = git.get("dirty") or ""
        rows = [
            ("HEAD", git.get("head", "")),
            ("BRANCH", git.get("branch", "")),
            ("TAGS", git.get("tags", "—")),
            ("DESCRIBE", git.get("describe", "")),
            ("COMMITTED_AT", git.get("committed_at", "")),
            ("TRACKED_FILES", str(git.get("tracked_files", ""))),
            ("حالةُ الشجرة",
             dirty.replace("\n", " · ") if dirty else "نظيفةٌ — لا متغيّر"),
            ("مصدرُ هذه الحقائق", f'{git["source"]}  ·  sha256 '
                                  f'{git["sha256"][:16]}…'),
        ]
    else:
        rows = [("الحال", "SOURCE_ABSENT"), ("لماذا", git.get("why", ""))]
    rows += [("TAAQOL_VENDOR_SHA", c["taaqol_commit"]),
             ("PYTHON", c["python"]),
             ("OPERATORS_SHA256", str(c["operators"]["sha256"])[:32] + "…")]
    P.append('<div class="card"><h3>هويّةُ التشغيل — مقروءةٌ من '
             '<span class="mono">git</span> لا مكتوبة</h3>'
             '<p class="k">هذه الحاويةُ التي شغَّلت المحاور ليست مستودعًا، '
             'فالهويّةُ قرأها <span class="mono">git</span> على جهازك وكُتبت '
             'في ملفّ، وبصمتُه أدناه. ومن أعاد التوليد قابَل البصمة.</p>'
             '<table>' + "".join(
                 f'<tr><th style="width:26%">{E(k)}</th>'
                 f'<td class="mono">{E(v)}</td></tr>' for k, v in rows)
             + "</table></div>")

    # ── بوّابةُ ما قبل التشغيل ───────────────────────────────────────────
    box = "ok" if mo["verified"] else "fail"
    P.append(f'<div class="card"><h3>بوّابةُ ما قبل التشغيل — ترتيبُ العلامات'
             f'</h3><p class="k">قاعدتُك: كلُّ سطحٍ مشكولٍ مكتوبٍ بيدٍ دعوى '
             f'حتى يُقابَل بمصدره. والنصُّ يكتب الشدّةَ قبل الحركة، واليدُ '
             f'تعكسهما — فتُقابَل نصوصُ المثبَّتات آليًّا قبل أن يُقاس شيء.</p>'
             f'<div class="{box}"><b>MARK_ORDER_VERIFIED = '
             f'{"YES" if mo["verified"] else "NO"}</b> — سطوحٌ مفحوصة '
             f'<b>{mo["scanned"]}</b> · مخالفات <b>{mo["deviations"]}</b> · '
             f'{E(mo["reason"])}</div></div>')

    # ── الجدولُ الرئيس ───────────────────────────────────────────────────
    body = []
    for r in f1["rows"]:
        cls = status_class(r)
        body.append(
            f'<tr><td class="mono">{E(str(r["no"]))}</td>'
            f'<td class="ar">{E(r["word"])}</td>'
            f'<td class="arn">{E(r["normalized"]) or "—"}</td>'
            f'<td>{cell(r["status"], gloss=True)}</td>'
            f'<td class="mono tiny">{E(r["rules"]) or "—"}</td>'
            f'<td class="mono tiny">{E(r["pattern"]) or "—"}</td>'
            f'<td class="mono">{E(str(r["peels"]) or "—")}</td>'
            f'<td class="mono">{E(r["prefixes"]) or "—"}</td>'
            f'<td class="arn">{E(r["stem"]) or "—"}</td>'
            f'<td class="{cls}">{cell(r["termination"], gloss=True)}</td></tr>')
    P.append('<h2>الجدولُ الرئيس — الآيةُ كلمةً كلمة '
             f'({len(f1["rows"])})</h2>'
             '<div class="card"><p class="k">كلُّ صفٍّ هنا مقروءٌ من مخرجات '
             'المحاور الخمسة ومربوطٌ بمفتاح الموضع لا بالترتيب — فلو سقط صفٌّ '
             'ظهر فراغًا يُسأل عنه، ولم ينزلق الجدولُ صامتًا.</p>'
             '<div class="scroll"><table><thead><tr>'
             '<th>#</th><th>الكلمة</th><th>المطبَّعة</th><th>حالُ التطبيع</th>'
             '<th>القواعد</th><th>المقاطع</th><th>قشور</th><th>المقشور</th>'
             '<th>الجذع</th><th>مخرجُ التقشير</th>'
             '</tr></thead><tbody>' + "".join(body)
             + "</tbody></table></div></div>")

    # ── المؤجَّلُ والمحجوب ───────────────────────────────────────────────
    held = [r for r in f1["rows"]
            if r["termination"].startswith(("DEFER", "BLOCK"))]
    rows = "".join(
        f'<tr><td class="ar">{E(r["word"])}</td>'
        f'<td class="arn">{E(r["normalized"])}</td>'
        f'<td class="{status_class(r)}">{cell(r["termination"], gloss=True)}</td>'
        f'<td class="mono tiny">{E(r["classes"]) or "—"}</td></tr>'
        for r in held)
    P.append(f'<h2>ما لم يُقشَّر — بأمانة ({len(held)})</h2>'
             f'<div class="card"><p class="k">التأجيلُ ليس خطأً: هو امتناعٌ '
             f'صادقٌ عن الإثبات حين لا يقوم الدليلُ عند هذه الطبقة. والحجبُ '
             f'دعوى بوجود مانع. وكلاهما <b>باسمٍ من قائمةٍ مغلقة</b>، لا '
             f'برسالةٍ حرّة.</p>'
             f'<table><thead><tr><th>الكلمة</th><th>المطبَّعة</th>'
             f'<th>السبب</th><th>صنفُ حكمك إن وُجد</th></tr></thead>'
             f'<tbody>{rows}</tbody></table></div>')

    # ── دفترُ الحمل ──────────────────────────────────────────────────────
    body = []
    for f in c["fixtures"]:
        for e in f["ledger"]:
            named = " · ".join(f"{k} {v:,}" for k, v in
                               sorted(e["named"].items(), key=lambda kv: -kv[1]))
            closes = e["into"] == e["carried"] + sum(e["named"].values()) \
                + e["unnamed"]
            body.append(
                f'<tr><td>{E(f["id"])}</td><td class="mono">{E(e["edge"])}</td>'
                f'<td class="mono">{e["into"]:,}</td>'
                f'<td class="mono">{e["carried"]:,}</td>'
                f'<td class="mono tiny">{E(named) or "—"}</td>'
                f'<td class="mono">{e["unnamed"]}</td>'
                f'<td class="{"cert" if closes else "bad"}">'
                f'{"يُغلق" if closes else "لا يُغلق"}</td></tr>')
    P.append('<h2>دفترُ الحمل — لا تخطٍّ صامت</h2><div class="card">'
             '<p class="k">لكلّ حافّةٍ بين محورين دفترٌ يُغلق: '
             '<span class="mono">دخل = حُمل + مسمًّى + بلا اسم</span>. '
             'فما لم ينتقل من محورٍ إلى تاليه يحمل اسمَ سببه، وما لا اسمَ له '
             'يظهر في عمودٍ خاصٍّ ولا يُبتلع.</p>'
             '<table><thead><tr><th>المثبَّت</th><th>الحافّة</th><th>دخل</th>'
             '<th>حُمل</th><th>أسبابُ عدم الحمل</th><th>بلا اسم</th>'
             '<th>الدفتر</th></tr></thead><tbody>' + "".join(body)
             + "</tbody></table></div>")

    # ── جردُ الرفض ───────────────────────────────────────────────────────
    fi = c["failure_inventory"]
    rows = "".join(
        f'<tr><td class="mono">{E(k)}</td><td>{E(GLOSS.get(k, "—"))}</td>'
        f'<td class="mono">{v:,}</td><td class="cert">مشهود</td></tr>'
        for k, v in sorted(fi["witnessed"].items(), key=lambda kv: -kv[1]))
    rows += "".join(
        f'<tr><td class="mono">{E(k)}</td><td>{E(GLOSS.get(k, "—"))}</td>'
        f'<td class="mono">0</td><td class="defer">مُعلَنٌ بلا شاهدٍ هنا</td>'
        f'</tr>' for k in fi["unwitnessed"])
    rows += "".join(
        f'<tr><td class="mono">{E(k)}</td><td>{E(GLOSS.get(k, "—"))}</td>'
        f'<td class="mono">{v:,}</td><td class="bad">ظهر ولم يُعلَن</td></tr>'
        for k, v in sorted(fi["undeclared"].items(), key=lambda kv: -kv[1]))
    verdict = ('<div class="ok"><b>UNDECLARED = 0</b> — لا قيمةَ حكمٍ خارج '
               'التاكسونومية المُعلَنة في هذه الجولة.</div>'
               if not fi["undeclared"] else
               f'<div class="fail"><b>UNDECLARED = {len(fi["undeclared"])}</b>'
               f' — قيمةٌ خرجت في مخرجٍ ولم تُعلَن.</div>')
    P.append('<h2>جردُ الرفض — مكتشَفٌ من التشغيل لا من قائمةٍ ثابتة</h2>'
             '<div class="card"><p class="k">الجردُ مقسومٌ ثلاثًا بمرجعٍ '
             'مُعلَن (<span class="mono">ASLOT_REFUSALS</span>) لا بتصنيفٍ من '
             'المولّد: مشهودٌ هنا · مُعلَنٌ بلا شاهدٍ هنا · <b>ظهر ولم يُعلَن'
             '</b>. والثالثُ خرقٌ يُسمّى ولا يُطوى.</p>'
             + verdict
             + f'<p class="k" style="margin-top:8px">مُعلَنٌ '
               f'<b>{fi["declared"]}</b> · بشاهدٍ هنا '
               f'<b>{len(fi["witnessed"])}</b> · بلا شاهدٍ هنا '
               f'<b>{len(fi["unwitnessed"])}</b> · غيرُ مُعلَن '
               f'<b>{len(fi["undeclared"])}</b></p>'
             + '<table><thead><tr><th>الرمز</th><th>بالعربيّة</th>'
               '<th>شواهد</th><th>الحال</th></tr></thead>'
               f'<tbody>{rows}</tbody></table></div>')

    # ── أصنافُ حكم المالك ────────────────────────────────────────────────
    rows = "".join(
        f'<tr><td class="mono">{E(k)}</td><td>{E(GLOSS.get(k, k))}</td>'
        f'<td class="mono">{v:,}</td>'
        f'<td class="defer">بانتظار حكمك — لا صنفَ بقيّةٍ بعد</td></tr>'
        for k, v in c["owner_classes"].items())
    P.append('<h2>أصنافُ قرارك — مقيسةٌ ولم يُسنَد لها صنفُ بقيّة</h2>'
             '<div class="card"><p class="k">هذه أصنافٌ رصدها المحورُ الأوّل '
             'في هذه المثبَّتات وتنتظر حكمك. وسقفُ الرتبة لكلٍّ منها موقوفٌ '
             'على تصنيفها، والمولّدُ <b>لا يصنّف واحدًا منها من عنده</b>.</p>'
             f'<table><thead><tr><th>الصنف</th><th>بالعربيّة</th>'
             f'<th>كلمات</th><th>الحال</th></tr></thead>'
             f'<tbody>{rows}</tbody></table>'
             f'<div class="warn" style="margin-top:8px">'
             f'<b>P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED</b> — الخانةُ تبقى '
             f'فارغةً حتى تملأها أنت.</div></div>')

    # ── العوامل ─────────────────────────────────────────────────────────
    op, cov = c["operators"], c["coverage"]
    labels = {
        "PROVEN_IN_ITS_OWN_WITNESS": ("ثبت في شاهده هو", "cert"),
        "PRESENT_BUT_NOT_PROVEN": ("ظهر توكنًا ولم يثبت", "defer"),
        "NOT_A_STANDALONE_TOKEN": ("ليس توكنًا قائمًا — حرفٌ متّصلٌ أو مركَّب",
                                   "defer"),
        "NOT_NORMALIZABLE": ("تعذّر تطبيعُه", "bad"),
        "WITNESS_NOT_LOCATED": ("لم يُعثر على سطر شاهده", "bad"),
    }
    rows = "".join(
        f'<tr><td>{E(ar)}</td><td class="mono">{E(k)}</td>'
        f'<td class="{cls}">{cov["buckets"].get(k, 0):,}</td></tr>'
        for k, (ar, cls) in labels.items())
    P.append('<h2>جدولُ عواملك وتغطيتُه</h2><div class="card">'
             f'<p class="k">الجدولُ المستعمَل: <span class="mono">'
             f'{E(Path(op["path"]).name)}</span> — <b>{op["count"]}</b> صفًّا · '
             f'<b>{op.get("unique_operators")}</b> عاملًا فريدًا · '
             f'<b>{op["with_example"]}</b> بشاهدٍ مشكول · '
             f'<span class="mono">sha256 {E(str(op["sha256"])[:16])}…</span></p>'
             f'<p class="k">والتغطيةُ تُقاس <b>في شاهد كلّ عاملٍ هو</b> لا في '
             f'مجموع النصّ: عاملٌ ثبت في سطر غيره لا يُثبت أنّ سطرَه رُئي.</p>'
             f'<table><thead><tr><th>الحال</th><th>الرمز</th><th>عدد</th>'
             f'</tr></thead><tbody>{rows}</tbody></table>'
             f'<div class="warn" style="margin-top:8px">'
             f'«ليس توكنًا قائمًا» ليست إخفاقًا: <span class="ar">بِ</span> في '
             f'<span class="ar">بِزَيْدٍ</span> حرفٌ متّصل، والمحورُ الثاني '
             f'جردُ كلماتٍ تامّةٍ مغلقة. فعدُّها إخفاقًا خلط، وعدُّها نجاحًا '
             f'دعوى — فسُمّيت وتُركت. و<b>LICENSE_GRANTED = NO</b>: قراءةُ '
             f'الجدول ليست اعتمادًا له.</div></div>')

    # ── المثبَّتات الثلاثة والإثباتُ الموجَب ─────────────────────────────
    rows = ""
    for f in c["fixtures"]:
        axes = " · ".join(str(a["rows"]) for a in f["run"]["axes"].values())
        bad = [x["name"] for x in f["checks"] if not x["ok"]]
        rows += (f'<tr><td class="mono">{E(f["id"])}</td><td>{E(f["name"])}'
                 f'<div class="k tiny">{E(f["kind"])}</div></td>'
                 f'<td class="mono">{f["stats"].get("tokens", "—")}</td>'
                 f'<td class="mono">{E(axes)}</td>'
                 f'<td class="mono tiny">{E(str(f["stats"].get("sha256"))[:16])}…'
                 f'</td>'
                 f'<td class="{"cert" if not bad else "bad"}">'
                 f'{"كلُّ موجَبٍ مرّ" if not bad else E(" · ".join(bad))}</td>'
                 f'</tr>')
    P.append('<h2>المثبَّتاتُ الثلاثة</h2><div class="card">'
             '<p class="k">قبل أن يُقرأ أيُّ نفي — «صفرُ إخفاقات» — يُثبت '
             'موجَبٌ أنّ الطاحونة دارت: خمسةُ محاورَ أنتجت، وعددُ صفوف المحور '
             'صفر يطابق توكنات النصّ، ولا صفَّ بلا مرساة. فمخرجٌ خالٍ يعطي '
             'صفرَ إخفاقاتٍ أيضًا.</p>'
             '<table><thead><tr><th>#</th><th>المثبَّت</th><th>توكنات</th>'
             '<th>المحاور ٠→٤</th><th>البصمة</th><th>الإثباتُ الموجَب</th>'
             f'</tr></thead><tbody>{rows}</tbody></table></div>')

    # ── الأثر ────────────────────────────────────────────────────────────
    P.append('<h2>الأثر</h2><div class="card">'
             '<p class="k">كلُّ صفٍّ يحمل مرساةً تدلّ على موضعه وسلسلةً تصله '
             'بالمحور السابق. والمرساةُ <b>محسوبةٌ من الموضع</b> لا مولَّدةٌ '
             'عشوائيًّا — فأُعيد بناؤها هنا وقُوبلت، ولم يُكتفَ بعدّها.</p>'
             '<table><tr>'
             f'<td style="text-align:center"><div class="big">{tr["rows"]:,}'
             f'</div><div class="lbl">صفوفٌ كلّيّة</div></td>'
             f'<td style="text-align:center"><div class="big">'
             f'{tr["anchored"]:,}</div><div class="lbl">بمرساة</div></td>'
             f'<td style="text-align:center"><div class="big" '
             f'style="color:#1a7f37">{tr["without"]:,}</div>'
             f'<div class="lbl">بلا مرساة</div></td>'
             f'<td style="text-align:center"><div class="big">'
             f'{tr["reconstructed"]:,}</div>'
             f'<div class="lbl">أُعيد بناؤها وطوبقت</div></td>'
             '</tr></table></div>')

    # ── التحقّقُ المستقلّ ────────────────────────────────────────────────
    P.append('<h2>التحقّقُ المستقلّ — حاجزٌ لا مجاملة</h2><div class="card">'
             '<p class="k">مدقِّقٌ يستورد المولِّد يعيد استعمال حسابه، فيوافقه '
             'ولو أخطأ كلاهما بالخطأ نفسِه. فالمدقِّقُ هنا لا يستورد من '
             'المولّد شيئًا: يقرأ هذا الملفَّ نصًّا، ويقرأ الـCSV خامًّا، '
             'ويقابل.</p>'
             '<div class="kv mono">GENERATOR_IMPORTS_VERIFIER = 0'
             ' &nbsp;·&nbsp; VERIFIER_IMPORTS_GENERATOR = 0</div>'
             '<table style="margin-top:8px"><thead><tr><th>الحاجز</th>'
             '<th>ما يُثبته</th></tr></thead><tbody>'
             '<tr><td class="mono">V0_SOURCE_CSVS_ARE_NON_EMPTY</td>'
             '<td>أنّ الطاحونة دارت — قبل أن يُقرأ أيُّ نفي</td></tr>'
             '<tr><td class="mono">V1_EVERY_WORD_OF_THE_VERSE_APPEARS</td>'
             '<td>أنّ الجدولَ لم يُسقط كلمةً صامتًا</td></tr>'
             '<tr><td class="mono">V2_HEADLINE_NUMBERS_MATCH_THE_CSV</td>'
             '<td>أنّ أعدادَ اللوحة مقروءةٌ من المخرج لا محسوبةٌ مرّتين</td></tr>'
             '<tr><td class="mono">V3_HEADLINE_CLOSES_ON_THE_VERSE</td>'
             '<td>أنّ اللوحةَ تقفل على عدد الكلمات بلا بقيّة</td></tr>'
             '<tr><td class="mono">V4_EVERY_POSITIVE_COUNT_HAS_A_WITNESS'
             '</td><td>ألّا اسمَ يحمل عددًا موجبًا بلا شاهدٍ خام</td></tr>'
             '<tr><td class="mono">V5_TRACE_TOTAL_MATCHES_RAW_ROW_COUNT</td>'
             '<td>أنّ مجموعَ الأثر هو العدُّ الخام نفسُه</td></tr>'
             '<tr><td class="mono">V6_PAYLOAD_SHA256_RECOMPUTES</td>'
             '<td>أنّ الوثيقةَ لم تُمسّ بعد توليدها</td></tr>'
             '</tbody></table>'
             '<div class="new" style="margin-top:8px">نتيجةُ التحقّق '
             '<b>غيرُ مضمَّنةٍ هنا عمدًا</b>: تضمينُها يغيّر الحمولةَ التي '
             'تحقَّق منها، فيسقط <span class="mono">V6</span>. فتُشغَّل على '
             'هذا الملفّ بعد توليده:<br>'
             '<span class="mono">python3 scripts/verify_manager_report.py '
             'inspection/manager_report.html</span></div></div>')

    # ── أعمدةٌ لا يعرضها التقرير ─────────────────────────────────────────
    unshown = c["unshown"]
    total = sum(len(v) for v in unshown.values())
    rows = "".join(
        f'<tr><td class="mono">المحور {i} — {E(AXIS_FILES[i][0])}</td>'
        f'<td class="mono">{" · ".join(E(x) for x in cols)}</td>'
        f'<td class="mono">{len(cols)}</td></tr>'
        for i, cols in sorted(unshown.items()))
    P.append('<h2>أعمدةٌ تنتجها المصدِّرات ولا يعرضها هذا التقرير</h2>'
             '<div class="card"><p class="k">هذا القسمُ هو ما يجعل التقريرَ '
             '<b>يتبع الشيفرة</b>: كلُّ عمودٍ يُضاف إلى مخرجات المحاور يظهر '
             'هنا في أوّل تشغيلٍ بعد إضافته، فلا يسقط في صمت. وإخفاءُ عمودٍ '
             'قرارُ عرضٍ يُعلَن، لا نسيانٌ يُكتشف بعد شهر.</p>'
             f'<div class="new">العدد: <b>{total}</b> عمودًا</div>'
             f'<table style="margin-top:8px"><thead><tr><th>المخرج</th>'
             f'<th>الأعمدة</th><th>عدد</th></tr></thead>'
             f'<tbody>{rows}</tbody></table></div>')

    # ── ما لا يُدَّعى ────────────────────────────────────────────────────
    rows = "".join(
        f'<tr><td>{E(ar)}</td><td class="mono">{E(k)}</td>'
        f'<td class="defer">{E(v)}</td><td class="k">{E(why)}</td></tr>'
        for ar, k, v, why in NOT_CLAIMED)
    P.append('<h2>ما لا يدّعيه هذا التقرير — بالتصريح لا بالعجز</h2>'
             '<div class="card"><p class="k">النظامُ الذي يسكت عمّا لم يفعله '
             'يُوهم أنه فعله. فهذه الطبقاتُ مُعلَنةٌ غيرَ مفتوحة، وسكوتُ '
             'التقرير عنها كان سيكون أخطرَ من إعلانها.</p>'
             f'<table><thead><tr><th>الطبقة</th><th>العلَم</th><th>القيمة</th>'
             f'<th>لماذا</th></tr></thead><tbody>{rows}</tbody></table></div>')

    # ── الموقوفُ على حكمك ────────────────────────────────────────────────
    rows = "".join(f'<tr><td class="mono">{i}</td><td>{E(t)}</td>'
                   f'<td class="k">{E(w)}</td></tr>'
                   for i, (t, w) in enumerate(c["owner_pending"], 1))
    P.append('<h2>الموقوفُ على حكمك</h2><div class="card">'
             '<p class="k">عند الفجوة الدستوريّة: لا تُصنع قاعدة، ولا يُضاف '
             'استثناء، ولا يُختار بين البدائل نيابةً عنك.</p>'
             f'<table><thead><tr><th>#</th><th>القرار</th><th>ما يفتحه</th>'
             f'</tr></thead><tbody>{rows}</tbody></table></div>')

    P.append('<div class="warn">الحالُ الحوكميّة: '
             '<span class="mono">RULE_OWNER = DR_HUSSEIN</span> · '
             '<span class="mono">LICENSE_GRANTED = NO</span> · '
             '<span class="mono">RATIFICATION = NO</span> — '
             'المراجعةُ اللغويّةُ البشريّة لم تجرِ على هذه المخرجات.</div>')
    return "\n".join(P)


def wrap(body: str, uid: str, payload_sha: str) -> str:
    return (f'<!doctype html>\n<html lang="ar" dir="rtl"><head>'
            f'<meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<title>تقريرُ المدير — سلسلةُ أسلوط</title>'
            f'<style>{CSS}</style></head><body>{body}'
            f'<div class="mono" style="margin-top:14px">REPORT_UID = {uid}'
            f'  ·  PAYLOAD_SHA256 = {payload_sha}'
            f'  (SCOPE = هذه الوثيقة عدا هذا السطر)</div>'
            f'</body></html>')


def build(args: argparse.Namespace) -> dict:
    dirs = {"F1": args.f1_dir, "F2": args.f2_dir, "F3": args.f3_dir}
    texts = {"F1": args.f1_text, "F2": args.f2_text, "F3": args.f3_text}

    fixtures = []
    for fid, name, kind in FIXTURES:
        run_dir = Path(dirs[fid]) if dirs[fid] else None
        run = load_run(run_dir)
        src = Path(texts[fid]) if texts[fid] else None
        stats = (text_stats(src.read_text(encoding="utf-8"))
                 if src and src.is_file() else {})
        fixtures.append({
            "id": fid, "name": name, "kind": kind, "run": run, "stats": stats,
            "rows": word_rows(run),
            "checks": positive_assertions(run, stats.get("tokens", UNMEASURED)),
            "ledger": carry_ledger(run),
            "owner_classes": owner_classes_of(run_dir),
        })

    runs = [f["run"] for f in fixtures]
    operators = load_operators(Path(args.operators_csv)
                               if args.operators_csv else None)
    f2 = next(f for f in fixtures if f["id"] == "F2")
    coverage = operator_coverage(operators, f2["run"],
                                 Path(args.f2_text) if args.f2_text else None)

    terms: Counter = Counter()
    for f in fixtures:
        own: Counter = Counter()
        for r in f["rows"]:
            t = r["termination"]
            if t.startswith("BLOCK"):
                own["block"] += 1
            elif t.startswith("DEFER"):
                own["defer"] += 1
            elif t:
                own["accept"] += 1
            else:
                own["not_carried"] += 1
        f["terms"] = {k: own.get(k, 0)
                      for k in ("accept", "defer", "block", "not_carried")}
        terms.update(own)

    return {
        "fixtures": fixtures,
        "trace": trace_totals(runs),
        "failure_inventory": failure_inventory(runs),
        "owner_classes": residual_totals(fixtures),
        "operators": operators,
        "coverage": coverage,
        "unshown": unshown_columns(runs),
        "term_counts": terms,
        "git": load_git_facts(Path(args.git_facts) if args.git_facts else None),
        "taaqol_commit": args.taaqol_commit or UNMEASURED,
        "python": ".".join(map(str, sys.version_info[:3])),
        "mark_order": mark_order_gate(
            args.mark_order_cmd,
            [Path(p) for p in (args.f1_text, args.f2_text, args.f3_text) if p]),
        "owner_pending": [
            ("T-4 · صنفُ البقيّة للأصناف السبعة", "سقوفَ الرتب كلَّها"),
            ("T-4 · عيبُ التنوين: حاجبٌ أم مؤجَّلٌ ظاهر", "فحصَ البقيّة المخفيّة"),
            ("T-5 · Γ يغيّر الأحكام", "أحكامَ الغلق الستّة"),
            ("T-6 · الخطوطُ تُنزل تقشيرَ «كَتَبَ»", "المنعَ في زمن التشغيل"),
            ("T-7 · بوّاباتُ الانتقال بين المحاور", "حكمَ الحركة"),
            ("اعتمادُ السجلّين", "رفعَ LICENSE_GRANTED"),
            ("آ خارجَ «أل»", "توسيعَ N10.2 أو حصرَها"),
        ],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="تقريرُ المدير")
    p.add_argument("--out", default="inspection/manager_report.html")
    for fixture in ("f1", "f2", "f3"):
        p.add_argument(f"--{fixture}-dir")
    p.add_argument("--f1-text", default="inspection/ayat.txt")
    p.add_argument("--f2-text", default="inspection/runs/f2/input.txt")
    p.add_argument("--f3-text", default="inspection/story.txt")
    p.add_argument("--operators-csv")
    p.add_argument("--git-facts")
    p.add_argument("--taaqol-commit")
    p.add_argument("--mark-order-cmd")
    args = p.parse_args(argv)

    context = build(args)
    body = render(context)
    payload = sha256_of(body.encode("utf-8"))
    head = context["git"].get("head", "UNKNOWN")[:7]
    uid = f"ASLOT_MANAGER_{head}-p{payload[:8]}"
    Path(args.out).write_text(wrap(body, uid, payload), encoding="utf-8")

    fi = context["failure_inventory"]
    print(f"REPORT_UID = {uid}")
    print(f"PAYLOAD_SHA256 = {payload}")
    print(f"GIT = {context['git'].get('status')} "
          f"{context['git'].get('head', '')[:12]} "
          f"({context['git'].get('branch', '')})")
    print(f"ROWS  F1 {len(context['fixtures'][0]['rows'])} · "
          f"F2 {len(context['fixtures'][1]['rows'])} · "
          f"F3 {len(context['fixtures'][2]['rows'])}")
    print(f"TERMINATIONS  {dict(context['term_counts'])}")
    print(f"REFUSALS  مُعلَن {fi['declared']} · بشاهد {len(fi['witnessed'])} · "
          f"بلا شاهد {len(fi['unwitnessed'])} · "
          f"غيرُ مُعلَن {len(fi['undeclared'])}")
    print(f"UNSHOWN_COLUMNS = {sum(len(v) for v in context['unshown'].values())}")
    print(f"→ {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
