"""
SadTalker Runner — expressive talking head with emotion, head pose, blink.
Requires: git clone https://github.com/OpenTalker/SadTalker repos/SadTalker
Run scripts/download_models.py first to get checkpoints.
"""

import os
import sys
import glob
import shutil
import subprocess
import torch
from huggingface_hub import hf_hub_download
from core.utils.logger import log
from core.utils.image_utils import prepare_avatar_image

SADTALKER_DIR = "repos/SadTalker"
SADTALKER_REPO_ID = "vinthony/SadTalker"
PYTHON_EXE = sys.executable

RESOLUTION_SIZE = {
    "720p":  256,
    "1080p": 512,
    "4k":    512,
}


class SadTalkerRunner:
    def __init__(self, device: str = "cuda"):
        self.device = device

    def _ensure_repo(self):
        if not os.path.exists(SADTALKER_DIR):
            log.info("  Cloning SadTalker repo...")
            result = subprocess.run(
                f"git clone https://github.com/OpenTalker/SadTalker {SADTALKER_DIR}",
                shell=True, capture_output=True, text=True
            )
            if result.returncode != 0:
                raise RuntimeError(f"Failed to clone SadTalker: {result.stderr}")

            # Install SadTalker deps
            subprocess.run(
                [PYTHON_EXE, "-m", "pip", "install", "-r", f"{SADTALKER_DIR}/requirements.txt"],
                shell=False, capture_output=True, text=True
            )

    def _ensure_checkpoints(self):
        ckpt_dir = f"{SADTALKER_DIR}/checkpoints"
        gfpgan_dir = f"{SADTALKER_DIR}/gfpgan/weights"
        os.makedirs(ckpt_dir, exist_ok=True)
        os.makedirs(gfpgan_dir, exist_ok=True)

        needed_files = [
            "mapping_00109-model.pth.tar",
            "mapping_00229-model.pth.tar",
            "auido2exp_00300-model.pth",
            "auido2pose_00140-model.pth",
            "facevid2vid_00189-model.pth.tar",
            "epoch_20.pth",
            "wav2lip.pth",
            "shape_predictor_68_face_landmarks.dat",
            "BFM_Fitting/01_MorphableModel.mat",
            "BFM_Fitting/BFM09_model_info.mat",
            "BFM_Fitting/BFM_exp_idx.mat",
            "BFM_Fitting/BFM_front_idx.mat",
            "BFM_Fitting/Exp_Pca.bin",
            "BFM_Fitting/facemodel_info.mat",
            "BFM_Fitting/select_vertex_id.mat",
            "BFM_Fitting/similarity_Lm3D_all.mat",
            "BFM_Fitting/std_exp.txt",
            "hub/checkpoints/2DFAN4-cd938726ad.zip",
            "hub/checkpoints/s3fd-619a316812.pth",
        ]

        failed = []
        for rel_path in needed_files:
            dest = os.path.join(ckpt_dir, rel_path)
            if os.path.exists(dest):
                continue

            log.info(f"  Downloading {rel_path}...")
            try:
                hf_hub_download(
                    repo_id=SADTALKER_REPO_ID,
                    filename=rel_path,
                    repo_type="model",
                    local_dir=ckpt_dir,
                )
            except Exception as e:
                failed.append((rel_path, str(e)))

        if failed:
            details = "; ".join([f"{name}: {err}" for name, err in failed[:3]])
            raise RuntimeError(f"SadTalker checkpoint download failed ({len(failed)} files): {details}")

    def generate(self, avatar_image: str, audio_path: str, output_path: str,
                 resolution: str = "1080p", fps: int = 25,
                 still_mode: bool = True, pose_style: int = 0, enhancer: str = "gfpgan",
                 vram_gb: float | None = None) -> bool:
        """
        Generate expressive talking head video from image + audio.
        Args:
            avatar_image: Path to portrait image
            audio_path:   Path to speech WAV
            output_path:  Output MP4 path
            resolution:   "720p" / "1080p" / "4k"
            fps:          Frames per second
            still_mode:   Reduce head movement (cleaner for presenters)
            enhancer:     "gfpgan" for face enhancement, None to skip
        """
        try:
            self._ensure_repo()
            self._ensure_checkpoints()

            size = RESOLUTION_SIZE.get(resolution, 256)
            # Heuristic: SadTalker 512 + GFPGAN often OOMs on 4–6GB GPUs.
            # We can still render final output at 1080p via ffmpeg later.
            if vram_gb is not None and vram_gb < 6:
                size = min(size, 256)
                enhancer = None
            result_dir = "temp/sadtalker_out"
            os.makedirs(result_dir, exist_ok=True)

            # Prepare avatar image
            prepared_img = prepare_avatar_image(avatar_image, resolution)

            env_prefix = "set PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True &&" if os.name == "nt" else "export PYTORCH_CUDA_ALLOC_CONF=expandable_segments:True &&"
            cmd_parts = [
                f"cd {SADTALKER_DIR} &&",
                env_prefix,
                f"{sys.executable} inference.py",
                f"--driven_audio {os.path.abspath(audio_path)}",
                f"--source_image {os.path.abspath(prepared_img)}",
                f"--result_dir {os.path.abspath(result_dir)}",
                f"--size {size}",
                f"--preprocess full",
            ]
            if vram_gb is not None and vram_gb < 6:
                cmd_parts.append("--batch_size 1")
            if still_mode:
                cmd_parts.append("--still")
            else:
                cmd_parts.append(f"--pose_style {pose_style}")
            if enhancer:
                cmd_parts.append(f"--enhancer {enhancer}")
            if self.device == "cpu":
                cmd_parts.append("--cpu")

            cmd = " ".join(cmd_parts)
            log.info(f"  Running SadTalker (size={size}, enhancer={enhancer})...")
            log.info(f"  This may take a while for long audio...")

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)

            if result.returncode != 0:
                log.error(f"  SadTalker error:\n{result.stderr[-1000:]}")
                return False

            # Find output video
            outputs = sorted(glob.glob(f"{result_dir}/**/*.mp4", recursive=True))
            if not outputs:
                log.error("  SadTalker produced no output video")
                return False

            shutil.copy(outputs[-1], output_path)
            log.info(f"  SadTalker complete → {output_path}")
            return True

        except Exception as e:
            log.error(f"  SadTalker failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    def unload(self):
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
