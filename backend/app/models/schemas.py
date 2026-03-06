"""
VisionGuard AI — Pydantic Schemas (request / response models)
"""
from __future__ import annotations
from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field


class BoundingBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectedObjectOut(BaseModel):
    id: Optional[UUID] = None
    frame_number: int = 0
    object_class: str
    confidence: float
    bbox: Optional[BoundingBox] = None

    class Config:
        from_attributes = True


class AlertOut(BaseModel):
    id: Optional[UUID] = None
    alert_type: str
    severity: str
    description: str
    confidence: Optional[float] = None
    frame_number: int = 0

    class Config:
        from_attributes = True


class AnalysisReportOut(BaseModel):
    id: Optional[UUID] = None
    filename: str
    file_type: str
    file_size_bytes: Optional[int] = None
    created_at: Optional[datetime] = None
    status: str = "pending"
    processing_time_ms: Optional[int] = None
    risk_level: Optional[str] = None
    risk_score: Optional[float] = None
    scene_description: Optional[str] = None
    ai_reasoning: Optional[str] = None
    total_objects: int = 0
    alert_count: int = 0
    detected_objects: List[DetectedObjectOut] = []
    alerts: List[AlertOut] = []
    metadata: Dict[str, Any] = {}

    class Config:
        from_attributes = True


class ReportSummaryOut(BaseModel):
    id: UUID
    filename: str
    file_type: str
    created_at: datetime
    status: str
    risk_level: Optional[str]
    risk_score: Optional[float]
    total_objects: int
    alert_count: int
    processing_time_ms: Optional[int]

    class Config:
        from_attributes = True


class StatsOut(BaseModel):
    total_analyses: int
    total_alerts: int
    risk_distribution: Dict[str, int]
    top_detected_objects: Dict[str, int]
    avg_processing_time_ms: Optional[float]
    recent_critical_alerts: int
    analyses_today: int
