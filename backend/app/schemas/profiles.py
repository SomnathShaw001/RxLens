from typing import Optional, List
from pydantic import BaseModel


class ProfileCreate(BaseModel):
    user_id: str
    name: str
    relationship_type: str = "self"  # self, father, mother, spouse, child, other
    dob: Optional[str] = None


class ProfileUpdate(BaseModel):
    name: Optional[str] = None
    relationship_type: Optional[str] = None
    dob: Optional[str] = None


class ProfileResponse(BaseModel):
    id: str
    user_id: str
    name: str
    relationship_type: Optional[str] = None
    dob: Optional[str] = None
