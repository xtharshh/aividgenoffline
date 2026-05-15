"""
Piper TTS Engine — ultra-fast offline TTS, great for 4 GB GPUs.
Requires: pip install piper-tts
Models: ~50-200 MB each, auto-downloaded.
"""

import os
import sys
import shutil
import subprocess
import urllib.request
from core.utils.logger import log

PIPER_MODELS = {
    "en_US_female": {
        "url_onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx",
        "url_json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json",
        "filename": "en_US-lessac-medium.onnx"
    },
    "en_US_male": {
        "url_onnx": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx",
        "url_json": "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/ryan/medium/en_US-ryan-medium.onnx.json",
        "filename": "en_US-ryan-medium.onnx"
    },
}

DEFAULT_VOICE = "en_US_female"
MODELS_DIR = "models/piper"


class PiperEngine:
    def __init__(self, voice: str = DEFAULT_VOICE):
        self.voice = voice
        self.model_path = None
        os.makedirs(MODELS_DIR, exist_ok=True)

    def _download_model(self):
        if self.voice not in PIPER_MODELS:
            log.warning(f"Unknown Piper voice '{self.voice}', using default")
            self.voice = DEFAULT_VOICE

        info = PIPER_MODELS[self.voice]
        onnx_path = os.path.join(MODELS_DIR, info["filename"])
        json_path  = onnx_path + ".json"

        if not os.path.exists(onnx_path):
            log.info(f"  Downloading Piper model: {info['filename']}...")
            urllib.request.urlretrieve(info["url_onnx"], onnx_path)
            urllib.request.urlretrieve(info["url_json"], json_path)
            log.info("  Piper model downloaded ✓")

        self.model_path = onnx_path
        return onnx_path

    def synthesize(self, text: str, output_path: str,
                   voice_sample: str = None, language: str = "en") -> bool:
        """
        Synthesize speech using Piper TTS.
        Note: Piper does not support voice cloning.
        """
        try:
            model_path = self._download_model()
            log.info(f"  Synthesizing with Piper ({self.voice})...")

            # Prefer CLI: it's more stable across piper-tts versions.
            scripts_dir = os.path.dirname(sys.executable)
            candidates = [
                os.path.join(scripts_dir, "piper.exe"),
                shutil.which("piper"),
            ]
            piper_bin = next((c for c in candidates if c and os.path.exists(c)), None)

            if piper_bin:
                result = subprocess.run(
                    [piper_bin, "--model", model_path, "--output_file", output_path],
                    input=text,
                    text=True,
                    capture_output=True,
                )
                if result.returncode == 0 and os.path.exists(output_path) and os.path.getsize(output_path) > 44:
                    log.info(f"  Audio saved: {output_path}")
                    return True
                log.warning("  Piper CLI produced empty/invalid output, trying Python API fallback...")

            # Try Python API first
            try:
                from piper import PiperVoice
                import wave

                voice_model = PiperVoice.load(model_path)
                with wave.open(output_path, "wb") as wav_file:
                    # Initialize WAV header before writing frames.
                    # Piper outputs mono 16-bit PCM.
                    sample_rate = 22050
                    if hasattr(voice_model, "config") and hasattr(voice_model.config, "sample_rate"):
                        sample_rate = int(voice_model.config.sample_rate)
                    wav_file.setnchannels(1)
                    wav_file.setsampwidth(2)
                    wav_file.setframerate(sample_rate)
                    voice_model.synthesize(text, wav_file)
                if os.path.exists(output_path) and os.path.getsize(output_path) > 44:
                    log.info(f"  Audio saved: {output_path}")
                    return True
                log.error("  Piper Python API generated empty audio")
                return False

            except ImportError:
                log.error("  Piper Python API not available and CLI was not found")
                return False

        except Exception as e:
            log.error(f"  Piper synthesis failed: {e}")
            log.error("  Install with: pip install piper-tts")
            return False

    def unload(self):
        pass  # Piper is lightweight, no cleanup needed
