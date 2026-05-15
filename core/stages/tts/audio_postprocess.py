"""
Audio post-processing: noise reduction, normalization, cleanup.
Requires: pip install noisereduce librosa soundfile
"""

import numpy as np
import soundfile as sf
import librosa
from core.utils.logger import log


def postprocess_audio(input_path: str, output_path: str,
                      target_dbfs: float = -3.0,
                      denoise: bool = True) -> bool:
    """
    Clean up TTS audio: denoise + normalize.
    Args:
        input_path:   Raw TTS audio path
        output_path:  Cleaned audio path
        target_dbfs:  Target peak level (-3 dB default)
        denoise:      Apply noise reduction
    """
    try:
        log.info("  Post-processing audio...")
        audio, sr = librosa.load(input_path, sr=None, mono=True)

        # Noise reduction
        if denoise:
            try:
                import noisereduce as nr
                audio = nr.reduce_noise(y=audio, sr=sr, prop_decrease=0.7,
                                        stationary=True)
                log.info("  Noise reduction applied")
            except ImportError:
                log.warning("  noisereduce not installed — skipping denoising")
                log.warning("  Install with: pip install noisereduce")

        # Trim leading/trailing silence
        audio, _ = librosa.effects.trim(audio, top_db=30)

        # Normalize to target dBFS
        peak = np.max(np.abs(audio))
        if peak > 0:
            target_linear = 10 ** (target_dbfs / 20)
            audio = audio * (target_linear / peak)

        # Clip guard
        audio = np.clip(audio, -1.0, 1.0)

        sf.write(output_path, audio, sr)
        duration = len(audio) / sr
        log.info(f"  Audio cleaned: {duration:.1f}s at {sr}Hz → {output_path}")
        return True

    except Exception as e:
        log.error(f"  Audio post-processing failed: {e}")
        # Fallback: just copy raw
        import shutil
        shutil.copy(input_path, output_path)
        return True  # Don't fail pipeline for this
