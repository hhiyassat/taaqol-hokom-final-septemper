"""المحور ٠ — بناء ملف القرآن من ``MASAQ.csv``.

MASAQ جدولٌ على مستوى **المقطع الصرفي**: الكلمة الواحدة موزّعة على عدّة
صفوف، وعمود ``Word`` يكرّر سطحها كاملًا في كل صفٍّ منها.

فالبناء ليس نسخًا للعمود، بل **طيُّ الصفوف إلى كلمات** ثم إلى آياتٍ فسور،
مع إثبات أن الطيّ لم يفقد شيئًا ولم يخترع شيئًا:

    ROW_COUNT ≠ WORD_COUNT
    WORD_SURFACE = القيمة المتّفق عليها في كل صفوف الكلمة ، لا القيمة الأولى
"""

from __future__ import annotations

import argparse
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from ..checks import CheckSuite, rejects
from ..constants import (
    OWNER_SEPARATORS,
    UNRULED_SEPARATORS,
    canonical_mark_order,
    strip_owner_separators,
)
from ..errors import owner_alert
from ..fileio import read_rows, require_file, sha256_of_file, write_csv, write_text
from ..reporting import Report
from ..runner import Axis
from ..trace import anchor, parent_anchor

#: الحقول الخمسة التي أذن بها المالك لهذا المحور — قائمة مغلقة.
CONSUMED_FIELDS = ("Sura_No", "Verse_No", "Word_No", "Segment_No", "Word")

#: كل ما عداها مرجعٌ لا مدخل: يُقارَن به ولا يُبنى عليه قرار.
REFERENCE_ONLY_FIELDS = (
    "ID", "Without_Diacritics", "Segmented_Word", "Morph_Tag", "Morph_Type",
    "Punctuation_Mark", "Invariable_Declinable", "Syntactic_Role",
    "Possessive_Construct", "Case_Mood", "Case_Mood_Marker", "Phrase",
    "Phrasal_Function", "Gloss",
)

EXPECTED_SURA_COUNT = 114


@dataclass
class Word:
    """كلمةٌ مطويّةٌ من صفوف MASAQ الخاصة بها."""

    sura: int
    verse: int
    number: int
    surface: str | None = None
    segments: list = field(default_factory=list)      # [(Segment_No, Word)]
    surface_conflict: bool = False
    #: ما قُطع من طرفَي السطح بحكم المالك في الفاصلة والنقطة — يُسجَّل ولا
    #: يُحذف بلا أثر. فارغٌ لأكثر التوكنات، وغيرُ فارغٍ حيث لصق فاصل.
    separators: str = ""

    def add(self, segment_no: int, surface: str) -> None:
        if self.surface is None:
            self.surface = surface
        elif self.surface != surface:
            # سطحُ الكلمة يجب أن يتّفق في كل صفوفها.
            # اختلافُه واقعةٌ تُسجَّل ولا تُرجَّح بينها.
            self.surface_conflict = True
        self.segments.append((segment_no, surface))

    def finalize(self) -> None:
        self.segments.sort(key=lambda item: item[0])

    @property
    def key(self) -> tuple[int, int, int]:
        return (self.sura, self.verse, self.number)

    @property
    def segment_count(self) -> int:
        return len(self.segments)

    @property
    def segment_numbers(self) -> list[int]:
        return [n for n, _ in self.segments]


class Corpus:
    """نتيجة الطيّ: كلماتٌ مرتّبة ترتيبًا مصحفيًّا."""

    def __init__(self, words: OrderedDict[tuple, Word], rows_read: int,
                 columns: int, source: Path, digest: str):
        self.words = words
        self.rows_read = rows_read
        self.columns = columns
        self.source = source
        self.digest = digest

    # -- البناء ---------------------------------------------------------
    @classmethod
    def from_masaq(cls, path: Path) -> Corpus:
        from ..fileio import strict_int

        words: OrderedDict[tuple, Word] = OrderedDict()
        rows_read = 0
        columns = 0
        for row_no, row in enumerate(
                read_rows(path, required_columns=CONSUMED_FIELDS), start=2):
            rows_read += 1
            columns = columns or len(row)
            key = tuple(strict_int(row[f], field=f, row_no=row_no)
                        for f in ("Sura_No", "Verse_No", "Word_No"))
            segment_no = strict_int(row["Segment_No"], field="Segment_No",
                                    row_no=row_no)
            word = words.get(key)
            if word is None:
                word = words[key] = Word(*key)
            bare, cut = strip_owner_separators(
                canonical_mark_order(row["Word"]))
            word.separators += cut
            word.add(segment_no, bare)

        for word in words.values():
            word.finalize()
        return cls(words, rows_read, columns, path, sha256_of_file(path))

    @classmethod
    def from_text(cls, path: Path) -> Corpus:
        """نصٌّ خامّ: سطرٌ لكل آية بصيغة ``سورة|آية|كلماتها``.

        هذه هي صيغةُ ``QURAN_FROM_MASAQ.txt`` نفسها، فالمحور يقرأ ما يكتب.
        وفائدتُها أن أيّ نصٍّ عثمانيّ يُصاغ بها يمضي في السلسلة كاملةً بلا
        حاجةٍ إلى جدولٍ صرفيّ — والقواعدُ العثمانية (N8 وN3.Q) لا شواهدَ لها
        في MASAQ وإنما تعمل هنا.

        والكلمةُ تُعدّ مقطعًا واحدًا: لا تحليلَ صرفيًّا في النصّ الخام، وهذا
        **إعلانُ نقصٍ لا ادّعاءُ تحليل**.
        """
        words: OrderedDict[tuple[int, int, int], Word] = OrderedDict()
        rows = 0
        for line_no, raw in enumerate(
                path.read_text(encoding="utf-8").splitlines(), start=1):
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("|")
            if len(parts) < 3:
                raise owner_alert(
                    "سطرٌ لا يوافق الصيغة «سورة|آية|كلماتها»",
                    المسار=path, السطر=line_no, المحتوى=line[:40])
            from ..fileio import strict_int
            sura = strict_int(parts[0], field="Sura_No", row_no=line_no)
            verse = strict_int(parts[1], field="Verse_No", row_no=line_no)
            for number, surface in enumerate("|".join(parts[2:]).split(), start=1):
                rows += 1
                bare, cut = strip_owner_separators(
                    canonical_mark_order(surface))
                word = Word(sura, verse, number)
                word.separators = cut
                word.add(1, bare)
                word.finalize()
                words[(sura, verse, number)] = word
        return cls(words, rows, 3, path, sha256_of_file(path))

    # -- قراءات ---------------------------------------------------------
    def __len__(self) -> int:
        return len(self.words)

    @property
    def keys(self) -> list[tuple]:
        return list(self.words)

    @property
    def total_segments(self) -> int:
        return sum(w.segment_count for w in self.words.values())

    @property
    def verses(self) -> OrderedDict[tuple, list[str]]:
        out: OrderedDict[tuple, list[str]] = OrderedDict()
        for word in self.words.values():
            out.setdefault((word.sura, word.verse), []).append(word.surface or "")
        return out

    @property
    def suras(self) -> list[int]:
        return sorted({w.sura for w in self.words.values()})


# ---------------------------------------------------------------------------
# الفحوص
# ---------------------------------------------------------------------------

def build_suite(corpus: Corpus, fragment: bool = False) -> CheckSuite:
    """``fragment`` = المدخل مقطعٌ من النصّ لا مصحفٌ كامل.

    فحوصُ الاكتمال (عددُ السور، اتّصالُ الترقيم) تقيس **حالة المدخل** لا التزام
    المحرّك. فإن كان المدخل مقطعًا صارت عيوبَ مدخلٍ تُسجَّل ولا تُسقط الجولة —
    وإلا لأخفق المحرّك على نصٍّ سليمٍ لأنه ليس مصحفًا كاملًا، وذاك حكمٌ على
    غير محلّه.
    """
    suite = CheckSuite("axis0")
    keys = corpus.keys

    suite.check("T1_INPUT_ORDER_IS_CANONICAL", keys == sorted(keys),
                "ترتيب ورود الكلمات = الترتيب المصحفي")

    # حدُّ حكم المالك يُحرَس بفحصين لا بنيّة: أن يُقطع ما حكم فيه، وألّا
    # يُقطع ما لم يحكم فيه. والثاني هو الحارسُ الحقيقيّ — فمدُّ حكمٍ إلى
    # ما لم يشمله هو الخرقُ الذي لا يشتكي منه أحد.
    surviving = "".join(w.surface or "" for w in corpus.words.values())
    suite.check("T_OWNER_SEPARATORS_ARE_CUT",
                not any(ch in OWNER_SEPARATORS for ch in surviving),
                f"لا فاصلةَ ولا نقطةَ بقيت في سطحٍ "
                f"({sum(1 for w in corpus.words.values() if w.separators)} كلمةً قُطع منها)")
    unruled = sum(1 for w in corpus.words.values()
                  if any(ch in UNRULED_SEPARATORS for ch in (w.surface or "")))
    suite.check("T_UNRULED_SEPARATORS_ARE_NOT_CUT",
                all(ch not in OWNER_SEPARATORS for w in corpus.words.values()
                    for ch in w.separators if ch not in OWNER_SEPARATORS)
                and not any(ch in UNRULED_SEPARATORS
                            for w in corpus.words.values() for ch in w.separators),
                f"{unruled} توكنًا يحمل علامةً لم يُحكم فيها — باقيةٌ كما هي")

    verses: dict[int, set[int]] = {}
    for sura, verse, _ in keys:
        verses.setdefault(sura, set()).add(verse)
    bad = [s for s, vs in verses.items() if sorted(vs) != list(range(1, len(vs) + 1))]
    complete_suras = len(corpus.suras) == EXPECTED_SURA_COUNT
    contiguous = corpus.suras == list(range(1, len(corpus.suras) + 1))

    if fragment:
        suite.defect("D0A_SURA_COUNT_NOT_FULL_MUSHAF",
                     0 if complete_suras else len(corpus.suras),
                     f"سورٌ في المدخل = {len(corpus.suras)} من {EXPECTED_SURA_COUNT}")
        suite.defect("D0B_NUMBERING_NOT_CONTIGUOUS",
                     0 if (contiguous and not bad) else len(bad) + (0 if contiguous else 1),
                     "ترقيمٌ غير متّصل — متوقَّعٌ في مقطعٍ من النصّ", bad)
    else:
        suite.check("T2_SURA_COUNT", complete_suras,
                    f"{len(corpus.suras)}/{EXPECTED_SURA_COUNT}")
        suite.check("T3_SURA_NUMBERING_CONTIGUOUS", contiguous,
                    "أرقام السور متّصلة من ١")
        suite.check("T4_VERSE_NUMBERING_CONTIGUOUS", not bad,
                    f"سور مخالفة = {bad[:5]}")

    conflicts = [w.key for w in corpus.words.values() if w.surface_conflict]
    suite.check("T5_WORD_SURFACE_AGREES_ACROSS_SEGMENTS", not conflicts,
                f"تعارضات = {len(conflicts)}")

    empty = [w.key for w in corpus.words.values() if not (w.surface or "").strip()]
    suite.check("T6_NO_EMPTY_SURFACE", not empty, f"فارغة = {len(empty)}")

    suite.check("T7_FOLD_IS_LOSSLESS", corpus.total_segments == corpus.rows_read,
                f"{corpus.total_segments:,} مقطعًا = {corpus.rows_read:,} صفًّا")

    _add_poisons(suite)
    _add_defects(suite, corpus)
    return suite


def _add_poisons(suite: CheckSuite) -> None:
    from ..fileio import strict_int

    for name, value, field_name in (
        ("P1_REJECT_NON_ASCII_DIGIT", "٢", "Sura_No"),
        ("P2_REJECT_EMPTY_NUMERIC", "", "Verse_No"),
        ("P6_REJECT_ARABIC_INDIC_DIGITS", "٢٣", "Verse_No"),
        ("P7_REJECT_SPACED_NUMBER", "1 2", "Word_No"),
    ):
        rejected, detail = rejects(
            lambda v=value, f=field_name: strict_int(v, field=f, row_no=0))
        suite.poison(name, rejected, detail)

    word = Word(1, 1, 1)
    word.add(1, "بِسْمِ")
    word.add(2, "بسم")
    suite.poison("P3_SURFACE_CONFLICT_IS_FLAGGED_NOT_RESOLVED", word.surface_conflict,
                 "التعارض يُسجَّل ولا يُختار أحد الطرفين")

    word = Word(1, 1, 1)
    word.add(2, "بِسْمِ")
    word.add(1, "بِسْمِ")
    word.finalize()
    suite.poison("P4_SEGMENTS_SORTED_NOT_TRUSTED", word.segment_numbers == [1, 2],
                 "تُرتَّب المقاطع ولا يُعتمد ترتيب الورود")

    word = Word(1, 1, 1)
    word.add(1, "و")
    word.add(3, "و")
    word.finalize()
    suite.poison("P5_SEGMENT_GAP_DETECTED",
                 word.segment_numbers != [1, 2], "الفجوة تُكشف")


def _add_defects(suite: CheckSuite, corpus: Corpus) -> None:
    """عيوبٌ في **المدخل** لا في المحرّك. لا يُرقَّع منها شيء."""
    words_by_verse: dict[tuple, set[int]] = {}
    for sura, verse, number in corpus.keys:
        words_by_verse.setdefault((sura, verse), set()).add(number)
    gaps = [k for k, ns in words_by_verse.items()
            if sorted(ns) != list(range(1, len(ns) + 1))]
    suite.defect("D1_WORD_NUMBER_GAPS_IN_VERSE", len(gaps),
                 "أرقام كلماتٍ مفقودة داخل آيات — لا تُردَم", gaps)

    duplicated, missing = [], []
    for word in corpus.words.values():
        numbers = word.segment_numbers
        if len(set(numbers)) != len(numbers):
            duplicated.append(word.key)
        elif numbers != list(range(1, len(numbers) + 1)):
            missing.append(word.key)
    suite.defect("D2A_SEGMENT_NUMBER_DUPLICATED", len(duplicated),
                 "تكرار Segment_No داخل الكلمة (أشهره «يا» الموصولة بما بعدها)",
                 duplicated)
    suite.defect("D2B_SEGMENT_NUMBER_GAP", len(missing), "ثغرة في ترقيم المقاطع",
                 missing)

    multiword = [w.key for w in corpus.words.values() if " " in (w.surface or "")]
    suite.defect("D3_MULTIWORD_SURFACE_IN_ONE_CELL", len(multiword),
                 "خليّة Word فيها أكثر من كلمة", multiword)


# ---------------------------------------------------------------------------
# المحور
# ---------------------------------------------------------------------------

class Axis0Corpus(Axis):
    number = 0
    slug = "corpus"
    title = "المحور ٠ — بناء ملف القرآن من MASAQ"
    module = "aslot.axes.axis0_corpus"
    default_output = "reports/axis_0_quran_build"

    def arguments(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument("--masaq", default="data/MASAQ.csv")
        parser.add_argument("--text", default=None,
                            help="نصٌّ خامّ بدل MASAQ: سطرٌ لكل آية «سورة|آية|كلماتها»")
        parser.add_argument("--fragment", action="store_true",
                            help="المدخل مقطعٌ لا مصحفٌ كامل: فحوصُ الاكتمال "
                                 "تصير عيوبَ مدخلٍ تُسجَّل ولا تُسقط الجولة")

    def execute(self, args, out_dir: Path):
        if args.text:
            path = require_file(Path(args.text), what="النصّ الخام")
            corpus = Corpus.from_text(path)
        else:
            path = require_file(Path(args.masaq), what="مدخل MASAQ")
            corpus = Corpus.from_masaq(path)

        write_text(out_dir / "QURAN_FROM_MASAQ.txt", "\n".join(
            f"{sura}|{verse}|{' '.join(words)}"
            for (sura, verse), words in corpus.verses.items()))

        write_csv(
            out_dir / "QURAN_WORDS.csv",
            ["Sura_No", "Verse_No", "Word_No", "Word", "Segment_Count",
             "Segment_Numbers", "Surface_Conflict", "Segment_Numbering_Gap",
             "Cut_Separators", "Trace_Anchor", "Parent_Anchor"],
            ([w.sura, w.verse, w.number, w.surface, w.segment_count,
              "|".join(map(str, w.segment_numbers)),
              "YES" if w.surface_conflict else "NO",
              "YES" if w.segment_numbers != list(range(1, w.segment_count + 1))
              else "NO",
              w.separators,
              anchor(0, w.sura, w.verse, w.number),
              parent_anchor(0, w.sura, w.verse, w.number)]
             for w in corpus.words.values()))

        measures = {
            "input": str(path),
            "input_sha256": corpus.digest,
            "rows_read": corpus.rows_read,
            "words_built": len(corpus),
            "verses_built": len(corpus.verses),
            "suras_built": len(corpus.suras),
            "segments_per_word": dict(sorted(
                Counter(w.segment_count for w in corpus.words.values()).items())),
            "fragment_mode": bool(args.fragment),
            "surface_conflicts": sum(
                1 for w in corpus.words.values() if w.surface_conflict),
            # أثرُ حكم المالك في الفاصلة والنقطة، مقيسًا في كلّ جولة.
            # وصفرُه على المصحف ليس مصادفة: لا ترقيمَ في رسمه.
            "words_with_cut_separators": sum(
                1 for w in corpus.words.values() if w.separators),
            "cut_separators": dict(sorted(Counter(
                ch for w in corpus.words.values() for ch in w.separators).items())),
            # ما لم يشمله الحكم، مقيسًا كذلك — فالفجوةُ تُعدّ لا تُوصف.
            "unruled_separator_tokens": sum(
                1 for w in corpus.words.values()
                if any(ch in UNRULED_SEPARATORS for ch in (w.surface or ""))),
        }
        return measures, build_suite(corpus, fragment=args.fragment)

    def report(self, m: dict, suite: CheckSuite) -> Report:
        r = Report("تقرير المحور ٠ — بناء ملف القرآن من MASAQ")
        r.kv({
            "MODULE": self.module,
            "AXIS": self.number,
            "INPUT": m["input"],
            "INPUT_SHA256": m["input_sha256"],
            "CONSUMED_FIELDS": ", ".join(CONSUMED_FIELDS),
            "REFERENCE_ONLY_FIELDS": f"{len(REFERENCE_ONLY_FIELDS)}  (لا تدخل المحرّك)",
            "ROWS_READ": m["rows_read"],
            "WORDS_BUILT": m["words_built"],
            "VERSES_BUILT": m["verses_built"],
            "SURAS_BUILT": m["suras_built"],
            "SURFACE_CONFLICTS": m["surface_conflicts"],
        })
        r.heading("توزيع المقاطع على الكلمات")
        r.counts({f"{k}_SEGMENTS": v for k, v in m["segments_per_word"].items()})
        r.proves(
            ["أن الطيّ لم يفقد صفًّا ولم يخترع كلمة، وأن الترتيب مصحفيّ."],
            ["صحّةَ رسم MASAQ — ينقله كما هو.",
             "تطبيعًا ولا تقطيعًا ولا تقشيرًا — تلك محاور تالية.",
             "شيئًا مبنيًّا على Segmented_Word أو Morph_Tag — هما مرجعٌ لا مدخل."],
            ["ROW_COUNT ≠ WORD_COUNT"])
        return r
