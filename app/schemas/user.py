from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class Token(BaseModel):
    access_token: str
    token_type: str

class UserOut(BaseModel):
    id: UUID
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    role: str
    is_active: bool

    class Config:
        from_attributes = True