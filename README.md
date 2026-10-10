# UPSKILL AI

[![CI](https://github.com/Hari211105/NSRIT/actions/workflows/ci.yml/badge.svg)](https://github.com/Hari211105/NSRIT/actions/workflows/ci.yml)

**UPSKILL AI — AI-Driven Personalized Competency & Learning Intelligence Platform**

---

## 📌 Project Overview
UPSKILL AI is an AI-driven competency intelligence and personalized learning platform built for learners across domains — from students and self-paced career switchers to industry professionals and public sector officers.

### Current Status
> **Production-Ready Full-Stack Platform** — Multi-sector competency framework, dual onboarding pathways (Role-Based Career Track & Goal-Based Course Track), diagnostic assessments with technical MCQs & practical situational scenarios, deterministic gap analysis, personalized resource recommendations, browser-based PDF upload to AI quiz, verified credentials, Docker containerization, PostgreSQL support with Alembic migrations, and GitHub Actions CI/CD.
>
> Test status: **119 comprehensive backend tests passing** (onboarding in both modes, dual-mode gap analysis and recommendations, diagnostic scoring, scenario assessments, course discovery search & filtering, document quiz generation, and production security hardening). Run with `pytest` from the project root.
>
> **Demo data honesty:** The learning catalogs, course modules, scenario questions, and resources are **demo seed data** designed to demonstrate end-to-end functionality without third-party vendor lock-in.

---

## 🛠️ Technology Stack
- **Frontend**: React (JavaScript), Vite, Plain Modern CSS (responsive, accessible, deployed on **Vercel**)
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Alembic (Dockerized on **Render** / Railway)
- **Database**: SQLite for local dev & testing; PostgreSQL for production with connection pooling and migrations
- **AI**: OpenRouter Free API — secure backend-mediated LLM interactions
- **CI/CD**: GitHub Actions (Pytest test suite, Node/Vite production build, Docker container verification, automated Render deploy webhook)

---

## 🚀 Getting Started

### 1. Local Setup with Docker Compose (Recommended)

Run both the PostgreSQL database and FastAPI backend with a single command:

```bash
# Start backend + PostgreSQL
docker compose up --build

# Verify backend health
curl http://localhost:8000/api/v1/health
```

### 2. Manual Local Setup (Without Docker)

#### Backend Setup:
```bash
cd backend
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On macOS/Linux:
# source .venv/bin/activate

pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
The backend runs at `http://127.0.0.1:8000`
- Health check: `http://127.0.0.1:8000/api/v1/health`
- Interactive API Docs: `http://127.0.0.1:8000/docs`

#### Frontend Setup:
```bash
cd frontend
npm install
npm run dev
```
The frontend runs at `http://localhost:5173`.

---

## 🗄️ Database Migrations with Alembic

UPSKILL AI uses Alembic for declarative database versioning.

```bash
cd backend
# Run all pending migrations
alembic upgrade head

# Check current migration revision
alembic current
```

---

## 🔐 Environment Variables Matrix

| Variable | Scope | Default / Example | Purpose |
|---|---|---|---|
| `ENVIRONMENT` | Backend | `development` / `production` | Set to `production` in live environments |
| `PORT` | Backend | `8000` | Port uvicorn binds to |
| `JWT_SECRET_KEY` | Backend | `upskill-dev-secret...` | In `production`, server **refuses to start** unless a strong key is set |
| `DATABASE_URL` | Backend | `sqlite:///./statlearn_ai.db` | Use `postgresql+psycopg://...` in production |
| `BACKEND_CORS_ORIGINS` | Backend | `["http://localhost:5173"]` | JSON array or comma-separated list of allowed frontend origins |
| `OPENROUTER_API_KEY` | Backend | `""` | OpenRouter API Key for document quiz generation |
| `VITE_API_BASE_URL` | Frontend | `http://127.0.0.1:8000/api/v1` | Backend URL with `/api/v1` prefix |

---

## 🚢 Production Deployment

For complete, step-by-step instructions on deploying the frontend to **Vercel**, containerizing the backend on **Render**, setting up **Neon / Supabase PostgreSQL**, and configuring **GitHub Actions CD secrets**, please see [DEPLOYMENT.md](file:///D:/NSRIT/DEPLOYMENT.md).

---

## 📊 Demo Credentials

| Account | Email | Password | Pathway |
|---|---|---|---|
| Pre-onboarded Demo Learner | `demo@statlearn.local` | `Demo@12345` | Governance & Statistical Track |

New users: **Create Account** on the login page → choose your learning pathway:
1. **Prepare for a Role**: Select sector & position, complete competency diagnostic, view role gap analysis.
2. **Learn a Subject**: Browse technical and non-technical courses with real-time keyword search and category filters, take scenario or MCQ assessments, and follow streamlined learning paths.
