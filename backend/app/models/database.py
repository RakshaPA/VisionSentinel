"""
VisionGuard AI — SQLAlchemy ORM Models & Database Session
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, String, Float, Integer,
    Text, BigInteger, ForeignKey, DateTime
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings


engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
    connect_args={"connect_timeout": 10},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yield a database session."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables() -> None:
    """Create all tables (called on startup if not using migrations)."""
    Base.metadata.create_all(bind=engine)


# ── ORM Models ────────────────────────────────────────────────────────────────

class AnalysisReport(Base):
    __tablename__ = "analysis_reports"

    id                  = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename            = Column(String(512), nullable=False)
    file_type           = Column(String(20),  nullable=False)   # image | video
    file_size_bytes     = Column(BigInteger)
    created_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at          = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    status              = Column(String(20),  default="pending")
    processing_time_ms  = Column(Integer)
    risk_level          = Column(String(20))
    risk_score          = Column(Float)
    scene_description   = Column(Text)
    ai_reasoning        = Column(Text)
    total_objects       = Column(Integer, default=0)
    alert_count         = Column(Integer, default=0)
    metadata_json       = Column("metadata", JSONB, default=dict)


class DetectedObject(Base):
    __tablename__ = "detected_objects"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id       = Column(UUID(as_uuid=True), ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=False)
    frame_number    = Column(Integer, default=0)
    object_class    = Column(String(100), nullable=False)
    confidence      = Column(Float, nullable=False)
    bbox_x1         = Column(Float)
    bbox_y1         = Column(Float)
    bbox_x2         = Column(Float)
    bbox_y2         = Column(Float)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))


class Alert(Base):
    __tablename__ = "alerts"

    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    report_id       = Column(UUID(as_uuid=True), ForeignKey("analysis_reports.id", ondelete="CASCADE"), nullable=False)
    alert_type      = Column(String(100), nullable=False)
    severity        = Column(String(20),  nullable=False)
    description     = Column(Text, nullable=False)
    confidence      = Column(Float)
    frame_number    = Column(Integer, default=0)
    created_at      = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))