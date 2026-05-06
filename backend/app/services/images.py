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


def _encode_jpeg(img: Image.Image, max_bytes: int, start_quality: int = 90) -> bytes:
    """Encode JPEG, stepping quality down until ≤ max_bytes.

    Order of operations: try start_quality first, drop by 5 until we hit a
    floor of 40, then downscale 5% and reset. `progressive=True` shaves a
    few % at no quality cost. `optimize=True` enables Pillow's Huffman
    optimisation pass (slow-ish but worth it for smaller payloads).
    """
    quality = start_quality
    while True:
        buf = io.BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        data = buf.getvalue()
        if len(data) <= max_bytes:
            return data
        if quality > 40:
            quality -= 5
            continue
        # At quality floor — downscale 5% and retry from start_quality
        w, h = img.size
        if w < 100 or h < 100:
            # Refuse to spiral down to nothing — return whatever we have.
            return data
        img = img.resize((int(w * 0.95), int(h * 0.95)), Image.LANCZOS)
        quality = start_quality


def process_upload(
    file_bytes: bytes,
    filename: str,
    is_primary: bool = False,
) -> tuple[bytes, bytes, bytes]:
    """Process uploaded photo into passport / blurred / thumb variants.

    All three variants are JPEG-encoded with iterative quality stepping so
    each lands within its own size cap. Errors include the actual measured
    value and the limit that was hit so the user can act on the message.

    Args:
        file_bytes: raw upload bytes
        filename: original filename (used for error messages)
        is_primary: True when this upload becomes the profile's primary
            photo. Face detection — when enabled in settings — is enforced
            ONLY for primary photos. Non-primary photos can be lifestyle
            or full-body shots.

    Returns (passport_bytes, blurred_bytes, thumb_bytes).
    Raises PhotoValidationError on rejection.
    """
    # Settings — all knobs in one place ------------------------------------
    upload_max_mb = settings_service.get_int("upload_max_mb", 10)
    upload_min_kb = settings_service.get_int("upload_min_kb", 5)
    photo_min_dim_px = settings_service.get_int("photo_min_dimension_px", 400)
    photo_max_dim_px = settings_service.get_int("photo_max_dimension_px", 4000)
    require_face = is_primary and settings_service.get_bool("require_face_detection", False)
    passport_w = settings_service.get_int("photo_passport_width", 413)
    passport_h = settings_service.get_int("photo_passport_height", 531)
    photo_max_kb = settings_service.get_int("photo_max_kb", 350)
    photo_min_kb = settings_service.get_int("photo_min_kb", 10)
    blur_width = settings_service.get_int("photo_blur_width", 600)
    blur_radius = settings_service.get_int("photo_blur_radius", 14)
    blur_max_kb = settings_service.get_int("photo_blur_max_kb", 120)
    thumb_size = settings_service.get_int("photo_thumb_size", 150)
    thumb_max_kb = settings_service.get_int("photo_thumb_max_kb", 25)

    raw_kb = len(file_bytes) / 1024

    # 1. Raw size guards (cheap, fail fast) ---------------------------------
    if len(file_bytes) > upload_max_mb * 1024 * 1024:
        raise PhotoValidationError(
            f"File '{filename}' is {raw_kb / 1024:.1f} MB — maximum allowed is {upload_max_mb} MB. "
            f"Please choose a smaller file or compress it before uploading."
        )
    if len(file_bytes) < upload_min_kb * 1024:
        raise PhotoValidationError(
            f"File '{filename}' is only {raw_kb:.1f} KB — minimum allowed is {upload_min_kb} KB. "
            f"This looks like a thumbnail or icon; please upload a proper photo."
        )

    # 2. Decode --------------------------------------------------------------
    try:
        img = Image.open(io.BytesIO(file_bytes))
    except Exception:
        raise PhotoValidationError(
            f"Cannot read '{filename}'. Make sure it's a valid image file (JPEG, PNG, or WebP)."
        )

    if img.format not in ALLOWED_FORMATS:
        raise PhotoValidationError(
            f"Format '{img.format}' is not supported (allowed: {', '.join(sorted(ALLOWED_FORMATS))}). "
            f"Please re-save '{filename}' as JPEG, PNG, or WebP and try again."
        )

    img = _exif_orient(img)
    img = img.convert("RGB")
    iw, ih = img.size

    # 3. Source dimension guards --------------------------------------------
    short_side = min(iw, ih)
    if short_side < photo_min_dim_px:
        raise PhotoValidationError(
            f"Photo is too small ({iw}×{ih} px) — the shortest side must be at least "
            f"{photo_min_dim_px} px. Please upload a higher-resolution photo."
        )

    # 4. CPU/memory saver: pre-downscale enormous images BEFORE doing further
    #    work. Iterative JPEG encoding on a 12000×9000 image is wasteful when
    #    the largest variant we keep is 800px wide.
    long_side = max(iw, ih)
    if long_side > photo_max_dim_px:
        scale = photo_max_dim_px / long_side
        img = img.resize((int(iw * scale), int(ih * scale)), Image.LANCZOS)
        iw, ih = img.size

    image_area = iw * ih

    # 5. Optional face check (off by default in current settings) -----------
    cx, cy = iw // 2, ih // 2
    if require_face:
        face = _detect_face(img)
        if face is None:
            raise PhotoValidationError(
                "Could not detect exactly one clear face in this photo. "
                "Please upload a single forward-facing portrait, well-lit, with no other people."
            )
        fx, fy, fw, fh = face
        if (fw * fh) < 0.08 * image_area:
            raise PhotoValidationError(
                f"The detected face occupies only {(fw * fh) / image_area * 100:.0f}% of the frame. "
                f"Please upload a closer portrait — at least 8% of the image should be face."
            )
        cx, cy = fx + fw // 2, fy + fh // 2

    # 6. Passport variant: smart-crop to portrait aspect, encode under cap --
    passport_img = _smart_crop(img, passport_w, passport_h, cx, cy)
    passport_img = passport_img.resize((passport_w, passport_h), Image.LANCZOS)
    passport_bytes = _encode_jpeg(passport_img, photo_max_kb * 1024)
    if len(passport_bytes) < photo_min_kb * 1024:
        raise PhotoValidationError(
            f"After processing, the photo compressed to {len(passport_bytes) / 1024:.1f} KB — "
            f"below the {photo_min_kb} KB quality floor. The source is too low-detail or too "
            f"flat (e.g. screenshot, AI-generated). Please upload a real high-resolution photo."
        )

    # 7. Blurred variant: scale to blur_width, Gaussian blur, encode under cap
    blur_h = int(img.height * (blur_width / img.width))
    blurred_img = img.resize((blur_width, blur_h), Image.LANCZOS)
    blurred_img = blurred_img.filter(ImageFilter.GaussianBlur(radius=blur_radius))
    blurred_bytes = _encode_jpeg(blurred_img, blur_max_kb * 1024, start_quality=80)

    # 8. Thumb variant: square crop to thumb_size, encode under cap ---------
    short = min(iw, ih)
    tx = (iw - short) // 2
    ty = (ih - short) // 2
    thumb_img = img.crop((tx, ty, tx + short, ty + short))
    thumb_img = thumb_img.resize((thumb_size, thumb_size), Image.LANCZOS)
    thumb_bytes = _encode_jpeg(thumb_img, thumb_max_kb * 1024, start_quality=80)

    return passport_bytes, blurred_bytes, thumb_bytes
