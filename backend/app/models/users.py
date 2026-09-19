from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.orm import relationship as sa_relationship
from app.core.database import Base
from app.models.base import generate_uuid, utc_now, TimestampMixin


class User(Base, TimestampMixin):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    google_uid = Column(String(128), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    locale = Column(String(10), default="en", nullable=False)

    profiles = sa_relationship("Profile", back_populates="user", cascade="all, delete-orphan")
    consents = sa_relationship("Consent", back_populates="user", cascade="all, delete-orphan")
    audit_logs = sa_relationship("AuditLog", back_populates="user", cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    relationship_type = Column("relationship", String(50), default="self", nullable=False) # e.g. "self", "father", "mother"
    dob = Column(String(20), nullable=True)

    user = sa_relationship("User", back_populates="profiles")
    prescriptions = sa_relationship("Prescription", back_populates="profile", cascade="all, delete-orphan")
    medications = sa_relationship("Medication", back_populates="profile", cascade="all, delete-orphan")


class Consent(Base):
    __tablename__ = "consents"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    purpose = Column(String(255), nullable=False)
    granted_at = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    withdrawn_at = Column(DateTime(timezone=True), nullable=True)

    user = sa_relationship("User", back_populates="consents")

