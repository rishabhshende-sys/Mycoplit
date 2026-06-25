from concurrent.futures import ThreadPoolExecutor
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..agents.boss_agent import plan_chat_run
from ..database import SessionLocal, get_db
from ..services.execution_service import create_workflow_run, run_workflow_sync

router = APIRouter(prefix="/api/chat", tags=["chat"])
_executor = ThreadPoolExecutor(max_workers=2)


def _run_async(run_id: int) -> None:
    with SessionLocal() as db:
        run_workflow_sync(db, run_id)


@router.post("/run")
def chat_run(payload: dict[str, Any], db: Session = Depends(get_db)):
    message = payload.get("user_message") or ""
    plan = plan_chat_run(db, message, payload.get("workflow_id"), payload.get("variables") or {})
    if not plan.get("ok"):
        raise HTTPException(status_code=400, detail=plan.get("message"))
    workflow = plan["workflow"]
    run = create_workflow_run(db, workflow.id, message, plan.get("variables") or {})
    _executor.submit(_run_async, run.id)
    return {"run_id": run.id, "selected_workflow": {"id": workflow.id, "name": workflow.name}, "initial_status": run.status, "variables": plan.get("variables")}
