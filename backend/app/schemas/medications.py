from pydantic import BaseModel, Field
from typing import Optional


class MedicationCreate(BaseModel):
    profile_id: str
    prescription_id: Optional[str] = None
    drug_name: str
    rxcui: Optional[str] = None
    salt: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None
    schedule_cron: Optional[str] = None  # Cron expression for reminders, e.g. "0 8 * * *"


class MedicationResponse(BaseModel):
    id: str
    profile_id: str
    prescription_id: Optional[str] = None
    drug_name: str
    salt: Optional[str] = None
    strength: Optional[str] = None
    dose: Optional[str] = None
    frequency: Optional[str] = None
    duration: Optional[str] = None
    route: Optional[str] = None


class AdherenceLogCreate(BaseModel):
    status: str = Field(..., description="taken | missed | skipped")
    taken_at: Optional[str] = None
