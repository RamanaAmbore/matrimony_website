"""Photo processing pipeline using Pillow + OpenCV."""
from __future__ import annotations

import io
import logging
from pathlib import Path

import cv2
import numpy as np
from PIL import ExifTags, Image, ImageFilter

from app.services.settings import settings_service

logger = logging.getLogger(__name__)

ALLOWED_FORMATS = {"JPEG", "PNG", "WEBP"}

# Path to OpenCV's bundled Haar cascade
_CASCADE_PATH = str(
    Path(cv2.__file__).parent / "data" / "haarcascade_frontalface_default.xml"
)
_face_cascade: cv2.CascadeClassifier | None = None


def _get_cascade() -> cv2.CascadeClassifier:
    global _face_cascade
    if _face_cascade is None:
        _face_cascade = cv2.CascadeClassifier(_CASCADE_PATH)
        if _face_cascade.empty():
            raise RuntimeError(f"Failed to load Haar cascade from {_CASCADE_PATH}")
    return _face_cascade


class PhotoValidationError(Exception):
    """User-facing error during photo validation/processing."""
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.user_message = message


def _exif_orient(img: Image.Image) -> Image.Image:
    """Apply EXIF orientation so image is always right-side up."""
    try:
        exif = img.getexif()
        if exif is None:
            return img
        orientation_key = next(
            (k for k, v in ExifTags.TAGS.items() if v == "Orientation"), None
        )
        if orientation_key is None:
            return img
        orientation = exif.get(orientation_key)
        rotations = {3: 180, 6: 270, 8: 90}
        if orientation in rotations:
            img = img.rotate(rotations[orientation], expand=True)
    except Exception:
        pass
    return img


def _detect_face(img: Image.Image) -> tuple[int, int, int, int] | None:
    """Return (x, y, w, h) of the single detected face, or None."""
    cascade = _get_cascade()
    arr = np.array(img.convert("L"))  # grayscale numpy
    faces = cascade.detectMultiScale(
        arr,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30),
    )
    if len(faces) == 0:
        return None
    if len(faces) > 1:
        return None  # multiple faces → reject
    x, y, w, h = faces[0]
    return int(x), int(y), int(w), int(h)


def _smart_crop(
    img: Image.Image,
    target_w: int,
    target_h: int,
    cx: int,
    cy: int,
) -> Image.Image:
    """Crop to target aspect ratio centred on (cx, cy)."""
    iw, ih = img.size
    target_ratio = target_w / target_h

    if iw / ih > target_ratio:
        # image wider than target: crop width
        new_w = int(ih * target_ratio)
        new_h = ih
    else:
        # image taller than target: crop height
        new_w = iw
        new_h = int(iw / target_ratio)

    left = max(0, min(cx - new_w // 2, iw - new_w))
    top = max(0, min(cy - new_h // 2, ih - new_h))
    return img.crop((left, top, left + new_w, top + new_h))


def _encode_jpeg(img: Image.Image, max_bytes: int) -> bytes:
    """Encode JPEG, stepping quality down until ≤ max_bytes."""
    quality = 90
    while True:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        data = buf.getvalue()
        if len(data) <= max_bytes or quality <= 40:
            if len(data) <= max_bytes:
                return data
            # Still too large — downscale 5% and retry from quality=90
            w, h = img.size
            img = img.resize((int(w * 0.95), int(h * 0.95)), Image.LANCZOS)
            quality = 90
            continue
        quality -= 5


def process_upload(
    file_bytes: bytes,
    filename: str,
) -> tuple[bytes, bytes, bytes]:
    """Process uploaded photo.

    Returns (passport_bytes, blurred_bytes, thumb_bytes).
    Raises PhotoValidationError on rejection.
    """
    upload_max_mb = settings_service.get_int("upload_max_mb", 10)
    if len(file_bytes) > upload_max_mb * 1024 * 1024:
        raise PhotoValidationError(
            f"File too large. Maximum size is {upload_max_mb} MB."
        )

    try:
        img = Image.open(io.BytesIO(file_bytes))
    except Exception:
        raise PhotoValidationError("Cannot read image file. Please upload a JPEG, PNG, or WebP.")

    if img.format not in ALLOWED_FORMATS:
        raise PhotoValidationError(
            f"Unsupported format '{img.format}'. Please upload JPEG, PNG, or WebP."
        )

    # EXIF orient
    img = _exif_orient(img)
    img = img.convert("RGB")

    iw, ih = img.size
    image_area = iw * ih

    require_face = settings_service.get_bool("require_face_detection", True)
    passport_w = settings_service.get_int("photo_passport_width", 413)
    passport_h = settings_service.get_int("photo_passport_height", 531)
    photo_max_kb = settings_service.get_int("photo_max_kb", 500)
    photo_min_kb = settings_service.get_int("photo_min_kb", 100)
    blur_width = settings_service.get_int("photo_blur_width", 600)
    blur_radius = settings_service.get_int("photo_blur_radius", 14)
    thumb_size = settings_service.get_int("photo_thumb_size", 150)

    cx, cy = iw // 2, ih // 2

    if require_face:
        face = _detect_face(img)
        if face is None:
            raise PhotoValidationError(
                "We could not detect exactly one clear face in the photo. "
                "Please upload a photo with a single, forward-facing portrait."
            )
        fx, fy, fw, fh = face
        face_area = fw * fh
        if face_area < 0.08 * image_area:
            raise PhotoValidationError(
                "The face in the photo is too small. Please upload a closer portrait photo."
            )
        cx = fx + fw // 2
        cy = fy + fh // 2

    # --- Passport variant ---
    passport_img = _smart_crop(img, passport_w, passport_h, cx, cy)
    passport_img = passport_img.resize((passport_w, passport_h), Image.LANCZOS)
    passport_bytes = _encode_jpeg(passport_img, photo_max_kb * 1024)
    if len(passport_bytes) < photo_min_kb * 1024:
        raise PhotoValidationError(
            f"Photo is too low quality after processing ({len(passport_bytes) // 1024} KB; "
            f"minimum {photo_min_kb} KB). Please upload a higher-resolution photo."
        )

    # --- Blurred variant ---
    blur_ratio = blur_width / img.width
    blur_h = int(img.height * blur_ratio)
    blurred_img = img.resize((blur_width, blur_h), Image.LANCZOS)
    blurred_img = blurred_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    buf = io.BytesIO()
    blurred_img.save(buf, format="JPEG", quality=70)
    blurred_bytes = buf.getvalue()

    # --- Thumb variant ---
    side = thumb_size
    tw, th = img.size
    short = min(tw, th)
    tx = (tw - short) // 2
    ty = (th - short) // 2
    thumb_img = img.crop((tx, ty, tx + short, ty + short))
    thumb_img = thumb_img.resize((side, side), Image.LANCZOS)
    buf = io.BytesIO()
    thumb_img.save(buf, format="JPEG", quality=75)
    thumb_bytes = buf.getvalue()

    return passport_bytes, blurred_bytes, thumb_bytes
