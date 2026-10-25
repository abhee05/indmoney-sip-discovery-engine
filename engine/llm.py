"""Minimal Groq client (OpenAI-compatible) with rate-limit handling and model fallback.

Configure with environment variables or Streamlit secrets:
  GROQ_API_KEY   required for live AI
  GROQ_MODELS    optional comma-separated fallback list (first = preferred)
If a model hits its daily token limit, the next model in the list is used and
that is recorded on every output, so the Evidence Log can report it.
"""
import json
import os
import re
import time

import requests

from engine import config as C

URL = "https://api.groq.com/openai/v1/chat/completions"
FALLBACK = [C.DEFAULT_MODEL, "openai/gpt-oss-120b",
            "meta-llama/llama-4-scout-17b-16e-instruct", "openai/gpt-oss-20b",
            "llama-3.1-8b-instant"]


class LLMUnavailable(Exception):
    pass


def _secret(name):
    if os.environ.get(name):
        return os.environ[name]
    try:
        import streamlit as st
        return st.secrets.get(name, "")
    except Exception:  # noqa: BLE001
        return ""


class Groq:
    def __init__(self, key=None, models=None):
        self.key = key or _secret("GROQ_API_KEY")
        env_models = _secret("GROQ_MODELS") or _secret("GROQ_MODEL")
        self.models = models or ([m.strip() for m in env_models.split(",") if m.strip()] or FALLBACK)
        self.exhausted = set()
        self.calls, self.tokens, self.seconds = 0, 0, 0.0

    @property
    def available(self):
        return bool(self.key)

    def model(self):
        for m in self.models:
            if m not in self.exhausted:
                return m
        raise LLMUnavailable("All configured models have hit their daily limit. Re-run later to resume.")

    def chat_json(self, system, user, max_tokens=2500, temperature=0):
        if not self.key:
            raise LLMUnavailable("GROQ_API_KEY is not set.")
        last = "unknown error"
        for attempt in range(30):
            model = self.model()
            body = {"model": model, "temperature": temperature, "max_tokens": max_tokens,
                    "response_format": {"type": "json_object"},
                    "messages": [{"role": "system", "content": system},
                                 {"role": "user", "content": user}]}
            t0 = time.monotonic()
            try:
                r = requests.post(URL, json=body, timeout=90,
                                  headers={"Authorization": f"Bearer {self.key}"})
            except requests.RequestException as e:
                time.sleep(min(5 * (attempt + 1), 60))
                last = str(e)
                continue
            self.seconds += time.monotonic() - t0
            if r.status_code == 429:
                msg = r.text.lower()
                if "per day" in msg or "tpd" in msg or "rpd" in msg:
                    print(f"  ! {model} hit its daily limit; switching model")
                    self.exhausted.add(model)
                    continue
                wait = r.headers.get("retry-after")
                m = re.search(r"try again in ([\d.]+)s", msg)
                wait = float(wait) if wait else (float(m.group(1)) if m else 15)
                time.sleep(min(wait + 1, 90))
                continue
            if r.status_code == 404 or (r.status_code == 400 and "decommission" in r.text.lower()):
                print(f"  ! {model} not available on this account; skipping")
                self.exhausted.add(model)
                continue
            if r.status_code >= 400:
                last = f"HTTP {r.status_code}: {r.text[:200]}"
                time.sleep(min(3 * (attempt + 1), 60))
                continue
            data = r.json()
            self.calls += 1
            self.tokens += data.get("usage", {}).get("total_tokens", 0)
            content = data["choices"][0]["message"]["content"]
            try:
                return json.loads(content), model
            except json.JSONDecodeError:
                last = "model returned invalid JSON"
                continue
        raise LLMUnavailable(f"Groq request failed after retries: {last}")
