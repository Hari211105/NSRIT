# UPSKILL AI

**UPSKILL AI — AI-Driven Competency Intelligence Platform for India's Official Statistical System**


---

## 📌 Project Overview
UPSKILL AI is an AI-driven competency intelligence and learning platform designed specifically for officers and professionals within India's Official Statistical System.

### Current Status
> **Working MVP** — Competency framework, deterministic gap analysis, personalized recommendations, PDF document processing, AI-generated MCQs, quiz scoring, competency evidence loop, a **direct PDF upload → quiz workflow**, and a **new-user onboarding flow (position → role-specific competency framework → assessment)** are all functional. See the feature breakdown below.
>
> Test status: **103 backend tests passing** (onboarding, authentication, diagnostic assessment, gap analysis, recommendations, document processing, MCQ generation, quiz scoring, competency evidence). Run with `pytest` from the project root (see `pytest.ini` — tests are discovered under `backend/` only; `scratch/` holds ad-hoc scripts, not pytest tests).
>
> **Demo data honesty:** the iGOT Karmayogi / NSSTA / TPAC learning catalog is **demo seed data** (clearly labelled `IGOT_DEMO` / `NSSTA_TPAC_DEMO`, no live API integration), and the competency scale (Awareness → Advanced) is a **prototype scale**, not an official MoSPI/iGOT standard.

---

## 🛠️ Technology Stack
- **Frontend**: React (JavaScript), Vite, Plain Modern CSS
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy
- **Database**: SQLite (SQLAlchemy ORM for easy migration to PostgreSQL in production)
- **AI**: OpenRouter Free API — AI calls happen only from the backend

---

## 🚀 Getting Started

### 1. Backend Setup & Run

Open a terminal and navigate to `backend`:

```bash
cd backend
# (Optional) Create and activate a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the FastAPI server
python -m uvicorn app.main:app --reload
```
The backend will run at `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/api/v1/health`
- Interactive API Docs: `http://127.0.0.1:8000/docs`

---

### 2. Frontend Setup & Run

Open a second terminal and navigate to `frontend`:

```bash
cd frontend

# Install node dependencies
npm install

# Start the Vite development server
npm run dev
```
The frontend will run at `http://localhost:5173`.

### 3. Demo Credentials

| Account | Email | Password |
|---|---|---|
| Pre-onboarded demo learner (has competency profile) | `demo@statlearn.local` | `Demo@12345` |

New users: **Create Account** on the login page → complete the onboarding profile (select your **Position/Role**) → take the role-specific assessment. The selected position drives the competency framework, assessment questions, gap analysis and recommendations.

### 4. Environment Variables

Copy `backend/.env.example` → `backend/.env` and fill in `OPENROUTER_API_KEY` and a strong `JWT_SECRET_KEY`. Copy `frontend/.env.example` → `frontend/.env` if you need to point the frontend at a non-default backend URL. See the root `.env.example` for the full documented list.

---

## 🚢 Deployment (MVP architecture)

| Layer | Hosting | Notes |
|---|---|---|
| Frontend (React/Vite) | **Vercel** | `frontend/vercel.json` included; set `VITE_API_BASE_URL` to the deployed backend URL + `/api/v1` |
| Backend (FastAPI) | **Render / Railway / Fly.io** (a Python web-service host — **not** Vercel serverless) | Start command: `pip install -r requirements.txt && uvicorn app.main:app --host 0.0.0.0 --port $PORT` |
| Database | SQLite (default) or managed PostgreSQL | `DATABASE_URL` decides; SQLAlchemy ORM works for both |
| AI | OpenRouter free tier | `OPENROUTER_API_KEY` in backend env only — never in frontend code |

Production checklist:
1. Backend: set `JWT_SECRET_KEY` (strong random value), `OPENROUTER_API_KEY`, `DATABASE_URL`, and add the deployed frontend URL to `BACKEND_CORS_ORIGINS`.
2. Frontend: set `VITE_API_BASE_URL=https://<backend-host>/api/v1`.
3. Never commit real `.env` files (`.gitignore` already excludes them; `.env.example` holds placeholders).

---

## 📊 Features

### Implemented & Working
- **Competency Framework** — Role-competency mappings with required levels and priorities
- **Deterministic Competency Scoring** — Level-based scoring with clear rules
- **Skill Gap Analysis** — Gap size, severity, and status for each competency
- **Recommendation Engine** — Deterministic resource matching based on gap, priority, and level fit
- **Quiz Generation & Scoring** — Difficulty-weighted MCQ scoring with server-side validation
- **Competency Update/Evidence Loop** — Quiz results feed back into competency levels
- **Authentication (Demo)** — Email/password register + login, bearer-token-protected learner APIs, persistent frontend session with expiry
- **New-User Onboarding** — Position/designation + professional profile collected after signup; the selected position is stored in the database and drives the role-specific competency framework, assessment, gap analysis and recommendations (new users see an honest "complete your assessment" dashboard state, not fake scores)
- **Diagnostic Assessment** — Competency-mapped diagnostic with difficulty-weighted scoring and per-competency evidence
- **PDF Processing** — PDF extraction and text chunking
- **MCQ Generation/Validation** — AI-generated MCQs with answer validation
- **iGOT/NSSTA Seeded Learning Resources** — Demo catalog with 16 learning resources
- **Competency Profile** — Learner competency table with current vs. required levels
- **Direct PDF Upload → Quiz** — Learner uploads a `.pdf` from the browser, Upskill AI extracts text, chunks it, generates a source-grounded quiz, and they take it in-app (no document ID needed; an "Enter Document ID" fallback remains for already-uploaded documents)

### Partially Implemented
- **Diagnostic Assessment** — Implemented (difficulty-weighted, per-competency evidence); adaptive question selection pending
- **Learning Path/Prerequisite Logic** — Basic ordering; prerequisite-aware paths pending
- **MCQ/RAG Architecture** — MCQ generation works; RAG-grounded generation pending
- **Officer Profile** — Basic profile; full officer profile integration pending
- **Backend Persistence** — SQLite working; production persistence pending
- **Frontend Product Flow** — Authenticated learner journey working (login → dashboard → diagnostic → quiz → gaps → recommendations); trainer/admin journeys and RBAC-gated UI pending

### Not Yet Implemented
- PostgreSQL + pgvector RAG infrastructure
- DOCX/PPTX unified document processing
- Proper vector retrieval
- RAG-grounded MCQ generation
- AI Tutor
- Proper Learner/Trainer/Admin RBAC
- Complete Trainer workflow
- Complete Admin workforce dashboard
- Live iGOT/NSSTA API integration
- Multilingual support
- Video/audio transcription
