"""Seed a complete bride or groom test profile with a real photo, leaving
the data in place for human verification.

Usage:
    # Bride profile, photo from a file:
    python -m scripts.seed_verify_profile --gender bride --photo /tmp/bride.jpg

    # Groom profile:
    python -m scripts.seed_verify_profile --gender groom --photo /tmp/groom.jpg

    # Cleanup afterwards:
    python -m scripts.seed_verify_profile --cleanup <user_uuid>

Every profile field across every wizard section is populated. The photo is
read from disk (not generated) — supply a real face JPEG/PNG so the image
actually renders meaningfully in the admin board / search results.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.config import IS_PROD
from app.db import AsyncSessionLocal
from app.models.profile import Profile
from app.models.user import User
from app.services.settings import settings_service


# ---------------------------------------------------------------------------
# Profile templates — every field populated for both bride and groom.
# ---------------------------------------------------------------------------

BRIDE: dict[str, Any] = {
    "gender": "bride",
    "first_name": "Priya",
    "last_name": "Patil",
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
    "employer": "Deloitte India",
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
    "hobbies": "Reading, hiking in the Sahyadris, Hindustani classical music, and weekend cooking",
    "city": "Hyderabad",
    "state": "Telangana",
    "country": "India",
    "pin_code": "500032",
    "about": (
        "Family-oriented finance professional based in Hyderabad. "
        "I split my weekends between trekking in the Sahyadris, cooking "
        "Maratha-style fish curry for friends, and learning Hindustani "
        "classical vocal. Close to my parents and a younger brother. "
        "I value honesty, growth, and a good sense of humour."
    ),
    "partner_expectations": (
        "Looking for a kind, well-educated partner who values family, "
        "open communication, and shared adventures. Maratha cultural roots "
        "are a plus but not a must. Ideally based in or open to Hyderabad, "
        "Pune, or remote-friendly cities."
    ),
}

GROOM: dict[str, Any] = {
    "gender": "groom",
    "first_name": "Aniket",
    "last_name": "Deshmukh",
    "surname_clan": "Deshmukh",
    "dob": "1992-09-08",
    "marital_status": "never_married",
    "mother_tongue": "Marathi",
    "caste": "Maratha",
    "sub_caste": "Maratha Non-Brahmin",
    "height_cm": 178,
    "weight_kg": 72,
    "complexion": "fair",
    "body_type": "athletic",
    "blood_group": "B+",
    "gotra": "Bharadwaj",
    "kuldevata": "Khandoba",
    "devak": "Audumbar",
    "nakshatram": "Pushya",
    "rashi": "Karka (Cancer)",
    "manglik": "no",
    "time_of_birth": "14:15",
    "place_of_birth": "Pune",
    "education": "M.Tech, Computer Science",
    "college_university": "IIT Bombay",
    "occupation": "Senior Software Engineer",
    "employer": "Atlassian",
    "annual_income_inr": 4200000,
    "work_location": "Bengaluru, India",
    "father_name": "Vikram Deshmukh",
    "mother_name": "Anjali Deshmukh",
    "father_occupation": "Civil Engineer",
    "mother_occupation": "School Principal",
    "num_family_members": 5,
    "num_brothers": 0,
    "num_sisters": 1,
    "num_brothers_married": 0,
    "num_sisters_married": 1,
    "family_type": "nuclear",
    "family_status": "upper_middle",
    "family_values": "traditional",
    "native_place": "Kolhapur",
    "diet": "non-veg",
    "smokes": "no",
    "drinks": "occasionally",
    "hobbies": "Long-distance running, photography, board games, and Marathi literature",
    "city": "Bengaluru",
    "state": "Karnataka",
    "country": "India",
    "pin_code": "560001",
    "about": (
        "Software engineer at Atlassian, based in Bengaluru. Originally from "
        "Pune; family roots in Kolhapur. Marathon finisher, weekend "
        "photographer, and slow reader of Marathi literature. Close to my "
        "parents and elder married sister. I value steadiness, curiosity, "
        "and a partner who makes me laugh."
    ),
    "partner_expectations": (
        "Seeking a well-educated, family-oriented partner with a sense of "
        "humour and shared interest in travel, books, or sports. Open to "
        "any location - would relocate for the right person."
    ),
}


# ---------------------------------------------------------------------------
# Driver
# ---------------------------------------------------------------------------


def make_credentials(suffix: str, gender: str) -> dict[str, str]:
    # Phone tail must be digits-only — suffix is hex, so derive a digit run.
    digit_tail = f"{int(suffix, 16) % 10**6:06d}"
    return {
        "email": f"verify_{gender}_{suffix}@marathakalyanam.com",
        "user_id": f"verify_{gender}_{suffix}",
        "password": "Verify1234!",
        # Bride uses +91 9000…, groom +91 9100…
        "phone": f"+91{'9000' if gender == 'bride' else '9100'}{digit_tail}",
        "full_name": "Priya Patil" if gender == "bride" else "Aniket Deshmukh",
    }


async def seed(gender: str, photo_path: Path) -> None:
    if gender not in ("bride", "groom"):
        raise SystemExit("--gender must be 'bride' or 'groom'")
    if not photo_path.exists():
        raise SystemExit(f"photo file not found: {photo_path}")

    payload = BRIDE if gender == "bride" else GROOM
    suffix = uuid.uuid4().hex[:6]
    creds = make_credentials(suffix, gender)
    photo_bytes = photo_path.read_bytes()

    print(f"\nSeeding {gender} profile (suffix={suffix})...")
    print(f"  email     {creds['email']}")
    print(f"  user_id   {creds['user_id']}")
    print(f"  phone     {creds['phone']}")
    print(f"  password  {creds['password']}")
    print(f"  photo     {photo_path} ({len(photo_bytes):,} bytes)\n")

    from httpx import ASGITransport, AsyncClient
    from app.main import app

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as c:
        # 1) Register
        resp = await c.post(
            "/auth/register",
            json={
                "email": creds["email"],
                "password": creds["password"],
                "user_id": creds["user_id"],
                "phone_number": creds["phone"],
                "full_name": creds["full_name"],
            },
        )
        assert resp.status_code == 201, f"register: {resp.status_code} {resp.text}"
        user_uuid = resp.json()["uuid"]
        print(f"[1/5] Registered user uuid={user_uuid}")

        # 2) Verify email + approve via DB
        async with AsyncSessionLocal() as session:
            user = (await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))).scalar_one()
            user.email_verified = True
            user.is_approved = True
            await session.commit()
        print("[2/5] Email verified + admin-approved (direct DB)")

        # 3) Login
        resp = await c.post("/auth/login", json={"identifier": creds["email"], "password": creds["password"]})
        assert resp.status_code == 200, f"login: {resp.status_code} {resp.text}"
        print("[3/5] Logged in")

        # 4) Create profile with every field populated
        resp = await c.post("/profiles", json=payload)
        assert resp.status_code == 201, f"create profile: {resp.status_code} {resp.text}"
        profile = resp.json()
        profile_id = profile["id"]
        profile_number = profile.get("profile_number") or "(unknown)"
        print(f"[4/5] Created profile id={profile_id}  number={profile_number}")
        # Confirm every field round-trips
        missing = [k for k in payload if profile.get(k) != payload[k]]
        if missing:
            print(f"      WARN: fields not echoed back: {missing}")

        # 5) Upload the supplied real photo (face detection on by default).
        files = {"data": (photo_path.name, photo_bytes, "image/jpeg")}
        resp = await c.post(f"/profiles/{profile_id}/photos", files=files)
        if resp.status_code != 201:
            # If face detection rejects, retry once with it disabled.
            print(f"      first attempt failed ({resp.status_code}); retrying with face detection off")
            print(f"      reason: {resp.text}")
            async with AsyncSessionLocal() as session:
                await settings_service.set("require_face_detection", False, session)
            try:
                resp = await c.post(f"/profiles/{profile_id}/photos", files=files)
                assert resp.status_code == 201, f"photo upload (retry): {resp.status_code} {resp.text}"
            finally:
                async with AsyncSessionLocal() as session:
                    await settings_service.set("require_face_detection", True, session)
        photo = resp.json()
        print(f"[5/5] Uploaded photo id={photo['id']}  bytes={photo['byte_size']}")

    print()
    print("=" * 70)
    print(f"DONE — {gender.upper()} profile is live.")
    print(f"  URL:       https://marathakalyanam.com/login")
    print(f"  User ID:   {creds['user_id']}     (or email: {creds['email']})")
    print(f"  Password:  {creds['password']}")
    print(f"  Profile:   {profile_number}  ({profile_id})")
    print()
    print("To delete this test data:")
    print(f"  python -m scripts.seed_verify_profile --cleanup {user_uuid}")
    print("=" * 70)


async def cleanup(user_uuid: str) -> None:
    import shutil
    from app.config import MEDIA_ROOT

    async with AsyncSessionLocal() as session:
        u = (await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))).scalar_one_or_none()
        if u is None:
            print(f"User {user_uuid} not found — already cleaned up?")
            return
        profs = (await session.execute(select(Profile).where(Profile.owner_user_id == u.id))).scalars().all()
        prof_ids = [str(p.id) for p in profs]
        await session.delete(u)
        await session.commit()
        print(f"Deleted user {u.email}  + {len(prof_ids)} profile(s) cascaded.")
        for pid in prof_ids:
            pdir = MEDIA_ROOT / "profiles" / pid
            if pdir.exists():
                shutil.rmtree(pdir)
                print(f"  removed {pdir}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gender", choices=("bride", "groom"), help="profile gender to seed")
    parser.add_argument("--photo", type=Path, help="path to real face photo (JPEG/PNG)")
    parser.add_argument("--cleanup", metavar="USER_UUID", help="delete data created by a prior seed run")
    args = parser.parse_args()
    if args.cleanup:
        asyncio.run(cleanup(args.cleanup))
    elif args.gender and args.photo:
        asyncio.run(seed(args.gender, args.photo))
    else:
        parser.error("either --cleanup, or both --gender and --photo, must be supplied")


if __name__ == "__main__":
    main()
