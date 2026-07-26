from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.api.dependencies import get_db
from app.schemas.policy import PolicyCreate, PolicyResponse
from app.services.policy_service import PolicyService
from sqlalchemy import desc
from app.models.policy import Policy

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