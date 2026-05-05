import uuid

from fastapi import APIRouter, BackgroundTasks, File, UploadFile, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.document import DocumentResponse
from app.services import document_service

router = APIRouter(prefix="/groups/{group_id}/documents", tags=["Documents"])


# upload new document in a group
@router.post("", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    group_id: uuid.UUID,
    current_user: CurrentUser,
    db: DBSession,
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
):
    return await document_service.upload_document(
        group_id, file, current_user, db, background_tasks
    )


# list of all documents of a group
@router.get("", response_model=list[DocumentResponse])
async def list_documents(group_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    return await document_service.list_documents(group_id, current_user, db)


# delete document in a group
@router.delete("/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: uuid.UUID, current_user: CurrentUser, db: DBSession
):
    await document_service.delete_document(document_id, current_user, db)
