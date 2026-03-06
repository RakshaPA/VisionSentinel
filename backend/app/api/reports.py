"""
VisionGuard AI — /reports API Routes
CRUD operations and statistics for analysis reports.
"""
from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from uuid import UUID
from datetime import datetime, timezone, timedelta
from loguru import logger

from app.models.database import get_db, AnalysisReport, DetectedObject, Alert
from app.models.schemas import AnalysisReportOut, ReportSummaryOut, StatsOut
from app.services.analysis_service import analysis_service

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/", response_model=List[ReportSummaryOut], summary="List analysis reports")
async def list_reports(
    skip:       int            = Query(0,    ge=0,                   description="Pagination offset"),
    limit:      int            = Query(20,   ge=1, le=100,           description="Page size"),
    risk_level: Optional[str]  = Query(None, pattern="^(low|medium|high|critical)$"),
    file_type:  Optional[str]  = Query(None, pattern="^(image|video)$"),
    db: Session = Depends(get_db),
):
    q = db.query(AnalysisReport).order_by(desc(AnalysisReport.created_at))
    if risk_level:
        q = q.filter(AnalysisReport.risk_level == risk_level)
    if file_type:
        q = q.filter(AnalysisReport.file_type == file_type)
    rows = q.offset(skip).limit(limit).all()
    return [
        ReportSummaryOut(
            id=r.id, filename=r.filename, file_type=r.file_type,
            created_at=r.created_at, status=r.status,
            risk_level=r.risk_level, risk_score=r.risk_score,
            total_objects=r.total_objects, alert_count=r.alert_count,
            processing_time_ms=r.processing_time_ms,
        )
        for r in rows
    ]


@router.get("/stats", response_model=StatsOut, summary="System-wide statistics")
async def get_stats(db: Session = Depends(get_db)):
    total       = db.query(func.count(AnalysisReport.id)).scalar() or 0
    total_alts  = db.query(func.count(Alert.id)).scalar() or 0

    risk_rows = (
        db.query(AnalysisReport.risk_level, func.count(AnalysisReport.id))
        .filter(AnalysisReport.risk_level.isnot(None))
        .group_by(AnalysisReport.risk_level)
        .all()
    )
    risk_dist = {r[0]: r[1] for r in risk_rows}

    obj_rows = (
        db.query(DetectedObject.object_class, func.count(DetectedObject.id))
        .group_by(DetectedObject.object_class)
        .order_by(desc(func.count(DetectedObject.id)))
        .limit(10).all()
    )
    top_objs = {r[0]: r[1] for r in obj_rows}

    avg_t = db.query(func.avg(AnalysisReport.processing_time_ms)).scalar()

    critical_alerts = db.query(func.count(Alert.id)).filter(Alert.severity == "critical").scalar() or 0

    today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    today_count = (
        db.query(func.count(AnalysisReport.id))
        .filter(AnalysisReport.created_at >= today_start)
        .scalar() or 0
    )

    return StatsOut(
        total_analyses=total,
        total_alerts=total_alts,
        risk_distribution=risk_dist,
        top_detected_objects=top_objs,
        avg_processing_time_ms=float(avg_t) if avg_t else None,
        recent_critical_alerts=critical_alerts,
        analyses_today=today_count,
    )


@router.get("/{report_id}", response_model=AnalysisReportOut, summary="Get full report")
async def get_report(report_id: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(report_id)
    except ValueError:
        raise HTTPException(400, "Invalid UUID format.")
    report = db.query(AnalysisReport).filter(AnalysisReport.id == uid).first()
    if not report:
        raise HTTPException(404, f"Report {report_id} not found.")
    return analysis_service._to_schema(report, db)


@router.delete("/{report_id}", summary="Delete a report")
async def delete_report(report_id: str, db: Session = Depends(get_db)):
    try:
        uid = UUID(report_id)
    except ValueError:
        raise HTTPException(400, "Invalid UUID format.")
    report = db.query(AnalysisReport).filter(AnalysisReport.id == uid).first()
    if not report:
        raise HTTPException(404, f"Report {report_id} not found.")

    db.query(DetectedObject).filter(DetectedObject.report_id == uid).delete()
    db.query(Alert).filter(Alert.report_id == uid).delete()
    db.delete(report)
    db.commit()
    logger.info(f"Deleted report {report_id}")
    return {"deleted": True, "id": report_id}
