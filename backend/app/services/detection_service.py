"""
VisionGuard AI — YOLOv8 Object Detection Service
Wraps Ultralytics YOLOv8 with lazy loading, video processing, and bbox annotation.
"""
from __future__ import annotations
import cv2
import numpy as np
from pathlib import Path
from typing import List, Optional, Dict, Any
from loguru import logger

from app.core.config import settings
from app.models.schemas import DetectedObjectOut, BoundingBox

# Colour palette for bounding boxes (per class)
_BBOX_COLORS: Dict[str, tuple] = {
    "person":    (0, 220, 100),
    "backpack":  (0, 165, 255),
    "handbag":   (0, 165, 255),
    "suitcase":  (0, 165, 255),
    "knife":     (0,   0, 255),
    "scissors":  (0,   0, 255),
    "car":       (255, 180,  0),
    "truck":     (255, 140,  0),
    "motorcycle":(255, 200,  0),
    "cell phone":(180,   0, 255),
    "laptop":    (180,   0, 255),
}
_DEFAULT_COLOR = (0, 212, 255)


class DetectionService:
    """Lazy-loads YOLOv8 and exposes detect/video helpers."""

    def __init__(self) -> None:
        self._model = None
        self._attempted = False

    # ── Model Loading ─────────────────────────────────────────────────────────

    def _load_model(self) -> None:
        if self._attempted:
            return
        self._attempted = True
        try:
            from ultralytics import YOLO
            logger.info(f"Loading YOLO model: {settings.YOLO_MODEL}")
            self._model = YOLO(settings.YOLO_MODEL)
            logger.success("YOLOv8 model loaded successfully")
        except Exception as exc:
            logger.warning(f"Could not load YOLOv8: {exc}. Using mock detections.")

    # ── Core Detection ────────────────────────────────────────────────────────

    def detect(
        self,
        image: np.ndarray,
        frame_number: int = 0,
        conf_threshold: Optional[float] = None,
    ) -> List[DetectedObjectOut]:
        """Run inference on a BGR numpy array. Returns list of detections."""
        self._load_model()
        if self._model is None:
            return self._mock_detections(frame_number)

        thresh = conf_threshold or settings.CONFIDENCE_THRESHOLD
        try:
            results = self._model(
                image,
                conf=thresh,
                iou=settings.IOU_THRESHOLD,
                device=settings.DEVICE,
                verbose=False,
            )
            detections: List[DetectedObjectOut] = []
            for result in results:
                if result.boxes is None:
                    continue
                for box in result.boxes:
                    cls_id = int(box.cls[0])
                    conf   = float(box.conf[0])
                    x1, y1, x2, y2 = [round(v, 1) for v in box.xyxy[0].tolist()]
                    cls_name = result.names.get(cls_id, f"class_{cls_id}")
                    detections.append(DetectedObjectOut(
                        frame_number=frame_number,
                        object_class=cls_name,
                        confidence=round(conf, 4),
                        bbox=BoundingBox(x1=x1, y1=y1, x2=x2, y2=y2),
                    ))
            logger.debug(f"Frame {frame_number}: {len(detections)} detections")
            return detections
        except Exception as exc:
            logger.error(f"Detection error frame {frame_number}: {exc}")
            return []

    def detect_from_path(self, path: str, frame_number: int = 0) -> List[DetectedObjectOut]:
        img = cv2.imread(path)
        if img is None:
            raise ValueError(f"Cannot read image: {path}")
        return self.detect(img, frame_number)

    # ── Video Processing ──────────────────────────────────────────────────────

    def process_video(
        self,
        video_path: str,
        max_frames: Optional[int] = None,
        frame_skip: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Sample frames from a video file and run detection on each.
        Returns aggregated detections + video metadata.
        """
        max_f  = max_frames or settings.MAX_VIDEO_FRAMES
        skip   = frame_skip  or settings.VIDEO_FRAME_SKIP

        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {video_path}")

        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps          = cap.get(cv2.CAP_PROP_FPS) or 25.0
        width        = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height       = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        all_dets: List[DetectedObjectOut] = []
        processed = 0
        idx = 0

        logger.info(f"Processing video: {total_frames} frames, {fps:.1f} fps, {width}x{height}")
        while cap.isOpened() and processed < max_f:
            ret, frame = cap.read()
            if not ret:
                break
            if idx % skip == 0:
                dets = self.detect(frame, frame_number=idx)
                all_dets.extend(dets)
                processed += 1
            idx += 1

        cap.release()
        logger.info(f"Video done: {processed} frames sampled, {len(all_dets)} total detections")

        return {
            "total_frames": total_frames,
            "frames_processed": processed,
            "fps": round(fps, 2),
            "resolution": f"{width}x{height}",
            "detections": all_dets,
        }

    # ── Annotation ────────────────────────────────────────────────────────────

    def draw_detections(
        self,
        image: np.ndarray,
        detections: List[DetectedObjectOut],
    ) -> np.ndarray:
        """Draw bounding boxes + labels on a copy of the image."""
        out = image.copy()
        for det in detections:
            if det.bbox is None:
                continue
            color = _BBOX_COLORS.get(det.object_class, _DEFAULT_COLOR)
            x1, y1, x2, y2 = int(det.bbox.x1), int(det.bbox.y1), int(det.bbox.x2), int(det.bbox.y2)
            cv2.rectangle(out, (x1, y1), (x2, y2), color, 2)
            label = f"{det.object_class} {det.confidence:.0%}"
            (lw, lh), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.55, 1)
            cv2.rectangle(out, (x1, y1 - lh - 6), (x1 + lw + 4, y1), color, -1)
            cv2.putText(out, label, (x1 + 2, y1 - 4),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 0, 0), 1, cv2.LINE_AA)
        return out

    # ── Mock Fallback ─────────────────────────────────────────────────────────

    @staticmethod
    def _mock_detections(frame_number: int) -> List[DetectedObjectOut]:
        """Synthetic detections used when YOLOv8 is unavailable (testing/demo)."""
        return [
            DetectedObjectOut(
                frame_number=frame_number,
                object_class="person",
                confidence=0.93,
                bbox=BoundingBox(x1=80,  y1=40,  x2=280, y2=490),
            ),
            DetectedObjectOut(
                frame_number=frame_number,
                object_class="backpack",
                confidence=0.81,
                bbox=BoundingBox(x1=300, y1=300, x2=460, y2=480),
            ),
        ]


detection_service = DetectionService()
