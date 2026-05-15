"""
Wav2Lip Runner — accurate lip sync, works on 4 GB VRAM.
Use as primary model (fast mode) or as refinement pass after SadTalker.
Requires: git clone https://github.com/Rudrabha/Wav2Lip repos/Wav2Lip
"""

import os
import sys
import glob
import shutil
import subprocess
import urllib.request
import torch
from core.utils.logger import log
from core.utils.image_utils import prepare_avatar_image

WAV2LIP_DIR   = "repos/Wav2Lip"
WAV2LIP_CKPT  = f"{WAV2LIP_DIR}/checkpoints/wav2lip_gan.pth"
WAV2LIP_URL   = "https://huggingface.co/numz/wav2lip_studio/resolve/main/Wav2lip/wav2lip_gan.pth"
FACE_DET_CKPT = f"{WAV2LIP_DIR}/face_detection/detection/sfd/s3fd.pth"
FACE_DET_URL  = "https://www.adrianbulat.com/downloads/python-fan/s3fd-619a316812.pth"


class Wav2LipRunner:
    """Primary Wav2Lip talking head (fast mode for 4 GB GPUs)."""

    def __init__(self, device: str = "cuda"):
        self.device = device

    def _ensure_repo(self):
        if not os.path.exists(WAV2LIP_DIR):
            log.info("  Cloning Wav2Lip repo...")
            subprocess.run(
                f"git clone https://github.com/Rudrabha/Wav2Lip {WAV2LIP_DIR}",
                shell=True, capture_output=True
            )
            subprocess.run(
                f"pip install -r {WAV2LIP_DIR}/requirements.txt",
                shell=True, capture_output=True
            )

    def _ensure_checkpoints(self):
        os.makedirs(f"{WAV2LIP_DIR}/checkpoints", exist_ok=True)
        os.makedirs(os.path.dirname(FACE_DET_CKPT), exist_ok=True)

        if not os.path.exists(WAV2LIP_CKPT):
            log.info("  Downloading Wav2Lip GAN checkpoint (~415 MB)...")
            urllib.request.urlretrieve(WAV2LIP_URL, WAV2LIP_CKPT)
            log.info("  Wav2Lip checkpoint downloaded ✓")

        if not os.path.exists(FACE_DET_CKPT):
            log.info("  Downloading face detection model...")
            urllib.request.urlretrieve(FACE_DET_URL, FACE_DET_CKPT)
            log.info("  Face detection model downloaded ✓")

    def generate(self, avatar_image: str, audio_path: str, output_path: str,
                 resolution: str = "1080p", fps: int = 25) -> bool:
        """Generate lip-synced video from avatar image + audio."""
        try:
            self._ensure_repo()
            self._ensure_checkpoints()

            prepared_img = prepare_avatar_image(avatar_image, resolution)

            nosmooth = "--nosmooth" if resolution in ("720p",) else ""
            resize   = "2" if resolution == "4k" else "1"

            cmd = (
                f"cd {WAV2LIP_DIR} && {sys.executable} inference.py "
                f"--checkpoint_path checkpoints/wav2lip_gan.pth "
                f"--face {os.path.abspath(prepared_img)} "
                f"--audio {os.path.abspath(audio_path)} "
                f"--outfile {os.path.abspath(output_path)} "
                f"--fps {fps} "
                f"--resize_factor {resize} "
                f"{nosmooth}"
            )

            log.info("  Running Wav2Lip...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                log.error(f"  Wav2Lip error:\n{result.stderr[-1000:]}")
                return False

            log.info(f"  Wav2Lip complete → {output_path}")
            return True

        except Exception as e:
            log.error(f"  Wav2Lip failed: {e}")
            return False

    def unload(self):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()


class Wav2LipRefiner:
    """Wav2Lip as refinement pass on top of SadTalker output."""

    def __init__(self, device: str = "cuda"):
        self.runner = Wav2LipRunner(device)

    def refine(self, input_video: str, audio_path: str, output_path: str) -> bool:
        """Apply Wav2Lip lip sync on top of an existing face video."""
        try:
            self.runner._ensure_repo()
            self.runner._ensure_checkpoints()

            cmd = (
                f"cd {WAV2LIP_DIR} && {sys.executable} inference.py "
                f"--checkpoint_path checkpoints/wav2lip_gan.pth "
                f"--face {os.path.abspath(input_video)} "
                f"--audio {os.path.abspath(audio_path)} "
                f"--outfile {os.path.abspath(output_path)} "
                f"--nosmooth"
            )
            log.info("  Running Wav2Lip refinement pass...")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                log.error(f"  Wav2Lip refinement error:\n{result.stderr[-500:]}")
                return False

            log.info(f"  Wav2Lip refinement complete → {output_path}")
            return True

        except Exception as e:
            log.error(f"  Wav2Lip refinement failed: {e}")
            return False

    def unload(self):
        self.runner.unload()
