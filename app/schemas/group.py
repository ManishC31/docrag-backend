import uuid
from datetime import datetime

from pydantic import BaseModel, field_validator


class GroupCreate(BaseModel):
    name: str
    description: str | None = None

    @field_validator("name")
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Group name cannot be empty")
        return v.strip()


class GroupUpdate(BaseModel):
    name: str | None = None
    description: str | None = None


class GroupResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    user_id: uuid.UUID
    document_count: int = 0
    created_at: datetime

    model_config = {"from_attributes": True}


class GroupDetailResponse(GroupResponse):
    pass
