"""
EventLens LLM client — one module that talks to any OpenAI-compatible
/chat/completions endpoint. No provider-specific branches anywhere else.

Features:
  - Client-side RPM throttle from LLM_RPM_LIMIT
  - Retry with backoff on 429
  - Optional fallback model on daily-limit 429
  - LLM_EXTRA_BODY JSON merged into every request
  - JSON extraction: strip ```blocks, reasoning text, extract first balanced JSON
  - Startup model check via GET /models
  - Token counting for LLM_MAX_INPUT_TOKENS compliance
"""
from __future__ import annotations

import json
import logging
import re
import time
from datetime import date
from typing import Any

import httpx
from pydantic import BaseModel, ValidationError

from app.core.config import get_settings

logger = logging.getLogger("eventlens.llm")


# ---------------------------------------------------------------------------
# RPM throttle
# ---------------------------------------------------------------------------

_last_call_times: list[float] = []


def _throttle():
    """Block until enough time has passed to stay under LLM_RPM_LIMIT."""
    cfg = get_settings()
    rpm = cfg.llm_rpm_limit
    if rpm <= 0:
        return
    min_interval = 60.0 / rpm
    now = time.time()
    # Prune old timestamps (older than 60s)
    global _last_call_times
    _last_call_times = [t for t in _last_call_times if now - t < 60.0]
    if _last_call_times:
        elapsed = now - _last_call_times[-1]
        if elapsed < min_interval:
            sleep_time = min_interval - elapsed
            logger.debug("RPM throttle: sleeping %.2fs", sleep_time)
            time.sleep(sleep_time)
    _last_call_times.append(time.time())


# ---------------------------------------------------------------------------
# Token estimation (rough — 4 chars ≈ 1 token)
# ---------------------------------------------------------------------------

def estimate_tokens(text: str) -> int:
    return len(text) // 4


def truncate_to_tokens(text: str, max_tokens: int) -> str:
    """Truncate text to approximately max_tokens."""
    max_chars = max_tokens * 4
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[...truncated...]"


# ---------------------------------------------------------------------------
# JSON extraction
# ---------------------------------------------------------------------------

def extract_json(text: str) -> str | None:
    """
    Extract the first balanced JSON object from text.
    Strips ```json blocks, reasoning text, and any preamble.
    Returns the raw JSON string or None if no valid JSON found.
    """
    if not text:
        return None

    # Strip ```json ... ``` blocks
    code_block = re.search(r'```(?:json)?\s*(.*?)\s*```', text, re.DOTALL)
    if code_block:
        text = code_block.group(1)

    # Strip  reasoning blocks (some reasoning models emit these)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)

    # Find the first { and try to extract a balanced object
    start = text.find('{')
    if start == -1:
        return None

    depth = 0
    in_string = False
    escape = False
    for i in range(start, len(text)):
        ch = text[i]
        if escape:
            escape = False
            continue
        if ch == '\\' and in_string:
            escape = True
            continue
        if ch == '"' and not escape:
            in_string = not in_string
            continue
        if in_string:
            continue
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                return text[start:i + 1]

    return None


# ---------------------------------------------------------------------------
# Chat completion call
# ---------------------------------------------------------------------------

class LLMError(Exception):
    pass


class LLMRateLimitError(LLMError):
    pass


def chat_completion(
    system_prompt: str,
    user_prompt: str,
    model: str | None = None,
    max_tokens_override: int | None = None,
) -> str:
    """
    Call the /chat/completions endpoint and return the assistant's text.

    - Throttles to LLM_RPM_LIMIT
    - Retries with backoff on 429
    - Falls back to LLM_FALLBACK_MODEL on daily-limit 429
    - Merges LLM_EXTRA_BODY into the request
    - Raises LLMError if all retries fail
    """
    cfg = get_settings()

    base_url = cfg.llm_base_url
    api_key = cfg.llm_api_key
    use_model = model or cfg.llm_model

    if not api_key:
        raise LLMError("LLM_API_KEY not set")

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    body: dict[str, Any] = {
        "model": use_model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": cfg.llm_temperature,
        "max_tokens": max_tokens_override or cfg.llm_max_tokens,
    }

    # Merge extra body
    extra = cfg.llm_extra_body_dict
    if extra:
        body.update(extra)

    # Truncate input if needed
    max_input = cfg.llm_max_input_tokens
    sys_tokens = estimate_tokens(system_prompt)
    user_tokens = estimate_tokens(user_prompt)
    if sys_tokens + user_tokens > max_input:
        allowed = max_input - sys_tokens - 100
        if allowed > 0:
            user_prompt = truncate_to_tokens(user_prompt, allowed)
            body["messages"][1]["content"] = user_prompt
            logger.warning("Input truncated to %d tokens", max_input)

    max_retries = 2
    models_to_try = [use_model]
    if cfg.llm_fallback_model:
        models_to_try.append(cfg.llm_fallback_model)

    last_error = None
    used_fallback = False

    for model_name in models_to_try:
        body["model"] = model_name
        for attempt in range(max_retries):
            _throttle()
            try:
                logger.info("LLM call: model=%s attempt=%d", model_name, attempt + 1)
                with httpx.Client(timeout=cfg.llm_timeout_s) as client:
                    resp = client.post(url, json=body, headers=headers)

                if resp.status_code == 429:
                    last_error = LLMRateLimitError(f"429 rate limit (model={model_name})")
                    wait = 2 ** (attempt + 1)
                    logger.warning("LLM 429, backing off %ds", wait)
                    time.sleep(wait)
                    continue

                if resp.status_code != 200:
                    last_error = LLMError(f"HTTP {resp.status_code}: {resp.text[:200]}")
                    logger.warning("LLM error %d: %s", resp.status_code, resp.text[:200])
                    # Try fallback model on non-429 errors too
                    break

                data = resp.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                if not content:
                    last_error = LLMError("Empty response from LLM")
                    continue

                if model_name != use_model:
                    used_fallback = True

                return content

            except httpx.TimeoutException:
                last_error = LLMError(f"Timeout after {cfg.llm_timeout_s}s")
                logger.warning("LLM timeout")
                time.sleep(2)
                continue
            except Exception as exc:
                last_error = LLMError(str(exc))
                logger.warning("LLM exception: %s", exc)
                continue

    raise last_error or LLMError("Unknown LLM error")


# ---------------------------------------------------------------------------
# JSON completion (with extraction + validation + retry)
# ---------------------------------------------------------------------------

def json_completion(
    system_prompt: str,
    user_prompt: str,
    output_model: type[BaseModel],
    model: str | None = None,
    max_tokens_override: int | None = None,
    max_attempts: int = 2,
) -> tuple[BaseModel | None, str | None, bool]:
    """
    Call LLM, extract JSON, validate with pydantic, retry once on failure.
    Returns (parsed_model, raw_response, used_fallback).
    On failure returns (None, raw_response_or_error, used_fallback).
    """
    used_fallback = False
    for attempt in range(max(1, max_attempts)):
        try:
            raw = chat_completion(
                system_prompt,
                user_prompt,
                model,
                max_tokens_override=max_tokens_override,
            )
            json_str = extract_json(raw)
            if not json_str:
                logger.warning("No JSON found in LLM response (attempt %d)", attempt + 1)
                if attempt + 1 < max(1, max_attempts):
                    continue
                return None, raw, used_fallback

            parsed = output_model.model_validate_json(json_str)
            return parsed, raw, used_fallback

        except ValidationError as e:
            logger.warning("LLM JSON validation failed (attempt %d): %s", attempt + 1, str(e)[:200])
            if attempt + 1 < max(1, max_attempts):
                continue
            return None, str(e), used_fallback
        except LLMError as e:
            logger.warning("LLM call failed (attempt %d): %s", attempt + 1, str(e))
            if attempt + 1 < max(1, max_attempts):
                continue
            return None, str(e), used_fallback
        except Exception as e:
            logger.warning("Unexpected error (attempt %d): %s", attempt + 1, str(e))
            if attempt + 1 < max(1, max_attempts):
                continue
            return None, str(e), used_fallback

    return None, "All retries exhausted", used_fallback


# ---------------------------------------------------------------------------
# Startup model check
# ---------------------------------------------------------------------------

_model_available: bool | None = None
_model_check_done = False


def check_model_availability() -> bool | None:
    """
    Call GET {LLM_BASE_URL}/models once.
    Returns True if LLM_MODEL is in the list, False if not, None if check skipped.
    """
    global _model_available, _model_check_done

    if _model_check_done:
        return _model_available

    _model_check_done = True
    cfg = get_settings()

    if not cfg.llm_api_key:
        _model_available = None
        return None

    try:
        url = f"{cfg.llm_base_url.rstrip('/')}/models"
        headers = {"Authorization": f"Bearer {cfg.llm_api_key}"}
        with httpx.Client(timeout=10) as client:
            resp = client.get(url, headers=headers)

        if resp.status_code != 200:
            logger.info("Model check: /models returned %d, skipping", resp.status_code)
            _model_available = None
            return None

        models = resp.json().get("data", [])
        model_ids = [m.get("id", "") for m in models]
        available = cfg.llm_model in model_ids

        if not available:
            logger.warning("Model check: %s not in available models: %s",
                          cfg.llm_model, model_ids[:10])

        _model_available = available
        return available

    except Exception as e:
        logger.info("Model check: endpoint not supported (%s), skipping", str(e)[:80])
        _model_available = None
        return None


def get_model_availability() -> bool | None:
    """Return cached model availability from check_model_availability()."""
    return _model_available
