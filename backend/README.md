# RxLens Backend API (FastAPI)

Production-grade, asynchronous backend for **RxLens** (Multilingual AI Prescription Digitization App) built per TRD & PRD v1.0 specifications.

---

## Architecture & Features

- **FastAPI Framework:** High-performance async REST API with interactive Swagger docs (`/docs`).
- **Multimodal AI OCR:** Google Gemini 2.5 Flash pipeline for clinical transcription and medication extraction.
- **RapidFuzz Drug Normalization:** Resolves Indian brand names and OCR typos (e.g., `"crocim"` $\rightarrow$ `"Crocin"`).
- **Confidence Scoring Gate (TRD Section 10):**
  $$\text{score} = 100 \times (0.35 \times \text{ocr} + 0.30 \times \text{fuzzy} + 0.25 \times \text{consistency} + 0.10 \times \text{validity})$$
  Automatically flags fields requiring human verification before clinical acceptance.
- **Drug Alternatives & Jan Aushadhi:** Salt resolution and affordable Jan Aushadhi generic equivalent mapping.
- **RAG AI Chat:** Prescription-grounded question answering with strict regulatory medical disclaimers.
- **DPDP Act Compliance:** Audit logging and Right to Erasure (`DELETE /v1/users/me`).

---

## Getting Started

### 1. Local Python Environment
```bash
cd backend
python -m venv .venv
.\.venv\Scripts\activate  # Windows
pip install -r requirements.txt
```

### 2. Start Services (PostgreSQL + Redis)
```bash
docker compose up -d
```

### 3. Run FastAPI Development Server
```bash
.\.venv\Scripts\uvicorn app.main:app --reload --port 8000
```
- Interactive API Docs: `http://localhost:8000/docs`
- Health Check: `http://localhost:8000/health`

### 4. Run Test Suite
```bash
.\.venv\Scripts\pytest -v
```

---

## Core Endpoints for Developer A (Flutter App)

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `POST` | `/v1/prescriptions/ingest` | Upload prescription image. Returns `202 Accepted` with `job_id`. |
| `GET` | `/v1/prescriptions/{job_id}` | Poll recognition progress, field confidence, bboxes, and `needs_review`. |
| `POST` | `/v1/prescriptions/{id}/correct` | Submit manual human correction for any low-confidence field. |
| `GET` | `/v1/drugs/{name_or_rxcui}/alternatives`| Get same-salt generics & Jan Aushadhi alternatives. |
| `POST` | `/v1/chat` | AI questions answered strictly from prescription context. |
| `POST` | `/v1/medications` | Save medication schedule and local reminder cron. |
| `GET` | `/v1/medications` | List current profile medications. |
| `DELETE` | `/v1/users/me` | DPDP Right to Erasure cascade deletion. |
