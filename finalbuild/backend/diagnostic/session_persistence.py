from __future__ import annotations

import logging
import os
from datetime import datetime, timezone

from sqlalchemy import JSON, DateTime, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session as DbSession, mapped_column

from diagnostic.models import DiagnosticSession

log = logging.getLogger(__name__)


class SessionStateBase(DeclarativeBase):
    pass


class DiagnosticSessionStateRow(SessionStateBase):
    __tablename__ = "diagnostic_session_state"

    session_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class DiagnosticSessionPersistence:
    """Shared persistence for Android, Desktop and iOS clients through the API.

    The API keeps the domain model in memory for fast deterministic reasoning,
    while persisting a complete DiagnosticSession snapshot to the configured
    DATABASE_URL. With Docker this is the shared PostgreSQL database.
    Without DATABASE_URL the existing in-memory development mode is retained.
    """

    def __init__(self) -> None:
        self.database_url = os.getenv("DATABASE_URL", "").strip()
        self.enabled = bool(self.database_url)
        self.engine = None
        if not self.enabled:
            return

        connect_args = {"check_same_thread": False} if self.database_url.startswith("sqlite") else {}
        self.engine = create_engine(
            self.database_url,
            future=True,
            pool_pre_ping=True,
            connect_args=connect_args,
        )
        SessionStateBase.metadata.create_all(self.engine)

    def load(self) -> dict[str, DiagnosticSession]:
        if not self.enabled or self.engine is None:
            return {}

        loaded: dict[str, DiagnosticSession] = {}
        try:
            with DbSession(self.engine) as db:
                rows = db.scalars(select(DiagnosticSessionStateRow)).all()
                for row in rows:
                    try:
                        session = DiagnosticSession.model_validate(row.payload)
                    except Exception:
                        log.exception("Skipping invalid persisted session %s", row.session_id)
                        continue
                    loaded[row.session_id] = session
        except Exception:
            log.exception("Failed to load persisted diagnostic sessions")
        return loaded

    def save_all(self, sessions: dict[str, DiagnosticSession]) -> None:
        if not self.enabled or self.engine is None:
            return

        try:
            with DbSession(self.engine) as db:
                for session_id, session in sessions.items():
                    payload = session.model_dump(mode="json")
                    row = db.get(DiagnosticSessionStateRow, session_id)
                    if row is None:
                        row = DiagnosticSessionStateRow(
                            session_id=session_id,
                            payload=payload,
                        )
                        db.add(row)
                    else:
                        row.payload = payload
                        row.updated_at = datetime.now(timezone.utc)
                db.commit()
        except Exception:
            log.exception("Failed to persist diagnostic sessions")


persistence = DiagnosticSessionPersistence()
