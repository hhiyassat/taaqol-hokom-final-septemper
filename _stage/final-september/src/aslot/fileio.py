"""قراءة الملفات وكتابتها — بمعاملاتٍ واحدة في كل المحاور.

سببُ وجود هذه الوحدة عمليّ: ترميزٌ أو ``newline`` مختلفٌ في محورٍ واحد يكفي
لأن تختلف بصمةُ مخرجٍ عن مخرج، فتنكسر المقارنةُ بين الجولات وهي أساس
`MEASURED_NOT_PRESET`. فالتوحيد هنا شرطُ إمكان القياس لا تنظيمٌ شكليّ.
"""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Iterable, Iterator, Sequence
from pathlib import Path

from .errors import owner_alert

ENCODING = "utf-8"


def sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def require_file(path: Path, *, what: str, remedy: str = "") -> Path:
    """وجودُ المدخل شرطٌ لا يُفترض. غيابُه إنذارُ مالكٍ لا استثناءُ بايثون."""
    path = Path(path)
    if not path.exists():
        detail = {"المسار": path}
        if remedy:
            detail["الحلّ"] = remedy
        raise owner_alert(f"{what} غير موجود", **detail)
    return path


def read_rows(path: Path, *, required_columns: Sequence[str] = ()) -> Iterator[dict]:
    """يقرأ CSV صفًّا صفًّا، ويرفض المدخل إن نقص عمودٌ مأذون."""
    with Path(path).open(encoding=ENCODING, newline="") as handle:
        reader = csv.DictReader(handle)
        missing = [c for c in required_columns if c not in (reader.fieldnames or [])]
        if missing:
            raise owner_alert("حقولٌ مأذونة غائبة عن المدخل",
                              المسار=path, الحقول=missing)
        yield from reader


def write_csv(path: Path, header: Sequence[str], rows: Iterable[Sequence]) -> int:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding=ENCODING, newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(header)
        for row in rows:
            writer.writerow(row)
            count += 1
    return count


def write_text(path: Path, text: str) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text if text.endswith("\n") else text + "\n", encoding=ENCODING)


def write_json(path: Path, payload: object) -> None:
    write_text(Path(path), json.dumps(payload, ensure_ascii=False, indent=2))


def read_json(path: Path) -> object:
    return json.loads(Path(path).read_text(encoding=ENCODING))


def strict_int(value: object, *, field: str, row_no: int) -> int:
    """تحويلٌ صارم إلى عدد.

    ``int()`` في بايثون يقبل الأرقام العربية-الهندية (٢ → 2) وهو قبولٌ ضمنيّ
    لم يأذن به المالك، فتُشترط خاناتُ ASCII صراحةً قبل التحويل.
    """
    raw = str(value).strip()
    if not raw or not all("0" <= ch <= "9" for ch in raw.lstrip("-")):
        raise owner_alert("حقلٌ عدديّ غير قابل للقراءة",
                          الحقل=field, الصفّ=row_no, القيمة=repr(value),
                          ruling="BLOCK (لا يُخمَّن رقمُ سورةٍ أو آيةٍ أو كلمة)")
    return int(raw)
