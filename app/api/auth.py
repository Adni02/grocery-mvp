"""Authentication API routes."""

from fastapi import APIRouter, HTTPException, Response, status

from app.dependencies import CurrentUser, CurrentUserOptional, DbSession
from app.schemas.auth import AuthVerifyRequest, AuthVerifyResponse, UserResponse
from app.services.auth_service import AuthService

router = APIRouter()


@router.post("/verify", response_model=AuthVerifyResponse)
async def verify_token(
    request: AuthVerifyRequest,
    response: Response,
    db: DbSession,
):
    """
    Verify Firebase ID token and create/update user session.

    This endpoint:
    1. Validates the Firebase ID token
    2. Creates or updates the user in our database
    3. Issues a session cookie for subsequent requests
    """
    auth_service = AuthService(db)

    # Verify Firebase token
    claims = await auth_service.verify_firebase_token(request.id_token)
    if not claims:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired Firebase token",
        )

    # Get or create user
    user = await auth_service.get_or_create_user(claims)

    # Create session token
    session_token = auth_service.create_session_token(user.id)

    # Set session cookie
    response.set_cookie(
        key="session",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=60 * 60 * 24 * 7,  # 7 days
    )

    return AuthVerifyResponse(user=UserResponse.model_validate(user))


@router.post("/logout")
async def logout(
    response: Response,
    user: CurrentUserOptional,
):
    """
    Log out the current user by clearing the session cookie.
    """
    response.delete_cookie(key="session")
    return {"message": "Logged out successfully"}


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(user: CurrentUser):
    """
    Get the current authenticated user's information.
    """
    return UserResponse.model_validate(user)
