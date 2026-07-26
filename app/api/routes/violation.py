from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db
from app.models.violation import Violation
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy import desc


router = APIRouter(prefix="/api/v1/violations", tags=["Violations"])

# --- ساختارهای کمکی برای دیتای Join شده ---
class VioPolicyMin(BaseModel):
    code: Optional[str] = None
    title: Optional[str] = None
    default_recomned: Optional[str] = None
    class Config: from_attributes = True

class VioContentMin(BaseModel):
    content_id: Optional[str] = None
    body: Optional[str] = None
    class Config: from_attributes = True

class VioAccountMin(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None
    platform: Optional[str] = None
    platform_account_id: Optional[str] = None
    class Config: from_attributes = True

class VioAssessmentMin(BaseModel):
    priority: Optional[str] = None
    reason: Optional[str] = None
    priority_score: Optional[float] = 0
    history_score: Optional[float] = 0
    importance_score: Optional[float] = 0
    influence_score: Optional[float] = 0
    frequency_score: Optional[float] = 0
    confidence_score: Optional[float] = 0
    class Config: from_attributes = True

# --- ساختار خروجی نهایی ---
class ViolationResponse(BaseModel):
    id: UUID
    expert_action: Optional[str] = None
    action_status: Optional[str] = None
    policy: Optional[VioPolicyMin] = None
    content: Optional[VioContentMin] = None
    account: Optional[VioAccountMin] = None
    assessment: Optional[VioAssessmentMin] = None
    class Config: from_attributes = True

@router.get("/", response_model=List[ViolationResponse])
def get_violations(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    # 🌟 استفاده از limit=50 و مرتب‌سازی نزولی
    # اگر در جدول violation ستون created_at دارید، آن را جایگزین Violation.id کنید
    violations = db.query(Violation).options(
        joinedload(Violation.policy),
        joinedload(Violation.content),
        joinedload(Violation.account),
        joinedload(Violation.assessment)
    ).order_by(desc(Violation.created_at)).offset(skip).limit(limit).all()
    
    return violations