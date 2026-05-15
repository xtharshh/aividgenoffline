"""
Pipeline Orchestrator — coordinates all stages, manages GPU, handles resume.
"""

import os
import json
import time
import torch
from pathlib import Path

from core.utils.logger import log
from core.utils.gpu import GPUManager
from core.pipeline.project_state import ProjectState
from core.pipeline.chunk_manager import ChunkManager


class Orchestrator:
    def __init__(self, config: dict):
        self.config = config
        self.temp_dir = "temp"
        self.output_dir = os.path.dirname(config["output"]) or "output"
        os.makedirs(self.temp_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)
        os.makedirs("logs", exist_ok=True)

        # Detect device + VRAM
        self.device = self._detect_device()
        self.vram_gb = self._detect_vram()
        self.gpu = GPUManager(self.vram_gb)

        # Select models based on mode + VRAM
        self.pipeline_config = self._select_pipeline()

        # Project state for resume support
        project_id = Path(config["output"]).stem
        self.state = ProjectState(f"projects/{project_id}.db")

        log.info(f"Device     : {self.device.upper()}")
        log.info(f"VRAM       : {self.vram_gb:.1f} GB")
        log.info(f"Mode       : {config['mode']}")
        log.info(f"TTS engine : {self.pipeline_config['tts']}")
        log.info(f"Avatar model: {self.pipeline_config['talking_head']}")

    def _detect_device(self) -> str:
        if self.config["device"] == "auto":
            return "cuda" if torch.cuda.is_available() else "cpu"
        return self.config["device"]

    def _detect_vram(self) -> float:
        if self.config.get("vram"):
            return self.config["vram"]
        if self.device == "cuda" and torch.cuda.is_available():
            total = torch.cuda.get_device_properties(0).total_memory
            return round(total / 1024**3, 1)
        return 0.0

    def _select_pipeline(self) -> dict:
        mode = self.config["mode"]
        vram = self.vram_gb
        tts_override = self.config.get("tts_engine")
        talking_head_override = self.config.get("talking_head", "auto")

        # TTS selection
        if tts_override:
            tts = tts_override
        elif mode == "fast" or vram < 6:
            tts = "piper"
        else:
            tts = "xtts"

        # Talking head selection
        if talking_head_override in {"sadtalker", "wav2lip"}:
            talking_head = talking_head_override
            use_refinement = talking_head == "sadtalker" and mode == "quality"
        else:
            if mode == "fast" or vram < 4:
                talking_head = "wav2lip"
                use_refinement = False
            elif vram < 8:
                talking_head = "sadtalker"
                use_refinement = False
            elif mode == "quality":
                talking_head = "sadtalker"
                use_refinement = True
            else:
                talking_head = "sadtalker"
                use_refinement = False

        # Whisper size
        if vram >= 10:
            whisper_size = "medium"
        else:
            whisper_size = "small"

        return {
            "tts": tts,
            "talking_head": talking_head,
            "use_refinement": use_refinement,
            "whisper_size": whisper_size,
            "chunk_duration": max(15, min(30, int(vram * 3))),
        }

    def run(self) -> bool:
        try:
            cfg = self.config
            pc  = self.pipeline_config

            # Read script
            with open(cfg["script"], "r", encoding="utf-8") as f:
                script_text = f.read().strip()
            log.info(f"Script: {len(script_text.split())} words")

            # ── Stage 1: TTS ──────────────────────────────────────────
            audio_path = self._stage_tts(script_text)
            if not audio_path:
                return False

            # ── Stage 2: Talking head ─────────────────────────────────
            avatar_video = self._stage_avatar(audio_path)
            if not avatar_video:
                return False

            # ── Stage 3: Subtitles ────────────────────────────────────
            srt_path, ass_path = None, None
            if cfg["subtitles"]:
                srt_path, ass_path = self._stage_subtitles(audio_path)

            # ── Stage 4: Screen overlay ───────────────────────────────
            final_input = avatar_video
            if cfg.get("screen") and os.path.exists(cfg["screen"]):
                final_input = self._stage_screen_overlay(avatar_video)

            # ── Stage 5: Final render ─────────────────────────────────
            success = self._stage_final_render(final_input, audio_path, ass_path)

            # Copy SRT to output dir
            if srt_path and os.path.exists(srt_path):
                out_srt = cfg["output"].replace(".mp4", ".srt")
                import shutil
                shutil.copy(srt_path, out_srt)

            return success

        except KeyboardInterrupt:
            log.warning("Interrupted — progress saved. Run with --resume to continue.")
            return False
        except Exception as e:
            log.error(f"Pipeline error: {e}")
            import traceback
            traceback.print_exc()
            return False

    # ─────────────────────────────────────────────────────────────────
    # Stage 1 — TTS
    # ─────────────────────────────────────────────────────────────────
    def _stage_tts(self, script_text: str) -> str | None:
        audio_path = f"{self.temp_dir}/speech_clean.wav"

        if self.state.is_done("tts") and os.path.exists(audio_path):
            log.info("[1/5] TTS — skipped (cached)")
            return audio_path

        log.info("[1/5] Generating speech audio...")
        print("\n🔊 Stage 1/5 — Text-to-Speech")

        tts_engine = self.pipeline_config["tts"]

        if tts_engine == "xtts":
            from core.stages.tts.xtts_engine import XTTSEngine
            engine = XTTSEngine(self.device)
        else:
            from core.stages.tts.piper_engine import PiperEngine
            engine = PiperEngine()

        raw_audio = f"{self.temp_dir}/speech_raw.wav"
        ok = engine.synthesize(
            text=script_text,
            output_path=raw_audio,
            voice_sample=self.config.get("voice")
        )
        engine.unload()
        self.gpu.clear()

        if not ok:
            log.error("TTS failed")
            return None

        # Post-process
        from core.stages.tts.audio_postprocess import postprocess_audio
        postprocess_audio(raw_audio, audio_path)

        self.state.mark_done("tts")
        log.info(f"  Audio saved: {audio_path}")
        return audio_path

    # ─────────────────────────────────────────────────────────────────
    # Stage 2 — Avatar / talking head
    # ─────────────────────────────────────────────────────────────────
    def _stage_avatar(self, audio_path: str) -> str | None:
        avatar_path = f"{self.temp_dir}/avatar_final.mp4"

        if self.state.is_done("avatar") and os.path.exists(avatar_path):
            log.info("[2/5] Avatar — skipped (cached)")
            return avatar_path

        log.info("[2/5] Generating talking avatar...")
        print("\n🎭 Stage 2/5 — Avatar Generation")

        model_name = self.pipeline_config["talking_head"]

        if model_name == "sadtalker":
            from core.stages.talking_head.sadtalker_runner import SadTalkerRunner
            runner = SadTalkerRunner(self.device)
        else:
            from core.stages.talking_head.wav2lip_runner import Wav2LipRunner
            runner = Wav2LipRunner(self.device)

        raw_avatar = f"{self.temp_dir}/avatar_raw.mp4"
        generate_kwargs = {
            "avatar_image": self.config["avatar"],
            "audio_path": audio_path,
            "output_path": raw_avatar,
            "resolution": self.config["resolution"],
            "fps": self.config["fps"],
        }
        if model_name == "sadtalker":
            generate_kwargs["vram_gb"] = self.vram_gb
            generate_kwargs["still_mode"] = self.config.get("motion", "static") == "static"
            generate_kwargs["pose_style"] = self.config.get("pose_style", 0)

        ok = runner.generate(**generate_kwargs)
        runner.unload()
        self.gpu.clear()

        if not ok:
            log.error("Avatar generation failed")
            return None

        # Optional Wav2Lip refinement pass
        if self.pipeline_config["use_refinement"] and model_name != "wav2lip":
            log.info("  Running Wav2Lip refinement pass...")
            from core.stages.lip_sync.wav2lip_runner import Wav2LipRefiner
            refiner = Wav2LipRefiner(self.device)
            ok2 = refiner.refine(raw_avatar, audio_path, avatar_path)
            refiner.unload()
            self.gpu.clear()
            if not ok2:
                log.warning("Refinement failed, using raw avatar")
                import shutil
                shutil.copy(raw_avatar, avatar_path)
        else:
            import shutil
            shutil.copy(raw_avatar, avatar_path)

        self.state.mark_done("avatar")
        return avatar_path

    # ─────────────────────────────────────────────────────────────────
    # Stage 3 — Subtitles
    # ─────────────────────────────────────────────────────────────────
    def _stage_subtitles(self, audio_path: str) -> tuple[str | None, str | None]:
        srt_path = f"{self.temp_dir}/subtitles.srt"
        ass_path = f"{self.temp_dir}/subtitles.ass"

        if self.state.is_done("subtitles") and os.path.exists(srt_path):
            log.info("[3/5] Subtitles — skipped (cached)")
            return srt_path, ass_path

        log.info("[3/5] Generating subtitles...")
        print("\n📝 Stage 3/5 — Subtitle Generation")

        from core.stages.subtitles.whisper_transcriber import WhisperTranscriber
        transcriber = WhisperTranscriber(
            model_size=self.pipeline_config["whisper_size"],
            device="cuda" if self.vram_gb >= 8 else "cpu"
        )
        ok = transcriber.transcribe(
            audio_path=audio_path,
            srt_path=srt_path,
            ass_path=ass_path,
            style=self.config["sub_style"],
            resolution=self.config["resolution"]
        )
        transcriber.unload()
        self.gpu.clear()

        if not ok:
            log.warning("Subtitle generation failed — continuing without subtitles")
            return None, None

        self.state.mark_done("subtitles")
        return srt_path, ass_path

    # ─────────────────────────────────────────────────────────────────
    # Stage 4 — Screen overlay
    # ─────────────────────────────────────────────────────────────────
    def _stage_screen_overlay(self, avatar_video: str) -> str:
        composite_path = f"{self.temp_dir}/composite.mp4"

        if self.state.is_done("screen_overlay") and os.path.exists(composite_path):
            log.info("[4/5] Screen overlay — skipped (cached)")
            return composite_path

        log.info("[4/5] Creating screen overlay...")
        print("\n🖥️  Stage 4/5 — Screen Overlay (PiP)")

        from core.stages.screen_overlay.pip_compositor import PiPCompositor
        comp = PiPCompositor()
        ok = comp.composite(
            screen_video=self.config["screen"],
            avatar_video=avatar_video,
            output_path=composite_path,
            layout=self.config["pip_layout"],
            resolution=self.config["resolution"]
        )

        if not ok:
            log.warning("PiP composite failed — using avatar only")
            return avatar_video

        self.state.mark_done("screen_overlay")
        return composite_path

    # ─────────────────────────────────────────────────────────────────
    # Stage 5 — Final render
    # ─────────────────────────────────────────────────────────────────
    def _stage_final_render(self, video_path: str, audio_path: str, ass_path: str | None) -> bool:
        log.info("[5/5] Final render...")
        print("\n🎬 Stage 5/5 — Final Render")

        from core.stages.compositor.ffmpeg_render import FFmpegRenderer
        renderer = FFmpegRenderer()
        ok = renderer.render(
            video_path=video_path,
            audio_path=audio_path,
            output_path=self.config["output"],
            ass_path=ass_path if self.config.get("burn_subs") else None,
            resolution=self.config["resolution"],
            fps=self.config["fps"]
        )

        if ok:
            self.state.mark_done("final_render")
        return ok
