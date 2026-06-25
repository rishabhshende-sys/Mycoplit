from typing import Any


def build_final_answer(summary: dict[str, Any], reports: list[dict[str, Any]]) -> dict[str, Any]:
    links = [r.get("download_url") for r in reports if r.get("download_url")]
    text = (
        f"Analysis completed. Total sales value is {summary.get('total_sales_value', 0)} "
        f"across {summary.get('invoice_count', 0)} invoices. Excel and PDF reports are ready."
    )
    return {"answer": text, "summary": summary, "reports": reports, "download_links": links}
