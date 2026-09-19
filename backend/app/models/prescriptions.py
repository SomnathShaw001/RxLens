from sqlalchemy import Column, String, Float, Boolean, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin


class Prescription(Base, TimestampMixin):
    __tablename__ = "prescriptions"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    image_url = Column(Text, nullable=False)
    status = Column(String(30), default="processing", nullable=False) # pending, processing, completed, failed
    overall_confidence = Column(Float, nullable=True)
    needs_review = Column(Boolean, default=False, nullable=False)

    profile = relationship("Profile", back_populates="prescriptions")
    fields = relationship("PrescriptionField", back_populates="prescription", cascade="all, delete-orphan")
    medications = relationship("Medication", back_populates="prescription", cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="prescription", cascade="all, delete-orphan")


class PrescriptionField(Base):
    __tablename__ = "prescription_fields"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    type = Column(String(50), nullable=False) # e.g. drug_name, strength, dosage, frequency, duration, route
    raw_text = Column(Text, nullable=True)
    translated_text = Column(Text, nullable=True)
    value = Column(Text, nullable=True)
    confidence = Column(Float, nullable=False, default=0.0)
    bbox = Column(JSON, nullable=True) # [ymin, xmin, ymax, xmax] or polygon
    verified = Column(Boolean, default=False, nullable=False)

    prescription = relationship("Prescription", back_populates="fields")
