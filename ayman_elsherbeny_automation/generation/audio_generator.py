"""
وحدة توليد الصوت (Text-to-Speech)
"""
import uuid
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Union, List
from ayman_elsherbeny_automation.config import config, OUTPUT_DIR
from ayman_elsherbeny_automation.utils.logging import logger


class AudioGenerator:
    """فئة توليد الصوت من النص"""

    def __init__(
        self,
        engine: Optional[str] = None,
        language: Optional[str] = None,
        voice: Optional[str] = None,
        speed: Optional[float] = None,
        pitch: Optional[int] = None,
        volume: Optional[float] = None,
    ):
        self.engine = engine or config.get("audio.tts_engine", "edge-tts")
        self.language = language or config.get("audio.language", "ar")
        self.voice = voice or config.get("audio.voice", "ar-SA-HamedNeural")
        self.speed = speed if speed is not None else config.get("audio.speed", 1.0)
        self.pitch = pitch if pitch is not None else config.get("audio.pitch", 0)
        self.volume = volume if volume is not None else config.get("audio.volume", 1.0)

        self._validate_engine()

    def _validate_engine(self) -> None:
        """التحقق من توفر المحرك المختار"""
        if self.engine == "edge-tts":
            if not self._check_edge_tts():
                raise RuntimeError("edge-tts not installed. Run: pip install edge-tts")
        elif self.engine == "coqui-tts":
            if not self._check_coqui_tts():
                raise RuntimeError("Coqui TTS not installed. Run: pip install TTS")
        elif self.engine == "gtts":
            if not self._check_gtts():
                raise RuntimeError("gTTS not installed. Run: pip install gtts")
        elif self.engine == "pyttsx3":
            if not self._check_pyttsx3():
                raise RuntimeError("pyttsx3 not installed. Run: pip install pyttsx3")
        else:
            raise ValueError(f"Unsupported TTS engine: {self.engine}")

    def _check_edge_tts(self) -> bool:
        try:
            import edge_tts
            return True
        except ImportError:
            return False

    def _check_coqui_tts(self) -> bool:
        try:
            from TTS.api import TTS
            return True
        except ImportError:
            return False

    def _check_gtts(self) -> bool:
        try:
            import gtts
            return True
        except ImportError:
            return False

    def _check_pyttsx3(self) -> bool:
        try:
            import pyttsx3
            return True
        except ImportError:
            return False

    async def generate_edge_tts(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        voice: Optional[str] = None,
        rate: Optional[str] = None,
        volume: Optional[str] = None,
        pitch: Optional[str] = None,
    ) -> Path:
        """توليد صوت باستخدام Edge TTS (مايكروسوفت)"""
        import edge_tts

        voice = voice or self.voice
        rate = rate or f"{int((self.speed - 1) * 100):+d}%"
        volume = volume or f"{int((self.volume - 1) * 100):+d}%"
        pitch = pitch or f"{self.pitch:+d}Hz"

        if output_path is None:
            output_path = OUTPUT_DIR / f"tts_{uuid.uuid4().hex[:8]}.mp3"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        communicate = edge_tts.Communicate(text, voice, rate=rate, volume=volume, pitch=pitch)
        await communicate.save(str(output_path))

        logger.info(f"Edge TTS generated: {output_path}")
        return output_path

    def generate_coqui_tts(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        model: Optional[str] = None,
        speaker: Optional[str] = None,
        language: Optional[str] = None,
    ) -> Path:
        """توليد صوت باستخدام Coqui TTS"""
        from TTS.api import TTS

        model = model or config.get("audio.coqui_model", "tts_models/multilingual/multi-dataset/xtts_v2")
        speaker = speaker or self.voice
        language = language or self.language

        if output_path is None:
            output_path = OUTPUT_DIR / f"tts_coqui_{uuid.uuid4().hex[:8]}.wav"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        tts = TTS(model)
        tts.tts_to_file(
            text=text,
            file_path=str(output_path),
            speaker=speaker,
            language=language,
            speed=self.speed,
        )

        logger.info(f"Coqui TTS generated: {output_path}")
        return output_path

    def generate_gtts(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        lang: Optional[str] = None,
        slow: bool = False,
    ) -> Path:
        """توليد صوت باستخدام gTTS (Google Translate TTS)"""
        from gtts import gTTS

        lang = lang or self.language

        if output_path is None:
            output_path = OUTPUT_DIR / f"tts_gtts_{uuid.uuid4().hex[:8]}.mp3"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        tts = gTTS(text=text, lang=lang, slow=slow)
        tts.save(str(output_path))

        logger.info(f"gTTS generated: {output_path}")
        return output_path

    def generate_pyttsx3(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        voice_id: Optional[str] = None,
        rate: Optional[int] = None,
        volume: Optional[float] = None,
    ) -> Path:
        """توليد صوت باستخدام pyttsx3 (محلي، لا يحتاج إنترنت)"""
        import pyttsx3

        if output_path is None:
            output_path = OUTPUT_DIR / f"tts_pyttsx3_{uuid.uuid4().hex[:8]}.wav"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        engine = pyttsx3.init()

        if voice_id:
            engine.setProperty("voice", voice_id)

        if rate:
            engine.setProperty("rate", rate)
        else:
            # تحويل speed إلى معدل
            engine.setProperty("rate", int(200 * self.speed))

        if volume:
            engine.setProperty("volume", volume)
        else:
            engine.setProperty("volume", self.volume)

        engine.save_to_file(text, str(output_path))
        engine.runAndWait()

        logger.info(f"pyttsx3 generated: {output_path}")
        return output_path

    def generate(
        self,
        text: str,
        output_path: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> Path:
        """
        توليد صوت من نص باستخدام المحرك المحدد

        Args:
            text: النص المراد تحويله لصوت
            output_path: مسار ملف الإخراج
            **kwargs: معاملات إضافية خاصة بكل محرك

        Returns:
            مسار ملف الصوت المولد
        """
        if not text or not text.strip():
            raise ValueError("Text cannot be empty")

        if self.engine == "edge-tts":
            import asyncio
            return asyncio.run(self.generate_edge_tts(text, output_path, **kwargs))
        elif self.engine == "coqui-tts":
            return self.generate_coqui_tts(text, output_path, **kwargs)
        elif self.engine == "gtts":
            return self.generate_gtts(text, output_path, **kwargs)
        elif self.engine == "pyttsx3":
            return self.generate_pyttsx3(text, output_path, **kwargs)
        else:
            raise ValueError(f"Unsupported TTS engine: {self.engine}")

    def generate_batch(
        self,
        texts: List[str],
        output_dir: Optional[Union[str, Path]] = None,
        prefix: str = "tts_batch",
    ) -> List[Path]:
        """توليد ملفات صوتية متعددة"""
        if output_dir is None:
            output_dir = OUTPUT_DIR / "batch"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for i, text in enumerate(texts):
            output_path = output_dir / f"{prefix}_{i:04d}.mp3"
            try:
                result = self.generate(text, output_path)
                results.append(result)
            except Exception as e:
                logger.error(f"Failed to generate audio for text {i}: {e}")
                results.append(None)

        return results

    @staticmethod
    def list_edge_voices(language: Optional[str] = None) -> List[dict]:
        """قائمة الأصوات المتاحة في Edge TTS"""
        import edge_tts
        import asyncio

        async def _list():
            voices = await edge_tts.list_voices()
            if language:
                voices = [v for v in voices if v["Locale"].startswith(language)]
            return voices

        return asyncio.run(_list())

    @staticmethod
    def list_coqui_models() -> List[str]:
        """قائمة نماذج Coqui TTS المتاحة"""
        from TTS.api import TTS
        return TTS.list_models()


def create_audio_generator(**kwargs) -> AudioGenerator:
    """دالة مساعدة لإنشاء مولد صوت"""
    return AudioGenerator(**kwargs)