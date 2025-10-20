import secrets
import bcrypt
from typing import Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User, APIToken, EmailVerification
from app.db.database import get_db_session
from app.services.email_service import get_email_service
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
    def generate_verification_token() -> str:
        """Generate a secure email verification token."""
        return secrets.token_urlsafe(32)

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
        Create a new user and send verification email.

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

            # Create user (unverified)
            user = User(
                username=username,
                email=email,
                hashed_password=self.hash_password(password),
                is_active=True,
                email_verified=False
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

            # Create verification token
            verification_token = self.generate_verification_token()
            token_hash = self.hash_token(verification_token)
            expires_at = datetime.utcnow() + timedelta(hours=24)

            email_verification = EmailVerification(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            db.add(email_verification)
            await db.commit()

            logger.info(f"Created user: {username} ({email})")

            # Send verification email (async, don't wait)
            email_service = get_email_service()
            try:
                await email_service.send_verification_email(
                    to_email=email,
                    username=username,
                    verification_token=verification_token
                )
            except Exception as e:
                logger.error(f"Failed to send verification email: {e}")
                # Don't fail registration if email fails

            return user, None

    async def verify_email(self, token: str) -> Tuple[bool, Optional[str]]:
        """
        Verify email with token.

        Returns:
            (success, error_message)
        """
        async with get_db_session() as db:
            # Get all active verification tokens
            result = await db.execute(
                select(EmailVerification).where(
                    EmailVerification.expires_at > datetime.utcnow()
                )
            )
            verifications = result.scalars().all()

            # Check each token hash
            for verification in verifications:
                if self.verify_token_hash(token, verification.token_hash):
                    # Get user
                    result = await db.execute(
                        select(User).where(User.id == verification.user_id)
                    )
                    user = result.scalar_one_or_none()

                    if not user:
                        return False, "User not found"

                    # Mark as verified
                    user.email_verified = True
                    user.email_verified_at = datetime.utcnow()

                    # Delete verification token
                    await db.delete(verification)
                    await db.commit()

                    logger.info(f"Email verified for user: {user.username}")
                    return True, None

            return False, "Invalid or expired verification token"

    async def resend_verification_email(self, email: str) -> Tuple[bool, Optional[str]]:
        """
        Resend verification email.

        Returns:
            (success, error_message)
        """
        email = email.lower().strip()

        async with get_db_session() as db:
            # Get user
            result = await db.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()

            if not user:
                return False, "Email not found"

            if user.email_verified:
                return False, "Email already verified"

            # Delete old verification tokens for this user
            await db.execute(
                delete(EmailVerification).where(EmailVerification.user_id == user.id)
            )

            # Create new verification token
            verification_token = self.generate_verification_token()
            token_hash = self.hash_token(verification_token)
            expires_at = datetime.utcnow() + timedelta(hours=24)

            email_verification = EmailVerification(
                user_id=user.id,
                token_hash=token_hash,
                expires_at=expires_at
            )
            db.add(email_verification)
            await db.commit()

            # Send verification email
            email_service = get_email_service()
            success = await email_service.send_verification_email(
                to_email=email,
                username=user.username,
                verification_token=verification_token
            )

            if success:
                logger.info(f"Resent verification email to: {email}")
                return True, None
            else:
                return False, "Failed to send verification email"

    async def authenticate_user(
            self,
            username_or_email: str,
            password: str
    ) -> Optional[User]:
        """
        Authenticate a user by username/email and password.
        Only allows login if email is verified.

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

            # Check if email is verified
            if not user.email_verified:
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