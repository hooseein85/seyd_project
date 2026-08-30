from datetime import date
from typing import List, Dict, Any, Optional

from pydantic import BaseModel, Field, model_validator


class ViolationExportRequest(BaseModel):
    from_date: date = Field(..., description="Start date")
    to_date: date = Field(..., description="End date")
    expert_action: Optional[str] = Field(
        default=None,
        min_length=1,
        description="Expert action. If omitted, all actions are included.",
    )

    @model_validator(mode="after")
    def validate_dates(self):
        if self.from_date > self.to_date:
            raise ValueError("from_date must be before or equal to to_date")
        return self