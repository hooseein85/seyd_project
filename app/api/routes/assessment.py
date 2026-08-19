from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentResponse
from sqlalchemy import desc

router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])

# @router.get("/", response_model=List[AssessmentResponse])
# def get_assessments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
#     # استفاده از joinedload برای دریافت همزمان اطلاعات policy
#     assessments = db.query(Assessment).options(joinedload(Assessment.policy)).offset(skip).limit(limit).all()
#     return assessments

# # در فایل assessment.py بک‌اند

@router.get("/", response_model=List[AssessmentResponse])
def get_assessments(skip: int = 0, limit: int = 20, db: Session = Depends(get_db)): # 👈 اینجا limit پیش‌فرض را 20 بگذارید
    
    # برای اطمینان صد در صد که هیچ‌وقت بیشتر از 20 تا نمی‌دهد:
    actual_limit = min(limit, 20) 
    
    assessments = (
        db.query(Assessment)
        # در کدهای کامنت‌شده‌ی قبلی‌تان joinedload داشتید. اگر فرانت به دیتای policy نیاز دارد، این خط را از کامنت در بیاورید:
        .options(joinedload(Assessment.policy))
        .order_by(desc(Assessment.created_at)) # 👈 استفاده از تاریخ ایجاد
        .offset(skip)
        .limit(actual_limit)
        .all()
    )
    return assessments