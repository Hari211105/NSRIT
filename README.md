# UPSKILL AI

**UPSKILL AI — AI-Driven Personalized Competency & Learning Intelligence Platform**

---

## 📌 Project Overview
UPSKILL AI is an AI-driven competency intelligence and personalized learning platform built for learners across domains — from students and self-paced career switchers to industry professionals and public sector officers.

### Current Status
> **Working Full-Stack Platform** — Multi-sector competency framework, dual onboarding pathways (Role-Based Career Track & Goal-Based Course Track), diagnostic assessments with technical MCQs & practical situational scenarios, deterministic gap analysis, personalized resource recommendations, browser-based PDF upload to AI quiz, and verified credentials.
>
> Test status: **110+ comprehensive backend tests passing** (onboarding in both modes, dual-mode gap analysis and recommendations, diagnostic scoring, scenario assessments, course discovery search & filtering, document quiz generation). Run with `pytest` from the project root.
>
> **Demo data honesty:** The learning catalogs, course modules, scenario questions, and resources are **demo seed data** designed to demonstrate end-to-end functionality without third-party vendor lock-in.

---

## 🛠️ Technology Stack
- **Frontend**: React (JavaScript), Vite, Plain Modern CSS (responsive, accessible)
- **Backend**: Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy
- **Database**: SQLite (SQLAlchemy ORM for seamless transition to PostgreSQL in production)
- **AI**: OpenRouter Free API — secure backend-mediated LLM interactions

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

## 2. Frontend Setup & Run

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

| Account | Email | Password | Pathway |
|---|---|---|---|
| Pre-onboarded Demo Learner | `demo@statlearn.local` | `Demo@12345` | Governance & Statistical Track |

New users: **Create Account** on the login page → choose your learning pathway:
1. **Prepare for a Role**: Select sector & position, complete competency diagnostic, view role gap analysis.
2. **Learn a Subject**: Browse technical and non-technical courses with real-time keyword search and category filters, take scenario or MCQ assessments, and follow streamlined learning paths.

---

## 📊 Core Features

### Implemented & Verified
- **Dual Learning Pathways (Phase 1 & Phase 2)**:
  - **Role Pathway**: Comprehensive sector and role mapping (Software, Data, Cloud, Governance, Health, Finance).
  - **Goal Pathway**: Course-based learning (Python, Web Development, Communication Skills, Time Management, Financial Literacy) with category tags and estimated completion hours.
- **Rich Assessment Types**:
  - **Technical MCQs**: Difficulty-weighted conceptual knowledge verification.
  - **Practical Scenarios**: Situational case studies for non-technical subjects with contextual explanations and judgement scoring.
- **Catalog Search & Discovery**:
  - Full-text search and category filtering for courses on both backend API and frontend UI.
- **Deterministic Skill Gap Analysis**:
  - Mathematical comparison of current proficiency vs. required target level for roles and courses.
- **Personalized Recommendations Engine**:
  - Multi-source learning resources matched by competency gap priority and target proficiency level.
- **Direct PDF Upload → AI Quiz Generation**:
  - Browser-based document upload, chunking, AI-assisted question generation, and automatic competency feedback loop.
- **Verified Credentials & Progress**:
  - Diagnostic certificates and skill level records.
