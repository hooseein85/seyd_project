from pydantic import BaseModel
from typing import Optional
from uuid import UUID

# ساختار کوچک برای دیتای Join شده‌ی قانون
class PolicyMinimal(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None

    class Config:
        from_attributes = True

class AssessmentBase(BaseModel):
    fingerprint: str
    import_batch_id: Optional[str] = None
    policy_id: Optional[UUID] = None
    category: Optional[str] = None
    confidence_score: Optional[float] = None
    risk: Optional[str] = None
    priority: Optional[str] = None
    reason: Optional[str] = None
    analyser: Optional[str] = None
    priority_score: Optional[float] = None
    history_score: Optional[float] = None
    importance_score: Optional[float] = None
    influence_score: Optional[float] = None
    frequency_score: Optional[float] = None
    recommendation: Optional[str] = None
    content_id: Optional[UUID] = None

class AssessmentResponse(AssessmentBase):
    id: UUID
    policy: Optional[PolicyMinimal] = None # اضافه شدن فیلد قانون به خروجی

    class Config:
        from_attributes = True