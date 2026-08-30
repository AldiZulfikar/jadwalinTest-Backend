from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserResponse, UserCreatePayload, UserUpdatePayload, UserStatusPayload, ResetPasswordPayload
from app.schemas.common import APIResponse, PaginatedResponse
from app.models.enums import UserRole
from app.models.user import User
from app.services.user_service import UserService
from app.api.deps import require_role

router = APIRouter(prefix="/users", tags=["Users"])

qa_only = require_role([UserRole.QA])


@router.get(
    "",
    response_model=APIResponse[PaginatedResponse[UserResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Users (QA Only)",
    description="Retrieves paginated list of system users. Supports filtering by role, active status, and search query. Requires QA role."
)
async def list_users(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    role: Optional[UserRole] = Query(None),
    is_active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(qa_only)
):
    user_service = UserService()
    items, total = await user_service.list_users(
        db,
        page=page,
        size=size,
        role=role,
        is_active=is_active,
        search=search
    )
    user_responses = [UserResponse.model_validate(u) for u in items]

    total_pages = (total + size - 1) // size if total > 0 else 0
    paginated = PaginatedResponse[UserResponse](
        items=user_responses,
        total=total,
        page=page,
        size=size,
        total_pages=total_pages
    )
    return APIResponse(
        success=True,
        message="Users retrieved successfully.",
        data=paginated
    )


@router.post(
    "",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Create User (QA Only)",
    description="Creates a new system user with bcrypt hashed password. Requires QA role."
)
async def create_user(
    payload: UserCreatePayload,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(qa_only)
):
    user_service = UserService()
    created_user = await user_service.create_user(db, payload)
    user_resp = UserResponse.model_validate(created_user)
    return APIResponse(
        success=True,
        message="User created successfully.",
        data=user_resp
    )


@router.get(
    "/{user_id}",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get User By ID (QA Only)",
    description="Retrieves details of a specific user. Requires QA role."
)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(qa_only)
):
    user_service = UserService()
    user = await user_service.get_user_by_id(db, user_id)
    user_resp = UserResponse.model_validate(user)
    return APIResponse(
        success=True,
        message="User details retrieved successfully.",
        data=user_resp
    )


@router.put(
    "/{user_id}",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Update User (QA Only)",
    description="Updates role, full_name, email, or active status of a user. Enforces Safety Rules 1 & 2. Requires QA role."
)
async def update_user(
    user_id: UUID,
    payload: UserUpdatePayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(qa_only)
):
    user_service = UserService()
    updated_user = await user_service.update_user(db, user_id, payload, current_user=current_user)
    user_resp = UserResponse.model_validate(updated_user)
    return APIResponse(
        success=True,
        message="User updated successfully.",
        data=user_resp
    )


@router.patch(
    "/{user_id}/status",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Toggle User Active Status (QA Only)",
    description="Activates or deactivates a user account. Enforces Safety Rules 1 & 2. Requires QA role."
)
async def update_user_status(
    user_id: UUID,
    payload: UserStatusPayload,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(qa_only)
):
    user_service = UserService()
    updated_user = await user_service.update_user_status(db, user_id, payload.is_active, current_user=current_user)
    user_resp = UserResponse.model_validate(updated_user)
    status_str = "activated" if payload.is_active else "deactivated"
    return APIResponse(
        success=True,
        message=f"User account {status_str} successfully.",
        data=user_resp
    )


@router.post(
    "/{user_id}/reset-password",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Reset User Password (QA Only)",
    description="Resets the password for a target user with a bcrypt hashed new password. Requires QA role."
)
async def reset_user_password(
    user_id: UUID,
    payload: ResetPasswordPayload,
    db: AsyncSession = Depends(get_db),
    _current_user: User = Depends(qa_only)
):
    user_service = UserService()
    updated_user = await user_service.reset_user_password(db, user_id, payload.new_password)
    user_resp = UserResponse.model_validate(updated_user)
    return APIResponse(
        success=True,
        message="User password reset successfully.",
        data=user_resp
    )
