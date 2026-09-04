#!/usr/bin/env python3
"""مخرجاتُ نتيجة تعقُّل على النازلة — جدولان وصفحةٌ وعلامة.

    .venv-taaqol/bin/python scripts/build_nazila_outputs.py \\
        --text inspection/case.txt \\
        --reference inspection/TAAQOL_NAZILA_MATRIX.md \\
        --out output/nazila_result

**لماذا ملفٌّ ثانٍ.** المصفوفةُ خرجت `.md`، والعلامةُ التي طُبعت آخِرَ مرّةٍ
(`٥٢٪`) كانت **علامةَ دفتر الإصلاح لا علامةَ النازلة** — مقامُها خمسةٌ
وعشرون بندًا، ومقامُ النازلة خاناتُها. وعرضُ علامةٍ على غير مقامها هو
الرقمُ الواحدُ بمقامين نفسُه، فيُفصلان هنا فصلًا لا يُلبَس.

**والقياسُ واحدٌ لا يتكرّر.** يُستورد `build_nazila_matrix` ويُشغَّل، فلا
تُعاد كتابةُ سطرِ قياسٍ واحد. ومولّدان يقيسان الشيءَ نفسَه يفترقان يومًا.

**والأعمدةُ لا تُحذف لفراغها.** أربعةٌ وعشرون حقلًا لـ`StageExecutionRecord`
تُطبع كلُّها بأسمائها؛ والفارغُ يُكتب `EMPTY_IN_RECORD` لا شرطةً ولا خانةً
بيضاء — فالفراغُ المقيس خبرٌ، وحذفُ عمودٍ لأنّه فارغ يُخفي أنّ المشغّلَ
أصدر السجلَّ ولم يضع فيه شيئًا.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import html
import importlib.util
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
sys.path.insert(0, str(VENDOR / "src"))

PIN = "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095"
EMPTY = "EMPTY_IN_RECORD"

STAGES = ("PATH_CLASSIFICATION", "PRE_WEIGHT_CAPACITY_AUDIT", "DAL_ONLY",
          "VERBAL_MADLUL", "DAL_MADLUL_BINDING", "CONTRACTABLE_UNIT",
          "RELATION", "FORMAL_SHAPE", "MUFRAD_DALALAH", "RELATION_CLOSURE",
          "IFADAH", "HUKM", "MANAT", "TANZIL", "ANSWER_AUDIT",
          "NON_CONTENT_FORMAL_ROUTE")


def load_matrix_module():
    """يستورد المولّدَ نفسَه — مصدرُ القياس واحد، ولا يُنسخ."""
    spec = importlib.util.spec_from_file_location(
        "bnm", ROOT / "scripts" / "build_nazila_matrix.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["bnm"] = mod
    spec.loader.exec_module(mod)
    return mod


# ── الجداول ────────────────────────────────────────────────────────────
def write_records_csv(path: Path, flat: list[dict], fields: list[str]) -> dict:
    """`records.csv` — كلُّ سجلٍّ بكلّ حقوله. ولا عمودَ يُحذف لأنّه فارغ."""
    empties: Counter = Counter()
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(fields)
        for r in flat:
            row = []
            for f in fields:
                v = r.get(f)
                if v is None or v == [] or v == "":
                    empties[f] += 1
                    row.append(EMPTY)
                elif isinstance(v, (list, tuple)):
                    row.append(" · ".join(str(x) for x in v))
                else:
                    row.append(str(v))
            w.writerow(row)
    return {"rows": len(flat), "columns": len(fields),
            "columns_entirely_empty": sorted(
                f for f in fields if empties[f] == len(flat)),
            "empty_cells_by_column": dict(sorted(empties.items()))}


def write_cells_csv(path: Path, cells) -> dict:
    """`cells.csv` — كلُّ خانةٍ بوسم مصدرها. والحالُ عمودٌ لا يُستنتج."""
    with path.open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["section", "field", "status", "value", "source",
                    "reason", "reason_family"])
        for c in cells:
            w.writerow([c.section, c.field,
                        "FROM_CODE" if c.from_code else "NOT_AVAILABLE",
                        "" if c.reason else render_value(c.value),
                        c.source if c.from_code else "",
                        c.reason, c.reason.split(":")[0] if c.reason else ""])
    return {"rows": len(cells)}


def render_value(v) -> str:
    if isinstance(v, (list, tuple)):
        return " · ".join(str(x) for x in v) if v else EMPTY
    return "" if v is None else str(v)


DATA_ROW = re.compile(r'data-section="([^"]*)" data-field="([^"]*)"')


def html_csv_disagreement(page: str, cells) -> list[str]:
    """`G5` — كلُّ خانةٍ في `cells.csv` لها نظيرٌ في الصفحة، بالزوج لا بالنصّ.

    والمقابلةُ بورود الاسم في النصّ تُخطئ في الجهتين: سهمٌ مختلفٌ يُسقط
    خانةً موجودة، واسمٌ في شرحٍ يُمرّر خانةً غائبة. فتُقرأ الأزواجُ من
    `data-section`/`data-field` — ولا يكتبها إلا صفُّ خانةٍ حقيقيّ.
    """
    in_page = {(html.unescape(a), html.unescape(b))
               for a, b in DATA_ROW.findall(page)}
    return sorted(f"{c.section}/{c.field}" for c in cells
                  if (c.section, c.field) not in in_page)


# ── العلامة — ح-٢ · وثلاثةُ أعدادٍ معًا وبمقاماتها ─────────────────────
def gates(cells, recount_ok: bool, missing_in_page: list[str] | None = None) -> dict:
    head = subprocess.run(["git", "-C", str(VENDOR), "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=False)
    st = subprocess.run(["git", "-C", str(VENDOR), "status", "--porcelain"],
                        capture_output=True, text=True, check=False)
    decided = [c.field for c in cells
               if c.reason == "OWNER_DECISION" and c.value is not None]
    broken = [f"{c.section}/{c.field}" for c in cells
              if not c.reason and (c.value is None or c.value == "")]
    return {
        "G1_REPRODUCIBLE": (head.stdout.strip() == PIN
                            and not st.stdout.strip()),
        "G2_LEDGER_CLOSES": recount_ok,
        "G3_NO_BROKEN": not broken,
        "G4_NO_OWNER_INFERENCE": not decided,
        "G5_HTML_CSV_AGREE": not missing_in_page,
        "_vendor_head": head.stdout.strip(),
        "_missing_in_page": list(missing_in_page or [])[:20],
        "_missing_in_page_count": len(missing_in_page or []),
        "_porcelain_lines": len(st.stdout.split()) // 2,
        "_broken": broken, "_owner_cells_decided": decided,
    }


def score(cells, g: dict, previous: dict | None) -> dict:
    """`GROUNDED / NAMED / BROKEN` — والعلامةُ لا تُطبع وحدَها أبدًا."""
    grounded = sum(1 for c in cells if c.from_code)
    broken = len(g["_broken"])
    named = len(cells) - grounded - broken
    pot = round(100 * grounded / len(cells), 1)
    passed = all(v for k, v in g.items() if not k.startswith("_"))
    by_reason = dict(sorted(Counter(c.reason for c in cells if c.reason).items()))
    moved = {}
    if previous:
        prev = previous.get("not_available_by_reason", {})
        for k in sorted(set(prev) | set(by_reason)):
            a, b = prev.get(k, 0), by_reason.get(k, 0)
            if a != b:
                moved[k] = {"previous_round": a, "this_round": b}
    return {
        "GROUNDED": grounded, "NAMED": named, "BROKEN": broken,
        "CELLS_TOTAL": len(cells),
        "CLOSURE_POTENTIAL": pot,
        "CLOSURE_EFFECTIVE": pot if passed else 0,
        "failed_gates": [k for k, v in g.items()
                         if not k.startswith("_") and not v],
        "gates": {k: v for k, v in g.items() if not k.startswith("_")},
        "STAGES_OPENED": "1/16",
        "not_available_by_reason": by_reason,
        # ح-٥ · نقلُ بندٍ بين أسر الأسباب يرفع العلامةَ بلا عمل، فيُقابَل
        # بالجولة السابقة ويُعلَن. وخلوُّ هذا الحقل خبرٌ كامتلائه.
        "reason_family_moves_vs_previous_round": moved,
        "denominator_note":
            "المقامُ خاناتُ هذه الوثيقة وحدَها. وعلامةُ دفتر الإصلاح "
            "(output/remediation) مقامُها بنودُه، ولا تُجمع بهذه.",
    }


# ── الصفحة ─────────────────────────────────────────────────────────────
def esc(x) -> str:
    return html.escape(str(x))


VOLATILE_FIELDS = ("utc_timestamp",)


def content_fingerprint(out: Path) -> dict:
    """بصمتان: الجدولُ الثابتُ كلُّه، والخاناتُ بلا الحقل المتغيّر بطبيعته."""
    rec = hashlib.sha256((out / "records.csv").read_bytes()).hexdigest()
    with (out / "cells.csv").open(encoding="utf-8", newline="") as fh:
        rows = [r for r in csv.reader(fh) if r[1] not in VOLATILE_FIELDS]
    cel = hashlib.sha256(repr(rows).encode()).hexdigest()
    return {"records_csv_sha256": rec,
            "cells_csv_sha256_excluding": cel,
            "excluded_fields": list(VOLATILE_FIELDS),
            "note": "records.csv مطابقٌ بايتةً بايتة بين تشغيلَين. "
                    "و cells.csv يختلف في utc_timestamp وحدَها، وهي مقيسةٌ "
                    "لا عشوائيّة، فتُستثنى بالاسم لا بالصمت."}


def one_of(flat: list[dict], field: str) -> str:
    """قيمةُ حقلٍ ثابتةٍ عبر السجلّات — ويُعلَن التعدّدُ إن وقع، ولا يُختار."""
    seen = sorted({str(r.get(field)) for r in flat})
    return seen[0] if len(seen) == 1 else f"MULTIPLE:{len(seen)} · {seen}"


def matrix_16x10(flat: list[dict], tokens: list[dict]) -> str:
    """المصفوفةُ كاملةً: ستَّ عشرةَ مرحلةً × عشرةَ توكنات، بلا اختصار."""
    by = {(r["token_id"], r["stage_id"]): r for r in flat}
    head = "".join(f'<th><span dir="rtl">{esc(t["surface"])}</span><br>'
                   f'<small>{esc(t["token_id"])}</small></th>' for t in tokens)
    rows = []
    for n, stage in enumerate(STAGES, 1):
        tds = []
        for t in tokens:
            r = by.get((t["token_id"], stage))
            s = r["transition_state"] if r else EMPTY
            tds.append(f'<td class="s-{esc(s)}">{esc(s)}</td>')
        rows.append(f'<tr><th class="stage">{n}. {esc(stage)}</th>'
                    f'{"".join(tds)}</tr>')
    return (f'<table class="matrix"><thead><tr><th>المرحلة</th>{head}</tr>'
            f'</thead><tbody>{"".join(rows)}</tbody></table>')


def kv_table(pairs) -> str:
    rows = "".join(
        f'<tr><th>{esc(k)}</th><td>{esc(v)}</td></tr>' for k, v in pairs)
    return f'<table class="kv"><tbody>{rows}</tbody></table>'


def count_table(counter: dict, total: int, label: str) -> str:
    if not counter:
        return f'<p class="empty">{EMPTY} — لم يُصدر المشغّلُ شيئًا لهذا الحقل.</p>'
    rows = "".join(f'<tr><th>{esc(k)}</th><td>{v}/{total}</td></tr>'
                   for k, v in sorted(counter.items()))
    return (f'<table class="kv"><thead><tr><th>{esc(label)}</th>'
            f'<th>العدد/المقام</th></tr></thead><tbody>{rows}</tbody></table>')


CSS = """
:root{--bg:#fbfaf8;--fg:#1c1a17;--mut:#6b655c;--line:#ddd8d0;--card:#fff;
--ok:#1f6f43;--warn:#8a5a12;--off:#8b8378;--accent:#2f4f7f}
:root:not([data-theme=light]) @media (prefers-color-scheme:dark){}
@media (prefers-color-scheme:dark){:root:not([data-theme=light]){
--bg:#15140f;--fg:#ece7dd;--mut:#9d968a;--line:#332f28;--card:#1d1b16;
--ok:#6cc48d;--warn:#d8a44a;--off:#8b8378;--accent:#8fb3e8}}
:root[data-theme=dark]{--bg:#15140f;--fg:#ece7dd;--mut:#9d968a;--line:#332f28;
--card:#1d1b16;--ok:#6cc48d;--warn:#d8a44a;--off:#8b8378;--accent:#8fb3e8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--fg);direction:rtl;
font:15px/1.65 "Segoe UI",Tahoma,system-ui,sans-serif}
.wrap{max-width:1180px;margin:0 auto;padding:32px 20px 64px}
h1{font-size:1.6rem;margin:0 0 4px;letter-spacing:-.01em}
h2{font-size:1.05rem;margin:38px 0 10px;padding-bottom:6px;
border-bottom:2px solid var(--line)}
.sub{color:var(--mut);margin:0 0 22px;font-size:.92rem}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:14px 16px;margin:12px 0}
.scores{display:flex;flex-wrap:wrap;gap:12px;margin:14px 0}
.score{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:12px 18px;min-width:150px}
.score b{display:block;font-size:1.9rem;line-height:1.1;font-variant-numeric:tabular-nums}
.score span{color:var(--mut);font-size:.8rem}
.scroll{overflow-x:auto;border:1px solid var(--line);border-radius:10px;
background:var(--card)}
table{border-collapse:collapse;width:100%;font-size:.86rem}
th,td{border:1px solid var(--line);padding:6px 9px;text-align:right;
vertical-align:top}
thead th{background:rgba(128,128,128,.10);font-weight:600;white-space:nowrap}
.kv th{width:44%;font-weight:600;color:var(--mut)}
.matrix{font-size:.74rem;font-family:ui-monospace,Menlo,Consolas,monospace}
.matrix th.stage{white-space:nowrap;text-align:right;font-family:inherit}
.matrix td{text-align:center;white-space:nowrap}
.s-EXECUTED{color:var(--ok);font-weight:700}
.s-DEFERRED,.s-DECLARED_NOT_IMPLEMENTED{color:var(--warn)}
.s-NOT_OPENED,.s-NOT_APPLICABLE{color:var(--off)}
code,.mono{font-family:ui-monospace,Menlo,Consolas,monospace;font-size:.88em}
pre{background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:14px;overflow-x:auto;direction:ltr;text-align:left;font-size:.82rem}
.empty{color:var(--mut);font-style:italic}
.gate-ok{color:var(--ok);font-weight:700}
.gate-no{color:#b4433a;font-weight:700}
.note{border-inline-start:3px solid var(--accent);padding:2px 12px;
color:var(--mut);margin:10px 0}
"""


def build_html(ctx: dict) -> str:
    m, s, sc, g = ctx["m"], ctx["src"], ctx["score"], ctx["gates"]
    flat, tokens, cells = m["flat"], m["tokens"], ctx["cells"]
    n = len(flat)
    states = Counter(r["transition_state"] for r in flat)
    hints = Counter(h for r in flat for h in (r.get("remediation_hints") or []))
    resid = Counter(x for r in flat for x in (r.get("residuals_after") or []))
    ranks = Counter(f'{r["rank_before"]}->{r["rank_after"]}' for r in flat)

    def sec(no, title, body):
        return f"<h2>{no}. {esc(title)}</h2>\n{body}"

    P = [f'<title>نتيجة تعقُّل على النازلة</title><style>{CSS}</style>',
         '<div class="wrap">',
         '<h1>نتيجةُ تعقُّل على النازلة</h1>',
         f'<p class="sub">محتوًى من الكود وحدَه · '
         f'{esc(ctx["utc"])} · CLAIM_PROJECT_FINISHED = NO</p>']

    # ١ · حدُّ الدخول أوّلًا — وهو الذي يمنع قراءةَ المصفوفة تحليلًا
    P.append(sec(1, "حدُّ الدخول المعلَن — يُقرأ قبل كلّ ما بعده",
                 entry_boundary_block(cells)))

    # ٢
    P.append(sec(2, "الهُويّة والبصمة", kv_table([
        ("INPUT_TEXT", ctx["text"]),
        ("INPUT_SHA256", ctx["sha"]),
        ("VENDOR_HEAD", g["_vendor_head"]),
        ("VENDOR_PIN", PIN),
        ("VENDOR_PORCELAIN_LINES", g["_porcelain_lines"]),
        ("RUN_ID", m["run"].get("run_id")),
        ("CORPUS_ID", ctx["corpus_id"]),
        ("PYTHON", platform.python_version()),
        ("PLATFORM", f"{platform.system()} {platform.machine()}"),
        ("TOKENS", len(tokens)),
        ("RECORDS", f'{n} = {len(tokens)} × {len(STAGES)}'),
        ("source_commit_sha (من السجلّ)", one_of(flat, "source_commit_sha")),
        ("registry_version (من السجلّ)", one_of(flat, "registry_version")),
        ("registry_hash (من السجلّ)", one_of(flat, "registry_hash")),
    ]) + '<p class="note">المشغّلُ لا يعرف التزامَه: يكتب '
         '<code>UNKNOWN_COMMIT_SHA</code> في السجلّات كلِّها. فالتثبيتُ الذي '
         'يقوم عليه <code>MATCH</code> <b>خارجيٌّ</b> — '
         '<code>git rev-parse</code> وبصماتُ الحوامل الستّ — لا إقرارٌ من '
         'المشغّل بنفسه. وبصمةُ السجلّ (<code>registry_hash</code>) تُثبت '
         'جردَه لا إصدارَه.</p>'))

    # ٢
    gl = "".join(
        f'<tr><th>{esc(k)}</th><td class="{"gate-ok" if v else "gate-no"}">'
        f'{v}</td></tr>'
        for k, v in sc["gates"].items())
    P.append(sec(3, "البوّابات والعلامة",
                 f'<div class="scores">'
                 f'<div class="score"><b>{sc["CLOSURE_EFFECTIVE"]}%</b>'
                 f'<span>CLOSURE_EFFECTIVE</span></div>'
                 f'<div class="score"><b>{sc["CLOSURE_POTENTIAL"]}%</b>'
                 f'<span>CLOSURE_POTENTIAL</span></div>'
                 f'<div class="score"><b>{sc["GROUNDED"]}<small>/'
                 f'{sc["CELLS_TOTAL"]}</small></b><span>GROUNDED</span></div>'
                 f'<div class="score"><b>{sc["NAMED"]}<small>/'
                 f'{sc["CELLS_TOTAL"]}</small></b><span>NAMED</span></div>'
                 f'<div class="score"><b>{sc["BROKEN"]}</b>'
                 f'<span>BROKEN</span></div>'
                 f'<div class="score"><b>1<small>/16</small></b>'
                 f'<span>STAGES_OPENED</span></div></div>'
                 f'<table class="kv"><tbody>{gl}</tbody></table>'
                 f'<p class="note">{esc(sc["denominator_note"])}</p>'
                 f'<p class="note">المئةُ لا تُبلَغ اليوم: يلزمها فتحُ '
                 f'PRE_WEIGHT_CAPACITY_AUDIT، وهي خارج الولاية.</p>'))

    # ٣
    rows = "".join(
        f'<tr><td class="mono">{esc(t["token_id"])}</td>'
        f'<td>{esc(t["surface"])}</td><td class="mono">{esc(t["path"])}</td>'
        f'<td class="mono">{esc(t["confidence"])}</td></tr>' for t in tokens)
    P.append(sec(4, "النصّ وتوكناتُه",
                 f'<div class="scroll"><table><thead><tr><th>المعرِّف</th>'
                 f'<th>اللفظ</th><th>path_id</th><th>confidence</th></tr>'
                 f'</thead><tbody>{rows}</tbody></table></div>'
                 f'<p class="note">الفاصلةُ والنقطة ملتصقتان بالتوكن: '
                 f'مشغّلُ تعقُّل لا يقطع الفواصل، وحكمُك في القطع محلُّه '
                 f'أسلوط. وهذا فرقٌ مقيس، لا عيبٌ يُصلَح هنا.</p>'))

    # ٤
    P.append(sec(5, "المصفوفة ١٦×١٠ كاملةً",
                 f'<div class="scroll">{matrix_16x10(flat, tokens)}</div>'
                 f'<p class="note">لا خليّةَ محذوفة: ستَّ عشرةَ مرحلةً في '
                 f'عشرةِ توكنات = {n} خليّة، وهي عددُ السجلّات نفسُه.</p>'))

    # ٥–٧
    P.append(sec(6, "حالاتُ الانتقال بمقاماتها",
                 count_table(states, n, "StageTransitionState")))
    P.append(sec(7, "البقايا والتلميحات",
                 count_table(resid, n, "residuals_after")
                 + count_table(hints, n, "remediation_hints")))
    P.append(sec(8, "الرتب",
                 count_table(ranks, n, "rank_before -> rank_after")
                 + '<p class="note">الرتبةُ اسمٌ لا رقم: القيمةُ العدديّة '
                   'لا تُسمّي، فتُؤخذ <code>.name</code>.</p>'))

    # ٨
    P.append(sec(9, "الجرد المغلق المستعمل", kv_table([
        ("Rank", " · ".join(s["Rank"])),
        ("ClosureState", " · ".join(s["ClosureState"])),
        ("TransitionState", " · ".join(s["TransitionState"])),
        ("StageTransitionState", " · ".join(s["StageTransitionState"])),
        ("FailureCode (الجرد كلُّه)", s["FailureCode_total"]),
    ])))

    # ٩
    rules = "".join(f'<tr><th>{esc(a)}</th><td>{esc(b)}</td></tr>'
                    for a, b in s["rules"])
    P.append(sec(10, "شكلُ سجلّ التنفيذ وقواعدُه",
                 kv_table([("حقولُ StageExecutionRecord",
                            f'{len(s["record_fields"])} حقلًا'),
                           ("الأعمدةُ الفارغةُ كلَّها",
                            " · ".join(ctx["records_meta"]
                                       ["columns_entirely_empty"]) or "—")])
                 + f'<table class="kv"><tbody>{rules}</tbody></table>'
                 + '<p class="note">القواعدُ المعلَّقة في المصدر مرقَّمةٌ '
                   '١ و٣ و٤ و٦ و٧ و٨ و٩ — وفي الترقيم ثغرتان عند ٢ و٥، '
                   'تُعدّ ولا تُملأ.</p>'))

    # ١٠
    fl = "".join(f'<tr><td class="mono">{esc(x["source"])} → '
                 f'{esc(x["target"])}</td><td class="mono">'
                 f'{esc(x["required_bridge"])}</td></tr>'
                 for x in s["forbidden_lines"])
    pairs = [(x["source"], x["target"]) for x in s["forbidden_lines"]]
    P.append(sec(11, "الخطوطُ المستقيمة الممنوعة",
                 f'<div class="card">الخطوط <b>{len(pairs)}</b> · '
                 f'الأزواجُ المتمايزة <b>{len(set(pairs))}</b> — '
                 f'فالزوجُ (مصدر ⟶ هدف) لا يُعرِّف خطًّا.</div>'
                 f'<div class="scroll"><table><thead><tr><th>الخطّ</th>'
                 f'<th>الجسرُ اللازم</th></tr></thead><tbody>{fl}</tbody>'
                 f'</table></div>'))

    # ١١
    nr = "".join(f'<tr><th class="mono">{esc(k)}</th><td>{v}</td></tr>'
                 for k, v in sc["not_available_by_reason"].items())
    moves = sc["reason_family_moves_vs_previous_round"]
    mv = ("<p class='empty'>لا انتقالَ بين أسر الأسباب عن الجولة السابقة.</p>"
          if not moves else
          "<table class='kv'><tbody>" + "".join(
              f'<tr><th class="mono">{esc(k)}</th><td>{v["previous_round"]} '
              f'⟶ {v["this_round"]}</td></tr>'
              for k, v in moves.items()) + "</tbody></table>")
    P.append(sec(12, "ما ليس متوفّرًا، وسببُه",
                 f'<table class="kv"><thead><tr><th>السبب</th><th>خانات</th>'
                 f'</tr></thead><tbody>{nr}</tbody></table>' + mv
                 + '<p class="note">نقلُ خانةٍ بين أسر الأسباب يضيّق المقام '
                   'ويرفع العلامةَ بلا عمل، فيُقابَل بالجولة السابقة ويُعلَن.'
                   '</p>'))

    # ١٢
    owner = [c for c in cells if c.reason in ("OWNER_DECISION",
                                              "HUMAN_DECLARED_ONLY")]
    ow = "".join(f'<tr><td>{esc(c.section)}</td>'
                 f'<td class="mono">{esc(c.field)}</td>'
                 f'<td class="mono">{esc(c.reason)}</td></tr>' for c in owner)
    P.append(sec(13, "الموقوفُ على المالك",
                 f'<div class="scroll"><table><thead><tr><th>الفصل</th>'
                 f'<th>الخانة</th><th>السبب</th></tr></thead><tbody>{ow}'
                 f'</tbody></table></div>'
                 f'<p class="note">{len(owner)} خانةً لا تُملأ من الكود بحال: '
                 f'ملؤها ادّعاءٌ لا قياس.</p>'))

    # ١٤ · الدفترُ كاملًا — وهو ما يجعل `G5` بنيويًّا لا نصّيًّا.
    # وقبل هذا الفصل كانت الصفحةُ ملخّصًا: 247 خانةً من 292 بلا نظيرٍ فيها،
    # فبدت وثيقةً مكتملةً وهي تعرض سُدسَ دفترها. والقياسُ سمّى العددَ، ولم
    # يُقبل التقديرُ الذي جاء في الأمر (سبعُ خانات).
    P.append(sec(14, "الدفترُ كاملًا — الخاناتُ الاثنتان وتسعون ومئتان",
                 ledger_block(cells)))

    P.append('</div>')
    return "\n".join(P)


def entry_boundary_block(cells) -> str:
    """فصلُ حدّ الدخول — ويُقرأ قبل المصفوفة، وإلا قُرئت المصفوفةُ تحليلًا.

    وسبعُ خاناته كلُّها `NOT_CONSTRUCTED_IN_SOURCE`: `EntryBoundary` معرَّفةٌ
    في `core.slot_graph` ولا يستوردها المشغّل، فلا يُنشئ حدَّ دخولٍ أصلًا.
    ومعنى ذلك أنّ ما تحت هذا الفصل **ليس تحليلًا ناقصًا، بل ليس تحليلًا**:
    شكلٌ منفَّذٌ مرحلةً واحدة، لا دخولَ مُعلَنًا له.
    """
    rows = [c for c in cells if c.section.startswith("0.")]
    body = "".join(
        f'<tr data-section="{esc(c.section)}" data-field="{esc(c.field)}">'
        f'<th class="mono">{esc(c.field)}</th>'
        f'<td class="mono">{esc(c.reason or render_value(c.value))}</td></tr>'
        for c in rows)
    return (f'<table class="kv"><thead><tr><th>الخانة</th><th>الحال</th></tr>'
            f'</thead><tbody>{body}</tbody></table>'
            f'<p class="note">{len(rows)} خاناتٍ، ولا واحدةَ منها مُنشأة. '
            f'<code>EntryBoundary</code> معرَّفةٌ في <code>core.slot_graph</code> '
            f'ولا يستوردها <code>corpus_runner</code> — فلا حدَّ دخولٍ يُعلَن. '
            f'وما بعد هذا الفصل يُقرأ على ذلك: شكلٌ مقيس، لا تحليل.</p>')


def ledger_block(cells) -> str:
    """كلُّ خانةٍ بنفسها. و`data-field` تجعل المقابلةَ بنيويّةً لا نصّيّة.

    فمقابلةٌ بورود الاسم في النصّ تُخطئ في الجهتين: تمرّ على سهمٍ مختلفٍ
    (`->` مقابل `→`)، وتمرّ كذلك لو ورد الاسمُ في شرحٍ لا في خانة.
    """
    out = []
    for section in dict.fromkeys(c.section for c in cells):
        rows = [c for c in cells if c.section == section]
        body = "".join(
            f'<tr data-section="{esc(c.section)}" data-field="{esc(c.field)}">'
            f'<td class="mono">{esc(c.field)}</td>'
            f'<td>{"FROM_CODE" if c.from_code else "NOT_AVAILABLE"}</td>'
            f'<td>{esc(render_value(c.value)) if c.from_code else ""}</td>'
            f'<td class="mono">{esc(c.source if c.from_code else c.reason)}</td>'
            f'</tr>' for c in rows)
        filled = sum(1 for c in rows if c.from_code)
        out.append(
            f'<h3>{esc(section)} <small>— من الكود {filled} · '
            f'غير متوفرة {len(rows) - filled}</small></h3>'
            f'<div class="scroll"><table><thead><tr><th>الخانة</th>'
            f'<th>الحال</th><th>القيمة</th><th>المصدر / السبب</th></tr>'
            f'</thead><tbody>{body}</tbody></table></div>')
    return "".join(out)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text", default="inspection/case.txt")
    ap.add_argument("--reference",
                    default="inspection/TAAQOL_NAZILA_MATRIX.md")
    ap.add_argument("--corpus-id", default="nazila")
    ap.add_argument("--out", default="output/nazila_result")
    ap.add_argument("--previous",
                    default="output/nazila_from_code/02_field_manifest.json")
    a = ap.parse_args()

    bnm = load_matrix_module()
    pre = bnm.preflight()
    if pre["verdict"] == "BLOCKED":
        print(f"BLOCKED_AT_PREFLIGHT: {json.dumps(pre, ensure_ascii=False)}")
        return 2

    text = Path(a.text).read_text(encoding="utf-8").strip()
    sha = hashlib.sha256(text.encode()).hexdigest()
    m = bnm.measure(text, a.corpus_id)
    src = bnm.source_facts()
    cells = bnm.build_cells(text, sha, a.corpus_id, m, src, pre)

    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    fields = list(src["record_fields"])
    rmeta = write_records_csv(out / "records.csv", m["flat"], fields)
    cmeta = write_cells_csv(out / "cells.csv", cells)

    # الإقفالُ يُقاس بعدٍّ ثانٍ من الملفَّين المكتوبَين، لا من الذاكرة.
    with (out / "records.csv").open(encoding="utf-8", newline="") as fh:
        rrows = list(csv.reader(fh))
    with (out / "cells.csv").open(encoding="utf-8", newline="") as fh:
        crows = list(csv.DictReader(fh))
    closes = (len(rrows) - 1 == len(m["flat"])
              and len(rrows[0]) == len(fields)
              and len(crows) == len(cells)
              and sum(1 for r in crows if r["status"] == "FROM_CODE")
              + sum(1 for r in crows if r["status"] == "NOT_AVAILABLE")
              == len(cells))

    prev = (json.loads(Path(a.previous).read_text(encoding="utf-8"))
            if Path(a.previous).is_file() else None)
    utc = datetime.now(timezone.utc).isoformat(timespec="seconds")

    # تُبنى الصفحةُ مرّتين: الأولى ليُقاس `G5` منها، والثانية لتحمل نتيجتَه.
    # فبوّابةٌ تُقاس من مخرَجٍ لم يُكتب بعدُ دعوى، لا قياس.
    def page_with(g, sc):
        return build_html({"m": m, "src": src, "cells": cells, "score": sc,
                           "gates": g, "text": text, "sha": sha,
                           "corpus_id": a.corpus_id, "records_meta": rmeta,
                           "utc": utc})

    g0 = gates(cells, closes, [])
    draft = page_with(g0, score(cells, g0, prev))
    missing = html_csv_disagreement(draft, cells)

    g = gates(cells, closes, missing)
    sc = score(cells, g, prev)
    page = page_with(g, sc)
    # ويُقاس ثالثةً على المكتوب فعلًا: الفصلُ الأخير لا يتغيّر بتغيّر البوّابة،
    # وإثباتُ ذلك أصدقُ من افتراضه.
    final_missing = html_csv_disagreement(page, cells)
    if final_missing != missing:
        print(f"OWNER_ALERT: G5_UNSTABLE — {len(missing)} ⟶ "
              f"{len(final_missing)}؛ الصفحةُ تتغيّر بتغيّر البوّابة")
        return 5
    (out / "nazila_result.html").write_text(page, encoding="utf-8")

    # بصمةُ محتوًى تُستثنى منها الخانةُ الوحيدةُ المتغيّرةُ بطبيعتها.
    # فـ`records.csv` مطابقٌ بايتةً بايتة بين تشغيلَين، و`cells.csv` يختلف
    # في `utc_timestamp` وحدَها — وهي مقيسةٌ لا عشوائيّة. وإعلانُ البصمتين
    # يجعل «يُعاد إنتاجُه» رقمًا يُقابَل، لا دعوى تُقال.
    scores = {**sc, "html_csv_missing": missing,
              "content_fingerprint": content_fingerprint(out),
              "recount_from_written_files": {
        "records_csv_rows": len(rrows) - 1,
        "records_csv_columns": len(rrows[0]),
        "cells_csv_rows": len(crows),
        "closes": closes},
        "records": rmeta, "cells": cmeta,
        "input_sha256": sha, "vendor_head": g["_vendor_head"]}
    (out / "scores.json").write_text(
        json.dumps(scores, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f'RECORDS   {rmeta["rows"]} صفًّا × {rmeta["columns"]} عمودًا')
    print(f'  أعمدةٌ فارغةٌ كلَّها: '
          f'{rmeta["columns_entirely_empty"] or "لا شيء"}')
    print(f'CELLS     {cmeta["rows"]} صفًّا')
    print(f'LEDGER    يقفل {closes}')
    for k, v in sc["gates"].items():
        print(f"  {k:24} {v}")
    print(f'CLOSURE_EFFECTIVE {sc["CLOSURE_EFFECTIVE"]}%  ·  '
          f'CLOSURE_POTENTIAL {sc["CLOSURE_POTENTIAL"]}%')
    print(f'GROUNDED {sc["GROUNDED"]} · NAMED {sc["NAMED"]} · '
          f'BROKEN {sc["BROKEN"]} · المقام {sc["CELLS_TOTAL"]}')
    print(f"→ {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
