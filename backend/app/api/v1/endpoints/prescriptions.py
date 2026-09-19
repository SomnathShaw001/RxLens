from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, List
from app.core.database import get_db
from app.models.prescriptions import Prescription, PrescriptionField
from app.models.users import Profile, User
from app.schemas.prescriptions import (
    IngestResponse,
    PrescriptionStatusResponse,
    PrescriptionFieldSchema,
    CorrectFieldRequest,
    CorrectFieldResponse,
)
from app.services.storage import StorageService
from app.workers.ocr_worker import process_prescription_job

router = APIRouter()


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_prescription(
    background_tasks: BackgroundTasks,
    file: Optional[UploadFile] = File(None),
    lang_hint: str = Form("en"),
    is_handwritten: bool = Form(True),
    profile_id: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
):
    """
    POST /v1/prescriptions/ingest
    Enqueues prescription processing job. Returns 202 Accepted with job_id.
    """
    # Verify or create a default dev profile if not provided
    if not profile_id:
        result = await db.execute(select(Profile).limit(1))
        existing_profile = result.scalar_one_or_none()
        if not existing_profile:
            # Create a bootstrap user and profile
            user = User(google_uid="demo_user_001", email="user@example.com")
            db.add(user)
            await db.flush()
            existing_profile = Profile(user_id=user.id, name="Primary User", relationship_type="self")
            db.add(existing_profile)
            await db.commit()
            await db.refresh(existing_profile)
        profile_id = existing_profile.id

    # Handle image upload
    if file:
        file_id, image_path = await StorageService.save_upload_file(file)
    else:
        # Create a placeholder demo image path for testing
        StorageService.ensure_local_dir()
        file_id = "demo_prescription"
        image_path = "uploads/demo_prescription.jpg"

    # Create prescription record in pending state
    prescription = Prescription(
        profile_id=profile_id,
        image_url=image_path,
        status="pending",
    )
    db.add(prescription)
    await db.commit()
    await db.refresh(prescription)

    # Dispatch to background task
    background_tasks.add_task(
        process_prescription_job,
        prescription_id=prescription.id,
        image_path=image_path,
        lang_hint=lang_hint,
        is_handwritten=is_handwritten,
    )

    return IngestResponse(
        job_id=prescription.id,
        status="pending",
        message="Prescription ingestion job enqueued successfully"
    )


@router.get("/{job_id}", response_model=PrescriptionStatusResponse)
async def get_prescription_status(
    job_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    GET /v1/prescriptions/{job_id}
    Retrieves the status, extracted fields, confidence scores, and review flags.
    """
    result = await db.execute(
        select(Prescription).where(Prescription.id == job_id)
    )
    prescription = result.scalar_one_or_none()
    if not prescription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Prescription with job_id {job_id} not found",
        )

    # Fetch fields
    fields_result = await db.execute(
        select(PrescriptionField).where(PrescriptionField.prescription_id == job_id)
    )
    fields = fields_result.scalars().all()

    field_schemas = [
        PrescriptionFieldSchema(
            name=f.type,
            value=f.value,
            raw_text=f.raw_text,
            translated_text=f.translated_text,
            confidence=f.confidence,
            bbox=f.bbox if isinstance(f.bbox, list) else None,
            verified=f.verified,
            needs_review=not f.verified,
        )
        for f in fields
    ]

    return PrescriptionStatusResponse(
        prescription_id=prescription.id,
        status=prescription.status,
        overall_confidence=prescription.overall_confidence,
        needs_review=prescription.needs_review,
        fields=field_schemas,
    )


@router.post("/{prescription_id}/correct", response_model=CorrectFieldResponse)
async def correct_prescription_field(
    prescription_id: str,
    payload: CorrectFieldRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    POST /v1/prescriptions/{id}/correct
    Applies human-in-the-loop correction and marks the field as verified.
    """
    result = await db.execute(
        select(PrescriptionField).where(
            PrescriptionField.prescription_id == prescription_id,
            (PrescriptionField.type == payload.field) | (PrescriptionField.id == payload.field),
        )
    )
    field = result.scalar_one_or_none()

    if not field:
        # Create field if correcting a new attribute
        field = PrescriptionField(
            prescription_id=prescription_id,
            type=payload.field,
            value=payload.corrected_value,
            confidence=100.0,
            verified=True
        )
        db.add(field)
    else:
        field.value = payload.corrected_value
        field.verified = True
        field.confidence = 100.0

    # Check if any remaining fields in prescription still need review
    await db.flush()
    unverified = await db.execute(
        select(PrescriptionField).where(
            PrescriptionField.prescription_id == prescription_id,
            PrescriptionField.verified == False
        )
    )
    has_unverified = unverified.scalar_one_or_none() is not None

    rx_res = await db.execute(
        select(Prescription).where(Prescription.id == prescription_id)
    )
    rx = rx_res.scalar_one_or_none()
    if rx:
        rx.needs_review = has_unverified

    await db.commit()

    return CorrectFieldResponse(
        updated=True,
        prescription_id=prescription_id,
        field=payload.field,
        value=payload.corrected_value,
    )
