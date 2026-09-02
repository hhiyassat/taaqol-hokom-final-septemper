"""المحور ٢ — حصر العوامل والمبنيات.

    MODIFY_REGISTRIES = NO        ADD_A_SURFACE_BY_HAND = NO
    REGISTRY_PRESENCE = EVIDENCE  REGISTRY_PRESENCE ≠ LICENSE

في العربية طبقةٌ **مغلقة** — الحروف والمبنيات والعوامل — تُحصى ولا تُشتقّ.
وقيمةُ الحصر هنا **إجرائية** لا معجمية: البقيةُ بعد القشر إن كانت من الطبقة
المغلقة **وقف التقشير**، لأنها كلمةٌ تامّة لا جذعٌ ينتظر مزيدًا. فالسجلّ هو
ما يمنع المحرّك من تقشير «مَا» في «بِمَا» إلى ما لا نهاية.

وضع المصدر
----------
سجلّا المالك غير مرفقين، وبحكمه (2026-09-01) يعمل هذا المحور في وضع:

    REGISTRY_SOURCE    = DERIVED_WITNESS_FROM_MASAQ
    REGISTRY_AUTHORITY = EVIDENCE_ONLY      LICENSE_GRANTED = NO

فالجرد **شاهدٌ مشتقّ من المرجع** لا سجلُّ مالك: يوقف التقشير بوصفه دليلًا،
ولا يمنح ترخيصًا. وتمريرُ السجلّين بالوسائط ينقل الوضع إلى ``OWNER_REGISTRY``.
"""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

from ..checks import CheckSuite
from ..errors import owner_alert
from ..fileio import read_json, read_rows, require_file, write_csv
from ..policy import OwnerPolicy
from ..reporting import Report
from ..runner import Axis
from .axis1_normalization import NORMALIZED, OWNER_DECISION, normalize_token

# ---------------------------------------------------------------------------
# القوائم المغلقة — لا تُوسَّع وقت التشغيل
# ---------------------------------------------------------------------------

OPERATOR_TAGS = frozenset({
    "PREP", "CONJ", "DET", "NEG_PART", "ANNUL_PART", "SUBJUNC_PART",
    "JUSSIVE_PART", "CONDITION_PART", "EXCEPT_PART", "INF_ANNUL_PART",
    "INF_SUBJUNC_PART", "CERT_PART", "VOC_PART", "INTERROG", "INTERROG_PART",
    "FUT_PART", "FUTURE_PART", "FUTUR_PART", "KAAFA_MAKFOUFA", "PART",
    "YES_NO_RESP_PART",
})

MABNIYAT_TAGS = frozenset({
    "PRON", "PRON_1P", "PRON_1S", "PRON_2MP", "PRON_2MS", "PRON_3D",
    "PRON_3FP", "PRON_3FS", "PRON_3MP", "PRON_3MS",
    "DEM_PRON", "DEM_PRON_F", "DEM_PRON_FS", "DEM_PRON_MP", "DEM_PRON_MS",
    "REL_PRON", "REL_ADV", "INTERROG_PRON", "EXCEPT_NOUN",
    "NOUN_VERB_LIKE", "UNINFLECTED_VERB",
})

CLOSED_CLASS_TAGS = OPERATOR_TAGS | MABNIYAT_TAGS

#: OWNER_RULING_1 — أفعالٌ هي في الوقت نفسه عوامل نحوية.
#: الحكم: WORD_CLASS = فعل ، OPERATOR_ROLE = TRUE ، TAG_حرف = NO
VERBAL_OPERATOR_STEMS = frozenset({"أصبح", "بئس", "نعم", "ليس", "عسى", "ليست"})

# ---------------------------------------------------------------------------
# القيم المغلقة
# ---------------------------------------------------------------------------

PROVEN = "PROVEN"
VERBAL_OPERATOR = "NOT_A_CLOSED_FORM_VERBAL_OPERATOR"
UNRESOLVED = "UNRESOLVED"
NOT_MATCHED = "NOT_MATCHED"
CLOSED_FORM_PROOF_VALUES = (PROVEN, VERBAL_OPERATOR, UNRESOLVED, NOT_MATCHED)

ACCEPT = "ACCEPT"
OWNER_DECISION_REQUIRED = "OWNER_DECISION_REQUIRED"
BLOCK = "BLOCK"

ROUTE_STOP = "STOP_CLOSED_FORM"
ROUTE_DEFER_UNRESOLVED = "DEFER_UNRESOLVED_CLOSURE"
ROUTE_DEFER_VERBAL = "DEFER_VERBAL_OPERATOR_REGISTRY_TAG"
ROUTE_CONTINUE = "CONTINUE"

#: عند تصادم التطبيع تُحفظ كل المعرّفات ولا يُختار أصغرها.
PRESERVE_ALL_MATCHED_ENTRY_IDS = True
#: لا ترجيح بين شهاداتٍ متعارضة.
CHOOSE_AMONG_ALTERNATIVES = False


@dataclass
class Entry:
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
class Verdict:
    surface: str
    closed_form_proof: str = NOT_MATCHED
    eligibility: str = BLOCK
    operator_role: bool = False
    word_class: str = ""
    next_route: str = ROUTE_CONTINUE
    matched_entry_ids: list = field(default_factory=list)
    note: str = ""

    @property
    def stops_peeling(self) -> bool:
        """الصورةُ المغلقة المبرهنة وحدها توقف التقشير."""
        return self.closed_form_proof == PROVEN and self.eligibility == ACCEPT


class Registry:
    """السجلّ + واجهة المطابقة. لا يقرأ سياقًا ولا يحكم على دورٍ في جملة."""

    def __init__(self, source_mode: str):
        self.source_mode = source_mode
        self.entries: dict[str, Entry] = {}
        self.match_index: dict[str, list[str]] = defaultdict(list)
        self.evidence_index: dict[str, list[str]] = defaultdict(list)
        self.collisions: dict[str, set] = defaultdict(set)
        self.open_witnesses: dict[str, int] = {}

    # -- البناء من الشاهد المشتقّ ---------------------------------------
    @classmethod
    def from_masaq_witness(cls, path: Path, policy: OwnerPolicy) -> Registry:
        """قاعدة الاشتقاق — مغلقة وصريحة.

        تدخل الجردَ كلمةٌ تامّة (أ) مقطعُها واحد في المرجع، و(ب) وسمُها في
        القائمة المغلقة. وما عداها **شهادةٌ مضادّة** تُسجَّل ولا تُهمَل، لأنها
        هي ما يولّد قيمة ``UNRESOLVED``.

        ولا تدخل مقاطعُ الكلمات المركّبة: عمود ``Segmented_Word`` غير مشكول،
        ومطابقةُ غير المشكول بالمشكول ممنوعة بـ OWNER_RULING_2.
        """
        self = cls("DERIVED_WITNESS_FROM_MASAQ")

        words: dict[tuple, dict] = {}
        for row in read_rows(path):
            key = (int(row["Sura_No"]), int(row["Verse_No"]), int(row["Word_No"]))
            entry = words.setdefault(key, {
                "surface": row["Word"], "bare": row["Without_Diacritics"],
                "tags": [], "segments": 0})
            entry["tags"].append(row["Morph_Tag"])
            entry["segments"] += 1

        witness: dict[str, dict] = {}
        for key, word in words.items():
            r = normalize_token(word["surface"], key, policy)
            if not r.normalized:
                continue
            tag = word["tags"][0] if word["tags"] else ""
            closed = word["segments"] == 1 and tag in CLOSED_CLASS_TAGS

            slot = witness.setdefault(r.normalized, {
                "raw": set(), "status": set(), "by_tag": defaultdict(int),
                "open": 0, "bare": set()})
            slot["raw"].add(word["surface"])
            slot["status"].add(r.status)
            slot["bare"].add(word["bare"])
            if closed:
                slot["by_tag"][tag] += 1
            else:
                slot["open"] += 1

        self._materialize(witness)
        return self

    def _materialize(self, witness: dict[str, dict]) -> None:
        """**مدخلةٌ لكل (سطحٍ مطبَّع ، وسم)** — لا مدخلة واحدة لكل سطح.

        هذا شرطُ إمكان ``UNRESOLVED``: لو طُويت الأوسمة في مدخلةٍ واحدة
        لاستحال على السجلّ أن يتعارض مع نفسه، ولصار التعارضُ غير قابل
        للظهور أصلًا — فتضيع القيمة الثالثة من الأربع.
        """
        number = 0
        for surface, slot in sorted(witness.items()):
            if not slot["by_tag"]:
                continue
            if slot["status"] <= {NORMALIZED}:
                eligibility, status = ACCEPT, NORMALIZED
            elif OWNER_DECISION in slot["status"]:
                eligibility, status = OWNER_DECISION_REQUIRED, OWNER_DECISION
            else:
                eligibility, status = BLOCK, "NOT_NORMALIZABLE"

            verbal = any(b in VERBAL_OPERATOR_STEMS for b in slot["bare"])
            for tag, count in sorted(slot["by_tag"].items()):
                number += 1
                is_operator = tag in OPERATOR_TAGS
                entry = Entry(
                    entry_id=f"DW:{number}",
                    raw_surface=" | ".join(sorted(slot["raw"])),
                    normalized_surface=surface,
                    normalization_status=status,
                    eligibility=eligibility,
                    tags={tag},
                    operator_role=is_operator or verbal,
                    mabni=tag in MABNIYAT_TAGS,
                    witness_count=count,
                    word_class="فعل" if verbal else ("حرف" if is_operator else "مبنيّ"),
                )
                self.entries[entry.entry_id] = entry
                self.evidence_index[surface].append(entry.entry_id)
                if eligibility == ACCEPT:
                    self.match_index[surface].append(entry.entry_id)

            if len(slot["raw"]) > 1:
                self.collisions[surface] |= slot["raw"]
            self.open_witnesses[surface] = slot["open"]

    # -- البناء من سجلات المالك الحقيقية --------------------------------
    @classmethod
    def from_owner_registries(cls, operators_csv: Path, mabniyat_json: Path,
                              policy: OwnerPolicy) -> Registry:
        self = cls("OWNER_REGISTRY")
        raw: list[tuple[str, str, bool]] = []
        for i, row in enumerate(read_rows(operators_csv), start=1):
            surface = _first_value(row, ("surface", "Surface", "سطح"))
            if surface:
                raw.append((f"OP:{i}", surface, True))

        data = read_json(mabniyat_json)
        items = data if isinstance(data, list) else data.get("entries", [])
        for i, item in enumerate(items, start=1):
            surface = _first_value(item, ("surface", "سطح")) if isinstance(item, dict) else ""
            if surface:
                raw.append((f"MB:{i}", surface, False))

        for entry_id, surface, is_operator in raw:
            r = normalize_token(surface, None, policy)
            eligibility = (ACCEPT if r.status == NORMALIZED else
                           OWNER_DECISION_REQUIRED if r.status == OWNER_DECISION
                           else BLOCK)
            entry = Entry(entry_id, surface, r.normalized, r.status, eligibility,
                          operator_role=is_operator, mabni=not is_operator,
                          word_class="حرف" if is_operator else "مبنيّ")
            self.entries[entry_id] = entry
            self.evidence_index[r.normalized].append(entry_id)
            if eligibility == ACCEPT:
                self.match_index[r.normalized].append(entry_id)
        return self

    # -- الواجهة ---------------------------------------------------------
    def recheck(self, surface: str) -> Verdict:
        """المطابقة الوحيدة المسموح بها: سطحٌ مطبَّع ⟷ سطحُ سجلٍّ مطبَّع.

        OWNER_RULING_2: الطرفان مطبَّعان بالمحور الأول نفسه، وإلا فلا مطابقة.
        """
        verdict = Verdict(surface=surface)

        ids = self.match_index.get(surface)
        if ids:
            entries = [self.entries[i] for i in ids]
            verdict.matched_entry_ids = (list(ids) if PRESERVE_ALL_MATCHED_ENTRY_IDS
                                         else ids[:1])
            classes = {e.word_class for e in entries}

            if classes == {"فعل"}:
                verdict.closed_form_proof = VERBAL_OPERATOR
                verdict.eligibility = ACCEPT
                verdict.operator_role = True
                verdict.word_class = "فعل"
                verdict.next_route = ROUTE_DEFER_VERBAL
                verdict.note = ("OWNER_RULING_1: WORD_CLASS=فعل ، "
                                "OPERATOR_ROLE=TRUE ، TAG_حرف=NO")
                return verdict

            if len(classes) > 1:
                # شهاداتٌ متعارضة — لا يُرجَّح بينها
                verdict.closed_form_proof = UNRESOLVED
                verdict.eligibility = ACCEPT
                verdict.next_route = ROUTE_DEFER_UNRESOLVED
                verdict.note = f"شهاداتٌ متعارضة: {sorted(classes)}"
                return verdict

            verdict.closed_form_proof = PROVEN
            verdict.eligibility = ACCEPT
            verdict.operator_role = any(e.operator_role for e in entries)
            verdict.word_class = entries[0].word_class
            verdict.next_route = ROUTE_STOP
            return verdict

        ids = self.evidence_index.get(surface)
        if ids:
            verdict.matched_entry_ids = list(ids)
            verdict.eligibility = self.entries[ids[0]].eligibility
            verdict.next_route = ROUTE_DEFER_UNRESOLVED
            verdict.note = "في فهرس الدليل لا في فهرس المطابقة — دليلٌ لا يُطابَق"
            return verdict

        return verdict

    @property
    def stats(self) -> dict:
        return {
            "entries": len(self.entries),
            "match_index": len(self.match_index),
            "evidence_index": len(self.evidence_index),
            "collisions": len(self.collisions),
        }


def _first_value(mapping, keys) -> str:
    for key in keys:
        value = mapping.get(key)
        if value:
            return str(value).strip()
    return ""


# ---------------------------------------------------------------------------
# الفحوص
# ---------------------------------------------------------------------------

def build_suite(registry: Registry, policy: OwnerPolicy) -> CheckSuite:
    suite = CheckSuite("axis2")

    def look(word):
        return registry.recheck(normalize_token(word, None, policy).normalized)

    # «مَا» يطابق أكثر من مدخلة وتختلف شهاداتها (حرف نفي / اسم موصول).
    # الحكم الصحيح ليس ترجيحًا بل UNRESOLVED — والمهمّ إجرائيًّا أنه لا يمضي.
    v = look("مَا")
    suite.check("T1_MAA_CONFLICTING_WITNESSES_ARE_NOT_ADJUDICATED",
                v.closed_form_proof == UNRESOLVED and v.next_route != ROUTE_CONTINUE,
                f"{v.closed_form_proof} / {v.next_route}")

    v = look("هَذَا")
    suite.check("T2_HADHA_IS_A_PROVEN_CLOSED_FORM",
                v.closed_form_proof == PROVEN and v.next_route == ROUTE_STOP,
                f"{v.closed_form_proof} / {v.word_class}")

    v = look("لَيْسَ")
    suite.check("T3_LAYSA_IS_VERBAL_OPERATOR_NOT_HARF",
                v.closed_form_proof == VERBAL_OPERATOR and v.word_class == "فعل",
                f"{v.closed_form_proof} / {v.word_class}")
    suite.check("T4_VERBAL_OPERATOR_DOES_NOT_STOP_PEELING", not v.stops_peeling,
                "يُرحَّل إلى DEFER لا BLOCK")

    suite.check("T5_OPEN_CLASS_NOT_MATCHED",
                look("كَتَبَ").closed_form_proof == NOT_MATCHED, NOT_MATCHED)
    suite.check("T6_PROOF_HAS_FOUR_VALUES", len(CLOSED_FORM_PROOF_VALUES) == 4,
                " · ".join(CLOSED_FORM_PROOF_VALUES))
    suite.check("T7_NO_CHOOSING_AMONG_ALTERNATIVES", not CHOOSE_AMONG_ALTERNATIVES,
                "CHOOSE_AMONG_ALTERNATIVES = NO")
    suite.check("T8_ALL_MATCHED_IDS_PRESERVED", PRESERVE_ALL_MATCHED_ENTRY_IDS,
                "PRESERVE_ALL_MATCHED_ENTRY_IDS = YES")
    suite.check("T9_MATCH_INDEX_SUBSET_OF_EVIDENCE_INDEX",
                set(registry.match_index) <= set(registry.evidence_index),
                f"{len(registry.match_index)} ⊆ {len(registry.evidence_index)}")
    suite.check("T10_REGISTRY_IS_EVIDENCE_NOT_LICENSE",
                registry.source_mode != "OWNER_REGISTRY",
                "REGISTRY_AUTHORITY = EVIDENCE_ONLY في هذا الوضع")

    v = look("عَلَى")
    suite.check("T11_ODR_SURFACE_IS_EVIDENCE_NOT_MATCH",
                v.closed_form_proof == NOT_MATCHED and bool(v.matched_entry_ids),
                f"{v.closed_form_proof} / eligibility={v.eligibility}")

    # -- السموم ---------------------------------------------------------
    suite.poison("P1_UNNORMALIZED_SURFACE_DOES_NOT_MATCH",
                 registry.recheck("مِن").closed_form_proof == NOT_MATCHED,
                 "OWNER_RULING_2: لا مطابقة إلا بتطبيعٍ متطابق للطرفين")
    suite.poison("P2_EMPTY_DOES_NOT_MATCH",
                 registry.recheck("").closed_form_proof == NOT_MATCHED, NOT_MATCHED)
    suite.poison("P3_VERBAL_OPERATOR_NOT_TAGGED_HARF",
                 look("لَيْسَ").word_class != "حرف", look("لَيْسَ").word_class)
    suite.poison("P4_WHOLE_WORD_WITH_PREFIX_IS_NOT_ITSELF_CLOSED",
                 not look("بِمَا").stops_peeling,
                 "المغلقةُ هي البقيةُ بعد القشر لا الكلمة بسابقتها")
    before = len(registry.entries)
    registry.recheck("سطحٌ لا وجود له")
    suite.poison("P5_LOOKUP_NEVER_MUTATES_REGISTRY", len(registry.entries) == before,
                 "ADD_A_SURFACE_BY_HAND = NO")
    suite.poison("P6_OPERATOR_PROVEN_IS_NOT_ATTACHABLE_PREFIX_PROVEN", True,
                 "هذا المحور لا يمنح ترخيص قشر أصلًا — الترخيص في المحور الرابع")
    return suite


# ---------------------------------------------------------------------------
# المحور
# ---------------------------------------------------------------------------

class Axis2Registry(Axis):
    number = 2
    slug = "registry"
    title = "المحور ٢ — حصر العوامل والمبنيات"
    module = "aslot.axes.axis2_registry"
    default_output = "reports/axis_2_mabniyat_operators"

    def arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--masaq", default="data/MASAQ.csv")
        parser.add_argument("--axis1-csv",
                            default="reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv")
        parser.add_argument("--operators", default=None,
                            help="سجلّ العوامل الحقيقي (يحوّل الوضع إلى OWNER_REGISTRY)")
        parser.add_argument("--mabniyat", default=None,
                            help="سجلّ المبنيات الحقيقي (يحوّل الوضع إلى OWNER_REGISTRY)")
        parser.add_argument("--policy", default=None)

    def execute(self, args, out_dir: Path):
        policy = OwnerPolicy.load(args.policy)
        registry = load_registry(args, policy)
        suite = build_suite(registry, policy)

        axis1 = require_file(Path(args.axis1_csv), what="مخرج المحور الأول",
                             remedy="شغّل  aslot normalize  أولًا")
        proofs: Counter = Counter()
        routes: Counter = Counter()
        rows = []
        for row in iter_usable(axis1):
            v = registry.recheck(row["Normalized_Word"])
            proofs[v.closed_form_proof] += 1
            routes[v.next_route] += 1
            rows.append([row["Sura_No"], row["Verse_No"], row["Word_No"],
                         row["Word"], row["Normalized_Word"],
                         v.closed_form_proof, v.eligibility,
                         "YES" if v.operator_role else "NO", v.word_class,
                         v.next_route, "|".join(v.matched_entry_ids), v.note])

        write_csv(out_dir / "AXIS_2_TOKENS.csv",
                  ["Sura_No", "Verse_No", "Word_No", "Word", "Normalized_Word",
                   "Closed_Form_Proof", "Eligibility", "Operator_Role",
                   "Word_Class", "Next_Route", "Matched_Entry_Ids", "Note"], rows)

        write_csv(out_dir / "AXIS_2_REGISTRY.csv",
                  ["Entry_Id", "Raw_Surfaces", "Normalized_Surface",
                   "Normalization_Status", "Eligibility", "Word_Class",
                   "Operator_Role", "Mabni", "Witness_Count", "Tags"],
                  ([e.entry_id, e.raw_surface, e.normalized_surface,
                    e.normalization_status, e.eligibility, e.word_class,
                    "YES" if e.operator_role else "NO",
                    "YES" if e.mabni else "NO", e.witness_count,
                    "|".join(sorted(e.tags))]
                   for e in registry.entries.values()))

        measures = {
            "source_mode": registry.source_mode,
            "registry": registry.stats,
            "closed_form_proof": dict(proofs),
            "next_route": dict(routes),
            "words_stopped_as_closed_form": proofs[PROVEN],
            "eligibility_tiers": dict(
                Counter(e.eligibility for e in registry.entries.values())),
        }
        return measures, suite

    def report(self, m: dict, suite: CheckSuite) -> Report:
        r = Report("تقرير المحور ٢ — العوامل والمبنيات")
        r.kv({
            "MODULE": self.module,
            "AXIS": self.number,
            "REGISTRY_SOURCE": m["source_mode"],
            "REGISTRY_AUTHORITY": "EVIDENCE_ONLY      LICENSE_GRANTED = NO",
            "OWNER_RATIFIED": "NO",
            "MODIFY_REGISTRIES": "NO",
            "ADD_A_SURFACE_BY_HAND": "NO",
            "CHOOSE_AMONG_ALTERNATIVES": "NO",
            "PRESERVE_ALL_MATCHED_ENTRY_IDS": "YES",
        })
        r.heading("بنية الجرد المقيسة")
        r.counts({
            "مدخلات السجلّ": m["registry"]["entries"],
            "فهرس المطابقة (ACCEPT وحده)": m["registry"]["match_index"],
            "فهرس الدليل (كل المدخلات)": m["registry"]["evidence_index"],
            "تصادمات التطبيع": m["registry"]["collisions"],
        })
        r.text("الفصل بين فهرس المطابقة وفهرس الدليل هو العمود الفقري:",
               "السجلّ الواحد قد يبقى في الجرد شاهدًا ولا يُسمح له بالمطابقة.")
        r.heading("التدرّج الثلاثي بحسب حالة تطبيع سطح السجلّ")
        r.counts([(f"{NORMALIZED} → {ACCEPT}", m["eligibility_tiers"].get(ACCEPT, 0)),
                  (f"{OWNER_DECISION} → {OWNER_DECISION_REQUIRED}",
                   m["eligibility_tiers"].get(OWNER_DECISION_REQUIRED, 0)),
                  (f"NOT_NORMALIZABLE → {BLOCK}",
                   m["eligibility_tiers"].get(BLOCK, 0))])
        r.heading("برهان الانغلاق — أربع قيم لا قيمتان")
        r.counts([(p, m["closed_form_proof"].get(p, 0))
                  for p in CLOSED_FORM_PROOF_VALUES])
        r.heading("المسارات")
        r.counts(sorted(m["next_route"].items(), key=lambda kv: -kv[1]))
        r.text("", f"كلمات أوقفها هذا المحور بوصفها صورةً مغلقة تامّة = "
                   f"{m['words_stopped_as_closed_form']:,}")
        r.proves(
            ["هويّةَ السطح، وحالةَ انغلاقه بأربع قيم، وتعارضَ الشهادات حين يقع."],
            ["أن السطح في هذه الجملة بعينها يؤدّي دور العامل — الدور سياقيّ،"
             " وهذا المحور لا يقرأ سياقًا.",
             "أن الجرد كامل. هو حصرُ ما في السجلات، لا حصرُ العربية."],
            ["OPERATOR_PROVEN ≠ ATTACHABLE_PREFIX_PROVEN",
             "COMPLETE_REGISTRY_MATCH ≠ CLOSED_FORM",
             "OPERATOR_ROLE ≠ WORD_CLASS"])
        return r


def load_registry(args, policy: OwnerPolicy) -> Registry:
    if args.operators and args.mabniyat:
        return Registry.from_owner_registries(
            Path(args.operators), Path(args.mabniyat), policy)
    if args.operators or args.mabniyat:
        raise owner_alert("مُرِّر أحد السجلّين دون الآخر",
                          ruling="BLOCK (لا يُخلط سجلُّ مالكٍ بشاهدٍ مشتقّ)")
    return Registry.from_masaq_witness(
        require_file(Path(args.masaq), what="مدخل MASAQ"), policy)


def iter_usable(axis1_csv: Path, skipped: Counter | None = None):
    """صفوفُ المحور الأول التي تمضي إلى ما بعده.

    الفواتحُ ولفظُ الجلالة والمُهمَلُ والموقوف لا تدخل المحاور التالية — وكانت هذه الشروط
    مكرّرة نصًّا في المحاور ٢ و٣ و٤، فأيّ تعديلٍ فيها كان ثلاثةَ تعديلات.
    ``skipped`` عدّادٌ اختياريّ يسجّل **ما لم يدخل** وبأيّ حالةٍ استُبعد،
    كي يبقى المستبعَد معلومًا لا مسكوتًا عنه.
    """
    from .axis1_normalization import FAWATIH, IGNORED, JALALAH
    for row in read_rows(axis1_csv):
        status = row["Normalization_Status"]
        if status in (FAWATIH, IGNORED, JALALAH) or status.startswith("STOPPED_"):
            if skipped is not None:
                skipped[status] += 1
            continue
        yield row
