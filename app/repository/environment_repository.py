from typing import List, Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.environment import Environment
from app.repository.base_repository import BaseRepository


class EnvironmentRepository(BaseRepository[Environment]):
    def __init__(self, db_session: AsyncSession):
        super().__init__(Environment, db_session)

    async def get_active_environments(self) -> List[Environment]:
        """Fetch all active environment master records."""
        stmt = select(Environment).where(Environment.active.is_(True)).order_by(Environment.code)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_code(self, code: str) -> Optional[Environment]:
        """Fetch environment by code."""
        stmt = select(Environment).where(Environment.code == code)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()
