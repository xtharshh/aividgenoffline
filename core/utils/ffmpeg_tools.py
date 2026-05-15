"""
FFmpeg helpers — resolve a usable ffmpeg binary and expose it to subprocesses.
"""

from __future__ import annotations

import os
import shutil
from pathlib import Path


_WRAPPER_DIR = Path(__file__).resolve().parents[2] / "temp" / "ffmpeg-bin"
_ENV_PATCHED = False


def _find_bundled_ffmpeg() -> str | None:
    try:
        import imageio_ffmpeg

        ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
        if ffmpeg_path and Path(ffmpeg_path).exists():
            return ffmpeg_path
    except Exception:
        pass

    for candidate in [
        r"C:\Program Files\ffmpeg-8.1.1-essentials_build\bin\ffmpeg.exe",
        r"C:\ffmpeg\bin\ffmpeg.exe",
    ]:
        if Path(candidate).exists():
            return candidate

    return None


def get_ffmpeg_executable() -> str | None:
    ffmpeg_path = _find_bundled_ffmpeg()
    if ffmpeg_path:
        return ffmpeg_path

    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path

    return None


def ensure_ffmpeg_on_path() -> str | None:
    """Create a small wrapper and prepend it to PATH if ffmpeg is otherwise unavailable."""
    global _ENV_PATCHED

    ffmpeg_path = get_ffmpeg_executable()
    if not ffmpeg_path:
        return None

    if _ENV_PATCHED:
        return ffmpeg_path

    _WRAPPER_DIR.mkdir(parents=True, exist_ok=True)
    wrapper_path = _WRAPPER_DIR / "ffmpeg.cmd"
    wrapper_path.write_text(f'@echo off\r\n"{ffmpeg_path}" %*\r\n', encoding="utf-8")

    current_path = os.environ.get("PATH", "")
    wrapper_dir_text = str(_WRAPPER_DIR)
    if wrapper_dir_text.lower() not in current_path.lower():
        os.environ["PATH"] = wrapper_dir_text + os.pathsep + current_path

    _ENV_PATCHED = True
    return ffmpeg_path