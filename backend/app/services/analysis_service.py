"""
VisionGuard AI — Main Analysis Pipeline Orchestrator
Coordinates: file intake → detection → risk → LLM → DB storage → report output
"""
from __future__ import annotations
import base64
import time
from pathlib import Path
from typing import Optional, Dict, Any
import cv2
import numpy as np
from loguru import logger
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.database import AnalysisReport, DetectedObject, Alert
from app.models.schemas import (
    AnalysisReportOut, DetectedObjectOut, AlertOut, BoundingBox
)
from app.services.detection_service import detection_service
from app.services.risk_service import risk_service
from app.services.llm_service import llm_service


class AnalysisService:
    """Runs the complete VisionGuard analysis pipeline."""

    # ── Image Analysis ────────────────────────────────────────────────────────

    def analyze_image(
        self,
        image_bytes: bytes,
        filename: str,
        db: Session,
    ) -> AnalysisReportOut:
        t0 = time.time()
        report = self._create_report(db, filename, "image", len(image_bytes))

        try:
            # Decode
            arr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if image is None:
                raise ValueError("Failed to decode image bytes")

            # Save original upload
            up_path = Path(settings.UPLOAD_DIR) / f"{report.id}_{filename}"
            cv2.imwrite(str(up_path), image)

            # ① Detection
            detections = detection_service.detect(image, frame_number=0)

            # ② Risk Assessment
            alerts, risk_score, risk_level = risk_service.assess(detections)

            # ③ LLM Reasoning
            analysis = llm_service.generate_analysis(detections, alerts, risk_score, risk_level)

            # ④ Annotated image
            annotated = detection_service.draw_detections(image, detections)
            ann_path = Path(settings.RESULTS_DIR) / f"{report.id}_annotated.jpg"
            cv2.imwrite(str(ann_path), annotated)

            proc_ms = int((time.time() - t0) * 1000)

            # ⑤ Persist
            self._save_detections(db, report.id, detections)
            self._save_alerts(db, report.id, alerts)
            self._update_report(
                db, report, proc_ms, risk_level, risk_score,
                analysis, len(detections), len(alerts),
                {
                    "object_summary": risk_service.object_summary(detections),
                    "annotated_path": str(ann_path),
                    "upload_path": str(up_path),
                },
            )
            logger.success(f"Image analysis complete: {filename} → {risk_level} ({risk_score:.3f})")

        except Exception as exc:
            logger.error(f"Image analysis failed [{filename}]: {exc}")
            report.status = "failed"
            report.metadata_json = {"error": str(exc)}
            db.commit()
            raise

        return self._to_schema(report, db)

    # ── Video Analysis ────────────────────────────────────────────────────────

    def analyze_video(
        self,
        video_bytes: bytes,
        filename: str,
        db: Session,
    ) -> AnalysisReportOut:
        t0 = time.time()
        report = self._create_report(db, filename, "video", len(video_bytes))

        vid_path = Path(settings.UPLOAD_DIR) / f"{report.id}_{filename}"
        try:
            # Save video to disk (needed for OpenCV VideoCapture)
            with open(vid_path, "wb") as fh:
                fh.write(video_bytes)

            # ① Detection across sampled frames
            vid_result = detection_service.process_video(str(vid_path))
            detections = vid_result["detections"]

            # ② Risk Assessment (aggregated)
            alerts, risk_score, risk_level = risk_service.assess_video(detections)

            # ③ LLM Reasoning
            analysis = llm_service.generate_analysis(detections, alerts, risk_score, risk_level)

            proc_ms = int((time.time() - t0) * 1000)

            # ④ Persist
            self._save_detections(db, report.id, detections)
            self._save_alerts(db, report.id, alerts)
            self._update_report(
                db, report, proc_ms, risk_level, risk_score,
                analysis, len(detections), len(alerts),
                {
                    "object_summary": risk_service.object_summary(detections),
                    "video_info": {
                        "total_frames":     vid_result["total_frames"],
                        "frames_processed": vid_result["frames_processed"],
                        "fps":              vid_result["fps"],
                        "resolution":       vid_result["resolution"],
                    },
                },
            )
            logger.success(f"Video analysis complete: {filename} → {risk_level} ({risk_score:.3f})")

        except Exception as exc:
            logger.error(f"Video analysis failed [{filename}]: {exc}")
            report.status = "failed"
            report.metadata_json = {"error": str(exc)}
            db.commit()
            raise

        return self._to_schema(report, db)

    # ── Annotated Image Retrieval ─────────────────────────────────────────────

    def get_annotated_image_b64(self, report_id: str) -> Optional[str]:
        p = Path(settings.RESULTS_DIR) / f"{report_id}_annotated.jpg"
        if p.exists():
            return base64.b64encode(p.read_bytes()).decode()
        return None

    # ── Private Helpers ───────────────────────────────────────────────────────

    @staticmethod
    def _create_report(db: Session, filename: str, file_type: str, size: int) -> AnalysisReport:
        r = AnalysisReport(
            filename=filename,
            file_type=file_type,
            file_size_bytes=size,
            status="processing",
        )
        db.add(r)
        db.commit()
        db.refresh(r)
        return r

    @staticmethod
    def _save_detections(
        db: Session,
        report_id,
        detections,
    ) -> None:
        for det in detections:
            db.add(DetectedObject(
                report_id=report_id,
                frame_number=det.frame_number,
                object_class=det.object_class,
                confidence=det.confidence,
                bbox_x1=det.bbox.x1 if det.bbox else None,
                bbox_y1=det.bbox.y1 if det.bbox else None,
                bbox_x2=det.bbox.x2 if det.bbox else None,
                bbox_y2=det.bbox.y2 if det.bbox else None,
            ))
        db.flush()

    @staticmethod
    def _save_alerts(db: Session, report_id, alerts) -> None:
        for a in alerts:
            db.add(Alert(
                report_id=report_id,
                alert_type=a.alert_type,
                severity=a.severity,
                description=a.description,
                confidence=a.confidence,
                frame_number=a.frame_number,
            ))
        db.flush()

    @staticmethod
    def _update_report(
        db: Session,
        report: AnalysisReport,
        proc_ms: int,
        risk_level: str,
        risk_score: float,
        analysis: Dict[str, str],
        total_objects: int,
        alert_count: int,
        metadata: Dict,
    ) -> None:
        report.status             = "completed"
        report.processing_time_ms = proc_ms
        report.risk_level         = risk_level
        report.risk_score         = risk_score
        report.scene_description  = analysis.get("scene_description", "")
        report.ai_reasoning       = analysis.get("ai_reasoning", "")
        report.total_objects      = total_objects
        report.alert_count        = alert_count
        report.metadata_json      = metadata
        db.commit()
        db.refresh(report)

    def _to_schema(self, report: AnalysisReport, db: Session) -> AnalysisReportOut:
        dets = db.query(DetectedObject).filter(DetectedObject.report_id == report.id).all()
        alts = db.query(Alert).filter(Alert.report_id == report.id).all()

        det_list = [
            DetectedObjectOut(
                id=d.id,
                frame_number=d.frame_number,
                object_class=d.object_class,
                confidence=d.confidence,
                bbox=BoundingBox(x1=d.bbox_x1 or 0, y1=d.bbox_y1 or 0,
                                  x2=d.bbox_x2 or 0, y2=d.bbox_y2 or 0)
                     if d.bbox_x1 is not None else None,
            )
            for d in dets
        ]
        alt_list = [
            AlertOut(
                id=a.id,
                alert_type=a.alert_type,
                severity=a.severity,
                description=a.description,
                confidence=a.confidence,
                frame_number=a.frame_number,
            )
            for a in alts
        ]

        return AnalysisReportOut(
            id=report.id,
            filename=report.filename,
            file_type=report.file_type,
            file_size_bytes=report.file_size_bytes,
            created_at=report.created_at,
            status=report.status,
            processing_time_ms=report.processing_time_ms,
            risk_level=report.risk_level,
            risk_score=report.risk_score,
            scene_description=report.scene_description,
            ai_reasoning=report.ai_reasoning,
            total_objects=report.total_objects,
            alert_count=report.alert_count,
            detected_objects=det_list,
            alerts=alt_list,
            metadata=report.metadata_json or {},
        )


analysis_service = AnalysisService()
