"""
وحدة توليد الصور من النص (Text-to-Image) باستخدام Stable Diffusion XL
"""
import uuid
from pathlib import Path
from typing import Optional, List, Union
from PIL import Image
import torch
from diffusers import StableDiffusionXLPipeline
from ayman_elsherbeny_automation.config import config, OUTPUT_DIR, MODELS_DIR
from ayman_elsherbeny_automation.utils.device import get_device, get_dtype, clear_memory, optimize_memory
from ayman_elsherbeny_automation.utils.logging import logger


class TextToImageGenerator:
    """فئة توليد الصور من النص"""

    def __init__(
        self,
        model_id: Optional[str] = None,
        refiner_id: Optional[str] = None,
        device: Optional[torch.device] = None,
        dtype: Optional[torch.dtype] = None,
        use_refiner: bool = False,
    ):
        self.model_id = model_id or config.get("text_to_image.model_path", "stabilityai/stable-diffusion-xl-base-1.0")
        self.refiner_id = refiner_id or config.get("text_to_image.refiner_path", "stabilityai/stable-diffusion-xl-refiner-1.0")
        self.device = device or get_device()
        self.dtype = dtype or get_dtype()
        self.use_refiner = use_refiner
        self.base_pipeline: Optional[StableDiffusionXLPipeline] = None
        self.refiner_pipeline = None
        self._load_pipelines()

    def _load_pipelines(self) -> None:
        """تحميل خطوط أنابيب SDXL الأساسية والمحسنة"""
        logger.info(f"Loading SDXL base model: {self.model_id}")

        self.base_pipeline = StableDiffusionXLPipeline.from_pretrained(
            self.model_id,
            torch_dtype=self.dtype,
            variant="fp16" if self.dtype == torch.float16 else None,
            use_safetensors=True,
            cache_dir=str(MODELS_DIR),
        )

        self.base_pipeline.to(self.device)
        self.base_pipeline.enable_vae_slicing()
        self.base_pipeline.enable_vae_tiling()
        optimize_memory(self.device)

        if self.use_refiner:
            logger.info(f"Loading SDXL refiner: {self.refiner_id}")
            from diffusers import DiffusionPipeline
            self.refiner_pipeline = DiffusionPipeline.from_pretrained(
                self.refiner_id,
                torch_dtype=self.dtype,
                variant="fp16" if self.dtype == torch.float16 else None,
                use_safetensors=True,
                cache_dir=str(MODELS_DIR),
            )
            self.refiner_pipeline.to(self.device)

        logger.info("Text-to-Image pipelines loaded successfully")

    def generate(
        self,
        prompt: str,
        negative_prompt: Optional[str] = None,
        output_path: Optional[Union[str, Path]] = None,
        width: Optional[int] = None,
        height: Optional[int] = None,
        num_inference_steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        seed: Optional[int] = None,
        num_images: int = 1,
    ) -> List[Path]:
        """
        توليد صورة من نص

        Args:
            prompt: النص الوصفي للصورة
            negative_prompt: نص سلبي لتجنب عناصر معينة
            output_path: مسار الحفظ
            width/height: أبعاد الصورة
            num_inference_steps: خطوات الاستنتاج
            guidance_scale: مقياس التوجيه
            seed: بذرة العشوائية
            num_images: عدد الصور المطلوبة

        Returns:
            قائمة بمسارات الصور المولدة
        """
        if self.base_pipeline is None:
            raise RuntimeError("Pipeline not loaded")

        default_negative = (
            "blurry, low quality, distorted, deformed, ugly, bad anatomy, "
            "extra limbs, missing limbs, watermark, text, signature, logo"
        )

        if output_path is None:
            output_path = OUTPUT_DIR
        else:
            output_path = Path(output_path)

        output_path.parent.mkdir(parents=True, exist_ok=True)

        generator = torch.Generator(device=self.device)
        if seed is not None:
            generator.manual_seed(seed)
        else:
            generator.seed()

        logger.info(f"Generating image from prompt: {prompt[:100]}...")

        width = width or config.get("text_to_image.width", 1024)
        height = height or config.get("text_to_image.height", 576)
        steps = num_inference_steps or config.get("text_to_image.steps", 30)
        guidance = guidance_scale or config.get("text_to_image.guidance_scale", 7.5)

        images = self.base_pipeline(
            prompt=prompt,
            negative_prompt=negative_prompt or default_negative,
            width=width,
            height=height,
            num_inference_steps=steps,
            guidance_scale=guidance,
            num_images_per_prompt=num_images,
            generator=generator,
            output_type="latent" if self.use_refiner else "pil",
        ).images

        if self.use_refiner and self.refiner_pipeline is not None:
            logger.info("Refining images with SDXL Refiner...")
            images = self.refiner_pipeline(
                prompt=prompt,
                negative_prompt=negative_prompt or default_negative,
                image=images,
                num_inference_steps=steps // 2,
                guidance_scale=guidance,
                generator=generator,
            ).images

        saved_paths = []
        for i, img in enumerate(images):
            if num_images > 1:
                save_path = output_path.parent / f"{output_path.stem}_{i}{output_path.suffix}"
            else:
                save_path = output_path

            if save_path.suffix == "":
                save_path = save_path.with_suffix(".png")

            img.save(save_path)
            saved_paths.append(save_path)
            logger.info(f"Image saved: {save_path}")

        clear_memory(self.device)
        return saved_paths

    def unload(self) -> None:
        """إلغاء تحميل النماذج"""
        if self.base_pipeline is not None:
            del self.base_pipeline
            self.base_pipeline = None
        if self.refiner_pipeline is not None:
            del self.refiner_pipeline
            self.refiner_pipeline = None
        clear_memory(self.device)
        logger.info("Text-to-Image pipelines unloaded")


def create_text_to_image_generator(**kwargs) -> TextToImageGenerator:
    """دالة مساعدة لإنشاء مولد نص إلى صورة"""
    return TextToImageGenerator(**kwargs)