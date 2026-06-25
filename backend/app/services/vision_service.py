import time
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image, ImageGrab

from ..config import SCREENSHOT_DIR, STORAGE_DIR

RUN_SCREENSHOT_DIR = SCREENSHOT_DIR / "runs"


def take_current_screenshot() -> dict[str, Any]:
    RUN_SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    path = RUN_SCREENSHOT_DIR / f"screen_{datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')}.png"
    image = ImageGrab.grab()
    image.save(path)
    return {"path": str(path), "width": image.width, "height": image.height, "timestamp": datetime.utcnow().isoformat()}


def match_template(current_screenshot: str, reference_screenshot: str) -> dict[str, Any]:
    try:
        import cv2
        import numpy as np
    except Exception as exc:
        return {"match_found": False, "confidence": 0.0, "error": f"OpenCV engine not configured: {exc}"}
    current = cv2.imread(str(current_screenshot), cv2.IMREAD_COLOR)
    reference = cv2.imread(str(reference_screenshot), cv2.IMREAD_COLOR)
    if current is None or reference is None:
        return {"match_found": False, "confidence": 0.0, "error": "Screenshot file could not be read."}
    if reference.shape[0] > current.shape[0] or reference.shape[1] > current.shape[1]:
        return {"match_found": False, "confidence": 0.0, "error": "Reference image is larger than current screenshot."}
    result = cv2.matchTemplate(current, reference, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, max_loc = cv2.minMaxLoc(result)
    h, w = reference.shape[:2]
    box = {"x": int(max_loc[0]), "y": int(max_loc[1]), "width": int(w), "height": int(h)}
    return {
        "match_found": bool(max_val >= 0.8),
        "confidence": float(round(max_val, 4)),
        "bounding_box": box,
        "center_x": int(max_loc[0] + w / 2),
        "center_y": int(max_loc[1] + h / 2),
    }


def wait_for_image(reference_screenshot: str, timeout: int = 30, confidence_threshold: float = 0.8) -> dict[str, Any]:
    deadline = time.time() + max(1, timeout)
    last: dict[str, Any] = {}
    while time.time() < deadline:
        shot = take_current_screenshot()
        last = match_template(shot["path"], reference_screenshot)
        last["current_screenshot"] = shot["path"]
        if last.get("confidence", 0) >= confidence_threshold:
            last["match_found"] = True
            return last
        time.sleep(0.8)
    last.setdefault("match_found", False)
    last["error"] = f"Timed out waiting for image at confidence {confidence_threshold}."
    return last


def detect_text(current_screenshot: str, expected_text: str | None = None) -> dict[str, Any]:
    try:
        import pytesseract
    except Exception:
        return {"found": False, "confidence": 0.0, "error": "OCR engine not configured."}
    image = Image.open(current_screenshot)
    text = pytesseract.image_to_string(image)
    found = expected_text.lower() in text.lower() if expected_text else bool(text.strip())
    return {"found": found, "confidence": 1.0 if found else 0.0, "text": text, "bounding_box": None}


def wait_for_text(expected_text: str, timeout: int = 30) -> dict[str, Any]:
    deadline = time.time() + max(1, timeout)
    last: dict[str, Any] = {}
    while time.time() < deadline:
        shot = take_current_screenshot()
        last = detect_text(shot["path"], expected_text)
        last["current_screenshot"] = shot["path"]
        if last.get("found"):
            return last
        if last.get("error"):
            return last
        time.sleep(0.8)
    last.setdefault("found", False)
    last["error"] = f"Timed out waiting for text: {expected_text}"
    return last
