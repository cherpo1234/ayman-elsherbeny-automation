"""
أوتوميشن "أيمن الشربيني" - Text/Image to Video with Audio
===========================================================
أوتوميشن احترافي لتحويل النص والصور إلى فيديو مع صوت
"""
__version__ = "1.0.0"
__author__ = "أيمن الشربيني"
__email__ = ""
__description__ = "أوتوميشن احترافي لتحويل النص/الصور إلى فيديو مع صوت"

from .config import config, ROOT_DIR, CONFIG_DIR, MODELS_DIR, OUTPUT_DIR, INPUT_DIR, LOGS_DIR
from .utils.logging import setup_logging, get_logger, logger
from .utils.device import get_device, get_dtype, optimize_model, clear_memory, get_gpu_memory_info

# إعداد السجل عند الاستيراد
setup_logging()

__all__ = [
    "config",
    "ROOT_DIR",
    "CONFIG_DIR",
    "MODELS_DIR",
    "OUTPUT_DIR",
    "INPUT_DIR",
    "LOGS_DIR",
    "setup_logging",
    "get_logger",
    "logger",
    "get_device",
    "get_dtype",
    "optimize_model",
    "clear_memory",
    "get_gpu_memory_info",
]