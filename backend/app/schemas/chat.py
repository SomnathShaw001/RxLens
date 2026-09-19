from typing import List, Optional
from pydantic import BaseModel


class ChatRequest(BaseModel):
    prescription_id: str
    message: str


class ChatResponse(BaseModel):
    answer: str
    sources: List[str] = []
    disclaimer: str = (
        "This app provides information only. It is not medical advice. "
        "Always confirm with your doctor or pharmacist. Do not change or substitute any medicine on your own."
    )
