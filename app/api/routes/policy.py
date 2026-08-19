from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_db
from app.schemas.policy import PolicyCreate, PolicyResponse
from app.services.policy_service import PolicyService
from sqlalchemy import desc
from app.models.policy import Policy
from pydantic import BaseModel
from typing import Optional
from uuid import UUID

router = APIRouter(prefix="/api/v1/policies", tags=["Policies"])
policy_service = PolicyService()

@router.get("/", response_model=List[PolicyResponse])
def get_policies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return policy_service.get_policies(db, skip, limit)

@router.get("/{policy_id}", response_model=PolicyResponse)
def get_policy(policy_id: str, db: Session = Depends(get_db)):
    policy = policy_service.get_policy(db, policy_id)
    if not policy:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Policy not found")
    return policy

@router.get("/", response_model=List[PolicyResponse])
def get_policies(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    policies = db.query(Policy).order_by(desc(Policy.created_at)).offset(skip).limit(limit).all()
    return policies

class PolicyUpdateRequest(BaseModel):
    title: Optional[str] = None
    severity: Optional[str] = None
    default_recomned: Optional[str] = None
    keywords: Optional[str] = None
    prompt: Optional[str] = None
    status: Optional[str] = None

@router.patch("/{policy_id}")
def update_policy(policy_id: UUID, req: PolicyUpdateRequest, db: Session = Depends(get_db)):
    db_policy = db.query(Policy).filter(Policy.id == policy_id).first()
    if not db_policy:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Policy not found")
    
    # آپدیت فقط فیلدهایی که ارسال شده‌اند
    update_data = req.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_policy, key, value)
        
    db.commit()
    db.refresh(db_policy)
    return db_policy