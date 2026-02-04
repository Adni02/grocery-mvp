"""Dependency injection for FastAPI routes."""

from typing import Annotated, Optional
from uuid import UUID

from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models.user import User
from app.services.auth_service import AuthService


async def get_current_user_optional(
    db: Annotated[AsyncSession, Depends(get_db)],
    session_token: Annotated[Optional[str], Cookie(alias="session")] = None,
) -> Optional[User]:
    """Get current user if authenticated, None otherwise."""
    if not session_token:
        return None

    auth_service = AuthService(db)
    user_id = auth_service.verify_session_token(session_token)
    if not user_id:
        return None

    return await auth_service.get_user_by_id(user_id)


async def get_current_user(
    user: Annotated[Optional[User], Depends(get_current_user_optional)],
) -> User:
    """Get current authenticated user, raise 401 if not authenticated."""
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


async def get_admin_user(
    user: Annotated[User, Depends(get_current_user)],
) -> User:
    """Get current user and verify they are an admin."""
    if not user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return user


async def verify_admin_api_key(
    x_admin_api_key: Annotated[Optional[str], Header(alias="X-Admin-API-Key")] = None,
) -> bool:
    """Verify admin API key for Retool/external admin access."""
    if not x_admin_api_key or x_admin_api_key != settings.admin_api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin API key",
        )
    return True


# Type aliases for cleaner route signatures
DbSession = Annotated[AsyncSession, Depends(get_db)]
CurrentUser = Annotated[User, Depends(get_current_user)]
CurrentUserOptional = Annotated[Optional[User], Depends(get_current_user_optional)]
AdminUser = Annotated[User, Depends(get_admin_user)]
AdminApiKey = Annotated[bool, Depends(verify_admin_api_key)]
