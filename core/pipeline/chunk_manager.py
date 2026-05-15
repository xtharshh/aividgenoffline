"""
Chunk manager — splits long audio/video into segments for stable long-form generation.
"""

import os
import math
import subprocess
import json
import wave
from core.utils.logger import log
from core.utils.ffmpeg_tools import get_ffmpeg_executable


class ChunkManager:
    def __init__(self, chunk_duration: int = 30, overlap: int = 2):
        self.chunk_duration = chunk_duration
        self.overlap = overlap

    def split_audio(self, audio_path: str, output_dir: str) -> list[dict]:
        """Split audio into overlapping chunks. Returns list of chunk info dicts."""
        os.makedirs(output_dir, exist_ok=True)

        # Get total duration
        try:
            with wave.open(audio_path, "rb") as wav_file:
                total_duration = wav_file.getnframes() / float(wav_file.getframerate())
        except Exception:
            total_duration = 0.0
            ffmpeg_exe = get_ffmpeg_executable()
            if ffmpeg_exe:
                result = subprocess.run([ffmpeg_exe, "-i", audio_path], capture_output=True, text=True)
                for line in (result.stderr or "").splitlines():
                    if "Duration:" in line:
                        duration_text = line.split("Duration:", 1)[1].split(",", 1)[0].strip()
                        hours, minutes, seconds = duration_text.split(":")
                        total_duration = (float(hours) * 3600.0) + (float(minutes) * 60.0) + float(seconds)
                        break
        log.info(f"Audio duration: {total_duration:.1f}s")

        chunks = []
        chunk_id = 0
        start = 0.0

        while start < total_duration:
            end = min(start + self.chunk_duration, total_duration)
            chunk_path = os.path.join(output_dir, f"chunk_{chunk_id:04d}.wav")

            ffmpeg_exe = get_ffmpeg_executable()
            if not ffmpeg_exe:
                raise RuntimeError("ffmpeg not available for audio chunking")

            subprocess.run([
                ffmpeg_exe, "-y", "-i", audio_path,
                "-ss", str(start),
                "-t", str(end - start),
                "-c:a", "pcm_s16le",
                chunk_path
            ], capture_output=True)

            chunks.append({
                "id": chunk_id,
                "start": start,
                "end": end,
                "duration": end - start,
                "path": chunk_path
            })

            chunk_id += 1
            start += self.chunk_duration - self.overlap
            if start >= total_duration:
                break

        log.info(f"Split into {len(chunks)} chunks ({self.chunk_duration}s each, {self.overlap}s overlap)")
        return chunks

    def merge_videos(self, chunk_paths: list[str], output_path: str,
                     crossfade_duration: float = 0.5) -> bool:
        """Merge video chunks with crossfade at boundaries."""
        if not chunk_paths:
            return False

        if len(chunk_paths) == 1:
            import shutil
            shutil.copy(chunk_paths[0], output_path)
            return True

        # Write concat list
        list_path = output_path.replace(".mp4", "_concat.txt")
        with open(list_path, "w") as f:
            for p in chunk_paths:
                f.write(f"file '{os.path.abspath(p)}'\n")

        ffmpeg_exe = get_ffmpeg_executable()
        if not ffmpeg_exe:
            raise RuntimeError("ffmpeg not available for video merging")

        result = subprocess.run([
            ffmpeg_exe, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c:v", "libx264", "-crf", "18", "-preset", "fast",
            "-c:a", "aac", "-b:a", "192k",
            output_path
        ], capture_output=True, text=True)

        os.remove(list_path)

        if result.returncode != 0:
            log.error(f"Merge failed: {result.stderr[-500:]}")
            return False

        log.info(f"Merged {len(chunk_paths)} chunks → {output_path}")
        return True

    def get_chunk_count(self, audio_duration: float) -> int:
        effective_step = self.chunk_duration - self.overlap
        return math.ceil((audio_duration - self.overlap) / effective_step)
