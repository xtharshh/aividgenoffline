"""
XTTS-v2 TTS Engine — high-quality multilingual TTS with voice cloning.
Requires: pip install TTS
Model auto-downloads on first use (~1.8 GB).
"""

import os
import torch
from core.utils.logger import log


class XTTSEngine:
    def __init__(self, device: str = "cuda"):
        self.device = device
        self.model = None

    def _load(self):
        if self.model is not None:
            return
        log.info("  Loading XTTS-v2...")
        try:
            from TTS.api import TTS
            self.model = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to(self.device)
            log.info("  XTTS-v2 loaded ✓")
        except Exception as e:
            log.error(f"  Failed to load XTTS-v2: {e}")
            log.error("  Install with: pip install TTS")
            raise

    def synthesize(self, text: str, output_path: str,
                   voice_sample: str = None, language: str = "en") -> bool:
        """
        Synthesize speech from text.
        Args:
            text: Input text (any length — handled internally)
            output_path: Output WAV path
            voice_sample: Optional reference audio for voice cloning
            language: Language code (en, es, fr, de, ja, zh, etc.)
        """
        try:
            self._load()

            kwargs = dict(
                text=text,
                file_path=output_path,
                language=language
            )

            if voice_sample and os.path.exists(voice_sample):
                kwargs["speaker_wav"] = voice_sample
                log.info(f"  Voice cloning from: {voice_sample}")
            else:
                # Use a built-in speaker
                speakers = self.model.speakers
                default_speaker = speakers[0] if speakers else None
                if default_speaker:
                    kwargs["speaker"] = default_speaker
                log.info(f"  Using default speaker: {default_speaker}")

            log.info(f"  Synthesizing {len(text.split())} words...")
            self.model.tts_to_file(**kwargs)
            log.info(f"  Audio saved: {output_path}")
            return True

        except Exception as e:
            log.error(f"  XTTS synthesis failed: {e}")
            return False

    def unload(self):
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
