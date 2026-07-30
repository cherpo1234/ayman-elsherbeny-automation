"""
Core Automation Class - أيمن الشربيني
Main orchestrator for Text/Image to Video with Audio
"""
import uuid
import subprocess
from pathlib import Path
from typing import Optional, Union, List, Dict, Any

from ayman_elsherbeny_automation import config, logger, OUTPUT_DIR as CONFIG_OUTPUT_DIR
from ayman_elsherbeny_automation.generation.text_to_image import create_text_to_image_generator
from ayman_elsherbeny_automation.generation.audio_generator import create_audio_generator


class AymanElsherbenyAutomation:
    """
    الفئة الرئيسية لأوتوميشن "أيمن الشربيني"

    تدعم:
    - Text-to-Video (نص إلى فيديو)
    - Image-to-Video (صورة إلى فيديو)
    - Text-to-Speech (نص إلى كلام)
    - دمج الفيديو والصوت
    - معالجة دفعية
    """

    def __init__(
        self,
        video_model: Optional[str] = None,
        tts_engine: Optional[str] = None,
        device: Optional[str] = None,
        dtype: Optional[str] = None,
        output_dir: Optional[Union[str, Path]] = None,
    ):
        self.video_model = video_model or config.get("video.model", "stabilityai/stable-video-diffusion-img2vid-xt")
        self.tts_engine = tts_engine or config.get("audio.tts_engine", "edge-tts")
        self.device = device or config.get("hardware.device", "auto")
        self.dtype = dtype or config.get("video.dtype", "float16")
        self.output_dir = Path(output_dir) if output_dir else CONFIG_OUTPUT_DIR

        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Lazy initialization
        self._text_to_image = None
        self._audio_generator = None

        logger.info(f"Initializing Ayman Elsherbeny Automation")
        logger.info(f"Video model: {self.video_model}")
        logger.info(f"TTS engine: {self.tts_engine}")
        logger.info(f"Device: {self.device}")
        logger.info(f"Output dir: {self.output_dir}")

    @property
    def text_to_image(self):
        if self._text_to_image is None:
            logger.info("Loading text-to-image generator...")
            self._text_to_image = create_text_to_image_generator()
        return self._text_to_image

    @property
    def audio_generator(self):
        if self._audio_generator is None:
            logger.info("Loading audio generator...")
            self._audio_generator = create_audio_generator()
        return self._audio_generator

    def text_to_video(
        self,
        prompt: str,
        audio_text: Optional[str] = None,
        negative_prompt: Optional[str] = None,
        audio_voice: Optional[str] = None,
        audio_language: Optional[str] = None,
        num_frames: Optional[int] = None,
        fps: Optional[int] = None,
        motion_bucket_id: Optional[int] = None,
        noise_aug_strength: Optional[float] = None,
        seed: Optional[int] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        output_name: Optional[str] = None,
        keep_intermediate: bool = False,
    ) -> Dict[str, Path]:
        """
        تحويل نص إلى فيديو مع صوت

        Args:
            prompt: نص وصف الفيديو
            audio_text: نص الصوت (إذا لم يحدد، يستخدم prompt)
            negative_prompt: نص سلبي لتوليد الصورة
            audio_voice: صوت TTS
            audio_language: لغة TTS
            num_frames: عدد الإطارات
            fps: معدل الإطارات
            motion_bucket_id: معرف حاوية الحركة
            noise_aug_strength: قوة ضوضاء الإضافة
            seed: بذرة العشوائية
            width/height: أبعاد الفيديو
            output_name: اسم ملف الإخراج (بدون امتداد)
            keep_intermediate: الاحتفاظ بالملفات الوسيطة

        Returns:
            قاموس بمسارات الملفات: {"video": ..., "audio": ..., "merged": ...}
        """
        logger.info(f"Starting Text-to-Video: {prompt[:100]}...")

        # 1. توليد صورة من النص
        logger.info("Step 1/4: Generating image from text...")
        image = self.text_to_image.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            guidance_scale=config.get("text_to_image.guidance_scale", 7.5),
            num_inference_steps=config.get("text_to_image.steps", 30),
            seed=seed,
        )

        # 2. توليد الصوت
        audio_text = audio_text or prompt
        logger.info("Step 2/4: Generating audio...")
        audio_path = self.audio_generator.generate(
            text=audio_text,
            voice=audio_voice,
            language=audio_language,
        )

        # 3. إنشاء فيديو من الصورة مع الصوت
        logger.info("Step 3/4: Creating video from image...")
        import subprocess
        import tempfile

        if output_name is None:
            output_name = f"txt2vid_{uuid.uuid4().hex[:8]}"

        merged_path = self.output_dir / f"{output_name}_final.mp4"

        image_path = self.output_dir / f"{output_name}_temp.png"
        image.save(image_path)

        # الحصول على مدة الصوت
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(audio_path)],
            capture_output=True, text=True
        )
        duration = float(result.stdout.strip()) if result.stdout else 10.0

        fps_val = fps or 24
        total_frames = int(duration * fps_val)

        # إنشاء فيديو من الصورة + الصوت باستخدام FFmpeg
        cmd = [
            "ffmpeg", "-y",
            "-loop", "1",
            "-i", str(image_path),
            "-i", str(audio_path),
            "-c:v", "libx264",
            "-t", str(duration),
            "-pix_fmt", "yuv420p",
            "-vf", f"scale=trunc(iw/2)*2:trunc(ih/2)*2",
            "-c:a", "aac",
            "-b:a", "128k",
            "-shortest",
            str(merged_path),
        ]
        subprocess.run(cmd, check=True, capture_output=True)

        image_path.unlink(missing_ok=True)

        result = {
            "video": merged_path,
            "audio": audio_path,
            "merged": merged_path,
        }

        logger.info(f"Text-to-Video completed: {merged_path}")
        return result

    def image_to_video(
        self,
        image_path: Union[str, Path],
        audio_text: Optional[str] = None,
        audio_voice: Optional[str] = None,
        audio_language: Optional[str] = None,
        num_frames: Optional[int] = None,
        fps: Optional[int] = None,
        motion_bucket_id: Optional[int] = None,
        noise_aug_strength: Optional[float] = None,
        seed: Optional[int] = None,
        output_name: Optional[str] = None,
        keep_intermediate: bool = False,
    ) -> Dict[str, Path]:
        """
        تحويل صورة إلى فيديو مع صوت

        Args:
            image_path: مسار الصورة المدخلة
            audio_text: نص الصوت
            audio_voice: صوت TTS
            audio_language: لغة TTS
            num_frames: عدد الإطارات
            fps: معدل الإطارات
            motion_bucket_id: معرف حاوية الحركة
            noise_aug_strength: قوة ضوضاء الإضافة
            seed: بذرة العشوائية
            output_name: اسم ملف الإخراج
            keep_intermediate: الاحتفاظ بالملفات الوسيطة

        Returns:
            قاموس بمسارات الملفات
        """
        logger.info(f"Starting Image-to-Video: {image_path}")

        # تحميل الصورة
        from PIL import Image
        image = Image.open(image_path).convert("RGB")

        # توليد الفيديو
        logger.info("Step 1/3: Generating video from image...")
        video_frames = self.video_generator.generate_from_image(
            image=image,
            num_frames=num_frames,
            fps=fps,
            motion_bucket_id=motion_bucket_id,
            noise_aug_strength=noise_aug_strength,
            decode_chunk_size=config.get("video.decode_chunk_size", 2),
            seed=seed,
        )

        # توليد الصوت
        logger.info("Step 2/3: Generating audio...")
        audio_text = audio_text or f"Video generated from image: {Path(image_path).stem}"
        audio_path = self.audio_generator.generate(
            text=audio_text,
            voice=audio_voice,
            language=audio_language,
        )

        # دمج
        logger.info("Step 3/3: Merging video and audio...")
        if output_name is None:
            output_name = f"img2vid_{uuid.uuid4().hex[:8]}"

        video_path = self.output_dir / f"{output_name}_video.mp4"
        merged_path = self.output_dir / f"{output_name}_final.mp4"

        self.video_generator.save_video(video_frames, video_path, fps=fps or 7)
        merged_path = self.video_merger.merge(
            video_path=video_path,
            audio_path=audio_path,
            output_path=merged_path,
        )

        result = {
            "video": video_path,
            "audio": audio_path,
            "merged": merged_path,
        }

        if not keep_intermediate:
            video_path.unlink(missing_ok=True)

        logger.info(f"Image-to-Video completed: {merged_path}")
        return result

    def batch_process(
        self,
        inputs: List[Dict[str, Any]],
        mode: str = "text_to_video",
        output_dir: Optional[Union[str, Path]] = None,
    ) -> List[Dict[str, Path]]:
        """
        معالجة دفعية لمدخلات متعددة

        Args:
            inputs: قائمة قواميس المدخلات
            mode: وضع المعالجة (text_to_video, image_to_video)
            output_dir: مجلد الإخراج

        Returns:
            قائمة النتائج
        """
        if output_dir:
            out_dir = Path(output_dir)
        else:
            out_dir = self.output_dir / "batch"
        out_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for i, inp in enumerate(inputs):
            logger.info(f"Processing item {i+1}/{len(inputs)}")
            try:
                output_name = inp.get("output_name", f"batch_{i:04d}")

                if mode == "text_to_video":
                    result = self.text_to_video(
                        prompt=inp["prompt"],
                        audio_text=inp.get("audio_text"),
                        negative_prompt=inp.get("negative_prompt"),
                        audio_voice=inp.get("voice"),
                        audio_language=inp.get("language"),
                        num_frames=inp.get("frames"),
                        fps=inp.get("fps"),
                        motion_bucket_id=inp.get("motion_bucket"),
                        noise_aug_strength=inp.get("noise_aug"),
                        seed=inp.get("seed"),
                        width=inp.get("width"),
                        height=inp.get("height"),
                        output_name=output_name,
                        keep_intermediate=inp.get("keep_intermediate", False),
                    )
                elif mode == "image_to_video":
                    result = self.image_to_video(
                        image_path=inp["image_path"],
                        audio_text=inp.get("audio_text"),
                        audio_voice=inp.get("voice"),
                        audio_language=inp.get("language"),
                        num_frames=inp.get("frames"),
                        fps=inp.get("fps"),
                        motion_bucket_id=inp.get("motion_bucket"),
                        noise_aug_strength=inp.get("noise_aug"),
                        seed=inp.get("seed"),
                        output_name=output_name,
                        keep_intermediate=inp.get("keep_intermediate", False),
                    )
                else:
                    raise ValueError(f"Unknown mode: {mode}")

                results.append(result)
            except Exception as e:
                logger.error(f"Failed to process item {i}: {e}")
                results.append(None)

        return results

    def generate_audio_only(
        self,
        text: str,
        voice: Optional[str] = None,
        language: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
    ) -> Path:
        """توليد صوت فقط"""
        return self.audio_generator.generate(
            text=text,
            output_path=output_path,
            voice=voice,
            language=language,
        )

    def unload_models(self) -> None:
        """إلغاء تحميل جميع النماذج لتحرير الذاكرة"""
        if self._text_to_image:
            self._text_to_image.unload()
            self._text_to_image = None
        if self._audio_generator:
            self._audio_generator = None

        from ayman_elsherbeny_automation.utils.device import clear_memory
        clear_memory()
        logger.info("All models unloaded")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.unload_models()
        return False


def create_automation(**kwargs) -> AymanElsherbenyAutomation:
    """دالة مساعدة لإنشاء كائن الأوتوميشن"""
    return AymanElsherbenyAutomation(**kwargs)