import logging

import requests

from app.core.config import MODEL_NAME, OLLAMA_URL

logger = logging.getLogger(__name__)


def _extract_text(payload: dict) -> str:
    if isinstance(payload.get("response"), str):
        return payload["response"].strip()

    message = payload.get("message")
    if isinstance(message, dict) and isinstance(message.get("content"), str):
        return message["content"].strip()

    if isinstance(payload.get("content"), str):
        return payload["content"].strip()

    if isinstance(payload.get("error"), str):
        return f"LLM Error: {payload['error']}"

    return ""


def generate(prompt: str) -> str:
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.1,
                    "num_predict": 512,
                },
            },
            timeout=90,
        )

        if not response.ok:
            logger.error("Ollama returned status=%s body=%s", response.status_code, response.text)
            return f"LLM Error: HTTP {response.status_code}"

        payload = response.json()
        text = _extract_text(payload)
        if text:
            return text

        logger.error("Ollama payload missing response text: %s", payload)
        return "LLM Error: Empty response from Ollama"

    except Exception as exc:
        logger.exception("LLM generate call failed")
        return f"LLM Error: {exc}"