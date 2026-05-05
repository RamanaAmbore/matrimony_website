"""Media file serving route with access control."""

import mimetypes
import uuid
from pathlib import Path
from typing import Any

from litestar import get
from litestar.connection import Request
from litestar.exceptions import HTTPException
from litestar.response import Response

from app.config import MEDIA_ROOT


@get("/media/{file_path:path}", media_type="application/octet-stream")
async def serve_media(file_path: str, request: Request) -> Response:
    """Serve media files. Passport photos require auth as owner or admin."""
    # Normalize path to prevent directory traversal
    try:
        resolved = (MEDIA_ROOT / file_path).resolve()
        resolved.relative_to(MEDIA_ROOT.resolve())
    except ValueError:
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Not found"})

    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(status_code=404, detail={"code": "not_found", "message": "File not found"})

    # Access control: passport.jpg is private
    if resolved.name == "passport.jpg":
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Not found"})

        is_admin = user.get("is_admin", False)
        if not is_admin:
            # Check ownership: path = profiles/<profile_id>/<photo_id>/passport.jpg
            parts = Path(file_path).parts
            if len(parts) >= 2:
                try:
                    profile_id = uuid.UUID(parts[1])
                    from sqlalchemy import select
                    from app.db import AsyncSessionLocal
                    from app.models.profile import Profile

                    async with AsyncSessionLocal() as session:
                        result = await session.execute(
                            select(Profile).where(Profile.id == profile_id)
                        )
                        profile = result.scalar_one_or_none()
                        if profile is None or str(profile.owner_user_id) != user["sub"]:
                            raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Not found"})
                except HTTPException:
                    raise
                except Exception:
                    raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Not found"})
            else:
                raise HTTPException(status_code=404, detail={"code": "not_found", "message": "Not found"})

    content_type, _ = mimetypes.guess_type(str(resolved))
    if not content_type:
        content_type = "image/jpeg"

    # passport.jpg is auth-gated — must NOT be cached by any intermediary
    # (Cloudflare, browser shared cache, etc.) because they don't vary by
    # cookie. A previous unauth hit getting cached as 404 would otherwise
    # block even authenticated reads. Public variants (blurred/thumb) can
    # stay cacheable.
    cache_control = (
        "private, no-store, max-age=0"
        if resolved.name == "passport.jpg"
        else "public, max-age=3600"
    )
    file_bytes = resolved.read_bytes()
    return Response(
        content=file_bytes,
        media_type=content_type,
        headers={"Cache-Control": cache_control},
    )
