from typing import Dict, Any, List, Optional
from app.services.fuzzy_matcher import FuzzyDrugMatcher


class DrugKnowledgeService:
    """
    Drug Knowledge Service implementing Brand to Alternatives flow (TRD Section 13.1):
    1. Read drug name from OCR.
    2. Fuzzy-match against RxNorm and Indian brand list.
    3. Retrieve the salt and RxCUI.
    4. Intersect with generic products and Jan Aushadhi generic availability.
    5. Return purpose, indication, disclaimer.
    """

    # Extended Jan Aushadhi generic catalogue sample
    JAN_AUSHADHI_CATALOGUE = {
        "Paracetamol": [
            {"brand_or_name": "Paracetamol Tablet IP 500mg", "price_estimate": "₹ 9.50 per strip of 10", "is_jan_aushadhi": True},
            {"brand_or_name": "Paracetamol Tablet IP 650mg", "price_estimate": "₹ 14.00 per strip of 10", "is_jan_aushadhi": True},
        ],
        "Amoxicillin and Clavulanate Potassium": [
            {"brand_or_name": "Amoxycillin and Potassium Clavulanate Tablets IP 625mg", "price_estimate": "₹ 55.00 per strip of 6", "is_jan_aushadhi": True},
        ],
        "Azithromycin": [
            {"brand_or_name": "Azithromycin Tablets IP 500mg", "price_estimate": "₹ 38.00 per strip of 3", "is_jan_aushadhi": True},
        ],
        "Metformin Hydrochloride": [
            {"brand_or_name": "Metformin Hydrochloride Sustained Release Tablets IP 500mg", "price_estimate": "₹ 11.20 per strip of 10", "is_jan_aushadhi": True},
        ],
        "Pantoprazole": [
            {"brand_or_name": "Pantoprazole Gastro-resistant Tablets IP 40mg", "price_estimate": "₹ 16.50 per strip of 10", "is_jan_aushadhi": True},
        ],
        "Telmisartan": [
            {"brand_or_name": "Telmisartan Tablets IP 40mg", "price_estimate": "₹ 15.00 per strip of 10", "is_jan_aushadhi": True},
        ],
    }

    def __init__(self):
        self.matcher = FuzzyDrugMatcher()

    def get_alternatives(self, drug_name_or_rxcui: str) -> Dict[str, Any]:
        """
        Resolves brand to generic salt and retrieves Jan Aushadhi price-saving alternatives.
        """
        matched_drug, ratio = self.matcher.match_drug(drug_name_or_rxcui, score_cutoff=50.0)

        if not matched_drug:
            return {
                "searched_drug": drug_name_or_rxcui,
                "rxcui": None,
                "salt": "Unknown Salt",
                "purpose": "Consult your doctor or pharmacist for details about this medication.",
                "generics": [],
                "jan_aushadhi": [],
                "disclaimer": (
                    "This app provides information only. It is not medical advice. "
                    "Always confirm with your doctor or pharmacist. Do not change or substitute any medicine on your own."
                )
            }

        salt = matched_drug["salt"]
        rxcui = matched_drug["rxcui"]
        purpose = matched_drug.get("purpose", "Therapeutic medication.")

        # Jan Aushadhi matches
        jan_aushadhi_items = []
        for known_salt, items in self.JAN_AUSHADHI_CATALOGUE.items():
            if known_salt.lower() in salt.lower() or salt.lower() in known_salt.lower():
                for it in items:
                    jan_aushadhi_items.append({
                        "brand_or_name": it["brand_or_name"],
                        "salt": salt,
                        "rxcui": rxcui,
                        "price_estimate": it["price_estimate"],
                        "is_jan_aushadhi": True
                    })

        # Generic equivalents
        generics = [
            {
                "brand_or_name": f"{salt} Generic formulation",
                "salt": salt,
                "rxcui": rxcui,
                "price_estimate": "50-80% cheaper than branded equivalent",
                "is_jan_aushadhi": False
            }
        ]

        return {
            "searched_drug": drug_name_or_rxcui,
            "rxcui": rxcui,
            "salt": salt,
            "purpose": purpose,
            "generics": generics,
            "jan_aushadhi": jan_aushadhi_items,
            "disclaimer": (
                "This app provides information only. It is not medical advice. "
                "Always confirm with your doctor or pharmacist. Do not change or substitute any medicine on your own."
            )
        }
