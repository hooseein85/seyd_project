import uuid
from sqlalchemy import Column, String, Text, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID
from app.db.base import Base

class Account(Base):
    __tablename__ = "account"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    platform = Column(String(100), nullable=False)
    platform_account_id = Column(String(255), nullable=True)
    first_name = Column(Text, nullable=True)
    last_name = Column(Text, nullable=True)
    username = Column(String(255), nullable=True)
    followers_count = Column(Integer, nullable=True)
    following_count = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)