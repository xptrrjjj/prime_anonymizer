"""Database setup and session management."""

import json
from contextlib import contextmanager
from pathlib import Path
from typing import Dict, Generator, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from app.config import get_settings, ensure_directories
from app.models import Base, AuditLog


class DatabaseManager:
    """Database manager for SQLite operations."""

    def __init__(self) -> None:
        """Initialize database manager."""
        self.settings = get_settings()
        ensure_directories()

        # Ensure database file path is absolute and directory exists
        db_path = Path(self.settings.db_path).resolve()
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Create SQLite engine with thread safety
        self.engine = create_engine(
            f"sqlite:///{db_path}",
            connect_args={"check_same_thread": False},
            echo=False,
        )

        # Create tables
        Base.metadata.create_all(bind=self.engine)

        # Session factory
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.engine
        )

    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Get database session with automatic cleanup."""
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def create_audit_log(
        self,
        request_id: str,
        client_ip: str,
        status_code: int,
        elapsed_ms: int,
        payload_bytes: int,
        pii_counts: Dict[str, int],
        error_msg: Optional[str] = None,
    ) -> None:
        """Create an audit log entry."""
        with self.get_session() as session:
            pii_total = sum(pii_counts.values())
            pii_by_type_json = json.dumps(pii_counts)

            audit_log = AuditLog(
                request_id=request_id,
                client_ip=client_ip,
                status_code=status_code,
                elapsed_ms=elapsed_ms,
                payload_bytes=payload_bytes,
                pii_total=pii_total,
                pii_by_type_json=pii_by_type_json,
                error_msg=error_msg,
            )

            session.add(audit_log)


# Global database manager instance
db_manager = DatabaseManager()