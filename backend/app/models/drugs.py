from sqlalchemy import Column, String, Text, UniqueConstraint
from app.core.database import Base
from app.models.base import generate_uuid


class DrugReference(Base):
    __tablename__ = "drug_reference"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    rxcui = Column(String(50), nullable=False, index=True)
    brand = Column(String(255), nullable=False, index=True)
    salt = Column(String(255), nullable=False, index=True)
    atc = Column(String(50), nullable=True)
    purpose = Column(Text, nullable=True)
    source = Column(String(50), default="RxNorm", nullable=False)  # RxNorm, Jan Aushadhi, openFDA

    __table_args__ = (
        UniqueConstraint("rxcui", "brand", name="uq_drug_rxcui_brand"),
    )
