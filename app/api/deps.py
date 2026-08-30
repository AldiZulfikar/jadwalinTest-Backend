from typing import List, Callable, Optional
from uuid import UUID
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.user import User
from app.models.enums import UserRole
from app.core.security import decode_token
from app.services.user_service import UserService
from app.services.booking_service import BookingService
from app.services.environment_service import EnvironmentService
from app.repository.booking_repository import BookingRepository
from app.repository.environment_repository import EnvironmentRepository
from app.services.email_service import get_email_service

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login", auto_error=False)


def get_booking_service(db: AsyncSession = Depends(get_db)) -> BookingService:
    """Dependency provider for BookingService."""
    return BookingService(
        booking_repo=BookingRepository(db),
        environment_repo=EnvironmentRepository(db),
        email_service=get_email_service()
    )


def get_environment_service(db: AsyncSession = Depends(get_db)) -> EnvironmentService:
    """Dependency provider for EnvironmentService."""
    return EnvironmentService(environment_repo=EnvironmentRepository(db))


async def get_current_user(
    token: Optional[str] = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Extracts and validates JWT Bearer token, returning the authenticated User."""
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token is missing. Please log in.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    payload = decode_token(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_id_str = payload.get("sub")
    if not user_id_str:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload subject.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    try:
        user_id = UUID(user_id_str)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Malformed user ID in token.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    user_service = UserService()
    try:
        user = await user_service.get_user_by_id(db, user_id)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authenticated user no longer exists.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated."
        )

    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """Ensures current user account is active."""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive."
        )
    return current_user


def require_role(allowed_roles: List[UserRole]) -> Callable:
    """
    RBAC Authorization Factory.
    Enforces that the current authenticated user possesses one of the specified allowed_roles.
    Raises HTTP 403 Forbidden if permissions are insufficient.
    """
    async def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Forbidden. Action requires one of the following roles: {[r.value for r in allowed_roles]}. Your role: '{current_user.role.value}'."
            )
        return current_user

    return role_checker
