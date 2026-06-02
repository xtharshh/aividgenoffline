"""
PiP Compositor — overlays avatar on screen recording.
Pure FFmpeg, no GPU required.
"""

import subprocess
import os
from core.utils.logger import log
from core.utils.ffmpeg_tools import get_ffmpeg_executable

RESOLUTION_DIMS = {
    "720p":  (1280, 720),
    "1080p": (1920, 1080),
    "4k":    (3840, 2160),
}


class PiPCompositor:
    def composite(self, screen_video: str, avatar_video: str, output_path: str,
                  layout: str = "bottom_right", resolution: str = "1080p") -> bool:
        """
        Composite avatar over screen recording.
        Args:
            screen_video: Background screen recording
            avatar_video: Talking head video (avatar)
            output_path:  Output composite MP4
            layout:       pip position or "side_by_side"
            resolution:   Target output resolution
        """
        try:
            W, H = RESOLUTION_DIMS.get(resolution, (1920, 1080))
            MARGIN = 20
            AV_W = W // 5   # Avatar is 20% of frame width
            AV_H = H // 5
            ffmpeg_path = get_ffmpeg_executable()
            if not ffmpeg_path:
                raise RuntimeError("ffmpeg not available")

            log.info(f"  Creating PiP layout: {layout} ({W}x{H})")

            if layout == "side_by_side":
                # Screen 60% | Avatar 40%
                sc_w = int(W * 0.6)
                av_w = int(W * 0.4)
                cmd = [
                    ffmpeg_path, "-y",
                    "-i", screen_video,
                    "-i", avatar_video,
                    "-filter_complex",
                    f"[0:v]scale={sc_w}:{H}:force_original_aspect_ratio=decrease,pad={sc_w}:{H}:(ow-iw)/2:(oh-ih)/2:black[left];"
                    f"[1:v]scale={av_w}:{H}:force_original_aspect_ratio=decrease,pad={av_w}:{H}:(ow-iw)/2:(oh-ih)/2:black[right];"
                    f"[left][right]hstack=inputs=2[v]",
                    "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    output_path
                ]
            else:
                # PiP overlay positions using FFmpeg expressions
                positions = {
                    "bottom_right": f"W-w-{MARGIN}:H-h-{MARGIN}",
                    "bottom_left":  f"{MARGIN}:H-h-{MARGIN}",
                    "top_right":    f"W-w-{MARGIN}:{MARGIN}",
                    "top_left":     f"{MARGIN}:{MARGIN}",
                    "center":       f"(W-w)/2:(H-h)/2",
                    "top":          f"(W-w)/2:{MARGIN}",
                    "bottom":       f"(W-w)/2:H-h-{MARGIN}",
                    "left":         f"{MARGIN}:(H-h)/2",
                    "right":        f"W-w-{MARGIN}:(H-h)/2",
                }
                overlay_pos = positions.get(layout, positions["bottom_right"])

                cmd = [
                    ffmpeg_path, "-y",
                    "-i", screen_video,
                    "-i", avatar_video,
                    "-filter_complex",
                    f"[0:v]scale={W}:{H}:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:(oh-ih)/2:black[bg];"
                    f"[1:v]scale={AV_W}:{AV_H}:force_original_aspect_ratio=decrease,"
                    f"format=yuva420p,"
                    f"geq=lum='p(X,Y)':a='if(gt(alpha(X,Y),128),255,0)'[pip];"
                    f"[bg][pip]overlay={overlay_pos}[v]",
                    "-map", "[v]", "-map", "1:a",
                    "-c:v", "libx264", "-crf", "18", "-preset", "fast",
                    "-c:a", "aac", "-b:a", "192k",
                    output_path
                ]

            result = subprocess.run(cmd, capture_output=True, text=True)

            if result.returncode != 0:
                log.error(f"  PiP composite failed:\n{result.stderr[-500:]}")
                return False

            log.info(f"  PiP composite created → {output_path}")
            return True

        except Exception as e:
            log.error(f"  PiP compositor error: {e}")
            return False
