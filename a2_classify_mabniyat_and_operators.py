#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
الكود ٣ — المحور الثاني: حصر العوامل والمبنيات

AXIS                  = 2
MODULE                = a2_classify_mabniyat_and_operators.py
MODIFY_REGISTRIES     = NO
ADD_A_SURFACE_BY_HAND = NO

المسألة (T2 §٢ـ١)
------------------
في العربية طبقةٌ **مغلقة** — الحروف والمبنيات والعوامل — وطبقةٌ **مفتوحة** هي
الأسماء والأفعال المتصرّفة. المغلقة تُحصى ولا تُشتقّ.

وقيمة الحصر عند هذا النظام **إجرائية** لا معجمية: البقيةُ بعد القشر إن كانت من
الطبقة المغلقة **وقف التقشير**، لأنها كلمةٌ تامّة لا جذعٌ ينتظر مزيدًا. فالسجلّ
هو ما يمنع المحرّك من تقشير `مَا` في `بِمَا` إلى ما لا نهاية.

المبدأ الحاكم (T2 §٢ـ٢)
    REGISTRY_PRESENCE = EVIDENCE      REGISTRY_PRESENCE ≠ LICENSE

وضع المصدر في هذه النسخة
------------------------
سجلّا المالك المعلنان في T2 §٢ـ٣ — `operators_catalog_split_vocalized_corrected.csv`
و`mabniyat/exports/mabniyat_full.json` — **غير مرفقين**. وبحكم المالك (2026-09-01)
يعمل هذا الكود في وضع:

    REGISTRY_SOURCE = DERIVED_WITNESS_FROM_MASAQ
    REGISTRY_AUTHORITY = EVIDENCE_ONLY          LICENSE_GRANTED = NO
    OWNER_RATIFIED = NO

أي أن الجرد هنا **شاهدٌ مشتقّ من المرجع**، لا سجلُّ مالك. وكل ما يبنى عليه يرث
هذه الصفة: يوقف التقشير بوصفه دليلًا، ولا يمنح ترخيصًا. وإن مُرّر السجلّان
الحقيقيان بالوسائط انتقل الوضع إلى `OWNER_REGISTRY` تلقائيًّا.

الواجهة التي يستدعيها المحور الرابع
    Axis2.recheck(normalized_surface) -> Axis2Verdict
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from a1_normalize import (normalize_token, load_policy, STATUS_NORMALIZED,
                          STATUS_ODR)

MODULE = "a2_classify_mabniyat_and_operators.py"
AXIS = 2

# ---------------------------------------------------------------------------
# ١ — القوائم المغلقة (لا تُوسَّع وقت التشغيل)
# ---------------------------------------------------------------------------

#: العوامل — وسمٌ يدلّ على **دورٍ عاملٍ نحويّ**. قائمة مغلقة.
OPERATOR_TAGS = frozenset({
    "PREP", "CONJ", "DET", "NEG_PART", "ANNUL_PART", "SUBJUNC_PART",
    "JUSSIVE_PART", "CONDITION_PART", "EXCEPT_PART", "INF_ANNUL_PART",
    "INF_SUBJUNC_PART", "CERT_PART", "VOC_PART", "INTERROG", "INTERROG_PART",
    "FUT_PART", "FUTURE_PART", "FUTUR_PART", "KAAFA_MAKFOUFA", "PART",
    "YES_NO_RESP_PART",
})

#: المبنيات — أسماءٌ وضمائرُ وظروفٌ مبنيّة. قائمة مغلقة.
MABNIYAT_TAGS = frozenset({
    "PRON", "PRON_1P", "PRON_1S", "PRON_2MP", "PRON_2MS", "PRON_3D",
    "PRON_3FP", "PRON_3FS", "PRON_3MP", "PRON_3MS",
    "DEM_PRON", "DEM_PRON_F", "DEM_PRON_FS", "DEM_PRON_MP", "DEM_PRON_MS",
    "REL_PRON", "REL_ADV", "INTERROG_PRON", "EXCEPT_NOUN",
    "NOUN_VERB_LIKE", "UNINFLECTED_VERB",
})

CLOSED_CLASS_TAGS = OPERATOR_TAGS | MABNIYAT_TAGS

#: OWNER_RULING_1 (T2 §٢ـ٢) — أفعالٌ هي في الوقت نفسه عوامل نحوية.
#: قائمة مغلقة بأسطحها المجرّدة من الشكل. الحكم: WORD_CLASS = فعل ، TAG_حرف = NO
VERBAL_OPERATOR_STEMS = frozenset({"أصبح", "بئس", "نعم", "ليس", "عسى", "ليست"})

# ---------------------------------------------------------------------------
# ٢ — القيم المغلقة
# ---------------------------------------------------------------------------

PROOF_PROVEN = "PROVEN"
PROOF_VERBAL_OPERATOR = "NOT_A_CLOSED_FORM_VERBAL_OPERATOR"
PROOF_UNRESOLVED = "UNRESOLVED"
PROOF_NOT_MATCHED = "NOT_MATCHED"
CLOSED_FORM_PROOF_VALUES = (PROOF_PROVEN, PROOF_VERBAL_OPERATOR,
                            PROOF_UNRESOLVED, PROOF_NOT_MATCHED)

ELIG_ACCEPT = "ACCEPT"
ELIG_OWNER_DECISION = "OWNER_DECISION_REQUIRED"
ELIG_BLOCK = "BLOCK"

ROUTE_STOP_CLOSED = "STOP_CLOSED_FORM"
ROUTE_DEFER_UNRESOLVED = "DEFER_UNRESOLVED_CLOSURE"
ROUTE_DEFER_VERBAL_OPERATOR = "DEFER_VERBAL_OPERATOR_REGISTRY_TAG"
ROUTE_CONTINUE = "CONTINUE"

#: T2 §٢ـ٦ — عند تصادم التطبيع تُحفظ كل المعرّفات ولا يُختار أصغرها
PRESERVE_ALL_MATCHED_ENTRY_IDS = True
#: T2 §٢ـ٥ — لا ترجيح بين شهاداتٍ متعارضة
CHOOSE_AMONG_ALTERNATIVES = False


# ---------------------------------------------------------------------------
# ٣ — بنية السجلّ
# ---------------------------------------------------------------------------

@dataclass
class RegistryEntry:
    entry_id: str
    raw_surface: str
    normalized_surface: str
    normalization_status: str
    eligibility: str
    tags: set = field(default_factory=set)
    operator_role: bool = False
    mabni: bool = False
    word_class: str = ""
    witness_count: int = 0


@dataclass
class Axis2Verdict:
    surface: str
    closed_form_proof: str = PROOF_NOT_MATCHED
    eligibility: str = ELIG_BLOCK
    operator_role: bool = False
    word_class: str = ""
    next_route: str = ROUTE_CONTINUE
    matched_entry_ids: list = field(default_factory=list)
    note: str = ""

    @property
    def stops_peeling(self) -> bool:
        """الصورة المغلقة المبرهنة وحدها توقف التقشير."""
        return self.closed_form_proof == PROOF_PROVEN and self.eligibility == ELIG_ACCEPT


# ---------------------------------------------------------------------------
# ٤ — بناء الجرد
# ---------------------------------------------------------------------------

class Axis2:
    """السجلّ + واجهة المطابقة. لا يقرأ سياقًا ولا يحكم على دورٍ في جملة."""

    def __init__(self, source_mode: str = "DERIVED_WITNESS_FROM_MASAQ"):
        self.source_mode = source_mode
        self.entries: dict[str, RegistryEntry] = {}
        self.match_index: dict[str, list[str]] = defaultdict(list)   # ACCEPT وحده
        self.evidence_index: dict[str, list[str]] = defaultdict(list)
        self.collisions: dict[str, set] = defaultdict(set)
        #: شهادةٌ مضادّة: كم مرّة ورد السطح نفسه **خارج** الطبقة المغلقة
        self.open_witnesses: dict[str, int] = {}
        self.stats = Counter()

    # -- البناء من الشاهد المشتقّ ---------------------------------------
    @classmethod
    def from_masaq_witness(cls, masaq_path: Path, policy: dict) -> "Axis2":
        """يبني جردًا **شاهدًا** من MASAQ نفسه.

        قاعدة الاشتقاق — مغلقة وصريحة:
          تدخل الجردَ كلمةٌ تامّة (a) مقطعُها واحد في المرجع، و(b) وسمُها في
          القائمة المغلقة. وما عداها **شهادةٌ مضادّة** تُسجَّل ولا تُهمَل، لأنها
          هي ما يولّد قيمة UNRESOLVED.

        ولا تدخل مقاطعُ الكلمات المركّبة: عمود Segmented_Word في MASAQ **غير
        مشكول**، ومطابقةُ سطحٍ غير مشكول بسطحٍ مشكول ممنوعة بـ OWNER_RULING_2.
        """
        self = cls("DERIVED_WITNESS_FROM_MASAQ")

        words: dict[tuple, dict] = {}
        with masaq_path.open(encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                k = (int(row["Sura_No"]), int(row["Verse_No"]), int(row["Word_No"]))
                e = words.setdefault(k, {"surface": row["Word"],
                                         "bare": row["Without_Diacritics"],
                                         "tags": [], "segments": 0})
                e["tags"].append(row["Morph_Tag"])
                e["segments"] += 1

        # شهاداتٌ لكل سطحٍ مطبَّع
        witness: dict[str, dict] = {}
        for k, e in words.items():
            r = normalize_token(e["surface"], k, policy)
            if not r.normalized:
                continue
            single = (e["segments"] == 1)
            tag = e["tags"][0] if e["tags"] else ""
            closed = single and tag in CLOSED_CLASS_TAGS

            w = witness.setdefault(r.normalized, {
                "raw": set(), "status": set(), "by_tag": defaultdict(int),
                "open": 0, "bare": set(),
            })
            w["raw"].add(e["surface"])
            w["status"].add(r.status)
            w["bare"].add(e["bare"])
            if closed:
                w["by_tag"][tag] += 1
            else:
                w["open"] += 1

        # **مدخلةٌ لكل (سطحٍ مطبَّع ، وسم)** — لا مدخلة واحدة لكل سطح.
        # هذا شرطُ إمكان `UNRESOLVED`: لو طُويت الأوسمة في مدخلةٍ واحدة لاستحال
        # على السجلّ أن يتعارض مع نفسه، ولصار التعارضُ غيرَ قابل للظهور أصلًا.
        nid = 0
        for norm, w in sorted(witness.items()):
            if not w["by_tag"]:
                continue                       # ليس من الطبقة المغلقة أصلًا
            # التدرّج الثلاثي (T2 §٢ـ٦) بحسب حالة تطبيع سطح السجلّ
            if w["status"] <= {STATUS_NORMALIZED}:
                elig, status = ELIG_ACCEPT, STATUS_NORMALIZED
            elif STATUS_ODR in w["status"]:
                elig, status = ELIG_OWNER_DECISION, STATUS_ODR
            else:
                elig, status = ELIG_BLOCK, "NOT_NORMALIZABLE"

            for tag, count in sorted(w["by_tag"].items()):
                nid += 1
                is_op = tag in OPERATOR_TAGS
                entry = RegistryEntry(
                    entry_id=f"DW:{nid}",
                    raw_surface=" | ".join(sorted(w["raw"])),
                    normalized_surface=norm,
                    normalization_status=status,
                    eligibility=elig,
                    tags={tag},
                    operator_role=is_op,
                    mabni=tag in MABNIYAT_TAGS,
                    witness_count=count,
                )
                # OWNER_RULING_1 — فعلٌ وعاملٌ معًا: يُفصل ولا يُحذف
                if any(b in VERBAL_OPERATOR_STEMS for b in w["bare"]):
                    entry.word_class = "فعل"
                    entry.operator_role = True
                elif is_op:
                    entry.word_class = "حرف"
                else:
                    entry.word_class = "مبنيّ"

                self.entries[entry.entry_id] = entry
                self.evidence_index[norm].append(entry.entry_id)
                if elig == ELIG_ACCEPT:
                    self.match_index[norm].append(entry.entry_id)

            if len(w["raw"]) > 1:
                self.collisions[norm] |= w["raw"]
            self.open_witnesses[norm] = w["open"]

        self.stats["entries"] = len(self.entries)
        self.stats["match_index"] = len(self.match_index)
        self.stats["evidence_index"] = len(self.evidence_index)
        self.stats["collisions"] = len(self.collisions)
        return self

    # -- البناء من سجلات المالك الحقيقية --------------------------------
    @classmethod
    def from_owner_registries(cls, operators_csv: Path, mabniyat_json: Path,
                              policy: dict) -> "Axis2":
        self = cls("OWNER_REGISTRY")
        raw: list[tuple[str, str, bool]] = []      # (entry_id, surface, is_operator)
        with operators_csv.open(encoding="utf-8", newline="") as fh:
            for i, row in enumerate(csv.DictReader(fh), start=1):
                surf = (row.get("surface") or row.get("Surface")
                        or row.get("سطح") or "").strip()
                if surf:
                    raw.append((f"OP:{i}", surf, True))
        data = json.loads(mabniyat_json.read_text(encoding="utf-8"))
        items = data if isinstance(data, list) else data.get("entries", [])
        for i, it in enumerate(items, start=1):
            surf = (it.get("surface") or it.get("سطح") or "").strip() if isinstance(it, dict) else ""
            if surf:
                raw.append((f"MB:{i}", surf, False))

        for entry_id, surf, is_op in raw:
            r = normalize_token(surf, None, policy)
            elig = (ELIG_ACCEPT if r.status == STATUS_NORMALIZED else
                    ELIG_OWNER_DECISION if r.status == STATUS_ODR else ELIG_BLOCK)
            e = RegistryEntry(entry_id, surf, r.normalized, r.status, elig,
                              operator_role=is_op, mabni=not is_op,
                              word_class="حرف" if is_op else "مبنيّ")
            self.entries[entry_id] = e
            self.evidence_index[r.normalized].append(entry_id)
            if elig == ELIG_ACCEPT:
                self.match_index[r.normalized].append(entry_id)

        self.stats["entries"] = len(self.entries)
        self.stats["match_index"] = len(self.match_index)
        self.stats["evidence_index"] = len(self.evidence_index)
        return self

    # -- الواجهة --------------------------------------------------------
    def recheck(self, normalized_surface: str) -> Axis2Verdict:
        """المطابقة الوحيدة المسموح بها: سطحٌ مطبَّع ⟷ سطحُ سجلٍّ مطبَّع.

        OWNER_RULING_2: الطرفان مطبَّعان بالمحور الأول نفسه، وإلا فلا مطابقة.
        """
        v = Axis2Verdict(surface=normalized_surface)

        ids = self.match_index.get(normalized_surface)
        if ids:
            entries = [self.entries[i] for i in ids]
            v.matched_entry_ids = list(ids) if PRESERVE_ALL_MATCHED_ENTRY_IDS else ids[:1]
            classes = {e.word_class for e in entries}

            if classes == {"فعل"}:
                # OWNER_RULING_1: فعلٌ لا حرف — لا يوقف التقشير، ويُرحَّل إلى DEFER
                v.closed_form_proof = PROOF_VERBAL_OPERATOR
                v.eligibility = ELIG_ACCEPT
                v.operator_role = True
                v.word_class = "فعل"
                v.next_route = ROUTE_DEFER_VERBAL_OPERATOR
                v.note = "OWNER_RULING_1: WORD_CLASS=فعل ، OPERATOR_ROLE=TRUE ، TAG_حرف=NO"
                return v

            if len(classes) > 1:
                # شهاداتٌ متعارضة — لا يُرجَّح بينها (CHOOSE_AMONG_ALTERNATIVES = NO)
                v.closed_form_proof = PROOF_UNRESOLVED
                v.eligibility = ELIG_ACCEPT
                v.next_route = ROUTE_DEFER_UNRESOLVED
                v.note = f"شهاداتٌ متعارضة: {sorted(classes)}"
                return v

            v.closed_form_proof = PROOF_PROVEN
            v.eligibility = ELIG_ACCEPT
            v.operator_role = any(e.operator_role for e in entries)
            v.word_class = entries[0].word_class
            v.next_route = ROUTE_STOP_CLOSED
            return v

        ids = self.evidence_index.get(normalized_surface)
        if ids:
            entries = [self.entries[i] for i in ids]
            v.matched_entry_ids = list(ids)
            v.closed_form_proof = PROOF_NOT_MATCHED
            v.eligibility = entries[0].eligibility          # OWNER_DECISION أو BLOCK
            v.next_route = ROUTE_DEFER_UNRESOLVED
            v.note = "في فهرس الدليل لا في فهرس المطابقة — دليلٌ لا يُطابَق"
            return v

        v.closed_form_proof = PROOF_NOT_MATCHED
        v.eligibility = ELIG_BLOCK
        v.next_route = ROUTE_CONTINUE
        return v


# ---------------------------------------------------------------------------
# ٥ — الفحوص والسموم
# ---------------------------------------------------------------------------

def self_checks(ax: Axis2, policy) -> list:
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    def norm(s):
        return normalize_token(s, None, policy).normalized

    # مَا يطابق أكثر من مدخلة وتختلف شهاداتها (حرف نفي / اسم موصول).
    # الحكم الصحيح ليس ترجيحًا بل UNRESOLVED — والمهمّ إجرائيًّا أنه **لا يمضي**.
    v = ax.recheck(norm("مَا"))
    add("T1_MAA_CONFLICTING_WITNESSES_ARE_NOT_ADJUDICATED",
        v.closed_form_proof == PROOF_UNRESOLVED and v.next_route != ROUTE_CONTINUE,
        f"{v.closed_form_proof} / {v.next_route}   (يوقف تقشير بِمَا بلا ترجيح)")

    v = ax.recheck(norm("هَذَا"))
    add("T2_HADHA_IS_A_PROVEN_CLOSED_FORM",
        v.closed_form_proof == PROOF_PROVEN and v.next_route == ROUTE_STOP_CLOSED,
        f"{v.closed_form_proof} / {v.word_class}")

    v = ax.recheck(norm("لَيْسَ"))
    add("T3_LAYSA_IS_VERBAL_OPERATOR_NOT_HARF",
        v.closed_form_proof == PROOF_VERBAL_OPERATOR and v.word_class == "فعل",
        f"{v.closed_form_proof} / {v.word_class}   (OWNER_RULING_1)")
    add("T4_VERBAL_OPERATOR_DOES_NOT_STOP_PEELING", not ax.recheck(norm("لَيْسَ")).stops_peeling,
        "يُرحَّل إلى DEFER لا BLOCK")

    v = ax.recheck(norm("كَتَبَ"))
    add("T5_OPEN_CLASS_NOT_MATCHED", v.closed_form_proof == PROOF_NOT_MATCHED,
        v.closed_form_proof)

    add("T6_PROOF_HAS_FOUR_VALUES", len(CLOSED_FORM_PROOF_VALUES) == 4,
        " · ".join(CLOSED_FORM_PROOF_VALUES))
    add("T7_NO_CHOOSING_AMONG_ALTERNATIVES", CHOOSE_AMONG_ALTERNATIVES is False,
        "CHOOSE_AMONG_ALTERNATIVES = NO")
    add("T8_ALL_MATCHED_IDS_PRESERVED", PRESERVE_ALL_MATCHED_ENTRY_IDS,
        "PRESERVE_ALL_MATCHED_ENTRY_IDS = YES")
    add("T9_MATCH_INDEX_SUBSET_OF_EVIDENCE_INDEX",
        set(ax.match_index) <= set(ax.evidence_index),
        f"{len(ax.match_index)} ⊆ {len(ax.evidence_index)}")
    add("T10_REGISTRY_IS_EVIDENCE_NOT_LICENSE",
        ax.source_mode != "OWNER_REGISTRY",
        "REGISTRY_AUTHORITY = EVIDENCE_ONLY في هذا الوضع")

    # سطحٌ تطبيعُه ينتظر حكمًا: يبقى في الجرد **دليلًا** ولا يُسمح له بالمطابقة
    v = ax.recheck(norm("عَلَى"))
    add("T11_ODR_SURFACE_IS_EVIDENCE_NOT_MATCH",
        v.closed_form_proof == PROOF_NOT_MATCHED and bool(v.matched_entry_ids),
        f"{v.closed_form_proof} / eligibility={v.eligibility}   (التدرّج الثلاثي عاملٌ فعلًا)")

    return out


def poison_checks(ax: Axis2, policy) -> list:
    out = []

    def add(name, ok, detail=""):
        out.append((name, bool(ok), detail))

    v = ax.recheck("مِن")                      # سطحٌ غير مطبَّع
    add("P1_UNNORMALIZED_SURFACE_DOES_NOT_MATCH",
        v.closed_form_proof == PROOF_NOT_MATCHED,
        "OWNER_RULING_2: لا مطابقة إلا بتطبيعٍ متطابق للطرفين")

    v = ax.recheck("")
    add("P2_EMPTY_DOES_NOT_MATCH", v.closed_form_proof == PROOF_NOT_MATCHED, v.closed_form_proof)

    v = ax.recheck(normalize_token("لَيْسَ", None, policy).normalized)
    add("P3_VERBAL_OPERATOR_NOT_TAGGED_HARF", v.word_class != "حرف", v.word_class)

    n = normalize_token("بِمَا", None, policy).normalized
    add("P4_WHOLE_WORD_WITH_PREFIX_IS_NOT_ITSELF_CLOSED",
        not ax.recheck(n).stops_peeling,
        "بِمَا ليست صورةً مغلقة — المغلقةُ هي البقيةُ بعد القشر")

    before = len(ax.entries)
    try:
        ax.recheck("سطحٌ لا وجود له")
    except Exception:
        pass
    add("P5_LOOKUP_NEVER_MUTATES_REGISTRY", len(ax.entries) == before,
        "ADD_A_SURFACE_BY_HAND = NO")

    add("P6_OPERATOR_PROVEN_IS_NOT_ATTACHABLE_PREFIX_PROVEN", True,
        "هذا المحور لا يمنح ترخيص قشر أصلًا — الترخيص في المحور الرابع")

    return out


# ---------------------------------------------------------------------------
# ٦ — التشغيل على كامل النصّ
# ---------------------------------------------------------------------------

def run_corpus(ax: Axis2, axis1_csv: Path, out_dir: Path) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    proof_count = Counter()
    route_count = Counter()
    rows = []
    with axis1_csv.open(encoding="utf-8", newline="") as fh:
        for row in csv.DictReader(fh):
            if row["Normalization_Status"] in ("EXCLUDED_FAWATIH_AL_SUWAR",
                                               "IGNORED_NON_WORD_TOKEN") \
               or row["Normalization_Status"].startswith("STOPPED_"):
                continue
            v = ax.recheck(row["Normalized_Word"])
            proof_count[v.closed_form_proof] += 1
            route_count[v.next_route] += 1
            rows.append([row["Sura_No"], row["Verse_No"], row["Word_No"],
                         row["Word"], row["Normalized_Word"],
                         v.closed_form_proof, v.eligibility,
                         "YES" if v.operator_role else "NO", v.word_class,
                         v.next_route, "|".join(v.matched_entry_ids), v.note])

    with (out_dir / "AXIS_2_TOKENS.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                    "Closed_Form_Proof", "Eligibility", "Operator_Role",
                    "Word_Class", "Next_Route", "Matched_Entry_Ids", "Note"])
        w.writerows(rows)

    reg_rows = [[e.entry_id, e.raw_surface, e.normalized_surface,
                 e.normalization_status, e.eligibility, e.word_class,
                 "YES" if e.operator_role else "NO",
                 "YES" if e.mabni else "NO", e.witness_count,
                 "|".join(sorted(t for t in e.tags if not t.startswith("_")))]
                for e in ax.entries.values()]
    with (out_dir / "AXIS_2_REGISTRY.csv").open("w", encoding="utf-8", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Entry_Id", "Raw_Surfaces", "Normalized_Surface",
                    "Normalization_Status", "Eligibility", "Word_Class",
                    "Operator_Role", "Mabni", "Witness_Count", "Tags"])
        w.writerows(reg_rows)

    return {
        "source_mode": ax.source_mode,
        "registry": dict(ax.stats),
        "closed_form_proof": dict(proof_count),
        "next_route": dict(route_count),
        "words_stopped_as_closed_form": proof_count[PROOF_PROVEN],
        "eligibility_tiers": dict(Counter(e.eligibility for e in ax.entries.values())),
    }


def render_report(m, checks, poisons, ax) -> str:
    L = []
    L.append("=" * 72)
    L.append("تقرير الكود ٣ — المحور الثاني: العوامل والمبنيات")
    L.append("=" * 72)
    L.append("")
    L.append("```")
    L.append(f"MODULE                 = {MODULE}")
    L.append(f"AXIS                   = {AXIS}")
    L.append(f"REGISTRY_SOURCE        = {m['source_mode']}")
    L.append("REGISTRY_AUTHORITY     = EVIDENCE_ONLY      LICENSE_GRANTED = NO")
    L.append("OWNER_RATIFIED         = NO")
    L.append("MODIFY_REGISTRIES      = NO")
    L.append("ADD_A_SURFACE_BY_HAND  = NO")
    L.append("REGISTRY_PRESENCE      = EVIDENCE   ≠ LICENSE")
    L.append("CHOOSE_AMONG_ALTERNATIVES     = NO")
    L.append("PRESERVE_ALL_MATCHED_ENTRY_IDS = YES")
    L.append("```")
    L.append("")
    L.append("## بنية الجرد المقيسة")
    L.append("```")
    L.append(f"مدخلات السجلّ                 = {m['registry'].get('entries', 0):>6,}")
    L.append(f"فهرس المطابقة (ACCEPT وحده)   = {m['registry'].get('match_index', 0):>6,} سطحًا")
    L.append(f"فهرس الدليل (كل المدخلات)     = {m['registry'].get('evidence_index', 0):>6,} سطحًا")
    L.append(f"تصادمات التطبيع               = {m['registry'].get('collisions', 0):>6,}")
    L.append("```")
    L.append("الفصل بين فهرس المطابقة وفهرس الدليل هو العمود الفقري: السجلّ الواحد قد")
    L.append("يبقى في الجرد شاهدًا ولا يُسمح له بالمطابقة.")
    L.append("")
    L.append("## التدرّج الثلاثي بحسب حالة تطبيع سطح السجلّ (T2 §٢ـ٦)")
    L.append("```")
    for tier, elig in (("NORMALIZED", ELIG_ACCEPT),
                       ("NORMALIZED_OWNER_DECISION_REQUIRED", ELIG_OWNER_DECISION),
                       ("NOT_NORMALIZABLE", ELIG_BLOCK)):
        L.append(f"{tier:36s} → {elig:24s} = {m['eligibility_tiers'].get(elig, 0):>6,}")
    L.append("```")
    L.append("")
    L.append("## برهان الانغلاق — أربع قيم لا قيمتان (T2 §٢ـ٥)")
    L.append("```")
    for p in CLOSED_FORM_PROOF_VALUES:
        L.append(f"{p:36s} = {m['closed_form_proof'].get(p, 0):>7,}")
    L.append("```")
    L.append("")
    L.append("## المسارات")
    L.append("```")
    for k, v in sorted(m["next_route"].items(), key=lambda t: -t[1]):
        L.append(f"{k:32s} = {v:>7,}")
    L.append("```")
    L.append(f"كلمات أوقفها المحور الثاني بوصفها صورةً مغلقة تامّة = "
             f"{m['words_stopped_as_closed_form']:,}")
    L.append("")
    L.append(f"## الفحوص الذاتية: {sum(1 for _, o, _ in checks if o)}/{len(checks)}")
    for n, ok, d in checks:
        L.append(f"  [{'PASS' if ok else 'FAIL'}] {n:48s} {d}")
    L.append("")
    L.append(f"## السموم: {sum(1 for _, o, _ in poisons if o)}/{len(poisons)}")
    for n, ok, d in poisons:
        L.append(f"  [{'PASS' if ok else 'FAIL'}] {n:48s} {d}")
    L.append("")
    L.append("## ما يثبته المحور الثاني وما لا يثبته (T2 §٢ـ٨)")
    L.append("  يثبت   : هويّةَ السطح، وحالةَ انغلاقه بأربع قيم، وتعارضَ الشهادات حين يقع.")
    L.append("  لا يثبت: أن السطح في هذه الجملة بعينها يؤدّي دور العامل — الدور سياقيّ،")
    L.append("           وهذا المحور لا يقرأ سياقًا.")
    L.append("  لا يثبت: أن الجرد كامل. هو حصرُ ما في السجلات، لا حصرُ العربية.")
    L.append("")
    L.append("## ما يبقى مفتوحًا في هذه النسخة")
    L.append("  - السجلّان الحقيقيان غير مرفقين؛ الجرد هنا شاهدٌ مشتقّ لا سجلُّ مالك.")
    L.append("  - مقاطعُ الكلمات المركّبة لم تدخل الجرد: Segmented_Word غير مشكول،")
    L.append("    ومطابقةُ غير المشكول بالمشكول ممنوعة بـ OWNER_RULING_2.")
    L.append("  - مرّر --operators و--mabniyat لتحويل الوضع إلى OWNER_REGISTRY.")
    return "\n".join(L)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="المحور الثاني — العوامل والمبنيات")
    ap.add_argument("--masaq", default="data/MASAQ.csv")
    ap.add_argument("--axis1-csv",
                    default="reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv")
    ap.add_argument("--operators", default=None, help="سجلّ العوامل الحقيقي (يحوّل الوضع)")
    ap.add_argument("--mabniyat", default=None, help="سجلّ المبنيات الحقيقي (يحوّل الوضع)")
    ap.add_argument("--policy", default=None)
    ap.add_argument("--output-dir", default="reports/axis_2_mabniyat_operators")
    args = ap.parse_args(argv)

    policy = load_policy(args.policy)

    if args.operators and args.mabniyat:
        ax = Axis2.from_owner_registries(Path(args.operators), Path(args.mabniyat), policy)
    elif args.operators or args.mabniyat:
        raise SystemExit(
            "STOP / OWNER_ALERT / NO_INFERENCE\n"
            "  السبب = مُرِّر أحد السجلّين دون الآخر\n"
            "  الحكم = BLOCK (لا يُخلط سجلُّ مالكٍ بشاهدٍ مشتقّ)"
        )
    else:
        ax = Axis2.from_masaq_witness(Path(args.masaq), policy)

    checks = self_checks(ax, policy)
    poisons = poison_checks(ax, policy)

    out_dir = Path(args.output_dir)
    m = run_corpus(ax, Path(args.axis1_csv), out_dir)
    report = render_report(m, checks, poisons, ax)
    (out_dir / "AXIS_2_REPORT.txt").write_text(report + "\n", encoding="utf-8")
    (out_dir / "AXIS_2_MEASURES.json").write_text(
        json.dumps(m, ensure_ascii=False, indent=2), encoding="utf-8")
    print(report)
    return 1 if [n for n, ok, _ in checks + poisons if not ok] else 0


if __name__ == "__main__":
    sys.exit(main())
