from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/reports", tags=["reports"])


@router.get("")
def list_reports(db: Session = Depends(get_db)):
    rows = list(db.scalars(select(models.Report).order_by(models.Report.created_at.desc())).all())
    return [{"id": r.id, "workflow_run_id": r.workflow_run_id, "report_type": r.report_type, "file_path": r.file_path, "summary": r.summary, "download_url": f"/api/reports/{r.id}/download", "created_at": r.created_at} for r in rows]


@router.get("/{report_id}/download")
def download_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(models.Report, report_id)
    if not report or not Path(report.file_path).exists():
        raise HTTPException(status_code=404, detail="Report not found")
    return FileResponse(report.file_path, filename=Path(report.file_path).name)
