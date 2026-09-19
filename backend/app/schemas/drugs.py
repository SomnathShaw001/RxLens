from typing import List, Optional
from pydantic import BaseModel


class GenericDrugItem(BaseModel):
    brand_or_name: str
    salt: str
    rxcui: Optional[str] = None
    price_estimate: Optional[str] = None
    is_jan_aushadhi: bool = False


class AlternativesResponse(BaseModel):
    rxcui: Optional[str] = None
    searched_drug: str
    salt: str
    purpose: Optional[str] = None
    generics: List[GenericDrugItem] = []
    jan_aushadhi: List[GenericDrugItem] = []
    disclaimer: str = (
        "This app provides information only. It is not medical advice. "
        "Always confirm with your doctor or pharmacist. Do not change or substitute any medicine on your own."
    )
