from fastapi import APIRouter, HTTPException

from ..services.vision_service import detect_text, match_template, take_current_screenshot

router = APIRouter(prefix="/api/vision", tags=["vision"])


@router.post("/test-screenshot")
def test_screenshot():
    try:
        return take_current_screenshot()
    except Exception as exc:
        raise HTTPException(status_code=503, detail=f"Screenshot capture failed: {exc}")


@router.post("/match-template")
def test_match(payload: dict):
    current = payload.get("current_screenshot")
    reference = payload.get("reference_screenshot")
    if not reference:
        raise HTTPException(status_code=400, detail="reference_screenshot is required")
    if not current:
        current = take_current_screenshot()["path"]
    return match_template(current, reference)


@router.post("/test-ocr")
def test_ocr(payload: dict):
    screenshot = payload.get("screenshot")
    if not screenshot:
        screenshot = take_current_screenshot()["path"]
    return detect_text(screenshot, payload.get("expected_text"))
