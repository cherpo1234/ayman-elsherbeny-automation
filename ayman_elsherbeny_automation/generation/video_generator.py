"""
وحدة توليد الفيديو (Stable Video Diffusion)
"""
import uuid
import torch
from pathlib import Path
from typing import Optional, Union, List
from PIL import Image
from diffusers import StableVideoDiffusionPipeline
from ayman_elsherbeny_automation.config import config, OUTPUT_DIR
from ayman_elsherbeny_automation.utils.device import get_device, get_dtype, optimize_model, clear_memory
from ayman_elsherbeny_automation.utils.logging import logger


class VideoGenerator:
    """فئة توليد الفيديو من نص/صورة باستخدام Stable Video Diffusion"""

    def __init__(
        self,
        model_id: Optional[str] = None,
        device: Optional[Union[str, torch.device]] = None,
        dtype: Optional[Union[str, torch.dtype]] = None,
        enable_cpu_offload: bool = False,
    ):
        self.model_id = model_id or config.get("video.model", "stabilityai/stable-video-diffusion-img2vid-xt")
        self.device = get_device(device)
        self.dtype = get_dtype(dtype)
        self.enable_cpu_offload = enable_cpu_offload
        self.pipeline = None
        self._load_pipeline()

    def _load_pipeline(self) -> None:
        """تحميل خط أنابيب SVD"""
        logger.info(f"Loading SVD pipeline: {self.model_id} on {self.device} with {self.dtype}")

        try:
            self.pipeline = StableVideoDiffusionPipeline.from_pretrained(
                self.model_id,
                torch_dtype=self.dtype,
                variant="fp16" if self.dtype == torch.float16 else None,
            )
            self.pipeline = optimize_model(self.pipeline, self.device)

            if self.enable_cpu_offload:
                self.pipeline.enable_model_cpu_offload()

            logger.info("SVD pipeline loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load SVD pipeline: {e}")
            raise

    def generate_from_image(
        self,
        image: Union[str, Path, Image.Image],
        num_frames: Optional[int] = None,
        fps: Optional[int] = None,
        motion_bucket_id: Optional[int] = None,
        noise_aug_strength: Optional[float] = None,
        decode_chunk_size: Optional[int] = None,
        seed: Optional[int] = None,
        output_path: Optional[Union[str, Path]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
    ) -> List[Image.Image]:
        """
        توليد فيديو من صورة (Image-to-Video)

        Args:
            image: صورة الإدخال (مسار أو كائن PIL)
            num_frames: عدد الإطارات
            fps: معدل الإطارات
            motion_bucket_id: معرّف دلو الحركة (1-255)
            noise_aug_strength: قوة ضوضاء التقوية
            decode_chunk_size: حجم قطعة التفكيك
            seed: البذرة العشوائية
            output_path: مسار حفظ الفيديو
            width: عرض الصورة
            height: ارتفاع الصورة

        Returns:
            قائمة إطارات PIL
        """
        if self.pipeline is None:
            self._load_pipeline()

        # تحميل الصورة
        if isinstance(image, (str, Path)):
            image = Image.open(image).convert("RGB")

        # تغيير الحجم إذا لزم
        target_width = width or config.get("video.width", 1024)
        target_height = height or config.get("video.height", 576)

        if image.size != (target_width, target_height):
            image = image.resize((target_width, target_height), Image.LANCZOS)

        # المعاملات
        num_frames = num_frames or config.get("video.num_frames", 25)
        fps = fps or config.get("video.fps", 7)
        motion_bucket_id = motion_bucket_id or config.get("video.motion_bucket_id", 127)
        noise_aug_strength = noise_aug_strength or config.get("video.noise_aug_strength", 0.02)
        decode_chunk_size = decode_chunk_size or config.get("video.decode_chunk_size", 2)

        if seed is None:
            seed = config.get("video.seed", -1)

        if seed == -1:
            seed = torch.randint(0, 2**32 - 1, (1,)).item()

        generator = torch.Generator(device=self.device).manual_seed(seed)

        logger.info(f"Generating video from image: {num_frames} frames, {fps} fps, seed={seed}")

        # تفريغ الذاكرة قبل التوليد
        clear_memory()

        # توليد الفيديو
        with torch.inference_mode():
            frames = self.pipeline(
                image=image,
                num_frames=num_frames,
                fps=fps,
                motion_bucket_id=motion_bucket_id,
                noise_aug_strength=noise_aug_strength,
                decode_chunk_size=decode_chunk_size,
                generator=generator,
            ).frames[0]

        logger.info(f"Generated {len(frames)} frames")

        # حفظ الفيديو إذا طُلب
        if output_path:
            self.save_video(frames, output_path, fps)

        return frames

    def generate_from_text(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        num_frames: Optional[int] = None,
        fps: Optional[int] = None,
        motion_bucket_id: Optional[int] = None,
        noise_aug_strength: Optional[float] = None,
        decode_chunk_size: Optional[int] = None,
        seed: Optional[int] = None,
        output_path: Optional[Union[str, Path]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        num_inference_steps: Optional[int] = None,
    ) -> List[Image.Image]:
        """
        توليد فيديو من نص (Text-to-Video عبر Text-to-Image ثم Image-to-Video)

        ملاحظة: SVD هو نموذج Image-to-Video. لتوليد فيديو من نص، نحتاج أولاً
        لتوليد صورة من النص ثم تحويلها لفيديو.
        """
        # هذه الدالة تحتاج إلى نموذج Text-to-Image منفصل
        # سنقوم بتوليد صورة أولاً ثم فيديو
        from ayman_elsherbeny_automation.generation.text_to_image import TextToImageGenerator

        logger.info(f"Text-to-Video: Generating image first from prompt: {prompt[:50]}...")

        # توليد صورة من النص
        t2i = TextToImageGenerator()
        image = t2i.generate(
            prompt=prompt,
            negative_prompt=negative_prompt,
            width=width,
            height=height,
            guidance_scale=guidance_scale,
            num_inference_steps=num_inference_steps,
            seed=seed,
        )

        # تحويل الصورة إلى فيديو
        return self.generate_from_image(
            image=image,
            num_frames=num_frames,
            fps=fps,
            motion_bucket_id=motion_bucket_id,
            noise_aug_strength=noise_aug_strength,
            decode_chunk_size=decode_chunk_size,
            seed=seed,
            output_path=output_path,
            width=width,
            height=height,
        )

    def save_video(
        self,
        frames: List[Image.Image],
        output_path: Union[str, Path],
        fps: int = 7,
        format: str = "mp4",
    ) -> Path:
        """حفظ الإطارات كملف فيديو"""
        from ayman_elsherbeny_automation.generation.video_merger import create_video_merger

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # حفظ الإطارات كصور مؤقتة
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir = Path(tmpdir)
            for i, frame in enumerate(frames):
                frame.save(tmpdir / f"frame_{i:05d}.png")

            # استخدام FFmpeg لتحويل الإطارات لفيديو
            merger = create_video_merger()
            # نحتاج لإنشاء فيديو من إطارات - استخدم concat
            import subprocess
            cmd = [
                "ffmpeg", "-y",
                "-framerate", str(fps),
                "-i", str(tmpdir / "frame_%05d.png"),
                "-c:v", "libx264",
                "-preset", "medium",
                "-crf", "23",
                "-pix_fmt", "yuv420p",
                str(output_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise RuntimeError(f"Failed to create video: {result.stderr}")

        logger.info(f"Video saved: {output_path}")
        return output_path

    def generate_batch(
        self,
        images: List[Union[str, Path, Image.Image]],
        output_dir: Optional[Union[str, Path]] = None,
        **kwargs,
    ) -> List[Path]:
        """توليد فيديوهات متعددة من قائمة صور"""
        if output_dir is None:
            output_dir = OUTPUT_DIR / "batch"
        else:
            output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)

        results = []
        for i, image in enumerate(images):
            output_path = output_dir / f"video_{i:04d}.mp4"
            try:
                frames = self.generate_from_image(image, output_path=output_path, **kwargs)
                results.append(output_path)
            except Exception as e:
                logger.error(f"Failed to generate video {i}: {e}")
                results.append(None)

        return results


class TextToImageGenerator:
    """فئة توليد الصور من النص (للاستخدام مع Text-to-Video)"""

    def __init__(
        self,
        model_id: Optional[str] = None,
        refiner_id: Optional[str] = None,
        device: Optional[Union[str, torch.device]] = None,
        dtype: Optional[Union[str, torch.dtype]] = None,
    ):
        self.model_id = model_id or config.get("text_to_image.model_path", "stabilityai/stable-diffusion-xl-base-1.0")
        self.refiner_id = refiner_id or config.get("text_to_image.refiner_path", "stabilityai/stable-diffusion-xl-refiner-1.0")
        self.device = get_device(device)
        self.dtype = get_dtype(dtype)
        self.pipeline = None
        self.refiner = None

    def _load_pipelines(self) -> None:
        """تحميل خطوط أنابيب SDXL الأساسي والمحسن"""
        from diffusers import DiffusionPipeline

        logger.info(f"Loading SDXL pipeline: {self.model_id}")

        self.pipeline = DiffusionPipeline.from_pretrained(
            self.model_id,
            torch_dtype=self.dtype,
            variant="fp16" if self.dtype == torch.float16 else None,
            use_safetensors=True,
        )
        self.pipeline = optimize_model(self.pipeline, self.device)

        logger.info(f"Loading SDXL refiner: {self.refiner_id}")
        self.refiner = DiffusionPipeline.from_pretrained(
            self.refiner_id,
            torch_dtype=self.dtype,
            variant="fp16" if self.dtype == torch.float16 else None,
            use_safetensors=True,
        )
        self.refiner = optimize_model(self.refiner, self.device)

    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        num_inference_steps: Optional[int] = None,
        seed: Optional[int] = None,
        use_refiner: bool = True,
    ) -> Image.Image:
        """توليد صورة من نص"""
        if self.pipeline is None:
            self._load_pipelines()

        width = width or config.get("text_to_image.width", 1024)
        height = height or config.get("text_to_image.height", 576)
        guidance_scale = guidance_scale or config.get("text_to_image.guidance_scale", 7.5)
        num_inference_steps = num_inference_steps or config.get("text_to_image.steps", 30)

        if seed is None:
            seed = config.get("text_to_image.seed", -1)

        if seed == -1:
            seed = torch.randint(0, 2**32 - 1, (1,)).item()

        generator = torch.Generator(device=self.device).manual_seed(seed)

        negative_prompt = negative_prompt or "blurry, low quality, distorted, ugly, bad anatomy"

        logger.info(f"Generating image: {width}x{height}, steps={num_inference_steps}, seed={seed}")

        clear_memory()

        with torch.inference_mode():
            # تمرير أساسي
            image = self.pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt,
                width=width,
                height=height,
                guidance_scale=guidance_scale,
                num_inference_steps=num_inference_steps,
                generator=generator,
                output_type="latent" if use_refiner else "pil",
            ).images[0]

            # محسن (Refiner)
            if use_refiner and self.refiner:
                image = self.refiner(
                    prompt=prompt,
                    negative_prompt=negative_prompt,
                    image=image,
                    guidance_scale=guidance_scale,
                    num_inference_steps=num_inference_steps // 2,
                    generator=generator,
                ).images[0]

        return image


def create_video_generator(**kwargs) -> VideoGenerator:
    """دالة مساعدة لإنشاء مولد فيديو"""
    return VideoGenerator(**kwargs)


def create_text_to_image_generator(**kwargs) -> TextToImageGenerator:
    """دالة مساعدة لإنشاء مولد نص لصورة"""
    return TextToImageGenerator(**kwargs)