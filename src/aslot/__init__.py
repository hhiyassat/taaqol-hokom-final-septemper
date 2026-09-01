"""محرّك أسلوط — خمسة محاور تقرأ ``MASAQ.csv`` بالتسلسل.

    RULE_OWNER = DR_HUSSEIN        OWNER_RULE_SOVEREIGNTY = ABSOLUTE
    CREATE_NON_OWNER_RULE = NO     INFER_LINGUISTIC_RULE  = NO
    MEASURED_NOT_PRESET

كلُّ محورٍ يقرأ **مخرجَ ما قبله** لا المدخل الخام، والاعتماد بينها مقصورٌ
على الواجهات:

    ٠ corpus     بناء ملف القرآن من MASAQ
    ١ normalize  التطبيع بقواعد المالك المسمّاة
    ٢ registry   حصر العوامل والمبنيات
    ٣ syllabify  المقاطع الصوتية وحدود القطع
    ٤ peel       التقشير إلى جذعٍ غير قابل للقشر
"""

__version__ = "2.4.0"

__all__ = ["__version__"]
