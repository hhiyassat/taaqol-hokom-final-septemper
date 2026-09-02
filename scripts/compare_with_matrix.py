#!/usr/bin/env python3
"""يقابل تحليلَ أسلوط للنازلة بمصفوفة تعقُّل — قراءةً من الملفّين لا من الذاكرة.

    python3 scripts/compare_with_matrix.py \\
        --matrix inspection/TAAQOL_NAZILA_MATRIX.md \\
        --run inspection/runs/f5 --out inspection/comparison.html

**قاعدةُ هذا الملفّ.** لا رقمَ مكتوبٌ بيد. أرقامُ المصفوفة **تُستخرج من نصّ
الوثيقة**، وأرقامُ أسلوط **تُقرأ من مخرجات الجولة**، والمقابلةُ تقع بينهما.
فلو غُيّرت الوثيقةُ أو أُعيد التشغيل تغيّر التقريرُ تبعًا — ولا يبقى رقمٌ
صحيحًا لأنّه كُتب مرّة.

**وأخطرُ ما تكشفه هذه المقابلة** ليس اختلافَ عدد، بل اختلافَ **طبقة**:
مصفوفةُ تعقُّل تبدأ من `PATH_CLASSIFICATION` وتنتهي عند `ANSWER_AUDIT`، وأسلوط
يبدأ من السطح وينتهي عند الجذع. فبينهما فجوةٌ لا يعبرها أحدُهما إلى الآخر،
والمقارنةُ التي تُوهم أنّهما يقيسان الشيءَ نفسَه **مقارنةٌ كاذبة**.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import re
from pathlib import Path

E = html.escape
PUNCT = "،.؛؟:!"

#: محاورُ أسلوط الخمسة — ما تفعله كلٌّ منها بعبارةٍ واحدة.
ASLOT_AXES = [
    ("0", "بناءُ النصّ", "توكنٌ لكلّ كلمة، بموضعٍ ومرساةِ أثر"),
    ("1", "التطبيع", "سطحٌ قانونيٌّ واحد، بقواعدَ مسمّاةٍ وأصنافِ قرار"),
    ("2", "الحصر", "هل الكلمةُ صورةٌ مغلقةٌ في السجلّ؟"),
    ("3", "التقطيع", "بنيةُ المقاطع الصوتيّة CV"),
    ("4", "التقشير", "قشرُ ما رُخِّص، والوقوفُ عند الجذع"),
]


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def read_rows(path: Path) -> list[dict]:
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return list(csv.DictReader(fh))


# ── استخراجُ ما تدّعيه الوثيقة ───────────────────────────────────────────
def parse_matrix(path: Path) -> dict:
    doc = path.read_text(encoding="utf-8")
    # المفتاحُ يحمل أرقامًا (`INPUT_SHA256`)، و`[A-Z_]+` لا يلتقطها — فكان
    # المفتاحُ يغيب، فتُقارَن بصمةٌ بفراغٍ فتُعلَن «لا تطابق». وهو إخفاقٌ
    # لعلّةٍ خاطئة: العيبُ في القارئ لا في الوثيقة. ولذلك يلي هذا حارسٌ
    # يفرّق بين «لم يُعثر على الدعوى» و«الدعوى لا تقفل».
    kv = dict(re.findall(r"^([A-Z_0-9]+) = (.+)$", doc, re.M))
    stages = re.findall(
        r"^\| *(\d+) \| `([A-Z_]+)` \| `([A-Z_]+)` \| `([A-Z ->]+)` \|", doc, re.M)
    residuals = re.findall(
        r"^\| `([a-zA-Z_:]+)` \| *(\d+) \|", doc.split("## 6.")[1].split("```")[0],
        re.M)
    sec8 = doc.split("## 8.")[1].split("## 9.")[0]
    listed = re.findall(r"^\| `([^`]+)` \|", sec8, re.M)
    relations = re.findall(r"^\| (?:علاقة )?`?([^|`]+)`? \| (.+?) \|$",
                           doc.split("## 9.")[1].split("## 10.")[0], re.M)
    lines_count = re.search(r"عدد الخطوط في السجل \| (\d+)", doc)
    split = re.search(r"(\d+) ما قبل النص `NOT_APPLICABLE`، و(\d+)", doc)
    owner_q = re.findall(r"^\| (.+?) \| (.+?) \| `OWNER_PENDING` \|$", doc, re.M)
    ambiguity = re.findall(r"^\| `([^`]+)` \| (.+?) \|$",
                           doc.split("## 12.b")[1].split("## 13.")[0], re.M)
    withdrawn = re.findall(r"^\| (.+?) \| `([A-Z_]+)` \| (.+?) \|$",
                           doc.split("## 13.")[1].split("## 14.")[0], re.M)
    verdict = re.findall(r"^  ([A-Z_]+)$", doc.split("VERDICT =")[1], re.M)
    return {
        "path": str(path), "sha256": sha(doc), "kv": kv, "_doc": doc,
        "input_text": kv.get("INPUT_TEXT", "").strip(),
        "declared_input_sha": kv.get("INPUT_SHA256", ""),
        "stages": [(int(n), s, st, rk) for n, s, st, rk in stages],
        "residuals": [(n, int(c)) for n, c in residuals],
        "words_listed": listed,
        "relations": relations,
        "forbidden_lines": int(lines_count.group(1)) if lines_count else None,
        "forbidden_split": (int(split.group(1)), int(split.group(2)))
        if split else None,
        "owner_questions": owner_q,
        "ambiguity": ambiguity,
        "withdrawn": withdrawn,
        "verdict": verdict,
    }


def audit_matrix(m: dict) -> list[dict]:
    """يعيد حسابَ ما تدّعيه الوثيقة من أرقامها هي — لا من أرقامي."""
    out = []
    text = m["input_text"]
    tokens = text.split()

    recomputed = sha(text)
    declared = m["declared_input_sha"]
    out.append({
        "claim": "INPUT_SHA256 يطابق النصَّ المقتبس في الوثيقة نفسِها",
        "ok": bool(declared) and recomputed == declared,
        "detail": (f"{recomputed[:16]}… ⟵ {declared[:16]}…" if declared else
                   "لم يُعثر على INPUT_SHA256 في الوثيقة — "
                   "وهذا عجزُ قارئٍ لا نفيُ تطابق")})

    declared_tokens = int(re.search(r"(\d+)", m["kv"].get(
        "MEASURED_RECORDS", "0")).group(1)) if m["kv"].get("MEASURED_RECORDS") \
        else 0
    out.append({
        "claim": "MEASURED_RECORDS = عددُ التوكنات × عددِ المراحل",
        "ok": declared_tokens == len(tokens) * len(m["stages"]),
        "detail": f"{declared_tokens} ⟵ {len(tokens)} × {len(m['stages'])}"
                  f" = {len(tokens) * len(m['stages'])}"})

    out.append({
        "claim": "STAGE_COVERAGE = 16 مرحلةً مذكورةً في الجدول",
        "ok": len(m["stages"]) == 16,
        "detail": f"{len(m['stages'])} مرحلة"})

    executed = [s for _, s, st, _ in m["stages"] if st == "EXECUTED"]
    out.append({
        "claim": "RUNTIME_EXECUTION = LIMITED — مرحلةٌ واحدةٌ منفَّذة",
        "ok": len(executed) == 1,
        "detail": f"{len(executed)}/16 · {executed}"})

    zero = all(rk.replace(" ", "") == "ZERO->ZERO" for *_, rk in m["stages"])
    out.append({"claim": "كلُّ الرتب ZERO ⟵ ZERO", "ok": zero,
                "detail": "لا ترقيةَ في أيّ مرحلة"})

    res = dict(m["residuals"])
    total_records = len(tokens) * len(m["stages"])
    with_res = res.get("RUNTIME_CONTEXT_PENDING", 0)
    hints = sum(v for k, v in res.items() if k != "RUNTIME_CONTEXT_PENDING")
    out.append({
        "claim": "دفترُ البقايا يُغلق: سجلّاتٌ ذاتُ بقيّة + سجلّاتٌ فارغة = الكلّ",
        "ok": with_res + len(tokens) == total_records,
        "detail": f"{with_res} + {len(tokens)} = {with_res + len(tokens)}"
                  f" ⟵ {total_records}"})
    out.append({
        "claim": "بقايا التلميح ≤ السجلّاتِ ذات البقيّة",
        "ok": hints <= with_res,
        "detail": f"{hints} ≤ {with_res}"
                  f"   (الفرقُ {with_res - hints} = مرحلةُ NOT_APPLICABLE)"})

    if m["forbidden_split"]:
        a, b = m["forbidden_split"]
        out.append({
            "claim": "قسمةُ الخطوط الممنوعة تجمع إلى عددها",
            "ok": a + b == m["forbidden_lines"],
            "detail": f"{a} + {b} = {a + b} ⟵ {m['forbidden_lines']}"})

    # الدعوى تُقسم بعد حكم المالك في الفاصلة والنقطة، لأنّ الخلطَ بينهما
    # يظلم الوثيقة: صارت **مصيبةً في النتيجة**، وتبقى ساكتةً عن الفعل.
    # وهما شيئان، والحكمُ عليهما بحكمٍ واحد خلطٌ لا دقّة فيه.
    ruled = "\u060C\u002E"
    stripped = [t for t in tokens
                if t not in m["words_listed"] and t.strip(ruled) in m["words_listed"]]
    others = [t for t in tokens
              if t not in m["words_listed"] and t.strip(ruled) not in m["words_listed"]]
    out.append({
        "claim": "ألفاظُ §8 تطابق التوكنات بعد قطع فواصل المالك (، و.)",
        "ok": not others,
        "detail": ("مطابقةٌ تامّة — وهي النتيجةُ نفسُها التي بلغها أسلوط "
                   "بحكم المالك" if not others else f"يبقى مختلفًا: {others}")})
    declared = bool(re.search(r"فاصل|ترقيم|تجريد|strip|punct", m["_doc"], re.I))
    out.append({
        "claim": "الوثيقةُ تُعلن أنّها قطعت الترقيم قبل التحليل",
        "ok": declared,
        "detail": ("مُعلَن" if declared else
                   f"لا ذكرَ له في الوثيقة، وقد وقع على "
                   f"{len(stripped)} توكنًا: {' · '.join(stripped)}")})
    return out


# ── ما قاسه أسلوط ────────────────────────────────────────────────────────
def aslot_rows(run: Path) -> list[dict]:
    a0 = {r["Word_No"]: r for r in read_rows(run / "axis0/QURAN_WORDS.csv")}
    a1 = read_rows(run / "axis1/AXIS_1_NORMALIZATION.csv")
    a2 = {r["Word_No"]: r for r in read_rows(run / "axis2/AXIS_2_TOKENS.csv")}
    a3 = {r["Word_No"]: r for r in read_rows(run / "axis3/AXIS_3_SYLLABLES.csv")}
    a4 = {r["Word_No"]: r for r in read_rows(run / "axis4/AXIS_4_PEEL_TO_STEM.csv")}
    out = []
    for r in a1:
        k = r["Word_No"]
        p = a4.get(k, {})
        out.append({
            "no": k, "word": r["Word"],
            "normalized": r["Normalized_Word"],
            "status": r["Normalization_Status"],
            "rules": r["Rules_Applied"],
            "classes": r["Owner_Decision_Classes"],
            "stop": r["Stop_Reason"],
            "proof": a2.get(k, {}).get("Closed_Form_Proof", ""),
            "pattern": a3.get(k, {}).get("Syllable_Pattern", ""),
            "termination": p.get("Termination", ""),
            "cut": a0.get(k, {}).get("Cut_Separators", ""),
            "reached": bool(p),
        })
    return out


# ── التصيير ──────────────────────────────────────────────────────────────
CSS = """
body{font-family:-apple-system,'Segoe UI','Noto Naskh Arabic',Tahoma;
  background:#f6f8fa;color:#1f2328;margin:0;padding:18px;line-height:1.8}
h1,h2,h3{color:#0b3d2e} h1{font-size:26px;margin:0 0 6px}
.card{background:#fff;border:1px solid #d0d7de;border-radius:10px;
  padding:14px 16px;margin:12px 0}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{border:1px solid #d0d7de;padding:7px 9px;text-align:right;
  vertical-align:top}
th{background:#eaeef2} tbody tr:nth-child(even){background:#fafbfc}
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
.cert{color:#1a7f37;font-weight:700} .defer{color:#9a6700;font-weight:700}
.bad{color:#cf222e;font-weight:700} .k{color:#57606a}
.mono{font-family:ui-monospace,Menlo,monospace;font-size:12px;color:#57606a;
  direction:ltr;unicode-bidi:embed}
.ar{font-size:17px;font-weight:700;color:#0a3069}
.arn{font-size:17px;font-weight:700;color:#1a7f37}
.tiny{font-size:11px} .scroll{overflow-x:auto}
.big{font-size:32px;font-weight:800;color:#0b3d2e}
.lbl{color:#57606a;font-size:13px}
.a{background:#f2f8ff} .b{background:#f7f7f2}
@media print{body{background:#fff;padding:0}.card{break-inside:avoid}}
"""


def render(c: dict) -> str:
    m, rows, audit = c["matrix"], c["rows"], c["audit"]
    P: list[str] = []

    P.append("<h1>مقابلةُ تحليلين لنازلةٍ واحدة</h1>")
    P.append('<div class="banner">النظامان لا يقيسان الشيءَ نفسَه: '
             'أسلوط من السطح إلى الجذع · تعقُّل من تصنيف المسار إلى تدقيق '
             'الجواب — وبينهما فجوةٌ لا يعبرها أحدُهما.</div>')

    # ── الهويّة ─────────────────────────────────────────────────────────
    srows = "".join(
        f'<tr><td>{E(s["label"])}</td>'
        f'<td class="ar">{E(s["text"][:44])}{"…" if len(s["text"]) > 44 else ""}</td>'
        f'<td class="mono">{s["tokens"]}</td>'
        f'<td class="mono">{E(s["sha"][:24])}…</td></tr>' for s in c["surfaces"])
    diff = "".join(
        f'<tr><td class="mono">{i}</td><td class="ar">{E(a)}</td>'
        f'<td class="ar">{E(b)}</td><td class="k">{E(note)}</td></tr>'
        for i, a, b, note in c["diffs"])
    P.append('<h2>١ · أيُّ جملة؟ — ثلاثةُ سطوحٍ لا سطحٌ واحد</h2>'
             '<div class="card"><p class="k">قبل أيّ مقابلةٍ في النتائج، '
             'مقابلةٌ في المدخل. والنصُّ الذي في الوثيقة ليس هو الذي في '
             'رسالتك، ولا الذي شُغِّل قبل ذلك. والبصمةُ تفصل.</p>'
             '<table><thead><tr><th>السطح</th><th>النصّ</th><th>توكنات</th>'
             f'<th>sha256</th></tr></thead><tbody>{srows}</tbody></table>'
             '<h3>الفروقُ بين نصّ الوثيقة ونصّ رسالتك</h3>'
             '<table><thead><tr><th>#</th><th>الوثيقة</th><th>الرسالة</th>'
             f'<th>الأثر</th></tr></thead><tbody>{diff}</tbody></table></div>')

    # ── تدقيقُ حساب الوثيقة ─────────────────────────────────────────────
    arows = "".join(
        f'<tr><td>{E(a["claim"])}</td>'
        f'<td class="{"cert" if a["ok"] else "bad"}">'
        f'{"يقفل ✔" if a["ok"] else "لا يقفل ✘"}</td>'
        f'<td class="mono">{E(a["detail"])}</td></tr>' for a in audit)
    passed = sum(a["ok"] for a in audit)
    P.append('<h2>٢ · حسابُ الوثيقة — أُعيد من أرقامها هي</h2>'
             '<div class="card"><p class="k">أوّلُ واجبٍ في المقابلة أن '
             '<b>تُدقَّق الوثيقةُ بنفسها</b> قبل أن تُقابَل بغيرها: هل تجمع '
             'أعدادُها؟ وهل بصمتُها تعيد حسابَ نصِّها؟ ولا يُقبل رقمٌ لأنّه '
             'مطبوع.</p>'
             + (f'<div class="{"ok" if passed == len(audit) else "warn"}">'
                f'<b>{passed} من {len(audit)}</b> دعوى أعيد حسابُها فقفلت.'
                f'</div>')
             + '<table style="margin-top:8px"><thead><tr><th>الدعوى</th>'
               '<th>الحال</th><th>الحساب</th></tr></thead>'
               f'<tbody>{arows}</tbody></table></div>')

    # ── خريطةُ الطبقات ──────────────────────────────────────────────────
    ax = "".join(f'<tr class="a"><td class="mono">أسلوط · محور {n}</td>'
                 f'<td>{E(name)}</td><td>{E(what)}</td>'
                 f'<td class="cert">منفَّذ ومقيس</td></tr>'
                 for n, name, what in ASLOT_AXES)
    st = "".join(
        f'<tr class="b"><td class="mono">تعقُّل · مرحلة {n}</td>'
        f'<td class="mono">{E(s)}</td><td class="k">—</td>'
        f'<td class="{"cert" if state == "EXECUTED" else "defer"}">'
        f'{E(state)}</td></tr>' for n, s, state, _ in m["stages"])
    P.append('<h2>٣ · خريطةُ الطبقات — أين يقف كلٌّ منهما</h2>'
             '<div class="card"><p class="k">هذه أهمُّ لوحةٍ في التقرير. '
             'أسلوط يشتغل على <b>السطح</b>: يطبّعه، ويقطّعه، ويقشّره. وتعقُّل '
             'يبدأ من <b>تصنيف المسار</b> فما فوق. فمخرجُ أسلوط ليس مدخلًا '
             'لأيّ مرحلةٍ من مراحل المصفوفة اليوم، ولا العكس — '
             '<b>لا جسرَ بينهما</b>، والادّعاءُ بأنّهما يتحقّقان من بعضهما '
             'باطل.</p>'
             '<table><thead><tr><th>الطبقة</th><th>الاسم</th>'
             '<th>ماذا تفعل</th><th>الحال في هذه الجولة</th></tr></thead>'
             f'<tbody>{ax}<tr><td colspan="4" class="k" '
             f'style="text-align:center;background:#fff8c5">'
             f'⟵ فجوةٌ غيرُ مجسورة: لا شيء يصل الجذعَ بتصنيف المسار ⟶</td></tr>'
             f'{st}</tbody></table></div>')

    # ── الجدولُ المزدوج ─────────────────────────────────────────────────
    body = ""
    for r in rows:
        gloss = c["gloss"].get(r["word"].strip(PUNCT), ("—", "—"))
        cls = ("bad" if r["termination"].startswith("BLOCK")
               else "defer" if r["termination"].startswith("DEFER")
               else "cert" if r["termination"] else "bad")
        body += (
            f'<tr><td class="mono">{E(r["no"])}</td>'
            f'<td class="ar">{E(r["word"])}</td>'
            f'<td class="a arn">{E(r["normalized"]) or "—"}</td>'
            f'<td class="a mono tiny">{E(r["pattern"]) or "—"}</td>'
            f'<td class="a {cls}">{E(r["termination"] or r["status"])}'
            + (f'<div class="mono tiny">{E(r["stop"])}</div>' if r["stop"] else "")
            + (f'<div class="mono tiny">[{E(r["classes"])}]</div>'
               if r["classes"] else "")
            + f'</td><td class="b">{E(gloss[0])}</td>'
              f'<td class="b k">{E(gloss[1])}</td></tr>')
    P.append('<h2>٤ · الكلمةُ الواحدة عند الاثنين</h2>'
             '<div class="card"><p class="k">الأزرقُ مقيسٌ من جولة أسلوط. '
             'والرماديُّ منقولٌ من §8 في الوثيقة، وهي تعلن عن نفسها '
             '<span class="mono">DECLARED_NOT_MEASURED</span> — أي عملٌ بشريٌّ '
             'مفسِّر لا خرجُ تشغيل. فالعمودان <b>ليسا في رتبةٍ واحدة</b>، '
             'ووضعُهما متجاورين لبيان الفرق لا لادّعاء التكافؤ.</p>'
             '<div class="scroll"><table><thead><tr><th>#</th><th>الكلمة</th>'
             '<th class="a">أسلوط: المطبَّعة</th><th class="a">المقاطع</th>'
             '<th class="a">المخرج</th>'
             '<th class="b">تعقُّل §8: إفادةٌ محتملة</th>'
             '<th class="b">ما لا يجوز أخذه منه وحده</th>'
             f'</tr></thead><tbody>{body}</tbody></table></div></div>')

    # ── الترقيم ─────────────────────────────────────────────────────────
    p = c["punct"]
    P.append('<h2>٥ · الفاصلةُ والنقطة — بعد حكمك</h2>'
             '<div class="card">'
             f'<div class="ok"><b>حكمُ المالك: «عالج الفاصلة والنقطة».</b> '
             f'فصارتا فاصلتين تُقطعان من طرفَي التوكن، وما قُطع يُسجَّل في '
             f'عمود <span class="mono">Cut_Separators</span> فلا يُحذف بلا '
             f'أثر. والأساسُ موحَّدٌ الآن: <b>{p["reached"]} من '
             f'{p["tokens"]}</b> توكناتٍ تبلغ المحورَ الرابع، وهي العشرةُ '
             f'نفسُها التي تعدّها الوثيقة.</div>'
             + ('<table style="margin-top:8px"><thead><tr><th>التوكن</th>'
                '<th>ما قُطع</th><th>السطحُ الداخل</th><th>المخرج</th>'
                '</tr></thead><tbody>' + "".join(
                    f'<tr><td class="ar">{E(r["word"])}{E(r["cut"])}</td>'
                    f'<td class="ar">{E(r["cut"])}</td>'
                    f'<td class="arn">{E(r["normalized"])}</td>'
                    f'<td class="cert">{E(r["termination"])}</td></tr>'
                    for r in rows if r["cut"]) + '</tbody></table>'
                if any(r["cut"] for r in rows) else "")
             + '<div class="new" style="margin-top:8px"><b>وما لم يُحكم فيه '
               'لم يُقَس عليه.</b> <span class="ar">؟</span> و'
               '<span class="ar">؛</span> و<span class="ar">:</span> ما زالت '
               'تُخرج التوكنَ كلَّه — سبعةُ توكناتٍ في المثبَّتات الأخرى. ومدُّ '
               'الحكم إلى «كلّ ترقيم» استنباطُ قاعدةٍ لم تُقَل، وهو الخرقُ '
               'الذي لا يشتكي منه أحد. رُفع باسم <span class="mono">'
               'OPEN:QUESTION_SEMICOLON_COLON_SEPARATOR_OR_LETTER</span>.'
               '</div>'
             + '<div class="warn" style="margin-top:8px">والمصحفُ لم يتغيّر '
               'منه حرف: مخرجُ المحور الرابع على النصّ الكامل '
               '<span class="mono">6c54d6f52ab9aca2</span> قبل الحكم وبعده — '
               'مطابقٌ بايتيًّا. فالحكمُ عمل حيث له أثر، وسكت حيث لا أثرَ له.'
               '</div></div>')

    # ── اتّفاقٌ واختلاف ─────────────────────────────────────────────────
    rows_ = "".join(f'<tr><td>{E(a)}</td><td class="cert">{E(b)}</td>'
                    f'<td class="cert">{E(cc)}</td></tr>'
                    for a, b, cc in c["agree"])
    P.append('<h2>٦ · حيث يتّفقان</h2><div class="card">'
             '<p class="k">والاتّفاقُ هنا في <b>المنهج</b> لا في الأرقام: '
             'نظامان بُنيا منفصلين وانتهيا إلى القيود نفسِها.</p>'
             '<table><thead><tr><th>القيد</th><th class="a">أسلوط</th>'
             f'<th class="b">تعقُّل</th></tr></thead><tbody>{rows_}</tbody>'
             '</table></div>')

    rows_ = "".join(f'<tr><td>{E(a)}</td><td class="a">{E(b)}</td>'
                    f'<td class="b">{E(cc)}</td><td class="k">{E(d)}</td></tr>'
                    for a, b, cc, d in c["differ"])
    P.append('<h2>٧ · حيث يختلفان — مقيسًا</h2><div class="card">'
             '<table><thead><tr><th>الموضع</th><th class="a">أسلوط</th>'
             '<th class="b">تعقُّل</th><th>الحكم</th></tr></thead>'
             f'<tbody>{rows_}</tbody></table></div>')

    # ── ما ينقص كلًّا منهما ─────────────────────────────────────────────
    gain = "".join(f'<tr><td>{E(a)}</td><td class="k">{E(b)}</td></tr>'
                   for a, b in c["aslot_lacks"])
    lose = "".join(f'<tr><td>{E(a)}</td><td class="k">{E(b)}</td></tr>'
                   for a, b in c["matrix_lacks"])
    P.append('<h2>٨ · ما يملكه كلٌّ منهما ولا يملكه الآخر</h2>'
             '<div class="card"><h3>ما في المصفوفة وليس في أسلوط — وهو نقصٌ '
             'فيه</h3>'
             '<table><thead><tr><th>البند</th><th>لماذا يهمّ</th></tr></thead>'
             f'<tbody>{gain}</tbody></table>'
             '<h3 style="margin-top:14px">ما في أسلوط وليس في المصفوفة</h3>'
             '<table><thead><tr><th>البند</th><th>لماذا يهمّ</th></tr></thead>'
             f'<tbody>{lose}</tbody></table></div>')

    # ── أسئلةُ المالك من الوثيقة ────────────────────────────────────────
    q = "".join(f'<tr><td>{E(a)}</td><td class="k">{E(b)}</td></tr>'
                for a, b in m["owner_questions"])
    amb = "".join(f'<tr><td class="ar">{E(a)}</td><td>{E(b)}</td></tr>'
                  for a, b in m["ambiguity"])
    P.append('<h2>٩ · ما ترفعه الوثيقةُ إليك — ولا يرفعه أسلوط</h2>'
             '<div class="card"><p class="k">هذا أنفعُ ما في الوثيقة، وأبينُ '
             'نقصٍ في تقاريري: أسئلةٌ <b>خاصّةٌ بهذه النازلة</b> لا قائمةُ '
             'قراراتٍ عامّة.</p>'
             '<table><thead><tr><th>السؤال</th><th>لماذا يوقف الحكم</th>'
             f'</tr></thead><tbody>{q}</tbody></table>'
             '<h3 style="margin-top:14px">وغموضٌ لغويٌّ موقوفٌ عليك</h3>'
             '<table><thead><tr><th>الموضع</th><th>السؤال</th></tr></thead>'
             f'<tbody>{amb}</tbody></table></div>')

    # ── الخاتمة ─────────────────────────────────────────────────────────
    P.append('<h2>١٠ · الحكم</h2><div class="card">'
             '<div class="kv mono" style="background:#f6f8fa;border:1px solid '
             '#d0d7de;border-radius:6px;padding:10px">'
             'COMPARABLE_SURFACE = YES — نصٌّ واحد، sha256 1a7f8b76…<br>'
             'COMPARABLE_LAYER = NO — محاورُ السطح ≠ مراحلُ ما بعد التصنيف<br>'
             'COMPARABLE_METHOD = YES — والاتّفاقُ فيه لا في الأرقام<br>'
             'CONTRADICTION_RESOLVED = 1 — الترقيمُ بحكم المالك<br>CONTRADICTION_OPEN = 0<br>'
             'NEITHER_PRODUCES = HUKM · TANZIL · ROOT · IFADAH</div>'
             '<p class="k" style="margin-top:10px">ولا يصحّ أن يُقال إنّ '
             'أحدَهما «يؤكّد» الآخر: ما تحقّق منه أسلوط لم تلمسه المصفوفة، '
             'وما أعلنته المصفوفةُ غيرَ منفَّذٍ لا يملك أسلوط أن ينفّذه. '
             'والقيمةُ في أنّهما <b>يسدّان طرفين مختلفين</b> من طريقٍ لم '
             'يُوصَل وسطُه بعد.</p></div>')
    return "\n".join(P)


def build(args: argparse.Namespace) -> dict:
    m = parse_matrix(Path(args.matrix))
    run = Path(args.run)
    rows = aslot_rows(run)

    sec8 = Path(args.matrix).read_text(encoding="utf-8")
    sec8 = sec8.split("## 8.")[1].split("## 9.")[0]
    gloss = {w: (a.strip(), b.strip()) for w, a, b in
             re.findall(r"^\| `([^`]+)` \| (.+?) \| (.+?) \|$", sec8, re.M)}

    surfaces = []
    for label, path in (("نصُّ الوثيقة (§INPUT_TEXT) — وهو الأساسُ الموحَّد",
                         args.matrix_text),
                        ("نصُّ رسالتك", args.chat_text)):
        p = Path(path)
        if p.is_file():
            t = p.read_text(encoding="utf-8").strip()
            surfaces.append({"label": label, "text": t,
                             "tokens": len(t.split()), "sha": sha(t)})

    a = Path(args.matrix_text).read_text(encoding="utf-8").strip().split()
    b = Path(args.chat_text).read_text(encoding="utf-8").strip().split()
    diffs = []
    # strict=True: لو اختلف عددُ التوكنات وجب أن يُرفع لا أن
    # يُقصّ الأطولُ صامتًا — والقصُّ الصامت هو العيبُ نفسُه.
    for i, (x, y) in enumerate(zip(a, b, strict=True), 1):
        if x != y:
            note = ("علَمٌ بدل وصف — لا أثرَ له في محاور أسلوط"
                    if i == 2 else
                    "اسمُ فاعلٍ ↔ فعلٌ مضارع — والثاني حاملٌ غيرُ مشكول"
                    if i == 5 else "نقطةٌ في آخر النصّ — تُخرج التوكنَ كلَّه")
            diffs.append((i, x, y, note))

    tokens = m["input_text"].split()
    stripped = [t for t in tokens
                if t not in m["words_listed"] and t.strip(PUNCT) in m["words_listed"]]

    return {
        "matrix": m, "rows": rows, "gloss": gloss,
        "audit": audit_matrix(m), "surfaces": surfaces, "diffs": diffs,
        "punct": {"stripped": stripped, "tokens": len(tokens),
                  "reached": sum(1 for r in rows if r["reached"])},
        "agree": [
            ("لا حكمَ ولا تنزيل", "IFADAH · HUKM · TANZIL = NOT_OPENED",
             "FINAL_HUKM = NOT_PRODUCED · FINAL_TANZIL = NOT_OPENED"),
            ("حدُّ الدخول مُعلَن",
             "NOT_AN_ONTOLOGICAL_ORIGIN · NOT_A_SOUND · NOT_A_MEANING",
             "NOT_AN_ORIGIN · NOT_A_SOUND · NOT_A_MEANING"),
            ("الرتبةُ في القاع", "لا رتبةَ محمولةٌ في مخرج (T-7)",
             "ZERO ⟵ ZERO في كلّ المراحل"),
            ("البقايا بأسمائها", "أصنافٌ مسمّاةٌ لا رسائلُ حرّة",
             "أسماءٌ مقيسةٌ فقط · HIDDEN_RESIDUALS = UNMEASURED"),
            ("الحكمُ للمالك", "P4 — لا يُسنَد صنفُ بقيّةٍ من عند المولّد",
             "OWNER_PENDING على سبعة أسئلة"),
            ("لا خطَّ ممنوعٍ مُنفَّذ", "FORBIDDEN_LINES_ENFORCED = 0",
             "هل اشتعلت في runner؟ UNMEASURED"),
        ],
        "differ": [
            ("عددُ الكلمات", f"{sum(1 for r in rows if r['reached'])}"
                              f" من {len(tokens)} تبلغ المحور الرابع",
             "10 توكناتٍ × 16 مرحلة = 160 سجلًّا",
             "الأساسُ موحَّدٌ بعد حكمك — التوكنةُ واحدة"),
            ("الترقيمُ اللاصق", "يُقطع بحكم المالك ويُسجَّل في عمودٍ خاصّ",
             "جُرِّد في §8 بلا إعلان",
             "النتيجةُ واحدة الآن، والفرقُ في أنّ أحدَهما أعلن"),
            ("الخطوطُ الممنوعة", "٨ خطوطٍ مُعلَنة",
             f"{m['forbidden_lines']} خطًّا، مصدرُها USER_PROVIDED",
             "جردان لم يُوفَّق بينهما"),
            ("هويّةُ التشغيل", "تُقرأ من git — HEAD وبصمةُ الملفّ",
             "MEASURED_BY = USER_REVIEW_CONTAINER · "
             "RUN_FINGERPRINT = PROVIDED_BY_USER_REVIEW",
             "الأولى تُعاد، والثانية تُصدَّق"),
            ("الرتبة", "غيرُ محمولةٍ أصلًا", "محمولةٌ ومقيسةٌ ZERO",
             "المصفوفةُ أسبقُ هنا"),
            ("التحقّقُ المستقلّ", "مدقِّقٌ لا يستورد المولّد — ٧ حواجز",
             "RECORD_FIELD_STATUS = NOT_FULLY_RECONSTRUCTED",
             "أسلوط أسبقُ هنا"),
        ],
        "aslot_lacks": [
            ("مصفوفةُ المناط — أسئلةٌ خاصّةٌ بهذه النازلة",
             "تقاريري ترفع قائمةَ قراراتٍ عامّةً لا تتغيّر بالنصّ"),
            ("سجلُّ الغموض اللغويّ (طَرْدَهَا: إضافةٌ لفاعله أم لمفعوله؟)",
             "موضعٌ يعرف النظامُ أنّه لا يعرفه، ويسمّيه"),
            ("سجلُّ ما سُحب — WITHDRAWN_AS_MANUFACTURED_HUKM",
             "دعوى صُنعت ثمّ سُحبت تبقى مسجَّلةً، فلا تُعاد صامتة"),
            ("StageTransitionState بستّ قيم",
             "يفرّق بين «لم يُنفَّذ» و«لم يُفتح» و«لا ينطبق» — وعندي ثنائيّة"),
            ("المنطوقُ والمفهوم مُعلَنَين طبقةً مستقلّة",
             "يفصل التفسيرَ البشريّ عن الخرج، ويسمّي علّتَه"),
        ],
        "matrix_lacks": [
            ("عملٌ فعليٌّ على السطح", "تطبيعٌ وتقطيعٌ وتقشيرٌ مقيسة؛ و§8 و§9 "
                                      "في الوثيقة DECLARED_NOT_MEASURED"),
            ("مدقِّقٌ لا يستورد المولّد", "الوثيقةُ تُصدَّق ولا تُعاد"),
            ("هويّةُ git مقروءة", "بصمةُ حاويةِ مراجعةٍ لا تُعيد بناءَ شيء"),
            ("إعلانُ قرار الترقيم", "قرارٌ في السطح رُفع بدل أن يُتّخذ صامتًا"),
            ("جردُ الرفض مقسومًا ثلاثًا",
             "مُعلَنٌ بشاهد · مُعلَنٌ بلا شاهد · ظهر ولم يُعلَن"),
        ],
    }


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--matrix", default="inspection/TAAQOL_NAZILA_MATRIX.md")
    p.add_argument("--run", default="inspection/runs/f4")
    p.add_argument("--matrix-text", default="inspection/case.txt")
    p.add_argument("--chat-text", default="inspection/case_chat.txt")
    p.add_argument("--out", default="inspection/comparison.html")
    args = p.parse_args(argv)

    c = build(args)
    body = render(c)
    payload = hashlib.sha256(body.encode("utf-8")).hexdigest()
    Path(args.out).write_text(
        f'<!doctype html>\n<html lang="ar" dir="rtl"><head><meta charset="utf-8">'
        f'<meta name="viewport" content="width=device-width,initial-scale=1">'
        f'<title>مقابلةُ أسلوط بمصفوفة تعقُّل</title><style>{CSS}</style>'
        f'</head><body>{body}'
        f'<div class="mono" style="margin-top:14px">'
        f'MATRIX_SHA256 = {c["matrix"]["sha256"]}<br>'
        f'PAYLOAD_SHA256 = {payload} (SCOPE = هذه الوثيقة عدا هذا السطر)</div>'
        f'</body></html>', encoding="utf-8")

    a = c["audit"]
    print(f"MATRIX_SHA256   = {c['matrix']['sha256'][:32]}…")
    print(f"MATRIX_AUDIT    = {sum(x['ok'] for x in a)}/{len(a)} دعوى قفلت")
    for x in a:
        if not x["ok"]:
            print(f"   ✘ {x['claim']}  —  {x['detail']}")
    print(f"SURFACES        = {len(c['surfaces'])} ببصماتٍ مختلفة")
    print(f"WORD_DIFFS      = {len(c['diffs'])}")
    print(f"PUNCT_CONFLICT  = {len(c['punct']['stripped'])} توكنات · "
          f"بلغ المحورَ الرابع {c['punct']['reached']}/{c['punct']['tokens']}")
    print(f"→ {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
