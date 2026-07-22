from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session, joinedload
from app.api.dependencies import get_db
from app.models.content import Content
from pydantic import BaseModel
from datetime import datetime
from uuid import UUID

router = APIRouter(prefix="/api/v1/contents", tags=["Contents"])

class TelegramChatMinimal(BaseModel):
    name: Optional[str] = None
    chat_type: Optional[str] = None
    username: Optional[str] = None

    class Config:
        from_attributes = True

class AccountMinimal(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    username: Optional[str] = None

    class Config:
        from_attributes = True

class ContentResponse(BaseModel):
    id: UUID
    content_id: Optional[str] = None
    publish_time: Optional[datetime] = None
    body: Optional[str] = None
    url: Optional[str] = None
    platform: Optional[str] = None
    view_count: Optional[int] = 0
    like_count: Optional[int] = 0
    telegram_chat: Optional[TelegramChatMinimal] = None # اضافه شد
    account: Optional[AccountMinimal] = None # اضافه شد

    class Config:
        from_attributes = True

@router.get("/", response_model=List[ContentResponse])
def get_contents(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    # جوین کردن همزمان چت و اکانت
    contents = db.query(Content).options(
        joinedload(Content.telegram_chat),
        joinedload(Content.account)
    ).offset(skip).limit(limit).all()
    return contents