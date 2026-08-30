from abc import ABC, abstractmethod
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.core.security import verify_password
from app.repository.user_repository import UserRepository


from fastapi import HTTPException, status


class BaseAuthenticationProvider(ABC):
    """
    Abstract Authentication Provider Interface.
    Enables future LDAP / Active Directory / OAuth integration by replacing
    the provider implementation without modifying business logic or APIs.
    """
    @abstractmethod
    async def authenticate(self, username: str, password: str, db: AsyncSession) -> Optional[User]:
        """Authenticates user credentials and returns User model if valid."""
        pass


class LocalAuthenticationProvider(BaseAuthenticationProvider):
    """
    Local Database Authentication Provider.
    Verifies user credentials against local database users and bcrypt password hashes.
    """
    async def authenticate(self, username: str, password: str, db: AsyncSession) -> Optional[User]:
        user_repo = UserRepository(db)
        user = await user_repo.find_by_username(username.strip().lower())
        if not user:
            return None

        if not verify_password(password, user.password_hash):
            return None

        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive.",
                headers={"WWW-Authenticate": "Bearer"}
            )

        return user


# Singleton instance of active authentication provider
_active_provider: BaseAuthenticationProvider = LocalAuthenticationProvider()


def get_auth_provider() -> BaseAuthenticationProvider:
    """Returns currently configured authentication provider."""
    return _active_provider
