"""Tests for profile CRUD and medication adherence tracking."""
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_and_list_profile(client: AsyncClient):
    # First create a user (via auth exchange with mock token)
    auth_res = await client.post(
        "/v1/auth/exchange",
        json={"firebase_id_token": "mock_test_profile_user", "locale": "en"}
    )
    assert auth_res.status_code == 200
    user_id = auth_res.json()["user_id"]

    # Create profile
    res = await client.post("/v1/profiles", json={
        "user_id": user_id,
        "name": "Dad",
        "relationship_type": "father",
        "dob": "1965-03-15",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Dad"
    assert data["relationship_type"] == "father"
    profile_id = data["id"]

    # List profiles
    list_res = await client.get(f"/v1/profiles?user_id={user_id}")
    assert list_res.status_code == 200
    profiles = list_res.json()
    assert any(p["id"] == profile_id for p in profiles)


@pytest.mark.asyncio
async def test_update_profile(client: AsyncClient):
    auth_res = await client.post(
        "/v1/auth/exchange",
        json={"firebase_id_token": "mock_update_profile_user", "locale": "en"}
    )
    user_id = auth_res.json()["user_id"]

    create_res = await client.post("/v1/profiles", json={
        "user_id": user_id,
        "name": "Mom",
        "relationship_type": "mother",
    })
    profile_id = create_res.json()["id"]

    patch_res = await client.patch(f"/v1/profiles/{profile_id}", json={"name": "Mother"})
    assert patch_res.status_code == 200
    assert patch_res.json()["name"] == "Mother"


@pytest.mark.asyncio
async def test_medication_adherence_lifecycle(client: AsyncClient):
    # Create medication
    ingest_res = await client.post(
        "/v1/prescriptions/ingest",
        data={"lang_hint": "en", "is_handwritten": "true"},
    )
    prescription_id = ingest_res.json()["job_id"]

    # Get or create profile_id from the prescription
    status_res = await client.get(f"/v1/prescriptions/{prescription_id}")
    assert status_res.status_code == 200

    auth_res = await client.post(
        "/v1/auth/exchange",
        json={"firebase_id_token": "mock_adh_user", "locale": "en"}
    )
    user_id = auth_res.json()["user_id"]
    profile_res = await client.post("/v1/profiles", json={
        "user_id": user_id, "name": "Self", "relationship_type": "self"
    })
    profile_id = profile_res.json()["id"]

    med_res = await client.post("/v1/medications", json={
        "profile_id": profile_id,
        "drug_name": "Crocin",
        "strength": "500 mg",
        "frequency": "TDS",
        "duration": "5 days",
    })
    assert med_res.status_code == 201
    med_id = med_res.json()["id"]

    # Log adherence
    log_res = await client.post(f"/v1/medications/{med_id}/adherence", json={"status": "taken"})
    assert log_res.status_code == 201
    assert log_res.json()["status"] == "taken"

    # Fetch adherence history
    history_res = await client.get(f"/v1/medications/{med_id}/adherence")
    assert history_res.status_code == 200
    assert len(history_res.json()) >= 1
