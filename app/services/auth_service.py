"""Authentication service with Firebase integration."""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

import firebase_admin
from firebase_admin import auth as firebase_auth, credentials
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.user import User

logger = logging.getLogger(__name__)

# Initialize Firebase Admin SDK
_firebase_app: Optional[firebase_admin.App] = None


def init_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    global _firebase_app
    if _firebase_app is None and settings.firebase_credentials_path:
        try:
            cred = credentials.Certificate(settings.firebase_credentials_path)
            _firebase_app = firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin SDK initialized successfully")
        except Exception as e:
            logger.warning(f"Could not initialize Firebase: {e}")


class AuthService:
    """Authentication service handling Firebase verification and session management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.secret_key = settings.secret_key
        self.algorithm = "HS256"
        self.access_token_expire_days = settings.access_token_expire_days

    async def verify_firebase_token(self, id_token: str) -> Optional[dict]:
        """Verify Firebase ID token and return decoded claims."""
        try:
            if _firebase_app is None:
                # Development mode: allow mock tokens
                if settings.is_development and id_token.startswith("dev_"):
                    return self._parse_dev_token(id_token)
                raise ValueError("Firebase not initialized")

            decoded_token = firebase_auth.verify_id_token(id_token)
            return decoded_token
        except Exception as e:
            logger.error(f"Firebase token verification failed: {e}")
            return None

    def _parse_dev_token(self, token: str) -> dict:
        """Parse development mock token for testing."""
        # Format: dev_email:test@example.com or dev_phone:+4512345678
        parts = token.replace("dev_", "").split(":", 1)
        if len(parts) != 2:
            return {}

        auth_type, value = parts
        return {
            "uid": f"dev_{value.replace('@', '_').replace('+', '')}",
            "email": value if auth_type == "email" else None,
            "phone_number": value if auth_type == "phone" else None,
            "name": "Dev User",
        }

    async def get_or_create_user(self, firebase_claims: dict) -> User:
        """Get existing user or create new one from Firebase claims."""
        firebase_uid = firebase_claims.get("uid")
        if not firebase_uid:
            raise ValueError("Invalid Firebase claims: missing uid")

        # Try to find existing user
        stmt = select(User).where(User.firebase_uid == firebase_uid)
        result = await self.db.execute(stmt)
        user = result.scalar_one_or_none()

        if user:
            # Update last login
            user.last_login_at = datetime.now(timezone.utc)
            await self.db.flush()
            return user

        # Create new user
        user = User(
            firebase_uid=firebase_uid,
            email=firebase_claims.get("email"),
            phone=firebase_claims.get("phone_number"),
            display_name=firebase_claims.get("name"),
            last_login_at=datetime.now(timezone.utc),
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get user by ID."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    def create_session_token(self, user_id: UUID) -> str:
        """Create a JWT session token."""
        expire = datetime.now(timezone.utc) + timedelta(days=self.access_token_expire_days)
        payload = {
            "sub": str(user_id),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
            "type": "session",
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)

    def verify_session_token(self, token: str) -> Optional[UUID]:
        """Verify session token and return user ID."""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id = payload.get("sub")
            token_type = payload.get("type")

            if user_id and token_type == "session":
                return UUID(user_id)
            return None
        except JWTError as e:
            logger.debug(f"Session token verification failed: {e}")
            return None


# Initialize Firebase on module load
init_firebase()
