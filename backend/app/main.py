from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ALLOWED_ORIGINS, APP_NAME, DEFAULT_MODE, ensure_storage
from .database import Base, SessionLocal, engine
from .routes import audit_routes, card_routes, chat_routes, execution_routes, file_routes, report_routes, screenshot_routes, vision_routes, workflow_routes
from .seed import seed_database
from .services.schema_service import ensure_phase3_schema


app = FastAPI(title=APP_NAME, version="0.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    ensure_storage()
    Base.metadata.create_all(bind=engine)
    with SessionLocal() as db:
        ensure_phase3_schema(db)
        seed_database(db)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "mode": DEFAULT_MODE, "automation_execution": "approval-first"}


app.include_router(workflow_routes.router)
app.include_router(execution_routes.router)
app.include_router(chat_routes.router)
app.include_router(file_routes.router)
app.include_router(report_routes.router)
app.include_router(vision_routes.router)
app.include_router(card_routes.router)
app.include_router(screenshot_routes.router)
app.include_router(audit_routes.router)
