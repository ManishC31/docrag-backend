import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.constants import ErrorMessages, UserRole
from app.models.document import Document
from app.models.group import Group
from app.models.user import User
from app.schemas.group import GroupCreate, GroupResponse, GroupUpdate


async def _get_group_or_404(group_id: uuid.UUID, db: AsyncSession) -> Group:
    result = await db.execute(
        select(Group).where(Group.id == group_id).options(selectinload(Group.documents))
    )
    group = result.scalar_one_or_none()
    if not group:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=ErrorMessages.GROUP_NOT_FOUND
        )
    return group


async def _assert_group_access(group: Group, current_user: User) -> None:
    if current_user.role != UserRole.ADMIN and group.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorMessages.GROUP_ACCESS_DENIED,
        )


def _to_response(group: Group) -> GroupResponse:
    return GroupResponse(
        id=group.id,
        name=group.name,
        description=group.description,
        user_id=group.user_id,
        document_count=len(group.documents) if group.documents else 0,
        created_at=group.created_at,
    )


async def create_group(
    data: GroupCreate, current_user: User, db: AsyncSession
) -> GroupResponse:
    group = Group(name=data.name, description=data.description, user_id=current_user.id)
    db.add(group)
    await db.flush()
    await db.refresh(group, ["documents"])
    return _to_response(group)


async def list_groups(current_user: User, db: AsyncSession) -> list[GroupResponse]:
    query = select(Group).options(selectinload(Group.documents))
    if current_user.role != UserRole.ADMIN:
        query = query.where(Group.user_id == current_user.id)
    query = query.order_by(Group.created_at.desc())

    result = await db.execute(query)
    groups = result.scalars().all()
    return [_to_response(g) for g in groups]


async def get_group(
    group_id: uuid.UUID, current_user: User, db: AsyncSession
) -> GroupResponse:
    group = await _get_group_or_404(group_id, db)
    await _assert_group_access(group, current_user)
    return _to_response(group)


async def update_group(
    group_id: uuid.UUID, data: GroupUpdate, current_user: User, db: AsyncSession
) -> GroupResponse:
    group = await _get_group_or_404(group_id, db)
    await _assert_group_access(group, current_user)

    if data.name is not None:
        group.name = data.name
    if data.description is not None:
        group.description = data.description

    await db.flush()
    return _to_response(group)


async def delete_group(
    group_id: uuid.UUID, current_user: User, db: AsyncSession
) -> None:
    group = await _get_group_or_404(group_id, db)
    await _assert_group_access(group, current_user)
    await db.delete(group)
