"""VisionGuard AI — Application Settings"""
from __future__ import annotations
from typing import List, Optional
from pydantic_settings import BaseSettings
import os


class Settings(BaseSettings):
    APP_NAME: str = "VisionGuard AI"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False
    SECRET_KEY: str = "change-me-in-production"

    DATABASE_URL: str = "postgresql://visionguard:visionguard_pass@db:5432/visionguard"

    YOLO_MODEL: str = "yolov8n.pt"
    CONFIDENCE_THRESHOLD: float = 0.50
    IOU_THRESHOLD: float = 0.45
    DEVICE: str = "cpu"

    LLM_PROVIDER: str = "huggingface"
    HUGGINGFACE_TOKEN: Optional[str] = None
    LLM_MODEL: str = "Qwen/Qwen2.5-1.5B-Instruct"
    LLM_MAX_NEW_TOKENS: int = 400
    LLM_TEMPERATURE: float = 0.6
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-3.5-turbo"

    CROWD_THRESHOLD: int = 5
    HIGH_RISK_THRESHOLD: float = 0.70

    MAX_VIDEO_FRAMES: int = 300
    VIDEO_FRAME_SKIP: int = 5

    UPLOAD_DIR: str = "/app/uploads"
    RESULTS_DIR: str = "/app/results"
    MAX_FILE_SIZE_MB: int = 100

    API_V1_PREFIX: str = "/api/v1"
    CORS_ORIGINS: List[str] = ["http://localhost:8501", "http://frontend:8501", "*"]

    class Config:
        env_file = ".env"
        extra = "ignore"

    def ensure_dirs(self) -> None:
        os.makedirs(self.UPLOAD_DIR, exist_ok=True)
        os.makedirs(self.RESULTS_DIR, exist_ok=True)


settings = Settings()
settings.ensure_dirs()
