"""
وحدة دمج الفيديو والصوت باستخدام FFmpeg
"""
import uuid
import subprocess
import shutil
from pathlib import Path
from typing import Optional, Union, List
from ayman_elsherbeny_automation.config import config
from ayman_elsherbeny_automation.utils.logging import logger


class VideoMerger:
    """فئة دمج الفيديو مع الصوت"""

    def __init__(
        self,
        video_codec: Optional[str] = None,
        audio_codec: Optional[str] = None,
        video_preset: Optional[str] = None,
        crf: Optional[int] = None,
        audio_bitrate: Optional[str] = None,
        output_format: Optional[str] = None,
    ):
        self.video_codec = video_codec or config.get("merge.video_codec", "libx264")
        self.audio_codec = audio_codec or config.get("merge.audio_codec", "aac")
        self.video_preset = video_preset or config.get("merge.video_preset", "medium")
        self.crf = crf or config.get("merge.crf", 23)
        self.audio_bitrate = audio_bitrate or config.get("merge.audio_bitrate", "128k")
        self.output_format = output_format or config.get("merge.output_format", "mp4")

        # التحقق من وجود FFmpeg
        self.ffmpeg_path = shutil.which("ffmpeg")
        if not self.ffmpeg_path:
            raise RuntimeError("FFmpeg not found. Please install FFmpeg and add to PATH.")

    def _run_ffmpeg(self, cmd: List[str]) -> subprocess.CompletedProcess:
        """تشغيل أمر FFmpeg"""
        logger.debug(f"Running FFmpeg: {' '.join(cmd)}")
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            logger.error(f"FFmpeg error: {result.stderr}")
            raise RuntimeError(f"FFmpeg failed: {result.stderr}")
        return result

    def get_video_info(self, video_path: Union[str, Path]) -> dict:
        """الحصول على معلومات الفيديو باستخدام ffprobe"""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        cmd = [
            "ffprobe",
            "-v", "quiet",
            "-print_format", "json",
            "-show_format",
            "-show_streams",
            str(video_path),
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr}")

        import json
        return json.loads(result.stdout)

    def get_duration(self, media_path: Union[str, Path]) -> float:
        """الحصول على مدة ملف الوسائط بالثواني"""
        info = self.get_video_info(media_path)
        duration = info.get("format", {}).get("duration")
        if duration:
            return float(duration)
        # محاولة من الدفق الأول
        for stream in info.get("streams", []):
            if stream.get("codec_type") in ("video", "audio"):
                dur = stream.get("duration")
                if dur:
                    return float(dur)
        return 0.0

    def merge(
        self,
        video_path: Union[str, Path],
        audio_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        audio_mix_mode: Optional[str] = None,
        audio_volume: Optional[float] = None,
        video_volume: Optional[float] = None,
        loop_video: bool = True,
        trim_to_audio: bool = True,
        shorted: bool = False,
    ) -> Path:
        """
        دمج الفيديو مع الصوت

        Args:
            video_path: مسار ملف الفيديو
            audio_path: مسار ملف الصوت
            output_path: مسار ملف الإخراج
            audio_mix_mode: وضع دمج الصوت (replace, mix, sidechain)
            audio_volume: مستوى صوت الصوت (0.0-2.0)
            video_volume: مستوى صوت الفيديو الأصلي (0.0-2.0)
            loop_video: تكرار الفيديو ليتناسب مع طول الصوت
            trim_to_audio: قص الفيديو ليتناسب مع طول الصوت
            shorted: إنهاء عند أقصر دفق

        Returns:
            مسار ملف الفيديو المدمج
        """
        video_path = Path(video_path)
        audio_path = Path(audio_path)

        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")
        if not audio_path.exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        if output_path is None:
            output_path = config.OUTPUT_DIR / f"merged_{uuid.uuid4().hex[:8]}.{self.output_format}"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        mix_mode = audio_mix_mode or config.get("merge.audio_mix_mode", "replace")
        a_vol = audio_volume if audio_volume is not None else config.get("merge.audio_volume", 1.0)
        v_vol = video_volume if video_volume is not None else config.get("merge.video_volume", 1.0)

        # بناء أمر FFmpeg
        cmd = [
            "ffmpeg",
            "-y",  # الكتابة فوق الملف الموجود
            "-i", str(video_path),
            "-i", str(audio_path),
        ]

        # خيارات الفيديو
        cmd.extend([
            "-c:v", self.video_codec,
            "-preset", self.video_preset,
            "-crf", str(self.crf),
        ])

        # خيارات الصوت
        cmd.extend([
            "-c:a", self.audio_codec,
            "-b:a", self.audio_bitrate,
        ])

        # فلتر الصوت
        filter_complex = []

        if mix_mode == "replace":
            # استبدال صوت الفيديو بالصوت الجديد
            filter_complex.append("[1:a]volume={a_vol}[a_out]".format(a_vol=a_vol))
            cmd.extend(["-map", "0:v:0", "-map", "[a_out]"])

        elif mix_mode == "mix":
            # خلط الصوتين
            filter_complex.append(
                "[0:a]volume={v_vol}[v_aud];"
                "[1:a]volume={a_vol}[a_aud];"
                "[v_aud][a_aud]amix=inputs=2:duration=first:dropout_transition=2[a_out]".format(
                    v_vol=v_vol, a_vol=a_vol
                )
            )
            cmd.extend(["-map", "0:v:0", "-map", "[a_out]"])

        elif mix_mode == "sidechain":
            # Sidechain: خفض صوت الفيديو عند وجود صوت في المسار الصوتي
            filter_complex.append(
                "[1:a]volume={a_vol}[a_main];"
                "[0:a]volume={v_vol}[v_aud];"
                "[v_aud][a_main]sidechaincompress=threshold=0.003:ratio=20:attack=20:release=2000[a_out]".format(
                    a_vol=a_vol, v_vol=v_vol
                )
            )
            cmd.extend(["-map", "0:v:0", "-map", "[a_out]"])

        else:
            raise ValueError(f"Unknown audio_mix_mode: {mix_mode}")

        # التعامل مع اختلاف المدة
        if loop_video:
            # تكرار الفيديو (stream_loop)
            cmd.insert(2, "-stream_loop")
            cmd.insert(3, "-1")

        if trim_to_audio or shorted:
            cmd.extend(["-shortest"])

        # إضافة filter_complex إذا وجدت
        if filter_complex:
            cmd.extend(["-filter_complex", ";".join(filter_complex)])

        # مسار الإخراج
        cmd.append(str(output_path))

        logger.info(f"Merging video: {video_path.name} + audio: {audio_path.name}")
        logger.info(f"Output: {output_path}")

        self._run_ffmpeg(cmd)

        logger.info(f"Merge completed: {output_path}")
        return output_path

    def concatenate_videos(
        self,
        video_paths: List[Union[str, Path]],
        output_path: Optional[Union[str, Path]] = None,
        transition_duration: float = 0.0,
    ) -> Path:
        """دمج عدة فيديوهات متتالية"""
        video_paths = [Path(p) for p in video_paths]
        for p in video_paths:
            if not p.exists():
                raise FileNotFoundError(f"Video not found: {p}")

        if output_path is None:
            output_path = config.OUTPUT_DIR / f"concat_{uuid.uuid4().hex[:8]}.{self.output_format}"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # إنشاء ملف قائمة للدمج
        list_file = output_path.parent / f"concat_list_{uuid.uuid4().hex[:8]}.txt"
        with open(list_file, "w", encoding="utf-8") as f:
            for p in video_paths:
                f.write(f"file '{p.absolute()}'\n")

        cmd = [
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(list_file),
            "-c", "copy",
            str(output_path),
        ]

        if transition_duration > 0:
            # استخدام فلتر الانتقال (أكثر تعقيداً)
            pass

        logger.info(f"Concatenating {len(video_paths)} videos")
        self._run_ffmpeg(cmd)

        # حذف ملف القائمة المؤقت
        list_file.unlink(missing_ok=True)

        logger.info(f"Concatenation completed: {output_path}")
        return output_path

    def extract_audio(
        self,
        video_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        audio_codec: Optional[str] = None,
    ) -> Path:
        """استخراج الصوت من الفيديو"""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if output_path is None:
            output_path = config.OUTPUT_DIR / f"{video_path.stem}_audio.mp3"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vn",
            "-c:a", audio_codec or "libmp3lame",
            "-q:a", "2",
            str(output_path),
        ]

        logger.info(f"Extracting audio from: {video_path}")
        self._run_ffmpeg(cmd)

        logger.info(f"Audio extracted: {output_path}")
        return output_path

    def resize_video(
        self,
        video_path: Union[str, Path],
        output_path: Optional[Union[str, Path]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        keep_aspect: bool = True,
    ) -> Path:
        """تغيير أبعاد الفيديو"""
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        if output_path is None:
            output_path = config.OUTPUT_DIR / f"{video_path.stem}_resized.{self.output_format}"
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        # بناء فلتر القياس
        if width and height:
            if keep_aspect:
                scale_filter = f"scale='if(gt(iw,ih),{width},-2)':'if(gt(iw,ih),-2,{height})'"
            else:
                scale_filter = f"scale={width}:{height}"
        elif width:
            scale_filter = f"scale={width}:-2"
        elif height:
            scale_filter = f"scale=-2:{height}"
        else:
            raise ValueError("Either width or height must be specified")

        cmd = [
            "ffmpeg", "-y",
            "-i", str(video_path),
            "-vf", scale_filter,
            "-c:v", self.video_codec,
            "-preset", self.video_preset,
            "-crf", str(self.crf),
            "-c:a", "copy",
            str(output_path),
        ]

        logger.info(f"Resizing video: {video_path} -> {width}x{height}")
        self._run_ffmpeg(cmd)

        logger.info(f"Resize completed: {output_path}")
        return output_path


def create_video_merger(**kwargs) -> VideoMerger:
    """دالة مساعدة لإنشاء كائن دمج الفيديو"""
    return VideoMerger(**kwargs)