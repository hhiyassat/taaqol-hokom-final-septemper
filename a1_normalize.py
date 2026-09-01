#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الكود ٢ — المحور الأول: التطبيع

AXIS                     = 1
MODULE                   = a1_normalize.py
OWNER_RULE_SOVEREIGNTY   = ABSOLUTE
RULE_OWNER               = DR_HUSSEIN
CREATE_NON_OWNER_RULE    = NO
INFER_LINGUISTIC_RULE    = NO
NORMALIZATION_IS_DISCLOSURE_NOT_INTERPRETATION

المسألة (T1 §١ـ١)
------------------
النصّ المشكول طبقتان: **صوتية** (حرف/حركة/سكون/مدّ) و**كتابية أدائية**
(شدّة، تطويل، علامات تجويد ووقف، صفر مستدير، ألف وصل، ألف خنجرية، ألف مقصورة، مدّة).
وكل ما بعد هذا المحور يعمل على الأولى وحدها.

فالتطبيع **فصلُ طبقةٍ عن طبقة**، لا تنظيفُ نصّ.

الواجهة التي تستدعيها المحاور التالية
--------------------------------------
    normalize_token(token, position=None) -> NormalizationResult

الحالات الخمس للمخرج (T1 §١ـ٢) — قائمة مغلقة لا سادس لها
    NORMALIZED
    NORMALIZED_OWNER_DECISION_REQUIRED
    STOPPED_OWNER_DECISION_REQUIRED_NO_CARRIER_FOR_A_HARAKA
    IGNORED_NON_WORD_TOKEN
    EXCLUDED_FAWATIH_AL_SUWAR

مصير كل خليّة (T1 §١ـ٢) — قائمة مغلقة
    PRESERVED · REPLACED · EXPANDED · IGNORED · DELETED_BY_OWNER_RULE
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

MODULE = "a1_normalize.py"
AXIS = 1

# ---------------------------------------------------------------------------
# ١ — الحروف والعلامات
# ---------------------------------------------------------------------------

FATHA, DAMMA, KASRA = "َ", "ُ", "ِ"
FATHATAN, DAMMATAN, KASRATAN = "ً", "ٌ", "ٍ"
SUKUN, SHADDA, MADDAH = "ْ", "ّ", "ٓ"
TATWEEL = "ـ"
DAGGER_ALIF = "ٰ"
ROUNDED_ZERO = "۟"
ALIF_WASLA = "ٱ"

HARAKAT = {FATHA, DAMMA, KASRA}
TANWEEN = {FATHATAN, DAMMATAN, KASRATAN}
TANWEEN_TO_HARAKA = {FATHATAN: FATHA, DAMMATAN: DAMMA, KASRATAN: KASRA}
MARKS = HARAKAT | TANWEEN | {SUKUN, SHADDA, MADDAH, DAGGER_ALIF, ROUNDED_ZERO}

ALIF, WAW, YAA, LAM, NOON = "ا", "و", "ي", "ل", "ن"
ALIF_MAQSURA = "ى"
ALEF_MADDA = "آ"
HAMZA = "ء"
HAMZA_SEATS = {"أ": FATHA, "إ": KASRA, "ؤ": None, "ئ": None}

CONSONANT_LETTERS = set(
    "ءآأؤإئابةتثج"
    "حخدذرزسشصضطظ"
    "عغفقكلمنهوىي"
    "ٱ"
)

#: حروف المدّ ومطابقة حركتها السابقة (T3 §٣ـ٤: madd = V ، madd ≠ C)
MADD_PARTNER = {ALIF: FATHA, WAW: DAMMA, YAA: KASRA}

# ---------------------------------------------------------------------------
# ٢ — الفواتح (T1 §١ـ٥) — قائمة مغلقة + شرط الموضع
# ---------------------------------------------------------------------------

#: N0.F — الشرطان معًا: السطح في القائمة **و** موضعه افتتاحيّ.
FAWATIH_SURFACES = frozenset({
    "الم", "المص", "المر", "الر", "كهيعص", "طه", "طسم", "طس",
    "يس", "ص", "حم", "عسق", "ق", "ن",
})

#: الحالة الخاصة المسجّلة في T1 §١ـ٥: عسق في 42:2:1 افتتاحٌ لأن ما قبلها حم في 42:1:1.
FAWATIH_EXTRA_POSITIONS = frozenset({(42, 2, 1)})

# ---------------------------------------------------------------------------
# ٣ — جدول القواعد المسمّاة
# ---------------------------------------------------------------------------

RULES = {
    "N0.F": "فاتحة سورة في موضع الافتتاح — تُحفظ كما كُتبت وتخرج من كل المحاور",
    "N1":   "المدّة تُحذف ولا تولّد همزةً في أي موضع",
    "N2":   "كل شدّة تُفكّ داخل كلمتها إلى ساكنٍ ومتحرّك",
    "N2.1": "شدّة على أول الكلمة بلا «ال» قبلها: علامةُ أداءٍ تُحذف ولا تُضاعف الحرف",
    "N2.2": "شدّة بعد «ال»: تعود إلى الفكّ العادي",
    "N3":   "حذف التطويل",
    "N7":   "ألف الوصل همزةٌ مع حركة، والأصل الفتح عند غياب الحركة المكتوبة",
    "N7.1": "ألفٌ مجرّدة أول الكلمة يتبعها لام وليست من الفواتح: همزةُ «ال» بفتحة",
    "N7.2": "«ال» بعد سابقةٍ داخل الكلمة: لا تُعامَل إلا بمطابقة الوحدة كلها في سجلٍّ معتمد",
    "N7.3": "ألف الوصل في رأس فعلٍ مبرهَن — معطّلة: EXECUTABLE_VERB_RULES = 0",
    "N10":  "الهمزة حرف لا حركة، ولا تُخترع من علامة",
    "N10.1": "تعيين كرسيّ الهمزة بحسب ما قبلها",
    "N12":  "كل حرفٍ حُكم بسكونه يحمل السكون صراحةً في المخرج",
    "N13":  "لا تحويل عامّ من الرسم العثماني إلى الإملائي — قرارُ إبقاء",
}

#: T1 §١ـ٤ — الفجوة المقيسة التي تعطّل N7.3
VERB_RULE_ROWS = 34
EXECUTABLE_VERB_RULES = 0

FATES = ("PRESERVED", "REPLACED", "EXPANDED", "IGNORED", "DELETED_BY_OWNER_RULE")

STATUS_NORMALIZED = "NORMALIZED"
STATUS_ODR = "NORMALIZED_OWNER_DECISION_REQUIRED"
STATUS_STOPPED = "STOPPED_OWNER_DECISION_REQUIRED_NO_CARRIER_FOR_A_HARAKA"
STATUS_IGNORED = "IGNORED_NON_WORD_TOKEN"
STATUS_FAWATIH = "EXCLUDED_FAWATIH_AL_SUWAR"


# ---------------------------------------------------------------------------
# ٤ — سياسة الأصناف غير الموثّقة
# ---------------------------------------------------------------------------

DEFAULT_POLICY_PATH = Path(__file__).with_name("data") / "axis_1_owner_policy.json"


def load_policy(path: Path | None = None) -> dict:
    p = Path(path) if path else DEFAULT_POLICY_PATH
    if not p.exists():
        raise SystemExit(
            "STOP / OWNER_ALERT / NO_INFERENCE\n"
            f"  السبب = ملف سياسة المالك غير موجود: {p}\n"
            "  الحكم = BLOCK (لا يُفترض حكمٌ في غياب الملف)"
        )
    data = json.loads(p.read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


# ---------------------------------------------------------------------------
# ٥ — نتيجة التطبيع
# ---------------------------------------------------------------------------

@dataclass
class Unit:
    """وحدةٌ صوتية: صامتٌ واحد + علامةٌ واحدة (حركة أو سكون). لا ثالث لهما."""
    letter: str
    mark: str
    rule: str
    source_index: int

    @property
    def text(self) -> str:
        return self.letter + self.mark


@dataclass
class NormalizationResult:
    token: str
    status: str
    normalized: str = ""
    units: list = field(default_factory=list)
    fates: list = field(default_factory=list)          # (idx, char, fate, rule)
    rules_applied: list = field(default_factory=list)
    owner_decisions: list = field(default_factory=list)  # (class, position, note)
    stop_reason: str = ""

    @property
    def is_usable(self) -> bool:
        """هل يمضي هذا السطح إلى المحورين ٣ و٤؟"""
        return self.status in (STATUS_NORMALIZED, STATUS_ODR)


# ---------------------------------------------------------------------------
# ٦ — التقطيع الأوّليّ: حرفٌ ثم علاماته
# ---------------------------------------------------------------------------

def _split_letters(token: str):
    """يُعيد [(index, letter, marks)] ويرفع خطأً إن سبقت علامةٌ حاملَها."""
    out = []
    i, n = 0, len(token)
    while i < n:
        ch = token[i]
        if ch in MARKS:
            raise ValueError(f"HARAKA_WITHOUT_CARRIER@{i}")
        if ch == TATWEEL:
            out.append((i, TATWEEL, ""))
            i += 1
            continue
        if ch not in CONSONANT_LETTERS:
            raise ValueError(f"NON_LETTER@{i}:{ch!r}")
        j = i + 1
        marks = ""
        while j < n and token[j] in MARKS:
            marks += token[j]
            j += 1
        out.append((i, ch, marks))
        i = j
    return out


# ---------------------------------------------------------------------------
# ٧ — التطبيع
# ---------------------------------------------------------------------------

def normalize_token(token: str, position: tuple | None = None,
                    policy: dict | None = None) -> NormalizationResult:
    """يطبّع كلمةً واحدة. ``position`` = (sura, verse, word_no) لأجل N0.F فقط."""
    policy = policy if policy is not None else load_policy()
    res = NormalizationResult(token=token, status=STATUS_NORMALIZED)

    def fate(idx, ch, f, rule):
        res.fates.append((idx, ch, f, rule))

    def use(rule):
        if rule and rule not in res.rules_applied:
            res.rules_applied.append(rule)

    def decide(cls, pos, note):
        """يستدعي سياسة صنفٍ غير موثّق ويسجّل أثرها على حالة الكلمة."""
        pol = policy.get(cls)
        if pol is None:
            raise SystemExit(
                "STOP / OWNER_ALERT / NO_INFERENCE\n"
                f"  السبب = صنفٌ لا سياسة له: {cls}\n  الحكم = BLOCK"
            )
        if not pol.get("ratified", False):
            res.owner_decisions.append((cls, pos, note))
        return pol["treatment"]

    # ---- (أ) رمزٌ ليس كلمة -------------------------------------------------
    stripped = token.strip()
    if not stripped:
        res.status = STATUS_IGNORED
        return res
    if not any(ch in CONSONANT_LETTERS for ch in stripped):
        res.status = STATUS_IGNORED
        return res

    # ---- (ب) N0.F الفواتح: السطحُ في القائمة **و** الموضعُ افتتاحيّ --------
    if stripped in FAWATIH_SURFACES and position is not None:
        s, v, w = position
        opening = (v == 1 and w == 1) or (s, v, w) in FAWATIH_EXTRA_POSITIONS
        if opening:
            res.status = STATUS_FAWATIH
            res.normalized = token          # تُحفظ كما كُتبت
            use("N0.F")
            for i, ch in enumerate(token):
                fate(i, ch, "PRESERVED", "N0.F")
            return res

    # ---- (ج) خليّةٌ فيها أكثر من كلمة -------------------------------------
    if " " in stripped:
        treat = decide("U_MULTIWORD_CELL", 0, "خليّة Word فيها كلمتان")
        if treat == "OWNER_DECISION_REQUIRED":
            res.status = STATUS_STOPPED
            res.stop_reason = "MULTIWORD_SURFACE_IN_ONE_CELL"
            return res

    # ---- (د) التقطيع الأوّليّ ----------------------------------------------
    try:
        letters = _split_letters(stripped)
    except ValueError as exc:
        msg = str(exc)
        if msg.startswith("HARAKA_WITHOUT_CARRIER"):
            res.status = STATUS_STOPPED
            res.stop_reason = msg
        else:
            res.status = STATUS_IGNORED
            res.stop_reason = msg
        return res

    units: list[Unit] = []
    n = len(letters)

    def prev_mark() -> str | None:
        return units[-1].mark if units else None

    def emit(letter, mark, rule, idx):
        units.append(Unit(letter, mark, rule, idx))

    k = 0
    while k < n:
        idx, letter, marks = letters[k]
        nxt_letter = letters[k + 1][1] if k + 1 < n else None
        nxt_marks = letters[k + 1][2] if k + 1 < n else ""
        is_first = (k == 0)
        is_last = (k == n - 1)

        # --- N3: التطويل يُحذف ------------------------------------------
        if letter == TATWEEL:
            if marks:
                # T1 §N10: همزةٌ حاملُها التطويل تُردّ حرفًا. لا يقع في هذا المدخل.
                res.status = STATUS_STOPPED
                res.stop_reason = "TATWEEL_CARRIES_MARKS_OWNER_DECISION"
                return res
            fate(idx, letter, "DELETED_BY_OWNER_RULE", "N3")
            use("N3")
            k += 1
            continue

        # --- الصفر المستدير: الحرف لا يُنطق ------------------------------
        if ROUNDED_ZERO in marks:
            fate(idx, letter, "DELETED_BY_OWNER_RULE", "N3")
            k += 1
            continue

        # --- N1: المدّة علامةٌ تُحذف ولا تولّد همزة -----------------------
        if MADDAH in marks:
            marks = marks.replace(MADDAH, "")
            fate(idx, MADDAH, "DELETED_BY_OWNER_RULE", "N1")
            use("N1")

        haraka = next((m for m in marks if m in HARAKAT), None)
        tanw = next((m for m in marks if m in TANWEEN), None)
        has_sukun = SUKUN in marks
        has_shadda = SHADDA in marks

        # --- تعدّد الحركات على حاملٍ واحد: يقف ولا يرجّح -------------------
        if sum(1 for m in marks if m in HARAKAT | TANWEEN) > 1:
            res.status = STATUS_STOPPED
            res.stop_reason = f"MULTIPLE_HARAKAT_ON_ONE_CARRIER@{idx}"
            return res

        # =================================================================
        # آ — ألف بمدّة (رمزٌ واحد = ألف + مدّة)
        # =================================================================
        if letter == ALEF_MADDA:
            treat = decide("U_ALEF_MADDA", idx, "آ = ألف + مدّة في رمزٍ واحد")
            if treat == "OWNER_DECISION_REQUIRED":
                res.status = STATUS_STOPPED
                res.stop_reason = f"ALEF_MADDA_OWNER_DECISION@{idx}"
                return res
            if treat == "HAMZA_FATHA_PLUS_MADD_ALIF":
                emit(HAMZA, FATHA, "N10+U_ALEF_MADDA", idx)
                emit(ALIF, SUKUN, "N12+U_ALEF_MADDA", idx)
                fate(idx, letter, "EXPANDED", "U_ALEF_MADDA")
                use("N10")
            else:                                     # MADDA_DELETED_ALIF_REMAINS
                emit(ALIF, SUKUN, "N1+N12", idx)
                fate(idx, letter, "REPLACED", "N1")
            use("N12")
            k += 1
            continue

        # =================================================================
        # ألف مجرّدة — أربعة مسارات لا خامس لها
        # =================================================================
        if letter in (ALIF, ALIF_WASLA) and not haraka and not tanw and not has_shadda:
            # N7.1 نصُّها في T1 §١ـ٣(ج) صريحٌ في نفي الشروط:
            #     «ولا يُشترط سكونُ اللام ولا شدّةٌ بعدها»
            # فتُطبَّق في أول الكلمة حرفيًّا: ألفٌ مجرّدة + لامٌ بعدها = همزة بفتحة.
            # وكلفةُ هذا الحرف معلومة وتُقاس: تصدُق على «الْتَقَى» و«اللَّاتِي»
            # وهما ليستا أداةَ تعريف. الكلفة تُسجَّل ولا تُطوى (انظر --cross-check-masaq).
            #
            # أمّا **داخل** الكلمة فالنصّ لا ينفي الشروط، والفاصل لازم:
            # لامُ التعريف لا تحمل حركة (مجرّدة/ساكنة/مشدّدة)، ولامٌ متحرّكة بعد
            # ألفٍ مجرّدة تعني أن الألف **مدٌّ** (مَالِكِ ، لَيَالِيَ) لا أداةَ تعريف.
            article_ahead_internal = (
                nxt_letter == LAM
                and not any(m in HARAKAT | TANWEEN for m in nxt_marks)
            )

            # N7.1 — أول الكلمة ويتبعها لام (بلا شرطٍ على اللام)
            if is_first and nxt_letter == LAM:
                emit(HAMZA, FATHA, "N7.1", idx)
                fate(idx, letter, "REPLACED", "N7.1")
                use("N7.1"); use("N10")
                k += 1
                continue

            # N7 العام — أول الكلمة، لا لام بعدها (رؤوس الأفعال تدخل هنا لتعطّل N7.3)
            if is_first:
                emit(HAMZA, FATHA, "N7", idx)
                fate(idx, letter, "REPLACED", "N7")
                use("N7")
                res.rules_applied.append("N7.3:INOPERATIVE") if "N7.3:INOPERATIVE" \
                    not in res.rules_applied else None
                k += 1
                continue

            # N7.2 — «ال» بعد سابقةٍ داخل الكلمة
            if article_ahead_internal:
                treat = decide("U_N7_2_INTERNAL_AL", idx,
                               "«ال» داخل الكلمة بعد سابقة — لا سجلّ وحداتٍ معتمد")
                if treat == "OWNER_DECISION_REQUIRED":
                    res.status = STATUS_STOPPED
                    res.stop_reason = f"N7_2_NO_APPROVED_REGISTRY@{idx}"
                    return res
                fate(idx, letter, "DELETED_BY_OWNER_RULE", "N7.2")
                use("N7.2")
                k += 1
                continue

            # مدّ — ألفٌ بعد فتحة
            if prev_mark() == FATHA:
                emit(ALIF, SUKUN, "MADD", idx)
                fate(idx, letter, "PRESERVED", "N12")
                use("N12")
                k += 1
                continue

            # ألف التفريق — بعد واو الجماعة في آخر الكلمة
            if is_last and units and units[-1].letter == WAW and units[-1].mark == SUKUN:
                treat = decide("U_ALIF_FARIQA", idx, "ألف التفريق بعد واو الجماعة")
                if treat == "DELETE":
                    fate(idx, letter, "DELETED_BY_OWNER_RULE", "U_ALIF_FARIQA")
                    k += 1
                    continue
                if treat == "OWNER_DECISION_REQUIRED":
                    res.status = STATUS_STOPPED
                    res.stop_reason = f"ALIF_FARIQA_OWNER_DECISION@{idx}"
                    return res
                emit(ALIF, SUKUN, "U_ALIF_FARIQA", idx)
                fate(idx, letter, "PRESERVED", "U_ALIF_FARIQA")
                k += 1
                continue

            # ما بقي: حاملٌ بلا حركةٍ ولا وجهٍ مدّيّ
            treat = decide("U_UNVOCALIZED_CARRIER", idx, f"ألفٌ بعد {prev_mark()!r}")
            if treat == "OWNER_DECISION_REQUIRED":
                res.status = STATUS_STOPPED
                res.stop_reason = f"UNVOCALIZED_ALIF@{idx}"
                return res
            emit(ALIF, SUKUN, "U_UNVOCALIZED_CARRIER", idx)
            fate(idx, letter, "PRESERVED", "N12")
            k += 1
            continue

        # =================================================================
        # ى — الألف المقصورة
        # =================================================================
        if letter == ALIF_MAQSURA and not haraka and not tanw:
            treat = decide("U_ALIF_MAQSURA", idx, "ألف مقصورة بلا حركة")
            if treat == "OWNER_DECISION_REQUIRED":
                res.status = STATUS_STOPPED
                res.stop_reason = f"ALIF_MAQSURA_OWNER_DECISION@{idx}"
                return res
            if treat == "MADD_ALIF":
                emit(ALIF, SUKUN, "U_ALIF_MAQSURA", idx)
                fate(idx, letter, "REPLACED", "U_ALIF_MAQSURA")
            else:
                emit(YAA, SUKUN, "U_ALIF_MAQSURA", idx)
                fate(idx, letter, "REPLACED", "U_ALIF_MAQSURA")
            use("N12")
            k += 1
            continue

        # =================================================================
        # كرسيّ الهمزة
        # =================================================================
        out_letter = letter
        if letter in HAMZA_SEATS:
            treat = decide("U_HAMZA_SEAT", idx, "كرسيّ همزة")
            if treat == "UNIFY_TO_BARE_HAMZA":
                out_letter = HAMZA
                fate(idx, letter, "REPLACED", "N10.1")
                use("N10.1")
            else:
                fate(idx, letter, "PRESERVED", "N10")
            use("N10")
        elif letter == ALIF_WASLA:
            out_letter = HAMZA

        # =================================================================
        # الحركة والسكون والشدّة والتنوين
        # =================================================================
        # التنوين أولًا: يُفكّ إلى حركةٍ + نونٍ ساكنة إن أذن المالك
        expand_tanween = False
        if tanw is not None:
            treat = decide("U_TANWEEN", idx, f"تنوين {tanw!r}")
            if treat == "OWNER_DECISION_REQUIRED":
                res.status = STATUS_STOPPED
                res.stop_reason = f"TANWEEN_OWNER_DECISION@{idx}"
                return res
            haraka = TANWEEN_TO_HARAKA[tanw]
            expand_tanween = (treat == "EXPAND_TO_NOON_SAKIN")

        # N2 — فكّ الشدّة
        if has_shadda:
            if is_first and not article_before(units):
                # N2.1 — علامة أداءٍ تُحذف ولا تُضاعف الحرف
                fate(idx, SHADDA, "DELETED_BY_OWNER_RULE", "N2.1")
                use("N2.1")
            else:
                emit(out_letter, SUKUN, "N2", idx)
                fate(idx, SHADDA, "EXPANDED", "N2.2" if article_before(units) else "N2")
                use("N2.2" if article_before(units) else "N2")

        if haraka is not None:
            emit(out_letter, haraka, "N12" if has_sukun else "SOURCE", idx)
            fate(idx, haraka, "PRESERVED", "N12")
        elif has_sukun:
            emit(out_letter, SUKUN, "N12", idx)
            fate(idx, SUKUN, "PRESERVED", "N12")
            use("N12")
        else:
            # حاملٌ بلا حركة: مدٌّ أو لينٌ أو ساكنٌ ضمنيّ
            pm = prev_mark()
            if letter in MADD_PARTNER and pm == MADD_PARTNER[letter]:
                emit(out_letter, SUKUN, "MADD", idx)     # مدّ = V (T3 §٣ـ٤)
                fate(idx, letter, "PRESERVED", "N12")
                use("N12")
            elif letter in (WAW, YAA) and pm == FATHA:
                emit(out_letter, SUKUN, "LAYN", idx)     # لين = C ساكن
                fate(idx, letter, "PRESERVED", "N12")
                use("N12")
            else:
                treat = decide("U_UNVOCALIZED_CARRIER", idx,
                               f"{letter!r} بلا حركة بعد {pm!r}")
                if treat == "OWNER_DECISION_REQUIRED":
                    res.status = STATUS_STOPPED
                    res.stop_reason = f"UNVOCALIZED_CARRIER@{idx}"
                    return res
                emit(out_letter, SUKUN, "N12", idx)      # N12: التصريح بالسكون
                fate(idx, letter, "PRESERVED", "N12")
                use("N12")

        if expand_tanween:
            emit(NOON, SUKUN, "U_TANWEEN", idx)
            fate(idx, tanw, "EXPANDED", "U_TANWEEN")

        k += 1

    res.units = units
    res.normalized = "".join(u.text for u in units)
    if not units:
        res.status = STATUS_IGNORED
        return res
    if res.owner_decisions:
        res.status = STATUS_ODR
    return res


def article_before(units) -> bool:
    """هل سبق هذا الموضعَ «ال» التعريف؟ (لتمييز N2.2 عن N2.1)"""
    if len(units) < 2:
        return False
    return units[-2].letter == HAMZA and units[-1].letter == LAM


# ---------------------------------------------------------------------------
# ٨ — السموم والفحوص
# ---------------------------------------------------------------------------

def self_checks(policy) -> list:
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    r = normalize_token("اللَّهِ", (1, 1, 2), policy)
    add("T1_ALLAH_SHADDA_UNFOLDS", r.normalized == "ءَلْلْلَهِ",
        f"{r.normalized}  (T1 §١ـ٣أ: ءَلْ + لْ + لَهِ)")

    r = normalize_token("مَا", (2, 20, 1), policy)
    add("T2_MADD_ALIF_GETS_EXPLICIT_SUKUN", r.normalized == "مَاْ",
        f"{r.normalized}  (T3 §٣ـ٤: مَاْ)")

    r = normalize_token("الم", (2, 1, 1), policy)
    add("T3_FAWATIH_EXCLUDED_AT_OPENING", r.status == STATUS_FAWATIH, r.status)

    r = normalize_token("الم", (2, 5, 3), policy)
    add("T4_FAWATIH_SURFACE_OUTSIDE_OPENING_IS_ORDINARY", r.status != STATUS_FAWATIH,
        f"{r.status} / {r.normalized}")

    r = normalize_token("عسق", (42, 2, 1), policy)
    add("T5_ASQ_AT_42_2_1_IS_OPENING", r.status == STATUS_FAWATIH, r.status)

    r = normalize_token("بِسْمِ", (1, 1, 1), policy)
    add("T6_BISMI_IS_PLAIN", r.normalized == "بِسْمِ" and r.status == STATUS_NORMALIZED,
        f"{r.normalized} / {r.status}")

    r = normalize_token("قَالَ", (2, 30, 5), policy)
    add("T7_QALA_MADD", r.normalized == "قَاْلَ", r.normalized)

    r = normalize_token("كَفَرُوا", (2, 6, 1), policy)
    add("T8_ALIF_FARIQA_DROPPED", r.normalized == "كَفَرُوْ", f"{r.normalized} / {r.status}")

    # كلُّ وحدةٍ صامتٌ + علامةٌ واحدة، لا ثالث
    r = normalize_token("الْحَمْدُ", (1, 2, 1), policy)
    ok = all(u.mark in HARAKAT | {SUKUN} for u in r.units)
    add("T9_EVERY_UNIT_IS_C_PLUS_ONE_MARK", ok, r.normalized)

    # المخرج مكتفٍ بذاته: لا حرف بلا علامة
    add("T10_NO_BARE_LETTER_IN_OUTPUT",
        all(len(u.text) == 2 for u in r.units), r.normalized)

    return out


def poison_checks(policy) -> list:
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    r = normalize_token(FATHA + "ب", None, policy)
    add("P1_HARAKA_WITHOUT_CARRIER_STOPS", r.status == STATUS_STOPPED, r.stop_reason)

    r = normalize_token("بَُ", None, policy)
    add("P2_TWO_HARAKAT_ON_ONE_CARRIER_STOPS", r.status == STATUS_STOPPED, r.stop_reason)

    r = normalize_token("123", None, policy)
    add("P3_NON_WORD_IGNORED", r.status == STATUS_IGNORED, r.status)

    r = normalize_token("", None, policy)
    add("P4_EMPTY_IGNORED", r.status == STATUS_IGNORED, r.status)

    # المدّة لا تولّد همزة (N1)
    r = normalize_token("بَ" + MADDAH, None, policy)
    add("P5_MADDAH_NEVER_CREATES_HAMZA", HAMZA not in r.normalized, r.normalized)

    # فاتحةٌ في غير موضع الافتتاح ليست فاتحة
    r = normalize_token("ن", (68, 4, 2), policy)
    add("P6_FAWATIH_REQUIRES_POSITION", r.status != STATUS_FAWATIH, r.status)

    # سطحٌ ليس في القائمة ولو كان في موضع الافتتاح
    r = normalize_token("قُلْ", (112, 1, 1), policy)
    add("P7_OPENING_POSITION_ALONE_IS_NOT_FAWATIH", r.status != STATUS_FAWATIH, r.status)

    # صنفٌ غير مصادَق يجب أن يرفع الحالة إلى ODR لا أن يمرّ صامتًا
    r = normalize_token("هُدَى", None, policy)
    add("P8_UNRATIFIED_CLASS_RAISES_ODR",
        r.status == STATUS_ODR and any(c == "U_ALIF_MAQSURA" for c, _, _ in r.owner_decisions),
        f"{r.status} / {r.normalized}")

    return out


# ---------------------------------------------------------------------------
# ٩ — التشغيل على كامل النصّ
# ---------------------------------------------------------------------------

def run_corpus(words_csv: Path, out_dir: Path, policy: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    status_count = Counter()
    rule_count = Counter()
    fate_count = Counter()
    class_count = Counter()
    stop_count = Counter()
    rows_out = []

    with words_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            pos = (int(row["Sura_No"]), int(row["Verse_No"]), int(row["Word_No"]))
            r = normalize_token(row["Word"], pos, policy)
            status_count[r.status] += 1
            for rule in r.rules_applied:
                rule_count[rule] += 1
            for _, _, f, _ in r.fates:
                fate_count[f] += 1
            for cls, _, _ in r.owner_decisions:
                class_count[cls] += 1
            if r.stop_reason:
                stop_count[r.stop_reason.split("@")[0]] += 1
            rows_out.append([
                pos[0], pos[1], pos[2], row["Word"], r.normalized, r.status,
                "|".join(sorted({c for c, _, _ in r.owner_decisions})),
                "|".join(r.rules_applied), r.stop_reason,
            ])

    with (out_dir / "AXIS_1_NORMALIZATION.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                    "Normalization_Status", "Owner_Decision_Classes",
                    "Rules_Applied", "Stop_Reason"])
        w.writerows(rows_out)

    return {
        "words": len(rows_out),
        "status": dict(status_count),
        "rules": dict(rule_count),
        "fates": dict(fate_count),
        "owner_decision_classes": dict(class_count),
        "stop_reasons": dict(stop_count),
    }


def cross_check_masaq(masaq_path: Path, policy: dict) -> dict:
    """قياسٌ مقابل المرجع — **للمقارنة لا للحكم**.

    MASAQ ليس سلطةً على قواعد المالك. الغرض من هذا القياس شيءٌ واحد:
    أن تكون كلفةُ تطبيق N7.1 حرفيًّا **معلومةً ومعلنة** كما في T4 §٤ـ٧
    (`KNOWN_COST_OF_OWNER_RULE`)، لا أن يُعدَّل الحكم لأجل المرجع.
    """
    words: dict[tuple, dict] = {}
    with masaq_path.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            k = (int(row["Sura_No"]), int(row["Verse_No"]), int(row["Word_No"]))
            e = words.setdefault(k, {"surface": row["Word"], "tags": []})
            e["tags"].append(row["Morph_Tag"])

    m = Counter()
    samples = {"engine_only": [], "reference_only": []}
    for k, e in words.items():
        r = normalize_token(e["surface"], k, policy)
        engine_al = ("N7.1" in r.rules_applied) or ("N7.2" in r.rules_applied)
        ref_al = "DET" in e["tags"]
        m[(ref_al, engine_al)] += 1
        if engine_al and not ref_al and len(samples["engine_only"]) < 6:
            samples["engine_only"].append((k, e["surface"], r.normalized))
        if ref_al and not engine_al and len(samples["reference_only"]) < 6:
            samples["reference_only"].append((k, e["surface"], r.normalized))

    return {
        "BOTH": m[(True, True)],
        "NEITHER": m[(False, False)],
        "ENGINE_ONLY_KNOWN_COST_OF_N7_1": m[(False, True)],
        "REFERENCE_ONLY_ELIDED_ALIF_GAP": m[(True, False)],
        "samples": samples,
    }


def render_report(measures, checks, poisons, policy, cross=None) -> str:
    L = []
    L.append("=" * 72)
    L.append("تقرير الكود ٢ — المحور الأول: التطبيع")
    L.append("=" * 72)
    L.append("")
    L.append("```")
    L.append(f"MODULE                 = {MODULE}")
    L.append(f"AXIS                   = {AXIS}")
    L.append("OWNER_RULE_SOVEREIGNTY = ABSOLUTE")
    L.append("CREATE_NON_OWNER_RULE  = NO")
    L.append("INFER_LINGUISTIC_RULE  = NO")
    L.append(f"NAMED_RULES            = {len(RULES)}")
    L.append(f"VERB_RULE_ROWS         = {VERB_RULE_ROWS}")
    L.append(f"EXECUTABLE_VERB_RULES  = {EXECUTABLE_VERB_RULES}   ⇒ N7.3 لا تنطبق عمليًّا")
    L.append(f"WORDS                  = {measures['words']:,}")
    L.append("```")
    L.append("")
    L.append("## الحالات الخمس — قائمة مغلقة")
    L.append("```")
    for s in (STATUS_NORMALIZED, STATUS_ODR, STATUS_STOPPED,
              STATUS_IGNORED, STATUS_FAWATIH):
        L.append(f"{s:56s} = {measures['status'].get(s, 0):>7,}")
    L.append("```")
    L.append("")
    L.append("## مصير الخلايا — قائمة مغلقة")
    L.append("```")
    for f in FATES:
        L.append(f"{f:24s} = {measures['fates'].get(f, 0):>9,}")
    L.append("```")
    L.append("")
    L.append("## القواعد المسمّاة المطبَّقة")
    L.append("```")
    for r, c in sorted(measures["rules"].items(), key=lambda t: -t[1]):
        L.append(f"{r:22s} = {c:>7,}   {RULES.get(r, '')}")
    L.append("```")
    L.append("")
    L.append("## أصنافٌ تنتظر حكم مالك (لا سند نصّيّ في T1)")
    L.append("```")
    if not measures["owner_decision_classes"]:
        L.append("لا شيء")
    for cls, c in sorted(measures["owner_decision_classes"].items(), key=lambda t: -t[1]):
        pol = policy.get(cls, {})
        L.append(f"{cls:24s} = {c:>7,}   treatment={pol.get('treatment')}  ratified={pol.get('ratified')}")
    L.append("```")
    if measures["stop_reasons"]:
        L.append("")
        L.append("## أسباب الوقوف")
        L.append("```")
        for r, c in sorted(measures["stop_reasons"].items(), key=lambda t: -t[1]):
            L.append(f"{r:48s} = {c:>7,}")
        L.append("```")
    if cross:
        L.append("")
        L.append("## قياسٌ مقابل المرجع MASAQ — للمقارنة لا للحكم")
        L.append("```")
        L.append(f"BOTH_AGREE_AL                  = {cross['BOTH']:>7,}")
        L.append(f"NEITHER                        = {cross['NEITHER']:>7,}")
        L.append(f"ENGINE_ONLY_KNOWN_COST_OF_N7_1 = {cross['ENGINE_ONLY_KNOWN_COST_OF_N7_1']:>7,}"
                 "   كلفةُ تطبيق N7.1 حرفيًّا (الْتَقَى ، اللَّاتِي ، اللَّهُمَّ)")
        L.append(f"REFERENCE_ONLY_ELIDED_ALIF_GAP = {cross['REFERENCE_ONLY_ELIDED_ALIF_GAP']:>7,}"
                 "   «ال» محذوفةُ الألف بعد لامٍ سابقة (لِلْـ) — لا يراها المحرّك")
        L.append("```")
        for k, label in (("engine_only", "المحرّك فقط"), ("reference_only", "المرجع فقط")):
            if cross["samples"][k]:
                L.append(f"  نماذج {label}:")
                for pos, surf, norm in cross["samples"][k]:
                    L.append(f"    {pos}  {surf}  →  {norm}")
    L.append("")
    L.append(f"## الفحوص الذاتية: {sum(1 for _, o, _ in checks if o)}/{len(checks)}")
    for n, ok, d in checks:
        L.append(f"  [{'PASS' if ok else 'FAIL'}] {n:44s} {d}")
    L.append("")
    L.append(f"## السموم: {sum(1 for _, o, _ in poisons if o)}/{len(poisons)}")
    for n, ok, d in poisons:
        L.append(f"  [{'PASS' if ok else 'FAIL'}] {n:44s} {d}")
    L.append("")
    L.append("## ما يثبته المحور الأول وما لا يثبته (T1 §١ـ٦)")
    L.append("  يثبت   : أن كل تغيير مأذون، ومسجَّل، وقابل لإعادة البناء إلى الأصل.")
    L.append("  لا يثبت: أن الشكل المطبّع هو النطق الصحيح. هو تمثيلٌ متّسق للمطابقة والتقطيع.")
    L.append("  جبر    : NORMALIZED_SURFACE_PRODUCED ≠ NORMALIZED_SURFACE_OWNER_AUTHORIZED")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="المحور الأول — التطبيع")
    ap.add_argument("--words", default="reports/axis_0_quran_build/QURAN_WORDS.csv")
    ap.add_argument("--policy", default=None)
    ap.add_argument("--output-dir", default="reports/axis_1_normalization")
    ap.add_argument("--cross-check-masaq", default=None,
                    help="مسار MASAQ.csv لقياس الكلفة مقابل المرجع (لا يغيّر أي حكم)")
    args = ap.parse_args(argv)

    policy = load_policy(args.policy)
    checks = self_checks(policy)
    poisons = poison_checks(policy)

    words_csv = Path(args.words)
    if not words_csv.exists():
        raise SystemExit(
            "STOP / OWNER_ALERT / NO_INFERENCE\n"
            f"  السبب = جدول الكلمات غير موجود: {words_csv}\n"
            "  الحلّ  = شغّل a0_build_quran_from_masaq.py أولًا\n  الحكم = BLOCK"
        )
    out_dir = Path(args.output_dir)
    measures = run_corpus(words_csv, out_dir, policy)

    cross = None
    if args.cross_check_masaq:
        cross = cross_check_masaq(Path(args.cross_check_masaq), policy)
        measures["masaq_cross_check"] = {k: v for k, v in cross.items() if k != "samples"}

    report = render_report(measures, checks, poisons, policy, cross)
    (out_dir / "AXIS_1_REPORT.txt").write_text(report + "\n", encoding="utf-8")
    (out_dir / "AXIS_1_MEASURES.json").write_text(
        json.dumps(measures, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report)
    return 1 if [n for n, ok, _ in checks + poisons if not ok] else 0


if __name__ == "__main__":
    sys.exit(main())
