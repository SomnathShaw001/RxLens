# RxLens (AI Multilingual Prescription Digitizer)

RxLens is an AI-powered multilingual prescription digitization, medication adherence, and interaction analysis platform tailored for Indian healthcare contexts.

---

## Repository Structure

```
RxLens/
├── .github/
│   └── workflows/
│       └── backend-ci.yml       # Automated CI test suite
├── backend/                     # FastAPI backend
│   ├── app/
│   │   ├── api/v1/endpoints/    # REST endpoints (auth, prescriptions, drugs, chat, etc.)
│   │   ├── core/                # Config, security, database engine, Celery task queue
│   │   ├── models/              # SQLAlchemy ORM models (pgvector semantic embeddings)
│   │   ├── schemas/             # Pydantic validation schemas
│   │   ├── scripts/             # DB migration seeders (99 Indian & generic drugs)
│   │   └── services/            # OCR, fuzzy matching, translation, RAG chat, safety
│   ├── migrations/              # Alembic versioned migrations
│   ├── tests/                   # Pytest test suite (18/18 tests passing)
│   ├── docker-compose.yml       # PostgreSQL (pgvector) + Redis + Celery worker
│   ├── requirements.txt         # Python dependencies
│   └── README.md                # Detailed backend documentation
└── mobile/                      # (Target directory for Flutter developer)
```

---

## Quick Start for Developers

### Prerequisites
- Python 3.11+ 
- Docker & Docker Compose
- Git

### 1. Clone the Repository
```bash
git clone https://github.com/SomnathShaw001/RxLens.git
cd RxLens
```

### 2. Backend Setup

```bash
cd backend

# Create and activate virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install aiosqlite  # for in-memory test execution

# Start PostgreSQL (with pgvector) and Redis
docker compose up -d

# Run database migrations
alembic upgrade head

# Seed initial drug reference database (99 drugs)
python -m app.scripts.seed_drugs

# Run test suite
pytest -v

# Start FastAPI development server
uvicorn app.main:app --reload --port 8000
```

- **Interactive API Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative ReDoc Docs:** [http://localhost:8000/redoc](http://localhost:8000/redoc)
- **Health Check:** [http://localhost:8000/health](http://localhost:8000/health)

---

## Collaboration Guide for Mobile App Developer

The backend provides complete REST APIs designed for the Flutter mobile application:
- **Authentication:** `POST /v1/auth/register`, `POST /v1/auth/login`, `POST /v1/auth/refresh`
- **Prescription Ingestion:** `POST /v1/prescriptions/ingest` (multipart image upload, returns `job_id`)
- **Prescription Status & OCR:** `GET /v1/prescriptions/{job_id}` (polling with confidence scores & bounding boxes)
- **Manual Field Correction:** `POST /v1/prescriptions/{id}/correct`
- **Salt & Generic Alternatives:** `GET /v1/drugs/{name_or_rxcui}/alternatives`
- **Drug Safety & Recall Warnings:** `GET /v1/drugs/{name}/safety`
- **Prescription RAG AI Chat:** `POST /v1/chat` (multilingual clinical Q&A grounded on patient prescription)
- **Family Profiles:** `POST /v1/profiles`, `GET /v1/profiles`
- **Medication Reminders & Adherence:** `POST /v1/medications`, `POST /v1/medications/adherence`
- **DPDP Act Right to Erasure:** `DELETE /v1/users/me`
