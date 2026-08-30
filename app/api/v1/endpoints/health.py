from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.db.session import get_db
from app.services.email_service import BaseEmailService, get_email_service
from app.schemas.common import APIResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Get System Health Status",
    description="Check overall system health, database connectivity, email service initialization, and API version."
)
async def get_health(
    db: AsyncSession = Depends(get_db),
    email_service: BaseEmailService = Depends(get_email_service)
):
    # 1. Database Check
    db_status = "UP"
    try:
        await db.execute(text("SELECT 1"))
    except Exception:
        db_status = "DOWN"

    # 2. Email Provider Check
    email_status = "UP"
    try:
        is_email_healthy = await email_service.health_check()
        if not is_email_healthy:
            email_status = "DOWN"
    except Exception:
        email_status = "DOWN"

    is_overall_healthy = (db_status == "UP" and email_status == "UP")

    return APIResponse(
        success=is_overall_healthy,
        message="System status retrieved successfully.",
        data={
            "status": "healthy" if is_overall_healthy else "unhealthy",
            "database": db_status,
            "email": email_status,
            "version": "2.0.0"
        }
    )


@router.get(
    "/live",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="OpenShift Liveness Probe",
    description="Lightweight liveness probe endpoint to check if the application container process is alive."
)
async def liveness_probe():
    return APIResponse(
        success=True,
        message="Application container is live.",
        data={"status": "ALIVE"}
    )


@router.get(
    "/ready",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="OpenShift Readiness Probe",
    description="Readiness probe validating DB connectivity and email service before routing traffic."
)
async def readiness_probe(
    db: AsyncSession = Depends(get_db),
    email_service: BaseEmailService = Depends(get_email_service)
):
    try:
        await db.execute(text("SELECT 1"))
        email_ready = await email_service.health_check()
        if not email_ready:
            raise Exception("Email service initialization failed.")

        return APIResponse(
            success=True,
            message="Application is ready to handle traffic.",
            data={"status": "READY"}
        )
    except Exception as exc:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "success": False,
                "message": f"Dependency check failed: {str(exc)}",
                "data": {"status": "NOT_READY"}
            }
        )
