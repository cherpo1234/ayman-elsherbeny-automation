<div align="center">
  <h1>🎬 أوتوميشن <span style="color:#00aaff">أيمن الشربيني</span></h1>
  <h3>Text/Image to Video with Audio Automation</h3>
  <p><em>أوتوميشن احترافي لتحويل النصوص والصور إلى فيديوهات مع صوت باستخدام الذكاء الاصطناعي</em></p>
  <br>
  <p>
    <a href="#features">✨ المميزات</a> •
    <a href="#installation">📥 التثبيت</a> •
    <a href="#usage">🚀 الاستخدام</a> •
    <a href="#cli-options">⚙️ الخيارات</a> •
    <a href="#supported-models">🧠 النماذج</a> •
    <a href="#troubleshooting">🛠️ استكشاف</a>
  </p>
  <br>
</div>

---

## 📌 نظرة عامة

نظام **أيمن الشربيني** هو أوتوميشن متكامل ومفتوح المصدر لتحويل النصوص والصور إلى فيديوهات مع صوت. يستخدم أحدث تقنيات الذكاء الاصطناعي مثل **Stable Video Diffusion (SVD)** و **Microsoft Edge TTS** لتوليد محتوى مرئي وصوتي احترافي دون الحاجة إلى مفاتيح API مدفوعة.

### ✨ المميزات الرئيسية

| الميزة | الوصف | التقنية |
|--------|-------|---------|
| 🎥 **Text-to-Video** | تحويل النص الوصفي إلى فيديو كامل | SDXL + SVD |
| 🖼️ **Image-to-Video** | تحويل الصور الثابتة إلى فيديوهات متحركة | SVD |
| 🔊 **Text-to-Speech** | توليد أصوات عربية وإنجليزية طبيعية | Edge TTS |
| 🎞️ **دمج تلقائي** | دمج الفيديو والصوت بسلاسة | FFmpeg |
| 📦 **معالجة دفعية** | معالجة قوائم متعددة مرة واحدة | JSON config |
| ⚙️ **تكوين مرن** | 50+ معلمة قابلة للتعديل | YAML |

---

<h2 id="installation">📥 التثبيت</h2>

### المتطلبات الأساسية

- **Python** ≥ 3.10
- **GPU مع CUDA** ≥ 8GB VRAM (موصى به بشدة)
- **FFmpeg** في PATH

### 🪟 Windows

```bash
# 1. تثبيت FFmpeg
winget install ffmpeg

# 2. تشغيل سكريبت التثبيت
cd ayman_elsherbeny_automation
run_windows.bat
```

### 🐧 Linux / 🍎 macOS

```bash
# 1. تثبيت FFmpeg
sudo apt install ffmpeg        # Ubuntu/Debian
brew install ffmpeg            # macOS

# 2. تشغيل سكريبت التثبيت
cd ayman_elsherbeny_automation
chmod +x run_linux.sh
./run_linux.sh
```

### 📦 تثبيت يدوي

```bash
python -m venv venv
source venv/bin/activate          # Linux/Mac
venv\Scripts\activate             # Windows

pip install -e .
```

---

<h2 id="usage">🚀 الاستخدام</h2>

### 🎬 نص إلى فيديو

```bash
ayman-elsherbeny txt2vid "منظر طبيعي مع جبال وأنهار وغروب شمس" \
  --voice ar-SA-HamedNeural       \
  --frames 25                      \
  --fps 7                          \
  --output sunset_video
```

### 🖼️ صورة إلى فيديو

```bash
ayman-elsherbeny img2vid input.jpg \
  --audio-text "وصف الصورة"        \
  --voice ar-EG-SalmaNeural        \
  --frames 25                       \
  --fps 7                           \
  --output from_image
```

### 🔊 توليد صوت فقط

```bash
ayman-elsherbeny audio "مرحباً بكم في أوتوميشن أيمن الشربيني" \
  --engine edge-tts                \
  --voice ar-SA-ZariyahNeural      \
  --output welcome.mp3
```

### 🗣️ عرض الأصوات المتاحة

```bash
ayman-elsherbeny voices --engine edge-tts --language ar
ayman-elsherbeny voices --engine edge-tts --language en
```

### ℹ️ معلومات النظام

```bash
ayman-elsherbeny info
```

### 📋 معالجة دفعية (Batch)

```bash
ayman-elsherbeny batch batch_input.json --mode text_to_video
```

<h2 id="cli-options">⚙️ خيارات سطر الأوامر</h2>

### الأوامر المتاحة

| الأمر | الوصف |
|-------|-------|
| `txt2vid` | نص إلى فيديو مع صوت |
| `img2vid` | صورة إلى فيديو مع صوت |
| `audio` | توليد صوت فقط |
| `batch` | معالجة دفعية من JSON |
| `voices` | عرض الأصوات المتاحة |
| `info` | معلومات النظام |

### خيارات txt2vid / img2vid

| الخيار | الوصف | الافتراضي |
|--------|-------|-----------|
| `--voice` | صوت TTS | `ar-SA-HamedNeural` |
| `--language` | لغة الصوت | `ar` |
| `--frames` | عدد الإطارات | `25` |
| `--fps` | معدل الإطارات | `7` |
| `--motion-bucket` | شدة الحركة (1-255) | `127` |
| `--noise-aug` | قوة الضوضاء | `0.02` |
| `--seed` | بذرة عشوائية | عشوائي |
| `--width` | العرض | `1024` |
| `--height` | الارتفاع | `576` |
| `--output` | اسم المخرج | تلقائي |

---

<h2 id="supported-models">🧠 النماذج المدعومة</h2>

### 🎥 نماذج الفيديو

| النموذج | المهمة | الوصف |
|---------|-------|-------|
| `stabilityai/stable-video-diffusion-img2vid-xt` | Image-to-Video | 25 إطار، دقة عالية |
| `stabilityai/stable-video-diffusion-img2vid` | Image-to-Video | 14 إطار، خفيف |
| `stabilityai/stable-diffusion-xl-base-1.0` | Text-to-Image | SDXL 1.0 الأساسي |
| `stabilityai/stable-diffusion-xl-refiner-1.0` | Text-to-Image | محسّن SDXL (اختياري) |

### 🔊 نماذج الصوت

| المحرك | التفعيل | الميزات |
|-------|---------|---------|
| `edge-tts` | افتراضي | أصوات عصبية عربية، مجاني |
| `coqui-tts` | `pip install TTS` | متعدد اللغات |
| `gtts` | `pip install gtts` | خدمة Google TTS |
| `pyttsx3` | `pip install pyttsx3` | بدون إنترنت |

---

<h2 id="voices">🎙️ الأصوات العربية (Edge TTS)</h2>

### ذكور

| الصوت | الدولة | الجودة |
|-------|--------|--------|
| `ar-SA-HamedNeural` | 🇸🇦 السعودية | ⭐ ممتاز |
| `ar-EG-ShakirNeural` | 🇪🇬 مصر | جيد |
| `ar-AE-HamdanNeural` | 🇦🇪 الإمارات | جيد |
| `ar-IQ-BasselNeural` | 🇮🇶 العراق | جيد |
| `ar-JO-TaimNeural` | 🇯🇴 الأردن | جيد |
| `ar-MA-JamalNeural` | 🇲🇦 المغرب | جيد |

### إناث

| الصوت | الدولة | الجودة |
|-------|--------|--------|
| `ar-SA-ZariyahNeural` | 🇸🇦 السعودية | ⭐ ممتاز |
| `ar-EG-SalmaNeural` | 🇪🇬 مصر | ⭐ ممتاز |
| `ar-AE-FatimaNeural` | 🇦🇪 الإمارات | جيد |
| `ar-DZ-AminaNeural` | 🇩🇿 الجزائر | جيد |
| `ar-IQ-RanaNeural` | 🇮🇶 العراق | جيد |
| `ar-MA-MalikaNeural` | 🇲🇦 المغرب | جيد |

---

<h2 id="config">📝 التكوين (config.yaml)</h2>

```yaml
video:
  model: "stabilityai/stable-video-diffusion-img2vid-xt"
  fps: 7
  num_frames: 25
  width: 1024
  height: 576
  motion_bucket_id: 127
  noise_aug_strength: 0.02
  decode_chunk_size: 2

audio:
  tts_engine: "edge-tts"
  language: "ar"
  voice: "ar-SA-HamedNeural"

merge:
  video_codec: "libx264"
  crf: 23
  audio_codec: "aac"
  audio_bitrate: "128k"

hardware:
  device: "auto"
  dtype: "float16"
  enable_xformers: true
  enable_vae_slicing: true
  enable_vae_tiling: true
```

---

<h2 id="library">🛠️ الاستخدام كمكتبة Python</h2>

```python
from ayman_elsherbeny_automation.core.automation import create_automation

with create_automation() as automation:
    # نص إلى فيديو
    result = automation.text_to_video(
        prompt="منظر طبيعي مع جبال وبحيرة",
        audio_text="بحيرة هادئة بين الجبال",
        voice="ar-SA-HamedNeural",
        num_frames=25,
        fps=7,
        output_name="my_video",
    )
    print(f"✅ الفيديو: {result['merged']}")
    print(f"🎵 الصوت: {result['audio']}")
    print(f"🎬 الفيديو النهائي: {result['merged']}")
```

---

<h2 id="troubleshooting">🛠️ استكشاف الأخطاء وحلها</h2>

### 🚀 تحسين الأداء

لتقليل استهلاك الذاكرة على GPU محدودة:

```yaml
hardware:
  enable_vae_slicing: true
  enable_vae_tiling: true
  cpu_offload: true
  dtype: "float16"
```

### ⚡ سرعة بطيئة على CPU

```yaml
hardware:
  device: "cpu"
  dtype: "float32"
video:
  num_frames: 14
  width: 512
  height: 288
```

### ❌ CUDA Out of Memory

- قلل `num_frames` إلى 14
- قلل الأبعاد (`width`/`height`) إلى 512×288
- فعّل `enable_vae_slicing` و `cpu_offload`

### 📁 FFmpeg غير موجود

```bash
# Windows
winget install ffmpeg

# Linux
sudo apt install ffmpeg

# macOS
brew install ffmpeg
```

---

<h2 id="structure">📂 هيكل المشروع</h2>

```
ayman_elsherbeny_automation/
├── ayman_elsherbeny_automation/
│   ├── cli.py                        # CLI (Click + Rich)
│   ├── config.py                     # إدارة التكوين
│   ├── core/
│   │   └── automation.py             # الفئة الأساسية
│   ├── generation/
│   │   ├── video_generator.py        # SVD (Image-to-Video)
│   │   ├── text_to_image.py          # SDXL (Text-to-Image)
│   │   ├── audio_generator.py        # TTS
│   │   └── video_merger.py           # FFmpeg
│   └── utils/
│       ├── device.py                 # GPU/CPU optimization
│       └── logging.py                # التسجيل
├── config/
│   └── config.yaml                   # ملف التكوين
├── examples/
│   └── batch_example.json            # مثال دفعي
├── pyproject.toml
├── requirements.txt
├── run_windows.bat
├── run_linux.sh
└── README.md
```

---

## 🎓 التوسعات المستقبلية

- **Hook API**: معالجة ما بعد التوليد
- **Webhook Callbacks**: إشعارات عند اكتمال المهام
- **واجهة REST API**: تشغيل الأوتوميشن عبر HTTP
- **Docker Images**: حاويات جاهزة للنشر السحابي
- **SMTP/WhatsApp Integration**: إرسال الفيديو مباشرة

---

## 📄 الترخيص

**MIT License** — راجع ملف `LICENSE` للتفاصيل.

---

## 🤝 المساهمة

المساهمات مرحب بها! يرجى فتح **Issue** أو **Pull Request** على GitHub.

---

<div align="center">
  <p>تم تطويره بواسطة <strong>أيمن الشربيني</strong> 🇪🇬</p>
  <p>🛡️ برمجيات مفتوحة المصدر — <strong>مجاني للاستخدام التجاري والشخصي</strong></p>
</div>