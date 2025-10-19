"""
PostgreSQL-backed session service for ADK and Coordinator agents.
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from google.adk.sessions import InMemorySessionService
from google.genai import types

from config import logger
from app.db.database import get_db_session
from app.db.models import Session as SessionModel, SessionMessage


class PostgreSQLSessionService(InMemorySessionService):
    """PostgreSQL-backed session service extending ADK's InMemorySessionService."""

    async def create_session(
        self,
        app_name: str,
        user_id: str,
        session_id: str,
        agent_type: str = "adk"
    ) -> None:
        """
        Create a new session in the database.

        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session identifier
            agent_type: Type of agent ('adk' or 'coordinator')
        """
        # Don't call parent - it has a different signature
        # Just persist to database
        async with get_db_session() as db:
            session = SessionModel(
                session_id=session_id,
                user_id=user_id,
                agent_type=agent_type,
                session_metadata={"app_name": app_name}
            )
            db.add(session)
            await db.commit()
            logger.info(f"Created session in DB: {session_id} (type: {agent_type})")

    async def get_session_history(
        self,
        app_name: str,
        user_id: str,
        session_id: str
    ) -> List[types.Content]:
        """
        Get session history for ADK agent.

        First checks database, then falls back to in-memory.

        Args:
            app_name: Application name
            user_id: User identifier
            session_id: Session identifier

        Returns:
            List of Content objects for ADK
        """
        try:
            async with get_db_session() as db:
                # Verify session exists in DB
                result = await db.execute(
                    select(SessionModel).where(SessionModel.session_id == session_id)
                )
                session = result.scalar_one_or_none()

                if session:
                    # Update last activity
                    await db.execute(
                        update(SessionModel)
                        .where(SessionModel.session_id == session_id)
                        .values(last_activity=datetime.utcnow())
                    )
                    await db.commit()

                    # Get messages from DB
                    result = await db.execute(
                        select(SessionMessage)
                        .where(SessionMessage.session_id == session_id)
                        .order_by(SessionMessage.created_at)
                    )
                    messages = result.scalars().all()

                    # Convert to ADK Content format
                    history = []
                    for msg in messages:
                        history.append(
                            types.Content(
                                role=msg.role,
                                parts=[types.Part(text=msg.content)]
                            )
                        )

                    return history
        except Exception as e:
            logger.warning(f"Failed to get session from DB: {e}")

        # Fallback to in-memory
        return await super().get_session_history(app_name, user_id, session_id)

    async def save_message(
        self,
        session_id: str,
        role: str,
        content: str
    ) -> None:
        """
        Save a message to the session.

        Args:
            session_id: Session identifier
            role: Message role ('user' or 'assistant')
            content: Message content
        """
        async with get_db_session() as db:
            message = SessionMessage(
                session_id=session_id,
                role=role,
                content=content
            )
            db.add(message)

            # Update session last activity
            await db.execute(
                update(SessionModel)
                .where(SessionModel.session_id == session_id)
                .values(last_activity=datetime.utcnow())
            )

            await db.commit()

    async def session_exists(self, session_id: str) -> bool:
        """
        Check if a session exists in the database.

        Args:
            session_id: Session identifier

        Returns:
            True if session exists, False otherwise
        """
        async with get_db_session() as db:
            result = await db.execute(
                select(SessionModel).where(SessionModel.session_id == session_id)
            )
            return result.scalar_one_or_none() is not None

    async def get_coordinator_history(
        self,
        session_id: str
    ) -> List[Dict[str, str]]:
        """
        Get session history for coordinator agent.

        Args:
            session_id: Session identifier

        Returns:
            List of message dicts with 'role' and 'content'
        """
        async with get_db_session() as db:
            # Update last activity
            await db.execute(
                update(SessionModel)
                .where(SessionModel.session_id == session_id)
                .values(last_activity=datetime.utcnow())
            )

            # Get messages
            result = await db.execute(
                select(SessionMessage)
                .where(SessionMessage.session_id == session_id)
                .order_by(SessionMessage.created_at)
            )
            messages = result.scalars().all()

            await db.commit()

            return [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]

    async def delete_session(self, session_id: str) -> None:
        """
        Delete a session and all its messages.

        Args:
            session_id: Session identifier
        """
        async with get_db_session() as db:
            result = await db.execute(
                select(SessionModel).where(SessionModel.session_id == session_id)
            )
            session = result.scalar_one_or_none()

            if session:
                await db.delete(session)
                await db.commit()
                logger.info(f"Deleted session from DB: {session_id}")