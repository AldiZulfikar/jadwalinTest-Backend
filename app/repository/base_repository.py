from typing import Generic, TypeVar, Type, Optional, List, Any, Tuple
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, asc, desc
from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Enhanced Repository providing soft-delete filtering and reusable query helpers."""

    def __init__(self, model: Type[ModelType], db_session: AsyncSession):
        self.model = model
        self.db = db_session

    def _base_query(self, include_deleted: bool = False):
        """Constructs base select query automatically filtering out soft-deleted records."""
        stmt = select(self.model)
        if not include_deleted and hasattr(self.model, "deleted_at"):
            stmt = stmt.where(getattr(self.model, "deleted_at").is_(None))
        return stmt

    async def find_by_id(self, id: UUID, include_deleted: bool = False) -> Optional[ModelType]:
        """Find record by ID, excluding soft-deleted records by default."""
        stmt = self._base_query(include_deleted=include_deleted).where(self.model.id == id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def find_active(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Find active (non-deleted) records."""
        stmt = self._base_query(include_deleted=False).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def find_deleted(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Find only soft-deleted records."""
        if not hasattr(self.model, "deleted_at"):
            return []
        stmt = select(self.model).where(getattr(self.model, "deleted_at").isnot(None)).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_by_id(self, id: UUID) -> Optional[ModelType]:
        """Alias for find_by_id for backward compatibility."""
        return await self.find_by_id(id)

    async def get_all(self, skip: int = 0, limit: int = 100) -> List[ModelType]:
        """Alias for find_active for backward compatibility."""
        return await self.find_active(skip=skip, limit=limit)

    async def create(self, obj: ModelType) -> ModelType:
        """Persists a new record to the database."""
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def update(self, obj: ModelType) -> ModelType:
        """Persists updates to an existing record in the database."""
        self.db.add(obj)
        await self.db.flush()
        await self.db.refresh(obj)
        return obj

    async def soft_delete(self, obj: ModelType, deleted_by: Optional[str] = None) -> None:
        """Logically marks a record as deleted without removing from DB."""
        if hasattr(obj, "deleted_at"):
            setattr(obj, "deleted_at", datetime.now())
        if hasattr(obj, "deleted_by"):
            setattr(obj, "deleted_by", deleted_by)
        self.db.add(obj)
        await self.db.flush()

    async def delete(self, obj: ModelType) -> None:
        """Physical deletion (overridden to perform soft delete if model supports it)."""
        if hasattr(obj, "deleted_at"):
            await self.soft_delete(obj)
        else:
            await self.db.delete(obj)
            await self.db.flush()
