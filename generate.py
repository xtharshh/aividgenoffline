#!/usr/bin/env python3
"""
Offline AI Avatar Video Generator
Usage:
    python generate.py --script script.txt --avatar avatar.jpg --output output.mp4
    python generate.py --script script.txt --avatar avatar.jpg --voice voice.wav --output output.mp4
    python generate.py --script script.txt --avatar avatar.jpg --screen screen.mp4 --output demo.mp4
"""

import argparse
import sys
import os
import time


def _bootstrap_project_python() -> None:
    """Re-exec under the bundled project environment when the active Python is incomplete."""
    try:
        import torch  # noqa: F401
        return
    except ModuleNotFoundError:
        pass

    project_root = os.path.dirname(os.path.abspath(__file__))
    bundled_python = os.path.join(project_root, "venv311", "Scripts", "python.exe")

    if os.path.exists(bundled_python) and os.path.abspath(sys.executable) != os.path.abspath(bundled_python):
        os.execv(bundled_python, [bundled_python, os.path.abspath(__file__), *sys.argv[1:]])

    raise ModuleNotFoundError(
        "No module named 'torch'. Activate the project venv with venv311\\Scripts\\activate "
        "or install torch into the current Python environment."
    )


_bootstrap_project_python()

from core.utils.ffmpeg_tools import ensure_ffmpeg_on_path

ensure_ffmpeg_on_path()

from core.pipeline.orchestrator import Orchestrator
from core.utils.logger import log
from core.utils.system_check import check_system


def _configure_stdio() -> None:
    if os.name == "nt":
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass
        try:
            sys.stderr.reconfigure(encoding="utf-8", errors="replace")
        except Exception:
            pass


def parse_args():
    parser = argparse.ArgumentParser(
        description="Offline AI Avatar Video Generator",
        formatter_class=argparse.RawTextHelpFormatter
    )

    # Required
    parser.add_argument("--script",  required=True, help="Path to script .txt file")
    parser.add_argument("--avatar",  required=True, help="Path to avatar image (jpg/png)")
    parser.add_argument("--output",  required=True, help="Output video path (.mp4)")

    # Optional inputs
    parser.add_argument("--voice",   default=None,  help="Voice sample for cloning (3-10s wav)")
    parser.add_argument("--screen",  default=None,  help="Screen recording for PiP overlay (.mp4)")

    # Quality / mode
    parser.add_argument("--mode",    default="balanced",
                        choices=["fast", "balanced", "quality"],
                        help="fast=Wav2Lip+Piper | balanced=SadTalker+XTTS | quality=SadTalker+XTTS+refinement")
    parser.add_argument("--talking-head", default="auto",
                        choices=["auto", "sadtalker", "wav2lip"],
                        help="Override talking-head model selection")
    parser.add_argument("--resolution", default="1080p", choices=["720p", "1080p", "4k"])
    parser.add_argument("--fps",     default=25, type=int)

    # Motion options
    parser.add_argument("--motion", default="static", choices=["static", "dynamic"],
                        help="static=reduced head movement | dynamic=natural head movement (SadTalker only)")
    parser.add_argument("--pose-style", default=0, type=int,
                        help="Pose style for dynamic motion (0-45). Modifies head movement pattern (SadTalker only).")

    # Subtitle options
    parser.add_argument("--subtitles",  action="store_true", default=True)
    parser.add_argument("--no-subtitles", dest="subtitles", action="store_false")
    parser.add_argument("--sub-style", default="modern",
                        choices=["modern", "corporate", "minimal", "karaoke"])
    parser.add_argument("--burn-subs", action="store_true", default=True)

    # Screen overlay
    parser.add_argument("--pip-layout", default="bottom_right",
                        choices=["bottom_right", "bottom_left", "side_by_side", "top_right"])

    # TTS
    parser.add_argument("--tts-engine", default=None,
                        choices=["piper", "xtts"],
                        help="Override TTS engine (auto-selected based on mode if not set)")

    # GPU
    parser.add_argument("--device", default="auto", choices=["auto", "cuda", "cpu"])
    parser.add_argument("--vram",   default=None, type=float,
                        help="Override VRAM GB (auto-detected if not set)")

    # Misc
    parser.add_argument("--resume",  action="store_true", help="Resume interrupted render")
    parser.add_argument("--preview", action="store_true", help="Generate 30s preview only")
    parser.add_argument("--skip-models-check", action="store_true")

    return parser.parse_args()


def main():
    _configure_stdio()
    args = parse_args()

    print("\n" + "=" * 55)
    print("  Offline AI Avatar Video Generator")
    print("=" * 55)

    # Validate inputs
    for path, label in [(args.script, "Script"), (args.avatar, "Avatar")]:
        if not os.path.exists(path):
            log.error(f"{label} file not found: {path}")
            sys.exit(1)

    if args.voice and not os.path.exists(args.voice):
        log.warning(f"Voice sample not found: {args.voice} — skipping voice cloning")
        args.voice = None

    if args.screen and not os.path.exists(args.screen):
        log.warning(f"Screen recording not found: {args.screen} — skipping PiP")
        args.screen = None

    # System check
    if not args.skip_models_check:
        check_system()

    # Build config
    config = {
        "script":       args.script,
        "avatar":       args.avatar,
        "output":       args.output,
        "voice":        args.voice,
        "screen":       args.screen,
        "mode":         args.mode,
        "talking_head": args.talking_head,
        "resolution":   args.resolution,
        "fps":          args.fps,
        "motion":       args.motion,
        "pose_style":   args.pose_style,
        "subtitles":    args.subtitles,
        "sub_style":    args.sub_style,
        "burn_subs":    args.burn_subs,
        "pip_layout":   args.pip_layout,
        "tts_engine":   args.tts_engine,
        "device":       args.device,
        "vram":         args.vram,
        "resume":       args.resume,
        "preview":      args.preview,
    }

    # Run pipeline
    start = time.time()
    orchestrator = Orchestrator(config)
    success = orchestrator.run()

    elapsed = time.time() - start
    mins = int(elapsed // 60)
    secs = int(elapsed % 60)

    print("\n" + "=" * 55)
    if success:
        print(f"  ✅  Done in {mins}m {secs}s")
        print(f"  📁  Output: {args.output}")
        if args.subtitles:
            srt = args.output.replace(".mp4", ".srt")
            if os.path.exists(srt):
                print(f"  📝  Subtitles: {srt}")
    else:
        print(f"  ❌  Generation failed after {mins}m {secs}s")
        print("  Check logs/pipeline.log for details")
    print("=" * 55 + "\n")

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
