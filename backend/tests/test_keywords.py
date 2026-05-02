"""Tests for the keyword extractor and its integration with profile endpoints."""
from __future__ import annotations

import uuid
from typing import Any

import pytest

from app.services.keywords import extract_keywords

pytestmark = pytest.mark.asyncio


# ---------------------------------------------------------------------------
# Unit tests — no database needed
# ---------------------------------------------------------------------------


def test_stopword_filtering() -> None:
    """Common English stopwords must be excluded from the output."""
    result = extract_keywords("I am looking for a good partner who is very kind")
    # 'looking', 'partner', 'who', 'very', 'for', 'a', 'am', 'is' are stopwords
    assert "looking" not in result
    assert "partner" not in result
    assert "who" not in result
    assert "for" not in result
    # 'good' and 'kind' should survive
    assert "good" in result
    assert "kind" in result


def test_punctuation_stripping() -> None:
    """Punctuation must be stripped before tokenising."""
    result = extract_keywords("well-educated, software-engineer! doctor.")
    # Hyphens become spaces → 'well', 'educated', 'software', 'engineer', 'doctor'
    assert "educated" in result
    assert "software" in result
    assert "engineer" in result
    assert "doctor" in result
    # 'well' is a stopword
    assert "well" not in result


def test_dedup_and_length_filter() -> None:
    """Tokens shorter than 3 chars must be dropped; duplicates must be removed."""
    result = extract_keywords("tall tall tall go go fit fit fit")
    # 'go' is 2 chars → dropped; 'tall' and 'fit' kept once each
    assert result.count("tall") == 1
    assert result.count("fit") == 1
    assert "go" not in result


def test_empty_input() -> None:
    """Empty and whitespace-only input must return an empty list."""
    assert extract_keywords("") == []
    assert extract_keywords("   ") == []


def test_long_input_capped_at_50() -> None:
    """Output must never exceed 50 keywords even on very long input."""
    # Generate 200 distinct 5-char words that are not stopwords
    words = [f"word{i:04d}" for i in range(200)]
    text = " ".join(words)
    result = extract_keywords(text)
    assert len(result) <= 50


def test_output_is_sorted() -> None:
    """Output list must be sorted alphabetically."""
    result = extract_keywords("zebra alpha mango banana cricket doctor")
    assert result == sorted(result)


# ---------------------------------------------------------------------------
# HTTP integration tests — require a running test database
# ---------------------------------------------------------------------------


def _sample_profile() -> dict[str, Any]:
    return {
        "gender": "bride",
        "first_name": "Kavya",
        "last_name": "Patil",
        "dob": "1997-03-20",
        "height_cm": 160,
        "complexion": "fair",
        "education": "MBA Finance",
        "occupation": "Banker",
        "city": "Pune",
        "state": "Maharashtra",
        "country": "India",
        "gotra": "Kashyapa",
        "kuldevata": "Bhavani",
        "devak": "Coconut",
        "surname_clan": "Patil",
        "nakshatram": "Uttara",
        "rashi": "Kanya",
        "manglik": "no",
        "mother_tongue": "Marathi",
        "diet": "veg",
        "about": "Friendly and family oriented",
        "partner_expectations": "Looking for educated professional doctor engineer stable",
    }


async def _create_verified_user_and_login(client: Any, db_session: Any) -> tuple[str, str]:
    """Register, verify email in DB, login; return (user_id, email)."""
    from sqlalchemy import select as sa_select
    from app.models.user import User

    email = f"kw_test_{uuid.uuid4().hex[:8]}@example.com"
    password = "ValidPass123!"

    resp = await client.post("/auth/register", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    user_id = resp.json()["user_id"]

    result = await db_session.execute(sa_select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one()
    user.email_verified = True
    await db_session.commit()

    await client.post("/auth/login", json={"email": email, "password": password})
    return user_id, email


async def test_keywords_extracted_on_profile_create(client: Any, db_session: Any) -> None:
    """partner_preference_keywords is populated from partner_expectations on create."""
    await _create_verified_user_and_login(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    assert resp.status_code == 201, resp.text
    data = resp.json()

    keywords = data.get("partner_preference_keywords")
    assert keywords is not None, "partner_preference_keywords should not be None"
    assert isinstance(keywords, list)
    # 'educated' and 'professional' and 'doctor' and 'engineer' and 'stable' are not stopwords
    assert "educated" in keywords
    assert "professional" in keywords
    assert "doctor" in keywords
    assert "engineer" in keywords
    assert "stable" in keywords


async def test_keywords_updated_on_profile_patch(client: Any, db_session: Any) -> None:
    """PATCH with a new partner_expectations recomputes partner_preference_keywords."""
    await _create_verified_user_and_login(client, db_session)

    profile_data = _sample_profile()
    resp = await client.post("/profiles", json=profile_data)
    assert resp.status_code == 201, resp.text
    profile_id = resp.json()["id"]

    patch_resp = await client.patch(
        f"/profiles/{profile_id}",
        json={"partner_expectations": "Seeking calm humble farmer rural background"},
    )
    assert patch_resp.status_code == 200, patch_resp.text
    data = patch_resp.json()

    keywords = data.get("partner_preference_keywords")
    assert keywords is not None
    assert "calm" in keywords
    assert "humble" in keywords
    assert "farmer" in keywords
    assert "rural" in keywords
    assert "background" in keywords
    # Old keywords should not persist
    assert "doctor" not in keywords
    assert "engineer" not in keywords
