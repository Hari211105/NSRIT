# 🚀 Deployment Guide — UPSKILL AI

This guide walks you through the production deployment of **UPSKILL AI**:
- **Frontend**: Hosted on [Vercel](https://vercel.com) (Static React + Vite SPA).
- **Backend**: Containerized FastAPI on [Render](https://render.com) (or Railway / Fly.io).
- **Database**: Managed PostgreSQL on Render Postgres, Supabase, Neon, or AWS RDS.
- **CI/CD**: Automated via GitHub Actions (`.github/workflows/ci.yml` and `cd.yml`).

---

## 📋 Manual Steps Checklist (What You Need to Do)

### 1. Database Setup (Managed PostgreSQL)
1. Sign up / log into **[Neon](https://neon.tech)**, **[Supabase](https://supabase.com)**, or **[Render](https://render.com)**.
2. Create a new PostgreSQL database instance (e.g. `upskill_production`).
3. Copy your connection URI. It will look like:
   ```
   postgresql://username:password@ep-sample-123.us-east-2.aws.neon.tech/upskill_production?sslmode=require
   ```
4. Note: UPSKILL AI automatically converts `postgres://` or `postgresql://` URIs to the modern `postgresql+psycopg://` driver.

---

### 2. Backend Deployment on Render
1. Sign up / log into **[Render](https://render.com)**.
2. Click **New +** → **Web Service** → Connect your GitHub repository: `https://github.com/Hari211105/NSRIT`.
3. Choose **Docker** as the environment (Render detects `backend/Dockerfile` automatically).
   - **Root Directory**: `backend` (or leave blank if context is set to repo root; if configuring via Dockerfile path, specify `backend/Dockerfile`).
4. Set Environment Variables in Render:
   | Key | Value | Description |
   |---|---|---|
   | `ENVIRONMENT` | `production` | Enables production security checks |
   | `JWT_SECRET_KEY` | *(Generate a 64-char key)* | `python -c "import secrets; print(secrets.token_urlsafe(48))"` |
   | `DATABASE_URL` | *(Your PostgreSQL URI)* | Managed Postgres connection string |
   | `INITIAL_ADMIN_EMAIL` | `admin@yourdomain.com` | Promotes this user to `ADMIN` on startup |
   | `BACKEND_CORS_ORIGINS` | `["https://your-frontend.vercel.app","http://localhost:5173"]` | Include your Vercel domain |
   | `OPENROUTER_API_KEY` | `sk-or-v1-...` | Your backend OpenRouter AI key |
   | `OPENROUTER_MODEL` | `openrouter/free` | AI generation model slug |
5. In Render settings, copy your **Deploy Hook URL** (e.g., `https://api.render.com/deploy/srv-xxxx?key=yyyy`).

---

### 3. Database Migrations (One-Time Initialization)
Once Render connects to your PostgreSQL database, run the Alembic migration:
1. In Render Web Service dashboard, click **Shell** (or run locally pointed to the remote `DATABASE_URL`):
   ```bash
   alembic upgrade head
   ```
2. Migrations `0001_initial_schema`, `0002_align_schema_with_models`, and `0003_rbac_trainer_admin` create all tables, indexes, constraints, and audit logs.
3. **Reference Data Initialization**: On the first production boot, UPSKILL AI automatically detects that the database is empty (0 sectors) and seeds the reference catalogs (sectors, framework roles, competencies, courses, resources, scenario & MCQ questions). Subsequent boots detect existing rows and skip seeding.
   - To force seeding on every start: set `SEED_ON_STARTUP=true`.
   - To completely disable automatic seeding: set `SEED_ON_STARTUP=false`.
   - **Security**: In `production` mode, hardcoded demo accounts (`demo@statlearn.local`, `trainer@statlearn.local`, `admin@statlearn.local`) are **never created**. An initial administrator can be designated by setting `INITIAL_ADMIN_EMAIL=your-email@domain.com`.

---

### 4. Frontend Deployment on Vercel
1. Sign up / log into **[Vercel](https://vercel.com)**.
2. Click **Add New...** → **Project** → Import `https://github.com/Hari211105/NSRIT`.
3. Configure project settings:
   - **Framework Preset**: Vite
   - **Root Directory**: `frontend`
   - **Build Command**: `npm run build`
   - **Output Directory**: `dist`
4. Environment Variables:
   | Key | Value |
   |---|---|
   | `VITE_API_BASE_URL` | `https://your-backend.onrender.com/api/v1` |
5. Click **Deploy**.

---

### 5. GitHub Actions Secrets Configuration
In your GitHub repository `https://github.com/Hari211105/NSRIT`:
1. Navigate to **Settings** → **Secrets and variables** → **Actions**.
2. Click **New repository secret**:
   - Name: `RENDER_DEPLOY_HOOK_URL`
   - Value: *(The Deploy Hook URL copied from Render)*
3. Now, whenever you push changes to `main`, GitHub Actions will:
   - Run the 130 backend Pytest tests.
   - Run the Vite production build.
   - Verify the Docker container build.
   - Automatically trigger Render to deploy the new container.

---

## 🐳 Local Container Testing (Docker Compose)

To test the entire stack locally with PostgreSQL:
1. Create `.env` from template:
   ```bash
   cp backend/.env.example backend/.env
   ```
2. Start the Postgres and FastAPI backend containers:
   ```bash
   docker compose up --build
   ```
3. Test healthcheck endpoint:
   ```bash
   curl http://localhost:8000/api/v1/health
   # Returns: {"status": "ok"}
   ```
