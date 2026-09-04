#!/usr/bin/env python3
"""ما لا تبلغه الحاويةُ — يُقاس على آلة المالك ويُطبع حِمْلًا واحدًا.

    python3 scripts/measure_device.py            # على ~/final-september
    .venv-taaqol/bin/python scripts/build_exec_now.py --device "$(...)"

**العلّة.** أربعةُ حقولٍ في `build_exec_now` مصدرُها آلةُ المالك لا
الحاوية: عددُ الالتزامات، ومقامُ `B1`، ومدى `A4`، ودفاترُ `~/hokom`.
وكانت تُجمع بيدٍ وتُلصق في سطر أمرٍ طويل — فإن نُسي حقلٌ خرج
`UNMEASURED` صامتًا، وإن شاخ رقمٌ لم يُعلن شيخوخته.

**فيُشتقّ الحِمْلُ كلُّه من تشغيلٍ واحد**، ويُطبع `JSON` يُمرَّر كما هو.
وما لم يُبلَغ يخرج `state: ABSENT` باسمه — لا صفرًا ولا سكوتًا.

**ولا يُقاس هنا شيءٌ تبلغه الحاوية.** فالحقلُ الذي يُقاس في الموضعين
يشيخ في أحدهما.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

#: دفاترُ الآلة — **مغلقة**، وبالمسار لا بالعدد (`E1`).
DEVICE_LEDGERS = (
    ("hokom/output/b83/02_ledger.json", "بندًا"),
    ("hokom/output/tail/03_report.md", "سطرًا"),
    ("hokom/output/nazila_result/"
     "TAAQOL_NAZILA_CODE_VS_REFERENCE_TWO_COLUMN.csv", "صفًّا"),
)


def sha256_of(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for c in iter(lambda: fh.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def stamp(p: Path) -> str:
    return datetime.fromtimestamp(
        p.stat().st_mtime, timezone.utc).isoformat(timespec="seconds")


def commits(repo: Path) -> int | str:
    r = subprocess.run(["git", "-C", str(repo), "rev-list", "--count", "HEAD"],
                       capture_output=True, text=True, check=False)
    return int(r.stdout.strip()) if r.returncode == 0 else "UNMEASURED"


def b1_denominator(hokom: Path) -> dict:
    """`B1` — المقامُ من الملفّ الحاكم، لا من الرسالة.

    والرسالةُ قالت «١٤ pyc و٤ مصادر»، والملفُّ يقول `12 · 6`. وكلاهما
    يجمع ١٨ — والقسمةُ هي محلُّ النزاع، فتُقرأ من الملفّ.
    """
    p = hokom / "output" / "tail" / "02_denominator.json"
    if not p.is_file():
        return {"state": "ABSENT", "path": str(p)}
    d = json.loads(p.read_text(encoding="utf-8"))
    fams = {}
    for k, n in (d.get("excluded_by_reason") or {}).items():
        fams[k.split(" —")[0].strip()] = n
    return {"source": str(p.relative_to(hokom.parent)),
            "sha256": sha256_of(p),
            "BYTECODE_CACHE_and_SOURCE": fams,
            "excluded_total": d.get("excluded_total"),
            "denominator": d.get("denominator"),
            "denominator_note": "المقامُ اثنان لأنّ المخرَجات اثنان، "
                                "لا لأنّ الجردَ ضاق.",
            "files_in_phases": d.get("files_in_phases"),
            "closes": d.get("closes"),
            "governing": "FILE_NOT_MESSAGE"}


def a4_scope(repo: Path) -> dict:
    """`B2` — مدى `NO_PROMOTION` حقلًا لا نثرًا، من مخرَج الفحص نفسِه.

    والمخرَجُ في `~/final-september/output/tail/01_a4.json` — لا في
    `~/hokom`. وقراءتُه من الشجرة الخطأ تُخرج الحقلَين `null` **بلا
    إنذار**، وهو الصفرُ النظيفُ الذي يُشبه القياس.
    """
    p = repo / "output" / "tail" / "01_a4.json"
    if not p.is_file():
        return {"state": "ABSENT", "path": str(p),
                "reason": "شغّل  python3 scripts/check_no_promotion.py"}
    d = json.loads(p.read_text(encoding="utf-8"))
    return {"data_held_constant_at":
                d.get("data_held_constant_at", "FIELD_ABSENT") or "FIELD_ABSENT",
            "scope_note": d.get("scope_note") or "FIELD_ABSENT",
            "NO_PROMOTION": d.get("NO_PROMOTION"),
            "cuts_total": d.get("cuts_total"),
            "cuts_measured": d.get("cuts_measured"),
            "cuts_unmeasurable": d.get("cuts_unmeasurable"),
            "cuts_not_in_history": d.get("cuts_not_in_history"),
            "last_run": stamp(p)}


def operators_catalog(hokom: Path) -> dict:
    import csv
    p = hokom / "data" / "operators_catalog_split_vocalized_corrected.csv"
    if not p.is_file():
        return {"path": str(p), "state": "ABSENT", "LICENSE_GRANTED": "NO"}
    with p.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))
    ops = {r.get("Operator", "").strip() for r in rows if r.get("Operator")}
    return {"path": str(p), "sha256": sha256_of(p), "rows": len(rows),
            "rows_denominator": "صفوفُ الملفّ بلا الترويسة",
            "unique_operators": len(ops),
            "unique_operators_denominator": "قيمٌ متمايزةٌ في عمود Operator",
            "LICENSE_GRANTED": "NO",
            "note": "تسميةُ الملفّ بحكم المالك ليست اعتمادَه."}


def ledgers(home: Path) -> list[dict]:
    """دفاترُ الآلة — كلٌّ بمقامه، ولا رقمَ جامعٌ عبرها."""
    out = []
    for rel, unit in DEVICE_LEDGERS:
        p = home / rel
        if not p.is_file():
            out.append({"ledger": rel, "machine": "device", "state": "ABSENT"})
            continue
        if p.suffix == ".json":
            d = json.loads(p.read_text(encoding="utf-8"))
            items = d.get("items")
            n = len(items) if isinstance(items, (list, dict)) else len(d)
            by = d.get("by_status") or {}
            if not by and isinstance(items, dict):
                by = {}
                for v in items.values():
                    s = (v or {}).get("status")
                    if s:
                        by[s] = by.get(s, 0) + 1
        elif p.suffix == ".csv":
            import csv
            with p.open(encoding="utf-8-sig", newline="") as fh:
                n = len(list(csv.DictReader(fh)))
            by = {}
        else:
            n = len(p.read_text(encoding="utf-8").splitlines())
            by = {}
        out.append({"ledger": rel, "machine": "device",
                    "denominator": f"{n} {unit}", "count": n,
                    "by_status": by, "sha256": sha256_of(p),
                    "last_run": stamp(p)})
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--home", default=str(Path.home() / "mnt"),
                    help="الجذرُ الذي تحته final-september و hokom")
    a = ap.parse_args()
    home = Path(a.home).expanduser()
    repo, hokom = home / "final-september", home / "hokom"
    payload = {
        "measured_on": "DEVICE",
        "measured_utc": datetime.now(timezone.utc).isoformat(
            timespec="seconds"),
        "home": str(home),
        "aslot_commits": commits(repo),
        "aslot_head": subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, check=False).stdout.strip()
        or "UNMEASURED",
        "denominator": b1_denominator(hokom),
        "a4_scope": a4_scope(repo),
        "operators_catalog": operators_catalog(hokom),
        "ledgers": ledgers(home),
    }
    absent = [k for k, v in payload.items()
              if isinstance(v, dict) and v.get("state") == "ABSENT"]
    absent += [x["ledger"] for x in payload["ledgers"]
               if x.get("state") == "ABSENT"]
    payload["absent"] = absent
    print(json.dumps(payload, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
