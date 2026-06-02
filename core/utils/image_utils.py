"""Image utilities — avatar preparation for different models."""

import os
from PIL import Image
from core.utils.logger import log

RESOLUTION_DIMS = {
    "720p":  (1280, 720),
    "1080p": (1920, 1080),
    "4k":    (3840, 2160),
}


def prepare_avatar_image(image_path: str, resolution: str = "1080p",
                         bg_color: tuple = (30, 30, 30)) -> str:
    """
    Resize avatar image to a safe working size (max 768px).
    Does NOT pad to full resolution, as FFmpeg handles padding later.
    This saves massive amounts of RAM and VRAM during AI generation.
    Returns path to prepared image (saved to temp/).
    """
    output_path = "temp/avatar_prepared.jpg"
    os.makedirs("temp", exist_ok=True)

    try:
        img = Image.open(image_path).convert("RGB")
        
        # Max dimension for working safely without OOM
        max_dim = 768
        if img.width > max_dim or img.height > max_dim:
            img.thumbnail((max_dim, max_dim), Image.LANCZOS)
            
        # Ensure dimensions are even (required by most video codecs/models)
        new_w = img.width if img.width % 2 == 0 else img.width - 1
        new_h = img.height if img.height % 2 == 0 else img.height - 1
        
        if new_w != img.width or new_h != img.height:
            img = img.resize((new_w, new_h), Image.LANCZOS)
            
        img.save(output_path, "JPEG", quality=95)
        log.info(f"  Avatar prepared: {img.width}x{img.height} (No padding)")
        return output_path
    except Exception as e:
        log.error(f"  Avatar preparation failed: {e}")
        return image_path  # Return original as fallback


def crop_face_region(image_path: str, padding: float = 0.3) -> str:
    """Crop to face region with padding — useful for portrait optimization."""
    try:
        import cv2
        import numpy as np

        img = cv2.imread(image_path)
        face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        )
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))

        if len(faces) == 0:
            log.warning("  No face detected for cropping — using full image")
            return image_path

        x, y, w, h = faces[0]
        pad_x = int(w * padding)
        pad_y = int(h * padding)
        x1 = max(0, x - pad_x)
        y1 = max(0, y - pad_y * 2)  # More padding above for hair
        x2 = min(img.shape[1], x + w + pad_x)
        y2 = min(img.shape[0], y + h + pad_y)

        cropped = img[y1:y2, x1:x2]
        out_path = "temp/avatar_face_crop.jpg"
        cv2.imwrite(out_path, cropped)
        log.info(f"  Face cropped: {x2-x1}x{y2-y1}")
        return out_path

    except Exception as e:
        log.warning(f"  Face crop failed: {e}")
        return image_path
