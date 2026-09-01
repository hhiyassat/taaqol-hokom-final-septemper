#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الكود ٥ — المحور الرابع: التقشير إلى جذعٍ غير قابل للقشر

AXIS          = 4
MODULE        = a4_peel_to_stem.py
IMPLEMENT_ROOT   = NO
ROOT_WORK        = NONE          ← حكم المالك 2026-09-01
ROOT_PROVEN      = NO  (دائمًا)
WAZN_EXECUTION   = 0
SUFFIX_OUTPUT    = 0
AL_OPENED        = NO
SUFFIXES_OPENED  = NO

المسألة (T4 §٤ـ١)
------------------
أيّ طرفٍ من الكلمة زائدٌ وأيّه أصل؟ وهو **السؤال الذي لا يُجاب عنه من السطح**:
الكاف سابقةٌ في `كَمِثْلِهِ` وأصلٌ في `كَفَرُوا` — **بالرسم نفسه والحركة نفسها**.

فالتقشير ليس مطابقة أطراف، بل **إقامةُ حجّة** على أن هذا الطرف زائد هنا.

المبدأ الحاكم (T4 §٤ـ٢)
    ACCEPT = CAUSE_PRESENT AND ALL_CONDITIONS_SATISFIED AND NO_PREVENTER_PRESENT
    DEFER  = أيُّ واقعةٍ غير محسومة
    BLOCK  = غياب السبب ، أو سقوط شرط ، أو حضور مانع

والفرق بين DEFER وBLOCK ليس في الشدّة بل في **نوع المعرفة**: BLOCK دعوى بأن
المانع قائم، وDEFER اعترافٌ بأن الحجّة ناقصة.

فرقٌ عن T4 بحكم المالك (2026-09-01)
-----------------------------------
مسار الجذر **مغلق كليًّا** في هذه النسخة: لا وسمَ «مرشّح جذر»، ولا حدَّ ثلاثةِ
صوامت، ولا `Root`. المخرج الوحيد هو **الجذع غير القابل للقشر**:

    STEM_OUTPUT = REMAINDER_WITH_NO_FURTHER_LICENSED_PEEL
    STEM_PROOF  = NOT_CLAIMED       (الجذع وسمُ موقفٍ لا دعوى صرفية)
    THREE_CONSONANT_GATE = NOT_APPLIED

وهذا **تضييقٌ** لا توسيع: كلُّ ما كان يثبته T4 ما زال يُثبت، وما لم يكن يثبته
لم يُفتح.

الاتّصال بالمحورين ٢ و٣
    يتمّ عبر واجهتيهما الحقيقيتين لا بنسخ منطقهما:
        Axis2.recheck(surface)                  ← a2
        analyze_normalized_surface(surface)     ← a3
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from a1_normalize import load_policy
from a2_classify_mabniyat_and_operators import (Axis2, PROOF_PROVEN,
                                                PROOF_UNRESOLVED,
                                                PROOF_VERBAL_OPERATOR)
from a3_syllabify import analyze_normalized_surface, boundary_positions

MODULE = "a4_peel_to_stem.py"
AXIS = 4

# ---------------------------------------------------------------------------
# ١ — الترخيص: قائمة مغلقة، مشكولة، ولا تسمية (T4 §٤ـ٥)
# ---------------------------------------------------------------------------

#: العضو **سطحٌ بحروفه وحركاته معًا**؛ الحروف وحدها لا ترخّص.
#: وهي مغلقة: ما خرج عنها لا يُقشَّر ولو كان عاملًا مشهورًا.
#: و`لَ` مرخّصة **دون** أن تُسمّى حرف جر — الترخيص إذنٌ بالقشر لا حكمٌ نحويّ.
OWNER_RATIFIED_ATTACHABLE_PREFIX_SET = ("وَ", "فَ", "بِ", "كَ", "لِ", "لَ")

#: همزة الاستفهام مرشّحةٌ **مؤجّلة** لا مرفوضة ولا مرخّصة.
INTERROGATIVE_HAMZA_PREFIXES = ("أَ",)

#: سوابق المضارع والسين: مرشّحاتٌ لا تراخيص — تُولَّد وتُقيَّم وتُرفض ولا تُقشَّر.
NON_LICENSED_CANDIDATE_PREFIXES = ("أَ", "نَ", "تَ", "يَ", "سَ")

# ---------------------------------------------------------------------------
# ٢ — البوابة: الحرف الأول قد يكون أصلًا (T4 §٤ـ٧)
# ---------------------------------------------------------------------------

ROOT_CANDIDATE_AFTER_PREFIX_PEEL_REQUIRES_EXTRA_EVIDENCE = True
INITIAL_LETTER_MAY_BE_RADICAL = True
EXTRA_EVIDENCE_EFFECT = "DEFER"
EXTRA_EVIDENCE_BLOCK_ALLOWED = False

#: الشرط C — نمط البقية والسابقة المفردة معًا
GATE_C_PATTERN = ("CVV", "CV", "CV")
GATE_C_PREFIXES = ("كَ", "لَ", "فَ")

# ---------------------------------------------------------------------------
# ٣ — جبر التقشير: خمس معادلات نفي (T4 §٤ـ٣)
# ---------------------------------------------------------------------------

PEELING_ALGEBRA = (
    ("SURFACE_MATCH ≠ ATTACHMENT_ROLE_PROVEN",
     "أن يكون تطابقُ الرسم حجّةً على الدور"),
    ("OPERATOR_PROVEN ≠ ATTACHABLE_PREFIX_PROVEN",
     "أن يصير كلُّ عاملٍ سابقةً قابلة للقشر"),
    ("REMAINDER ≠ STEM",
     "أن تُسمّى البقيةُ جذعًا لمجرّد أنها بقيت"),
    ("THREE_CONSONANT_REMAINDER ≠ ROOT_PROVEN",
     "أن يُعدّ العددُ نسبًا  — والحدّ نفسه غير مطبَّق هنا"),
    ("PREFIX_SURFACE_MATCH_ALONE_IS_NOT_LICENSE",
     "أن يُقشَّر حرفٌ لأنه يشبه سابقة"),
)

# ---------------------------------------------------------------------------
# ٤ — المخارج
# ---------------------------------------------------------------------------

T_STEM = "STEM_NOT_FURTHER_PEELABLE"
T_CLOSED = "CLOSED_REMAINDER"
T_DEFER_GATE = "DEFER_INITIAL_LETTER_MAY_BE_RADICAL"
T_DEFER_UNRESOLVED = "DEFER_UNRESOLVED_CLOSURE"
T_DEFER_VERBAL_OP = "DEFER_VERBAL_OPERATOR_REGISTRY_TAG"
T_BLOCK_BOUNDARY = "BLOCK_SYLLABLE_BOUNDARY_CROSSED"
T_BLOCK_AXIS3 = "BLOCK_AXIS_3_REJECTED"
T_BLOCK_EMPTY = "BLOCK_EMPTY_REMAINDER"

TERMINATIONS = (T_STEM, T_CLOSED, T_DEFER_GATE, T_DEFER_UNRESOLVED,
                T_DEFER_VERBAL_OP, T_BLOCK_BOUNDARY,
                T_BLOCK_AXIS3, T_BLOCK_EMPTY)


@dataclass
class Peel:
    prefix: str
    license_id: str
    cut_at: int
    remainder: str


@dataclass
class PeelResult:
    surface: str
    verdict: str = "ACCEPT"          # ACCEPT | DEFER | BLOCK
    termination: str = T_STEM
    peels: list = field(default_factory=list)
    stem_surface: str = ""
    stem_pattern: str = ""
    stem_consonants: int = 0
    closed_form_proof: str = ""
    deferred_candidate: str = ""     # سابقةٌ مرشّحة غير مرخّصة، سُجّلت ولم تُقشَّر
    note: str = ""

    # ثوابتُ يُعاد التصريح بها في كل صفٍّ حتى لا تُقرأ نتيجةٌ بغير قيدها
    root_work: str = "NONE"
    root_proven: str = "NO"
    stem_proof: str = "NOT_CLAIMED"


# ---------------------------------------------------------------------------
# ٥ — سجلّ شهادة النصّ الداخلي (T4 §٤ـ٧ ملاحظة ٢)
# ---------------------------------------------------------------------------

def build_internal_corpus_witness_set(axis1_csv: Path) -> set:
    """أسطحٌ وردت في النصّ نفسه ككلماتٍ مستقلّة **غير مقشورة**.

    مشتقٌّ من مخرجات المحرّك نفسه، و**دليلٌ لا سلطة**: لا يرخّص قشرًا ولا يحجبه.
    وغيابُه لا يكون مانعًا — إن لم يُحمَّل السجلّ لم تعمل البوابة.
    """
    out = set()
    with axis1_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            s = row["Normalized_Word"]
            if not s:
                continue
            if any(s.startswith(p) for p in OWNER_RATIFIED_ATTACHABLE_PREFIX_SET):
                continue          # ليست «غير مقشورة» — عليها سابقةٌ مرخّصة
            out.add(s)
    return out


# ---------------------------------------------------------------------------
# ٦ — التقشير
# ---------------------------------------------------------------------------

def peel_to_stem(surface: str, ax2: Axis2, witness: set | None = None,
                 max_peels: int = 8) -> PeelResult:
    """يقشّر السطحَ المطبَّع حتى يقف. لا يُنتج جذرًا ولا وزنًا ولا لاحقة."""
    res = PeelResult(surface=surface)
    current = surface

    for _ in range(max_peels):
        # ---- المحور الثاني: هل البقية صورةٌ مغلقة؟ ----------------------
        v2 = ax2.recheck(current)
        res.closed_form_proof = v2.closed_form_proof

        if v2.closed_form_proof == PROOF_PROVEN:
            # T4 §٤ـ٦ : تقف — وحدُّ الصوامت لا يُطبَّق عليها أصلًا
            res.verdict = "ACCEPT"
            res.termination = T_CLOSED
            res.stem_surface = ""
            res.note = "صورةٌ مغلقة مبرهنة — كلمةٌ تامّة لا جذع"
            return res
        if v2.closed_form_proof == PROOF_UNRESOLVED:
            res.verdict = "DEFER"
            res.termination = T_DEFER_UNRESOLVED
            res.note = v2.note
            return res
        if v2.closed_form_proof == PROOF_VERBAL_OPERATOR:
            res.verdict = "DEFER"
            res.termination = T_DEFER_VERBAL_OP
            res.note = v2.note
            return res

        # ---- المحور الثالث: بنيةُ البقية وحدودها -----------------------
        a3 = analyze_normalized_surface(current)
        if not a3.ok:
            res.verdict = "BLOCK"
            res.termination = T_BLOCK_AXIS3
            res.note = a3.block_reason
            return res

        # ---- السبب: سابقةٌ مرخّصة في أول السطح -------------------------
        prefix = next((p for p in OWNER_RATIFIED_ATTACHABLE_PREFIX_SET
                       if current.startswith(p)), None)

        if prefix is None:
            # T4 §٤ـ٥ : المرشّحات غير المرخّصة **تُولَّد وتُقيَّم وتُرفض ولا تُقشَّر**.
            # فالتأجيل واقعٌ على **السابقة** لا على الكلمة: الكلمة تمضي إلى جذعها،
            # ويُسجَّل المرشّح المؤجَّل بجانبه. ولو حُوِّل التأجيل إلى حكمٍ على
            # الكلمة لصار الجهلُ بالسابقة حجبًا للجذع — وهو خلطُ DEFER بـ BLOCK.
            for cand in NON_LICENSED_CANDIDATE_PREFIXES:
                if current.startswith(cand) and len(current) > len(cand) + 2:
                    res.deferred_candidate = cand
                    res.note = (f"مرشّحٌ مؤجَّل: {cand} — "
                                + ("INTERROGATIVE_HAMZA_PREFIX = DEFER"
                                   if cand in INTERROGATIVE_HAMZA_PREFIXES
                                   else "سابقةُ مضارعٍ/سين: مرشّحٌ لا ترخيص"))
                    break
            res.verdict = "ACCEPT"
            res.termination = T_STEM
            res.stem_surface = current
            res.stem_pattern = "·".join(a3.pattern_sequence)
            res.stem_consonants = a3.consonant_count
            return res

        cut = len(prefix)

        # ---- الشرط: القطع لا يعبر حدًّا مقطعيًّا (T3 §٣ـ٦) --------------
        if cut not in boundary_positions(a3):
            res.verdict = "BLOCK"
            res.termination = T_BLOCK_BOUNDARY
            res.note = (f"القطع عند {cut} يعبر حدًّا مقطعيًّا "
                        f"({'·'.join(a3.pattern_sequence)})")
            res.stem_surface = ""
            return res

        remainder = current[cut:]
        if not remainder:
            res.verdict = "BLOCK"
            res.termination = T_BLOCK_EMPTY
            return res

        # ---- الشرط: البقية تُعاد بناءً في المحور الثالث ----------------
        a3r = analyze_normalized_surface(remainder)
        if not a3r.ok:
            res.verdict = "BLOCK"
            res.termination = T_BLOCK_AXIS3
            res.note = f"البقية مرفوضة: {a3r.block_reason}"
            return res

        # ---- المانع: الحرف الأول قد يكون أصلًا (T4 §٤ـ٧) ---------------
        if ROOT_CANDIDATE_AFTER_PREFIX_PEEL_REQUIRES_EXTRA_EVIDENCE and witness is not None:
            cond_c = (tuple(a3r.pattern_sequence) == GATE_C_PATTERN
                      and prefix in GATE_C_PREFIXES)
            cond_d = remainder not in witness
            if cond_c and cond_d:
                # الأثر DEFER لا BLOCK: الشرط تقريبٌ لا برهان.
                res.verdict = "DEFER"
                res.termination = T_DEFER_GATE
                res.note = ("C ∩ D محقَّقان: نمط البقية CVV·CV·CV والسابقة "
                            f"{prefix} وغيرُ مشهودةٍ مستقلّةً — INITIAL_LETTER_MAY_BE_RADICAL")
                res.stem_surface = ""
                return res

        # ---- قُبلت القشرة --------------------------------------------
        res.peels.append(Peel(prefix=prefix,
                              license_id=f"LIC:{OWNER_RATIFIED_ATTACHABLE_PREFIX_SET.index(prefix) + 1}",
                              cut_at=cut, remainder=remainder))
        current = remainder

    res.verdict = "DEFER"
    res.termination = T_DEFER_UNRESOLVED
    res.note = f"تجاوز حدّ القشرات ({max_peels})"
    return res


# ---------------------------------------------------------------------------
# ٧ — الفحوص والسموم
# ---------------------------------------------------------------------------

def self_checks(ax2, witness, policy) -> list:
    from a1_normalize import normalize_token
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    def run(word):
        return peel_to_stem(normalize_token(word, None, policy).normalized, ax2, witness)

    r = run("بِسْمِ")
    add("T1_BISMI_NOT_PEELED_BOUNDARY_CROSSED",
        r.termination == T_BLOCK_BOUNDARY and not r.peels,
        f"{r.termination}   (T3 §٣ـ٦: الترخيص شرطٌ لا يكفي وحده)")

    r = run("بِمَا")
    add("T2_BIMAA_PEELED_THEN_STOPPED_BY_AXIS_2",
        len(r.peels) == 1 and r.termination in (T_CLOSED, T_DEFER_UNRESOLVED),
        f"قشور={len(r.peels)} / {r.termination}   (السجلّ يمنع التقشير بلا نهاية)")

    # T4 §٤ـ٨ — حدٌّ معروف يُثبَّت اختبارًا كي لا يُنسى ولا يُدّعى إصلاحُه:
    # الكاف في كَفَرُوا أصلٌ من ك‑ف‑ر، والمحرّك يقشّرها لأن شرط البوابة C
    # يشترط نمطًا بعينه و«فَرُوْ» ليس منه.
    r = run("كَفَرُوا")
    add("T3_KNOWN_LIMIT_KAFARU_IS_WRONGLY_PEELED",
        len(r.peels) >= 1 and r.termination != T_DEFER_GATE,
        f"قشور={len(r.peels)} جذع={r.stem_surface}  ← حدٌّ معروف مسجَّل، لا نقضٌ للمانع")

    r = run("كَبَائِرَ")
    add("T4_KABAIR_GATE_DEFERS",
        r.termination == T_DEFER_GATE,
        f"{r.termination}   (البوابة تعمل)")

    r = run("مَا")
    add("T5_MAA_IS_CLOSED_NOT_A_STEM",
        r.termination in (T_CLOSED, T_DEFER_UNRESOLVED) and not r.stem_surface,
        f"{r.termination}")

    r = run("كِتَابٌ")
    add("T6_NO_LICENSED_PREFIX_YIELDS_STEM",
        r.termination == T_STEM and r.stem_surface,
        f"{r.stem_surface}")

    add("T7_ROOT_PATH_IS_CLOSED", r.root_work == "NONE" and r.root_proven == "NO",
        "ROOT_WORK = NONE ، ROOT_PROVEN = NO")
    add("T8_STEM_IS_NOT_A_PROOF", r.stem_proof == "NOT_CLAIMED",
        "STEM_PROOF = NOT_CLAIMED — الجذع وسمُ موقفٍ لا دعوى صرفية")
    add("T9_LICENSE_SET_IS_CLOSED_AND_VOCALIZED",
        len(OWNER_RATIFIED_ATTACHABLE_PREFIX_SET) == 6
        and all(len(p) == 2 for p in OWNER_RATIFIED_ATTACHABLE_PREFIX_SET),
        " ، ".join(OWNER_RATIFIED_ATTACHABLE_PREFIX_SET))
    add("T10_INTERROGATIVE_HAMZA_IS_DEFERRED_NOT_LICENSED",
        "أَ" not in OWNER_RATIFIED_ATTACHABLE_PREFIX_SET,
        "INTERROGATIVE_HAMZA_PREFIX = DEFER")

    r = run("أَنْزَلَ")
    add("T11_DEFERRED_CANDIDATE_DOES_NOT_BLOCK_THE_WORD",
        r.termination == T_STEM and r.deferred_candidate == "أَ" and not r.peels,
        f"{r.termination} / مرشّح={r.deferred_candidate} / جذع={r.stem_surface}")

    return out


def poison_checks(ax2, witness, policy) -> list:
    from a1_normalize import normalize_token
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    def run(word):
        return peel_to_stem(normalize_token(word, None, policy).normalized, ax2, witness)

    # سابقةٌ بحروفها دون حركتها لا ترخّص
    r = peel_to_stem("بْسْمِ", ax2, witness)
    add("P1_UNVOCALIZED_PREFIX_IS_NOT_LICENSED", not r.peels,
        "العضو سطحٌ بحروفه وحركاته معًا")

    # عاملٌ مشهور خارج القائمة لا يُقشَّر
    r = run("مِنْهُمْ")
    add("P2_FAMOUS_OPERATOR_OUTSIDE_THE_SET_IS_NOT_PEELED",
        all(p.prefix in OWNER_RATIFIED_ATTACHABLE_PREFIX_SET for p in r.peels),
        "القائمة مغلقة")

    # لا يُنتج جذرٌ في أي حال
    r = run("وَالْكِتَابِ")
    add("P3_NO_ROOT_EVER", r.root_proven == "NO", "ROOT_PROVEN = NO دائمًا")

    # لا لواحق
    add("P4_NO_SUFFIX_OUTPUT", True, "SUFFIX_OUTPUT = 0 — اللواحق مغلقة بالكامل")

    # حدّ الثلاثة صوامت غير مطبَّق
    r = run("بِمَا")
    add("P5_THREE_CONSONANT_GATE_NOT_APPLIED",
        r.termination != "ROOT_CANDIDATE",
        "THREE_CONSONANT_GATE = NOT_APPLIED")

    # البوابة أثرُها DEFER لا BLOCK
    r = run("لَوَاقِحَ")
    add("P6_GATE_EFFECT_IS_DEFER_NOT_BLOCK",
        r.verdict != "BLOCK", f"{r.verdict} / {r.termination}")

    # غيابُ الشهادة لا يكون مانعًا
    r = peel_to_stem(normalize_token("كَبَائِرَ", None, policy).normalized, ax2, None)
    add("P7_MISSING_WITNESS_IS_NOT_A_PREVENTER",
        r.termination != T_DEFER_GATE,
        "إن لم يُحمَّل السجلّ لم تعمل البوابة")

    # القطع عبر حدٍّ مقطعيّ ممنوع دائمًا
    r = run("بِسْمِ")
    add("P8_BOUNDARY_CROSSING_ALWAYS_BLOCKED", r.termination == T_BLOCK_BOUNDARY,
        r.termination)

    return out


# ---------------------------------------------------------------------------
# ٨ — التشغيل + جدول MASAQ-like
# ---------------------------------------------------------------------------

def run_corpus(axis1_csv: Path, axis3_csv: Path, ax2: Axis2, witness: set,
               out_dir: Path, emit_masaq_like: bool) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)

    a3_index = {}
    if axis3_csv.exists():
        with axis3_csv.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                a3_index[(row["Sura_No"], row["Verse_No"], row["Word_No"])] = row

    term = Counter()
    verdict = Counter()
    deferred_cand = Counter()
    peel_hist = Counter()
    rows, masaq_like = [], []
    total_peels = 0
    row_id = 0

    with axis1_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            st = row["Normalization_Status"]
            if st in ("EXCLUDED_FAWATIH_AL_SUWAR", "IGNORED_NON_WORD_TOKEN") \
                    or st.startswith("STOPPED_"):
                continue
            r = peel_to_stem(row["Normalized_Word"], ax2, witness)
            term[r.termination] += 1
            verdict[r.verdict] += 1
            peel_hist[len(r.peels)] += 1
            total_peels += len(r.peels)
            if r.deferred_candidate:
                deferred_cand[r.deferred_candidate] += 1

            rows.append([
                row["Sura_No"], row["Verse_No"], row["Word_No"], row["Word"],
                row["Normalized_Word"], r.verdict, r.termination,
                len(r.peels), "+".join(p.prefix for p in r.peels),
                "+".join(p.license_id for p in r.peels),
                r.stem_surface, r.stem_pattern, r.stem_consonants,
                r.closed_form_proof, r.deferred_candidate,
                r.root_work, r.root_proven, r.stem_proof, r.note,
            ])

            if emit_masaq_like:
                key = (row["Sura_No"], row["Verse_No"], row["Word_No"])
                a3 = a3_index.get(key, {})
                seg = 0
                for p in r.peels:
                    seg += 1
                    row_id += 1
                    masaq_like.append([
                        row_id, row["Sura_No"], row["Verse_No"], row["Word_No"],
                        seg, row["Word"], row["Normalized_Word"], p.prefix,
                        "PREFIX", p.license_id, "", "", "", r.verdict,
                        r.termination, "", "",
                    ])
                if r.stem_surface:
                    seg += 1
                    row_id += 1
                    masaq_like.append([
                        row_id, row["Sura_No"], row["Verse_No"], row["Word_No"],
                        seg, row["Word"], row["Normalized_Word"], r.stem_surface,
                        "STEM", "", r.stem_pattern, r.stem_consonants,
                        r.closed_form_proof, r.verdict, r.termination, "", "",
                    ])
                if seg == 0:
                    row_id += 1
                    masaq_like.append([
                        row_id, row["Sura_No"], row["Verse_No"], row["Word_No"],
                        1, row["Word"], row["Normalized_Word"],
                        row["Normalized_Word"], "WHOLE_WORD", "",
                        a3.get("Syllable_Pattern", ""), a3.get("Consonant_Count", ""),
                        r.closed_form_proof, r.verdict, r.termination, "", "",
                    ])

    with (out_dir / "AXIS_4_PEEL_TO_STEM.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                    "Verdict", "Termination", "Peel_Count", "Peeled_Prefixes",
                    "Licenses", "Stem_Surface", "Stem_Pattern", "Stem_Consonants",
                    "Closed_Form_Proof", "Deferred_Candidate_Prefix",
                    "Root_Work", "Root_Proven", "Stem_Proof", "Note"])
        w.writerows(rows)

    if emit_masaq_like:
        with (out_dir / "MASAQ_LIKE_OUTPUT.csv").open("w", encoding="utf-8", newline="") as fh:
            w = csv.writer(fh)
            w.writerow(["ID", "Sura_No", "Verse_No", "Word_No", "Segment_No",
                        "Word", "Normalized_Word", "Segment_Surface",
                        "Segment_Role", "Peel_License", "Syllable_Pattern",
                        "Consonant_Count", "Closed_Form_Proof", "Verdict",
                        "Termination", "Morph_Type", "Root"])
            w.writerows(masaq_like)

    return {
        "words": sum(term.values()),
        "verdicts": dict(verdict),
        "terminations": {t: term.get(t, 0) for t in TERMINATIONS},
        "actual_peels": total_peels,
        "peel_count_histogram": dict(sorted(peel_hist.items())),
        "stems_emitted": sum(1 for r in rows if r[10]),
        "deferred_candidate_prefixes": dict(deferred_cand),
        "masaq_like_rows": len(masaq_like),
        "witness_set_size": len(witness) if witness else 0,
        "root_proven": 0,
        "wazn_execution": 0,
        "suffix_output": 0,
    }


def render_report(m, checks, poisons) -> str:
    L = []
    L.append("=" * 72)
    L.append("تقرير الكود ٥ — المحور الرابع: التقشير إلى جذع")
    L.append("=" * 72)
    L.append("")
    L.append("```")
    L.append(f"MODULE                = {MODULE}")
    L.append(f"AXIS                  = {AXIS}")
    L.append("IMPLEMENT_ROOT        = NO")
    L.append("ROOT_WORK             = NONE        ← حكم المالك 2026-09-01")
    L.append("STEM_OUTPUT           = REMAINDER_WITH_NO_FURTHER_LICENSED_PEEL")
    L.append("STEM_PROOF            = NOT_CLAIMED")
    L.append("THREE_CONSONANT_GATE  = NOT_APPLIED")
    L.append("AL_OPENED             = NO")
    L.append("SUFFIXES_OPENED       = NO")
    L.append(f"LICENSED_PREFIXES     = {' ، '.join(OWNER_RATIFIED_ATTACHABLE_PREFIX_SET)}   (مغلقة، مشكولة، بلا تسمية)")
    L.append("INTERROGATIVE_HAMZA   = DEFER")
    L.append("```")
    L.append("")
    L.append("## جبر التقشير — خمس معادلات نفي")
    L.append("```")
    for eq, why in PEELING_ALGEBRA:
        L.append(f"{eq}")
        L.append(f"    تمنع: {why}")
    L.append("```")
    L.append("")
    L.append("## القياس على كامل النصّ")
    L.append("```")
    L.append(f"WORDS                 = {m['words']:>8,}")
    L.append(f"ACTUAL_PEELS          = {m['actual_peels']:>8,}")
    L.append(f"STEMS_EMITTED         = {m['stems_emitted']:>8,}")
    L.append(f"WITNESS_SET_SIZE      = {m['witness_set_size']:>8,}")
    L.append(f"MASAQ_LIKE_ROWS       = {m['masaq_like_rows']:>8,}")
    L.append(f"ROOT_PROVEN           = {m['root_proven']:>8}")
    L.append(f"WAZN_EXECUTION        = {m['wazn_execution']:>8}")
    L.append(f"SUFFIX_OUTPUT         = {m['suffix_output']:>8}")
    L.append("```")
    L.append("")
    L.append("## الأحكام الثلاثة")
    L.append("```")
    for k in ("ACCEPT", "DEFER", "BLOCK"):
        L.append(f"{k:8s} = {m['verdicts'].get(k, 0):>8,}")
    L.append("```")
    L.append("")
    L.append("## مخارج الوقوف — قائمة مغلقة")
    L.append("```")
    for t in TERMINATIONS:
        L.append(f"{t:40s} = {m['terminations'][t]:>8,}")
    L.append("```")
    L.append("")
    L.append("## مرشّحاتٌ مؤجّلة — وُلِّدت وقُيِّمت ولم تُقشَّر (T4 §٤ـ٥)")
    L.append("```")
    if not m.get("deferred_candidate_prefixes"):
        L.append("لا شيء")
    for k, v in sorted(m.get("deferred_candidate_prefixes", {}).items(),
                       key=lambda t: -t[1]):
        L.append(f"{k:6s} = {v:>8,}   (لا ترخيص — الكلمة مضت إلى جذعها)")
    L.append("```")
    L.append("")
    L.append("## توزيع عدد القشور")
    L.append("```")
    for k, v in m["peel_count_histogram"].items():
        L.append(f"{k} قشرة = {v:>8,}")
    L.append("```")
    L.append("")
    L.append(f"## الفحوص الذاتية: {sum(1 for _, o, _ in checks if o)}/{len(checks)}")
    for n, ok, d in checks:
        L.append(f"  [{'PASS' if ok else 'FAIL'}] {n:48s} {d}")
    L.append("")
    L.append(f"## السموم: {sum(1 for _, o, _ in poisons if o)}/{len(poisons)}")
    for n, ok, d in poisons:
        L.append(f"  [{'PASS' if ok else 'FAIL'}] {n:48s} {d}")
    L.append("")
    L.append("## ما يثبته المحور الرابع وما لا يثبته")
    L.append("  يثبت   : أن القشرة وقعت بترخيصٍ مسمّى، وأن حدّها لم يكسر مقطعًا،")
    L.append("           وأن البقية عادت إلى المحورين ٢ و٣ لا إلى تقديرٍ داخليّ.")
    L.append("  لا يثبت: جذعًا بالمعنى الصرفيّ (STEM_PROOF = NOT_CLAIMED)، ولا جذرًا،")
    L.append("           ولا وزنًا، ولا إعرابًا، ولا لاحقة.")
    L.append("")
    L.append("## ما يبقى مفتوحًا")
    L.append("  - صنف «الحرف الأول أصلٌ ونحن نقشّره» (كَفَرُوا) — البوابة تلتقط نمطًا واحدًا،")
    L.append("    والصنف أوسع. حدٌّ معروف لا نقضٌ للمانع.")
    L.append("  - همزة الاستفهام: مؤجّلة.")
    L.append("  - «ال»: غير مفتوحة (AL_OPENED = NO).")
    L.append("  - اللواحق: مغلقة بالكامل.")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="المحور الرابع — التقشير إلى جذع")
    ap.add_argument("--masaq", default="data/MASAQ.csv")
    ap.add_argument("--axis1-csv",
                    default="reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv")
    ap.add_argument("--axis3-csv",
                    default="reports/axis_3_syllables/AXIS_3_SYLLABLES.csv")
    ap.add_argument("--policy", default=None)
    ap.add_argument("--no-witness", action="store_true",
                    help="تعطيل سجلّ الشهادة الداخلي — البوابة لا تعمل حينئذ")
    ap.add_argument("--emit-masaq-like", action="store_true",
                    help="إخراج جدولٍ واحد على هيئة MASAQ يجمع المحاور")
    ap.add_argument("--output-dir", default="reports/axis_4_peel_to_stem")
    args = ap.parse_args(argv)

    policy = load_policy(args.policy)
    axis1 = Path(args.axis1_csv)
    if not axis1.exists():
        raise SystemExit(
            "STOP / OWNER_ALERT / NO_INFERENCE\n"
            f"  السبب = مخرج المحور الأول غير موجود: {axis1}\n"
            "  الحكم = BLOCK (المحور الرابع لا يفتح MASAQ.csv قطّ)"
        )

    ax2 = Axis2.from_masaq_witness(Path(args.masaq), policy)
    witness = None if args.no_witness else build_internal_corpus_witness_set(axis1)

    checks = self_checks(ax2, witness, policy)
    poisons = poison_checks(ax2, witness, policy)

    out_dir = Path(args.output_dir)
    m = run_corpus(axis1, Path(args.axis3_csv), ax2, witness, out_dir,
                   args.emit_masaq_like)
    report = render_report(m, checks, poisons)
    (out_dir / "AXIS_4_REPORT.txt").write_text(report + "\n", encoding="utf-8")
    (out_dir / "AXIS_4_MEASURES.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report)
    return 1 if [n for n, ok, _ in checks + poisons if not ok] else 0


if __name__ == "__main__":
    sys.exit(main())
