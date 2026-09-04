#!/usr/bin/env python3
"""`MAX_EXECUTABLE` — جامعُ الجولة: التحريراتُ الأربع، وجهوزيّةُ ما بعد `B2`.

    .venv-taaqol/bin/python scripts/build_max.py --device "$(cat data/device_facts.json)"

يقرأ ما كُتب بالقياس ولا يعيد قياسَه من الذاكرة: مخرَجاتُ النازلة، وظلُّ
الخطوط الممنوعة، وظلُّ البوّابة، وقياساتُ `B2`، وأثرُ الإسناد. ويطبع رأسَ
النازلة **في الصدر**، لا في الذيل.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VENDOR = ROOT / "vendor" / "Taaqol-GPT"
sys.path.insert(0, str(VENDOR / "src"))

AXES = tuple(sorted(str(p.relative_to(ROOT))
                    for p in (ROOT / "reports").glob("axis_*/*")
                    if p.is_file()))

#: التحريراتُ الأربع — ولكلٍّ موضعٌ في الشيفرة وسمٌّ يُشغَّل.
EDITS = {
    "E1": {
        "was": "حارسُ الفهرس `len(idx) >= 5` — عددٌ لا هُويّة.",
        "now": "جردٌ مُثبَّتٌ بالمسار: ستّةُ دفاترَ مسمّاةٌ بمساراتها "
               "على آلتَين.",
        "why": "العددُ يمرّ بعد حذفِ دفترٍ ما دام سادسٌ قد أُضيف. "
               "والمسارُ لا يمرّ.",
        "site": "tests_taaqol/test_exec_now.py::PINNED_LEDGERS",
        "poison": "tests_taaqol/test_exec_now.py::"
                  "test_poison_a_deleted_ledger_falls_even_when_another_is_added",
    },
    "E2": {
        "was": "`G_NO_LEDGER_MERGE` يُقرأ حارسًا بنيويًّا.",
        "now": "`NO_MERGE_KIND = NUMERIC_COINCIDENCE_CHECK` — والوسمُ في "
               "اسم الحارس نفسِه في الدفتر.",
        "why": "لا يقرأ نسبًا ولا مسارات: يبحث عن مصادفةٍ عدديّة. فيتّهم "
               "بريئًا صادف المجموعَ، ويُبرّئ مدموجًا لم يصادف.",
        "site": "scripts/build_exec_now.py::NO_MERGE_KIND",
        "poison": "tests_taaqol/test_exec_now.py::"
                  "test_no_merge_is_labelled_a_numeric_coincidence_check",
    },
    "E3": {
        "was": "٢٩٩ و٢٩٢ مكتوبتان في تعليق، والفرقُ مشروحٌ نثرًا.",
        "now": "`repeat_is_entry_boundary(page)` — يُشتقّ الفرقُ ويُقابَل "
               "بحقول `EntryBoundary` مستفتاةً من الصنف حيًّا.",
        "why": "رقمٌ مكتوبٌ في تعليقٍ لا يسقط حين يتغيّر المخرَج.",
        "site": "scripts/build_exec_now.py::repeat_is_entry_boundary",
        "poison": "tests_taaqol/test_exec_now.py::"
                  "test_poison_e3_falls_when_a_foreign_pair_repeats",
    },
    "E4": {
        "was": "القاعدةُ السابعةُ مذكورةٌ في الكلام، غيرُ موثَّقةٍ ولا مسمومة.",
        "now": "`COUNT_IS_NOT_MEMBERSHIP` سابعةً في `RULES` — وُسِّعت "
               "بحكم المالك إلى الجهتين بعد أن كانت في جهةٍ واحدة.",
        "why": "العددُ ظلُّ المجموعة لا هي. وأوّلُ صيغةٍ قالت «تساوٍ بلا "
               "اتّحاد» وحدَها، فمرّ الخطأُ المعاكس: «Example سقط» رُفع "
               "لاختلافِ 55/160 ولم يضع صفٌّ واحد. فصارت الجهتان معًا.",
        "site": "scripts/build_exec_now.py::RULES",
        "poison": "tests_taaqol/test_exec_now.py::"
                  "test_count_is_not_membership_in_both_directions",
    },
}


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
            "untouched": not dirty}


def byte_identical(evidence: Path | None = None) -> dict:
    """`G_BYTE_IDENTICAL` — بمقامٍ مُعلَن: كلُّ ملفٍّ تحت `reports/axis_*`.

    ولا يُعاد التشغيلُ هنا: البصماتُ تُقرأ من الملفّات كما هي، وشهادةُ
    التطابقِ بين تشغيلَين مكتوبةٌ في `run_evidence` بأمرِها. فحارسٌ يدّعي
    تطابقًا لم يُشغَّل مرّتَين يشهد بما لم يرَ.
    """
    ev = evidence or (ROOT / "output" / "max" / "byte_identity_evidence.json")
    now = {rel: hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()
           for rel in AXES}
    if not ev.is_file():
        return {"guard": "G_BYTE_IDENTICAL", "denominator": len(AXES),
                "state": "NOT_AVAILABLE:NO_SECOND_RUN_RECORDED",
                "files": sorted(now), "passes": False,
                "note": "لم تُسجَّل شهادةُ تشغيلٍ ثانٍ بعد."}
    prev = json.loads(ev.read_text(encoding="utf-8"))
    before = prev.get("sha256", {})
    missing = sorted(set(now) - set(before))
    differ = sorted(k for k in now if k in before and now[k] != before[k])
    return {"guard": "G_BYTE_IDENTICAL", "denominator": len(AXES),
            "denominator_note": "كلُّ ملفٍّ تحت reports/axis_* — لا الجداولُ "
                                "الخمسةُ وحدَها",
            "compared": len(before), "not_in_evidence": missing,
            "differing": differ, "command": prev.get("command"),
            "runs": prev.get("runs"), "state": "MEASURED",
            "passes": not differ and not missing}


def t5_ready() -> dict:
    """ما يُشغَّل في دقائقَ لحظةَ يُسند المالكُ الأصناف."""
    assign = read("data/residual_kind_assignment.json")
    pending = sorted(k for k, v in assign["assignments"].items() if v is None)
    proj = read("reports/gamma_shadow/PROJECTED_IMPACT.json")
    return {
        "state": "BLOCKED_AWAITING_B2" if pending else "READY",
        "classes": len(assign["assignments"]),
        "pending": pending,
        "assignable_kinds": ["BLOCKING", "DEFERRABLE",
                             "NON_BLOCKING", "EXPLANATORY"],
        "hidden_forbidden_is_not_assignable": True,
        "distinct_rank_outcomes": sorted(set(proj["ceilings"].values())),
        "built_and_failing_closed": [
            {"path": "scripts/gamma_over_axes.py",
             "exit": 3, "writes": "لا ملفَّ واحدًا ما دام صنفٌ null"},
        ],
        "built_and_running_in_shadow": [
            "scripts/projected_impact.py ⟶ reports/gamma_shadow/",
            "scripts/forbidden_shadow.py ⟶ reports/forbidden_shadow/",
            "scripts/gate_shadow.py ⟶ reports/gate_shadow/",
        ],
        "what_runs_the_moment_b2_lands": [
            "يُملأ data/residual_kind_assignment.json بأربعةٍ لا خمسة",
            "يُشغَّل scripts/gamma_over_axes.py — فيخرج من الوقف",
            "تُقرأ مصفوفةُ الانتقال في PROJECTED_IMPACT.md فتصير أثرًا واقعًا",
        ],
        "what_still_will_not_run": {
            "C1_stages": "إحدى عشرةَ مرحلةً تفتحها C1 — وهي خارجَ الولاية",
            "ANSWER_AUDIT": "لا تُفتح بـ C1 ولا بـ B2 — runtime_implemented=False",
        },
    }


def nazila_header(naz: dict, gate: dict, bi: dict) -> list[str]:
    return [
        "```text",
        f'NAZILA_REGENERATED = {naz["utc"]}',
        f'NAZILA_SCORE       = {naz["score"]}% ({naz["grounded"]}/'
        f'{naz["total"]})   ·   STAGES_OPENED = {naz["stages_opened"]}',
        f'NAZILA_HTML        = {naz["sections"]} فصلًا · '
        f'{naz["derivation"]} [{naz["repeat_identity"]}]',
        f'AXIS_BYTE_IDENTITY = {bi["state"]} · '
        f'{bi["compared"] if bi.get("compared") is not None else "—"}/'
        f'{bi["denominator"]} ملفًّا',
        "```", "", "```text",
        "TASK_ID = MAX_EXECUTABLE",
        f'VENDOR_HEAD = {gate["vendor_head"]} · '
        f'porcelain {gate["porcelain_lines"]} · '
        f'VENDOR_UNTOUCHED = {str(gate["untouched"]).upper()}',
        "NO_COMMIT = TRUE   ·   LICENSE_GRANTED = NO",
        "P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED = TRUE",
        "CLAIM_PROJECT_FINISHED = NO",
        "```", "",
    ]


def render(naz, gate, bi, t5, t6, t7, proj, b2) -> str:
    o = ["# `MAX_EXECUTABLE` — ما نُفِّذ، وما وقف، ولمن الباب", ""]
    o += nazila_header(naz, gate, bi)

    o += ["## التحريراتُ الأربع", "",
          "| # | كان | صار | لماذا | السمّ |", "|---|---|---|---|---|"]
    for k, e in EDITS.items():
        o.append(f'| `{k}` | {e["was"]} | {e["now"]} | {e["why"]} | '
                 f'`{e["poison"].split("::")[1]}` |')

    o += ["", "## `B2` — ما قيس، وما بقي للمالك", "",
          "| القياس | النتيجة |", "|---|---|"]
    m1 = b2["M1_tanween_split"]
    o += [f'| `M1` المميِّزُ المقترَح | '
          f'{m1["proposed_discriminator"]["matches"]}/'
          f'{m1["proposed_discriminator"]["of"]} — يشطر؟ '
          f'**{m1["proposed_discriminator"]["discriminates"]}** |',
          f'| `M1` المميِّزُ المقيس | '
          f'{m1["measured_discriminator"]["on_silent_alif"]} · '
          f'{m1["measured_discriminator"]["rest"]} — يشطر؟ '
          f'**{m1["measured_discriminator"]["closes"]}** |',
          f'| `M2` الأصنافُ التي تبلغ محورًا لاحقًا | '
          f'{sum(1 for d in b2["M2_reach"]["per_class"].values() if d.get("carries_into_a_later_axis"))}'
          f'/{len(b2["M2_reach"]["per_class"])} |',
          f'| `M3` الاختياراتُ المملوءة | **{t5["classes"] - len(t5["pending"])}'
          f'/{t5["classes"]}** — والاختيارُ حكمُ المالك |',
          f'| السقوفُ المتمايزة | {" · ".join(t5["distinct_rank_outcomes"])} '
          f'— **ثلاثةٌ لا خمسة** |']

    o += ["", "**وأربعةُ أسماءٍ على ثلاثةِ آثار.** `NON_BLOCKING` "
          "و`EXPLANATORY` سقفُهما واحد؛ فاختيارُ أحدهما دون الآخر لا يغيّر "
          "حكمًا واحدًا في المخرَج. وهذا ممّا يُعرَض على المالك قبل أن "
          "يختار.", "",
          "## أثرُ الإسناد قبل وقوعه — `T5.3`", "",
          f'{len(proj["scenarios"])} سيناريو = '
          f'{len(set(s["class"] for s in proj["scenarios"]))} أصناف × '
          f'{len(t5["assignable_kinds"])} إسنادات. '
          "والتفصيلُ في `reports/gamma_shadow/PROJECTED_IMPACT.md`.", "",
          "| الصنف | أقصى ما يتحرّك | تحت |", "|---|---|---|"]
    top: dict = {}
    for s in proj["scenarios"]:
        cur = top.get(s["class"])
        if cur is None or s["verdicts_that_move"] > cur["verdicts_that_move"]:
            top[s["class"]] = s
    for cls, s in sorted(top.items(), key=lambda kv: -kv[1]["verdicts_that_move"]):
        o.append(f'| `{cls}` | {s["verdicts_that_move"]} حكمًا | '
                 f'`{s["kind"]}` ⟶ `{s["rank_cap"]}` |')

    o += ["", "## `T-6` — ظلُّ الخطوط المستقيمة الممنوعة", "",
          f'صفوفٌ {t6["rows"]} · **دليلٌ {t6["evidence_rows"]}** · '
          f'ترديدٌ {t6["guards"][2]["tautology_rows"]}.', "",
          "**والسؤالُ الذي يجيب نفسَه ليس دليلًا.** استفتاءُ السجلّ عن "
          f'صفوفِ السجلّ يردّ `True` في {t6["registry"]["layer_leap_rows"]} '
          f'من {t6["registry"]["layer_leap_rows"]} — وهذا ترديد، لا شهادة. '
          "والدليلُ ما جاء من خارجه:", "",
          "| المصدر | مفحوصٌ | يقع |", "|---|---|---|",
          f'| حوافُّ رسم المراحل | {t6["reach"]["stage_edges_checked"]} | '
          f'{t6["reach"]["stage_edges_forbidden"]} |',
          f'| أزواجُ طبقات البوّابة | '
          f'{t6["reach"]["gate_layers"] * (t6["reach"]["gate_layers"] - 1)} | '
          f'{t6["reach"]["layer_pairs_that_are_registry_rows"]} |', "",
          f'فمن {t6["registry"]["layer_leap_rows"]} صفًّا في السجلّ يبلغه '
          f'رسمُ المراحلِ **{t6["reach"]["stage_edges_forbidden"]}**، وتبلغه '
          f'طبقاتُ البوّابةِ **'
          f'{t6["reach"]["layer_pairs_that_are_registry_rows"]}**: '
          f'`{" · ".join(t6["would_fire_on_evidence"]) or "لا شيء"}`. '
          "والباقي مكتوبٌ لا مسؤولٌ عنه في هذا التشغيل — وذلك خبرٌ عن "
          "**مدى الاستفتاء**، لا طعنٌ في السجلّ.", "",
          "**والواقعةُ المتوقَّعةُ لم تقع.** `Signifier → WordForm` سطرٌ "
          "قائمٌ في السجلّ، غير أنّ `كَتَبَ` في هذا الجسد لم يقشِر مرّةً "
          "واحدة، و`Root_Proven` لم يصر `YES` في صفٍّ واحدٍ من "
          "٧٤٬٦٦٨. فلا واقعةَ تقع تحت السطر. وأمّا **أنّ قشرَ المحور "
          "الرابع هو هذا الانتقالُ بعينه** فليس في الشيفرة ما يدلّ عليه — "
          "`OWNER_RULING_REQUIRED`.", "",
          "## `T-7` — ظلُّ البوّابة", "",
          f'{t7["rows"]} صفًّا، حاملُها من فَخّ الـ vendor نفسِه — '
          "لا من لوحة المفاتيح.", "",
          "| الحالة | العدد |", "|---|---|"]
    for k, v in t7["states"].items():
        o.append(f"| `{k}` | {v} |")
    o += ["", f'والرتبُ الممنوحةُ كلُّها: '
          f'`{" · ".join(t7["ranks_granted"])}` — ولا `CERTIFICATE` '
          "بحال، ولو كانت البيّنةُ برتبة `CERTIFICATE` والبوّابةُ "
          "`LICENSED`. لأنّ الـ`meet` يُقيَّد برتبةِ الحاملِ نفسِه.", "",
          "## الحرّاس", ""]
    # يُسمّى مصدرُ كلّ حارس: حارسان باسمٍ واحدٍ من ملفَّين ليسا واحدًا،
    # واسمٌ مكرَّرٌ بلا نسبةٍ يُقرأ تكرارًا أو يُقرأ اختلافًا — وكلاهما خطأ.
    o += ["| الحارس | من | المقام | النتيجة |", "|---|---|---|---|"]
    tagged = ([("T-6", g) for g in t6["guards"]]
              + [("T-7", g) for g in t7["guards"]]
              + [("T5.3", g) for g in proj["guards"]]
              + [("MAX", bi)])
    for src, g in tagged:
        den = g.get("denominator")
        if den is None:
            den = (f'{g.get("denominator_approved")}+'
                   f'{g.get("denominator_short_circuit")}')
        o.append(f'| `{g["guard"]}` | {src} | {den} | '
                 f'{"PASS" if g["passes"] else "FALLS"} |')

    o += ["", "## ما وقف — ولمن الباب", "",
          "| الموقوف | الحال | لمن |", "|---|---|---|",
          f'| `T-5` (Γ على المحاور) | `{t5["state"]}` — '
          f'{len(t5["pending"])}/{t5["classes"]} بلا إسناد، ولا يُكتب '
          "ملفٌّ واحد | **المالك** — `B2` |",
          "| إسنادُ الأصناف السبعة | `null` × 7 | **المالك** — "
          "`P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED` |",
          "| نسبةُ قشرِ المحور الرابع إلى سطرٍ في السجلّ | "
          "`OWNER_RULING_REQUIRED` | **المالك** |",
          "| إحدى عشرةَ مرحلةً تفتحها `C1` | خارجَ الولاية | **المالك** |",
          "| `ANSWER_AUDIT` | `runtime_implemented = False` — لا تفتحها "
          "`C1` ولا `B2` | **المالك** |", "",
          "```text", "CLAIM_PROJECT_FINISHED = NO", "```", ""]
    return "\n".join(o) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/max")
    a = ap.parse_args()

    gate = vendor_gate()
    if not gate["untouched"]:
        raise Blocked(f"BLOCKED_AT_VENDOR: {gate}")

    corr = read("output/exec_now/00_corrections.json")
    naz = dict(corr["nazila"])
    naz["utc"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    b2 = read("output/max/01_b2_measures.json")
    t6 = read("reports/forbidden_shadow/SUMMARY.json")
    t7 = read("reports/gate_shadow/SUMMARY.json")
    proj = read("reports/gamma_shadow/PROJECTED_IMPACT.json")
    bi = byte_identical()
    t5 = t5_ready()

    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "00_edits.json").write_text(
        json.dumps({"task": "MAX_EXECUTABLE", "edits": EDITS,
                    "vendor": gate}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    (out / "02_t5_ready.json").write_text(
        json.dumps(t5, ensure_ascii=False, indent=1), encoding="utf-8")
    doc = render(naz, gate, bi, t5, t6, t7, proj, b2)
    (out / "03_report.md").write_text(doc, encoding="utf-8")

    print("\n".join(nazila_header(naz, gate, bi)))
    print(f'EDITS         {len(EDITS)} · كلُّها مسمومة')
    print(f'T5            {t5["state"]} · بلا إسناد '
          f'{len(t5["pending"])}/{t5["classes"]}')
    print(f'T6            دليلٌ {t6["evidence_rows"]}/{t6["rows"]} · '
          f'يقع {t6["would_fire_on_evidence"]}')
    print(f'T7            {t7["rows"]} صفًّا · رتبٌ {t7["ranks_granted"]}')
    print(f'{bi["guard"]:22} {"PASS" if bi["passes"] else "FALLS"} · '
          f'{bi.get("compared", "—")}/{bi["denominator"]} ملفًّا')
    print(f"→ {out}/03_report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
