from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db
from ..services.workflow_service import normalize_workflow

router = APIRouter(tags=["audit"])


@router.get("/api/audit-logs", response_model=list[schemas.AuditLogOut])
def list_audit_logs(db: Session = Depends(get_db)):
    return db.scalars(select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(100)).all()


@router.get("/api/dashboard", response_model=schemas.DashboardStats)
def dashboard(db: Session = Depends(get_db)):
    workflows = db.scalars(select(models.WorkflowTemplate).order_by(models.WorkflowTemplate.updated_at.desc()).limit(5)).all()
    logs = db.scalars(select(models.AuditLog).order_by(models.AuditLog.created_at.desc()).limit(10)).all()
    total_workflows = db.scalar(select(func.count(models.WorkflowTemplate.id))) or 0
    total_cards = db.scalar(select(func.count(models.WorkflowNode.id))) or 0
    uploaded_screenshots = db.scalar(select(func.count(models.CardScreenshot.id))) or 0
    return {
        "total_workflows": total_workflows,
        "total_cards": total_cards,
        "uploaded_screenshots": uploaded_screenshots,
        "recent_workflows": [normalize_workflow(workflow) for workflow in workflows],
        "recent_audit_logs": logs,
    }
