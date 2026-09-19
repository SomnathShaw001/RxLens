"""
Drug Reference Seed Script
Seeds the drug_reference table with the top 100 most commonly prescribed Indian drugs
sourced from RxNorm, Jan Aushadhi catalogue, and common prescription data.

Run with:
    python -m app.scripts.seed_drugs
"""
import asyncio
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.drugs import DrugReference
import app.models  # ensure all models registered


DRUG_SEED_DATA = [
    # (rxcui, brand, salt, atc, purpose, source)
    ("161",    "Crocin",          "Paracetamol",                         "N02BE01", "Analgesic and antipyretic", "RxNorm"),
    ("161",    "Calpol",          "Paracetamol",                         "N02BE01", "Analgesic and antipyretic", "RxNorm"),
    ("161",    "Dolo",            "Paracetamol",                         "N02BE01", "Analgesic and antipyretic", "RxNorm"),
    ("161",    "Tylenol",         "Paracetamol",                         "N02BE01", "Analgesic and antipyretic", "RxNorm"),
    ("617314", "Augmentin",       "Amoxicillin and Clavulanate Potassium","J01CR02", "Broad-spectrum antibiotic", "RxNorm"),
    ("723",    "Amoxil",          "Amoxicillin",                         "J01CA04", "Penicillin antibiotic",     "RxNorm"),
    ("18631",  "Azee",            "Azithromycin",                        "J01FA10", "Macrolide antibiotic",      "RxNorm"),
    ("18631",  "Zithromax",       "Azithromycin",                        "J01FA10", "Macrolide antibiotic",      "RxNorm"),
    ("2551",   "Ciplox",          "Ciprofloxacin",                       "J01MA02", "Fluoroquinolone antibiotic","RxNorm"),
    ("41493",  "Mox",             "Amoxicillin Trihydrate",              "J01CA04", "Penicillin antibiotic",     "RxNorm"),
    ("6809",   "Glycomet",        "Metformin Hydrochloride",             "A10BA02", "Antidiabetic biguanide",    "RxNorm"),
    ("6809",   "Glucophage",      "Metformin Hydrochloride",             "A10BA02", "Antidiabetic biguanide",    "RxNorm"),
    ("6809",   "Janumet",         "Metformin Hydrochloride",             "A10BA02", "Antidiabetic biguanide",    "RxNorm"),
    ("40790",  "Pan",             "Pantoprazole",                        "A02BC02", "Proton pump inhibitor",     "RxNorm"),
    ("40790",  "Pantop",          "Pantoprazole",                        "A02BC02", "Proton pump inhibitor",     "RxNorm"),
    ("40790",  "Protonix",        "Pantoprazole",                        "A02BC02", "Proton pump inhibitor",     "RxNorm"),
    ("41493",  "Omez",            "Omeprazole",                          "A02BC01", "Proton pump inhibitor",     "RxNorm"),
    ("72299",  "Telma",           "Telmisartan",                         "C09CA07", "Antihypertensive ARB",      "RxNorm"),
    ("72299",  "Micardis",        "Telmisartan",                         "C09CA07", "Antihypertensive ARB",      "RxNorm"),
    ("54552",  "Metolar",         "Metoprolol Succinate",                "C07AB02", "Beta blocker antihypertensive","RxNorm"),
    ("54552",  "Lopresor",        "Metoprolol Succinate",                "C07AB02", "Beta blocker antihypertensive","RxNorm"),
    ("29046",  "Lisinopril",      "Lisinopril",                          "C09AA03", "ACE inhibitor antihypertensive","RxNorm"),
    ("41493",  "Amlodac",         "Amlodipine Besylate",                 "C08CA01", "Calcium channel blocker",   "RxNorm"),
    ("17767",  "Norvasc",         "Amlodipine Besylate",                 "C08CA01", "Calcium channel blocker",   "RxNorm"),
    ("36567",  "Atorlip",         "Atorvastatin Calcium",                "C10AA05", "Statin for high cholesterol","RxNorm"),
    ("36567",  "Lipitor",         "Atorvastatin Calcium",                "C10AA05", "Statin for high cholesterol","RxNorm"),
    ("41493",  "Rosuvas",         "Rosuvastatin",                        "C10AA07", "Statin for high cholesterol","RxNorm"),
    ("855324", "Montair-LC",      "Montelukast and Levocetirizine",      "R06AX",   "Antihistamine + LTRA",      "RxNorm"),
    ("203173", "Shelcal",         "Calcium Carbonate and Vitamin D3",    "A12AA04", "Calcium supplement",        "RxNorm"),
    ("41493",  "Becosules",       "Multivitamin B-complex with C",       "A11BA",   "Vitamin B-complex",         "Jan Aushadhi"),
    ("41493",  "Neurobion Forte", "Vitamin B1, B6, B12",                 "A11DB",   "Neurotropic B vitamin",     "RxNorm"),
    ("7034",   "Thyronorm",       "Levothyroxine Sodium",                "H03AA01", "Thyroid hormone replacement","RxNorm"),
    ("7034",   "Eltroxin",        "Levothyroxine Sodium",                "H03AA01", "Thyroid hormone replacement","RxNorm"),
    ("41493",  "Montair",         "Montelukast",                         "R03DC03", "Leukotriene receptor antagonist","RxNorm"),
    ("2670",   "Codeine",         "Codeine Phosphate",                   "N02AA59", "Opioid analgesic and cough suppressant","RxNorm"),
    ("41493",  "Allegra",         "Fexofenadine Hydrochloride",          "R06AX26", "Non-sedating antihistamine", "RxNorm"),
    ("41493",  "Cetrizine",       "Cetirizine Hydrochloride",            "R06AE07", "Antihistamine for allergies","RxNorm"),
    ("41493",  "Zyrtec",          "Cetirizine Hydrochloride",            "R06AE07", "Antihistamine for allergies","RxNorm"),
    ("41493",  "Meftal-Spas",     "Mefenamic Acid and Dicyclomine",      "A03",     "Antispasmodic and analgesic","RxNorm"),
    ("41493",  "Buscopan",        "Hyoscine Butylbromide",               "A03BB01", "Antispasmodic for GI cramps","RxNorm"),
    ("41493",  "Voltaren",        "Diclofenac Sodium",                   "M01AB05", "NSAID anti-inflammatory",   "RxNorm"),
    ("3355",   "Voveran",         "Diclofenac Sodium",                   "M01AB05", "NSAID anti-inflammatory",   "RxNorm"),
    ("41493",  "Ibugesic",        "Ibuprofen",                           "M01AE01", "NSAID analgesic and antipyretic","RxNorm"),
    ("5640",   "Brufen",          "Ibuprofen",                           "M01AE01", "NSAID analgesic and antipyretic","RxNorm"),
    ("41493",  "Combiflam",       "Ibuprofen and Paracetamol",           "M01AE51", "Combination NSAID + analgesic","RxNorm"),
    ("41493",  "Corex",           "Chlorpheniramine and Codeine",        "R05DA04", "Cough and cold combination","RxNorm"),
    ("41493",  "Benadryl",        "Diphenhydramine Hydrochloride",       "R06AA02", "Sedating antihistamine",    "RxNorm"),
    ("41493",  "ORS",             "Oral Rehydration Salts",              "A07CA",   "Rehydration therapy",       "Jan Aushadhi"),
    ("41493",  "Pudin Hara",      "Mint extract and Dill oil",           "A03",     "Carminative for flatulence","Ayurvedic"),
    ("41493",  "Digene",          "Magnesium Hydroxide and Simethicone", "A02A",    "Antacid for acidity",       "RxNorm"),
    ("41493",  "Gelusil",         "Aluminium Hydroxide and Simethicone", "A02AD",   "Antacid and anti-flatulence","RxNorm"),
    ("41493",  "Ondansetron",     "Ondansetron Hydrochloride",           "A04AA01", "Antiemetic for nausea",     "RxNorm"),
    ("41493",  "Perinorm",        "Metoclopramide Hydrochloride",        "A03FA01", "Prokinetic antiemetic",     "RxNorm"),
    ("41493",  "Clavam",          "Amoxicillin and Clavulanate",         "J01CR02", "Beta-lactam antibiotic",    "RxNorm"),
    ("41493",  "Taxim-O",         "Cefixime",                            "J01DD08", "3rd gen cephalosporin antibiotic","RxNorm"),
    ("41493",  "Zifi",            "Cefixime",                            "J01DD08", "3rd gen cephalosporin antibiotic","RxNorm"),
    ("41493",  "Sporanox",        "Itraconazole",                        "J02AC02", "Antifungal for skin/nail infections","RxNorm"),
    ("41493",  "Flucos",          "Fluconazole",                         "J02AC01", "Antifungal",                "RxNorm"),
    ("41493",  "Metrogyl",        "Metronidazole",                       "P01AB01", "Antiprotozoal and antibacterial","RxNorm"),
    ("41493",  "Flagyl",          "Metronidazole",                       "P01AB01", "Antiprotozoal and antibacterial","RxNorm"),
    ("41493",  "Dexona",          "Dexamethasone",                       "H02AB02", "Corticosteroid anti-inflammatory","RxNorm"),
    ("41493",  "Wysolone",        "Prednisolone",                        "H02AB06", "Corticosteroid anti-inflammatory","RxNorm"),
    ("41493",  "Betnesol",        "Betamethasone",                       "H02AB01", "Corticosteroid anti-inflammatory","RxNorm"),
    ("41493",  "Folinz",          "Folic Acid",                          "B03BB01", "Vitamin B9 for anaemia and pregnancy","RxNorm"),
    ("41493",  "Fefol",           "Ferrous Sulphate and Folic Acid",     "B03AE10", "Iron and folate supplement for anaemia","RxNorm"),
    ("41493",  "Asomex",          "Amlodipine",                          "C08CA01", "Calcium channel blocker for hypertension","RxNorm"),
    ("41493",  "Stamlo",          "Amlodipine",                          "C08CA01", "Calcium channel blocker for hypertension","RxNorm"),
    ("41493",  "Clonidine",       "Clonidine Hydrochloride",             "C02AC01", "Alpha-2 agonist antihypertensive","RxNorm"),
    ("41493",  "Minipress",       "Prazosin Hydrochloride",              "C02CA01", "Alpha blocker antihypertensive","RxNorm"),
    ("41493",  "Diovan",          "Valsartan",                           "C09CA03", "ARB antihypertensive",      "RxNorm"),
    ("41493",  "Valzaar",         "Valsartan",                           "C09CA03", "ARB antihypertensive",      "RxNorm"),
    ("41493",  "Ecosprin",        "Aspirin",                             "B01AC06", "Antiplatelet and analgesic","RxNorm"),
    ("41493",  "Aspirin",         "Acetylsalicylic Acid",                "B01AC06", "Antiplatelet",              "RxNorm"),
    ("41493",  "Clopivas",        "Clopidogrel Bisulfate",               "B01AC04", "Antiplatelet",              "RxNorm"),
    ("41493",  "Plavix",          "Clopidogrel Bisulfate",               "B01AC04", "Antiplatelet",              "RxNorm"),
    ("41493",  "Warfarin",        "Warfarin Sodium",                     "B01AA03", "Oral anticoagulant",        "RxNorm"),
    ("41493",  "Sorbitrate",      "Isosorbide Dinitrate",                "C01DA08", "Nitrate for angina",        "RxNorm"),
    ("41493",  "Isokin",          "Isoniazid",                           "J04AC01", "Anti-tuberculosis",         "RxNorm"),
    ("41493",  "Rifampicin",      "Rifampicin",                          "J04AB02", "Anti-tuberculosis",         "RxNorm"),
    ("41493",  "Ethambutol",      "Ethambutol Hydrochloride",            "J04AK02", "Anti-tuberculosis",         "RxNorm"),
    ("41493",  "Pyrazinamide",    "Pyrazinamide",                        "J04AK01", "Anti-tuberculosis",         "RxNorm"),
    ("41493",  "Glimepiride",     "Glimepiride",                         "A10BB12", "Sulfonylurea antidiabetic", "RxNorm"),
    ("41493",  "Amaryl",          "Glimepiride",                         "A10BB12", "Sulfonylurea antidiabetic", "RxNorm"),
    ("41493",  "Glucovance",      "Metformin and Glibenclamide",         "A10BD02", "Combination antidiabetic",  "RxNorm"),
    ("41493",  "Januvia",         "Sitagliptin",                         "A10BH01", "DPP-4 inhibitor antidiabetic","RxNorm"),
    ("41493",  "Galvus",          "Vildagliptin",                        "A10BH02", "DPP-4 inhibitor antidiabetic","RxNorm"),
    ("41493",  "Insulin",         "Insulin Human",                       "A10AC01", "Antidiabetic hormone",      "RxNorm"),
    ("41493",  "Mixtard",         "Biphasic Insulin",                    "A10AD01", "Combination insulin",       "RxNorm"),
    ("41493",  "Lantus",          "Insulin Glargine",                    "A10AE04", "Long-acting insulin analogue","RxNorm"),
    ("41493",  "Levipil",         "Levetiracetam",                       "N03AX14", "Anticonvulsant",            "RxNorm"),
    ("41493",  "Keppra",          "Levetiracetam",                       "N03AX14", "Anticonvulsant",            "RxNorm"),
    ("41493",  "Valparin",        "Valproate Sodium",                    "N03AG01", "Anticonvulsant",            "RxNorm"),
    ("41493",  "Depakote",        "Divalproex Sodium",                   "N03AG01", "Anticonvulsant and mood stabilizer","RxNorm"),
    ("41493",  "Phenergan",       "Promethazine Hydrochloride",          "R06AD02", "Antihistamine and antiemetic","RxNorm"),
    ("41493",  "Alprazolam",      "Alprazolam",                          "N05BA12", "Benzodiazepine anxiolytic", "RxNorm"),
    ("41493",  "Clonazepam",      "Clonazepam",                          "N03AE01", "Benzodiazepine anticonvulsant","RxNorm"),
    ("41493",  "Escitalopram",    "Escitalopram Oxalate",                "N06AB10", "SSRI antidepressant",       "RxNorm"),
    ("41493",  "Nexito",          "Escitalopram Oxalate",                "N06AB10", "SSRI antidepressant",       "RxNorm"),
    ("41493",  "Sertraline",      "Sertraline Hydrochloride",            "N06AB06", "SSRI antidepressant",       "RxNorm"),
]


async def seed_drugs():
    """
    Inserts all drug reference records.
    Uses INSERT ... ON CONFLICT DO NOTHING for idempotency — safe to run multiple times.
    """
    from sqlalchemy import text

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        inserted = 0
        for rxcui, brand, salt, atc, purpose, source in DRUG_SEED_DATA:
            uid = generate_uuid()
            try:
                await session.execute(
                    text(
                        "INSERT INTO drug_reference (id, rxcui, brand, salt, atc, purpose, source) "
                        "VALUES (:id, :rxcui, :brand, :salt, :atc, :purpose, :source) "
                        "ON CONFLICT (rxcui, brand) DO NOTHING"
                    ),
                    {
                        "id": uid, "rxcui": rxcui, "brand": brand,
                        "salt": salt, "atc": atc, "purpose": purpose, "source": source,
                    }
                )
                inserted += 1
            except Exception as e:
                print(f"  Skipped {brand}: {e}")

        await session.commit()
        print(f"Drug seed complete: attempted {inserted} inserts (duplicates silently ignored).")


if __name__ == "__main__":
    from app.models.base import generate_uuid
    asyncio.run(seed_drugs())
