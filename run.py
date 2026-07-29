#!/usr/bin/env python3
"""
تشغيل سريع لأوتوميشن أيمن الشربيني بدون تثبيت
"""
import sys
import subprocess
from pathlib import Path

PROJECT_DIR = Path(__file__).parent
VENV_DIR = PROJECT_DIR / "venv"

def run_cmd(cmd, cwd=None):
    """تشغيل أمر وطباعة المخرجات"""
    print(f"$ {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd or PROJECT_DIR)
    return result.returncode == 0

def main():
    print("=" * 60)
    print("  أيمن الشربيني - Text/Image to Video Automation")
    print("  التشغيل السريع")
    print("=" * 60)

    # 1. التحقق من Python
    python_exe = sys.executable
    print(f"\nPython: {python_exe}")

    # 2. إنشاء بيئة افتراضية
    if not VENV_DIR.exists():
        print("\n[1/4] إنشاء بيئة افتراضية...")
        if not run_cmd([python_exe, "-m", "venv", "venv"]):
            print("فشل في إنشاء البيئة الافتراضية")
            return 1
    else:
        print("\n[1/4] البيئة الافتراضية موجودة")

    # 3. تحديد pip
    if sys.platform == "win32":
        pip_exe = VENV_DIR / "Scripts" / "pip.exe"
        python_venv = VENV_DIR / "Scripts" / "python.exe"
    else:
        pip_exe = VENV_DIR / "bin" / "pip"
        python_venv = VENV_DIR / "bin" / "python"

    # 4. ترقية pip
    print("\n[2/4] ترقية pip...")
    run_cmd([str(pip_exe), "install", "--upgrade", "pip"])

    # 5. تثبيت المتطلبات
    print("\n[3/4] تثبيت المتطلبات...")
    req_file = PROJECT_DIR / "requirements.txt"
    if not run_cmd([str(pip_exe), "install", "-r", str(req_file)]):
        print("فشل في تثبيت المتطلبات")
        return 1

    # 6. تثبيت الحزمة في وضع التطوير
    print("\n[4/4] تثبيت الحزمة...")
    if not run_cmd([str(pip_exe), "install", "-e", "."]):
        print("فشل في تثبيت الحزمة")
        return 1

    print("\n" + "=" * 60)
    print("  ✅ التثبيت مكتمل!")
    print("=" * 60)
    print(f"\nلتشغيل الأوامر:")
    print(f"  {python_venv} -m ayman_elsherbeny_automation.cli --help")
    print(f"\nأو استخدم السكريبت:")
    print(f"  {VENV_DIR / 'Scripts' / 'ayman-elsherbeny.exe' if sys.platform == 'win32' else VENV_DIR / 'bin' / 'ayman-elsherbeny'} --help")

    # عرض أمثلة
    print("\nأمثلة:")
    print(f'  ayman-elsherbeny txt2vid "منظر طبيعي جميل" --voice ar-SA-HamedNeural')
    print(f'  ayman-elsherbeny img2vid photo.jpg --audio-text "وصف الصورة"')
    print(f'  ayman-elsherbeny voices --engine edge-tts --language ar')

    return 0

if __name__ == "__main__":
    sys.exit(main())