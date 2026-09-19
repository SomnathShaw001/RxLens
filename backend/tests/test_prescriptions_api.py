import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_drug_alternatives_endpoint(client: AsyncClient):
    response = await client.get("/v1/drugs/Crocin/alternatives")
    assert response.status_code == 200
    data = response.json()
    assert data["salt"] == "Paracetamol"
    assert "disclaimer" in data
    assert len(data["jan_aushadhi"]) > 0


@pytest.mark.asyncio
async def test_ingest_and_correct_pipeline(client: AsyncClient):
    # 1. Ingest prescription
    ingest_res = await client.post(
        "/v1/prescriptions/ingest",
        data={"lang_hint": "en", "is_handwritten": "true"},
    )
    assert ingest_res.status_code == 202
    job_id = ingest_res.json()["job_id"]
    assert job_id is not None

    # 2. Query status
    status_res = await client.get(f"/v1/prescriptions/{job_id}")
    assert status_res.status_code == 200
    data = status_res.json()
    assert data["prescription_id"] == job_id
    assert "status" in data

    # 3. Apply human correction
    correct_res = await client.post(
        f"/v1/prescriptions/{job_id}/correct",
        json={"field": "medication", "corrected_value": "Crocin 650mg 1 tablet TDS"},
    )
    assert correct_res.status_code == 200
    assert correct_res.json()["updated"] is True
