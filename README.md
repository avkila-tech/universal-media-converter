<<<<<<< HEAD
# universal-media-converter
Universal Media Converter. Converts all video, image and audio types. Written in Python
=======
# Universal Media Converter
**Developer:** Avkila
**Status:** Tested / Working
**Version:** 1.1 — June 2026

---

### 🎬 Supported Formats

* **Video (12):** MP4, MKV, AVI, MOV, FLV, WEBM, WMV, 3GP, MPEG, TS, OGV, M4V
* **Audio (11):** MP3, M4A, FLAC, WAV, WMA, AAC, OGG, OPUS, AMR, AIFF, M4R
* **Image (8):** PNG, JPG, JPEG, WEBP, BMP, TIFF, GIF, ICO
* **Audio extraction:** Pull audio out of any video file directly — no intermediate steps

---

### ✨ Features

* **Real-time progress** with live time-remaining estimate (`Xm Xs left`)
* **Instant cancel** — kills FFmpeg immediately via `taskkill /F /T`
* **Smart format dropdown** — auto-populates based on the detected source type
* **Thread allocation slider** — controls encoder, filtergraph, and thread scheduling simultaneously
* **Windows Explorer integration** — adds a *"Universal Convert..."* right-click option to every file
* **Theme engine** — Pitch Black / Pure White presets + per-element hex color picker
* **Single-file app** — one `.py`, no config files, no install wizard
* Output is saved alongside the source file as `filename_converted.ext`

---

### ⚡ Performance & Thread Tuning

The thread slider controls three FFmpeg output-side flags at once:

| Flag | What it does |
|---|---|
| `-threads N` | Caps the encoder thread pool |
| `-filter_threads N` | Caps the filtergraph (scaling, resampling, etc.) |
| `-thread_type slice+frame` | Forces FFmpeg to actually respect the cap |

* Default on launch is `max(4, cpu_count // 2)` — half your cores, minimum 4
* Lowering the thread count reduces power draw and heat at the cost of speed
* Raising it above 6–8 threads gives diminishing returns on most hardware

> [!NOTE]
> The thread flags must be placed **after** the `-i` input flag in the FFmpeg command to affect the encoder. Placing them before `-i` only targets the demuxer, which does almost no CPU work. This is a common FFmpeg mistake — it's handled correctly here.

---

### 🖥️ Shell Integration

Open the **⚙ Settings** tab and click **Enable Right-Click Integration**. This writes a registry entry to `HKEY_CLASSES_ROOT\*\shell\UniversalConverter`, so every file in Explorer gets a *"Universal Convert..."* context menu option.

Click **Disable Right-Click Menu** in the same tab to remove it cleanly.

> [!CAUTION]
> **Administrator privileges required.** Right-click the `.exe` or your terminal and choose *Run as administrator* before using the registry integration. Without elevation, the write will fail with a permission error.

---

### 🔧 Requirements

* Windows 10 or 11
* Python 3.9+
* [FFmpeg](https://ffmpeg.org/download.html) — must be on your system `PATH`

```bash
pip install customtkinter
```

---

### 🚀 Usage

**Download the compiled release** (no Python required):
Download the latest `.zip` from the [Releases](../../releases) tab, extract it, and run `universal_converter.exe`.

**Run from source:**
```bash
python universal_converter.py
```

**Pre-load a file on launch** (what the right-click menu uses):
```bash
python universal_converter.py "C:\path\to\your\file.mp4"
```

**Compile to a standalone `.exe` yourself:**
```bash
pyinstaller --onefile --windowed --icon=icon.ico universal_converter.py
```

---

### 🤝 Credits

* **Developed by:** Avkila
* **GitHub:** [avkila-tech](https://github.com/avkila-tech)
* **Discord:** `avkila`
>>>>>>> bfe6da8 (Release)
