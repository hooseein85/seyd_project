import uuid
from sqlalchemy import Column, String, Text, Numeric, ForeignKey, DateTime, Integer, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.base import Base

class Violation(Base):
    __tablename__ = "violation"
    __table_args__ = {"schema": "core"}

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, nullable=False)
    fingerprint = Column(String(255), nullable=False)
    import_batch_id = Column(String(255), nullable=True)
    
    # کلیدهای خارجی برای اتصال به ۴ جدول دیگر
    content_id = Column(UUID(as_uuid=True), ForeignKey("core.content.id"), nullable=True)
    assessment_id = Column(UUID(as_uuid=True), ForeignKey("core.assessment.id"), nullable=True)
    account_id = Column(UUID(as_uuid=True), ForeignKey("core.account.id"), nullable=True)
    policy_id = Column(UUID(as_uuid=True), ForeignKey("core.policy.id"), nullable=True)
    
    person_id = Column(UUID(as_uuid=True), nullable=True)
    expert_id = Column(String(255), nullable=True)
    expert_action = Column(String(255), nullable=True)
    expert_comment = Column(Text, nullable=True)
    action_status = Column(String(100), nullable=True, default="pending")
    created_at = Column(DateTime, nullable=True)
    matchedRules = Column(JSON, default=list)

    # تعریف روابط برای استفاده در JoinedLoad
    content = relationship("Content", primaryjoin="Violation.content_id == Content.id")
    assessment = relationship("Assessment", primaryjoin="Violation.assessment_id == Assessment.id")
    account = relationship("Account", primaryjoin="Violation.account_id == Account.id")
    policy = relationship("Policy", primaryjoin="Violation.policy_id == Policy.id")