"""Minimal Groq client (OpenAI-compatible). Returns None-safe errors so the app can fall back.

Key: GROQ_API_KEY in the environment or in Streamlit secrets.
Models: GROQ_MODELS (comma-separated, first preferred) or the defaults below.
"""
from __future__ import annotations

import os
import time

import requests

URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_MODELS = ["openai/gpt-oss-120b", "llama-3.3-70b-versatile", "openai/gpt-oss-20b"]


class LLMError(Exception):
    pass


def _secret(name: str) -> str:
    if os.environ.get(name):
        return os.environ[name]
    try:
        import streamlit as st
        return str(st.secrets.get(name, "") or "")
    except Exception:  # noqa: BLE001
        return ""


class Groq:
    def __init__(self, key: str | None = None, models: list[str] | None = None, timeout: int = 25):
        self.key = key if key is not None else _secret("GROQ_API_KEY")
        env_models = _secret("GROQ_MODELS")
        self.models = models or [m.strip() for m in env_models.split(",") if m.strip()] or DEFAULT_MODELS
        self.timeout = timeout
        self.last_model = None
        self.last_seconds = 0.0

    @property
    def available(self) -> bool:
        return bool(self.key)

    def chat(self, system: str, user: str) -> str:
        if not self.available:
            raise LLMError("No GROQ_API_KEY configured.")
        errors = []
        for model in self.models:
            body = {"model": model, "temperature": 0.2, "max_tokens": 900,
                    "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
            t0 = time.monotonic()
            try:
                r = requests.post(URL, json=body, timeout=self.timeout,
                                  headers={"Authorization": f"Bearer {self.key}"})
            except requests.RequestException as e:
                errors.append(f"{model}: {e.__class__.__name__}")
                continue
            self.last_seconds = time.monotonic() - t0
            if r.status_code in (404, 413, 429, 500, 502, 503):
                errors.append(f"{model}: HTTP {r.status_code}")
                continue
            if r.status_code != 200:
                raise LLMError(f"{model}: HTTP {r.status_code} {r.text[:200]}")
            text = (r.json()["choices"][0]["message"].get("content") or "").strip()
            if not text:
                errors.append(f"{model}: empty reply")
                continue
            self.last_model = model
            return text
        raise LLMError("; ".join(errors) or "No model answered.")
