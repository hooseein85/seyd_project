import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class TelegramChat(Base):
    __tablename__ = "telegram_chat"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    telegram_chat_id = Column(String(255), nullable=False)
    name = Column(Text, nullable=True)
    username = Column(String(255), nullable=True)
    chat_type = Column(String(50), nullable=False)
    member_count = Column(Integer, nullable=True)
    description = Column(Text, nullable=True)
    language = Column(String(50), nullable=True)
    influence_score = Column(Numeric(5, 2), nullable=True)