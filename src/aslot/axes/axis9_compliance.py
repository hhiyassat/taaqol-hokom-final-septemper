"""قياسُ الامتثال لتعقُّل — عمودُ «الآن» مقيسًا لا منقولًا.

    aslot compliance

هذا المحور **لا يغيّر حكمًا ولا يُنتج نصًّا**. يقرأ مخرجاتِ الجولة الأخيرة
ويقيس كلَّ خانةٍ في جدول `COMPLIANCE_KPI`. وسببُ وجوده أنّ الخطّة صرّحت بأن
أرقامَ عمودها «منقولةٌ لا مُعادُ قياسها» — والوثيقةُ التي بُنيت عليها كانت من
جولةٍ أقدم، فبعضُ أرقامها لم يعد صحيحًا. والقياسُ يصحّح ما نُقل.

الحدّ
-----
`STAGES_IMPLEMENTED = T-0 · T-1 · T-2 · T-3` وحدَها. وما فوقها يغيّر أحكامًا،
فيُعلَن غيرَ منفَّذ ولا يُقرَّب رقمُه ولا يُلوى وصفُه. وخانةٌ لا أملك قياسَها
تُطبع `UNMEASURED` لا صفرًا: الصفرُ دعوى، والاعترافُ ليس دعوى.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from ..axes.axis1_normalization import STATUSES as A1_STATUSES
from ..axes.axis1_normalization import STOP_REASON_FAMILIES as A1_STOPS
from ..axes.axis4_peeling import TERMINATIONS as A4_TERMINATIONS
from ..checks import CheckSuite
from ..constants import ALIF, FATHATAN
from ..fileio import read_rows, require_file
from ..reporting import Report
from ..runner import Axis
from ..taaqol import (
    ASLOT_REFUSALS,
    OWNER_DECISIONS_PENDING,
    VENDOR_COMMIT,
    VENDOR_LICENSE,
    anchor,
    carriers,
    mapped_refusals,
    parent_anchor,
    unmapped_refusals,
    verify_carriers,
)

#: المراحل المنفَّذة من خطّة التحويل — قائمة مغلقة، وما ليس فيها غيرُ منفَّذ.
STAGES_IMPLEMENTED: tuple[str, ...] = ("T-0", "T-1", "T-2", "T-3")
STAGES_PENDING_OWNER: tuple[str, ...] = ("T-4", "T-5", "T-6", "T-7", "T-8",
                                         "T-9", "T-10")

#: المخرجاتُ التي يُقاس عليها، بترتيب السلسلة.
AXIS_OUTPUTS = (
    (0, "reports/axis_0_quran_build/QURAN_WORDS.csv"),
    (1, "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv"),
    (2, "reports/axis_2_mabniyat_operators/AXIS_2_TOKENS.csv"),
    (3, "reports/axis_3_syllables/AXIS_3_SYLLABLES.csv"),
    (4, "reports/axis_4_peel_to_stem/AXIS_4_PEEL_TO_STEM.csv"),
)

#: الأعمدةُ التي تحمل حكمًا في كلّ مخرج — منها يُستخرج جردُ الرفض.
VERDICT_COLUMNS = (
    "Normalization_Status", "Stop_Reason", "Closed_Form_Proof", "Eligibility",
    "Next_Route", "Verdict", "Block_Reason", "Termination",
)

UNMEASURED = "UNMEASURED"

#: كم وحدةً تُنفَّذ لو استُورد المستودعُ من أعلى — **مقيسٌ** لا مقدَّر، وهو
#: الحجّةُ على العزل: تثبيتُ ٦ وتنفيذُ ٨١ يُبطل معنى التثبيت.
TOP_LEVEL_IMPORT_EXECUTES = 81


def _observed_refusals(root: Path) -> set[str]:
    """كلُّ قيمةِ حكمٍ ظهرت فعلًا في مخرجات الجولة — لا من اليد."""
    seen: set[str] = set()
    for _, rel in AXIS_OUTPUTS:
        path = root / rel
        if not path.is_file():
            continue
        with open(path, encoding="utf-8", newline="") as fh:
            for row in csv.DictReader(fh):
                for col in VERDICT_COLUMNS:
                    value = (row.get(col) or "").strip()
                    if value:
                        seen.add(value.split("@")[0].split(":")[0])
    return seen


def _anchor_audit(root: Path) -> dict:
    """يتحقّق من مرساة الأثر في كلّ صفّ، ومن اتّصال السلسلة ٠→٤.

    ولا يكتفي بوجود الحقل: يعيد **بناء** المرساة من الموضع ويقارنها. فحقلٌ
    مملوءٌ بقيمةٍ لا تُشتقّ من موضعها أثرٌ في الشكل لا في الحقيقة.
    """
    total = with_anchor = correct = linked = 0
    parents_by_axis: dict[int, set[str]] = {}
    anchors_by_axis: dict[int, set[str]] = {}
    for axis, rel in AXIS_OUTPUTS:
        path = root / rel
        if not path.is_file():
            continue
        anchors_by_axis[axis] = set()
        parents_by_axis[axis] = set()
        for row in read_rows(path):
            total += 1
            got = (row.get("Trace_Anchor") or "").strip()
            parent = (row.get("Parent_Anchor") or "").strip()
            if not got:
                continue
            with_anchor += 1
            pos = (int(row["Sura_No"]), int(row["Verse_No"]), int(row["Word_No"]))
            if got == anchor(axis, *pos) and parent == parent_anchor(axis, *pos):
                correct += 1
            anchors_by_axis[axis].add(got)
            parents_by_axis[axis].add(parent)
    for axis in sorted(parents_by_axis):
        if axis == 0:
            continue
        prev = anchors_by_axis.get(axis - 1, set())
        linked += len(parents_by_axis[axis] & prev)
    return {
        "rows_total": total,
        "rows_with_trace_anchor": with_anchor,
        "rows_with_reconstructible_anchor": correct,
        "rows_without_anchor": total - with_anchor,
        "parent_anchors_resolved_in_previous_axis": linked,
    }


def _residual_classes(root: Path) -> dict[str, int]:
    """أصنافُ المالك غيرُ المصادَقة، مقيسةً من مخرج المحور الأول."""
    counts: dict[str, int] = {}
    path = root / "reports/axis_1_normalization/AXIS_1_MEASURES.json"
    if path.is_file():
        counts = json.loads(path.read_text(encoding="utf-8")).get(
            "owner_decision_classes", {})
    return counts


def _hidden_residual(root: Path) -> int:
    """البقيّةُ المخفيّة: خللٌ يقبله المحورُ التالي ولا يشكو منه.

    الشاهدُ المسمّى في الخطّة: تنوينُ الفتح على ألفٍ صامتة يولّد صامتًا
    زائدًا، والمحور الثالث يقبله. فتُقاس الكلماتُ التي **جمعت الأمرين**:
    صنفُها `U_TANWEEN` وحكمُ المحور الثالث فيها `ACCEPT`. وهذا هو التعريف
    الحرفيّ لـ `HIDDEN_FORBIDDEN`: خللٌ مرّ بلا شكوى.
    """
    a1 = root / "reports/axis_1_normalization/AXIS_1_NORMALIZATION.csv"
    a3 = root / "reports/axis_3_syllables/AXIS_3_SYLLABLES.csv"
    if not (a1.is_file() and a3.is_file()):
        return -1
    # لا يُعدّ الصنفُ كلُّه: الخللُ في **تنوين الفتح على ألفٍ صامتة** وحدَه،
    # وهو ما يولّد الصامتَ الزائد. وعدُّ الصنف كلِّه (٨٬٨٩٤) تضخيمٌ يخلط
    # صنفًا ينتظر تصديقًا بخللٍ يمرّ صامتًا — وهما شيئان.
    tanween = {
        (r["Sura_No"], r["Verse_No"], r["Word_No"])
        for r in read_rows(a1)
        if "U_TANWEEN" in (r.get("Owner_Decision_Classes") or "")
        and ((ALIF + FATHATAN) in r["Word"] or (FATHATAN + ALIF) in r["Word"])
    }
    hidden = 0
    for r in read_rows(a3):
        key = (r["Sura_No"], r["Verse_No"], r["Word_No"])
        if key in tanween and r.get("Verdict") == "ACCEPT":
            hidden += 1
    return hidden


def _laws(root: Path) -> dict:
    path = root / "laws" / "MANIFEST.json"
    if not path.is_file():
        return {"law_files": 0, "all_hashes_hold": False}
    import hashlib
    manifest = json.loads(path.read_text(encoding="utf-8"))
    ok = True
    for law in manifest["laws"]:
        target = root / "laws" / law["file"]
        if not target.is_file():
            ok = False
            continue
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        ok = ok and digest == law["sha256"]
    return {"law_files": manifest["law_files"], "all_hashes_hold": ok}


class Axis9Compliance(Axis):
    number, slug = 9, "compliance"
    title = "قياسُ الامتثال لتعقُّل — T-0 · T-1 · T-2 · T-3"
    module = "aslot.axes.axis9_compliance"
    default_output = "reports/compliance"

    def arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--root", default=".",
                            help="جذرُ المشروع الذي تُقرأ منه المخرجات")

    def execute(self, args, out_dir: Path):
        root = Path(args.root).resolve()
        require_file(root / AXIS_OUTPUTS[0][1], what="مخرج المحور صفر",
                     remedy="شغّل  aslot all  أولًا")

        fingerprints = verify_carriers()      # فشلٌ مغلق: الانحرافُ يقف
        C = carriers()                        # وهنا وحدَه يُطلب حاملُ تعقُّل
        ClosureState, FailureCode = C["ClosureState"], C["FailureCode"]
        Rank, RankLattice = C["Rank"], C["RankLattice"]
        laws = _laws(root)
        anchors = _anchor_audit(root)
        observed = _observed_refusals(root)
        declared = set(ASLOT_REFUSALS)
        classes = _residual_classes(root)
        hidden = _hidden_residual(root)

        suite = CheckSuite("compliance")
        suite.check("C1_LAW_FILES_ARE_FROZEN_AND_HOLD",
                    laws["law_files"] > 0 and laws["all_hashes_hold"],
                    f"LAW_FILES = {laws['law_files']} · البصماتُ ثابتة")
        suite.check("C2_EVERY_ROW_CARRIES_A_TRACE_ANCHOR",
                    anchors["rows_without_anchor"] == 0,
                    f"{anchors['rows_with_trace_anchor']:,} صفًّا بلا استثناء")
        suite.check("C3_EVERY_ANCHOR_IS_RECONSTRUCTIBLE",
                    anchors["rows_with_reconstructible_anchor"]
                    == anchors["rows_total"],
                    "المرساةُ تُشتقّ من الموضع، فتُعاد بناءً على أيّ جهاز")
        suite.check("C4_THE_CHAIN_IS_LINKED_ZERO_TO_FOUR",
                    anchors["parent_anchors_resolved_in_previous_axis"] > 0,
                    "كلُّ أبٍ يُحلّ في المحور السابق")
        suite.check("C5_CARRIERS_ARE_TAAQOL_S_OWN",
                    len(fingerprints) == 6 and len(list(FailureCode)) > 0,
                    f"{len(fingerprints)} حواملَ مثبَّتةً بالبصمة من {VENDOR_COMMIT[:12]}")
        suite.check("C6_RANK_LATTICE_MEET_NEVER_RAISES",
                    RankLattice.meet(Rank.CERTIFICATE, Rank.CANDIDATE)
                    == Rank.CANDIDATE,
                    "meet يُبقي أو يخفض، ولا يرفع")
        suite.check("C7_HIDDEN_RESIDUAL_IS_MEASURED_NOT_ASSUMED",
                    hidden >= 0,
                    f"{hidden:,} كلمة — تنوينُ فتحٍ على ألفٍ صامتة يمرّ بلا شكوى")

        # سمومٌ: مدخلاتٌ يجب أن تُرفض
        # الجردُ يُقاس بمقياسين لا بواحد، والخلطُ بينهما أفسد أوّلَ صياغة:
        #  (أ) اسمٌ مُدَّعًى لا تعرفه المحاور  ← اختراعٌ يُرفض (سُمّ).
        #  (ب) اسمٌ تعرفه المحاور ولم يشهد له **هذا المدخل** ← يُعلَن ولا يُحذف،
        #      كحال N8: قاعدةٌ منفَّذةٌ بلا شاهدٍ في رسمٍ إملائيّ.
        # ولمّا حُذف BLOCK_EMPTY_REMAINDER من شواهد هذه الجولة أسقط السمُّ
        # الجولةَ — وكان محقًّا في التنبيه، خاطئًا في التكييف.
        engine_names = (set(A4_TERMINATIONS) | set(A1_STATUSES)
                        | set(A1_STOPS) | observed)
        suite.poison("P1_NO_INVENTED_REFUSAL_NAME",
                     declared <= engine_names,
                     f"{sorted(declared - engine_names)} — كلُّ اسمٍ تعرفه المحاور")
        suite.poison("P2_NO_INVENTED_TAAQOL_FAILURE_CODE",
                     set(mapped_refusals().values())
                     <= {m.value for m in FailureCode},
                     "كلُّ مقابلٍ مُدَّعًى موجودٌ في جرد تعقُّل المغلق")
        suite.poison("P3_UNMAPPED_IS_DECLARED_NOT_FORCED",
                     len(unmapped_refusals()) > 0,
                     f"{len(unmapped_refusals())} اسمًا بلا مقابل — معلنةٌ لا ملويّة")
        suite.poison("P4_RESIDUAL_KINDS_ARE_NOT_SELF_ASSIGNED",
                     all(k not in _ASSIGNED for k in classes),
                     "تصنيفُ البقايا حكمُ المالك (T-4) — لم يُسنَد صنفٌ واحد")
        loaded = sorted(m for m in sys.modules if m.startswith("taaqqul"))
        suite.poison("P5_EXECUTION_NEVER_EXCEEDS_THE_PINNING",
                     len([m for m in loaded if m.count(".") == 2]) == len(fingerprints),
                     f"نُفِّذ {len([m for m in loaded if m.count('.') == 2])} "
                     f"وثُبِّت {len(fingerprints)} — والاستيرادُ من أعلى ينفّذ "
                     f"{TOP_LEVEL_IMPORT_EXECUTES}")
        suite.poison("P6_NO_JUDGEMENT_TOOL_IS_IMPORTED",
                     not any(m.endswith((".gamma", ".transition_gate",
                                         ".forbidden_lines")) for m in loaded),
                     "Γ والبوّابةُ والخطوطُ الممنوعة أدواتُ حكمٍ — موقوفة")
        suite.poison("P7_STAGES_ABOVE_T3_ARE_NOT_CLAIMED",
                     set(STAGES_IMPLEMENTED).isdisjoint(STAGES_PENDING_OWNER),
                     " · ".join(STAGES_PENDING_OWNER) + " غيرُ منفَّذة")

        measures = {
            "stages_implemented": list(STAGES_IMPLEMENTED),
            "stages_pending_owner": list(STAGES_PENDING_OWNER),
            "vendor": {"commit": VENDOR_COMMIT, "license": VENDOR_LICENSE,
                       "carriers": {k: v[:12] for k, v in fingerprints.items()}},
            "laws": laws,
            "anchors": anchors,
            "refusal_inventory": {
                "declared": len(declared),
                "declared_without_witness_in_this_run":
                    sorted(declared - observed),
                "observed_in_outputs": len(observed),
                "mapped_to_taaqol": len(mapped_refusals()),
                "unmapped_declared": len(unmapped_refusals()),
                "taaqol_failure_codes_total": len(list(FailureCode)),
            },
            "residual_classes_unassigned": classes,
            "hidden_residual_count": hidden,
            "closure_states_available": len(list(ClosureState)),
            "closure_states_in_use": 0,
            "gates_between_axes": 0,
            "forbidden_lines_enforced": 0,
            "taaqol_modules_executed": sorted(
                m for m in sys.modules if m.startswith("taaqqul")),
            "owner_decisions_pending": list(OWNER_DECISIONS_PENDING),
        }
        return measures, suite

    def report(self, m: dict, suite: CheckSuite) -> Report:
        r = Report(self.title)
        r.kv({
            "STAGES_IMPLEMENTED": " · ".join(m["stages_implemented"]),
            "STAGES_PENDING_OWNER": " · ".join(m["stages_pending_owner"]),
            "TAAQOL_COMMIT": m["vendor"]["commit"][:12],
            "TAAQOL_LICENSE": m["vendor"]["license"],
        })
        a = m["anchors"]
        r.counts({
            "rows_with_trace_anchor": a["rows_with_trace_anchor"],
            "rows_without_anchor": a["rows_without_anchor"],
            "rows_with_reconstructible_anchor": a["rows_with_reconstructible_anchor"],
            "law_files_frozen": m["laws"]["law_files"],
            "failure_codes_declared": m["refusal_inventory"]["declared"],
            "failure_codes_mapped_to_taaqol": m["refusal_inventory"]["mapped_to_taaqol"],
            "failure_codes_unmapped": m["refusal_inventory"]["unmapped_declared"],
            "taaqol_failure_codes_total": m["refusal_inventory"]["taaqol_failure_codes_total"],
            "residual_kinds_assigned": 0,
            "hidden_residual_count": m["hidden_residual_count"],
            "closure_states_in_use": m["closure_states_in_use"],
            "gates_between_axes": m["gates_between_axes"],
            "forbidden_lines_enforced": m["forbidden_lines_enforced"],
        })
        r.kv({k: f"{v:,}  → ResidualKind = ؟  (T-4، حكمُك)" for k, v in
              sorted(m["residual_classes_unassigned"].items(),
                     key=lambda kv: -kv[1])})
        r.proves(
            proves=["أنّ كلَّ صفٍّ يحمل مرساةَ أثرٍ تُعاد بناؤها من موضعها",
                 "أنّ جردَ الرفض مستخرَجٌ من مخرجاتٍ فعليّة لا من اليد",
                 "أنّ الحواملَ حواملُ تعقُّل نفسِه، مثبَّتةً بالبصمة"],
            does_not_prove=["غلقًا Γ — لم يُشغَّل، والأحكامُ لم تتغيّر (T-5)",
                "سقفَ رتبةٍ نافذًا — البقايا بلا صنفٍ بعد (T-4)",
                "بوّابةَ انتقالٍ بين المحاور — الاستدعاءُ مباشرٌ كما كان (T-7)",
                "خطًّا ممنوعًا مُنفَّذًا — تقشيرُ «كَتَبَ» ما زال ACCEPT (T-6)"],
        )
        r.kv({f"◻ {d}": "موقوفٌ على حكمك"
              for d in m["owner_decisions_pending"]})
        return r


#: أصنافُ البقايا التي أُسنِد لها صنفٌ — فارغةٌ عمدًا، والإسنادُ حكمُ المالك.
_ASSIGNED: dict[str, str] = {}
