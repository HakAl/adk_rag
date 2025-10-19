"""
SQLAlchemy models for session storage.
"""
from sqlalchemy import Column, String, Text, DateTime, Integer, ForeignKey, Index
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.database import Base


class Session(Base):
    """Session model for storing chat sessions."""

    __tablename__ = "sessions"

    session_id = Column(String(100), primary_key=True)
    user_id = Column(String(100), nullable=False, index=True)
    agent_type = Column(String(50), nullable=False)  # 'adk' or 'coordinator'
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    last_activity = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    session_metadata = Column(JSONB, nullable=True)

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