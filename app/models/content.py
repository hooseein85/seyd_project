import uuid
from sqlalchemy import Column, String, Text, Integer, DateTime, ForeignKey, text
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.db.base import Base
from sqlalchemy.orm import relationship

class Content(Base):
    __tablename__ = "content"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    content_id = Column(String(255), nullable=True)
    publish_time = Column(DateTime, nullable=True)
    language = Column(String(50), nullable=True)
    content_type = Column(String(100), nullable=True)
    body = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    media_url = Column(ARRAY(Text), nullable=True)
    view_count = Column(Integer, nullable=True)
    like_count = Column(Integer, nullable=True)
    repost_count = Column(Integer, nullable=True)
    share_count = Column(Integer, nullable=True)
    analysis_status = Column(String(50), server_default='Pending', nullable=True)
    fingerprint = Column(Text, nullable=False)
    created_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=True)
    updated_at = Column(DateTime, server_default=text('CURRENT_TIMESTAMP'), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("core.account.id"), nullable=True)
    source_id = Column(UUID(as_uuid=True), nullable=True)
    chat_id = Column(UUID(as_uuid=True), ForeignKey("core.telegram_chat.id"), nullable=True)
    import_batch_id = Column(String(50), nullable=True)
    platform = Column(String, nullable=True)
    account = relationship("Account", primaryjoin="Content.account_id == Account.id")
    telegram_chat = relationship("TelegramChat", primaryjoin="Content.chat_id == TelegramChat.id")
    