#!/usr/bin/env python3
"""`NO_PROMOTION` عند **كلّ قَطعِ إصدار**، لا عند الرأس وحدَه  (`A4`).

    python3 scripts/check_no_promotion.py --out output/tail

**الواقعةُ التي وُضع لها.** `2.7.0` رقّى أحدَ عشرَ صفًّا من تأجيلٍ إلى قبولٍ
بلا دليل — ومنها `كَبَائِرَ`، وهو **شاهدُ بوّابةٍ مسمًّى** — ولم يصطدها
إجراء، وزوالُها في `2.9.0` كان عرَضًا لا قصدًا. وفحصٌ على الرأس وحدَه يرى
النتيجةَ الأخيرةَ ولا يرى الطريق.

**ويُشغَّل ولا يُقرأ.** لكلّ قَطعٍ تُستخرج شجرتُه (`git archive` — لا
`checkout`، فلا يتحرّك رأسٌ ولا تُمسّ شجرةُ العمل)، وتُشغَّل شواهدُه
بكودِ ذلك القَطع نفسِه. ولا يُفحص نصٌّ ولا رسالةُ التزام.

**والقَطعُ الذي لا يُقاس يُسمّى.** `UNMEASURABLE_AT_CUT` باسمه وعلّته —
تبعيّةٌ ذهبت، أو بيئةٌ لا تُبنى، أو دالّةٌ لم تكن موجودةً بعد. ولا يُقفز
عنه صامتًا، ولا يُعدّ ناجحًا: القفزُ الصامتُ هو العيبُ الذي وُضع له الفحص.
"""
from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

#: الشواهدُ المسمّاةُ في فحوص المحور الرابع وسمومه.
NAMED = ("بِسْمِ", "كَفَرُوا", "كَبَائِرَ", "كَتَبَ", "مَا",
         "كِتَاْبُنْ", "وَلِلْكَافِرِينَ")

#: ما يُعدّ ترقيةً: انتقالُ حكمٍ إلى القبول. والقبولُ دعوى كالمنع سواء.
PROMOTION = "->ACCEPT"

PROBE = r'''
import json, sys
sys.path.insert(0, "src")
out = {}
try:
    from aslot.axes.axis1_normalization import normalize_token
    from aslot.axes.axis2_registry import Registry
    from aslot.axes.axis4_peeling import peel_to_stem
    from aslot.policy import OwnerPolicy
    try:
        from aslot.axes.axis4_peeling import SUITE_WITNESS as W
    except ImportError:
        W = frozenset({"مَاْ", "كِتَاْبُنْ"})
    policy = OwnerPolicy.load("data/axis_1_owner_policy.json")
    reg = Registry.from_masaq_witness("data/MASAQ.csv", policy)
    for w in json.loads(sys.argv[1]):
        r = peel_to_stem(normalize_token(w, None, policy).normalized, reg, W)
        out[w] = {"verdict": str(r.verdict), "termination": str(r.termination)}
    print("OK" + json.dumps(out, ensure_ascii=False))
except Exception as exc:
    print("ERR" + json.dumps({"type": type(exc).__name__, "msg": str(exc)[:300]},
                             ensure_ascii=False))
'''


def cuts() -> list[dict]:
    """قطوعُ الإصدار من التاريخ نفسِه — لا من قائمةٍ مكتوبةٍ بيد.

    والمستودعُ **بلا أوسام** (`git tag` يردّ صفرًا)، فالقَطعُ يُعرَف برسالة
    الالتزام. وذلك يُعلَن ولا يُسكت عنه: فحصٌ يُعدِّد أوسامًا لا وجودَ لها
    يمرّ على الفراغ.
    """
    log = subprocess.run(["git", "log", "--all", "--pretty=%H|%h|%s"],
                         capture_output=True, text=True, cwd=ROOT,
                         check=False).stdout
    out = []
    for line in log.splitlines():
        full, short, subj = line.split("|", 2)
        m = re.match(r"^(\d+\.\d+\.\d+)\s+—", subj)
        if m:
            out.append({"version": m.group(1), "sha": full, "short": short,
                        "subject": subj, "form": "SUBJECT_PREFIX"})
        elif re.search(r"\d+\.\d+\.\d+", subj):
            out.append({"version": re.search(r"\d+\.\d+\.\d+", subj).group(0),
                        "sha": full, "short": short, "subject": subj,
                        "form": "MENTIONED_ONLY"})
    return list(reversed(out))


def measure_at(cut: dict, data: Path) -> dict:
    """يُشغَّل كودُ القَطع نفسِه على البيانات نفسِها. ولا `checkout` يقع."""
    tmp = Path(tempfile.mkdtemp(prefix=f"a4_{cut['short']}_"))
    try:
        tar = subprocess.run(["git", "archive", cut["sha"]],
                             capture_output=True, cwd=ROOT, check=False)
        if tar.returncode != 0:
            return {"state": "UNMEASURABLE_AT_CUT",
                    "reason": "GIT_ARCHIVE_FAILED"}
        subprocess.run(["tar", "-x", "-C", str(tmp)], input=tar.stdout,
                       check=False)
        if not (tmp / "src" / "aslot").is_dir():
            return {"state": "UNMEASURABLE_AT_CUT",
                    "reason": "NO_SRC_ASLOT_AT_THIS_CUT — الحزمةُ لم تكن بعد"}
        # البياناتُ مستبعَدةٌ من التاريخ بسياسة U1، فتُنسخ من الحاضر:
        # الجردُ واحدٌ في القطعَين، والمتغيّرُ هو الكودُ لا النصّ.
        (tmp / "data").mkdir(exist_ok=True)
        for f in ("MASAQ.csv", "axis_1_owner_policy.json"):
            src = data / f
            if not src.is_file():
                return {"state": "UNMEASURABLE_AT_CUT",
                        "reason": f"DATA_ABSENT:{f}"}
            if not (tmp / "data" / f).exists():
                shutil.copy2(src, tmp / "data" / f)
        r = subprocess.run([sys.executable, "-c", PROBE,
                            json.dumps(list(NAMED), ensure_ascii=False)],
                           capture_output=True, text=True, cwd=tmp,
                           check=False, timeout=180)
        line = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        if line.startswith("OK"):
            return {"state": "MEASURED", "verdicts": json.loads(line[2:])}
        if line.startswith("ERR"):
            e = json.loads(line[3:])
            return {"state": "UNMEASURABLE_AT_CUT",
                    "reason": f'{e["type"]}: {e["msg"]}'}
        return {"state": "UNMEASURABLE_AT_CUT",
                "reason": (r.stderr or r.stdout or "NO_OUTPUT")[-300:]}
    except subprocess.TimeoutExpired:
        return {"state": "UNMEASURABLE_AT_CUT", "reason": "TIMEOUT"}
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def boundary(measured: list[dict]) -> dict:
    """أقدمُ قَطعٍ مقيسٍ هو حدُّ ما يراه هذا الفحص — ويُطبع صراحةً.

    فالثلاثةُ التي عادت إلى التأجيل في `2.9.0` كانت **مقبولةً بالفعل** عند
    أقدم قَطعٍ في التاريخ. أي أنّ الترقيةَ وقعت قبله، ولا يراها الفحص:
    `2.7.0` ليس في هذا المستودع. فيُقال ذلك عددًا لا وصفًا، وإلا قُرئ
    `NO_PROMOTION = True` براءةً وهي إنّما تعني «لا ترقيةَ فيما قِيس».
    """
    if not measured:
        return {"earliest_measured_cut": None,
                "note": "لا قَطعَ مقيسٌ — فلا حدَّ يُعلَن"}
    first = measured[0]
    accepted = sorted(w for w, v in first["verdicts"].items()
                      if v["verdict"] == "ACCEPT")
    last = measured[-1]
    now_deferred = sorted(w for w in accepted
                          if last["verdicts"].get(w, {}).get("verdict")
                          != "ACCEPT")
    return {
        "earliest_measured_cut": first["version"],
        "latest_measured_cut": last["version"],
        "accepted_already_at_earliest_cut": accepted,
        "of_those_no_longer_accepted_today": now_deferred,
        "reading": ("ما كان مقبولًا عند أقدم قَطعٍ مقيسٍ لا يُعرف متى رُقّي: "
                    "الترقيةُ وقعت قبل حدّ الفحص. فـNO_PROMOTION تعني "
                    "«لا ترقيةَ فيما قِيس»، لا «لم تقع ترقيةٌ قطّ»."),
    }


def promotions(series: list[dict]) -> list[dict]:
    """ترقيةٌ = شاهدٌ مسمًّى انتقل حكمُه إلى `ACCEPT` بين قَطعَين متتاليَين.

    والقطوعُ غيرُ المقيسة **تقطع السلسلة**: لا يُقابَل قَطعٌ بقَطعٍ بينهما
    مجهول، لأنّ ذلك يُخفي ما وقع في المجهول ويُسمّيه استقرارًا.
    """
    found, prev = [], None
    for cut in series:
        if cut["state"] != "MEASURED":
            prev = None
            continue
        if prev is not None:
            for w, now in cut["verdicts"].items():
                was = prev["verdicts"].get(w)
                if was and was["verdict"] != now["verdict"]:
                    move = f'{was["verdict"]}->{now["verdict"]}'
                    found.append({
                        "witness": w, "from_cut": prev["version"],
                        "to_cut": cut["version"], "move": move,
                        "termination_before": was["termination"],
                        "termination_after": now["termination"],
                        "is_promotion": move.endswith(PROMOTION)})
        prev = cut
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--out", default="output/tail")
    a = ap.parse_args()

    series = []
    for c in cuts():
        series.append({**c, **measure_at(c, ROOT / "data")})

    measured = [c for c in series if c["state"] == "MEASURED"]
    unmeasurable = [{"version": c["version"], "short": c["short"],
                     "reason": c["reason"]}
                    for c in series if c["state"] != "MEASURED"]
    moves = promotions(series)
    proms = [m for m in moves if m["is_promotion"]]

    tags = subprocess.run(["git", "tag"], capture_output=True, text=True,
                          cwd=ROOT, check=False).stdout.split()
    result = {
        "repo": "final-september",
        "head": subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT,
                               capture_output=True, text=True,
                               check=False).stdout.strip(),
        "git_tags": tags,
        "cut_marker": "SUBJECT_PREFIX — المستودعُ بلا أوسام، فالقَطعُ برسالته",
        "cuts_total": len(series),
        "cuts_measured": len(measured),
        "cuts_unmeasurable": unmeasurable,
        "named_witnesses": list(NAMED),
        "verdict_moves": moves,
        "promotions": proms,
        "NO_PROMOTION": not proms,
        "series": series,
        "boundary": boundary(measured),
        # `B2` — حقلٌ لا نثر. عزلُ أثر الكود اختيارٌ صحيح، ولازمُه أنّ
        # تغيُّرَ حكمٍ سببُه بيانٌ **لا يراه هذا الفحص أصلًا**. فيُعلَن مداه
        # حقلًا يُقرأ، وإلا قُرئ NO_PROMOTION أوسعَ ممّا يقيس.
        "data_held_constant_at": "HEAD",
        "scope_note": ("NO_PROMOTION يقيس أثرَ الكود وحدَه · وتغيُّرُ حكمٍ "
                       "سببُه بيانٌ خارج مداه"),
        "cuts_not_in_history": {
            "2.7.0": "القَطعُ الذي وُضع له هذا البند غيرُ موجودٍ في هذا "
                     "المستودع — فترقياتُه الإحدى عشرةَ لا تُعاد قياسًا هنا",
        },
        "command": "python3 scripts/check_no_promotion.py",
    }
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    (out / "01_a4.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f'TAGS              {len(tags)}  ← الفحصُ لا يُعدِّد أوسامًا')
    print(f'CUTS              {len(series)} · مقيسٌ {len(measured)} · '
          f'غيرُ مقيس {len(unmeasurable)}')
    for u in unmeasurable:
        print(f'   UNMEASURABLE_AT_CUT {u["version"]:8} {u["reason"][:70]}')
    print(f'VERDICT_MOVES     {len(moves)}')
    for m in moves:
        print(f'   {m["witness"]:16} {m["from_cut"]} ⟶ {m["to_cut"]}  '
              f'{m["move"]}  ترقية={m["is_promotion"]}')
    print(f'NO_PROMOTION      {result["NO_PROMOTION"]}')
    print(f'→ {out}/01_a4.json')
    return 0 if result["NO_PROMOTION"] else 4


if __name__ == "__main__":
    raise SystemExit(main())
