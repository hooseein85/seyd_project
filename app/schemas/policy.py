from pydantic import BaseModel, UUID4, ConfigDict
from typing import Optional

class PolicyBase(BaseModel):
    fingerprint: str
    import_batch_id: Optional[str] = None
    code: Optional[str] = None
    title: Optional[str] = None
    severity: Optional[str] = None
    default_recomned: Optional[str] = None
    keywords: Optional[str] = None
    prompt: Optional[str] = None

class PolicyCreate(PolicyBase):
    pass

class PolicyResponse(PolicyBase):
    id: UUID4
    model_config = ConfigDict(from_attributes=True)