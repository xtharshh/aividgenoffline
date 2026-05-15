"""
System check — verifies all required tools and dependencies are present.
"""

import sys
import subprocess
import shutil
import torch
from core.utils.logger import log
from core.utils.ffmpeg_tools import get_ffmpeg_executable


def check_system():
    print("\n🔍 Checking system requirements...")
    issues = []

    # Python version
    if sys.version_info < (3, 9):
        issues.append(f"Python 3.9+ required (you have {sys.version})")
    else:
        print(f"  ✅ Python {sys.version_info.major}.{sys.version_info.minor}")

    # FFmpeg
    ffmpeg_path = get_ffmpeg_executable()
    if ffmpeg_path:
        result = subprocess.run([ffmpeg_path, "-version"], capture_output=True, text=True)
        version = result.stdout.split("\n")[0]
        print(f"  ✅ FFmpeg: {version[:40]}")
    else:
        issues.append("FFmpeg not found — install from https://ffmpeg.org/download.html")

    # Git
    if shutil.which("git"):
        print("  ✅ Git")
    else:
        issues.append("Git not found — required for cloning model repos")

    # CUDA / GPU
    if torch.cuda.is_available():
        gpu_name = torch.cuda.get_device_name(0)
        vram_gb  = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"  ✅ CUDA GPU: {gpu_name} ({vram_gb:.1f} GB VRAM)")
        if vram_gb < 4:
            issues.append(f"GPU has only {vram_gb:.1f} GB VRAM — minimum 4 GB recommended")
    else:
        print("  ⚠️  No CUDA GPU — will run on CPU (very slow)")
        log.warning("No CUDA GPU detected. Generation will be much slower on CPU.")

    # Core Python packages
    required_packages = [
        ("torch",          "torch"),
        ("torchaudio",     "torchaudio"),
        ("PIL",            "Pillow"),
        ("cv2",            "opencv-python"),
        ("soundfile",      "soundfile"),
        ("librosa",        "librosa"),
        ("faster_whisper", "faster-whisper"),
    ]

    for import_name, pip_name in required_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {pip_name}")
        except ImportError:
            issues.append(f"Missing: {pip_name} — install with: pip install {pip_name}")

    # Optional packages (warn but don't fail)
    optional_packages = [
        ("noisereduce", "noisereduce",   "audio denoising"),
        ("TTS",         "TTS",           "XTTS-v2 voice synthesis"),
        ("piper",       "piper-tts",     "Piper TTS (fast mode)"),
    ]

    for import_name, pip_name, feature in optional_packages:
        try:
            __import__(import_name)
            print(f"  ✅ {pip_name} ({feature})")
        except ImportError:
            print(f"  ⚠️  {pip_name} not installed ({feature})")
            print(f"       Install with: pip install {pip_name}")

    # Report results
    if issues:
        print("\n❌ Issues found:")
        for issue in issues:
            print(f"   • {issue}")
        print("\nFix the above issues before running the pipeline.")
        print("Or run with --skip-models-check to bypass.\n")
        if any("FFmpeg" in i or "Git" in i for i in issues):
            sys.exit(1)  # Hard fail for critical deps
    else:
        print("\n✅ All checks passed!\n")
