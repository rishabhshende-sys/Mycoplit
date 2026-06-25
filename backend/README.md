# Mycoplit Backend

FastAPI backend for Phase 1 of Mycoplit Visual AI Command Center.

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000
```

The backend creates SQLite tables on startup, seeds a demo workflow, and exposes `GET /health`.
