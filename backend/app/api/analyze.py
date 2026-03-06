"""
VisionGuard AI — /analyze API Routes
Handles image and video upload + analysis.
"""
from __future__ import annotations
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from loguru import logger

from app.models.database import get_db
from app.models.schemas import AnalysisReportOut
from app.services.analysis_service import analysis_service
from app.core.config import settings

router = APIRouter(prefix="/analyze", tags=["Analysis"])

_ALLOWED_IMAGES = {"image/jpeg", "image/jpg", "image/png", "image/webp", "image/bmp"}
_ALLOWED_VIDEOS = {"video/mp4", "video/avi", "video/mov", "video/mkv", "video/x-msvideo", "video/quicktime"}
_MAX_BYTES = settings.MAX_FILE_SIZE_MB * 1024 * 1024


def _check_size(content: bytes) -> None:
    if len(content) > _MAX_BYTES:
        raise HTTPException(413, f"File exceeds {settings.MAX_FILE_SIZE_MB} MB limit.")


@router.post(
    "/image",
    response_model=AnalysisReportOut,
    summary="Analyse a surveillance image",
    description=(
        "Upload a JPEG / PNG / WEBP image. "
        "The pipeline runs YOLOv8 detection, rule-based risk assessment, "
        "and LLM scene reasoning. Returns a structured analysis report."
    ),
)
async def analyze_image(
    file: UploadFile = File(..., description="Surveillance image file"),
    db: Session = Depends(get_db),
):
    if file.content_type not in _ALLOWED_IMAGES:
        raise HTTPException(400, f"Unsupported type {file.content_type!r}. Expected: {_ALLOWED_IMAGES}")
    content = await file.read()
    _check_size(content)
    logger.info(f"analyze_image: {file.filename!r} {len(content)//1024} KB")
    try:
        return analysis_service.analyze_image(content, file.filename or "image.jpg", db)
    except Exception as exc:
        raise HTTPException(500, f"Analysis failed: {exc}") from exc


@router.post(
    "/video",
    response_model=AnalysisReportOut,
    summary="Analyse a surveillance video",
    description=(
        "Upload an MP4 / AVI / MOV video. "
        "Frames are sampled, YOLOv8 runs on each, and results are aggregated "
        "through risk assessment and LLM reasoning."
    ),
)
async def analyze_video(
    file: UploadFile = File(..., description="Surveillance video file"),
    db: Session = Depends(get_db),
):
    if file.content_type not in _ALLOWED_VIDEOS:
        raise HTTPException(400, f"Unsupported type {file.content_type!r}. Expected: {_ALLOWED_VIDEOS}")
    content = await file.read()
    _check_size(content)
    logger.info(f"analyze_video: {file.filename!r} {len(content)//1024} KB")
    try:
        return analysis_service.analyze_video(content, file.filename or "video.mp4", db)
    except Exception as exc:
        raise HTTPException(500, f"Analysis failed: {exc}") from exc


@router.get(
    "/image/{report_id}/annotated",
    summary="Get annotated image with bounding boxes",
)
async def get_annotated(report_id: str):
    b64 = analysis_service.get_annotated_image_b64(report_id)
    if b64 is None:
        raise HTTPException(404, "Annotated image not found for this report.")
    return {"image_base64": b64, "format": "jpeg"}
