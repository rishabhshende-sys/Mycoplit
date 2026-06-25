import json

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from .. import models, schemas
from .audit_service import log_action


def encode_json(value: dict | None) -> str | None:
    return json.dumps(value or {})


def decode_json(value: str | None) -> dict:
    return json.loads(value) if value else {}


def normalize_workflow(workflow: models.WorkflowTemplate) -> models.WorkflowTemplate:
    for node in workflow.nodes:
        node.config_json = decode_json(node.config_json)  # type: ignore[assignment]
        for shot in node.screenshots:
            shot.crop_json = decode_json(shot.crop_json)  # type: ignore[assignment]
        for action in node.actions:
            action.action_config_json = decode_json(action.action_config_json)  # type: ignore[assignment]
    for edge in workflow.edges:
        edge.condition_json = decode_json(edge.condition_json)  # type: ignore[assignment]
    return workflow


def get_workflows(db: Session) -> list[models.WorkflowTemplate]:
    workflows = db.scalars(
        select(models.WorkflowTemplate)
        .options(selectinload(models.WorkflowTemplate.nodes), selectinload(models.WorkflowTemplate.edges))
        .order_by(models.WorkflowTemplate.updated_at.desc())
    ).all()
    return [normalize_workflow(workflow) for workflow in workflows]


def get_workflow(db: Session, workflow_id: int) -> models.WorkflowTemplate | None:
    workflow = db.scalar(
        select(models.WorkflowTemplate)
        .where(models.WorkflowTemplate.id == workflow_id)
        .options(
            selectinload(models.WorkflowTemplate.nodes).selectinload(models.WorkflowNode.screenshots),
            selectinload(models.WorkflowTemplate.nodes).selectinload(models.WorkflowNode.actions),
            selectinload(models.WorkflowTemplate.edges),
        )
    )
    return normalize_workflow(workflow) if workflow else None


def create_workflow(db: Session, data: schemas.WorkflowCreate) -> models.WorkflowTemplate:
    workflow = models.WorkflowTemplate(**data.model_dump())
    db.add(workflow)
    db.flush()
    log_action(db, "create", "workflow", workflow.id, f"Created workflow {workflow.name}")
    db.commit()
    db.refresh(workflow)
    return normalize_workflow(workflow)


def update_workflow(db: Session, workflow_id: int, data: schemas.WorkflowUpdate) -> models.WorkflowTemplate | None:
    workflow = db.get(models.WorkflowTemplate, workflow_id)
    if not workflow:
        return None
    for key, value in data.model_dump(exclude_unset=True).items():
        setattr(workflow, key, value)
    log_action(db, "update", "workflow", workflow.id, f"Updated workflow {workflow.name}")
    db.commit()
    return get_workflow(db, workflow_id)


def delete_workflow(db: Session, workflow_id: int) -> bool:
    workflow = db.get(models.WorkflowTemplate, workflow_id)
    if not workflow:
        return False
    db.delete(workflow)
    log_action(db, "delete", "workflow", workflow_id, f"Deleted workflow {workflow.name}")
    db.commit()
    return True
