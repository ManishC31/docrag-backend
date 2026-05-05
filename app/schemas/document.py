import uuid
from datetime import datetime

from pydantic import BaseModel

from app.core.constants import DocumentStatus


class DocumentResponse(BaseModel):
    id: uuid.UUID
    name: str
    original_filename: str
    file_type: str
    file_size: int
    group_id: uuid.UUID
    status: DocumentStatus
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
