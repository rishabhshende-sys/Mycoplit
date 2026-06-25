from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from .audit_service import log_action
from .workflow_service import decode_json, encode_json


def normalize_node(node: models.WorkflowNode) -> models.WorkflowNode:
    node.config_json = decode_json(node.config_json)  # type: ignore[assignment]
    for shot in node.screenshots:
        shot.crop_json = decode_json(shot.crop_json)  # type: ignore[assignment]
    for action in node.actions:
        action.action_config_json = decode_json(action.action_config_json)  # type: ignore[assignment]
    return node


def create_node(db: Session, workflow_id: int, data: schemas.NodeCreate) -> models.WorkflowNode:
    payload = data.model_dump()
    payload["workflow_id"] = workflow_id
    payload["config_json"] = encode_json(payload.get("config_json"))
    node = models.WorkflowNode(**payload)
    db.add(node)
    db.flush()
    log_action(db, "create", "node", node.id, f"Created card {node.card_name}")
    db.commit()
    return get_node(db, node.id)  # type: ignore[return-value]


def get_node(db: Session, node_id: int) -> models.WorkflowNode | None:
    node = db.scalar(
        select(models.WorkflowNode)
        .where(models.WorkflowNode.id == node_id)
        .options(selectinload(models.WorkflowNode.screenshots), selectinload(models.WorkflowNode.actions))
    )
    return normalize_node(node) if node else None


def update_node(db: Session, workflow_id: int, node_id: int, data: schemas.NodeUpdate) -> models.WorkflowNode | None:
    node = db.get(models.WorkflowNode, node_id)
    if not node or node.workflow_id != workflow_id:
        return None
    payload = data.model_dump(exclude_unset=True)
    if "config_json" in payload:
        payload["config_json"] = encode_json(payload["config_json"])
    for key, value in payload.items():
        setattr(node, key, value)
    log_action(db, "update", "node", node.id, f"Updated card {node.card_name}")
    db.commit()
    return get_node(db, node_id)


def delete_node(db: Session, workflow_id: int, node_id: int) -> bool:
    node = db.get(models.WorkflowNode, node_id)
    if not node or node.workflow_id != workflow_id:
        return False
    db.delete(node)
    log_action(db, "delete", "node", node_id, f"Deleted card {node.card_name}")
    db.commit()
    return True
