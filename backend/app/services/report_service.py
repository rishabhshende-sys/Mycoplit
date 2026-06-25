from pathlib import Path
from typing import Any

from openpyxl import Workbook
from sqlalchemy.orm import Session

from .. import models
from ..config import REPORT_DIR
from .audit_service import log_action
from .workflow_service import encode_json


def _summary_text(summary: dict[str, Any]) -> str:
    return f"Total sales {summary.get('total_sales_value', 0)} across {summary.get('invoice_count', 0)} invoices."


def generate_excel(db: Session, workflow_run_id: int, summary: dict[str, Any]) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"workflow_{workflow_run_id}_sales_report.xlsx"
    wb = Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["Metric", "Value"])
    for key in ["total_sales_value", "total_quantity", "invoice_count", "first_invoice_date", "last_invoice_date"]:
        ws.append([key, summary.get(key)])
    month_ws = wb.create_sheet("Month Wise")
    month_ws.append(["Month", "Sales", "Quantity", "Invoices"])
    for row in summary.get("month_wise_summary", []):
        month_ws.append([row.get("month"), row.get("sales"), row.get("quantity"), row.get("invoices")])
    wb.save(path)
    return _save_report(db, workflow_run_id, "excel", path, summary)


def generate_pdf(db: Session, workflow_run_id: int, summary: dict[str, Any]) -> dict[str, Any]:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORT_DIR / f"workflow_{workflow_run_id}_sales_report.pdf"
    lines = [
        "Sales Analysis Report",
        f"Total sales value: {summary.get('total_sales_value', 0)}",
        f"Total quantity: {summary.get('total_quantity', 0)}",
        f"Invoice count: {summary.get('invoice_count', 0)}",
        f"First invoice date: {summary.get('first_invoice_date')}",
        f"Last invoice date: {summary.get('last_invoice_date')}",
        "Month Wise Summary",
    ]
    for row in summary.get("month_wise_summary", [])[:20]:
        lines.append(f"{row.get('month')}: sales={row.get('sales')} quantity={row.get('quantity')}")
    _write_simple_pdf(path, lines)
    return _save_report(db, workflow_run_id, "pdf", path, summary)


def _write_simple_pdf(path: Path, lines: list[str]) -> None:
    content_lines = ["BT", "/F1 12 Tf", "72 750 Td"]
    for index, line in enumerate(lines):
        clean = str(line).replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if index:
            content_lines.append("0 -18 Td")
        content_lines.append(f"({clean}) Tj")
    content_lines.append("ET")
    stream = "\n".join(content_lines).encode("latin-1", errors="replace")
    objects = [
        b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n",
        b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n",
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n",
        b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n",
        b"5 0 obj << /Length " + str(len(stream)).encode() + b" >> stream\n" + stream + b"\nendstream endobj\n",
    ]
    output = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(len(output))
        output.extend(obj)
    xref = len(output)
    output.extend(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets[1:]:
        output.extend(f"{offset:010d} 00000 n \n".encode())
    output.extend(f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF\n".encode())
    path.write_bytes(output)


def _save_report(db: Session, workflow_run_id: int, report_type: str, path: Path, summary: dict[str, Any]) -> dict[str, Any]:
    item = models.Report(workflow_run_id=workflow_run_id, report_type=report_type, file_path=str(path), summary=_summary_text(summary))
    db.add(item)
    db.flush()
    log_action(db, "report_generated", "report", item.id, encode_json({"type": report_type, "path": str(path)}))
    db.commit()
    return {"report_id": item.id, "report_type": report_type, "file_path": str(path), "download_url": f"/api/reports/{item.id}/download", "summary": item.summary}
