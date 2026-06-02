from __future__ import annotations

import os
import queue
import subprocess
import threading
import uuid
from dataclasses import dataclass
from pathlib import Path

from flask import Flask, jsonify, render_template, request, send_from_directory, url_for
from werkzeug.utils import secure_filename
from dotenv import load_dotenv

load_dotenv()


BASE_DIR = Path(__file__).resolve().parents[1]
UPLOAD_ROOT = BASE_DIR / "web_uploads"
JOB_ROOT = UPLOAD_ROOT / "jobs"
OUTPUT_ROOT = BASE_DIR / "web_outputs"
GENERATE_PY = BASE_DIR / "generate.py"
PYTHON_EXE = BASE_DIR / "venv311" / "Scripts" / "python.exe"

ALLOWED_AVATAR_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
ALLOWED_SCRIPT_EXTENSIONS = {".txt"}
ALLOWED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".m4a", ".flac", ".ogg"}
ALLOWED_VIDEO_EXTENSIONS = {".mp4", ".mov", ".avi", ".mkv"}

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 250 * 1024 * 1024


@dataclass
class JobState:
    job_id: str
    status: str = "queued"
    message: str = "Queued"
    mode: str = "fast"
    talking_head: str = "sadtalker"
    tts_engine: str = "piper"
    piper_voice: str = "en_US_male"
    motion: str = "static"
    pose_style: int = 0
    pip_layout: str = "bottom_right"
    smart_sync: bool = False
    openai_api_key: str = ""
    script_path: Path | None = None
    avatar_path: Path | None = None
    voice_path: Path | None = None
    screen_path: Path | None = None
    output_path: Path | None = None
    stderr: str = ""
    logs: list[str] = None


jobs: dict[str, JobState] = {}
job_queue: queue.Queue[str] = queue.Queue()
worker_started = False
jobs_lock = threading.Lock()


def ensure_directories() -> None:
    UPLOAD_ROOT.mkdir(parents=True, exist_ok=True)
    JOB_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_ROOT.mkdir(parents=True, exist_ok=True)


def is_allowed(filename: str, extensions: set[str]) -> bool:
    return Path(filename.lower()).suffix in extensions


def append_log(job: JobState, line: str) -> None:
    with jobs_lock:
        if job.logs is None:
            job.logs = []
        job.logs.append(line.rstrip("\n"))
        if len(job.logs) > 500:
            job.logs = job.logs[-500:]


def start_worker() -> None:
    global worker_started
    if worker_started:
        return

    def worker() -> None:
        while True:
            job_id = job_queue.get()
            job = jobs.get(job_id)
            if job is None:
                job_queue.task_done()
                continue

            try:
                job.status = "running"
                job.message = "Running generator"
                append_log(job, "[web] Starting pipeline")

                output_path = OUTPUT_ROOT / f"{job_id}.mp4"
                command = [
                    str(PYTHON_EXE),
                    "-u",
                    str(GENERATE_PY),
                    "--script", str(job.script_path),
                    "--avatar", str(job.avatar_path),
                    "--output", str(output_path),
                    "--mode", job.mode,
                    "--talking-head", job.talking_head,
                    "--motion", job.motion,
                    "--pose-style", str(job.pose_style),
                    "--device", "cuda",
                    "--skip-models-check",
                ]

                if job.tts_engine:
                    command.extend(["--tts-engine", job.tts_engine])
                if job.piper_voice:
                    command.extend(["--piper-voice", job.piper_voice])
                if job.voice_path:
                    command.extend(["--voice", str(job.voice_path)])
                if job.screen_path:
                    command.extend(["--screen", str(job.screen_path), "--pip-layout", job.pip_layout])
                    if job.smart_sync:
                        command.append("--smart-sync")
                        if job.openai_api_key:
                            command.extend(["--openai-api-key", job.openai_api_key])

                child_env = {
                    **os.environ,
                    "PYTHONUTF8": "1",
                    "PYTHONIOENCODING": "utf-8",
                    "PYTHONUNBUFFERED": "1",
                }

                process = subprocess.Popen(
                    command,
                    cwd=str(BASE_DIR),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    bufsize=1,
                    env=child_env,
                )

                assert process.stdout is not None
                for line in process.stdout:
                    append_log(job, line)

                return_code = process.wait()
                if return_code != 0:
                    raise subprocess.CalledProcessError(return_code, command)

                job.status = "done"
                job.message = "Finished"
                job.output_path = output_path
                append_log(job, "[web] Pipeline complete")
            except subprocess.CalledProcessError as exc:
                job.status = "error"
                job.message = "Generation failed"
                job.stderr = str(exc)
                append_log(job, f"[web] ERROR: {exc}")
            except Exception as exc:  # pragma: no cover - defensive
                job.status = "error"
                job.message = "Unexpected error"
                job.stderr = str(exc)
                append_log(job, f"[web] ERROR: {exc}")
            finally:
                job_queue.task_done()

    threading.Thread(target=worker, daemon=True).start()
    worker_started = True


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/submit", methods=["POST"])
def submit():
    ensure_directories()

    avatar_file = request.files.get("avatar_file")
    script_file = request.files.get("script_file")
    voice_file = request.files.get("voice_file")
    screen_file = request.files.get("screen_file")
    script_text = (request.form.get("script_text") or "").strip()
    mode = request.form.get("mode", "fast")
    talking_head = request.form.get("talking_head", "sadtalker")
    tts_engine = request.form.get("tts_engine", "piper")
    piper_voice = request.form.get("piper_voice", "en_US_male")
    motion = request.form.get("motion", "static")
    pip_layout = request.form.get("pip_layout", "bottom_right")
    smart_sync = request.form.get("smart_sync") == "true"
    openai_api_key = request.form.get("openai_api_key") or os.environ.get("OPENAI_API_KEY", "")
    try:
        pose_style = int(request.form.get("pose_style", "0"))
    except ValueError:
        pose_style = 0

    if not avatar_file or not avatar_file.filename:
        return jsonify({"error": "Avatar image is required."}), 400
    if not script_text and (not script_file or not script_file.filename):
        return jsonify({"error": "Provide script text or upload a .txt file."}), 400
    if talking_head not in {"sadtalker", "wav2lip"}:
        return jsonify({"error": "Invalid talking head selection."}), 400
    if piper_voice not in {"en_US_female", "en_US_male"}:
        return jsonify({"error": "Invalid Piper voice selection."}), 400

    avatar_name = secure_filename(avatar_file.filename)
    if not is_allowed(avatar_name, ALLOWED_AVATAR_EXTENSIONS):
        return jsonify({"error": "Avatar must be a jpg, jpeg, png, or webp file."}), 400
    if script_file and script_file.filename and not is_allowed(script_file.filename, ALLOWED_SCRIPT_EXTENSIONS):
        return jsonify({"error": "Script upload must be a .txt file."}), 400
    if voice_file and voice_file.filename and not is_allowed(voice_file.filename, ALLOWED_AUDIO_EXTENSIONS):
        return jsonify({"error": "Voice sample must be a wav, mp3, m4a, flac, or ogg file."}), 400
    if screen_file and screen_file.filename and not is_allowed(screen_file.filename, ALLOWED_VIDEO_EXTENSIONS):
        return jsonify({"error": "Screen recording must be a video file (mp4, mov, etc.)."}), 400

    job_id = uuid.uuid4().hex[:12]
    job_dir = JOB_ROOT / job_id
    job_dir.mkdir(parents=True, exist_ok=True)

    if script_file and script_file.filename:
        script_path = job_dir / "script.txt"
        script_file.save(script_path)
    else:
        script_path = job_dir / "script.txt"
        script_path.write_text(script_text, encoding="utf-8")

    avatar_path = job_dir / f"avatar{Path(avatar_name).suffix.lower()}"
    avatar_file.save(avatar_path)

    voice_path = None
    if voice_file and voice_file.filename:
        voice_path = job_dir / f"voice{Path(secure_filename(voice_file.filename)).suffix.lower()}"
        voice_file.save(voice_path)

    screen_path = None
    if screen_file and screen_file.filename:
        screen_path = job_dir / f"screen{Path(secure_filename(screen_file.filename)).suffix.lower()}"
        screen_file.save(screen_path)

    job = JobState(
        job_id=job_id,
        mode=mode,
        talking_head=talking_head,
        tts_engine=tts_engine,
        piper_voice=piper_voice,
        motion=motion,
        pose_style=pose_style,
        pip_layout=pip_layout,
        smart_sync=smart_sync,
        openai_api_key=openai_api_key,
        script_path=script_path,
        avatar_path=avatar_path,
        voice_path=voice_path,
        screen_path=screen_path,
    )
    jobs[job_id] = job
    job_queue.put(job_id)

    return jsonify({
        "job_id": job_id,
        "status_url": url_for("job_status", job_id=job_id),
        "result_url": url_for("job_result", job_id=job_id),
    })


@app.route("/jobs/<job_id>")
def job_status(job_id: str):
    job = jobs.get(job_id)
    if job is None:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({
        "job_id": job.job_id,
        "status": job.status,
        "message": job.message,
        "result_url": url_for("job_result", job_id=job.job_id) if job.output_path else None,
        "stderr": job.stderr,
        "logs": job.logs or [],
    })


@app.route("/jobs/<job_id>/result")
def job_result(job_id: str):
    output_path = OUTPUT_ROOT / f"{job_id}.mp4"
    if not output_path.exists():
        return jsonify({"error": "Result not ready"}), 404
    return send_from_directory(str(OUTPUT_ROOT), output_path.name, as_attachment=True)


def create_app() -> Flask:
    ensure_directories()
    start_worker()
    return app


if __name__ == "__main__":
    create_app().run(host="127.0.0.1", port=5000, debug=True)