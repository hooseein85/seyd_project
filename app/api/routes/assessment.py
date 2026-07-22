from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db
from app.models.assessment import Assessment
from app.schemas.assessment import AssessmentResponse

router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])

@router.get("/", response_model=List[AssessmentResponse])
def get_assessments(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # استفاده از joinedload برای دریافت همزمان اطلاعات policy
    assessments = db.query(Assessment).options(joinedload(Assessment.policy)).offset(skip).limit(limit).all()
    return assessments