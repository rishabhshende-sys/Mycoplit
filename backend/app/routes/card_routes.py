from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import card_service, workflow_service
from ..services.audit_service import log_action
from ..services.workflow_service import decode_json, encode_json

router = APIRouter(tags=["cards"])


@router.post("/api/workflows/{workflow_id}/nodes", response_model=schemas.WorkflowNodeOut)
def create_node(workflow_id: int, payload: schemas.NodeCreate, db: Session = Depends(get_db)):
    if not db.get(models.WorkflowTemplate, workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return card_service.create_node(db, workflow_id, payload)


@router.put("/api/workflows/{workflow_id}/nodes/{node_id}", response_model=schemas.WorkflowNodeOut)
def update_node(workflow_id: int, node_id: int, payload: schemas.NodeUpdate, db: Session = Depends(get_db)):
    node = card_service.update_node(db, workflow_id, node_id, payload)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.delete("/api/workflows/{workflow_id}/nodes/{node_id}")
def delete_node(workflow_id: int, node_id: int, db: Session = Depends(get_db)):
    if not card_service.delete_node(db, workflow_id, node_id):
        raise HTTPException(status_code=404, detail="Node not found")
    return {"ok": True}


@router.get("/api/nodes/{node_id}", response_model=schemas.WorkflowNodeOut)
def get_node(node_id: int, db: Session = Depends(get_db)):
    node = card_service.get_node(db, node_id)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node


@router.post("/api/nodes/{node_id}/actions", response_model=schemas.CardActionOut)
def create_action(node_id: int, payload: schemas.ActionCreate, db: Session = Depends(get_db)):
    if not db.get(models.WorkflowNode, node_id):
        raise HTTPException(status_code=404, detail="Node not found")
    action = models.CardAction(
        node_id=node_id,
        action_order=payload.action_order,
        action_type=payload.action_type,
        action_config_json=encode_json(payload.action_config_json),
        timeout_seconds=payload.timeout_seconds,
        retry_count=payload.retry_count,
        approved_for_execution=payload.approved_for_execution,
        requires_gui_control=payload.requires_gui_control,
        safety_notes=payload.safety_notes,
    )
    db.add(action)
    db.flush()
    log_action(db, "create", "action", action.id, f"Configured action {action.action_type}")
    db.commit()
    db.refresh(action)
    action.action_config_json = decode_json(action.action_config_json)  # type: ignore[assignment]
    return action


@router.get("/api/nodes/{node_id}/actions", response_model=list[schemas.CardActionOut])
def list_actions(node_id: int, db: Session = Depends(get_db)):
    actions = db.query(models.CardAction).filter_by(node_id=node_id).order_by(models.CardAction.action_order).all()
    for action in actions:
        action.action_config_json = decode_json(action.action_config_json)  # type: ignore[assignment]
    return actions


@router.put("/api/actions/{action_id}", response_model=schemas.CardActionOut)
def update_action(action_id: int, payload: schemas.ActionUpdate, db: Session = Depends(get_db)):
    action = db.get(models.CardAction, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    data = payload.model_dump(exclude_unset=True)
    if "action_config_json" in data:
        data["action_config_json"] = encode_json(data["action_config_json"])
    for key, value in data.items():
        setattr(action, key, value)
    log_action(db, "update", "action", action.id, f"Updated action {action.action_type}")
    db.commit()
    db.refresh(action)
    action.action_config_json = decode_json(action.action_config_json)  # type: ignore[assignment]
    return action


@router.delete("/api/actions/{action_id}")
def delete_action(action_id: int, db: Session = Depends(get_db)):
    action = db.get(models.CardAction, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Action not found")
    db.delete(action)
    log_action(db, "delete", "action", action_id, "Deleted configured action")
    db.commit()
    return {"ok": True}
