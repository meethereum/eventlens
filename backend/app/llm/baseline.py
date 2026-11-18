"""
Plain LLM baseline — the stretch toggle for the "Compare with plain LLM" tab.

Calls the LLM once with no card context — just the user's query.
Uses BASELINE_LLM_* vars if set, otherwise the same LLM_* config.
"""
from __future__ import annotations

import logging

from app.llm.client import chat_completion, LLMError
from app.core.config import get_settings

logger = logging.getLogger("eventlens.llm.baseline")

BASELINE_SYSTEM_PROMPT = """You are a financial analyst. Answer the user's question about a company event concisely and factually. 
You have no access to real-time data or specific analysis cards.
Provide a 3-4 sentence response based on general financial knowledge.
Do not give specific buy/sell advice or price targets."""


def get_baseline_response(query: str) -> dict:
    """
    Call the LLM with no card context.
    Returns {response, model_used, is_fallback, error}.
    """
    cfg = get_settings()

    if not cfg.effective_baseline_api_key:
        return {
            "response": "LLM not configured. Set LLM_API_KEY in .env to enable this feature.",
            "model_used": "none",
            "is_fallback": True,
            "error": "LLM_API_KEY not set",
        }

    model = cfg.effective_baseline_model
    try:
        response = chat_completion(
            system_prompt=BASELINE_SYSTEM_PROMPT,
            user_prompt=query,
            is_baseline=True,
        )
        return {
            "response": response,
            "model_used": model,
            "is_fallback": False,
            "error": None,
        }
    except LLMError as e:
        return {
            "response": f"LLM unavailable: {str(e)[:100]}",
            "model_used": model,
            "is_fallback": True,
            "error": str(e),
        }
