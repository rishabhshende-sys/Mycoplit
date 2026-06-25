from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models
from ..config import CLEANED_DIR, UPLOAD_DIR
from .audit_service import log_action
from .workflow_service import encode_json

SALES_COLUMNS = [
    "invoice_no", "invoice_date", "customer_code", "customer_name", "material_code",
    "material_name", "quantity", "net_value", "plant", "sales_org",
]
COLUMN_MAP = {
    "billing doc": "invoice_no", "invoice no": "invoice_no", "bill no": "invoice_no",
    "billing date": "invoice_date", "invoice date": "invoice_date",
    "sold-to party": "customer_code", "customer code": "customer_code",
    "customer name": "customer_name", "sold-to name": "customer_name",
    "material": "material_code", "material code": "material_code",
    "material description": "material_name", "qty": "quantity", "quantity": "quantity",
    "net amount": "net_value", "net value": "net_value", "amount": "net_value",
}


def read_frame(path: str | Path) -> pd.DataFrame:
    path = Path(path)
    if path.suffix.lower() in {".xlsx", ".xls"}:
        return pd.read_excel(path)
    return pd.read_csv(path)


def inspect_file(path: str | Path) -> dict[str, Any]:
    df = read_frame(path)
    return {
        "columns": list(df.columns),
        "row_count": int(len(df)),
        "sample_rows": df.head(5).fillna("").to_dict(orient="records"),
        "detected_schema": {c: COLUMN_MAP.get(str(c).strip().lower(), str(c).strip()) for c in df.columns},
    }


def save_upload(db: Session, upload: UploadFile) -> models.UploadedFile:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    safe_name = Path(upload.filename or "upload.csv").name
    target = UPLOAD_DIR / safe_name
    suffix = target.suffix.lower().lstrip(".") or "csv"
    with target.open("wb") as handle:
        handle.write(upload.file.read())
    row_count = inspect_file(target)["row_count"]
    item = models.UploadedFile(original_name=safe_name, stored_path=str(target), file_type=suffix, row_count=row_count, status="uploaded")
    db.add(item)
    db.flush()
    log_action(db, "file_uploaded", "uploaded_file", item.id, f"Uploaded {safe_name}")
    db.commit()
    db.refresh(item)
    return item


def clean_file(path: str | Path) -> dict[str, Any]:
    CLEANED_DIR.mkdir(parents=True, exist_ok=True)
    df = read_frame(path)
    df = df.dropna(how="all").copy()
    df.columns = [COLUMN_MAP.get(str(c).strip().lower(), str(c).strip().lower().replace(" ", "_")) for c in df.columns]
    for col in SALES_COLUMNS:
        if col not in df.columns:
            df[col] = None
    df = df[SALES_COLUMNS]
    df["invoice_date"] = pd.to_datetime(df["invoice_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["net_value"] = pd.to_numeric(df["net_value"], errors="coerce").fillna(0)
    df["customer_code"] = df["customer_code"].astype(str).str.strip().str.upper()
    output = CLEANED_DIR / f"cleaned_{Path(path).stem}.csv"
    df.to_csv(output, index=False)
    return {"cleaned_file": str(output), "row_count": int(len(df)), "columns": SALES_COLUMNS}


def validation_warnings(df: pd.DataFrame, variables: dict[str, Any] | None = None) -> list[str]:
    warnings: list[str] = []
    missing = [c for c in SALES_COLUMNS if c not in df.columns]
    if missing:
        warnings.append(f"Missing required columns: {', '.join(missing)}")
    if df.duplicated().sum():
        warnings.append(f"Duplicate rows found: {int(df.duplicated().sum())}")
    for col in ["invoice_no", "invoice_date", "customer_code", "material_code"]:
        if col in df.columns and df[col].isna().sum():
            warnings.append(f"Null values in {col}: {int(df[col].isna().sum())}")
    if "quantity" in df.columns and (pd.to_numeric(df["quantity"], errors="coerce") < 0).sum():
        warnings.append("Negative quantity values found")
    if "net_value" in df.columns and (pd.to_numeric(df["net_value"], errors="coerce") < 0).sum():
        warnings.append("Negative net_value values found")
    return warnings


def save_sales_to_database(db: Session, path: str | Path, source_file_id: int | None = None) -> dict[str, Any]:
    df = read_frame(path)
    imported = 0
    duplicates = 0
    for row in df.fillna("").to_dict(orient="records"):
        key = select(models.SalesFact).where(
            models.SalesFact.invoice_no == str(row["invoice_no"]),
            models.SalesFact.invoice_date == str(row["invoice_date"]),
            models.SalesFact.customer_code == str(row["customer_code"]),
            models.SalesFact.material_code == str(row["material_code"]),
        )
        if db.scalar(key):
            duplicates += 1
            continue
        db.add(models.SalesFact(**{c: row.get(c) for c in SALES_COLUMNS}, source_file_id=source_file_id))
        imported += 1
    log_action(db, "data_imported", "sales_fact", None, encode_json({"imported_count": imported, "duplicate_count": duplicates}))
    db.commit()
    return {"imported_count": imported, "duplicate_count": duplicates}
