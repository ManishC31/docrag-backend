import uuid
from datetime import datetime

from pydantic import BaseModel


class ChatRequest(BaseModel):
    question: str


class SourceChunk(BaseModel):
    document_name: str
    content: str
    chunk_index: int


class ChatResponse(BaseModel):
    id: uuid.UUID
    question: str
    answer: str
    sources: list[SourceChunk] | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AdminStatsResponse(BaseModel):
    total_users: int
    total_groups: int
    total_documents: int
    total_queries: int
