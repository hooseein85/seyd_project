import uuid
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Assessment(Base):
    __tablename__ = "assessment"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True, nullable=False)
    fingerprint = Column(String(255), nullable=False, unique=True, index=True)
    import_batch_id = Column(String(255), nullable=True)
    
    # اضافه شدن کلید خارجی به شمای core و جدول policy
    policy_id = Column(UUID(as_uuid=True), ForeignKey("core.policy.id"), nullable=True)
    
    category = Column(String(255), nullable=True)
    confidence_score = Column(Numeric, nullable=True)
    risk = Column(String(100), nullable=True)
    priority = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    analyser = Column(String(255), nullable=True)
    priority_score = Column(Numeric, nullable=True)
    history_score = Column(Numeric, nullable=True)
    importance_score = Column(Numeric, nullable=True)
    influence_score = Column(Numeric, nullable=True)
    frequency_score = Column(Numeric, nullable=True)
    recommendation = Column(Text, nullable=True)
    content_id = Column(UUID(as_uuid=True), ForeignKey("core.content.id"), nullable=True)
    policy = relationship("Policy", primaryjoin="Assessment.policy_id == Policy.id")
    content = relationship("Content", primaryjoin="Assessment.content_id == Content.id")
    created_at = Column(DateTime, nullable=True)
    status = Column(String(50), nullable=True) 
    previous_violations_count = Column(Integer, default=0)
    matchedRules = Column(JSON, default=list)