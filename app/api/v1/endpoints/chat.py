import uuid

from fastapi import APIRouter

from app.api.deps import CurrentUser, DBSession
from app.schemas.chat import ChatRequest, ChatResponse
from app.services import rag_service

router = APIRouter(prefix="/groups/{group_id}/chat", tags=["Chat"])


# create new chat
@router.post("", response_model=ChatResponse)
async def ask_question(
    group_id: uuid.UUID, data: ChatRequest, current_user: CurrentUser, db: DBSession
):
    return await rag_service.query_group(group_id, data.question, current_user, db)


# get chat history of the group
@router.get("/history", response_model=list[ChatResponse])
async def get_chat_history(
    group_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    return await rag_service.get_chat_history(group_id, current_user, db)
