"""
وحدة تسجيل الأحداث (Logging)
"""
import logging
import sys
from pathlib import Path


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None,
    format_str: Optional[str] = None,
) -> logging.Logger:
    """إعداد نظام التسجيل"""
    from ayman_elsherbeny_automation.config import config

    level = level or config.get("logging.level", "INFO")
    log_file = log_file or Path(config.get("logging.file", "./logs/ayman_elsherbeny.log"))
    format_str = format_str or config.get(
        "logging.format",
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # إنشاء مجلد السجلات
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # تنسيق
    formatter = logging.Formatter(format_str)

    # معالج الملف
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(getattr(logging, level.upper()))

    # معالج الكونسول
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, level.upper()))

    # إعداد المسجل الجذري
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, level.upper()))

    # إزالة المعالجات السابقة
    root_logger.handlers.clear()

    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    # تقليل مستوى مكتبات الطرف الثالث
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("transformers").setLevel(logging.WARNING)
    logging.getLogger("diffusers").setLevel(logging.WARNING)
    logging.getLogger("accelerate").setLevel(logging.WARNING)

    return root_logger


def get_logger(name: str) -> logging.Logger:
    """الحصول على مسجل باسم محدد"""
    return logging.getLogger(name)


# إعداد افتراضي عند الاستيراد
_logger_initialized = False


def _ensure_logger() -> None:
    global _logger_initialized
    if not _logger_initialized:
        setup_logging()
        _logger_initialized = True


# مسجل الوحدة - lazy initialization
_logger_instance = None
logger = get_logger(__name__)