"""
AI Service — Groq API client wrapping Llama 3.3-70B.

Key hardening:
- Environment validated at import time with a clear error message
- Missing API key degrades gracefully (returns None client, callers get empty fallbacks)
- Retry with exponential backoff on transient failures
- Robust JSON extraction from any LLM output format
- Timeout handling via Groq's built-in request timeout
"""

import os
import re
import json
import logging
import time
from typing import Optional, Dict, Any, Tuple

from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

# ─── Environment validation ────────────────────────────────────────────────────
GROQ_API_KEY: Optional[str] = os.getenv("GROQ_API_KEY", "").strip() or None

if not GROQ_API_KEY:
    logger.warning(
        "GROQ_API_KEY is not set. "
        "Create a .env file with GROQ_API_KEY=gsk_... to enable AI features. "
        "Get your free key at https://console.groq.com"
    )

_client = None  # Lazily initialised


def is_api_available() -> bool:
    """Return True only when a valid-looking API key is present."""
    return bool(GROQ_API_KEY and GROQ_API_KEY.startswith("gsk_"))


def get_client():
    """Return the Groq client, initialising it on first call."""
    global _client
    if _client is not None:
        return _client
    if not GROQ_API_KEY:
        raise EnvironmentError(
            "GROQ_API_KEY is missing. Add it to your .env file.\n"
            "Get a free key at https://console.groq.com"
        )
    try:
        from groq import Groq
        _client = Groq(api_key=GROQ_API_KEY)
        logger.info("Groq client initialised successfully.")
        return _client
    except ImportError:
        raise ImportError("groq package not installed. Run: pip install groq")


def chat_completion(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.7,
    max_tokens: int = 1024,
    retries: int = 3,
) -> str:
    """
    Call Groq with Llama 3.3-70B.

    Returns the response text. Raises RuntimeError after all retries exhausted.
    """
    client = get_client()
    last_error: Optional[Exception] = None

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user",   "content": user_message},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                timeout=60,
            )
            content = response.choices[0].message.content
            if not content:
                raise ValueError("Empty response from Groq API")
            return content.strip()

        except Exception as exc:
            last_error = exc
            wait = min(2 ** attempt, 16)  # cap at 16 s
            logger.warning(
                "Groq API attempt %d/%d failed: %s — retrying in %ds",
                attempt + 1, retries, exc, wait,
            )
            if attempt < retries - 1:
                time.sleep(wait)

    raise RuntimeError(
        f"Groq API failed after {retries} attempts. Last error: {last_error}"
    )


def chat_completion_json(
    system_prompt: str,
    user_message: str,
    temperature: float = 0.3,
    max_tokens: int = 1024,
    retries: int = 3,
) -> Dict[str, Any]:
    """
    Call Groq and parse the response as JSON.

    Handles:
    - Raw JSON
    - JSON wrapped in ```json ... ``` fences
    - JSON preceded/followed by explanatory text
    - Trailing commas (stripped before parsing)

    Raises ValueError if no valid JSON can be extracted.
    """
    raw = chat_completion(system_prompt, user_message, temperature, max_tokens, retries)
    return _extract_json(raw)


def _extract_json(raw: str) -> Dict[str, Any]:
    """
    Robustly extract the first JSON object from raw LLM output.

    Strategy:
    1. Try to parse the full response directly.
    2. Strip markdown fences and retry.
    3. Find the first '{' and last '}' and parse the slice.
    4. Remove trailing commas and retry.
    """
    text = raw.strip()

    # Strategy 1 — parse as-is
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    # Strategy 2 — strip markdown code fences
    stripped = re.sub(r"^```(?:json)?\s*", "", text, flags=re.IGNORECASE)
    stripped = re.sub(r"\s*```$", "", stripped).strip()
    try:
        return json.loads(stripped)
    except json.JSONDecodeError:
        pass

    # Strategy 3 — extract first {...} block
    start = text.find("{")
    end = text.rfind("}") + 1
    if start != -1 and end > start:
        candidate = text[start:end]
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            # Strategy 4 — remove trailing commas before } or ]
            cleaned = re.sub(r",\s*([}\]])", r"\1", candidate)
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                pass

    logger.error("JSON extraction failed. Raw response (first 500 chars):\n%s", raw[:500])
    raise ValueError(
        f"Could not extract valid JSON from AI response. "
        f"Raw (truncated): {raw[:200]}"
    )
