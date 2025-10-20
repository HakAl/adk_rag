"""
SQLAlchemy models for session storage.
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Index, Boolean
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.db.database import Base


class Session(Base):
    """Session model for storing chat sessions."""

    __tablename__ = "sessions"

    session_id = Column(String(100), primary_key=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)  # 'adk' or 'coordinator'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    session_metadata = Column(JSONB, nullable=True)

    # Add relationship
    user = relationship("User", back_populates="sessions")

    # Relationship to messages
    messages = relationship("SessionMessage", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Session(session_id={self.session_id}, user_id={self.user_id}, agent_type={self.agent_type})>"


class SessionMessage(Base):
    """Session message model for storing conversation history."""

    __tablename__ = "session_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(100), ForeignKey("sessions.session_id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship to session
    session = relationship("Session", back_populates="messages")

    # Index for faster queries
    __table_args__ = (
        Index('idx_session_messages_session_id', 'session_id'),
    )

    def __repr__(self):
        return f"<SessionMessage(id={self.id}, session_id={self.session_id}, role={self.role})>"


class User(Base):
    """User model for authentication."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(30), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)

    # Email verification fields
    email_verified = Column(Boolean, default=False, nullable=False)
    email_verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    api_tokens = relationship("APIToken", back_populates="user", cascade="all, delete-orphan")
    email_verifications = relationship("EmailVerification", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class APIToken(Base):
    """API token model for CLI authentication."""

    __tablename__ = "api_tokens"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=True)  # e.g., "John's Laptop"
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_used_at = Column(DateTime(timezone=True), nullable=True)

    # Relationship
    user = relationship("User", back_populates="api_tokens")

    # Index for faster lookups
    __table_args__ = (
        Index('idx_api_tokens_user_id', 'user_id'),
    )

    def __repr__(self):
        return f"<APIToken(id={self.id}, user_id={self.user_id}, name={self.name})>"


class EmailVerification(Base):
    """Email verification model for storing verification tokens."""

    __tablename__ = "email_verifications"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token_hash = Column(String(255), unique=True, nullable=False, index=True)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    user = relationship("User", back_populates="email_verifications")

    # Indexes for faster lookups
    __table_args__ = (
        Index('idx_email_verifications_user_id', 'user_id'),
        Index('idx_email_verifications_token_hash', 'token_hash'),
        Index('idx_email_verifications_expires_at', 'expires_at'),
    )

    def __repr__(self):
        return f"<EmailVerification(id={self.id}, user_id={self.user_id})>"