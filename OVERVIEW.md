# Avatar System — Overview

This repository contains tools and models to generate talking-head avatars from scripts and audio.

## Purpose
- End-to-end avatar generation pipeline (TTS → lip-sync → talking-head → compositing).

## Quick start
- Create and activate the virtualenv: `venv311\Scripts\Activate.ps1` (Windows).
- Install dependencies: `pip install -r requirements.txt`.
- Run a simple demo: `python generate.py` (reads script and SRT inputs).

## Key files
- `generate.py`: top-level runner that orchestrates generation.
- `requirements.txt`: Python dependencies.
- `README.md`: project notes and examples.

## Important folders
- `core/`: main pipeline code and stage implementations.
  - `pipeline/`: orchestrator, chunk manager, project state.
  - `stages/`: modular stages (tts, talking_head, lip_sync, subtitles, compositor, screen_overlay).
  - `utils/`: helper utilities (ffmpeg wrappers, GPU helpers, image utilities, logger).
- `models/`: pre-downloaded or pre-trained models (e.g., `piper` TTS models).
- `gfpgan/weights/`: face restoration checkpoints used by some pipelines.
- `projects/`: third-party project integrations (SadTalker, Wav2Lip) and their helpers.
- `scripts/`: helper scripts like `download_models.py` and installers.
- `web/`: minimal web UI (`app.py`, `templates`, `static`) for uploads/preview.
- `output/`: generated artifacts (SRTs, images, videos).
- `temp/`: transient files and ffmpeg binaries used during processing.

## Where to look for functionality
- Text-to-speech: `core/stages/tts/` and `models/piper/`.
- Lip sync + audio-video sync: `core/stages/lip_sync/` and `projects/Wav2Lip/`.
- Talking-head generation: `core/stages/talking_head/` and `projects/SadTalker/`.
- Compositing and overlays: `core/stages/compositor/` and `core/stages/screen_overlay/`.

## Notes & next steps
- Use `scripts/download_models.py` to fetch required model weights before running.
- If you want, I can expand any section with file-level links or run examples.
