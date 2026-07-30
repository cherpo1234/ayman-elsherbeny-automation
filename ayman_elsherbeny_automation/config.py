"""
وحدة التكوين (Configuration)
"""
import yaml
import logging
from pathlib import Path
from typing import Any, Optional, Dict

logger = logging.getLogger(__name__)


class Config:
    """فئة إدارة التكوين"""

    def __init__(self, config_path: Optional[Path] = None):
        self.config_path = config_path or Path(__file__).parent.parent / "config" / "config.yaml"
        self._config: Dict[str, Any] = {}
        self.load()

    def load(self) -> None:
        """تحميل التكوين من ملف YAML"""
        if self.config_path.exists():
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._config = yaml.safe_load(f) or {}
            logger.info(f"Config loaded from {self.config_path}")
        else:
            logger.warning(f"Config file not found: {self.config_path}, using defaults")
            self._config = {}

    def save(self) -> None:
        """حفظ التكوين إلى ملف YAML"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump(self._config, f, allow_unicode=True, default_flow_style=False)
        logger.info(f"Config saved to {self.config_path}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        الحصول على قيمة من التكوين باستخدام تدوين النقطة
        مثال: config.get("video.fps", 7)
        """
        keys = key.split(".")
        value = self._config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k)
            else:
                return default
            if value is None:
                return default
        return value

    def set(self, key: str, value: Any) -> None:
        """تعيين قيمة في التكوين"""
        keys = key.split(".")
        config = self._config
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        config[keys[-1]] = value

    def update(self, updates: Dict[str, Any]) -> None:
        """تحديث متعدد القيم"""
        for key, value in updates.items():
            self.set(key, value)

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None


# مسارات المجلدات
ROOT_DIR = Path(__file__).parent.parent
CONFIG_DIR = ROOT_DIR / "config"
MODELS_DIR = ROOT_DIR / "models"
OUTPUT_DIR = ROOT_DIR / "output"
INPUT_DIR = ROOT_DIR / "input"
LOGS_DIR = ROOT_DIR / "logs"

# إنشاء المجلدات
for d in [CONFIG_DIR, MODELS_DIR, OUTPUT_DIR, INPUT_DIR, LOGS_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# مثيل التكوين العام
config = Config()

# تصدير المسارات
__all__ = ["config", "CONFIG_DIR", "MODELS_DIR", "OUTPUT_DIR", "INPUT_DIR", "LOGS_DIR", "ROOT_DIR"]