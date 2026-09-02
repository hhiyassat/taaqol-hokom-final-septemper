#!/usr/bin/env python3
"""يشغّل مشغّلَ تعقُّل نفسَه على نصّ النازلة — تشغيلٌ ثانٍ مستقلّ، لا تصديق.

    .venv-taaqol/bin/python scripts/run_taaqol_nazila.py \\
        --text inspection/case.txt --out inspection/nazila

**لماذا هذا الملفّ.** طُلب مني أن أُثبت `BRIDGE_VERDICT = MATCH` ببصمتي.
وبصمةٌ على تشغيلٍ لم يقع **شهادةُ زور**، وهي أسوأُ ما يمكن أن يُنتجه هذا
المشروع. فبدل أن أختم، شغّلتُ.

**والحدّ الذي لا يُخرق.** هذا المشغّلُ **معزولٌ عن أسلوط تمامًا**:

* يُنفَّذ ببيئةٍ منفصلة (`.venv-taaqol`، بايثون ٣٫١١) — وأسلوط يبقى على ٣٫١٠.
* لا يستورده محورٌ من محاور أسلوط، ولا يدخل مخرجُه أيَّ حكمٍ فيها.
* فسمُّ `P6_NO_JUDGEMENT_TOOL_IS_IMPORTED` يبقى مارًّا كما كان: تشغيلُ أداةٍ
  في تجربةٍ مُعلَنةٍ ليس استيرادَها في سلسلةِ حكم.

والمخرجُ سجلٌّ لكلّ (توكن × مرحلة) بكلّ حقوله — ليكون التدقيقُ ممكنًا،
لا التصديقُ مطلوبًا.
"""
from __future__ import annotations

import argparse
import dataclasses
import hashlib
import json
import platform
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "vendor" / "Taaqol-GPT" / "src"))


def to_plain(value):
    """يفرّغ السجلَّ إلى JSON بلا تأويل: التعداداتُ بقيمها، والبنى بحقولها."""
    if dataclasses.is_dataclass(value) and not isinstance(value, type):
        return {f.name: to_plain(getattr(value, f.name))
                for f in dataclasses.fields(value)}
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [to_plain(v) for v in value]
    if hasattr(value, "value") and hasattr(value, "name"):
        return value.value
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--text", default="inspection/case.txt")
    ap.add_argument("--corpus-id", default="nazila")
    ap.add_argument("--out", default="inspection/nazila")
    args = ap.parse_args()

    src = Path(args.text)
    raw = src.read_text(encoding="utf-8")
    text = raw.strip()
    tokens = tuple(text.split())

    from taaqqul_slot_geometry.runtime.corpus_runner import run_native_corpus
    result = run_native_corpus(args.corpus_id, tokens)
    plain = to_plain(result)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    records = [r for t in plain.get("token_results", [])
               for r in t.get("records", [])]
    # أسماءُ الحقول تُقرأ من السجلّ نفسِه لا تُخمَّن: أوّلُ محاولةٍ عدّت
    # `stage_transition_state` و`hint` فخرجت {None: 160} و{} — عدٌّ لحقلٍ
    # لا وجودَ له يعطي صفرًا نظيفًا يُشبه القياس. والحقلان الحقيقيّان
    # `transition_state` و`remediation_hints`.
    fields = sorted({k for r in records for k in r})
    states = Counter(r.get("transition_state") for r in records)
    hints = Counter(h for r in records for h in (r.get("remediation_hints") or []))
    residuals = Counter(x for r in records
                        for x in (r.get("residuals_after") or []))
    ranks = Counter(f'{r.get("rank_before")}->{r.get("rank_after")}'
                    for r in records)
    stages = Counter(r.get("stage_id") for r in records)
    paths = Counter(r.get("path_id") for r in records)
    # حارسٌ عامّ: لا يُعدُّ حقلٌ لا وجودَ له. فلو أُعيدت تسميةُ حقلٍ في تعقُّل
    # ظهر ذلك إنذارًا، لا صفرًا صامتًا يُقرأ سلامةً.
    absent = [k for k, v in (("transition_state", states),
                             ("stage_id", stages),
                             ("rank_before", ranks)) if set(v) == {None}]
    if absent:
        raise SystemExit(f"OWNER_ALERT: حقولٌ غائبةٌ في السجلّ — {absent}. "
                         f"الحقولُ الموجودة: {fields}")

    # البصمتان تُطبعان **معًا وبمقاميهما**، فلا يُقابَل ملفٌّ بنصٍّ مجرَّد.
    # وهذا هو الخطأُ الذي أقرّ به المالكُ في تعليمته، ويُسدّ هنا بالطبع لا
    # بالتذكير: من يقرأ يرى أيَّ رقمٍ يقابل أيَّ أمر.
    identity = {
        "source_file": str(src),
        "sha256_stripped_text": hashlib.sha256(text.encode()).hexdigest(),
        "sha256_file_bytes": hashlib.sha256(raw.encode()).hexdigest(),
        "how_to_reproduce": {
            "sha256_stripped_text":
                "python -c \"import hashlib,sys;print(hashlib.sha256("
                "open(sys.argv[1],encoding='utf-8').read().strip()"
                ".encode()).hexdigest())\" <file>",
            "sha256_file_bytes": "shasum -a 256 <file>",
        },
        "tokens": len(tokens),
        "corpus_id": args.corpus_id,
        "run_id": plain.get("run_id"),
        "python": platform.python_version(),
        "platform": f"{platform.system()} {platform.machine()}",
        "taaqol_commit": "3cccdded7951ba71b3cb2a8b9b477f3fb3d91095",
        "taaqol_modules_executed": sum(1 for m in sys.modules
                                       if m.startswith("taaqqul")),
        "measured_by": "REVIEW_CONTAINER_CLOUD",
        "aslot_isolation": "لم يُستورد في أيّ محور، ولم يدخل مخرجُه أيَّ حكم",
    }
    summary = {
        "identity": identity,
        "records_total": len(records),
        "stage_transition_states": dict(sorted(states.items())),
        "hints": dict(sorted(hints.items())),
        "residuals_after": dict(sorted(residuals.items())),
        "ranks": dict(sorted(ranks.items())),
        "stage_ids": dict(sorted(stages.items())),
        "path_ids": dict(sorted(paths.items())),
        "record_fields": fields,
        "record_field_count": len(fields),
    }
    (out / "01_run.json").write_text(
        json.dumps(plain, ensure_ascii=False, indent=1), encoding="utf-8")
    (out / "00_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"TOKENS            {len(tokens)}")
    print(f"RECORDS           {len(records)}")
    print(f"RECORD_FIELDS     {len(fields)}")
    print(f"SHA256_TEXT       {identity['sha256_stripped_text'][:16]}…"
          f"   (النصُّ المجرَّد)")
    print(f"SHA256_FILE       {identity['sha256_file_bytes'][:16]}…"
          f"   (بايتات الملفّ — ما يطبعه shasum)")
    print(f"PYTHON            {identity['python']} · {identity['platform']}")
    print(f"STATES            {dict(sorted(states.items()))}")
    print(f"HINTS             {dict(sorted(hints.items()))}")
    print(f"RESIDUALS         {dict(sorted(residuals.items()))}")
    print(f"RANKS             {dict(sorted(ranks.items()))}")
    print(f"→ {out}/01_run.json · {out}/00_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
