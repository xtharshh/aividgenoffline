"""
FFmpeg Final Renderer — merges video, audio, subtitles into final MP4.
"""

import os
import subprocess
import shutil
from core.utils.logger import log
from core.utils.ffmpeg_tools import get_ffmpeg_executable

RESOLUTION_DIMS = {
    "720p":  (1280, 720),
    "1080p": (1920, 1080),
    "4k":    (3840, 2160),
}


class FFmpegRenderer:
    def render(self, video_path: str, audio_path: str, output_path: str,
               ass_path: str = None, resolution: str = "1080p",
               fps: int = 25, quality: int = 18) -> bool:
        """
        Final render: merge video + audio, burn subtitles, encode.
        Args:
            video_path:  Input video (avatar or composite)
            audio_path:  Clean audio WAV
            output_path: Output MP4
            ass_path:    ASS subtitle path (None = no burn-in)
            resolution:  Target resolution
            fps:         Output FPS
            quality:     CRF value (lower = better quality, larger file)
        """
        try:
            W, H = RESOLUTION_DIMS.get(resolution, (1920, 1080))
            os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)

            log.info(f"  Rendering {resolution} @ {fps}fps → {output_path}")

            # Build video filter chain
            vf_filters = [f"scale={W}:{H}:force_original_aspect_ratio=decrease",
                         f"pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black",
                         f"fps={fps}"]

            if ass_path and os.path.exists(ass_path):
                # Escape path for FFmpeg subtitle filter
                safe_ass = ass_path.replace("\\", "/").replace(":", "\\:")
                vf_filters.append(f"subtitles='{safe_ass}'")
                log.info("  Burning in subtitles")

            vf_string = ",".join(vf_filters)

            ffmpeg_path = get_ffmpeg_executable()
            if not ffmpeg_path:
                raise RuntimeError("ffmpeg not available")
            cmd = [
                ffmpeg_path, "-y",
                "-i", video_path,
                "-i", audio_path,
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-vf", vf_string,
                "-c:v", "libx264",
                "-crf", str(quality),
                "-preset", "slow",
                "-profile:v", "high",
                "-level", "4.1",
                "-c:a", "aac",
                "-b:a", "192k",
                "-ar", "44100",
                "-ac", "2",
                "-movflags", "+faststart",
                "-shortest",
                output_path
            ]

            log.info("  Running FFmpeg final encode...")
            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                log.error(f"  FFmpeg failed:\n{result.stderr[-1000:]}")
                return False

            # Report output stats
            size_mb = os.path.getsize(output_path) / (1024 * 1024)
            duration = self._get_duration(output_path)
            log.info(f"  ✅ Rendered: {size_mb:.1f} MB, {duration:.1f}s")
            return True

        except Exception as e:
            log.error(f"  FFmpeg renderer error: {e}")
            return False

    def _get_duration(self, video_path: str) -> float:
        try:
            ffprobe_path = shutil.which("ffprobe")
            if not ffprobe_path:
                return 0.0
            result = subprocess.run(
                [ffprobe_path, "-v", "error", "-show_entries", "format=duration",
                 "-of", "default=noprint_wrappers=1:nokey=1", video_path],
                capture_output=True, text=True
            )
            return float(result.stdout.strip())
        except:
            return 0.0
