from sqlalchemy.orm import Session
from app.models.policy import Policy
from app.schemas.policy import PolicyCreate

class PolicyRepository:
    def get_all(self, db: Session, skip: int = 0, limit: int = 100):
        return db.query(Policy).offset(skip).limit(limit).all()

    def get_by_id(self, db: Session, policy_id: str):
        return db.query(Policy).filter(Policy.id == policy_id).first()

    def create(self, db: Session, policy_in: PolicyCreate):
        db_policy = Policy(**policy_in.model_dump())
        db.add(db_policy)
        db.commit()
        db.refresh(db_policy)
        return db_policy