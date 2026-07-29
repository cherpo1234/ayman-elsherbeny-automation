#!/bin/bash
# تشغيل سريع لأوتوميشن أيمن الشربيني على Linux/macOS

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$PROJECT_DIR/venv"

echo "============================================================"
echo "  أيمن الشربيني - Text/Image to Video Automation"
echo "  التشغيل السريع (Linux/macOS)"
echo "============================================================"
echo

# التحقق من Python
if ! command -v python3 &> /dev/null; then
    echo "[خطأ] Python 3 غير مثبت"
    echo "Ubuntu/Debian: sudo apt install python3 python3-venv"
    echo "macOS: brew install python"
    exit 1
fi

echo "[1/4] التحقق من Python..."
python3 --version

# التحقق من FFmpeg
if ! command -v ffmpeg &> /dev/null; then
    echo "[تحذير] FFmpeg غير مثبت - مطلوب لدمج الفيديو والصوت"
    echo "Ubuntu/Debian: sudo apt install ffmpeg"
    echo "macOS: brew install ffmpeg"
    echo
    read -p "المتابعة على أي حال؟ (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# إنشاء بيئة افتراضية
if [ ! -d "$VENV_DIR" ]; then
    echo "[2/4] إنشاء بيئة افتراضية..."
    python3 -m venv "$VENV_DIR"
else
    echo "[2/4] البيئة الافتراضية موجودة"
fi

# تفعيل البيئة وتثبيت المتطلبات
echo "[3/4] تثبيت المتطلبات..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip >/dev/null 2>&1
pip install -r "$PROJECT_DIR/requirements.txt"

# تثبيت الحزمة
echo "[4/4] تثبيت الحزمة..."
pip install -e "$PROJECT_DIR"

echo
echo "============================================================"
echo "  [نجاح] التثبيت مكتمل!"
echo "============================================================"
echo
echo "للاستخدام:"
echo "  source venv/bin/activate"
echo "  ayman-elsherbeny --help"
echo
echo "أمثلة:"
echo '  ayman-elsherbeny txt2vid "منظر طبيعي جميل" --voice ar-SA-HamedNeural'
echo "  ayman-elsherbeny img2vid photo.jpg --audio-text \"وصف الصورة\""
echo "  ayman-elsherbeny voices --engine edge-tts --language ar"
echo "  ayman-elsherbeny info"
echo