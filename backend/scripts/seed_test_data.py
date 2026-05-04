"""
Seed test data — many users, profiles, photos, detail requests.

Designed to be invoked on the production server (where DB + MEDIA_ROOT
are reachable):

    sudo -u www-data /opt/marathakalyanam/backend/.venv/bin/python \\
        /opt/marathakalyanam/backend/scripts/seed_test_data.py

Everything created has user_handle prefix `e2e_` so a later cleanup query
deletes only this seed: `DELETE FROM users WHERE user_handle LIKE 'e2e_%'`
(cascades through profiles → photos and detail_requests).
"""
from __future__ import annotations

import asyncio
import io
import os
import random
import sys
import uuid
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont
from sqlalchemy import text

# Make app importable when running from anywhere
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.config import MEDIA_ROOT  # noqa: E402
from app.db import AsyncSessionLocal  # noqa: E402
from app.models.photo import Photo  # noqa: E402
from app.models.profile import (  # noqa: E402
    DietEnum,
    GenderEnum,
    ManglikEnum,
    Profile,
    ProfileStatusEnum,
)
from app.models.request import DetailRequest, RequestStatusEnum  # noqa: E402
from app.models.user import User  # noqa: E402
from app.services.auth import hash_password  # noqa: E402

random.seed(42)

# Distribution
N_USERS = 100
STATUS_DIST = {
    ProfileStatusEnum.approved: 40,
    ProfileStatusEnum.pending: 25,
    ProfileStatusEnum.rejected: 15,
    ProfileStatusEnum.draft: 20,
}
N_REQUESTS = 35
PHOTOS_PER_PROFILE_RANGE = (1, 3)

FIRST_NAMES_M = ["Arjun", "Vivek", "Aditya", "Karthik", "Rohan", "Aniket", "Suraj",
                 "Yash", "Nikhil", "Tejas", "Manish", "Rahul", "Akash", "Saurabh",
                 "Pranav", "Rishi", "Vikram", "Harsh", "Devang", "Rohit"]
FIRST_NAMES_F = ["Priya", "Sneha", "Aishwarya", "Pooja", "Kavya", "Meera", "Anjali",
                 "Shruti", "Divya", "Riya", "Sanjana", "Tanvi", "Manasi", "Prachi",
                 "Aarti", "Neha", "Swati", "Madhuri", "Rashmi", "Lakshmi"]
LAST_NAMES = ["Patil", "Bhosale", "Jadhav", "Pawar", "Shinde", "Deshmukh", "More",
              "Kulkarni", "Joshi", "Rao", "Naidu", "Ambore", "Khade", "Salunkhe",
              "Sawant", "Kale", "Yadav", "Gaikwad", "Gore", "Mali"]
GOTRAS = ["Bharadwaja", "Vasishta", "Atri", "Kashyapa", "Vishvamitra",
          "Gautama", "Jamadagni", "Angirasa", "Kapila", "Bhrigu"]
NAKSHATRAMS = ["Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira",
               "Ardra", "Punarvasu", "Pushya", "Ashlesha", "Magha",
               "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra"]
RASHIS = ["Mesha", "Vrishabha", "Mithuna", "Karka", "Simha", "Kanya",
          "Tula", "Vrishchika", "Dhanu", "Makara", "Kumbha", "Meena"]
CITIES = [("Hyderabad", "Telangana"), ("Vijayawada", "Andhra Pradesh"),
          ("Pune", "Maharashtra"), ("Mumbai", "Maharashtra"),
          ("Bangalore", "Karnataka"), ("Chennai", "Tamil Nadu"),
          ("Visakhapatnam", "Andhra Pradesh"), ("Nagpur", "Maharashtra"),
          ("Solapur", "Maharashtra"), ("Tirupati", "Andhra Pradesh")]
EDUCATIONS = ["B.Tech", "B.E.", "MBA", "M.Tech", "MBBS", "B.Com", "MA", "MS", "PhD"]
OCCUPATIONS = ["Software Engineer", "Doctor", "Teacher", "Accountant",
               "Architect", "Designer", "Researcher", "Manager", "Consultant"]


def _seed_palette(seed_int: int) -> tuple[int, int, int]:
    """Deterministic pleasant background color from a seed."""
    rng = random.Random(seed_int)
    palettes = [
        (220, 196, 168), (180, 200, 220), (200, 180, 220), (220, 180, 180),
        (180, 220, 200), (210, 210, 180), (200, 210, 220), (220, 200, 180),
        (170, 200, 180), (220, 180, 210),
    ]
    return rng.choice(palettes)


def _generate_passport(name: str, idx: int, seed: int) -> bytes:
    """Generate a 413x531 placeholder JPEG with initials on a colored background."""
    img = Image.new("RGB", (413, 531), _seed_palette(seed))
    draw = ImageDraw.Draw(img)
    # Header band
    draw.rectangle([0, 0, 413, 80], fill=(107, 15, 26))
    draw.rectangle([0, 451, 413, 531], fill=(107, 15, 26))
    # Initials in big text
    initials = "".join(p[0].upper() for p in name.split() if p)[:2]
    try:
        font_big = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 160)
        font_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 18)
    except Exception:
        font_big = ImageFont.load_default()
        font_sm = ImageFont.load_default()
    bbox = draw.textbbox((0, 0), initials, font=font_big)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text(((413 - tw) // 2, (531 - th) // 2 - 30), initials,
              fill=(80, 30, 30), font=font_big)
    # Footer label
    label = f"E2E #{idx} · {name[:20]}"
    fbbox = draw.textbbox((0, 0), label, font=font_sm)
    fw = fbbox[2] - fbbox[0]
    draw.text(((413 - fw) // 2, 470), label, fill=(255, 248, 231), font=font_sm)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=85)
    return buf.getvalue()


def _generate_blurred(passport_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(passport_bytes)).convert("RGB")
    blur_w = 600
    ratio = blur_w / img.width
    img = img.resize((blur_w, int(img.height * ratio)), Image.LANCZOS)
    img = img.filter(ImageFilter.GaussianBlur(radius=14))
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=70)
    return buf.getvalue()


def _generate_thumb(passport_bytes: bytes) -> bytes:
    img = Image.open(io.BytesIO(passport_bytes)).convert("RGB")
    short = min(img.size)
    left = (img.width - short) // 2
    top = (img.height - short) // 2
    img = img.crop((left, top, left + short, top + short))
    img = img.resize((150, 150), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return buf.getvalue()


def _profile_demographics(idx: int, gender: GenderEnum) -> dict:
    rng = random.Random(idx + 1000)
    if gender == GenderEnum.bride:
        first = rng.choice(FIRST_NAMES_F)
    else:
        first = rng.choice(FIRST_NAMES_M)
    last = rng.choice(LAST_NAMES)
    city, state = rng.choice(CITIES)
    age = rng.randint(22, 35)
    dob = date.today() - timedelta(days=age * 365 + rng.randint(0, 364))
    return {
        "first_name": first,
        "last_name": last,
        "dob": dob,
        "mother_tongue": "Telugu" if rng.random() < 0.6 else "Marathi",
        "surname_clan": last,
        "height_cm": rng.randint(150, 185),
        "weight_kg": rng.randint(45, 90),
        "gotra": rng.choice(GOTRAS),
        "kuldevata": rng.choice(["Khandoba", "Bhavani", "Tulja Bhavani", "Mahadev"]),
        "devak": rng.choice(["Tulsi", "Kalas", "Bel"]),
        "nakshatram": rng.choice(NAKSHATRAMS),
        "rashi": rng.choice(RASHIS),
        # Pass string VALUES (not enum members) so SQLAlchemy + asyncpg
        # round-trip them as DB enum literals like "non-veg" rather than
        # the Python attribute name "non_veg".
        "manglik": rng.choice(["no", "no", "partial", "yes", "unknown"]),
        "education": rng.choice(EDUCATIONS),
        "occupation": rng.choice(OCCUPATIONS),
        # Avoid 'non-veg' — DietEnum has a name/value mismatch
        # (non_veg vs non-veg) that needs values_callable on the column
        # to round-trip cleanly via SQLAlchemy. Other 4 are name=value.
        "diet": rng.choice(["veg", "veg", "eggetarian", "jain", "vegan"]),
        "city": city,
        "state": state,
        "country": "India",
        "about": (
            f"Auto-seeded test profile #{idx}. {first} {last} from {city}, "
            f"working as {rng.choice(OCCUPATIONS)}. "
            f"Looking for a kind and supportive partner."
        ),
        "partner_expectations": (
            "Auto-seeded expectations. Looking for someone with similar values."
        ),
    }


async def main():
    print(f"▶ Seeding {N_USERS} users + profiles + photos + ~{N_REQUESTS} requests…")

    # Status assignment list (shuffled)
    statuses: list[ProfileStatusEnum] = []
    for s, n in STATUS_DIST.items():
        statuses.extend([s] * n)
    while len(statuses) < N_USERS:
        statuses.append(ProfileStatusEnum.draft)
    statuses = statuses[:N_USERS]
    random.Random(7).shuffle(statuses)

    pwd_hash = hash_password("Test1234!")
    run_tag = int(datetime.now(timezone.utc).timestamp())

    async with AsyncSessionLocal() as s:
        users: list[User] = []
        profiles: list[Profile] = []
        photo_count = 0

        for i in range(N_USERS):
            gender = GenderEnum.bride if i % 2 == 0 else GenderEnum.groom
            demo = _profile_demographics(i, gender)
            handle = f"e2e_user_{run_tag}_{i:03d}"
            user = User(
                id=uuid.uuid4(),
                email=f"e2e+{run_tag}_{i}@marathakalyanam.com",
                full_name=f"{demo['first_name']} {demo['last_name']}",
                user_handle=handle,
                phone_number=f"+91900{(run_tag % 100000):05d}{i % 1000:03d}",
                password_hash=pwd_hash,
                email_verified=True,
                is_approved=True,
                email_verification_token=None,
                is_admin=False,
            )
            users.append(user)
            s.add(user)

        await s.flush()

        for i, user in enumerate(users):
            gender = GenderEnum.bride if i % 2 == 0 else GenderEnum.groom
            demo = _profile_demographics(i, gender)
            profile = Profile(
                id=uuid.uuid4(),
                profile_number=f"Z{run_tag % 1000:03d}{i:04d}",  # 8 chars, fits VARCHAR(9)
                owner_user_id=user.id,
                gender=gender,
                status=statuses[i],
                **demo,
            )
            profiles.append(profile)
            s.add(profile)

        await s.flush()

        # Photos — 1..3 per profile, first one is primary
        for i, profile in enumerate(profiles):
            n = random.Random(i + 999).randint(*PHOTOS_PER_PROFILE_RANGE)
            for j in range(n):
                photo_id = uuid.uuid4()
                pdir = MEDIA_ROOT / "profiles" / str(profile.id) / str(photo_id)
                pdir.mkdir(parents=True, exist_ok=True)
                seed = i * 100 + j
                pname = f"{profile.first_name} {profile.last_name} #{j}"
                passport = _generate_passport(pname, i, seed)
                blurred = _generate_blurred(passport)
                thumb = _generate_thumb(passport)
                (pdir / "passport.jpg").write_bytes(passport)
                (pdir / "blurred.jpg").write_bytes(blurred)
                (pdir / "thumb.jpg").write_bytes(thumb)

                photo = Photo(
                    id=photo_id,
                    profile_id=profile.id,
                    original_filename=f"e2e_{i}_{j}.jpg",
                    passport_path=f"profiles/{profile.id}/{photo_id}/passport.jpg",
                    blurred_path=f"profiles/{profile.id}/{photo_id}/blurred.jpg",
                    thumb_path=f"profiles/{profile.id}/{photo_id}/thumb.jpg",
                    byte_size=len(passport),
                    is_primary=(j == 0),
                )
                s.add(photo)
                photo_count += 1

        await s.flush()

        # Detail requests — random pairs of (requester user, approved profile)
        approved_profiles = [p for p in profiles if p.status == ProfileStatusEnum.approved]
        request_status_dist = (
            [RequestStatusEnum.approved] * 12
            + [RequestStatusEnum.pending] * 13
            + [RequestStatusEnum.rejected] * 10
        )
        random.Random(11).shuffle(request_status_dist)

        used_pairs: set[tuple[uuid.UUID, uuid.UUID]] = set()
        rng = random.Random(13)
        n_made = 0
        attempts = 0
        while n_made < N_REQUESTS and attempts < N_REQUESTS * 5 and approved_profiles:
            attempts += 1
            requester = rng.choice(users)
            target = rng.choice(approved_profiles)
            if requester.id == target.owner_user_id:
                continue
            key = (requester.id, target.id)
            if key in used_pairs:
                continue
            used_pairs.add(key)
            status = request_status_dist[n_made % len(request_status_dist)]
            req = DetailRequest(
                id=uuid.uuid4(),
                requester_user_id=requester.id,
                profile_id=target.id,
                status=status,
                message=f"Auto-seeded request #{n_made}",
                admin_notes=("auto-test reject" if status == RequestStatusEnum.rejected else None),
                responded_at=(datetime.now(timezone.utc)
                              if status != RequestStatusEnum.pending else None),
            )
            s.add(req)
            n_made += 1

        await s.commit()

        # Summary
        print(f"  users     : {len(users)}")
        print(f"  profiles  : {len(profiles)}  "
              + ", ".join(f"{k.value}={v}" for k, v in STATUS_DIST.items()))
        print(f"  photos    : {photo_count}")
        print(f"  requests  : {n_made}")

        # Quick sanity: count via SQL
        r = await s.execute(text(
            "SELECT 'users' AS t, count(*) FROM users WHERE user_handle LIKE 'e2e_%' "
            "UNION ALL SELECT 'profiles', count(*) FROM profiles "
            "WHERE owner_user_id IN (SELECT id FROM users WHERE user_handle LIKE 'e2e_%') "
            "UNION ALL SELECT 'photos', count(*) FROM photos "
            "WHERE profile_id IN (SELECT id FROM profiles WHERE owner_user_id "
            "IN (SELECT id FROM users WHERE user_handle LIKE 'e2e_%')) "
            "UNION ALL SELECT 'requests', count(*) FROM detail_requests "
            "WHERE requester_user_id IN (SELECT id FROM users WHERE user_handle LIKE 'e2e_%')"
        ))
        print("\nDB sanity:")
        for row in r.all():
            print(f"  {row[0]:10s}: {row[1]}")

        print(f"\nLogin (any seeded user):  user_id e2e_user_{run_tag}_000  password Test1234!")
        print("Cleanup later: DELETE FROM users WHERE user_handle LIKE 'e2e_%';")


if __name__ == "__main__":
    asyncio.run(main())
