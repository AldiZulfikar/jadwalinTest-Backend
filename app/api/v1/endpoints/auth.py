from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.auth import LoginPayload, TokenResponse, RefreshTokenPayload, PasswordChangePayload
from app.schemas.user import UserResponse
from app.schemas.common import APIResponse
from app.core.auth_provider import get_auth_provider, BaseAuthenticationProvider
from app.core.security import create_access_token, create_refresh_token, decode_token
from app.services.user_service import UserService
from app.models.user import User
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post(
    "/login",
    response_model=APIResponse[TokenResponse],
    status_code=status.HTTP_200_OK,
    summary="Authenticate User & Issue JWT Tokens",
    description="Authenticates credentials using configured AuthenticationProvider (Local/LDAP) and returns JWT access & refresh tokens."
)
async def login(
    payload: LoginPayload,
    db: AsyncSession = Depends(get_db),
    auth_provider: BaseAuthenticationProvider = Depends(get_auth_provider)
):
    user = await auth_provider.authenticate(payload.username, payload.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Update last login timestamp
    user_service = UserService()
    updated_user = await user_service.update_last_login(db, user)

    # Issue Tokens
    token_data = {"sub": str(updated_user.id), "username": updated_user.username, "role": updated_user.role.value}
    access_token = create_access_token(data=token_data)
    refresh_token = create_refresh_token(data=token_data)

    user_resp = UserResponse.model_validate(updated_user)
    token_response = TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        user=user_resp
    )

    return APIResponse(
        success=True,
        message="Authentication successful.",
        data=token_response
    )


@router.post(
    "/refresh",
    response_model=APIResponse[dict],
    status_code=status.HTTP_200_OK,
    summary="Refresh JWT Access Token",
    description="Accepts a valid refresh token and issues a new access token."
)
async def refresh_token(
    payload: RefreshTokenPayload,
    db: AsyncSession = Depends(get_db)
):
    token_payload = decode_token(payload.refresh_token)
    if not token_payload or token_payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token."
        )

    user_id_str = token_payload.get("sub")
    if not user_id_str:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token payload.")

    user_service = UserService()
    try:
        from uuid import UUID
        user = await user_service.get_user_by_id(db, UUID(user_id_str))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User no longer exists.")

    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="User account is deactivated.")

    new_access_token = create_access_token(data={"sub": str(user.id), "username": user.username, "role": user.role.value})
    return APIResponse(
        success=True,
        message="Access token refreshed successfully.",
        data={"access_token": new_access_token, "token_type": "bearer"}
    )


@router.get(
    "/me",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Get Authenticated User Profile",
    description="Returns current authenticated user details."
)
async def get_me(current_user: User = Depends(get_current_user)):
    user_resp = UserResponse.model_validate(current_user)
    return APIResponse(
        success=True,
        message="User profile retrieved successfully.",
        data=user_resp
    )


@router.post(
    "/change-password",
    response_model=APIResponse[UserResponse],
    status_code=status.HTTP_200_OK,
    summary="Change User Password",
    description="Allows authenticated user to change their password."
)
async def change_password(
    payload: PasswordChangePayload,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    user_service = UserService()
    updated_user = await user_service.change_password(
        db=db,
        user=current_user,
        current_password=payload.current_password,
        new_password=payload.new_password
    )
    user_resp = UserResponse.model_validate(updated_user)
    return APIResponse(
        success=True,
        message="Password updated successfully.",
        data=user_resp
    )
