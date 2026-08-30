from typing import List, Optional
from uuid import UUID
from app.models.environment import Environment
from app.repository.environment_repository import EnvironmentRepository
from app.core.exceptions import EnvironmentNotFoundException
from app.core.logging import logger


class EnvironmentService:
    def __init__(self, environment_repo: EnvironmentRepository):
        self.environment_repo = environment_repo

    async def get_active_environments(self) -> List[Environment]:
        """Fetch all active environment records."""
        return await self.environment_repo.get_active_environments()

    async def validate_environment_exists(self, environment_id: UUID) -> Environment:
        """Validate that an environment exists and is active."""
        env = await self.environment_repo.find_by_id(environment_id)
        if not env or not env.active:
            logger.warning(f"Environment ID={environment_id} not found or inactive.")
            raise EnvironmentNotFoundException(f"Environment with ID {environment_id} not found or inactive.")
        return env
