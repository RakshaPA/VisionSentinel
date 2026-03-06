"""
VisionGuard AI — LLM Scene Reasoning Service
Supports HuggingFace Transformers, OpenAI, and intelligent rule-based fallback.
"""
from __future__ import annotations
from typing import List, Dict, Optional
from loguru import logger

from app.core.config import settings
from app.models.schemas import DetectedObjectOut, AlertOut


_SYSTEM_PROMPT = (
    "You are a professional security analyst AI embedded in a surveillance system. "
    "Your responses must be concise, accurate, and professional. "
    "Focus strictly on security implications."
)

_ANALYSIS_TEMPLATE = """Surveillance scene analysis — detected objects: {object_summary}
Active security alerts: {alert_summary}
Risk level: {risk_level} (score: {risk_score:.2f})

Provide:
1. Scene Description (2 sentences): What is happening in this scene?
2. Security Reasoning (2-3 sentences): What are the security implications?
3. Recommended Action (1 sentence): What should security personnel do?

Be direct and professional. Do not use bullet points."""


class LLMService:
    """Generates AI-powered scene analysis using LLMs with graceful fallback."""

    def __init__(self) -> None:
        self._hf_pipeline = None
        self._openai_client = None
        self._loaded = False

    def generate_analysis(
        self,
        detections: List[DetectedObjectOut],
        alerts: List[AlertOut],
        risk_score: float,
        risk_level: str,
    ) -> Dict[str, str]:
        """
        Generate scene_description and ai_reasoning.
        Tries LLM first, falls back to rule-based generation.
        """
        obj_counts: Dict[str, int] = {}
        for d in detections:
            obj_counts[d.object_class] = obj_counts.get(d.object_class, 0) + 1

        obj_summary = ", ".join(f"{c} {k}(s)" for k, c in obj_counts.items()) or "no objects"
        alert_summary = "; ".join(f"{a.alert_type} [{a.severity}]" for a in alerts) or "none"

        prompt = _ANALYSIS_TEMPLATE.format(
            object_summary=obj_summary,
            alert_summary=alert_summary,
            risk_level=risk_level,
            risk_score=risk_score,
        )

        try:
            if settings.LLM_PROVIDER == "openai" and settings.OPENAI_API_KEY:
                return self._openai_generate(prompt)
            elif settings.LLM_PROVIDER == "huggingface" and settings.HUGGINGFACE_TOKEN:
                return self._hf_generate(prompt)
        except Exception as exc:
            logger.warning(f"LLM generation failed ({exc}), using rule-based fallback")

        return self._rule_based(obj_counts, alerts, risk_score, risk_level)

    # ── OpenAI ────────────────────────────────────────────────────────────────

    def _openai_generate(self, prompt: str) -> Dict[str, str]:
        if self._openai_client is None:
            from openai import OpenAI
            self._openai_client = OpenAI(api_key=settings.OPENAI_API_KEY)
            logger.info("OpenAI client initialised")

        resp = self._openai_client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user",   "content": prompt},
            ],
            max_tokens=350,
            temperature=0.5,
        )
        text = resp.choices[0].message.content.strip()
        return self._parse_response(text)

    # ── HuggingFace ───────────────────────────────────────────────────────────

    def _hf_generate(self, prompt: str) -> Dict[str, str]:
        if self._hf_pipeline is None:
            self._load_hf()
        if self._hf_pipeline is None:
            raise RuntimeError("HuggingFace pipeline unavailable")

        full_prompt = f"{_SYSTEM_PROMPT}\n\n{prompt}"
        outputs = self._hf_pipeline(
            full_prompt,
            max_new_tokens=settings.LLM_MAX_NEW_TOKENS,
            temperature=settings.LLM_TEMPERATURE,
            do_sample=True,
            pad_token_id=50256,
        )
        generated = outputs[0]["generated_text"]
        # Strip the prompt from the response
        if full_prompt in generated:
            generated = generated[len(full_prompt):].strip()
        return self._parse_response(generated)

    def _load_hf(self) -> None:
        try:
            from transformers import pipeline
            import torch
            logger.info(f"Loading HuggingFace model: {settings.LLM_MODEL}")
            dtype = torch.float16 if settings.DEVICE == "cuda" else torch.float32
            self._hf_pipeline = pipeline(
                "text-generation",
                model=settings.LLM_MODEL,
                torch_dtype=dtype,
                device_map="auto" if settings.DEVICE == "cuda" else None,
                token=settings.HUGGINGFACE_TOKEN,
            )
            logger.success("HuggingFace model loaded")
        except Exception as exc:
            logger.warning(f"HuggingFace load failed: {exc}")

    # ── Response Parsing ──────────────────────────────────────────────────────

    @staticmethod
    def _parse_response(text: str) -> Dict[str, str]:
        lines = [ln.strip() for ln in text.split("\n") if ln.strip()]
        if len(lines) >= 3:
            return {
                "scene_description": " ".join(lines[:2]),
                "ai_reasoning": " ".join(lines[2:]),
            }
        mid = max(1, len(lines) // 2)
        return {
            "scene_description": " ".join(lines[:mid]) or text[:200],
            "ai_reasoning": " ".join(lines[mid:]) or "Analysis complete.",
        }

    # ── Rule-Based Fallback ───────────────────────────────────────────────────

    @staticmethod
    def _rule_based(
        obj_counts: Dict[str, int],
        alerts: List[AlertOut],
        risk_score: float,
        risk_level: str,
    ) -> Dict[str, str]:
        """Produce a human-readable report without any external LLM call."""
        people   = obj_counts.get("person", 0)
        bags     = sum(obj_counts.get(b, 0) for b in ["backpack", "handbag", "suitcase"])
        vehicles = sum(obj_counts.get(v, 0) for v in ["car", "truck", "motorcycle", "bus"])
        weapons  = sum(obj_counts.get(w, 0) for w in ["knife", "scissors"])
        devices  = sum(obj_counts.get(d, 0) for d in ["laptop", "cell phone"])

        # ── Scene Description ─────────────────────────────────────────────────
        parts = []
        if people == 0 and bags == 0 and vehicles == 0:
            parts.append("The surveillance area appears clear with no significant objects detected.")
        else:
            if people > 0:
                parts.append(
                    f"{people} {'person' if people == 1 else 'people'} "
                    f"{'is' if people == 1 else 'are'} visible in the surveillance area."
                )
            if bags > 0:
                parts.append(
                    f"{bags} {'bag' if bags == 1 else 'bags'} or luggage item(s) identified in the scene."
                )
            if vehicles > 0:
                parts.append(
                    f"{vehicles} vehicle(s) detected within the monitored zone."
                )
            if weapons > 0:
                parts.append("A potentially dangerous implement has been identified in the frame.")
            if devices > 0:
                parts.append(f"{devices} electronic device(s) are present.")

        scene_description = " ".join(parts)

        # ── AI Reasoning ──────────────────────────────────────────────────────
        if not alerts:
            if risk_level == "low":
                reasoning = (
                    "No security anomalies detected. The scene conforms to expected patterns "
                    "and presents no immediate concerns. Routine monitoring is sufficient."
                )
            else:
                reasoning = (
                    f"The scene presents a {risk_level} risk profile (score {risk_score:.2f}). "
                    "Security personnel should review the live feed for contextual confirmation."
                )
        else:
            reasoning_parts = []
            alert_map = {a.alert_type: a for a in alerts}

            if "weapon_detected" in alert_map:
                reasoning_parts.append(
                    "A CRITICAL alert has been raised: a potentially dangerous weapon or sharp implement "
                    "is visible in the surveillance frame. Immediate security deployment is advised."
                )
            if "unattended_bag" in alert_map or "multiple_unattended_items" in alert_map:
                bag_word = f"{bags} bag(s)" if bags > 1 else "a bag"
                reasoning_parts.append(
                    f"{bag_word} detected without an identifiable owner. "
                    "Per standard security protocol, unattended items must be investigated without delay."
                )
            if "crowd_gathering" in alert_map:
                reasoning_parts.append(
                    f"A group of {people} individuals has formed in the monitored area. "
                    "Monitor for signs of escalation, obstruction, or coordinated suspicious activity."
                )
            if "vehicle_in_restricted_zone" in alert_map:
                reasoning_parts.append(
                    "A vehicle has entered an area shared with pedestrians. "
                    "Verify vehicle authorisation and ensure no safety hazard exists."
                )
            if "suspicious_loitering" in alert_map:
                reasoning_parts.append(
                    "Individual(s) are present in the zone without evident purpose or belongings. "
                    "Extended presence without activity warrants closer observation."
                )
            if "person_with_concealed_device" in alert_map and len(alerts) == 1:
                reasoning_parts.append(
                    "Routine detection: person(s) carrying electronic devices. "
                    "Note this for high-security environments where devices may be restricted."
                )

            reasoning = " ".join(reasoning_parts) if reasoning_parts else (
                f"Scene assessed at {risk_level.upper()} risk level ({risk_score:.2f}). "
                "Review the full alert list and apply appropriate security protocols."
            )

        return {
            "scene_description": scene_description,
            "ai_reasoning": reasoning,
        }


llm_service = LLMService()
