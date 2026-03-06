# 🛡️ VisionGuard AI
### Scene Understanding & Risk Detection System

> Intelligent surveillance analysis combining **YOLOv8** computer vision with **LLM reasoning** to automatically understand scenes and detect security threats.

---

## 🏗️ System Architecture

```
┌──────────────────────────────────────────────────────────┐
│              VISIONGUARD AI PIPELINE                     │
│                                                          │
│  Upload  →  YOLOv8  →  Risk Engine  →  LLM  →  Report  │
│  Image/      Object     Rule-Based    Scene    JSON +    │
│  Video       Detect     Threat Eval   Reason   Alerts    │
└──────────────────────────────────────────────────────────┘

┌────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Streamlit UI  │────▶│  FastAPI Backend  │────▶│  PostgreSQL DB  │
│   :8501        │     │    :8000          │     │    :5432        │
└────────────────┘     └──────────────────┘     └─────────────────┘
                               │
               ┌───────────────┼───────────────┐
               ▼               ▼               ▼
        ┌──────────┐    ┌──────────┐    ┌──────────┐
        │ YOLOv8   │    │ OpenCV   │    │ HF / GPT │
        │ Detect   │    │ Video    │    │ Reasoning│
        └──────────┘    └──────────┘    └──────────┘
```

---

## 🚀 Quick Start

### Option A — Docker Compose (Recommended)

```bash
# 1. Clone repo and enter directory
git clone <repo-url>
cd visionguard

# 2. Configure environment
cp .env.example .env
# Edit .env → add HUGGINGFACE_TOKEN or OPENAI_API_KEY

# 3. Launch all services
docker-compose up --build

# 4. Open in browser
#    Streamlit UI  → http://localhost:8501
#    FastAPI Docs  → http://localhost:8000/docs
#    API Health    → http://localhost:8000/health
```

### Option B — Local Development

```bash
# Start PostgreSQL via Docker
docker-compose up db -d

# Backend
cd backend
pip install -r requirements.txt
export DATABASE_URL=postgresql://visionguard:visionguard_pass@localhost:5432/visionguard
uvicorn app.main:app --reload --port 8000

# Frontend (new terminal)
cd frontend
pip install -r requirements.txt
BACKEND_URL=http://localhost:8000 streamlit run app.py
```

---

## 📦 Tech Stack

| Component        | Technology                    | Version  |
|-----------------|-------------------------------|----------|
| Object Detection | Ultralytics YOLOv8            | 8.2      |
| Video Processing | OpenCV                        | 4.10     |
| AI Reasoning     | HuggingFace Transformers      | 4.42     |
| Alt. LLM         | OpenAI GPT-3.5/4              | —        |
| REST API         | FastAPI + Uvicorn             | 0.111    |
| Frontend         | Streamlit                     | 1.36     |
| Database ORM     | SQLAlchemy                    | 2.0      |
| Database         | PostgreSQL                    | 15       |
| Containers       | Docker + Docker Compose       | —        |

---

## 🎯 Features

| Feature | Description |
|---------|-------------|
| 📷 Image Analysis | Upload JPEG/PNG, get instant YOLOv8 detections + AI report |
| 🎬 Video Analysis | MP4/AVI CCTV footage — frame sampling + aggregated report |
| 🔍 Object Detection | 80+ COCO classes with confidence scores and bounding boxes |
| 🧠 Scene Understanding | LLM generates human-readable scene description + reasoning |
| ⚠️ Risk Assessment | 7 rule-based alert types, 4 severity levels |
| 📊 Dashboard | Live system stats, risk distribution charts, top objects |
| 📋 Reports | Full history with filtering, detail views, delete |
| 🖼️ Annotated Output | Colour-coded bounding boxes drawn on original image |
| 🐳 Docker Ready | One command full-stack deployment |

---

## ⚠️ Risk Levels & Alert Types

### Risk Levels

| Level | Score | Indicator |
|-------|-------|-----------|
| 🟢 LOW | 0.00–0.29 | Normal activity |
| 🟡 MEDIUM | 0.30–0.54 | Monitor situation |
| 🟠 HIGH | 0.55–0.79 | Action recommended |
| 🔴 CRITICAL | 0.80–1.00 | Immediate response |

### Alert Rules

| Rule ID | Severity | Trigger Condition |
|---------|----------|-------------------|
| `unattended_bag` | HIGH | Bag detected, no person visible |
| `crowd_gathering` | MEDIUM | People count ≥ `CROWD_THRESHOLD` |
| `weapon_detected` | CRITICAL | Knife or scissors detected |
| `suspicious_loitering` | MEDIUM | Person(s) with no belongings/activity |
| `vehicle_in_restricted_zone` | HIGH | Vehicle + persons in same frame |
| `multiple_unattended_items` | HIGH | ≥2 bags with ≤1 person |
| `person_with_concealed_device` | LOW | Person carrying electronic device |

---

## 📡 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/analyze/image` | Analyse a surveillance image |
| `POST` | `/api/v1/analyze/video` | Analyse a CCTV video |
| `GET` | `/api/v1/analyze/image/{id}/annotated` | Annotated image (base64) |
| `GET` | `/api/v1/reports/` | List reports (filter: risk_level, file_type) |
| `GET` | `/api/v1/reports/stats` | System-wide statistics |
| `GET` | `/api/v1/reports/{id}` | Full report detail |
| `DELETE` | `/api/v1/reports/{id}` | Delete report + data |
| `GET` | `/health` | Health check |
| `GET` | `/docs` | Swagger UI |

---

## 📁 Project Structure

```
visionguard/
├── backend/
│   ├── app/
│   │   ├── main.py                     # FastAPI entry + lifespan
│   │   ├── core/
│   │   │   └── config.py               # Pydantic settings (env vars)
│   │   ├── models/
│   │   │   ├── database.py             # SQLAlchemy ORM models
│   │   │   └── schemas.py              # Pydantic request/response schemas
│   │   ├── api/
│   │   │   ├── analyze.py              # POST /analyze/image & /video
│   │   │   └── reports.py              # GET/DELETE /reports
│   │   └── services/
│   │       ├── detection_service.py    # YOLOv8 wrapper + video processor
│   │       ├── risk_service.py         # Rule engine + score computation
│   │       ├── llm_service.py          # HF / OpenAI / rule-based fallback
│   │       └── analysis_service.py     # Pipeline orchestrator
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── app.py                          # Streamlit dashboard (all pages)
│   ├── requirements.txt
│   └── Dockerfile
├── docker/
│   └── init.sql                        # PostgreSQL schema + indexes
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## ⚙️ Configuration

Key `.env` settings:

```env
# LLM — choose provider
LLM_PROVIDER=huggingface          # or: openai
HUGGINGFACE_TOKEN=hf_...          # get at huggingface.co/settings/tokens
OPENAI_API_KEY=sk-...             # alternative

# Detection accuracy vs speed
YOLO_MODEL=yolov8n.pt             # n=nano(fast) s=small m=medium x=best
CONFIDENCE_THRESHOLD=0.50         # lower = more detections

# Video sampling
MAX_VIDEO_FRAMES=300              # cap frames per video
VIDEO_FRAME_SKIP=5                # analyse every 5th frame

# Risk tuning
CROWD_THRESHOLD=5                 # people count to fire crowd alert
```

The LLM layer falls back to intelligent rule-based scene descriptions if
no API key is configured — the system works fully out of the box for detection
and risk assessment without any LLM token.
