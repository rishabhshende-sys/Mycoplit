from datetime import date
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from .. import models


def run_sales_summary(db: Session, variables: dict[str, Any]) -> dict[str, Any]:
    rows = list(db.scalars(select(models.SalesFact)).all())
    customer_code = variables.get("customer_code")
    customer_name = str(variables.get("customer_name") or "").lower()
    from_date = variables.get("from_date")
    to_date = variables.get("to_date") or date.today().isoformat()
    filtered = []
    for row in rows:
        if customer_code and row.customer_code != str(customer_code).upper():
            continue
        if customer_name and customer_name not in (row.customer_name or "").lower():
            continue
        if from_date and row.invoice_date < str(from_date):
            continue
        if to_date and row.invoice_date > str(to_date):
            continue
        filtered.append(row)
    by_month: dict[str, dict[str, float]] = {}
    by_year: dict[str, dict[str, float]] = {}
    warnings: list[str] = []
    for row in filtered:
        month = row.invoice_date[:7]
        year = row.invoice_date[:4]
        by_month.setdefault(month, {"sales": 0.0, "quantity": 0.0, "invoices": 0})
        by_year.setdefault(year, {"sales": 0.0, "quantity": 0.0, "invoices": 0})
        for bucket in (by_month[month], by_year[year]):
            bucket["sales"] += float(row.net_value or 0)
            bucket["quantity"] += float(row.quantity or 0)
            bucket["invoices"] += 1
        if (row.net_value or 0) < 0:
            warnings.append(f"Negative net value in invoice {row.invoice_no}")
        if not row.material_name:
            warnings.append(f"Missing material_name in invoice {row.invoice_no}")
    total_sales = sum(float(r.net_value or 0) for r in filtered)
    total_qty = sum(float(r.quantity or 0) for r in filtered)
    months = sorted(by_month.items())
    best = max(months, key=lambda item: item[1]["sales"], default=(None, None))
    worst = min(months, key=lambda item: item[1]["sales"], default=(None, None))
    return {
        "total_sales_value": round(total_sales, 2),
        "total_quantity": round(total_qty, 2),
        "invoice_count": len({r.invoice_no for r in filtered}),
        "first_invoice_date": min((r.invoice_date for r in filtered), default=None),
        "last_invoice_date": max((r.invoice_date for r in filtered), default=None),
        "month_wise_summary": [{"month": k, **v} for k, v in months],
        "year_wise_summary": [{"year": k, **v} for k, v in sorted(by_year.items())],
        "best_month": {"month": best[0], "summary": best[1]},
        "worst_month": {"month": worst[0], "summary": worst[1]},
        "validation_warnings": sorted(set(warnings)),
    }
