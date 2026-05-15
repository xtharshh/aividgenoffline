"""
Whisper Transcriber — generates word-level subtitles from audio.
Requires: pip install faster-whisper
"""

import os
import torch
from core.utils.logger import log

RESOLUTION_DIMS = {
    "720p":  (1280, 720),
    "1080p": (1920, 1080),
    "4k":    (3840, 2160),
}

SUBTITLE_STYLES = {
    "modern": {
        "FontName": "Arial", "FontSize": 26,
        "PrimaryColour": "&H00FFFFFF", "BackColour": "&H80000000",
        "BorderStyle": 3, "Outline": 0, "Shadow": 0,
        "Alignment": 2, "MarginV": 50,
    },
    "corporate": {
        "FontName": "Arial", "FontSize": 22,
        "PrimaryColour": "&H00FFFFFF", "BackColour": "&HCC003366",
        "BorderStyle": 3, "Outline": 0, "Shadow": 0,
        "Alignment": 2, "MarginV": 40,
    },
    "minimal": {
        "FontName": "Arial", "FontSize": 24,
        "PrimaryColour": "&H00FFFFFF", "BackColour": "&H00000000",
        "BorderStyle": 1, "Outline": 2, "Shadow": 1,
        "Alignment": 2, "MarginV": 40,
    },
    "karaoke": {
        "FontName": "Arial", "FontSize": 26,
        "PrimaryColour": "&H00FFFFFF", "SecondaryColour": "&H0000FFFF",
        "BackColour": "&H80000000",
        "BorderStyle": 3, "Outline": 0, "Shadow": 0,
        "Alignment": 2, "MarginV": 50,
    },
}


class WhisperTranscriber:
    def __init__(self, model_size: str = "medium", device: str = "cuda"):
        self.model_size = model_size
        self.device = device
        self.model = None

    def _load(self):
        if self.model is not None:
            return
        log.info(f"  Loading faster-whisper ({self.model_size})...")
        try:
            from faster_whisper import WhisperModel
            compute_type = "float16" if self.device == "cuda" else "int8"
            self.model = WhisperModel(
                self.model_size,
                device=self.device,
                compute_type=compute_type
            )
            log.info("  Whisper loaded ✓")
        except ImportError:
            log.error("  faster-whisper not installed")
            log.error("  Install with: pip install faster-whisper")
            raise

    def transcribe(self, audio_path: str, srt_path: str, ass_path: str,
                   style: str = "modern", resolution: str = "1080p") -> bool:
        try:
            self._load()
            log.info(f"  Transcribing: {audio_path}")

            segments, info = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                language="en",
                beam_size=5
            )
            segments = list(segments)
            log.info(f"  Detected language: {info.language} ({info.language_probability:.0%})")
            log.info(f"  Segments: {len(segments)}")

            # Write SRT
            self._write_srt(segments, srt_path)

            # Write ASS
            width, height = RESOLUTION_DIMS.get(resolution, (1920, 1080))
            self._write_ass(segments, ass_path, style, width, height)

            log.info(f"  SRT → {srt_path}")
            log.info(f"  ASS → {ass_path}")
            return True

        except Exception as e:
            log.error(f"  Transcription failed: {e}")
            return False

    def _format_time_srt(self, seconds: float) -> str:
        h  = int(seconds // 3600)
        m  = int((seconds % 3600) // 60)
        s  = int(seconds % 60)
        ms = int((seconds % 1) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    def _format_time_ass(self, seconds: float) -> str:
        h  = int(seconds // 3600)
        m  = int((seconds % 3600) // 60)
        s  = int(seconds % 60)
        cs = int((seconds % 1) * 100)
        return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

    def _write_srt(self, segments, srt_path: str):
        lines = []
        for i, seg in enumerate(segments, 1):
            lines.append(str(i))
            lines.append(f"{self._format_time_srt(seg.start)} --> {self._format_time_srt(seg.end)}")
            lines.append(seg.text.strip())
            lines.append("")
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

    def _write_ass(self, segments, ass_path: str, style_name: str,
                   width: int, height: int):
        st = SUBTITLE_STYLES.get(style_name, SUBTITLE_STYLES["modern"])

        header = f"""[Script Info]
ScriptType: v4.00+
PlayResX: {width}
PlayResY: {height}
WrapStyle: 0

[V4+ Styles]
Format: Name, FontName, FontSize, PrimaryColour, BackColour, BorderStyle, Outline, Shadow, Alignment, MarginV
Style: Default,{st['FontName']},{st['FontSize']},{st['PrimaryColour']},{st['BackColour']},{st['BorderStyle']},{st['Outline']},{st['Shadow']},{st['Alignment']},{st['MarginV']}

[Events]
Format: Layer, Start, End, Style, Text
"""
        events = []
        for seg in segments:
            if style_name == "karaoke" and seg.words:
                # Word-level karaoke highlighting
                karaoke_text = ""
                for word in seg.words:
                    dur_cs = int((word.end - word.start) * 100)
                    karaoke_text += f"{{\\kf{dur_cs}}}{word.word}"
                events.append(
                    f"Dialogue: 0,{self._format_time_ass(seg.start)},"
                    f"{self._format_time_ass(seg.end)},Default,{karaoke_text.strip()}"
                )
            else:
                text = seg.text.strip().replace("\n", " ")
                events.append(
                    f"Dialogue: 0,{self._format_time_ass(seg.start)},"
                    f"{self._format_time_ass(seg.end)},Default,{text}"
                )

        with open(ass_path, "w", encoding="utf-8") as f:
            f.write(header + "\n".join(events))

    def unload(self):
        if self.model is not None:
            del self.model
            self.model = None
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
