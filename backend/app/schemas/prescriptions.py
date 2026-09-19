from typing import List, Optional, Any
from pydantic import BaseModel, Field


class IngestRequest(BaseModel):
    image_id: Optional[str] = None
    lang_hint: Optional[str] = "en"
    is_handwritten: bool = True
    profile_id: Optional[str] = None


class IngestResponse(BaseModel):
    job_id: str
    status: str = "pending"
    message: str = "Prescription queued for processing"


class PrescriptionFieldSchema(BaseModel):
    name: str # e.g. "drug_name", "strength", "dosage", "frequency", "duration", "route"
    value: Optional[str] = None
    raw_text: Optional[str] = None
    translated_text: Optional[str] = None
    confidence: float
    bbox: Optional[List[float]] = None
    verified: bool = False
    needs_review: bool = False


class PrescriptionStatusResponse(BaseModel):
    prescription_id: str
    status: str # "pending", "processing", "completed", "failed"
    overall_confidence: Optional[float] = None
    needs_review: bool = False
    translation: Optional[str] = None
    fields: List[PrescriptionFieldSchema] = []
    error: Optional[str] = None


class CorrectFieldRequest(BaseModel):
    field: str # name of field to correct, e.g. "drug_name" or field ID
    corrected_value: str


class CorrectFieldResponse(BaseModel):
    updated: bool = True
    prescription_id: str
    field: str
    value: str
