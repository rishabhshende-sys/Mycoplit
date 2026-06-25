import asyncio
import json
import time
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..config import UPLOAD_DIR
from .action_service import ApprovalRequired, SafetyBlock, execute_action
from .audit_service import log_action
from .workflow_service import decode_json, encode_json


def emit_event(db: Session, run_id: int, node_id: int | None, event_type: str, message: str, payload: dict[str, Any] | None = None) -> models.WorkflowEvent:
    event = models.WorkflowEvent(workflow_run_id=run_id, node_id=node_id, event_type=event_type, message=message, payload_json=encode_json(payload or {}))
    db.add(event)
    log_action(db, event_type, "workflow_run", run_id, message)
    db.commit()
    db.refresh(event)
    return event


def create_workflow_run(db: Session, workflow_id: int, user_message: str | None = None, variables: dict[str, Any] | None = None) -> models.WorkflowRun:
    run = models.WorkflowRun(workflow_id=workflow_id, user_message=user_message, input_json=encode_json(variables or {}), status="queued", stop_requested=False)
    db.add(run)
    db.commit()
    db.refresh(run)
    emit_event(db, run.id, None, "workflow_run_started", "Workflow run started", {"workflow_id": workflow_id})
    return run


def _ordered_nodes(db: Session, workflow_id: int) -> list[models.WorkflowNode]:
    nodes = list(db.scalars(select(models.WorkflowNode).where(models.WorkflowNode.workflow_id == workflow_id)).all())
    edges = list(db.scalars(select(models.WorkflowEdge).where(models.WorkflowEdge.workflow_id == workflow_id)).all())
    by_id = {n.id: n for n in nodes}
    start = next((n for n in nodes if n.node_type == "START" or n.card_name.upper() == "START"), None)
    if not start:
        return sorted(nodes, key=lambda n: n.position_x)
    ordered = [start]
    seen = {start.id}
    current = start.id
    while True:
        edge = next((e for e in edges if e.source_node_id == current and e.target_node_id not in seen), None)
        if not edge or edge.target_node_id not in by_id:
            break
        ordered.append(by_id[edge.target_node_id])
        seen.add(edge.target_node_id)
        current = edge.target_node_id
    ordered.extend([n for n in sorted(nodes, key=lambda n: n.position_x) if n.id not in seen])
    return ordered


def _stop_if_requested(db: Session, run: models.WorkflowRun) -> bool:
    db.refresh(run)
    if run.stop_requested or run.status == "stopped":
        run.status = "stopped"
        run.completed_at = datetime.utcnow()
        db.commit()
        emit_event(db, run.id, run.current_node_id, "workflow_stopped", "Workflow stopped", {})
        return True
    return False


def _wait_for_approval(db: Session, run: models.WorkflowRun, node_run: models.NodeRun, action_run: models.ActionRun, message: str) -> str:
    run.status = "paused"
    node_run.status = "approval_required"
    action_run.status = "approval_required"
    action_run.error_message = message
    db.commit()
    emit_event(db, run.id, node_run.node_id, "approval_required", message, {"node_run_id": node_run.id, "action_run_id": action_run.id})
    deadline = time.time() + 600
    while time.time() < deadline:
        db.refresh(run)
        db.refresh(node_run)
        if run.stop_requested or run.status == "stopped":
            return "stopped"
        if node_run.status in {"approved", "rejected", "skipped"}:
            return node_run.status
        time.sleep(0.8)
    return "rejected"


def _store_action_output(action_run: models.ActionRun, output: dict[str, Any]) -> None:
    action_run.output_json = encode_json(output)
    action_run.screenshot_path = output.get("path") or output.get("current_screenshot")
    action_run.confidence = output.get("confidence")
    coords = output.get("coordinates") or ({"x": output.get("center_x"), "y": output.get("center_y")} if output.get("center_x") is not None else None)
    action_run.coordinates_json = encode_json(coords) if coords else None
    action_run.before_screenshot_path = output.get("before_screenshot_path")
    action_run.after_screenshot_path = output.get("after_screenshot_path")


def run_workflow_sync(db: Session, run_id: int) -> None:
    run = db.get(models.WorkflowRun, run_id)
    if not run:
        return
    workflow = db.get(models.WorkflowTemplate, run.workflow_id)
    if not workflow:
        return
    context: dict[str, Any] = dict(decode_json(run.input_json) or {})
    context.setdefault("uploaded_file", str(UPLOAD_DIR / "sample_sales.csv"))
    run.status = "running"
    run.started_at = datetime.utcnow()
    db.commit()
    try:
        for node in _ordered_nodes(db, run.workflow_id):
            if _stop_if_requested(db, run):
                return
            run.current_node_id = node.id
            node_run = models.NodeRun(workflow_run_id=run.id, node_id=node.id, status="running", input_json=encode_json(context), started_at=datetime.utcnow())
            db.add(node_run)
            db.commit()
            db.refresh(node_run)
            emit_event(db, run.id, node.id, "node_started", f"{node.card_name} started", {"node_run_id": node_run.id, "card_name": node.card_name})
            actions = list(db.scalars(select(models.CardAction).where(models.CardAction.node_id == node.id).order_by(models.CardAction.action_order)).all())
            if not actions:
                actions = [models.CardAction(id=None, node_id=node.id, action_order=1, action_type="wait", action_config_json=encode_json({"seconds": 0}), approved_for_execution=True)]
            node_output: dict[str, Any] = {}
            for action in actions:
                if _stop_if_requested(db, run):
                    return
                action_run = models.ActionRun(node_run_id=node_run.id, action_id=action.id, action_type=action.action_type, status="running", input_json=encode_json(context), started_at=datetime.utcnow())
                db.add(action_run)
                db.commit()
                db.refresh(action_run)
                emit_event(db, run.id, node.id, "action_started", f"{node.card_name}: {action.action_type} started", {"action_run_id": action_run.id, "action_type": action.action_type})
                approved_retry = False
                while True:
                    try:
                        if approved_retry:
                            context["_approved_once"] = True
                        output = execute_action(db, workflow, run, node, action, context)
                        context.pop("_approved_once", None)
                        context["last_output"] = output
                        node_output[action.action_type] = output
                        action_run.status = "completed"
                        _store_action_output(action_run, output)
                        action_run.completed_at = datetime.utcnow()
                        db.commit()
                        emit_event(db, run.id, node.id, "action_completed", f"{node.card_name}: {action.action_type} completed", {"output": output, "action_run_id": action_run.id})
                        break
                    except ApprovalRequired as exc:
                        decision = _wait_for_approval(db, run, node_run, action_run, str(exc))
                        if decision == "approved":
                            emit_event(db, run.id, node.id, "gui_action_approved", "GUI action approved", {"action_run_id": action_run.id})
                            run.status = "running"
                            node_run.status = "running"
                            action_run.status = "running"
                            db.commit()
                            if action.action_type == "human_approval":
                                output = {"approved": True, "message": "Human approval received."}
                                context["last_output"] = output
                                node_output[action.action_type] = output
                                action_run.status = "completed"
                                _store_action_output(action_run, output)
                                action_run.completed_at = datetime.utcnow()
                                db.commit()
                                emit_event(db, run.id, node.id, "action_completed", f"{node.card_name}: human_approval completed", {"output": output, "action_run_id": action_run.id})
                                break
                            approved_retry = True
                            continue
                        if decision == "skipped" and node.allow_skip_on_failure:
                            emit_event(db, run.id, node.id, "node_skipped", f"{node.card_name} skipped", {"node_run_id": node_run.id})
                            break
                        run.status = "stopped" if decision == "stopped" else "failed"
                        node_run.status = decision
                        action_run.status = decision
                        action_run.completed_at = datetime.utcnow()
                        run.completed_at = datetime.utcnow()
                        db.commit()
                        emit_event(db, run.id, node.id, "gui_action_rejected", f"Approval decision: {decision}", {"action_run_id": action_run.id})
                        return
                    except (SafetyBlock, Exception) as exc:
                        action_run.status = "failed"
                        action_run.error_message = str(exc)
                        action_run.completed_at = datetime.utcnow()
                        node_run.status = "failed"
                        node_run.error_message = str(exc)
                        db.commit()
                        emit_event(db, run.id, node.id, "action_failed", f"{node.card_name}: {action.action_type} failed - {exc}", {"error": str(exc), "action_run_id": action_run.id})
                        if node.allow_skip_on_failure:
                            emit_event(db, run.id, node.id, "node_skip_available", f"{node.card_name} can be skipped", {"node_run_id": node_run.id})
                        run.status = "failed"
                        run.completed_at = datetime.utcnow()
                        db.commit()
                        emit_event(db, run.id, node.id, "node_failed", f"{node.card_name} failed", {"error": str(exc), "node_run_id": node_run.id})
                        return
            node_run.status = "completed" if node_run.status not in {"skipped"} else node_run.status
            node_run.output_json = encode_json(node_output)
            node_run.completed_at = datetime.utcnow()
            db.commit()
            emit_event(db, run.id, node.id, "node_completed", f"{node.card_name} completed", {"node_run_id": node_run.id})
        run.status = "completed"
        run.final_output = encode_json(context.get("final_answer") or context.get("last_output") or {})
        run.completed_at = datetime.utcnow()
        db.commit()
        emit_event(db, run.id, None, "workflow_completed", "Workflow completed", {"final_output": decode_json(run.final_output)})
    except Exception as exc:
        run.status = "failed"
        run.final_output = encode_json({"error": str(exc)})
        run.completed_at = datetime.utcnow()
        db.commit()
        emit_event(db, run.id, run.current_node_id, "workflow_failed", f"Workflow failed - {exc}", {"error": str(exc)})


async def sse_events(db_factory, run_id: int):
    last_id = 0
    while True:
        with db_factory() as db:
            events = list(db.scalars(select(models.WorkflowEvent).where(models.WorkflowEvent.workflow_run_id == run_id, models.WorkflowEvent.id > last_id).order_by(models.WorkflowEvent.id)).all())
            run = db.get(models.WorkflowRun, run_id)
            for event in events:
                last_id = event.id
                payload = {"id": event.id, "workflow_run_id": event.workflow_run_id, "node_id": event.node_id, "event_type": event.event_type, "message": event.message, "payload": decode_json(event.payload_json), "created_at": event.created_at.isoformat()}
                yield f"event: {event.event_type}\ndata: {json.dumps(payload)}\n\n"
            if run and run.status in {"completed", "failed", "stopped"} and not events:
                yield f"event: close\ndata: {json.dumps({'status': run.status})}\n\n"
                break
        await asyncio.sleep(0.8)
