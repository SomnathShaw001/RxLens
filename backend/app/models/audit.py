from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from app.models.base import generate_uuid, utc_now


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    action = Column(String(100), nullable=False) # e.g. "view_prescription", "edit_field", "delete_user"
    entity = Column(String(100), nullable=False)
    timestamp = Column(DateTime(timezone=True), default=utc_now, nullable=False)
    ip = Column(String(45), nullable=True)

    user = relationship("User", back_populates="audit_logs")
