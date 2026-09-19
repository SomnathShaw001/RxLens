from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.medications import Medication, Reminder, AdherenceLog
from app.schemas.medications import MedicationCreate, MedicationResponse, AdherenceLogCreate

router = APIRouter()


@router.post("", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    payload: MedicationCreate,
    db: AsyncSession = Depends(get_db),
):
    """POST /v1/medications — Add a medication to the patient profile."""
    medication = Medication(
        profile_id=payload.profile_id,
        prescription_id=payload.prescription_id,
        drug_name=payload.drug_name,
        rxcui=payload.rxcui,
        salt=payload.salt,
        strength=payload.strength,
        dose=payload.dose,
        frequency=payload.frequency,
        duration=payload.duration,
        route=payload.route,
    )
    db.add(medication)
    await db.flush()

    if payload.schedule_cron:
        reminder = Reminder(
            medication_id=medication.id,
            schedule_cron=payload.schedule_cron,
            active=True
        )
        db.add(reminder)

    await db.commit()
    await db.refresh(medication)

    return MedicationResponse(
        id=medication.id,
        profile_id=medication.profile_id,
        prescription_id=medication.prescription_id,
        drug_name=medication.drug_name,
        salt=medication.salt,
        strength=medication.strength,
        dose=medication.dose,
        frequency=medication.frequency,
        duration=medication.duration,
        route=medication.route,
    )


@router.get("", response_model=List[MedicationResponse])
async def list_medications(
    profile_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """GET /v1/medications?profile_id=... — Lists medications for the patient."""
    query = select(Medication)
    if profile_id:
        query = query.where(Medication.profile_id == profile_id)
    result = await db.execute(query)
    medications = result.scalars().all()
    return [
        MedicationResponse(
            id=m.id, profile_id=m.profile_id, prescription_id=m.prescription_id,
            drug_name=m.drug_name, salt=m.salt, strength=m.strength,
            dose=m.dose, frequency=m.frequency, duration=m.duration, route=m.route,
        )
        for m in medications
    ]


@router.get("/{medication_id}", response_model=MedicationResponse)
async def get_medication(medication_id: str, db: AsyncSession = Depends(get_db)):
    """GET /v1/medications/{medication_id}"""
    result = await db.execute(select(Medication).where(Medication.id == medication_id))
    med = result.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    return MedicationResponse(
        id=med.id, profile_id=med.profile_id, prescription_id=med.prescription_id,
        drug_name=med.drug_name, salt=med.salt, strength=med.strength,
        dose=med.dose, frequency=med.frequency, duration=med.duration, route=med.route,
    )


@router.delete("/{medication_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(medication_id: str, db: AsyncSession = Depends(get_db)):
    """DELETE /v1/medications/{medication_id}"""
    result = await db.execute(select(Medication).where(Medication.id == medication_id))
    med = result.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")
    await db.delete(med)
    await db.commit()
    return None


# ─── Adherence Tracking ───────────────────────────────────────────────────────

@router.post("/{medication_id}/adherence", status_code=status.HTTP_201_CREATED)
async def log_adherence(
    medication_id: str,
    payload: AdherenceLogCreate,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /v1/medications/{medication_id}/adherence
    Logs a medication dose taken, missed, or skipped.
    """
    med_res = await db.execute(select(Medication).where(Medication.id == medication_id))
    med = med_res.scalar_one_or_none()
    if not med:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Medication not found")

    log = AdherenceLog(
        medication_id=medication_id,
        status=payload.status,
        taken_at=payload.taken_at or datetime.now(timezone.utc),
    )
    db.add(log)
    await db.commit()
    await db.refresh(log)

    return {
        "id": log.id,
        "medication_id": log.medication_id,
        "status": log.status,
        "taken_at": log.taken_at.isoformat(),
    }


@router.get("/{medication_id}/adherence")
async def get_adherence_logs(
    medication_id: str,
    db: AsyncSession = Depends(get_db),
):
    """GET /v1/medications/{medication_id}/adherence — Retrieves adherence history."""
    result = await db.execute(
        select(AdherenceLog)
        .where(AdherenceLog.medication_id == medication_id)
        .order_by(AdherenceLog.taken_at.desc())
    )
    logs = result.scalars().all()
    return [
        {
            "id": log.id,
            "medication_id": log.medication_id,
            "status": log.status,
            "taken_at": log.taken_at.isoformat() if log.taken_at else None,
        }
        for log in logs
    ]
