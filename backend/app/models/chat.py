from sqlalchemy import Column, String, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship as sa_relationship
from app.core.database import Base
from app.models.base import generate_uuid, TimestampMixin

try:
    from pgvector.sqlalchemy import Vector
    _pgvector_available = True
except ImportError:
    _pgvector_available = False


class ChatMessage(Base, TimestampMixin):
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    prescription_id = Column(String(36), ForeignKey("prescriptions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # "user" or "assistant"
    content = Column(Text, nullable=False)
    # pgvector 768-dim embedding for semantic retrieval (Gemini text-embedding-004)
    embedding = Column(Vector(768), nullable=True) if _pgvector_available else Column(Text, nullable=True)

    prescription = sa_relationship("Prescription", back_populates="chat_messages")
