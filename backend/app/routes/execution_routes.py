from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import SessionLocal, get_db
from ..services import execution_service
from ..services.workflow_service import decode_json

router = APIRouter(tags=["execution"])
_executor = ThreadPoolExecutor(max_workers=2)


def _run_async(run_id: int) -> None:
    with SessionLocal() as db:
        execution_service.run_workflow_sync(db, run_id)


@router.post("/api/workflows/{workflow_id}/run")
def run_workflow(workflow_id: int, payload: dict[str, Any] | None = None, db: Session = Depends(get_db)):
    if not db.get(models.WorkflowTemplate, workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    payload = payload or {}
    run = execution_service.create_workflow_run(db, workflow_id, payload.get("user_message"), payload.get("variables") or payload.get("input_json") or {})
    _executor.submit(_run_async, run.id)
    return {"run_id": run.id, "status": run.status}


@router.get("/api/workflow-runs/{run_id}")
def get_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(models.WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    return {**run.__dict__, "input_json": decode_json(run.input_json), "final_output": decode_json(run.final_output)}


@router.get("/api/workflow-runs/{run_id}/nodes")
def get_node_runs(run_id: int, db: Session = Depends(get_db)):
    rows = list(db.scalars(select(models.NodeRun).where(models.NodeRun.workflow_run_id == run_id).order_by(models.NodeRun.id)).all())
    return [{**r.__dict__, "input_json": decode_json(r.input_json), "output_json": decode_json(r.output_json)} for r in rows]


@router.get("/api/workflow-runs/{run_id}/actions")
def get_action_runs(run_id: int, db: Session = Depends(get_db)):
    node_ids = [r.id for r in db.scalars(select(models.NodeRun).where(models.NodeRun.workflow_run_id == run_id)).all()]
    rows = list(db.scalars(select(models.ActionRun).where(models.ActionRun.node_run_id.in_(node_ids)).order_by(models.ActionRun.id)).all()) if node_ids else []
    return [{**r.__dict__, "input_json": decode_json(r.input_json), "output_json": decode_json(r.output_json), "coordinates_json": decode_json(r.coordinates_json)} for r in rows]


@router.get("/api/workflow-runs/{run_id}/events")
def get_events(run_id: int, db: Session = Depends(get_db)):
    rows = list(db.scalars(select(models.WorkflowEvent).where(models.WorkflowEvent.workflow_run_id == run_id).order_by(models.WorkflowEvent.id)).all())
    return [{**r.__dict__, "payload_json": decode_json(r.payload_json)} for r in rows]


@router.get("/api/workflow-runs/{run_id}/stream")
def stream_events(run_id: int):
    return StreamingResponse(execution_service.sse_events(SessionLocal, run_id), media_type="text/event-stream")


@router.post("/api/workflow-runs/{run_id}/stop")
def stop_run(run_id: int, db: Session = Depends(get_db)):
    run = db.get(models.WorkflowRun, run_id)
    if not run:
        raise HTTPException(status_code=404, detail="Run not found")
    run.stop_requested = True
    run.status = "stopped" if run.status in {"queued", "paused"} else run.status
    execution_service.emit_event(db, run.id, run.current_node_id, "workflow_stopped", "Workflow stop requested", {})
    db.commit()
    return {"ok": True, "status": "stop_requested"}


@router.post("/api/node-runs/{node_run_id}/retry")
def retry_node(node_run_id: int, db: Session = Depends(get_db)):
    node_run = db.get(models.NodeRun, node_run_id)
    if not node_run:
        raise HTTPException(status_code=404, detail="Node run not found")
    execution_service.emit_event(db, node_run.workflow_run_id, node_run.node_id, "workflow_retried", "Retry requested for node", {"node_run_id": node_run_id})
    return {"ok": True, "message": "Retry request audit logged. Rerun workflow or node-level retry can be expanded in the next iteration."}


@router.post("/api/node-runs/{node_run_id}/skip")
def skip_node(node_run_id: int, db: Session = Depends(get_db)):
    node_run = db.get(models.NodeRun, node_run_id)
    if not node_run:
        raise HTTPException(status_code=404, detail="Node run not found")
    node = db.get(models.WorkflowNode, node_run.node_id)
    if not node or not node.allow_skip_on_failure:
        raise HTTPException(status_code=400, detail="Node is not configured to allow skip on failure")
    node_run.status = "skipped"
    node_run.completed_at = datetime.utcnow()
    execution_service.emit_event(db, node_run.workflow_run_id, node_run.node_id, "node_skipped", "Node skipped by user", {"node_run_id": node_run_id})
    db.commit()
    return {"ok": True, "status": "skipped"}


@router.post("/api/node-runs/{node_run_id}/approve")
def approve_node(node_run_id: int, db: Session = Depends(get_db)):
    node_run = db.get(models.NodeRun, node_run_id)
    if not node_run:
        raise HTTPException(status_code=404, detail="Node run not found")
    node_run.status = "approved"
    execution_service.emit_event(db, node_run.workflow_run_id, node_run.node_id, "gui_action_approved", "Approval granted", {"node_run_id": node_run_id})
    db.commit()
    return {"ok": True, "status": "approved"}


@router.post("/api/node-runs/{node_run_id}/reject")
def reject_node(node_run_id: int, db: Session = Depends(get_db)):
    node_run = db.get(models.NodeRun, node_run_id)
    if not node_run:
        raise HTTPException(status_code=404, detail="Node run not found")
    node_run.status = "rejected"
    execution_service.emit_event(db, node_run.workflow_run_id, node_run.node_id, "gui_action_rejected", "Approval rejected", {"node_run_id": node_run_id})
    db.commit()
    return {"ok": True, "status": "rejected"}
