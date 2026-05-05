"""Seed bride/groom test profiles with multiple real photos and FULL data
populated. Each variant has distinct values for every field so the admin
list reads as four genuinely different people.

Usage:
    python -m scripts.seed_verify_profile --variant bride1 --photos a.jpg b.jpg c.jpg
    python -m scripts.seed_verify_profile --variant bride2 --photos ...
    python -m scripts.seed_verify_profile --variant groom1 --photos ...
    python -m scripts.seed_verify_profile --variant groom2 --photos ...

    # Cleanup later:
    python -m scripts.seed_verify_profile --cleanup <user_uuid>
"""
from __future__ import annotations

import argparse
import asyncio
import uuid
from pathlib import Path
from typing import Any

from sqlalchemy import select

from app.db import AsyncSessionLocal
from app.models.profile import Profile
from app.models.user import User
from app.services.settings import settings_service


# ---------------------------------------------------------------------------
# Profile templates — every variant has distinct values for every field.
# ---------------------------------------------------------------------------

VARIANTS: dict[str, dict[str, Any]] = {
    "bride1": {
        "_full_name": "Priya Patil",
        "gender": "bride",
        "first_name": "Priya",
        "last_name": "Patil",
        "surname_clan": "Patil",
        "dob": "1996-04-12",
        "marital_status": "never_married",
        "mother_tongue": "Marathi",
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
        "hobbies": "Reading, hiking in the Sahyadris, Hindustani classical music, weekend cooking",
        "city": "Hyderabad",
        "state": "Telangana",
        "country": "India",
        "pin_code": "500032",
        "about": (
            "Family-oriented finance professional based in Hyderabad. Split my "
            "weekends between trekking, classical vocal practice, and Maratha-style "
            "cooking. Close to my parents and a younger brother. I value honesty, "
            "growth, and a good sense of humour."
        ),
        "partner_expectations": (
            "Looking for a kind, well-educated partner who values family, open "
            "communication, and shared adventures. Maratha cultural roots are a "
            "plus but not a must."
        ),
    },
    "bride2": {
        "_full_name": "Anjali Joshi",
        "gender": "bride",
        "first_name": "Anjali",
        "last_name": "Joshi",
        "surname_clan": "Joshi",
        "dob": "1994-11-23",
        "marital_status": "never_married",
        "mother_tongue": "Telugu",
        "caste": "Maratha",
        "sub_caste": "Are Marathi",
        "height_cm": 158,
        "weight_kg": 52,
        "complexion": "fair",
        "body_type": "average",
        "blood_group": "O+",
        "gotra": "Vasishta",
        "kuldevata": "Tuljabhavani",
        "devak": "Mango",
        "nakshatram": "Hasta",
        "rashi": "Kanya (Virgo)",
        "manglik": "partial",
        "time_of_birth": "21:45",
        "place_of_birth": "Mumbai",
        "education": "MBBS, MD Pediatrics",
        "college_university": "Grant Medical College, Mumbai",
        "occupation": "Pediatrician",
        "employer": "Lilavati Hospital",
        "annual_income_inr": 2400000,
        "work_location": "Mumbai, India",
        "father_name": "Vinod Joshi",
        "mother_name": "Lata Joshi",
        "father_occupation": "Chartered Accountant",
        "mother_occupation": "School Teacher",
        "num_family_members": 5,
        "num_brothers": 1,
        "num_sisters": 1,
        "num_brothers_married": 1,
        "num_sisters_married": 0,
        "family_type": "joint",
        "family_status": "affluent",
        "family_values": "traditional",
        "native_place": "Nashik",
        "diet": "veg",
        "smokes": "no",
        "drinks": "no",
        "hobbies": "Bharatanatyam, oil painting, weekend volunteering at children's NGO",
        "city": "Mumbai",
        "state": "Maharashtra",
        "country": "India",
        "pin_code": "400050",
        "about": (
            "Pediatrician working at Lilavati. Trained Bharatanatyam dancer; I "
            "weekend-volunteer at an NGO that provides medical care for kids in "
            "the Mumbai slums. Joint family rooted in Nashik. I value compassion, "
            "balance, and quiet evenings with good food and conversation."
        ),
        "partner_expectations": (
            "Hoping to meet a thoughtful partner with strong professional values "
            "and a soft side. Comfortable with my evening clinics and occasional "
            "dance recitals. Mumbai-based or willing to relocate."
        ),
    },
    "groom1": {
        "_full_name": "Aniket Deshmukh",
        "gender": "groom",
        "first_name": "Aniket",
        "last_name": "Deshmukh",
        "surname_clan": "Deshmukh",
        "dob": "1992-09-08",
        "marital_status": "never_married",
        "mother_tongue": "Hindi",
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
        "hobbies": "Long-distance running, photography, board games, Marathi literature",
        "city": "Bengaluru",
        "state": "Karnataka",
        "country": "India",
        "pin_code": "560001",
        "about": (
            "Software engineer at Atlassian, based in Bengaluru. From Pune, family "
            "rooted in Kolhapur. Marathon finisher, weekend photographer, slow "
            "reader of Marathi literature. Close to my parents and elder married "
            "sister. I value steadiness, curiosity, and a partner who makes me laugh."
        ),
        "partner_expectations": (
            "Seeking a well-educated, family-oriented partner with a sense of "
            "humour and shared interest in travel, books, or sports. Open to any "
            "location - would relocate for the right person."
        ),
    },
    "groom2": {
        "_full_name": "Rohan Pawar",
        "gender": "groom",
        "first_name": "Rohan",
        "last_name": "Pawar",
        "surname_clan": "Pawar",
        "dob": "1990-02-17",
        "marital_status": "divorced",
        "mother_tongue": "Marathi",
        "caste": "Maratha",
        "sub_caste": "Arya Kshatriya",
        "height_cm": 173,
        "weight_kg": 78,
        "complexion": "wheatish",
        "body_type": "average",
        "blood_group": "AB+",
        "gotra": "Atri",
        "kuldevata": "Jotiba",
        "devak": "Banyan",
        "nakshatram": "Shravana",
        "rashi": "Makara (Capricorn)",
        "manglik": "yes",
        "time_of_birth": "08:05",
        "place_of_birth": "Satara",
        "education": "B.E., Mechanical Engineering",
        "college_university": "COEP Pune",
        "occupation": "Mechanical Design Lead",
        "employer": "Tata Motors",
        "annual_income_inr": 1800000,
        "work_location": "Pune, India",
        "father_name": "Sanjay Pawar",
        "mother_name": "Pushpa Pawar",
        "father_occupation": "Sugar Mill Manager",
        "mother_occupation": "Homemaker",
        "num_family_members": 6,
        "num_brothers": 2,
        "num_sisters": 1,
        "num_brothers_married": 1,
        "num_sisters_married": 1,
        "family_type": "joint",
        "family_status": "middle_class",
        "family_values": "orthodox",
        "native_place": "Satara",
        "diet": "non-veg",
        "smokes": "occasionally",
        "drinks": "no",
        "hobbies": "Cricket, vintage car restoration, watching Marathi theatre",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "pin_code": "411038",
        "about": (
            "Design lead at Tata Motors, Pune. From Satara, second of three "
            "siblings. I spend weekends restoring my grandfather's old Fiat and "
            "watching Marathi theatre with my parents. Divorced two years ago, "
            "no children. Looking for a fresh start with the right partner."
        ),
        "partner_expectations": (
            "Looking for a kind-hearted, family-oriented partner. Open to brides "
            "who have been married before. Pune-based or willing to settle in "
            "Pune is preferred."
        ),
    },
}


def make_credentials(suffix: str, variant: str) -> dict[str, str]:
    digit_tail = f"{int(suffix, 16) % 10**6:06d}"
    gender = VARIANTS[variant]["gender"]
    full_name = VARIANTS[variant]["_full_name"]
    return {
        "email": f"verify_{variant}_{suffix}@marathakalyanam.com",
        "user_id": f"verify_{variant}_{suffix}",
        "password": "Verify1234!",
        "phone": f"+91{'9000' if gender == 'bride' else '9100'}{digit_tail}",
        "full_name": full_name,
    }


async def seed(variant: str, photo_paths: list[Path]) -> None:
    if variant not in VARIANTS:
        raise SystemExit(f"--variant must be one of {list(VARIANTS)}")
    for p in photo_paths:
        if not p.exists():
            raise SystemExit(f"photo file not found: {p}")

    payload = {k: v for k, v in VARIANTS[variant].items() if not k.startswith("_")}
    suffix = uuid.uuid4().hex[:6]
    creds = make_credentials(suffix, variant)
    photos = [(p.name, p.read_bytes()) for p in photo_paths]

    print(f"\nSeeding {variant} profile (suffix={suffix})...")
    print(f"  email     {creds['email']}")
    print(f"  user_id   {creds['user_id']}")
    print(f"  phone     {creds['phone']}")
    print(f"  password  {creds['password']}")
    print(f"  photos    {len(photos)} files: {[p.name for p in photo_paths]}\n")

    from httpx import ASGITransport, AsyncClient
    from app.main import app

    # Disable face detection for the duration — pravatar avatars don't always
    # pass the OpenCV cascade reliably even though they're real faces.
    async with AsyncSessionLocal() as session:
        await settings_service.set("require_face_detection", False, session)
    # Bump max-photos to ensure 3 fit
    async with AsyncSessionLocal() as session:
        await settings_service.set("photos_max_per_profile", 5, session)

    user_uuid = None
    profile_id = None
    profile_number = "(none)"
    try:
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://testserver",
        ) as c:
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

            async with AsyncSessionLocal() as session:
                user = (await session.execute(select(User).where(User.id == uuid.UUID(user_uuid)))).scalar_one()
                user.email_verified = True
                user.is_approved = True
                await session.commit()
            print("[2/5] Email verified + admin-approved")

            resp = await c.post("/auth/login", json={"identifier": creds["email"], "password": creds["password"]})
            assert resp.status_code == 200, f"login: {resp.status_code} {resp.text}"
            print("[3/5] Logged in")

            resp = await c.post("/profiles", json=payload)
            assert resp.status_code == 201, f"create profile: {resp.status_code} {resp.text}"
            profile = resp.json()
            profile_id = profile["id"]
            profile_number = profile.get("profile_number") or "(unknown)"
            print(f"[4/5] Created profile id={profile_id}  number={profile_number}")

            print(f"[5/5] Uploading {len(photos)} photo(s)…")
            for i, (fname, jpeg) in enumerate(photos, start=1):
                files = {"data": (fname, jpeg, "image/jpeg")}
                resp = await c.post(f"/profiles/{profile_id}/photos", files=files)
                assert resp.status_code == 201, f"photo upload #{i}: {resp.status_code} {resp.text}"
                photo = resp.json()
                marker = "PRIMARY" if photo["is_primary"] else "       "
                print(f"      [{i}/{len(photos)}] {marker}  id={photo['id'][:8]}…  bytes={photo['byte_size']}")
    finally:
        # Restore settings
        async with AsyncSessionLocal() as session:
            await settings_service.set("require_face_detection", True, session)

    print()
    print("=" * 70)
    print(f"DONE — {variant.upper()} ({creds['full_name']}) is live.")
    print(f"  URL:       https://marathakalyanam.com/login")
    print(f"  User ID:   {creds['user_id']}     (email: {creds['email']})")
    print(f"  Password:  {creds['password']}")
    print(f"  Profile:   {profile_number}  ({profile_id})")
    print(f"  Cleanup:   python -m scripts.seed_verify_profile --cleanup {user_uuid}")
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
    parser.add_argument("--variant", choices=tuple(VARIANTS), help="profile to seed")
    parser.add_argument("--photos", type=Path, nargs="+", help="one or more real face photos")
    parser.add_argument("--cleanup", metavar="USER_UUID", help="delete data created by a prior seed run")
    args = parser.parse_args()
    if args.cleanup:
        asyncio.run(cleanup(args.cleanup))
    elif args.variant and args.photos:
        asyncio.run(seed(args.variant, args.photos))
    else:
        parser.error("either --cleanup, or both --variant and --photos, must be supplied")


if __name__ == "__main__":
    main()
