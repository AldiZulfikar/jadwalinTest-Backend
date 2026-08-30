from typing import List
from fastapi import APIRouter, Depends, status

from app.schemas.environment import EnvironmentResponse
from app.schemas.common import APIResponse
from app.services.environment_service import EnvironmentService
from app.api.deps import get_environment_service

router = APIRouter(prefix="/environments", tags=["Environments"])


@router.get(
    "",
    response_model=APIResponse[List[EnvironmentResponse]],
    status_code=status.HTTP_200_OK,
    summary="List Active Environments",
    description="Retrieve a read-only master list of active performance testing environments."
)
async def list_environments(
    service: EnvironmentService = Depends(get_environment_service)
):
    environments = await service.get_active_environments()
    response_data = [EnvironmentResponse.model_validate(env) for env in environments]
    return APIResponse(
        success=True,
        message="Environments retrieved successfully.",
        data=response_data
    )
