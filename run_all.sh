#!/usr/bin/env bash
# تشغيل السلسلة كاملة بالترتيب. كل محورٍ يقرأ مخرجَ ما قبله، لا المدخلَ الخام.
set -euo pipefail
cd "$(dirname "$0")"

echo "### ١ — بناء ملف القرآن من MASAQ"
python3 a0_build_quran_from_masaq.py "$@"

echo; echo "### ٢ — المحور الأول: التطبيع"
python3 a1_normalize.py --cross-check-masaq data/MASAQ.csv

echo; echo "### ٣ — المحور الثاني: العوامل والمبنيات"
python3 a2_classify_mabniyat_and_operators.py

echo; echo "### ٤ — المحور الثالث: المقاطع الصوتية"
python3 a3_syllabify.py

echo; echo "### ٥ — المحور الرابع: التقشير إلى جذع"
python3 a4_peel_to_stem.py --emit-masaq-like

echo; echo "تمّ. المخرجات تحت reports/"
