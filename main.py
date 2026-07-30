#!/usr/bin/env python3
"""
أيمن الشربيني - مدخل المستخدم البسيط
طريقة مجانية 100% لتحويل نص/صور إلى فيديو ريلز عمودي
"""
import sys
import os
from pathlib import Path

# إضافة مسار المشروع
sys.path.insert(0, str(Path(__file__).parent))

from ayman_elsherbeny_automation.core.automation import create_automation
from ayman_elsherbeny_automation import config, OUTPUT_DIR


PRESETS = {
    # ريلز عمودي (TikTok, Reels, Shorts)
    "vertical_reels": {
        "width": 1080,
        "height": 1920,
        "fps": 24,
        "frames": 25,
        "motion_bucket": 130,
        "noise_aug": 0.03,
        "voice": "ar-SA-HamedNeural",
        "desc": "فيديو رأسي 9:16 للمنصات الاجتماعية",
    },
    # أفقي كلاسيك
    "horizontal": {
        "width": 1920,
        "height": 1080,
        "fps": 24,
        "frames": 25,
        "motion_bucket": 127,
        "noise_aug": 0.02,
        "voice": "ar-SA-HamedNeural",
        "desc": "فيديو أفقي 16:9 كلاسيكي",
    },
    # مربع
    "square": {
        "width": 1080,
        "height": 1080,
        "fps": 24,
        "frames": 25,
        "motion_bucket": 127,
        "noise_aug": 0.02,
        "voice": "ar-SA-HamedNeural",
        "desc": "فيديو مربع 1:1 مناسب Instagram",
    },
    # سينمائي عريض
    "cinematic": {
        "width": 1920,
        "height": 820,
        "fps": 24,
        "frames": 25,
        "motion_bucket": 120,
        "noise_aug": 0.015,
        "voice": "ar-SA-HamedNeural",
        "desc": "فيديو سينمائي عريض 21:9",
    },
}


def load_script(script_path):
    """قراءة ملف النص وإرجاع قائمة بالأسطر غير الفارغة"""
    with open(script_path, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    return lines


def load_images(images_path):
    """قراءة الصور من مجلد"""
    imgs = sorted(Path(images_path).glob("*"))
    imgs = [i for i in imgs if i.suffix.lower() in (".jpg", ".jpeg", ".png", ".webp", ".bmp")]
    if not imgs:
        print("❌ لا توجد صور في المجلد")
        sys.exit(1)
    return imgs


def show_presets():
    """عرض القوالب المتاحة"""
    print("\n🎯 القوالب المتاحة:")
    print("-" * 60)
    for name, p in PRESETS.items():
        print(f"  {name:<20} {p['desc']:<30} {p['width']}x{p['height']}")
    print()


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="أيمن الشربيني - أوتوميشن فيديو مجاني 100%",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
أمثلة:
  python main.py --script input/script.txt --images input/images --preset vertical_reels --out my_reel
  python main.py --script script.txt --images photos --preset horizontal --voice ar-EG-SalmaNeural
  python main.py --presets
  python main.py --simple "منظر طبيعي" --voice ar-SA-HamedNeural
        """,
    )

    # مدخل رئيسي
    parser.add_argument("--script", help="ملف النص (كل سطر = مشهد أو وصف)")
    parser.add_argument("--images", help="مجلد الصور")
    parser.add_argument("--preset", choices=list(PRESETS.keys()) + [""], default="vertical_reels",
                        help="قالب الفيديو (افتراضي: vertical_reels)")
    parser.add_argument("--format", default="mp4", help="صيغة الخرج")
    parser.add_argument("--out", default="output", help="اسم ملف الخرج")
    parser.add_argument("--voice", help="صوت TTS (افتراضي: ar-SA-HamedNeural)")
    parser.add_argument("--language", default="ar", help="لغة الصوت")
    parser.add_argument("--fps", type=int, help="معدل الإطارات")
    parser.add_argument("--frames", type=int, help="عدد الإطارات لكل فيديو")
    parser.add_argument("--presets", action="store_true", help="عرض القوالب المتاحة")
    parser.add_argument("--simple", help="طريقة بسيطة: نص مباشر لفيديو")
    parser.add_argument("--motion", type=int, help="شدة الحركة (1-255)")
    parser.add_argument("--noise", type=float, help="قوة الضوضاء")

    args = parser.parse_args()

    if args.presets:
        show_presets()
        return

    # ===== طريقة بسيطة: نص مباشر =====
    if args.simple:
        print(f"\n🎬 'أيمن الشربيني' - فيديو من نص بسيط")
        print("=" * 60)
        with create_automation() as automation:
            preset = PRESETS.get(args.preset, PRESETS["vertical_reels"])
            result = automation.text_to_video(
                prompt=args.simple,
                audio_text=args.simple,
                audio_voice=args.voice or preset["voice"],
                audio_language=args.language,
                num_frames=args.frames or preset["frames"],
                fps=args.fps or preset["fps"],
                motion_bucket_id=args.motion or preset["motion_bucket"],
                noise_aug_strength=args.noise or preset["noise_aug"],
                width=preset["width"],
                height=preset["height"],
                output_name=args.out,
            )
        print(f"\n✅ تم بنجاح!")
        print(f"   📁 {result['merged']}")
        return

    # ===== طريقة متقدمة: سكريبت + صور =====
    if not args.script:
        print("❌ يجب تحديد --script أو --simple")
        show_presets()
        parser.print_help()
        sys.exit(1)

    # تحميل القالب
    preset = PRESETS.get(args.preset, PRESETS["vertical_reels"])
    print(f"\n🎯 القالب: {args.preset} ({preset['desc']})")
    print(f"   الأبعاد: {preset['width']}x{preset['height']}")
    print(f"   fps: {args.fps or preset['fps']}")

    # تحميل النص
    lines = load_script(args.script)
    print(f"📝 عدد المشاهد: {len(lines)}")

    # تحميل الصور
    images = []
    if args.images:
        images = load_images(args.images)
        print(f"🖼️  عدد الصور: {len(images)}")

    # تجهيز المدخلات
    # كل سطر = فيديو مستقل، يتم دمجهم في النهاية
    inputs = []
    for i, line in enumerate(lines):
        inp = {
            "prompt": line,
            "audio_text": line,
            "voice": args.voice or preset["voice"],
            "language": args.language,
            "frames": args.frames or preset["frames"],
            "fps": args.fps or preset["fps"],
            "motion_bucket": args.motion or preset["motion_bucket"],
            "noise_aug": args.noise or preset["noise_aug"],
            "width": preset["width"],
            "height": preset["height"],
            "output_name": f"{args.out}_{i:03d}",
        }
        # إذا فيه صور، استخدم أول صورة متاحة
        if images:
            img_idx = min(i, len(images) - 1)
            inp["image_path"] = str(images[img_idx])
        inputs.append(inp)

    # تشغيل الأوتوميشن
    print(f"\n🚀 بدء المعالجة ({len(inputs)} مقطع)...")
    print("=" * 60)

    with create_automation() as automation:
        if args.images:
            results = automation.batch_process(inputs, mode="image_to_video")
        else:
            results = automation.batch_process(inputs, mode="text_to_video")

    print("\n" + "=" * 60)
    success = sum(1 for r in results if r is not None)
    print(f"✅ تم: {success}/{len(results)} مقطع")
    print(f"📂 المخرجات في مجلد: {OUTPUT_DIR}")
    print(f"   شغل: python main.py --presets لعرض القوالب")
    print("=" * 60)


if __name__ == "__main__":
    main()
