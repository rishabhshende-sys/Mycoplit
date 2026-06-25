import shutil
from pathlib import Path
from uuid import uuid4

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from .. import models, schemas
from ..config import SCREENSHOT_DIR
from ..database import get_db
from ..services.audit_service import log_action
from ..services.workflow_service import decode_json, encode_json

router = APIRouter(tags=["screenshots"])


@router.post("/api/nodes/{node_id}/screenshots", response_model=schemas.CardScreenshotOut)
def upload_screenshot(
    node_id: int,
    screenshot_type: str = Form(...),
    description: str | None = Form(None),
    expected_text: str | None = Form(None),
    confidence_threshold: float = Form(0.8),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if not db.get(models.WorkflowNode, node_id):
        raise HTTPException(status_code=404, detail="Node not found")
    suffix = file.filename.rsplit(".", 1)[-1] if file.filename and "." in file.filename else "png"
    filename = f"node_{node_id}_{screenshot_type}_{uuid4().hex}.{suffix}"
    destination = SCREENSHOT_DIR / filename
    with destination.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    shot = models.CardScreenshot(
        node_id=node_id,
        screenshot_type=screenshot_type,
        file_path=str(destination),
        description=description,
        expected_text=expected_text,
        crop_json=encode_json({}),
        confidence_threshold=confidence_threshold,
    )
    db.add(shot)
    db.flush()
    log_action(db, "create", "screenshot", shot.id, f"Uploaded {screenshot_type} screenshot")
    db.commit()
    db.refresh(shot)
    shot.crop_json = decode_json(shot.crop_json)  # type: ignore[assignment]
    return shot


@router.get("/api/nodes/{node_id}/screenshots", response_model=list[schemas.CardScreenshotOut])
def list_screenshots(node_id: int, db: Session = Depends(get_db)):
    shots = db.query(models.CardScreenshot).filter_by(node_id=node_id).order_by(models.CardScreenshot.created_at).all()
    for shot in shots:
        shot.crop_json = decode_json(shot.crop_json)  # type: ignore[assignment]
    return shots


@router.get("/api/screenshots/file")
def screenshot_file(path: str):
    target = Path(path).resolve()
    root = SCREENSHOT_DIR.resolve()
    if root not in target.parents and target != root:
        raise HTTPException(status_code=403, detail="Screenshot path is outside storage")
    if not target.exists():
        raise HTTPException(status_code=404, detail="Screenshot file not found")
    return FileResponse(str(target))


@router.delete("/api/screenshots/{screenshot_id}")
def delete_screenshot(screenshot_id: int, db: Session = Depends(get_db)):
    shot = db.get(models.CardScreenshot, screenshot_id)
    if not shot:
        raise HTTPException(status_code=404, detail="Screenshot not found")
    db.delete(shot)
    log_action(db, "delete", "screenshot", screenshot_id, "Deleted screenshot metadata")
    db.commit()
    return {"ok": True}
