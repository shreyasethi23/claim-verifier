"""Shared Groq client: one place for API keys, model routing, retries and JSON mode."""
import json
import os
import random
import time

from groq import Groq

try:
    import streamlit as st
    GROQ_API_KEY = st.secrets["GROQ_API_KEY"]
except Exception:
    from dotenv import load_dotenv
    load_dotenv()
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# Model routing: a small fast model for simple steps, a stronger one for reasoning + tool use.
# Both are self-serve on Groq and support tool calling + JSON mode. Override in .env if needed.
FAST_MODEL = os.getenv("FAST_MODEL", "openai/gpt-oss-20b")
SMART_MODEL = os.getenv("SMART_MODEL", "openai/gpt-oss-120b")

_client = None


def get_client():
    global _client
    if _client is None:
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


def _is_retryable(error) -> bool:
    """Retry rate limits (429), timeouts and server errors (5xx). Don't retry permanent errors
    like 400/401/404 (bad request, bad key, unknown model): retrying can't fix them."""
    status = getattr(error, "status_code", None)
    return status is None or status == 429 or status >= 500


def chat(messages, model=FAST_MODEL, tools=None, json_mode=False,
         temperature=0.0, max_tokens=2048, retries=3):
    """Call the LLM with exponential backoff + jitter on transient errors (rate limits, timeouts).

    temperature=0 by default: fact-checking needs consistent, repeatable outputs.
    """
    kwargs = dict(model=model, messages=messages, temperature=temperature, max_tokens=max_tokens)
    if tools:
        kwargs["tools"] = tools
        kwargs["tool_choice"] = "auto"
    if json_mode:
        kwargs["response_format"] = {"type": "json_object"}

    last_error = None
    for attempt in range(retries):
        try:
            return get_client().chat.completions.create(**kwargs).choices[0].message
        except Exception as e:
            last_error = e
            if not _is_retryable(e) or attempt == retries - 1:
                break
            time.sleep((2 ** attempt) + random.random())   # exponential backoff + jitter
    raise RuntimeError(f"LLM call failed ({model}): {last_error}")


def chat_json(messages, model=FAST_MODEL, **kw) -> dict:
    """Chat in JSON mode and parse the result; raises ValueError if it isn't valid JSON."""
    msg = chat(messages, model=model, json_mode=True, **kw)
    try:
        return json.loads(msg.content or "")
    except json.JSONDecodeError as e:
        raise ValueError(f"Model did not return valid JSON: {e}") from e
