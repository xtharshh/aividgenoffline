"""GPU manager — VRAM monitoring and cleanup."""

import torch
from core.utils.logger import log


class GPUManager:
    def __init__(self, vram_gb: float):
        self.vram_gb = vram_gb

    def clear(self):
        """Free VRAM between stages."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.synchronize()

    def available_vram_gb(self) -> float:
        if not torch.cuda.is_available():
            return 0.0
        free = torch.cuda.mem_get_info()[0]
        return free / 1024**3

    def used_vram_gb(self) -> float:
        if not torch.cuda.is_available():
            return 0.0
        return (torch.cuda.memory_allocated() / 1024**3)

    def log_vram(self, label: str = ""):
        if torch.cuda.is_available():
            used = self.used_vram_gb()
            avail = self.available_vram_gb()
            log.debug(f"  VRAM {label}: {used:.1f} GB used, {avail:.1f} GB free")
