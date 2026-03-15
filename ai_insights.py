"""AI insights using Ollama (local) or Groq (cloud) LLM."""

import os
import requests
import json
import re

OLLAMA_URL = os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434")
OLLAMA_MODEL = "llama3.2:1b"
GENERATE_TIMEOUT = 600
GROQ_MODEL = "llama-3.1-8b-instant"


def _get_groq_api_key() -> str | None:
    """Get Groq API key from Streamlit secrets or environment."""
    key = os.environ.get("GROQ_API_KEY")
    if key:
        return key
    try:
        import streamlit as st
        if "GROQ_API_KEY" in st.secrets:
            return st.secrets["GROQ_API_KEY"]
    except Exception:
        pass
    return None


def is_ollama_available() -> bool:
    """Check if Ollama is running and the model is available."""
    try:
        r = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        if r.status_code != 200:
            return False
        models = r.json().get("models", [])
        model_names = [m.get("name", "") for m in models]
        return any(OLLAMA_MODEL in name for name in model_names)
    except requests.exceptions.RequestException:
        return False


def is_cloud_ai_available() -> bool:
    """Check if Groq API key is configured for cloud deployment."""
    return _get_groq_api_key() is not None


def _get_ai_status() -> str:
    """Return human-readable AI backend status."""
    if is_ollama_available():
        return "🟢 Ollama (local)"
    if is_cloud_ai_available():
        return "🟢 Groq (cloud)"
    return "🔴 Not configured"


def generate_insights(aggregated: dict) -> str:
    """
    Generate insights using Ollama (local) or Groq (cloud).
    Falls back to a basic summary if neither is available.
    """
    prompt = _build_prompt(aggregated)

    # Prefer Ollama when running locally
    if is_ollama_available():
        return _generate_via_ollama(prompt, aggregated)

    # Use Groq when deployed to cloud
    if is_cloud_ai_available():
        return _generate_via_groq(prompt, aggregated)

    return _fallback_insights(aggregated)


def _generate_via_ollama(prompt: str, aggregated: dict) -> str:
    """Generate via local Ollama."""
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": OLLAMA_MODEL,
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


def _generate_via_groq(prompt: str, aggregated: dict) -> str:
    """Generate via Groq cloud API."""
    api_key = _get_groq_api_key()
    if not api_key:
        return _fallback_insights(aggregated)

    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,
        )
        text = completion.choices[0].message.content.strip()
        return text if text else _fallback_insights(aggregated)
    except Exception as e:
        return f"Groq API error: {e}\n\n" + _fallback_insights(aggregated)


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
    """Return a basic summary when no AI is available."""
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
*To get AI-powered insights:*
- **Local:** Run Ollama and pull a model: `ollama pull llama3.2:1b`
- **Cloud:** Add GROQ_API_KEY to Streamlit secrets (free at [console.groq.com](https://console.groq.com))
"""
