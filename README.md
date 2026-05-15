# 🎬 Offline AI Avatar Video Generator

A powerful, fully offline system for generating professional presenter videos from scripts, avatar images, and optional voice samples. No cloud services, no API costs, completely local processing with GPU acceleration.

## ✨ Features

### Core Capabilities
- **Text-to-Speech (TTS)**: Multiple engines for speech synthesis
  - **XTTS-v2**: High-quality multilingual TTS with voice cloning (Coqui)
  - **Piper**: Fast, lightweight TTS (ideal for speed-focused workflows)
  
- **Talking Head Animation**: Realistic avatar movements synchronized to speech
  - **SadTalker**: Advanced facial animation with natural expressions (requires higher VRAM)
  - **Wav2Lip**: Fast, accurate lip-sync animation (efficient on 4GB+ VRAM)

- **Lip Synchronization**: Precise mouth movement matching to audio

- **Automatic Subtitles**: AI-powered transcription and subtitle generation using Whisper

- **Screen Overlay**: Picture-in-Picture (PiP) support for screen recordings alongside avatar

- **Quality Modes**:
  - **Fast**: Wav2Lip + Piper (5-10 min for 5-10 min video on mid-range GPU)
  - **Balanced**: SadTalker + XTTS (10-20 min, better quality)
  - **Quality**: SadTalker + XTTS + refinement passes (highest quality, longest processing)

- **Resume Support**: Interrupted renders can be resumed from the last completed stage

- **Multi-format Output**: Supports 720p, 1080p, and 4K resolution

## 🏗️ Architecture

### Pipeline Stages

```
Input Files
    ↓
[Script Processing] → Extract text & timing
    ↓
[TTS Engine] → Generate speech audio
    ↓
[Audio Post-Processing] → Noise reduction, normalization
    ↓
[Subtitle Generation] → Transcribe & generate SRT
    ↓
[Talking Head Animation] → Generate avatar video with mouth/expression sync
    ↓
[Lip Sync Refinement] → Optional second-pass for precise lip movement
    ↓
[Screen Overlay Composition] → Optional PiP with screen recording
    ↓
[Final Video Composition] → Merge audio, video, subtitles, effects
    ↓
Output Video (.mp4) + Subtitles (.srt)
```

### Project Structure

```
avatar_system/
├── core/                          # Core pipeline & processing modules
│   ├── pipeline/
│   │   ├── orchestrator.py       # Main pipeline coordinator
│   │   ├── chunk_manager.py      # Handle long videos via chunking
│   │   ├── project_state.py      # Resume support (SQLite DB)
│   │   └── __init__.py
│   │
│   ├── stages/                    # Processing stages
│   │   ├── tts/
│   │   │   ├── xtts_engine.py    # XTTS-v2 synthesis
│   │   │   ├── piper_engine.py   # Piper TTS
│   │   │   └── audio_postprocess.py  # Normalization, noise reduction
│   │   ├── talking_head/
│   │   │   ├── sadtalker_runner.py   # SadTalker animation
│   │   │   └── wav2lip_runner.py     # Wav2Lip animation
│   │   ├── lip_sync/
│   │   │   └── wav2lip_runner.py     # Lip-sync refinement
│   │   ├── subtitles/
│   │   │   └── whisper_transcriber.py # Subtitle generation
│   │   ├── screen_overlay/
│   │   │   └── pip_compositor.py     # PiP composition
│   │   └── compositor/
│   │       └── ffmpeg_render.py      # Final video assembly
│   │
│   ├── utils/
│   │   ├── gpu.py                # GPU memory management
│   │   ├── image_utils.py        # Avatar image preprocessing
│   │   ├── logger.py             # Logging system
│   │   └── system_check.py       # Environment validation
│   └── __init__.py
│
├── scripts/                       # Setup & utility scripts
│   ├── install_windows.bat       # Windows installation (Python, deps, models)
│   ├── install_linux.sh          # Linux installation
│   └── download_models.py        # Model downloader
│
├── generate.py                    # Main entry point
├── requirements.txt               # Python dependencies
├── sample_script.txt             # Example input script
│
├── output/                        # Generated videos (auto-created)
├── temp/                          # Processing cache (auto-created)
├── models/                        # Model checkpoints (auto-downloaded)
├── repos/                         # External repos (Wav2Lip, etc.)
├── projects/                      # Project state databases
└── logs/                          # Pipeline logs

```

## 📋 Requirements

### System Requirements
- **OS**: Windows, Linux, or macOS
- **Python**: 3.10+
- **GPU**: NVIDIA GPU (CUDA 11.8+) recommended
  - **Minimum**: 4 GB VRAM (Wav2Lip + Piper)
  - **Recommended**: 8-12 GB VRAM (SadTalker + XTTS)
  - **Optional**: 24+ GB for 4K or very long videos
- **Storage**: ~10 GB for models + space for output videos
- **CPU**: 4+ cores (for audio processing & encoding)

### Software Dependencies
Core frameworks:
- **PyTorch** 2.1.0+ with CUDA support
- **TorchVision** & **TorchAudio**
- **FFmpeg** (binary, not Python package)
- **Git** (for cloning external repos)

Python packages (see `requirements.txt`):
- **TTS**: Coqui TTS, Piper TTS
- **Speech Recognition**: Faster Whisper
- **Face Detection**: MediaPipe, InsightFace, Face-Alignment
- **Audio**: librosa, soundfile, noisereduce
- **Video**: OpenCV, ffmpeg-python
- **Models**: HuggingFace Hub, SafeTensors

## 🚀 Installation

### Windows

1. **Download & Extract**
   ```bash
   # Clone or download this repository
   cd avatar_system
   ```

2. **Run Installer** (handles Python, Git, FFmpeg verification)
   ```bash
   scripts\install_windows.bat
   ```
   This will:
   - Verify Python 3.10+, Git, and FFmpeg installed
   - Create Python virtual environment (`venv`)
   - Install PyTorch with CUDA support
   - Install all Python dependencies
   - Download minimal model checkpoints (~560 MB)
   - Create necessary directories

3. **Verify Installation**
   ```bash
   venv\Scripts\activate
   python generate.py --help
   ```

### Linux / macOS

```bash
# Make install script executable
chmod +x scripts/install_linux.sh

# Run installer
./scripts/install_linux.sh

# Verify
source venv/bin/activate
python generate.py --help
```

### Manual FFmpeg Installation (if needed)

**Windows:**
1. Download from: https://www.gyan.dev/ffmpeg/builds/
2. Extract to: `C:\Program Files\ffmpeg-8.1.1-essentials_build`
3. Add `bin/` folder to system PATH
4. Restart terminal/VS Code

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install ffmpeg
```

**macOS (Homebrew):**
```bash
brew install ffmpeg
```

## 🎯 Usage

### Basic Usage

```bash
# Activate environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Generate video
python generate.py \
    --script script.txt \
    --avatar avatar.jpg \
    --output output.mp4
```

### Complete Example with Options

```bash
python generate.py \
    --script my_script.txt \
    --avatar presenter.jpg \
    --voice voice_sample.wav \           # Optional: for voice cloning
    --screen screen_recording.mp4 \      # Optional: for PiP overlay
    --output video.mp4 \
    --mode balanced \                    # fast | balanced | quality
    --resolution 1080p \                 # 720p | 1080p | 4k
    --fps 25 \
    --subtitles \                        # Enable subtitle generation
    --sub-style modern \                 # modern | corporate | minimal | karaoke
    --burn-subs \                        # Burn subtitles into video
    --pip-layout bottom_right \          # bottom_right | bottom_left | side_by_side | top_right
    --tts-engine xtts \                  # piper | xtts (auto-selected if not set)
    --device cuda \                      # auto | cuda | cpu
    --preview                            # Generate 30s preview only
```

### Command-Line Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--script` | Required | — | Path to script text file |
| `--avatar` | Required | — | Path to avatar image (JPG/PNG) |
| `--output` | Required | — | Output video path (.mp4) |
| `--voice` | Optional | None | Voice sample for cloning (3-10s WAV) |
| `--screen` | Optional | None | Screen recording for PiP overlay (.mp4) |
| `--mode` | Choice | balanced | Processing quality mode (fast/balanced/quality) |
| `--resolution` | Choice | 1080p | Output resolution (720p/1080p/4k) |
| `--fps` | Integer | 25 | Frames per second |
| `--subtitles` | Flag | True | Generate subtitle file |
| `--no-subtitles` | Flag | — | Disable subtitles |
| `--sub-style` | Choice | modern | Subtitle styling (modern/corporate/minimal/karaoke) |
| `--burn-subs` | Flag | True | Embed subtitles in video |
| `--pip-layout` | Choice | bottom_right | PiP positioning |
| `--tts-engine` | Choice | auto | TTS engine selection (piper/xtts) |
| `--device` | Choice | auto | GPU device (auto/cuda/cpu) |
| `--vram` | Float | auto | Override detected VRAM (GB) |
| `--resume` | Flag | False | Resume interrupted render |
| `--preview` | Flag | False | Generate 30-second preview |
| `--skip-models-check` | Flag | False | Skip model download verification |

## 📝 Input Formats

### Script File (.txt)

Plain text script. Each line becomes a separate audio segment/animation sequence.

**Example** (`script.txt`):
```
Hello and welcome to this tutorial.
Today we are going to walk through the key features of our product.
This AI-powered system allows you to create professional presenter videos entirely offline.
You simply provide a script, an avatar image, and optionally a voice sample.
The system handles everything else automatically.
```

### Avatar Image

- **Formats**: JPG, PNG
- **Resolution**: 512×512 to 1024×1024 recommended
- **Content**: Face should be clearly visible, well-lit, frontal or slight angle
- **Quality**: High-resolution for best results

### Voice Sample (Optional)

- **Format**: WAV
- **Duration**: 3-10 seconds recommended
- **Content**: Clear, natural speech in target language
- **Use**: Reference for voice cloning (XTTS engine only)

### Screen Recording (Optional)

- **Format**: MP4 or other video format
- **Duration**: Should match or exceed script length
- **Use**: Picture-in-Picture overlay alongside avatar

## ⚙️ Configuration & Modes

### Processing Modes

**Fast Mode** (Wav2Lip + Piper)
- Fastest processing
- Works on 4+ GB VRAM
- Good lip-sync quality
- Less expressive face
- Best for: Quick turnarounds, limited resources

**Balanced Mode** (SadTalker + XTTS)
- Good balance of speed and quality
- Requires 8+ GB VRAM
- Expressive avatar with natural movements
- Better voice cloning capability
- Best for: Professional videos, general use

**Quality Mode** (SadTalker + XTTS + refinement)
- Highest quality output
- Requires 12+ GB VRAM
- Multiple refinement passes
- Longest processing time
- Best for: High-stakes productions, premium content

### Resolution & FPS

| Resolution | Use Cases | Performance |
|-----------|-----------|-------------|
| 720p | Social media, web streaming | Fastest |
| 1080p | Professional videos, YouTube | Balanced |
| 4K | Premium, high-detail content | Slowest, needs 24+ GB VRAM |

Standard FPS: 24-30 (higher = larger files, smoother motion)

## 🔧 Advanced Features

### Resume / Checkpoint Recovery

If a render fails or is interrupted:

```bash
# Restart with resume flag (starts from last completed stage)
python generate.py \
    --script script.txt \
    --avatar avatar.jpg \
    --output output.mp4 \
    --resume
```

Project state is stored in `projects/{video_name}.db` (SQLite).

### Preview Mode

Generate only a 30-second preview to test settings before full render:

```bash
python generate.py --script script.txt --avatar avatar.jpg --output output.mp4 --preview
```

### Download Models

Manually download models or switch between minimal and full sets:

```bash
# Minimal model set (~560 MB)
python scripts/download_models.py --minimal

# Full model set (~2.5 GB total)
python scripts/download_models.py --full
```

Models auto-download on first use, so this is optional.

## 📊 Performance Expectations

### Processing Time Estimates

(Approximate times on RTX 3090 / RTX 4090)

| Mode | Duration | Resolution | Time |
|------|----------|-----------|------|
| Fast (Wav2Lip + Piper) | 1 min | 1080p | 2-3 min |
| Fast | 5 min | 1080p | 8-12 min |
| Balanced (SadTalker + XTTS) | 1 min | 1080p | 3-5 min |
| Balanced | 5 min | 1080p | 12-20 min |
| Quality (with refinement) | 1 min | 1080p | 5-8 min |
| Quality | 5 min | 1080p | 20-35 min |

**Notes:**
- First run downloads models (~2-5 min)
- Processing scales with video duration and resolution
- Slower on GPUs with less VRAM (CPU fallback slower)
- Voice cloning (XTTS) adds ~10% processing time

### Disk Space Usage

- **Models**: ~2.5 GB (downloaded to `models/`)
- **Temp processing**: ~1-3 GB per video (cleared on success)
- **Output video**: ~50-200 MB (varies by resolution, compression, duration)

## 🐛 Troubleshooting

### FFmpeg Not Found

**Error**: `[WARNING] FFmpeg not found`

**Solution**:
1. Install FFmpeg from https://www.gyan.dev/ffmpeg/builds/
2. Add `bin/` folder to system PATH
3. Restart terminal/VS Code
4. Run installer again

### Out of Memory (OOM)

**Error**: `CUDA out of memory` or similar

**Solutions**:
1. Switch to faster mode:
   ```bash
   python generate.py ... --mode fast
   ```
2. Reduce resolution:
   ```bash
   python generate.py ... --resolution 720p
   ```
3. Use CPU (slower but works):
   ```bash
   python generate.py ... --device cpu
   ```
4. Close other GPU applications (browser, games, etc.)

### Model Download Fails

**Error**: `Connection timeout` or failed checksum

**Solution**:
```bash
# Manually retry with --minimal flag
python scripts/download_models.py --minimal

# Or delete corrupted models and retry
rm -rf models/
python generate.py ... --skip-models-check
```

### Poor Quality Avatar Animation

**Causes**:
- Low-quality avatar image
- Unfavorable lighting in image
- Head at extreme angle

**Solutions**:
1. Use well-lit, frontal-facing photo
2. Try different avatar image
3. Switch to `--mode quality` for better refinement

### Slow Processing

**Possible Causes**:
- GPU overloaded (other apps using VRAM)
- CPU-bound (audio processing, encoding)
- Using CPU instead of GPU

**Solutions**:
1. Close unnecessary applications
2. Use faster mode: `--mode fast`
3. Verify GPU is being used: check logs

### Script Not Recognized / Encoding Issues

**Error**: Invalid characters in script file

**Solution**:
- Ensure script file is UTF-8 encoded
- Avoid special Unicode characters
- Use plain ASCII where possible

## 📚 Model Information

### Talking Head Models

| Model | Speed | Quality | VRAM | Voice Clone | Notes |
|-------|-------|---------|------|------------|-------|
| Wav2Lip | ⚡⚡⚡ | ⭐⭐⭐ | 4 GB | No | Accurate lip-sync only |
| SadTalker | ⚡⚡ | ⭐⭐⭐⭐ | 8+ GB | Via audio | Full facial animation |

### TTS Engines

| Engine | Speed | Quality | VRAM | Voice Clone | Languages |
|--------|-------|---------|------|------------|-----------|
| Piper | ⚡⚡⚡ | ⭐⭐⭐ | 1 GB | No | Multiple |
| XTTS-v2 | ⚡⚡ | ⭐⭐⭐⭐ | 6 GB | ✓ Yes | 13+ languages |

## 📝 License & Attribution

This project integrates several open-source models:
- **Wav2Lip**: [https://github.com/Rudrabha/Wav2Lip](https://github.com/Rudrabha/Wav2Lip)
- **SadTalker**: [https://github.com/OpenTalker/SadTalker](https://github.com/OpenTalker/SadTalker)
- **XTTS-v2**: [https://github.com/coqui-ai/TTS](https://github.com/coqui-ai/TTS)
- **Whisper**: [https://github.com/openai/whisper](https://github.com/openai/whisper)

Please refer to each model's license for usage terms.

## 🎓 Examples & Workflows

### Workflow 1: Quick Social Media Video

```bash
python generate.py \
    --script social_post.txt \
    --avatar avatar.jpg \
    --output social.mp4 \
    --mode fast \
    --resolution 720p \
    --no-subtitles
```
**Time**: ~5-8 minutes for 2-minute video

### Workflow 2: Professional Training Video

```bash
python generate.py \
    --script training.txt \
    --avatar trainer.jpg \
    --voice trainer_voice.wav \
    --output training.mp4 \
    --mode balanced \
    --resolution 1080p \
    --subtitles \
    --sub-style corporate \
    --burn-subs
```
**Time**: ~15-25 minutes for 5-minute video

### Workflow 3: Premium Marketing Video with Screen Share

```bash
python generate.py \
    --script marketing_pitch.txt \
    --avatar presenter.jpg \
    --voice presenter_voice.wav \
    --screen demo_screen.mp4 \
    --output marketing.mp4 \
    --mode quality \
    --resolution 1080p \
    --subtitles \
    --sub-style modern \
    --pip-layout side_by_side
```
**Time**: ~30-45 minutes for 5-minute video

## 📞 Support & Debugging

### View Detailed Logs

Check pipeline execution details:
```bash
cat logs/pipeline.log
```

### System Diagnostics

Verify environment setup:
```bash
python generate.py --script script.txt --avatar avatar.jpg --output out.mp4 --skip-models-check
```

(Skips model validation but runs diagnostics)

### GPU Diagnostics

Check CUDA setup:
```bash
python -c "import torch; print(f'CUDA: {torch.cuda.is_available()}'); print(f'GPU: {torch.cuda.get_device_name()}')"
```

---

**Last Updated**: May 10, 2026  
**Version**: 1.0  
**Status**: Production Ready

avatar_system/
├── generate.py              ← Main entry point (run this)
├── requirements.txt
├── sample_script.txt        ← Test script to try first
├── core/
│   ├── pipeline/
│   │   ├── orchestrator.py  ← Controls all stages
│   │   ├── project_state.py ← Resume interrupted renders
│   │   └── chunk_manager.py ← Long-form video splitting
│   ├── stages/
│   │   ├── tts/             ← XTTS-v2 + Piper TTS
│   │   ├── talking_head/    ← SadTalker + Wav2Lip
│   │   ├── subtitles/       ← faster-whisper
│   │   ├── screen_overlay/  ← PiP compositor
│   │   └── compositor/      ← FFmpeg final render
│   └── utils/               ← GPU, logger, image tools
└── scripts/
    ├── install_windows.bat  ← Windows one-click setup
    ├── install_linux.sh     ← Linux one-click setup
    └── download_models.py   ← Downloads all checkpoints