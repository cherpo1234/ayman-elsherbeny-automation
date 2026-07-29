@echo off
REM تشغيل سريع لأوتوميشن أيمن الشربيني على Windows
chcp 65001 >nul
title أيمن الشربيني - Text/Image to Video Automation

echo ============================================================
echo   أيمن الشربيني - Text/Image to Video Automation
echo   التشغيل السريع (Windows)
echo ============================================================
echo.

REM التحقق من Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [خطأ] Python غير مثبت أو غير مضاف لـ PATH
    echo يرجى تثبيت Python 3.10+ من https://python.org
    pause
    exit /b 1
)

echo [1/4] التحقق من Python...
python --version

REM إنشاء بيئة افتراضية
if not exist venv (
    echo [2/4] إنشاء بيئة افتراضية...
    python -m venv venv
    if errorlevel 1 (
        echo فشل في إنشاء البيئة الافتراضية
        pause
        exit /b 1
    )
) else (
    echo [2/4] البيئة الافتراضية موجودة
)

REM ترقية pip وتثبيت المتطلبات
echo [3/4] تثبيت المتطلبات...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip >nul 2>&1
pip install -r requirements.txt
if errorlevel 1 (
    echo فشل في تثبيت المتطلبات
    pause
    exit /b 1
)

REM تثبيت الحزمة
echo [4/4] تثبيت الحزمة...
pip install -e .
if errorlevel 1 (
    echo فشل في تثبيت الحزمة
    pause
    exit /b 1
)

echo.
echo ============================================================
echo   [نجاح] التثبيت مكتمل!
echo ============================================================
echo.
echo للتشغيل:
echo   venv\Scripts\ayman-elsherbeny.exe --help
echo.
echo أمثلة:
echo   venv\Scripts\ayman-elsherbeny.exe txt2vid "منظر طبيعي جميل" --voice ar-SA-HamedNeural
echo   venv\Scripts\ayman-elsherbeny.exe img2vid photo.jpg --audio-text "وصف الصورة"
echo   venv\Scripts\ayman-elsherbeny.exe voices --engine edge-tts --language ar
echo   venv\Scripts\ayman-elsherbeny.exe info
echo.
pause