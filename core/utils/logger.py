"""Centralized logger for the avatar video pipeline."""

import io
import logging
import os
import sys

os.makedirs("logs", exist_ok=True)


def _build_stdout_stream():
    if hasattr(sys.stdout, "buffer"):
        return io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace", line_buffering=True)
    return sys.stdout


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
    handlers=[
        logging.StreamHandler(_build_stdout_stream()),
        logging.FileHandler("logs/pipeline.log", mode="a", encoding="utf-8")
    ]
)

log = logging.getLogger("avatar")
