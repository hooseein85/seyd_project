from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db
from app.models.violation import Violation
from pydantic import BaseModel
from uuid import UUID
from sqlalchemy import desc
from fastapi.responses import StreamingResponse

from app.schemas.violation_export import ViolationExportRequest
from app.services.violation_export_service import ViolationExportService


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
    previous_violations_count: Optional[int] = 0
    class Config: from_attributes = True

# --- ساختار خروجی نهایی ---
class ViolationResponse(BaseModel):
    id: UUID
    expert_action: Optional[str] = None
    expert_comment: Optional[str] = None
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

### Export to Excell 
@router.post("/export")
def export_violations(
    request: ViolationExportRequest,
    db: Session = Depends(get_db),
):
    service = ViolationExportService()

    excel_file = service.export_to_excel(
        db=db,
        from_date=request.from_date,
        to_date=request.to_date,
        expert_action=request.expert_action,
    )

    filename = (
        f"violations_"
        f"{request.from_date}_"
        f"{request.to_date}.xlsx"
    )

    return StreamingResponse(
        excel_file,
        media_type=(
            "application/vnd.openxmlformats-"
            "officedocument.spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        },
    )
# --- ساختار ورودی برای آپدیت تخلف ---
class ViolationUpdateRequest(BaseModel):
    expert_action: Optional[str] = None
    expert_comment: Optional[str] = None
    action_status: Optional[str] = None

@router.patch("/{violation_id}", response_model=ViolationResponse)
def update_violation(violation_id: UUID, req: ViolationUpdateRequest, db: Session = Depends(get_db)):
    db_violation = db.query(Violation).filter(Violation.id == violation_id).first()
    if not db_violation:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Violation not found")
    
    if req.expert_action is not None:
        db_violation.expert_action = req.expert_action
    if req.expert_comment is not None:
        db_violation.expert_comment = req.expert_comment
    if req.action_status is not None:
        db_violation.action_status = req.action_status
        
    db.commit()
    db.refresh(db_violation)
    return db_violation
    