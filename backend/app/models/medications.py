from sqlalchemy import Column, String, Boolean, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, utc_now


class Medication(Base):
    __tablename__ = "medications"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    profile_id = Column(String(36), ForeignKey("profiles.id", ondelete="CASCADE"), nullable=False, index=True)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id", ondelete="SET NULL"), nullable=True)
    drug_name = Column(String(255), nullable=False)
    rxcui = Column(String(50), nullable=True)
    salt = Column(String(255), nullable=True)
    strength = Column(String(50), nullable=True)
    dose = Column(String(50), nullable=True)
    frequency = Column(String(100), nullable=True)
    duration = Column(String(50), nullable=True)
    route = Column(String(50), nullable=True)

    profile = relationship("Profile", back_populates="medications")
    prescription = relationship("Prescription", back_populates="medications")
    reminders = relationship("Reminder", back_populates="medication", cascade="all, delete-orphan")
    adherence_logs = relationship("AdherenceLog", back_populates="medication", cascade="all, delete-orphan")


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    medication_id = Column(String(36), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True)
    schedule_cron = Column(String(50), nullable=False) # e.g. "0 9,21 * * *"
    next_at = Column(DateTime(timezone=True), nullable=True)
    active = Column(Boolean, default=True, nullable=False)

    medication = relationship("Medication", back_populates="reminders")


class AdherenceLog(Base):
    __tablename__ = "adherence_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    medication_id = Column(String(36), ForeignKey("medications.id", ondelete="CASCADE"), nullable=False, index=True)
    taken_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    status = Column(String(30), nullable=False) # taken, missed, skipped

    medication = relationship("Medication", back_populates="adherence_logs")
