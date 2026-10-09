# CodeMind DNA

This repository contains the CodeMind DNA project (frontend + backend).

## Local development

Backend (Python/FastAPI)

- Create a virtual environment and install dependencies:

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

- Run the backend:

```powershell
.venv\Scripts\python.exe -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Frontend (Vite/React)

```bash
cd frontend
npm ci
npm run dev
```

Open the app at `http://localhost:5173`.

## CI / Deploy (Render)

The root `render.yaml` defines the FastAPI backend and Vite frontend as a Render Blueprint. In Render, choose **New + → Blueprint**, connect this repository, and deploy the Blueprint. The frontend is configured to call the backend service and to serve client-side routes.

Set `ADMIN_PHONE_NUMBERS` in the backend service's environment to the four authorized E.164 phone numbers if admin phone login is needed. Render generates `JWT_SECRET_KEY` for the backend.

The backend defaults to SQLite for local development. Render's local filesystem is ephemeral, so configure a persistent database with `DATABASE_URL` before using the deployed app for data that must survive restarts.