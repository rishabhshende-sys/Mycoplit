from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..config import UPLOAD_DIR
from ..database import get_db
from ..services.file_service import inspect_file, save_upload

router = APIRouter(prefix="/api/files", tags=["files"])


@router.post("/upload")
def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return save_upload(db, file)


@router.get("")
def list_files(db: Session = Depends(get_db)):
    rows = list(db.scalars(select(models.UploadedFile).order_by(models.UploadedFile.created_at.desc())).all())
    sample = UPLOAD_DIR / "sample_sales.csv"
    items = [{"id": r.id, "original_name": r.original_name, "stored_path": r.stored_path, "file_type": r.file_type, "row_count": r.row_count, "status": r.status, "created_at": r.created_at} for r in rows]
    if sample.exists():
        items.append({"id": 0, "original_name": "sample_sales.csv", "stored_path": str(sample), "file_type": "csv", "row_count": inspect_file(sample)["row_count"], "status": "sample", "created_at": None})
    return items


@router.get("/{file_id}")
def get_file(file_id: int, db: Session = Depends(get_db)):
    if file_id == 0:
        sample = UPLOAD_DIR / "sample_sales.csv"
        return {"id": 0, "original_name": "sample_sales.csv", "stored_path": str(sample), **inspect_file(sample)}
    item = db.get(models.UploadedFile, file_id)
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    return {**item.__dict__, **inspect_file(item.stored_path)}


@router.post("/{file_id}/inspect")
def inspect_uploaded_file(file_id: int, db: Session = Depends(get_db)):
    if file_id == 0:
        return inspect_file(UPLOAD_DIR / "sample_sales.csv")
    item = db.get(models.UploadedFile, file_id)
    if not item:
        raise HTTPException(status_code=404, detail="File not found")
    return inspect_file(item.stored_path)
