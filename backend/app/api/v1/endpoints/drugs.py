from fastapi import APIRouter, HTTPException, status
from app.schemas.drugs import AlternativesResponse
from app.services.drug_knowledge import DrugKnowledgeService
from app.services.openfda import fetch_drug_label_info, get_adverse_event_count
from typing import Optional, Dict, Any

router = APIRouter()
drug_service = DrugKnowledgeService()


@router.get("/{rxcui_or_name}/alternatives", response_model=AlternativesResponse)
async def get_drug_alternatives(rxcui_or_name: str):
    """
    GET /v1/drugs/{rxcui_or_name}/alternatives
    Returns same-salt generic equivalents and Jan Aushadhi generic options.
    Includes mandatory regulatory disclaimer.
    """
    data = drug_service.get_alternatives(rxcui_or_name)
    return AlternativesResponse(**data)


@router.get("/{drug_name}/safety")
async def get_drug_safety_info(drug_name: str) -> Dict[str, Any]:
    """
    GET /v1/drugs/{drug_name}/safety
    Fetches FDA safety label, warnings, contraindications, and adverse events summary.
    Data sourced from openFDA public API.
    """
    label_info = await fetch_drug_label_info(drug_name)
    adverse_count = await get_adverse_event_count(drug_name)

    if not label_info:
        return {
            "drug_name": drug_name,
            "message": f"No FDA label data found for '{drug_name}'. This may be an Indian brand name. Try the generic/salt name.",
            "adverse_event_count": adverse_count,
            "disclaimer": (
                "Data sourced from US FDA openFDA. May not reflect Indian formulations. "
                "Consult your prescribing physician or pharmacist for complete safety information."
            )
        }

    label_info["adverse_event_count"] = adverse_count
    return label_info
