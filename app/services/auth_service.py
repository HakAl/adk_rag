import secrets
import bcrypt
from typing import Optional, Tuple
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, APIToken
from app.db.database import get_db_session
from config import settings, logger


class AuthService:
    """Service for authentication operations."""

    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt."""
        salt = bcrypt.gensalt(rounds=12)
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

    @staticmethod
    def verify_password(password: str, hashed: str) -> bool:
        """Verify a password against its hash."""
        return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

    @staticmethod
    def generate_token() -> str:
        """Generate a secure API token."""
        random_part = secrets.token_urlsafe(32)
        return f"vba_{random_part}"

    @staticmethod
    def hash_token(token: str) -> str:
        """Hash an API token for storage."""
        return bcrypt.hashpw(token.encode('utf-8'), bcrypt.gensalt(rounds=12)).decode('utf-8')

    @staticmethod
    def verify_token_hash(token: str, token_hash: str) -> bool:
        """Verify a token against its hash."""
        return bcrypt.checkpw(token.encode('utf-8'), token_hash.encode('utf-8'))

    @staticmethod
    def validate_username(username: str) -> Tuple[bool, Optional[str]]:
        """
        Validate username format.

        Returns:
            (is_valid, error_message)
        """
        if len(username) < 3:
            return False, "Username must be at least 3 characters"
        if len(username) > 30:
            return False, "Username must be at most 30 characters"
        if not username.isalnum():
            return False, "Username must contain only letters and numbers"
        return True, None

    @staticmethod
    def validate_email(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format and domain.

        Returns:
            (is_valid, error_message)
        """
        if '@' not in email:
            return False, "Invalid email format"

        domain = email.split('@')[1].lower()

        # Get allowed domains from settings
        allowed_domains_str = getattr(settings, 'email_domain_allowlist', '')
        if not allowed_domains_str:
            logger.warning("EMAIL_DOMAIN_ALLOWLIST not configured, allowing all domains")
            return True, None

        allowed_domains = [d.strip().lower() for d in allowed_domains_str.split(',')]

        if domain not in allowed_domains:
            return False, f"Email domain not allowed. Allowed domains: {', '.join(allowed_domains)}"

        return True, None

    @staticmethod
    def validate_password(password: str) -> Tuple[bool, Optional[str]]:
        """
        Validate password strength.

        Returns:
            (is_valid, error_message)
        """
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        return True, None

    async def create_user(
            self,
            username: str,
            email: str,
            password: str
    ) -> Tuple[Optional[User], Optional[str]]:
        """
        Create a new user.

        Returns:
            (user, error_message)
        """
        # Normalize
        username = username.lower().strip()
        email = email.lower().strip()

        # Validate
        valid, error = self.validate_username(username)
        if not valid:
            return None, error

        valid, error = self.validate_email(email)
        if not valid:
            return None, error

        valid, error = self.validate_password(password)
        if not valid:
            return None, error

        async with get_db_session() as db:
            # Check if username exists
            result = await db.execute(
                select(User).where(User.username == username)
            )
            if result.scalar_one_or_none():
                return None, "Username already exists"

            # Check if email exists
            result = await db.execute(
                select(User).where(User.email == email)
            )
            if result.scalar_one_or_none():
                return None, "Email already exists"

            # Create user
            user = User(
                username=username,
                email=email,
                hashed_password=self.hash_password(password),
                is_active=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            logger.info(f"Created user: {username} ({email})")
            return user, None

    async def authenticate_user(
            self,
            username_or_email: str,
            password: str
    ) -> Optional[User]:
        """
        Authenticate a user by username/email and password.

        Returns:
            User if authenticated, None otherwise
        """
        username_or_email = username_or_email.lower().strip()

        async with get_db_session() as db:
            # Try username first
            result = await db.execute(
                select(User).where(User.username == username_or_email)
            )
            user = result.scalar_one_or_none()

            # Try email if not found
            if not user:
                result = await db.execute(
                    select(User).where(User.email == username_or_email)
                )
                user = result.scalar_one_or_none()

            if not user:
                return None

            if not user.is_active:
                return None

            if not self.verify_password(password, user.hashed_password):
                return None

            return user

    async def create_api_token(
            self,
            user_id: str,
            name: Optional[str] = None
    ) -> Tuple[str, APIToken]:
        """
        Create an API token for a user.

        Returns:
            (token_string, token_model)
        """
        token = self.generate_token()
        token_hash = self.hash_token(token)

        async with get_db_session() as db:
            api_token = APIToken(
                user_id=user_id,
                token_hash=token_hash,
                name=name,
                is_active=True
            )
            db.add(api_token)
            await db.commit()
            await db.refresh(api_token)

            logger.info(f"Created API token for user {user_id}: {name or 'unnamed'}")
            return token, api_token

    async def validate_api_token(self, token: str) -> Optional[User]:
        """
        Validate an API token and return the associated user.

        Returns:
            User if token is valid, None otherwise
        """
        if not token.startswith('vba_'):
            return None

        async with get_db_session() as db:
            # Get all active tokens
            result = await db.execute(
                select(APIToken).where(APIToken.is_active == True)
            )
            tokens = result.scalars().all()

            # Check each token hash
            for api_token in tokens:
                if self.verify_token_hash(token, api_token.token_hash):
                    # Update last used
                    api_token.last_used_at = datetime.utcnow()
                    await db.commit()

                    # Get user
                    result = await db.execute(
                        select(User).where(User.id == api_token.user_id)
                    )
                    user = result.scalar_one_or_none()

                    if user and user.is_active:
                        return user

            return None

    async def get_user_by_id(self, user_id: str) -> Optional[User]:
        """Get a user by ID."""
        async with get_db_session() as db:
            result = await db.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()