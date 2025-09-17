"""SQLAlchemy ORM models for the application."""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class AuditLog(Base):
    """Audit log model for tracking API requests."""

    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts = Column(DateTime, nullable=False, default=datetime.utcnow)
    request_id = Column(String(36), nullable=False, index=True)
    client_ip = Column(String(45), nullable=False)  # IPv6 max length
    status_code = Column(Integer, nullable=False)
    elapsed_ms = Column(Integer, nullable=False)
    payload_bytes = Column(Integer, nullable=False)
    pii_total = Column(Integer, nullable=False, default=0)
    pii_by_type_json = Column(Text, nullable=False, default="{}")
    error_msg = Column(Text, nullable=True)

    def __repr__(self) -> str:
        return (
            f"<AuditLog(id={self.id}, request_id={self.request_id}, "
            f"status_code={self.status_code}, pii_total={self.pii_total})>"
        )