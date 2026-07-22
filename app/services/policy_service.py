from sqlalchemy.orm import Session
from app.repositories.policy_repo import PolicyRepository
from app.schemas.policy import PolicyCreate

policy_repo = PolicyRepository()

class PolicyService:
    def get_policies(self, db: Session, skip: int, limit: int):
        return policy_repo.get_all(db, skip, limit)

    def get_policy(self, db: Session, policy_id: str):
        return policy_repo.get_by_id(db, policy_id)

    def create_policy(self, db: Session, policy_in: PolicyCreate):
        # اینجا منطق بیزینسی و ولیدیشن‌های قبل از ثبت دیتابیس قرار می‌گیرد
        return policy_repo.create(db, policy_in)