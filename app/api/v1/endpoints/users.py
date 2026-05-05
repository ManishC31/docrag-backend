from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DBSession
from app.models.user import User
from app.schemas.chat import AdminStatsResponse
from app.schemas.user import UserAdminView, UserResponse, UserUpdate
from sqlalchemy import func, select
from app.models.group import Group
from app.models.document import Document, ChatMessage

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: CurrentUser):
    return UserResponse.model_validate(current_user)


@router.patch("/me", response_model=UserResponse)
async def update_me(data: UserUpdate, current_user: CurrentUser, db: DBSession):
    if data.full_name is not None:
        current_user.full_name = data.full_name
    if data.avatar_url is not None:
        current_user.avatar_url = data.avatar_url
    await db.flush()
    return UserResponse.model_validate(current_user)


@router.get("/admin/users", response_model=list[UserAdminView])
async def list_all_users(_: AdminUser, db: DBSession):
    result = await db.execute(select(User).order_by(User.created_at.desc()))
    users = result.scalars().all()
    return [UserAdminView.model_validate(u) for u in users]


@router.patch("/admin/users/{user_id}/deactivate", response_model=UserResponse)
async def deactivate_user(user_id: str, _: AdminUser, db: DBSession):
    from sqlalchemy import select
    import uuid
    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        from fastapi import HTTPException, status
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    user.is_active = False
    await db.flush()
    return UserResponse.model_validate(user)


@router.get("/admin/stats", response_model=AdminStatsResponse)
async def get_admin_stats(_: AdminUser, db: DBSession):
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_groups = (await db.execute(select(func.count(Group.id)))).scalar_one()
    total_documents = (await db.execute(select(func.count(Document.id)))).scalar_one()
    total_queries = (await db.execute(select(func.count(ChatMessage.id)))).scalar_one()

    return AdminStatsResponse(
        total_users=total_users,
        total_groups=total_groups,
        total_documents=total_documents,
        total_queries=total_queries,
    )
