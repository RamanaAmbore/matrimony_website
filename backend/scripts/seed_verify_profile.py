"""One-off seed script: create a complete test profile with a real photo, then
print credentials so a human can log in and verify everything looks right.

Run via: python -m scripts.seed_verify_profile
Requires the backend venv. Talks to whatever DATABASE_URL/site is in .env.

The created data is left in place. Cleanup is your call — to remove afterwards:
    python -m scripts.seed_verify_profile --cleanup <user_uuid>
"""
from __future__ import annotations

import argparse
import asyncio
import io
import random
import sys
import uuid
from datetime import date

from PIL import Image
from sqlalchemy import select

from app.config import IS_PROD
from app.db import AsyncSessionLocal
from app.models.profile import Profile
from app.models.user import User
from app.services import auth as auth_svc
from app.services.settings import settings_service


SUFFIX = uuid.uuid4().hex[:6]
EMAIL = f"verify_{SUFFIX}@marathakalyanam.com"
USER_ID = f"verify_{SUFFIX}"
PASSWORD = "Verify1234!"
PHONE = f"+9198{random.Random(SUFFIX).randint(0, 99999999):08d}"
FULL_NAME = "Verify Tester"


def make_jpeg() -> bytes:
    """Random-pixel JPEG large enough to clear photo_min_kb after compression."""
    rng = random.Random(SUFFIX)
    img = Image.new("RGB", (1200, 1200))
    pixels = img.load()
    for y in range(1200):
        for x in range(1200):
            pixels[x, y] = (
                rng.randint(80, 230),
                rng.randint(80, 230),
                rng.randint(80, 230),
            )
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


async def seed() -> None:
    from httpx import ASGITransport, AsyncClient
    from app.main import app

    print(f"\nSeeding test profile (suffix={SUFFIX})...")
    print(f"  email     {EMAIL}")
    print(f"  user_id   {USER_ID}")
    print(f"  phone     {PHONE}")
    print(f"  password  {PASSWORD}\n")

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        # 1) Register
        resp = await c.post(
            "/auth/register",
            json={
                "email": EMAIL,
                "password": PASSWORD,
                "user_id": USER_ID,
                "phone_number": PHONE,
                "full_name": FULL_NAME,
            },
        )
        assert resp.status_code == 201, f"register: {resp.status_code} {resp.text}"
        user_uuid = resp.json()["uuid"]
        print(f"[1/5] Registered user uuid={user_uuid}")

        # 2) Verify email + approve via DB (skips the email round-trip)
        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))).scalar_one()
            user.email_verified = True
            user.is_approved = True
            await session.commit()
        print("[2/5] Email verified + admin-approved (direct DB)")

        # 3) Login → JWT cookie attaches to client
        resp = await c.post("/auth/login", json={"identifier": EMAIL, "password": PASSWORD})
        assert resp.status_code == 200, f"login: {resp.status_code} {resp.text}"
        print("[3/5] Logged in")

        # 4) Create a draft profile with broad coverage of all sections
        profile_payload = {
            "gender": "bride",
            "first_name": "Verify",
            "last_name": "Tester",
            "surname_clan": "Patil",
            "dob": "1996-04-12",
            "marital_status": "never_married",
            "mother_tongue": "Telugu",
            "caste": "Maratha",
            "sub_caste": "Maratha",
            "height_cm": 165,
            "weight_kg": 58,
            "complexion": "wheatish",
            "body_type": "slim",
            "blood_group": "A+",
            "gotra": "Kashyap",
            "kuldevata": "Bhavani",
            "devak": "Neem",
            "nakshatram": "Rohini",
            "rashi": "Vrishabha (Taurus)",
            "manglik": "no",
            "time_of_birth": "06:30",
            "place_of_birth": "Hyderabad",
            "education": "MBA, Finance",
            "college_university": "Osmania University",
            "occupation": "Financial Analyst",
            "employer": "Deloitte",
            "annual_income_inr": 1500000,
            "work_location": "Hyderabad, India",
            "father_name": "Ramesh Patil",
            "mother_name": "Sunita Patil",
            "father_occupation": "Retired Govt. Officer",
            "mother_occupation": "Homemaker",
            "num_family_members": 4,
            "num_brothers": 1,
            "num_sisters": 0,
            "num_brothers_married": 0,
            "num_sisters_married": 0,
            "family_type": "nuclear",
            "family_status": "upper_middle",
            "family_values": "moderate",
            "native_place": "Pune",
            "diet": "non-veg",
            "smokes": "no",
            "drinks": "occasionally",
            "hobbies": "Reading, hiking, classical music",
            "city": "Hyderabad",
            "state": "Telangana",
            "country": "India",
            "pin_code": "500032",
            "about": (
                "Family-oriented finance professional based in Hyderabad. "
                "Enjoys travel, cooking, and weekend treks in the Sahyadris. "
                "Looking for a partner who values family, integrity, and growth."
            ),
            "partner_expectations": (
                "Seeking a kind, well-educated partner with similar values, "
                "ideally based in or open to Hyderabad / Pune. Cultural roots "
                "in the Maratha community are a plus."
            ),
        }
        resp = await c.post("/profiles", json=profile_payload)
        assert resp.status_code == 201, f"create profile: {resp.status_code} {resp.text}"
        profile = resp.json()
        profile_id = profile["id"]
        profile_number = profile.get("profile_number") or "(unknown)"
        print(f"[4/5] Created profile id={profile_id}  number={profile_number}")

        # 5) Upload a photo. Disable face detection for the synthetic JPEG.
        async with AsyncSessionLocal() as session:
            await settings_service.set("require_face_detection", False, session)
        try:
            jpeg = make_jpeg()
            files = {"data": (f"verify_{SUFFIX}.jpg", jpeg, "image/jpeg")}
            resp = await c.post(f"/profiles/{profile_id}/photos", files=files)
            assert resp.status_code == 201, f"photo upload: {resp.status_code} {resp.text}"
            photo = resp.json()
            print(f"[5/5] Uploaded photo id={photo['id']}  bytes={photo['byte_size']}")
            print(f"      passport_url  {photo['passport_url']}")
            print(f"      blurred_url   {photo['blurred_url']}")
            print(f"      thumb_url     {photo['thumb_url']}")
        finally:
            async with AsyncSessionLocal() as session:
                await settings_service.set("require_face_detection", True, session)

    print()
    print("=" * 70)
    print("DONE.  Sign in to verify:")
    print(f"  URL:       {'https://marathakalyanam.com' if IS_PROD else 'http://localhost:5173'}/login")
    print(f"  User ID:   {USER_ID}     (or email: {EMAIL})")
    print(f"  Password:  {PASSWORD}")
    print(f"  Profile:   {profile_number}  ({profile_id})")
    print()
    print("To delete the test data afterwards:")
    print(f"  python -m scripts.seed_verify_profile --cleanup {user_uuid}")
    print("=" * 70)


async def cleanup(user_uuid: str) -> None:
    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))).scalar_one_or_none()
        if u is None:
            print(f"User {user_uuid} not found — already cleaned up?")
            return
        # Find profile(s) so we can DELETE through the route to also clear files.
        profs = (await session.execute(select(Profile).where(Profile.owner_user_id == u.id))).scalars().all()
        prof_ids = [str(p.id) for p in profs]
        await session.delete(u)
        await session.commit()
        print(f"Deleted user {u.email}  + {len(prof_ids)} profile(s) cascaded.")
        # The profile-delete route does on-disk cleanup; cascade-delete from User
        # leaves the JPEG variants on disk. Do a best-effort sweep here.
        from pathlib import Path
        from app.config import MEDIA_ROOT
        for pid in prof_ids:
            pdir = MEDIA_ROOT / "profiles" / pid
            if pdir.exists():
                import shutil
                shutil.rmtree(pdir)
                print(f"  removed {pdir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cleanup", metavar="USER_UUID", help="delete test data created by a prior seed run")
    args = parser.parse_args()
    if args.cleanup:
        asyncio.run(cleanup(args.cleanup))
    else:
        asyncio.run(seed())


if __name__ == "__main__":
    main()
