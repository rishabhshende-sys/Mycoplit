from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services import workflow_service
from ..services.audit_service import log_action
from ..services.workflow_service import encode_json, normalize_workflow

router = APIRouter(prefix="/api/workflows", tags=["workflows"])


@router.post("", response_model=schemas.WorkflowOut)
def create_workflow(payload: schemas.WorkflowCreate, db: Session = Depends(get_db)):
    return workflow_service.create_workflow(db, payload)


@router.get("", response_model=list[schemas.WorkflowOut])
def list_workflows(db: Session = Depends(get_db)):
    return workflow_service.get_workflows(db)


@router.get("/{workflow_id}", response_model=schemas.WorkflowOut)
def get_workflow(workflow_id: int, db: Session = Depends(get_db)):
    workflow = workflow_service.get_workflow(db, workflow_id)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.put("/{workflow_id}", response_model=schemas.WorkflowOut)
def update_workflow(workflow_id: int, payload: schemas.WorkflowUpdate, db: Session = Depends(get_db)):
    workflow = workflow_service.update_workflow(db, workflow_id, payload)
    if not workflow:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return workflow


@router.delete("/{workflow_id}")
def delete_workflow(workflow_id: int, db: Session = Depends(get_db)):
    if not workflow_service.delete_workflow(db, workflow_id):
        raise HTTPException(status_code=404, detail="Workflow not found")
    return {"ok": True}


@router.post("/{workflow_id}/edges", response_model=schemas.WorkflowEdgeOut)
def create_edge(workflow_id: int, payload: schemas.EdgeCreate, db: Session = Depends(get_db)):
    edge = models.WorkflowEdge(
        workflow_id=workflow_id,
        source_node_id=payload.source_node_id,
        target_node_id=payload.target_node_id,
        condition_json=encode_json(payload.condition_json),
    )
    db.add(edge)
    db.flush()
    log_action(db, "create", "edge", edge.id, f"Connected {edge.source_node_id} to {edge.target_node_id}")
    db.commit()
    db.refresh(edge)
    edge.condition_json = workflow_service.decode_json(edge.condition_json)  # type: ignore[assignment]
    return edge


@router.delete("/{workflow_id}/edges/{edge_id}")
def delete_edge(workflow_id: int, edge_id: int, db: Session = Depends(get_db)):
    edge = db.get(models.WorkflowEdge, edge_id)
    if not edge or edge.workflow_id != workflow_id:
        raise HTTPException(status_code=404, detail="Edge not found")
    db.delete(edge)
    log_action(db, "delete", "edge", edge_id, "Deleted workflow connection")
    db.commit()
    return {"ok": True}
