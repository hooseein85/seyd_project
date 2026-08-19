import uuid
from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Policy(Base):
    __tablename__ = "policy"
    __table_args__ = {"schema": "core"} # <--- این خط باید اضافه شود

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    fingerprint = Column(String(255), nullable=False, unique=True, index=True)
    import_batch_id = Column(String(255), nullable=True)
    code = Column(String(255), nullable=True, index=True)
    title = Column(String(255), nullable=True)
    severity = Column(String(100), nullable=True)
    default_recomned = Column(Text, nullable=True)
    keywords = Column(Text, nullable=True)
    status = Column(String(50), nullable=True, default="active")
    description = Column(String, nullable=True)
    prompt = Column(Text, nullable=True)
    prompt_examples = Column(String, nullable=True) # مثال‌های Few-Shot