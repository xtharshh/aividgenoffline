#!/usr/bin/env python3
"""
Model Downloader — download all required model checkpoints.
Run this once before first use.

Usage:
    python scripts/download_models.py             # download all
    python scripts/download_models.py --minimal   # Wav2Lip + Piper only (4 GB GPU)
    python scripts/download_models.py --list      # list available models
"""

import os
import sys
import argparse
import urllib.request
import subprocess
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))


def progress_bar(count, block_size, total_size):
    if total_size > 0:
        percent = min(count * block_size / total_size * 100, 100)
        mb_done  = count * block_size / 1024 / 1024
        mb_total = total_size / 1024 / 1024
        print(f"\r    {percent:5.1f}% ({mb_done:.0f}/{mb_total:.0f} MB)", end="", flush=True)


def download(url, dest, label=""):
    if os.path.exists(dest):
        size_mb = os.path.getsize(dest) / 1024 / 1024
        print(f"  Already downloaded: {label} ({size_mb:.0f} MB)")
        return True
    os.makedirs(os.path.dirname(dest) if os.path.dirname(dest) else ".", exist_ok=True)
    print(f"  Downloading: {label}")
    try:
        urllib.request.urlretrieve(url, dest, reporthook=progress_bar)
        print()
        size_mb = os.path.getsize(dest) / 1024 / 1024
        print(f"  Done ({size_mb:.0f} MB)")
        return True
    except Exception as e:
        print(f"\n  Failed: {e}")
        return False


def clone_repo(url, dest, label=""):
    if os.path.exists(dest):
        print(f"  Repo already exists: {label}")
        return True
    print(f"  Cloning: {label}")
    result = subprocess.run(
        f"git clone --depth 1 {url} {dest}",
        shell=True, capture_output=True, text=True
    )
    if result.returncode == 0:
        print(f"  Cloned OK: {dest}")
        req = os.path.join(dest, "requirements.txt")
        if os.path.exists(req):
            print(f"  Installing deps...")
            # Try to install requirements, but continue even if it fails
            # (some repos have incompatible dependencies for latest Python versions)
            result = subprocess.run(
                f"pip install -q -r {req} --no-cache-dir --disable-pip-version-check",
                shell=True, capture_output=True, text=True
            )
            if result.returncode != 0:
                print(f"  WARNING: Some dependencies failed to install (this is OK)")
                print(f"      Repo can still be used - some features may be unavailable")
            else:
                print(f"  OK: Dependencies installed")
        return True
    else:
        print(f"  WARNING: Clone failed: {result.stderr[:200]}")
        print(f"      This may not be critical - proceeding anyway")
        return False


REPOS = {
    "wav2lip":   ("https://github.com/Rudrabha/Wav2Lip",          "repos/Wav2Lip",    "minimal"),
    "sadtalker": ("https://github.com/OpenTalker/SadTalker",       "repos/SadTalker",  "full"),
}

CHECKPOINTS = [
    # (url, dest, label, tier, size_mb_approx)
    ("https://huggingface.co/numz/wav2lip_studio/resolve/main/Wav2lip/wav2lip_gan.pth",
     "repos/Wav2Lip/checkpoints/wav2lip_gan.pth",
     "Wav2Lip GAN checkpoint", "minimal", 415),

    ("https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth",
     "repos/Wav2Lip/face_detection/detection/sfd/s3fd.pth",
     "Wav2Lip face detection", "minimal", 85),

    ("https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
     "models/piper/en_US-lessac-medium.onnx",
     "Piper TTS voice (English female)", "minimal", 63),

    ("https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
     "models/piper/en_US-lessac-medium.onnx.json",
     "Piper TTS voice config", "minimal", 1),

    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_256.safetensors",
     "repos/SadTalker/checkpoints/SadTalker_V0.0.2_256.safetensors",
     "SadTalker 256px checkpoint", "full", 726),

    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/SadTalker_V0.0.2_512.safetensors",
     "repos/SadTalker/checkpoints/SadTalker_V0.0.2_512.safetensors",
     "SadTalker 512px checkpoint", "full", 726),

    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00109-model.pth.tar",
     "repos/SadTalker/checkpoints/mapping_00109-model.pth.tar",
     "SadTalker mapping 1", "full", 170),

    ("https://github.com/OpenTalker/SadTalker/releases/download/v0.0.2-rc/mapping_00229-model.pth.tar",
     "repos/SadTalker/checkpoints/mapping_00229-model.pth.tar",
     "SadTalker mapping 2", "full", 170),
]


def main():
    parser = argparse.ArgumentParser(description="Download model checkpoints")
    parser.add_argument("--minimal", action="store_true",
                        help="Minimal set only (Wav2Lip + Piper, for 4 GB GPU)")
    parser.add_argument("--full",    action="store_true",
                        help="Full set (Wav2Lip + SadTalker + Piper)")
    parser.add_argument("--list",    action="store_true",
                        help="List all models without downloading")
    args = parser.parse_args()

    tier_filter = "minimal" if args.minimal else "all"

    if args.list:
        print("\nAvailable models:")
        print(f"{'Model':<45} {'Tier':<10} {'Size':>8}")
        print("-" * 65)
        for url, dest, label, tier, size in CHECKPOINTS:
            exists = "[OK]" if os.path.exists(dest) else "    "
            print(f"{exists} {label:<43} {tier:<10} {size:>5} MB")
        return

    print("\n" + "=" * 55)
    print("  Model Downloader")
    print("=" * 55)
    print(f"  Tier: {'minimal (4 GB GPU)' if args.minimal else 'full'}")

    # Clone repos
    print("\n── Repositories ──────────────────────────────")
    for name, (url, dest, tier) in REPOS.items():
        if tier_filter == "minimal" and tier != "minimal":
            continue
        clone_repo(url, dest, name)

    # Download checkpoints
    print("\n── Checkpoints ───────────────────────────────")
    total_size = 0
    skipped_size = 0
    for url, dest, label, tier, size in CHECKPOINTS:
        if tier_filter == "minimal" and tier != "minimal":
            continue
        if os.path.exists(dest):
            skipped_size += size
        else:
            total_size += size

    if total_size > 0:
        print(f"  Will download ~{total_size} MB of new models")
    else:
        print("  All models already downloaded!")

    for url, dest, label, tier, size in CHECKPOINTS:
        if tier_filter == "minimal" and tier != "minimal":
            continue
        download(url, dest, label)

    print("\n" + "=" * 55)
    print("  Download complete!")
    print(f"\n  Next steps:")
    print(f"  1. python generate.py --script script.txt --avatar avatar.jpg --output out.mp4")
    if args.minimal:
        print(f"  2. For better quality, run: python scripts/download_models.py --full")
    print("=" * 55 + "\n")


if __name__ == "__main__":
    main()
