from typing import Optional, List, Tuple
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, or_, desc

from app.models.user import User
from app.models.enums import UserRole
from app.repository.base_repository import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(User, db_session)

    async def find_by_username(self, username: str) -> Optional[User]:
        stmt = select(User).where(func.lower(User.username) == username.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def find_by_email(self, email: str) -> Optional[User]:
        stmt = select(User).where(func.lower(User.email) == email.lower().strip())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def count_active_qa(self) -> int:
        """Counts the total number of active QA users in the system."""
        stmt = select(func.count()).select_from(User).where(
            User.role == UserRole.QA,
            User.is_active.is_(True)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def filter_and_paginate(
        self,
        page: int = 1,
        size: int = 20,
        role: Optional[UserRole] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None
    ) -> Tuple[List[User], int]:
        stmt = select(User)
        conditions = []

        if role:
            conditions.append(User.role == role)
        if is_active is not None:
            conditions.append(User.is_active.is_(is_active))
        if search:
            search_pattern = f"%{search.strip()}%"
            conditions.append(
                or_(
                    User.username.ilike(search_pattern),
                    User.full_name.ilike(search_pattern),
                    User.email.ilike(search_pattern)
                )
            )

        if conditions:
            stmt = stmt.where(*conditions)

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total_result = await self.db.execute(count_stmt)
        total = total_result.scalar_one()

        offset = (page - 1) * size
        stmt = stmt.order_by(desc(User.created_at)).offset(offset).limit(size)

        result = await self.db.execute(stmt)
        items = list(result.scalars().all())

        return items, total
