"""Photo upload/management routes."""
import uuid
from typing import Annotated, Any

from litestar import Controller, delete, post
from litestar.connection import Request
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import HTTPException
from litestar.params import Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.photo import Photo
from app.models.profile import Profile, ProfileStatusEnum
from app.services import storage as storage_svc
from app.services.images import PhotoValidationError, process_upload
from app.services.settings import settings_service


def _reset_to_pending_if_approved(profile: Profile, is_owner_edit: bool) -> bool:
    """G4: photo CRUD by the OWNER on an approved profile drops it back to
    pending so an admin re-reviews the visual content. Without this, an
    owner could swap the verified photo out post-approval (bait-and-switch).
    Mirrors the same auto-pending behaviour used by `update_profile`.

    Admin / super edits preserve status — the admin is the reviewer, no
    re-review is needed when they make the change themselves.

    Returns True if the status was reset.
    """
    if is_owner_edit and profile.status == ProfileStatusEnum.approved:
        profile.status = ProfileStatusEnum.pending
        return True
    return False


def _check_can_edit_photos(profile: Profile, user_payload: dict) -> tuple[bool, bool]:
    """Returns (is_owner, is_admin_caller). Raises 403 if neither.

    Admin / super may upload, delete, and reorder photos on any profile —
    same access pattern the rest of the admin profile-edit flow uses.
    """
    is_owner = str(profile.owner_user_id) == user_payload["sub"]
    is_admin_caller = bool(user_payload.get("is_admin")) or bool(user_payload.get("is_super"))
    if not is_owner and not is_admin_caller:
        raise HTTPException(status_code=403, detail={"code": "forbidden", "message": "Not your profile"})
    return is_owner, is_admin_caller


def _photo_to_dict(photo: Photo, request: Request) -> dict[str, Any]:
    """Owner-side photo serialization. Caller is the profile owner (auth-
    gated by the route), so passport gets a private URL — signed-URL on
    R2, direct on local. Non-private variants always get public URLs."""
    storage = storage_svc.get_storage()
    return {
        "id": str(photo.id),
        "profile_id": str(photo.profile_id),
        "original_filename": photo.original_filename,
        "passport_url": storage.private_url(photo.passport_path),
        "blurred_url": storage.public_url(photo.blurred_path),
        "thumb_url": storage.public_url(photo.thumb_path),
        "byte_size": photo.byte_size,
        "is_primary": photo.is_primary,
        "created_at": photo.created_at.isoformat(),
    }


class PhotoController(Controller):
    path = "/profiles/{profile_id:str}/photos"

    @post("", status_code=201)
    async def upload_photo(
        self,
        profile_id: str,
        request: Request,
        db: AsyncSession,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> dict[str, Any]:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthenticated", "message": "Authentication required"},
            )

        try:
            pid = uuid.UUID(profile_id)
        except ValueError:
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "Profile not found"}
            )

        result = await db.execute(
            select(Profile).where(Profile.id == pid).options(selectinload(Profile.photos))
        )
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "Profile not found"}
            )

        is_owner, _is_admin = _check_can_edit_photos(profile, user)

        max_photos = settings_service.get_int("photos_max_per_profile", 3)
        if len(profile.photos) >= max_photos:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "photo_limit",
                    "message": f"Maximum {max_photos} photos per profile",
                },
            )

        file_bytes = await data.read()
        filename = data.filename or "upload.jpg"

        # First photo on the profile is the primary by default;
        # face detection is only enforced for the primary photo.
        is_primary = len(profile.photos) == 0

        try:
            passport_bytes, blurred_bytes, thumb_bytes = process_upload(
                file_bytes, filename, is_primary=is_primary
            )
        except PhotoValidationError as exc:
            raise HTTPException(
                status_code=422,
                detail={"code": "photo_validation_error", "message": exc.user_message},
            )

        photo_id = uuid.uuid4()
        passport_rel = f"profiles/{pid}/{photo_id}/passport.jpg"
        blurred_rel = f"profiles/{pid}/{photo_id}/blurred.jpg"
        thumb_rel = f"profiles/{pid}/{photo_id}/thumb.jpg"

        # Write all three variants through the active storage backend
        # (local disk or R2). Run in parallel via asyncio.gather since
        # boto3 calls block — to_thread releases the loop.
        import asyncio as _asyncio
        await _asyncio.gather(
            storage_svc.write_async(passport_rel, passport_bytes),
            storage_svc.write_async(blurred_rel, blurred_bytes),
            storage_svc.write_async(thumb_rel, thumb_bytes),
        )

        photo = Photo(
            id=photo_id,
            profile_id=pid,
            original_filename=filename,
            passport_path=passport_rel,
            blurred_path=blurred_rel,
            thumb_path=thumb_rel,
            byte_size=len(passport_bytes),
            is_primary=is_primary,
        )
        db.add(photo)
        _reset_to_pending_if_approved(profile, is_owner_edit=is_owner)
        await db.commit()
        await db.refresh(photo)

        return _photo_to_dict(photo, request)

    @delete("/{photo_id:str}", status_code=204)
    async def delete_photo(
        self,
        profile_id: str,
        photo_id: str,
        request: Request,
        db: AsyncSession,
    ) -> None:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthenticated", "message": "Authentication required"},
            )

        try:
            pid = uuid.UUID(profile_id)
            phid = uuid.UUID(photo_id)
        except ValueError:
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "Not found"}
            )

        result = await db.execute(select(Profile).where(Profile.id == pid))
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "Profile not found"}
            )

        is_owner, _is_admin = _check_can_edit_photos(profile, user)

        result2 = await db.execute(
            select(Photo).where(Photo.id == phid, Photo.profile_id == pid)
        )
        photo = result2.scalar_one_or_none()
        if not photo:
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "Photo not found"}
            )

        # Delete all three variants from the active storage backend.
        for path_rel in [photo.passport_path, photo.blurred_path, photo.thumb_path]:
            await storage_svc.delete_async(path_rel)

        was_primary = photo.is_primary
        await db.delete(photo)
        _reset_to_pending_if_approved(profile, is_owner_edit=is_owner)
        await db.commit()

        if was_primary:
            result3 = await db.execute(
                select(Photo).where(Photo.profile_id == pid).order_by(Photo.created_at)
            )
            remaining = result3.scalars().first()
            if remaining:
                remaining.is_primary = True
                await db.commit()

    @post("/{photo_id:str}/primary")
    async def set_primary(
        self,
        profile_id: str,
        photo_id: str,
        request: Request,
        db: AsyncSession,
    ) -> dict[str, Any]:
        user = request.scope.get("user_payload")
        if not user:
            raise HTTPException(
                status_code=401,
                detail={"code": "unauthenticated", "message": "Authentication required"},
            )

        try:
            pid = uuid.UUID(profile_id)
            phid = uuid.UUID(photo_id)
        except ValueError:
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "Not found"}
            )

        result = await db.execute(select(Profile).where(Profile.id == pid))
        profile = result.scalar_one_or_none()
        if not profile:
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "Profile not found"}
            )

        is_owner, _is_admin = _check_can_edit_photos(profile, user)

        result2 = await db.execute(select(Photo).where(Photo.profile_id == pid))
        all_photos = result2.scalars().all()
        target = None
        for p in all_photos:
            if p.id == phid:
                target = p
            p.is_primary = p.id == phid

        if target is None:
            raise HTTPException(
                status_code=404, detail={"code": "not_found", "message": "Photo not found"}
            )

        _reset_to_pending_if_approved(profile, is_owner_edit=is_owner)
        await db.commit()
        await db.refresh(target)
        return _photo_to_dict(target, request)
