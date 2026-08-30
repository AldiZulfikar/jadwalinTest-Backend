from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.enums import UserRole
from app.schemas.user import UserCreatePayload, UserUpdatePayload
from app.repository.user_repository import UserRepository
from app.core.security import hash_password, verify_password
from app.utils.timezone import get_utc_now
from app.core.exceptions import BusinessLogicException, ResourceNotFoundException


class UserService:
    async def get_user_by_id(self, db: AsyncSession, user_id: UUID) -> User:
        user_repo = UserRepository(db)
        user = await user_repo.find_by_id(user_id)
        if not user:
            raise ResourceNotFoundException("User not found.")
        return user

    async def get_user_by_username(self, db: AsyncSession, username: str) -> User:
        user_repo = UserRepository(db)
        user = await user_repo.find_by_username(username)
        if not user:
            raise ResourceNotFoundException("User not found.")
        return user

    async def list_users(
        self,
        db: AsyncSession,
        page: int = 1,
        size: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        user_repo = UserRepository(db)
        return await user_repo.filter_and_paginate(
            page=page,
            size=size,
            role=role,
            is_active=is_active,
            search=search
        )

    async def create_user(self, db: AsyncSession, payload: UserCreatePayload) -> User:
        user_repo = UserRepository(db)
        existing_username = await user_repo.find_by_username(payload.username)
        if existing_username:
            raise BusinessLogicException(f"Username '{payload.username}' is already taken.")

        existing_email = await user_repo.find_by_email(payload.email)
        if existing_email:
            raise BusinessLogicException(f"Email '{payload.email}' is already registered.")

        new_user = User(
            username=payload.username.strip().lower(),
            password_hash=hash_password(payload.password),
            full_name=payload.full_name.strip(),
            email=payload.email.strip().lower(),
            role=payload.role,
            is_active=payload.is_active,
            created_at=get_utc_now(),
            updated_at=get_utc_now()
        )
        return await user_repo.create(new_user)

    async def update_user(
        self,
        db: AsyncSession,
        user_id: UUID,
        payload: UserUpdatePayload,
        current_user: Optional[User] = None
    ) -> User:
        user_repo = UserRepository(db)
        user = await self.get_user_by_id(db, user_id)

        # Safety Rule 1: QA cannot deactivate itself
        if current_user and current_user.id == user.id and payload.is_active is False:
            raise BusinessLogicException("You cannot deactivate your own account.")

        # Safety Rule 2: At least one active QA must always exist
        is_deactivating_qa = (user.role == UserRole.QA and payload.is_active is False)
        is_changing_qa_role = (user.role == UserRole.QA and payload.role is not None and payload.role != UserRole.QA and user.is_active)
        if is_deactivating_qa or is_changing_qa_role:
            active_qa_count = await user_repo.count_active_qa()
            if active_qa_count <= 1:
                raise BusinessLogicException("The system must have at least one active QA user.")

        if payload.email and payload.email.lower() != user.email.lower():
            existing_email = await user_repo.find_by_email(payload.email)
            if existing_email:
                raise BusinessLogicException(f"Email '{payload.email}' is already registered.")
            user.email = payload.email.lower().strip()

        if payload.full_name:
            user.full_name = payload.full_name.strip()
        if payload.role:
            user.role = payload.role
        if payload.is_active is not None:
            user.is_active = payload.is_active

        user.updated_at = get_utc_now()
        return await user_repo.update(user)

    async def update_user_status(
        self,
        db: AsyncSession,
        user_id: UUID,
        is_active: bool,
        current_user: User
    ) -> User:
        user_repo = UserRepository(db)
        user = await self.get_user_by_id(db, user_id)

        # Safety Rule 1: QA cannot deactivate itself
        if current_user.id == user.id and is_active is False:
            raise BusinessLogicException("You cannot deactivate your own account.")

        # Safety Rule 2: At least one active QA must always exist
        if user.role == UserRole.QA and is_active is False and user.is_active:
            active_qa_count = await user_repo.count_active_qa()
            if active_qa_count <= 1:
                raise BusinessLogicException("The system must have at least one active QA user.")

        user.is_active = is_active
        user.updated_at = get_utc_now()
        return await user_repo.update(user)

    async def reset_user_password(
        self,
        db: AsyncSession,
        user_id: UUID,
        new_password: str
    ) -> User:
        user_repo = UserRepository(db)
        user = await self.get_user_by_id(db, user_id)

        if len(new_password) < 8:
            raise BusinessLogicException("New password must be at least 8 characters long.")

        user.password_hash = hash_password(new_password)
        user.updated_at = get_utc_now()
        return await user_repo.update(user)

    async def change_password(
        self,
        db: AsyncSession,
        user: User,
        current_password: str,
        new_password: str
    ) -> User:
        user_repo = UserRepository(db)
        if not verify_password(current_password, user.password_hash):
            raise BusinessLogicException("Current password is incorrect.")

        if current_password == new_password:
            raise BusinessLogicException("New password cannot be the same as the current password.")

        if len(new_password) < 8:
            raise BusinessLogicException("New password must be at least 8 characters long.")

        user.password_hash = hash_password(new_password)
        user.updated_at = get_utc_now()
        return await user_repo.update(user)

    async def update_last_login(self, db: AsyncSession, user: User) -> User:
        user_repo = UserRepository(db)
        user.last_login = get_utc_now()
        return await user_repo.update(user)
