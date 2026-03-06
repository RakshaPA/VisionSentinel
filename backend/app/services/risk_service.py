"""
VisionGuard AI — Rule-Based Risk Assessment Engine
Evaluates detected objects against security rules and produces alerts + risk scores.
"""
from __future__ import annotations
from typing import List, Tuple, Dict
from loguru import logger

from app.models.schemas import DetectedObjectOut, AlertOut
from app.core.config import settings


# ── Rule Definitions ──────────────────────────────────────────────────────────

def _count(dets: List[DetectedObjectOut], cls: str) -> int:
    return sum(1 for d in dets if d.object_class == cls)

def _count_any(dets: List[DetectedObjectOut], classes: List[str]) -> int:
    return sum(1 for d in dets if d.object_class in classes)

BAG_CLASSES     = ["backpack", "handbag", "suitcase"]
VEHICLE_CLASSES = ["car", "truck", "motorcycle", "bus"]
WEAPON_CLASSES  = ["knife", "scissors"]
DEVICE_CLASSES  = ["laptop", "cell phone", "keyboard"]

RULES = [
    {
        "id": "unattended_bag",
        "severity": "high",
        "trigger": lambda d: _count_any(d, BAG_CLASSES) > 0 and _count(d, "person") == 0,
        "description": (
            "A bag or luggage item detected in the scene with no person present nearby. "
            "This is a classic indicator of an unattended object that warrants immediate inspection."
        ),
    },
    {
        "id": "crowd_gathering",
        "severity": "medium",
        "trigger": lambda d: _count(d, "person") >= settings.CROWD_THRESHOLD,
        "description": (
            "An unusually large group of people has been detected. This may indicate a crowd "
            "gathering, congestion, or a public disturbance that requires monitoring."
        ),
    },
    {
        "id": "weapon_detected",
        "severity": "critical",
        "trigger": lambda d: _count_any(d, WEAPON_CLASSES) > 0,
        "description": (
            "A potentially dangerous object (knife or sharp implement) has been detected in the scene. "
            "Immediate security assessment and response is strongly recommended."
        ),
    },
    {
        "id": "suspicious_loitering",
        "severity": "medium",
        "trigger": lambda d: (
            1 <= _count(d, "person") <= 2
            and _count_any(d, DEVICE_CLASSES) == 0
            and _count_any(d, BAG_CLASSES) == 0
        ),
        "description": (
            "One or two individuals have been detected without apparent activity or belongings. "
            "This pattern may indicate loitering or surveillance of the area."
        ),
    },
    {
        "id": "vehicle_in_restricted_zone",
        "severity": "high",
        "trigger": lambda d: (
            _count_any(d, VEHICLE_CLASSES) > 0 and _count(d, "person") > 0
        ),
        "description": (
            "A vehicle has been detected alongside persons in an area that may be pedestrian-only "
            "or restricted to authorised vehicles. Verify authorisation immediately."
        ),
    },
    {
        "id": "multiple_unattended_items",
        "severity": "high",
        "trigger": lambda d: (
            _count_any(d, BAG_CLASSES) >= 2 and _count(d, "person") <= 1
        ),
        "description": (
            "Multiple bags or luggage items detected with very few or no persons present. "
            "This scenario strongly suggests abandoned items requiring security investigation."
        ),
    },
    {
        "id": "person_with_concealed_device",
        "severity": "low",
        "trigger": lambda d: (
            _count(d, "person") >= 1 and _count_any(d, DEVICE_CLASSES) >= 1
        ),
        "description": (
            "Person(s) detected carrying electronic devices. This is typically routine but "
            "should be noted in high-security environments where devices may be restricted."
        ),
    },
]

_SEVERITY_WEIGHT = {"low": 0.15, "medium": 0.45, "high": 0.75, "critical": 1.0}


class RiskAssessmentService:
    """Evaluates a list of detections against security rules."""

    def assess(
        self,
        detections: List[DetectedObjectOut],
        frame_number: int = 0,
    ) -> Tuple[List[AlertOut], float, str]:
        """
        Run all rules.  Returns (alerts, risk_score 0-1, risk_level str).
        """
        alerts: List[AlertOut] = []
        avg_conf = (
            sum(d.confidence for d in detections) / len(detections)
            if detections else 0.5
        )

        for rule in RULES:
            try:
                if rule["trigger"](detections):
                    alerts.append(AlertOut(
                        alert_type=rule["id"],
                        severity=rule["severity"],
                        description=rule["description"],
                        confidence=round(avg_conf, 4),
                        frame_number=frame_number,
                    ))
            except Exception as exc:
                logger.error(f"Rule {rule['id']} error: {exc}")

        score = self._compute_score(alerts)
        level = self._score_to_level(score)
        logger.debug(f"Risk: score={score:.3f} level={level} alerts={len(alerts)}")
        return alerts, score, level

    def assess_video(
        self,
        all_detections: List[DetectedObjectOut],
    ) -> Tuple[List[AlertOut], float, str]:
        """Aggregate per-frame assessments; deduplicate alert types."""
        frames: Dict[int, List[DetectedObjectOut]] = {}
        for det in all_detections:
            frames.setdefault(det.frame_number, []).append(det)

        seen: set = set()
        final_alerts: List[AlertOut] = []
        for fn, dets in sorted(frames.items()):
            alerts, _, _ = self.assess(dets, fn)
            for a in alerts:
                if a.alert_type not in seen:
                    final_alerts.append(a)
                    seen.add(a.alert_type)

        score = self._compute_score(final_alerts)
        level = self._score_to_level(score)
        return final_alerts, score, level

    def object_summary(self, detections: List[DetectedObjectOut]) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for d in detections:
            summary[d.object_class] = summary.get(d.object_class, 0) + 1
        return dict(sorted(summary.items(), key=lambda x: x[1], reverse=True))

    # ── Helpers ───────────────────────────────────────────────────────────────

    @staticmethod
    def _compute_score(alerts: List[AlertOut]) -> float:
        if not alerts:
            return 0.0
        weights = [_SEVERITY_WEIGHT.get(a.severity, 0.15) for a in alerts]
        # Dominant-weight formula: 70% max + 30% mean
        score = 0.70 * max(weights) + 0.30 * (sum(weights) / len(weights))
        return round(min(score, 1.0), 4)

    @staticmethod
    def _score_to_level(score: float) -> str:
        if score >= 0.80:
            return "critical"
        if score >= 0.55:
            return "high"
        if score >= 0.30:
            return "medium"
        return "low"


risk_service = RiskAssessmentService()
