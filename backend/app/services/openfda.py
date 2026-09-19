"""
openFDA Drug Information Service.
Fetches safety information, adverse events, and drug label data from the
US National Library of Medicine openFDA public REST API.
Configured with exponential backoff for resiliency.
"""
import logging
from typing import Dict, Any, Optional
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

logger = logging.getLogger(__name__)

OPENFDA_BASE = "https://api.fda.gov/drug"
OPENFDA_LABEL_URL = f"{OPENFDA_BASE}/label.json"
OPENFDA_EVENT_URL = f"{OPENFDA_BASE}/event.json"


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=8),
    retry=retry_if_exception_type(httpx.HTTPError),
)
async def fetch_drug_label_info(drug_name: str) -> Optional[Dict[str, Any]]:
    """
    Fetches the FDA drug label (prescribing information) for a given drug name.
    Returns a simplified summary dict or None if not found.
    """
    params = {
        "search": f'openfda.brand_name:"{drug_name}" OR openfda.generic_name:"{drug_name}"',
        "limit": 1,
    }
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(OPENFDA_LABEL_URL, params=params)
            if response.status_code == 404:
                return None
            response.raise_for_status()
            data = response.json()
            results = data.get("results", [])
            if not results:
                return None
            label = results[0]
            return {
                "drug_name": drug_name,
                "indications": (label.get("indications_and_usage") or ["Not available"])[0][:500],
                "warnings": (label.get("warnings") or ["Not available"])[0][:500],
                "contraindications": (label.get("contraindications") or ["Not available"])[0][:300],
                "adverse_reactions": (label.get("adverse_reactions") or ["Not available"])[0][:400],
                "dosage_forms": label.get("dosage_forms_and_strengths", ["Not specified"]),
                "storage": (label.get("how_supplied") or ["See packaging"])[0][:200],
                "source": "openFDA Drug Label",
                "disclaimer": (
                    "This information is sourced from the US FDA drug database. "
                    "Dosage and usage patterns may differ for Indian formulations. "
                    "Always follow your prescribing doctor's guidance."
                )
            }
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            logger.warning(f"openFDA request failed for {drug_name}: {e}")
            return None


async def get_adverse_event_count(drug_name: str) -> Optional[int]:
    """Returns the total number of FDA adverse event reports for a drug."""
    params = {
        "search": f'patient.drug.medicinalproduct:"{drug_name}"',
        "count": "patient.reaction.reactionmeddrapt.exact",
        "limit": 1,
    }
    async with httpx.AsyncClient(timeout=8.0) as client:
        try:
            response = await client.get(OPENFDA_EVENT_URL, params=params)
            if response.status_code == 404:
                return 0
            response.raise_for_status()
            data = response.json()
            meta = data.get("meta", {})
            return meta.get("results", {}).get("total", 0)
        except Exception as e:
            logger.warning(f"openFDA adverse event count failed for {drug_name}: {e}")
            return None
