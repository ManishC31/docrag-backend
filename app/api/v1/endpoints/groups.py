import uuid

from fastapi import APIRouter, status

from app.api.deps import CurrentUser, DBSession
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate
from app.services import group_service

router = APIRouter(prefix="/groups", tags=["Groups"])


@router.post("", response_model=GroupResponse, status_code=status.HTTP_201_CREATED)
async def create_group(data: GroupCreate, current_user: CurrentUser, db: DBSession):
    return await group_service.create_group(data, current_user, db)


@router.get("", response_model=list[GroupResponse])
async def list_groups(current_user: CurrentUser, db: DBSession):
    return await group_service.list_groups(current_user, db)


@router.get("/{group_id}", response_model=GroupResponse)
async def get_group(group_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    return await group_service.get_group(group_id, current_user, db)


@router.patch("/{group_id}", response_model=GroupResponse)
async def update_group(group_id: uuid.UUID, data: GroupUpdate, current_user: CurrentUser, db: DBSession):
    return await group_service.update_group(group_id, data, current_user, db)


@router.delete("/{group_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_group(group_id: uuid.UUID, current_user: CurrentUser, db: DBSession):
    await group_service.delete_group(group_id, current_user, db)
