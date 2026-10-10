# UPSKILL AI — Project Context

> **This file is the persistent project context for UPSKILL AI.**
> If the current AI coding session is replaced, the next AI assistant must read this file first before making any changes.

---

## Project

**Name:** UPSKILL AI

**Problem:**
Develop an AI-enabled learning platform that identifies competency gaps, recommends personalised training through integration with the iGOT Karmayogi ecosystem, and generates quizzes/MCQs from uploaded learning materials to strengthen competency building in India's Official Statistical System.

---

## Current Goal

Build a working MVP demonstrating the core competency-learning-assessment closed loop.

### Core Product Flow (Learner)

```
Learner Login
-> Role / Profile
-> Diagnostic Assessment
-> Competency Scoring
-> Competency Gap Analysis
-> Personalized Learning Recommendations
-> Learning Resource
-> Upload Learning Material
-> AI-generated source-grounded MCQs
-> Quiz
-> Updated Competency
-> Updated Gap
-> Updated Recommendations
```

### Admin Flow

```
Admin Login
-> Admin Dashboard
-> Upload Learning Material
-> AI MCQ Generation
-> Review Questions
-> Approve Questions
-> Quiz
```

---

## Developer

The developer is a **complete beginner and a vibe coder**.

All implementation should therefore:
- Remain simple
- Avoid unnecessary abstraction and dependencies
- Explain important changes briefly
- Avoid over-engineering
- Implement **one phase at a time**

---

## Technology Stack

| Layer | Technology |
|---|---|
| Frontend | React, Vite, JavaScript, Plain CSS |
| Backend | Python 3.11+, FastAPI, Uvicorn, Pydantic, SQLAlchemy |
| Database | SQLite (SQLAlchemy ORM enables future migration to PostgreSQL) |
| AI | OpenRouter Free API — AI calls must happen only from the backend. Never expose API keys in frontend code. |
| Document processing | PyMuPDF (PDF extraction and text chunking) |

---

## Current Project Structure

```
UPSKILL_AI/
├── PROJECT_CONTEXT.md         <- This file
├── README.md
├── .env.example
├── .gitignore
├── ai/
│   └── README.md              <- AI services placeholder
├── backend/
│   ├── .env.example
│   ├── requirements.txt
│   ├── statlearn_ai.db        <- SQLite database (kept as-is for compatibility)
│   ├── test_phase4.py
│   ├── test_phase5_ai_service.py
│   ├── test_phase5_chunks.py
│   ├── test_phase5_mcqs_api.py
│   ├── test_phase5_mcq_service.py
│   ├── test_phase5_quiz_api.py
│   ├── test_phase5_upload.py
│   ├── test_phase6a_competency_evidence.py
│   └── app/
│       ├── __init__.py
│       ├── main.py            <- FastAPI app, startup DB init + seed + routers
│       ├── config.py          <- Pydantic settings (PROJECT_NAME: "UPSKILL AI")
│       ├── database.py        <- SQLAlchemy engine + session + Base
│       ├── models.py          <- ORM models: Role, Competency, RoleCompetency, User,
│       │                          LearnerCompetency, LearningResource, Document, DocumentChunk,
│       │                          MCQ, QuizAssessment
│       ├── seed.py            <- Idempotent demo data seeder
│       ├── routes/
│       │   ├── __init__.py│   │   ├── roles.py       <- GET /api/v1/roles, GET /api/v1/roles/{id}/competencies
│   │   ├── competencies.py <- GET /api/v1/competencies
│   │   ├── learner.py     <- GET /api/v1/me, /me/competencies, /me/evidence
│   │   ├── gaps.py        <- GET /api/v1/me/gaps
│   │   ├── catalog.py     <- GET /api/v1/catalog/resources
│   │   ├── recommendations.py <- GET /api/v1/me/recommendations
│   │   ├── documents.py   <- POST /api/v1/documents/upload, GET /documents/{id},
│   │                          POST /documents/{id}/mcqs/generate,
│   │                          GET /documents/{id}/mcqs, GET /documents/{id}/quiz,
│   │                          POST /documents/{id}/quiz/submit
│   │   ├── diagnostic.py  <- POST /diagnostic/start, POST /diagnostic/{id}/submit,
│   │                          GET /diagnostic/history
│   │   └── auth.py        <- POST /auth/register, POST /auth/login, GET /auth/me
│   ├── security.py        <- Password hashing + bearer token create/decode
│   └── services/
│       ├── __init__.py
│       ├── ai_service.py          <- OpenRouter API client
│       ├── gap_service.py          <- Deterministic gap analysis
│       ├── recommendation_service.py <- Deterministic recommendation engine
│       ├── mcq_service.py          <- AI MCQ generation
│       ├── quiz_service.py         <- Quiz scoring and validation
│       ├── competency_evidence_service.py <- Evidence-based competency update
│       └── diagnostic_service.py  <- Diagnostic questions, weighted scoring
├── data/
│   └── README.md              <- Demo data placeholder
├── database/
│   └── README.md              <- Schema placeholder
├── scratch/
│   └── test_phase4.py         <- Manual/scratch test
└── frontend/
    ├── index.html
    ├── package.json
    ├── vite.config.js
    └── src/
        ├── main.jsx
        ├── App.jsx            <- Auth gate + sidebar/topbar shell + view routing
        ├── index.css          <- Full design system (light/dark tokens + all views)
        ├── components/
        │   ├── Login.jsx              <- Glassmorphic login/register page
        │   ├── OfficialEmblems.jsx    <- Emblem of India + India map SVGs
        │   ├── DashboardOverview.jsx  <- Hero banner, metric cards, progress donut, quick actions
        │   ├── CompetencyProfile.jsx  <- Learner competency table
        │   ├── GapAnalysis.jsx        <- Gap summary + sorted gap list
        │   ├── Recommendations.jsx    <- Ranked recommendation cards
        │   ├── DiagnosticAssessment.jsx <- Diagnostic flow UI (start/answer/result)
        │   ├── DocumentQuiz.jsx       <- Learner quiz (manual document-ID entry) + shared QuizRunner/QuizResult
        │   ├── PdfUploadQuiz.jsx      <- Direct PDF upload -> generate -> quiz (default in Document Quiz section)
        │   ├── Certificates.jsx       <- Certificate cards view
        │   ├── Profile.jsx            <- Learner profile view
        │   └── Settings.jsx           <- Preferences view (toggles)
        ├── context/
        │   ├── AuthContext.jsx        <- Session state, login/register/logout
        │   └── ThemeContext.jsx       <- Light/dark theme
        └── services/
            ├── api.js         <- All API calls (single place; incl. auth + bearer header)
            └── tokenStorage.js <- Token persistence with expiry
```

---

## Running the Project

### Backend
```bash
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```
Runs at: http://127.0.0.1:8000
- Health: http://127.0.0.1:8000/api/v1/health
- Docs: http://127.0.0.1:8000/docs

### Frontend
```bash
cd frontend
npm install
npm run dev
```
Runs at: http://localhost:5173

### Tests
```bash
# From the project root
pytest                 # discovers under backend/ only (see pytest.ini)
```
`pytest.ini` sets `testpaths = backend` and excludes `scratch/`, `.venv/`, and
`frontend/` so ad-hoc scratch scripts are never collected as tests.

---

## Current Phase Status

### Phase 1 — Technical Foundation (COMPLETE)
- FastAPI backend created
- React/Vite frontend created
- SQLite + SQLAlchemy setup
- CORS configured for local dev
- GET /api/v1/health working

### Phase 2 — Competency Engine (COMPLETE)
- ORM models: Role, Competency, RoleCompetency, User, LearnerCompetency
- Demo data seeded: 1 role, 8 competencies, 8 mappings, 1 learner
- APIs: /roles, /competencies, /roles/{id}/competencies, /me, /me/competencies

### Phase 3 — Gap Analysis (COMPLETE)
- Gap service: deterministic gap calculation, status classification, priority assignment
- Summary metrics: total, with gaps, major, moderate, meeting target, above target
- API: GET /api/v1/me/gaps

### Phase 4 — Recommendation Engine (COMPLETE)
- 16 seeded demo learning resources (iGOT/NSSTA)
- Deterministic recommendation algorithm: gap-based filtering, level-fit, relevance scoring
- Priority ranking: CRITICAL > HIGH > MEDIUM, gap size, relevance, duration
- APIs: GET /api/v1/catalog/resources, GET /api/v1/me/recommendations

### Phase 5 — Document Processing + Quiz (COMPLETE)
- PDF upload with PyMuPDF text extraction
- Document chunking for MCQ generation
- AI MCQ generation via OpenRouter (with fallback)
- MCQ persistence and inspection API
- Learner quiz endpoint (no answer key exposed)
- Server-side quiz scoring with 60% pass threshold
- APIs: POST /documents/upload, GET /documents/{id}, POST /documents/{id}/mcqs/generate,
        GET /documents/{id}/mcqs, GET /documents/{id}/quiz, POST /documents/{id}/quiz/submit

### Phase 6A — Competency Evidence & Recalculation (COMPLETE)
- Percentage → evidence level mapping (0-3)
- At-most-one-level safety rule per quiz
- Level never decreases; capped at 4
- Gap recalculation via existing gap_service
- Evidence persistence and retrieval
- APIs: quiz submission returns competency_update, GET /api/v1/me/evidence

### Phase 6B — Test Stabilization + PDF Upload UI (COMPLETE)
- Tests: added `pytest.ini` (tests discovered under `backend/`; `scratch/` excluded), fixed missing helper + JSON import in `test_phase2_diagnostic.py`, added `comp_by_id()` to handle string-keyed JSON competency results, and made the demo seeder reset existing learner levels to seed values. **Full suite: 81 passed, 0 failed.**
- Frontend: `PdfUploadQuiz.jsx` default flow under **Assessments → Document Quiz** — pick a `.pdf`, upload via `POST /documents/upload`, generate MCQs (`POST /documents/{id}/mcqs/generate`), take the quiz, view the server-scored result. Original "Enter Document ID" `DocumentQuiz` retained as a toggle. API client extended with `uploadDocument` + `generateDocumentMcqs`. No backend behavior changed.

### Phase 7 — Authentication + Diagnostic Backend (COMPLETE)
- Backend auth: `app/security.py` (password hashing, bearer token create/decode) and `app/routes/auth.py`
  (`POST /auth/register` → 201, `POST /auth/login` → token, `GET /auth/me` via bearer header). All learner
  routes now require a valid bearer token; tests use the `AuthenticatedClient` helper in `auth_test_utils.py`.
- Diagnostic assessment backend: `DiagnosticQuestion` + `DiagnosticAssessment` models, `diagnostic_service.py`
  (difficulty weights EASY=1/MEDIUM=2/HARD=3, weighted percent, per-competency evidence), routes under
  `/api/v1/diagnostic` (start / submit / history). Evidence flows through the existing Phase 6A engine
  (at most one level per submission, never decreases).
- Test suites: `test_phase7a_auth.py`, `test_phase7b_route_auth.py`; diagnostic suite expanded.
  **Full suite: 97 passed, 0 failed.**
- Frontend: `AuthContext` + `tokenStorage` (session persistence with expiry), `Login.jsx` (sign in /
  create account), sidebar + top header app shell, `DashboardOverview`, `DiagnosticAssessment`, `Profile`,
  `Settings`, `Certificates` views. Light/dark theme support via `ThemeContext`.

### Phase 7E — Frontend CSS Restoration (COMPLETE)
- `frontend/src/index.css` had been truncated to ~84 class rules (stray `test` token at end) while the
  redesigned components reference ~306 classes — pages rendered unstyled despite a passing Vite build.
- Restored by appending missing rules only (login glass card, app shell/sidebar/topbar, dashboard hero,
  metrics, progress donut, quick actions, quiz runner/results, recommendations, settings toggles, profile
  fields, diagnostic, dynamic underscore status variants). No pre-existing rules were modified.
- Verified: every `className` referenced by any component now has a matching CSS rule; `npm run build` passes.

### Phase 8 — New-User Onboarding + Demo Readiness (COMPLETE)
- **Onboarding backend:** `users` table gained nullable profile columns (`designation`, `department`,
  `assignment`, `education`, `work_experience`, `previous_training`, `profile_completed`) via the
  existing `ensure_schema()` migration; `POST /auth/complete-onboarding` + `GET /auth/onboarding-status`
  added; `serialize_user`/`/me` include the profile. A user is onboarded once they have a role AND
  `profile_completed=True`. Position change later re-opens onboarding but preserves assessed levels.
- **Framework positions seeded:** Statistical Officer, Data Analyst, Statistical Assistant,
  Administrative Officer, Research Officer, Data Entry / Data Processing — each with its own
  RoleCompetency mappings, so the selected position genuinely drives diagnostic questions, gaps and
  recommendations. "Statistical / Data Officer" (original demo role) reuses the Statistical Officer set.
- **Diagnostic persistence fix:** a learner with NO prior competency rows gets their full assessed
  profile persisted on submit (previously only levelled-up competencies were saved, leaving new users
  with an empty dashboard after passing).
- **Frontend:** `Onboarding.jsx` gate in `App.jsx` (shown only while `profile_completed === false`),
  `DashboardOverview` rewritten to show ONLY backend data (new users get an honest
  "Complete your competency assessment…" empty state + Start Assessment CTA instead of fake scores),
  optional competency link on PDF upload (enables the Phase 6A evidence loop from the UI),
  competency_update banner on quiz results, honest empty states in Gap Analysis / Recommendations.
- **MCQ reliability:** `mcq_service.generate_mcqs` retries invalid (empty/non-JSON) model replies up to
  3 attempts — free-tier models intermittently return empty responses. Validation remains strict;
  `AIServiceError` still propagates unchanged.
- **Deployment files:** `frontend/vercel.json` (SPA rewrites), complete `.env.example` templates
  (root, backend, frontend incl. `VITE_API_BASE_URL`), README demo credentials + deployment section.
- Tests: `test_phase8_onboarding.py` (6 tests). **Full suite: 103 passed, 0 failed.**
- Verified in-browser (Playwright): onboarding gate → profile save → honest empty dashboard →
  assessment start → re-login persistence; demo learner dashboard unchanged; zero console errors.

---

## Prototype Competency Scale

| Level | Label |
|---|---|
| 1 | Awareness |
| 2 | Working |
| 3 | Proficient |
| 4 | Advanced |

IMPORTANT: This is a prototype scoring scale for UPSKILL AI.
It must NOT be presented as an official MoSPI/iGOT competency-level definition in any UI text or code comments.

---

## Demo Role

**Statistical / Data Officer**
A demonstration role representing a statistical professional working with official statistical data, surveys, analysis, data management and dissemination.

---

## Demo Competencies

| # | Competency | Required Level | Priority |
|---|---|---|---|
| 1 | Official Statistics | 3 — Proficient | HIGH |
| 2 | Survey Methodology | 3 — Proficient | HIGH |
| 3 | Statistical Data Analysis | 3 — Proficient | HIGH |
| 4 | Data Management | 3 — Proficient | HIGH |
| 5 | Statistical Software | 2 — Working | MEDIUM |
| 6 | Data Visualization | 2 — Working | MEDIUM |
| 7 | AI/ML for Statistics | 2 — Working | MEDIUM |
| 8 | Data Quality and Validation | 3 — Proficient | HIGH |

---

## Demo Learner Initial Competency Levels

| Competency | Current Level | Required Level |
|---|---|---|
| Official Statistics | 2 — Working | 3 — Proficient |
| Survey Methodology | 1 — Awareness | 3 — Proficient |
| Statistical Data Analysis | 2 — Working | 3 — Proficient |
| Data Management | 1 — Awareness | 3 — Proficient |
| Statistical Software | 1 — Awareness | 2 — Working |
| Data Visualization | 3 — Proficient | 2 — Working |
| AI/ML for Statistics | 1 — Awareness | 2 — Working |
| Data Quality and Validation | 2 — Working | 3 — Proficient |

---

## Feature Implementation Status

### ALREADY IMPLEMENTED / WORKING

- **Competency Framework** — Role-competency mappings with required levels and priorities (Phase 2)
- **Deterministic Competency/Evidence Logic** — Level-based scoring, evidence-to-level mapping, at-most-one-level safety rule (Phase 6A)
- **Skill-Gap Analysis** — Gap size, severity status (MAJOR/MODERATE/MEETS/ABOVE), priority classification (Phase 3)
- **Recommendation Engine** — Deterministic resource matching based on gap, priority, level fit, and relevance scoring (Phase 4)
- **Quiz Generation/Scoring** — AI-generated MCQs, server-side scoring with 60% threshold, difficulty-weighted scoring (Phase 5)
- **Competency Update/Evidence Loop** — Quiz results feed back into competency levels with evidence persistence (Phase 6A)
- **PDF Processing** — PyMuPDF extraction, text chunking (Phase 5)
- **Existing MCQ Generation/Validation** — OpenRouter-based generation with answer validation (Phase 5)
- **iGOT/NSSTA Seeded Learning Resources** — 16 demo catalog resources, clearly labelled (Phase 4)
- **Competency Profile UI** — Competency table with current vs. required levels (Phase 2)
- **Gap Analysis UI** — Summary cards + sorted gap list with visual bars (Phase 3)
- **Recommendations UI** — Ranked recommendation cards with reasons (Phase 4)
- **Quiz UI** — Learner quiz interface with scoring and results review (Phase 5)
- **Direct PDF Upload Quiz UI** — Pick a `.pdf` in the browser, upload, generate MCQs, and take the quiz, all in-app (Phase 6B)

### PARTIALLY IMPLEMENTED

- **Diagnostic Assessment** — Dedicated diagnostic now implemented (Phase 7): seeded questions per competency,
  difficulty-weighted scoring, per-competency evidence, history endpoint; adaptive question selection pending
- **Learning Path/Prerequisite Logic** — Recommendation engine provides ranked resources but no prerequisite-aware ordering
- **MCQ/RAG Architecture** — MCQ generation works via AI service; no RAG-grounded architecture yet
- **Officer Profile** — Basic learner profile via /me endpoint; no full officer profile model
- **Backend Persistence** — SQLite working; no production persistence setup
- **Frontend Product Flow** — Authenticated learner journey working (login → dashboard → diagnostic → quiz →
  gaps → recommendations); trainer/admin journeys and RBAC-gated UI not yet built

### NOT YET IMPLEMENTED / FUTURE

- PostgreSQL + pgvector RAG infrastructure
- DOCX/PPTX unified document processing (only PDF is supported)
- Proper vector retrieval for document chunks
- RAG-grounded MCQ generation (currently AI generates from chunk text, not vector similarity)
- AI Tutor (RAG-grounded conversational tutor)
- Proper Learner/Trainer/Admin RBAC and access control
- Complete Trainer workflow (review, approve, publish assessments)
- Complete Admin workforce dashboard
- Live iGOT Karmayogi API integration
- Live NSSTA/TPAC API integration
- HRIS/SSO authentication
- Multilingual support
- Video/audio transcription
- Predictive workforce forecasting
- Complex live adaptive branching
- Custom ML model training
- Major frontend redesign

---

## Important Integration Constraint

We do NOT have authorized iGOT Karmayogi APIs.

Therefore:
- Do not claim live iGOT API integration
- Do not scrape iGOT
- Use clearly labelled demo/catalog data for iGOT resources
- Use clearly labelled demo/catalog data for NSSTA/TPAC resources
- Build an integration adapter/interface so authorized APIs can be connected later

---

## AI Cost Constraint

The project must use free AI API options.

- Initial planned provider: OpenRouter Free
- Do not assume paid OpenAI API access
- Keep a fallback/demo MCQ mechanism so the application can still demonstrate the workflow if the free AI API is unavailable or rate-limited

---

## Core Design Principle

The project is NOT a replacement for iGOT.

It is an intelligence layer connecting:

```
Competency Evidence -> Skill Gap -> Personalized Learning -> Assessment -> Competency Improvement
```

The main differentiator is the closed competency-learning-assessment loop.

---

## Deterministic vs AI Logic

| Use deterministic code for | Use AI for |
|---|---|
| Assessment scoring | Learning material understanding |
| Competency level calculation | MCQ generation |
| Gap calculation | Explanations |
| Recommendation ranking | Optional semantic interpretation |
| Quiz scoring | |
| Validation and permissions | |

---

## Critical Rules

1. Do not rebuild working components unnecessarily.
2. Do not switch frameworks.
3. Do not introduce microservices.
4. Do not add PostgreSQL unless specifically requested.
5. Do not add Redis or MongoDB.
6. Do not train an LLM.
7. Do not scrape iGOT.
8. Do not expose API keys in frontend code.
9. Do not implement multiple future phases automatically.
10. Do not delete working code without checking first.
11. Keep the project beginner-friendly.
12. Test after each major change.
13. Preserve the /api/v1/health endpoint at all times.
14. Prefer simple working code over sophisticated architecture.
15. Do not add unnecessary packages.
16. The LLM must NEVER decide competency scores, gap sizes, severity, or recommendation rankings. Those must remain deterministic and explainable.

---

## AI Coding Assistant Instructions

Before making any changes:

1. Read this file (PROJECT_CONTEXT.md).
2. Inspect the existing project structure.
3. Determine the current phase from the Phase Status table above.
4. Do not assume future functionality already exists.
5. Make only the changes requested by the developer.
6. Test the changes after implementation.
7. Report modified files and test results clearly.
8. Stop when the requested phase/task is complete.

---

END OF PROJECT CONTEXT
