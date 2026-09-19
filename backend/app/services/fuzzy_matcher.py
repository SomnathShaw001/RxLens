from typing import Optional, Dict, Any, Tuple
from rapidfuzz import process, fuzz


class FuzzyDrugMatcher:
    """
    RapidFuzz drug matcher normalized against common Indian Brands and RxNorm generics.
    Handles OCR misspellings (e.g. 'crocim' -> 'Crocin').
    """

    # Reference database bootstrapped with common Indian prescription drugs and salts
    DEFAULT_DRUG_DATABASE = [
        {
            "brand": "Crocin",
            "salt": "Paracetamol",
            "rxcui": "161",
            "strengths": ["500 mg", "650 mg", "120 mg/5ml"],
            "purpose": "Analgesic and antipyretic for pain and fever relief"
        },
        {
            "brand": "Calpol",
            "salt": "Paracetamol",
            "rxcui": "161",
            "strengths": ["500 mg", "650 mg", "250 mg/5ml"],
            "purpose": "Fever and mild to moderate pain relief"
        },
        {
            "brand": "Dolo",
            "salt": "Paracetamol",
            "rxcui": "161",
            "strengths": ["650 mg"],
            "purpose": "High fever and pain management"
        },
        {
            "brand": "Augmentin",
            "salt": "Amoxicillin and Clavulanate Potassium",
            "rxcui": "617314",
            "strengths": ["625 mg", "375 mg", "1000 mg"],
            "purpose": "Broad-spectrum antibacterial for bacterial infections"
        },
        {
            "brand": "Azee",
            "salt": "Azithromycin",
            "rxcui": "18631",
            "strengths": ["250 mg", "500 mg"],
            "purpose": "Macrolide antibiotic for respiratory and skin infections"
        },
        {
            "brand": "Glycomet",
            "salt": "Metformin Hydrochloride",
            "rxcui": "6809",
            "strengths": ["500 mg", "850 mg", "1000 mg"],
            "purpose": "Oral antidiabetic for type 2 diabetes management"
        },
        {
            "brand": "Pan",
            "salt": "Pantoprazole",
            "rxcui": "40790",
            "strengths": ["40 mg", "20 mg"],
            "purpose": "Proton pump inhibitor for acid reflux and peptic ulcers"
        },
        {
            "brand": "Telma",
            "salt": "Telmisartan",
            "rxcui": "72299",
            "strengths": ["20 mg", "40 mg", "80 mg"],
            "purpose": "Antihypertensive for high blood pressure and cardiovascular risk"
        },
        {
            "brand": "Montair-LC",
            "salt": "Montelukast and Levocetirizine",
            "rxcui": "855324",
            "strengths": ["10 mg / 5 mg"],
            "purpose": "Antihistamine and leukotriene receptor antagonist for allergic rhinitis and asthma"
        },
        {
            "brand": "Shelcal",
            "salt": "Calcium and Vitamin D3",
            "rxcui": "203173",
            "strengths": ["500 mg"],
            "purpose": "Nutritional supplement for bone density and calcium deficiency"
        }
    ]

    def __init__(self, drug_records: Optional[list[dict]] = None):
        self.drugs = drug_records or self.DEFAULT_DRUG_DATABASE
        # Map brand lowercase to item
        self.brand_names = [d["brand"] for d in self.drugs]

    def match_drug(self, raw_input_name: str, score_cutoff: float = 60.0) -> Tuple[Optional[Dict[str, Any]], float]:
        """
        Finds the closest matching drug brand or salt using RapidFuzz.
        Returns: (matched_record, similarity_ratio_0_to_1)
        """
        if not raw_input_name or not raw_input_name.strip():
            return None, 0.0

        cleaned = raw_input_name.strip()
        match = process.extractOne(
            cleaned,
            self.brand_names,
            scorer=fuzz.ratio,
            processor=lambda s: s.lower().strip(),
            score_cutoff=score_cutoff
        )

        if match:
            matched_name, score, index = match
            matched_record = self.drugs[index]
            similarity_fraction = score / 100.0
            return matched_record, similarity_fraction

        return None, 0.0

    def validate_drug_and_strength(self, matched_drug: Optional[Dict[str, Any]], extracted_strength: Optional[str]) -> bool:
        """
        Validates whether the extracted strength is known for this drug.
        Prevents dangerous hallucinations (e.g. Ciprofloxacin 500mg read as 30mg).
        """
        if not matched_drug:
            return False

        if not extracted_strength or not extracted_strength.strip():
            # If no strength extracted, it cannot be verified
            return False

        known_strengths = matched_drug.get("strengths", [])
        cleaned_strength = extracted_strength.lower().replace(" ", "")

        for valid_s in known_strengths:
            if valid_s.lower().replace(" ", "") in cleaned_strength or cleaned_strength in valid_s.lower().replace(" ", ""):
                return True

        return False
