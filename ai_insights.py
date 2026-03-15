"""AI insights using Ollama with Llama 3.2 1B."""

import os
import requests
import json
import re

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
MODEL = "llama3.2:1b"
GENERATE_TIMEOUT = 600


def is_ollama_available() -> bool:
    """Check if Ollama is running and the model is available."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code != 200:
            return False
        models = r.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        return any(MODEL in name for name in model_names)
    except requests.exceptions.RequestException:
        return False


def generate_insights(aggregated: dict) -> str:
    """
    Send aggregated expense data to Ollama model and return insights.
    Falls back to a basic summary if Ollama is unavailable.
    """
    if not is_ollama_available():
        return _fallback_insights(aggregated)

    prompt = _build_prompt(aggregated)

    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {"temperature": 0.3},
            },
            timeout=GENERATE_TIMEOUT,
        )
        response.raise_for_status()
        result = response.json()
        text = result.get("response", "").strip()
        return text if text else _fallback_insights(aggregated)
    except requests.exceptions.RequestException as e:
        return f"Could not reach Ollama: {e}\n\n" + _fallback_insights(aggregated)


def _build_prompt(aggregated: dict) -> str:
    summary = aggregated.get("summary_text", "")
    recent = aggregated.get("recent_expenses", [])[:5]

    recent_text = "\n".join(
        f"- {e['date']}: {e['amount']} ({e['category']}) - {e.get('description', '')}"
        for e in recent
    )

    return f"""You are a personal finance advisor. Analyze the following expense data and provide a concise insights report.

## Expense Summary
{summary}

## Recent Expenses (sample)
{recent_text}

## Instructions
Write a short report (3-5 paragraphs) that includes:
1. **Patterns** - Identify spending patterns (e.g., high spending categories, timing trends)
2. **Suggestions** - 2-3 actionable suggestions to save money or budget better
3. **Highlights** - One positive observation if applicable

Keep the tone helpful and practical. Use clear sections with **bold** headers. Do not use markdown code blocks."""


def _fallback_insights(aggregated: dict) -> str:
    """Return a basic summary when Ollama is not available."""
    total = aggregated.get("total_spending", 0)
    count = aggregated.get("expense_count", 0)
    by_cat = aggregated.get("by_category", {})
    top = max(by_cat, key=by_cat.get) if by_cat else "N/A"
    pct = round((by_cat.get(top, 0) / total) * 100, 1) if total else 0

    return f"""## Basic Expense Summary

**Total:** {total:.2f} across {count} expenses.

**Top category:** {top} ({pct}% of spending).

**By category:**
{chr(10).join(f"- {k}: {v:.2f}" for k, v in sorted(by_cat.items(), key=lambda x: -x[1]))}

---
*To get AI-powered insights, run Ollama locally and pull a model:*
*`ollama pull llama3.2:1b`*
"""
