"""Aggregation logic for expense data using Pandas."""

import pandas as pd
from datetime import datetime


def aggregate_expenses(expenses: list[dict]) -> dict:
    """
    Aggregate expense data for AI analysis.
    Returns a structured dict with totals, by-category, and trends.
    """
    if not expenses:
        return {
            "total_spending": 0,
            "expense_count": 0,
            "period": {"start": None, "end": None},
            "by_category": {},
            "monthly_trend": [],
            "recent_expenses": [],
            "summary_text": "No expenses recorded.",
        }

    df = pd.DataFrame(expenses)
    df["date"] = pd.to_datetime(df["date"])
    df["amount"] = pd.to_numeric(df["amount"])

    total = df["amount"].sum()
    count = len(df)

    # By category
    by_cat = df.groupby("category")["amount"].sum().to_dict()
    by_cat = {k: round(v, 2) for k, v in by_cat.items()}

    # Period
    date_min = df["date"].min()
    date_max = df["date"].max()

    # Monthly trend
    monthly = df.groupby(df["date"].dt.to_period("M"))["amount"].sum()
    monthly_trend = [{"month": str(m), "total": round(v, 2)} for m, v in monthly.items()]

    # Recent (last 10) for context
    recent = df.nlargest(10, "date")
    recent_expenses = []
    for _, row in recent.iterrows():
        desc = row.get("description")
        desc = "" if (desc is None or (hasattr(desc, "__float__") and pd.isna(desc))) else str(desc)
        recent_expenses.append({
            "amount": float(row["amount"]),
            "category": str(row["category"]),
            "date": str(row["date"].date()),
            "description": desc,
        })

    # Top category
    top_category = max(by_cat, key=by_cat.get) if by_cat else None
    top_pct = round((by_cat[top_category] / total) * 100, 1) if top_category else 0

    # Build a human-readable summary for the LLM
    summary_lines = [
        f"Total spending: {total:.2f} across {count} expenses.",
        f"Date range: {date_min.date()} to {date_max.date()}.",
        f"Top category: {top_category} ({top_pct}% of total).",
        "",
        "Spending by category:",
    ]
    for cat, amt in sorted(by_cat.items(), key=lambda x: -x[1]):
        pct = round((amt / total) * 100, 1)
        summary_lines.append(f"  - {cat}: {amt:.2f} ({pct}%)")

    return {
        "total_spending": round(total, 2),
        "expense_count": count,
        "period": {
            "start": str(date_min.date()),
            "end": str(date_max.date()),
        },
        "by_category": by_cat,
        "monthly_trend": monthly_trend,
        "recent_expenses": recent_expenses,
        "summary_text": "\n".join(summary_lines),
    }
