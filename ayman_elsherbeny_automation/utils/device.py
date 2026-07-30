"""
أدوات إدارة الجهاز (GPU/CPU) وتحميل النماذج
"""
import torch
from typing import Optional, Literal
from ..config import config


def get_device(device: Optional[str] = None) -> torch.device:
    """
    تحديد الجهاز المناسب (CUDA/MPS/CPU)

    Args:
        device: "auto", "cuda", "mps", "cpu" أو رقم GPU محدد مثل "cuda:0"

    Returns:
        torch.device
    """
    if device is None:
        device = config.get("hardware.device", "auto")

    if device == "auto":
        if torch.cuda.is_available():
            return torch.device("cuda")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        return torch.device("cpu")

    if device.startswith("cuda"):
        if not torch.cuda.is_available():
            print("CUDA not available, falling back to CPU")
            return torch.device("cpu")
        return torch.device(device)

    if device == "mps":
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return torch.device("mps")
        print("MPS not available, falling back to CPU")
        return torch.device("cpu")

    return torch.device("cpu")


def get_dtype(dtype: Optional[str] = None) -> torch.dtype:
    """
    تحديد نوع البيانات (float16/float32/bfloat16)

    Args:
        dtype: "float16", "float32", "bfloat16" أو "auto"

    Returns:
        torch.dtype
    """
    if dtype is None:
        dtype = config.get("video.dtype", "float16")

    if dtype == "auto":
        device = get_device()
        if device.type == "cuda":
            # التحقق من دعم bfloat16
            if torch.cuda.is_bf16_supported():
                return torch.bfloat16
            return torch.float16
        elif device.type == "mps":
            return torch.float16
        return torch.float32

    dtype_map = {
        "float16": torch.float16,
        "fp16": torch.float16,
        "half": torch.float16,
        "float32": torch.float32,
        "fp32": torch.float32,
        "bfloat16": torch.bfloat16,
        "bf16": torch.bfloat16,
    }

    return dtype_map.get(dtype.lower(), torch.float16)


def optimize_model(model: torch.nn.Module, device: Optional[torch.device] = None) -> torch.nn.Module:
    """
    تحسين النموذج للاستدلال

    Args:
        model: نموذج PyTorch
        device: الجهاز المستهدف

    Returns:
        النموذج المحسن
    """
    if device is None:
        device = get_device()

    model = model.to(device)

    # تمكين xformers إذا كان متاحاً
    if config.get("hardware.enable_xformers", True):
        try:
            model.enable_xformers_memory_efficient_attention()
            print("xformers memory efficient attention enabled")
        except Exception as e:
            print(f"xformers not available: {e}")

    # VAE slicing لتقليل الذاكرة
    if config.get("hardware.enable_vae_slicing", True):
        try:
            model.enable_vae_slicing()
            print("VAE slicing enabled")
        except Exception:
            pass

    # VAE tiling
    if config.get("hardware.enable_vae_tiling", True):
        try:
            model.enable_vae_tiling()
            print("VAE tiling enabled")
        except Exception:
            pass

    # CPU offload
    if config.get("hardware.cpu_offload", False):
        try:
            model.enable_model_cpu_offload()
            print("Model CPU offload enabled")
        except Exception:
            pass

    # Sequential CPU offload
    if config.get("hardware.sequential_cpu_offload", False):
        try:
            model.enable_sequential_cpu_offload()
            print("Sequential CPU offload enabled")
        except Exception:
            pass

    # تعيين وضع التقييم
    model.eval()

    # تجميع النموذج (PyTorch 2.0+)
    if hasattr(torch, "compile") and config.get("hardware.compile", False):
        try:
            model = torch.compile(model, mode="reduce-overhead")
            print("Model compiled with torch.compile")
        except Exception as e:
            print(f"torch.compile failed: {e}")

    return model


def clear_memory(device: Optional[torch.device] = None) -> None:
    """تنظيف ذاكرة GPU"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        torch.cuda.ipc_collect()
    import gc
    gc.collect()


def optimize_memory(device: Optional[torch.device] = None) -> None:
    """تحسين/تنظيف الذاكرة (مرادف clear_memory)"""
    clear_memory(device)


def get_gpu_memory_info() -> dict:
    """الحصول على معلومات ذاكرة GPU"""
    if not torch.cuda.is_available():
        return {"available": False}

    return {
        "available": True,
        "device_count": torch.cuda.device_count(),
        "current_device": torch.cuda.current_device(),
        "device_name": torch.cuda.get_device_name(),
        "memory_allocated": torch.cuda.memory_allocated() / 1024**3,  # GB
        "memory_reserved": torch.cuda.memory_reserved() / 1024**3,
        "max_memory_allocated": torch.cuda.max_memory_allocated() / 1024**3,
        "max_memory_reserved": torch.cuda.max_memory_reserved() / 1024**3,
    }


def set_memory_fraction(fraction: float = 0.9) -> None:
    """تعيين نسبة ذاكرة GPU المسموح بها"""
    if torch.cuda.is_available():
        torch.cuda.set_per_process_memory_fraction(fraction)


def print_memory_summary() -> None:
    """طباعة ملخص الذاكرة"""
    info = get_gpu_memory_info()
    if info["available"]:
        print(f"GPU: {info['device_name']}")
        print(f"Allocated: {info['memory_allocated']:.2f} GB")
        print(f"Reserved: {info['memory_reserved']:.2f} GB")
    else:
        print("No GPU available")