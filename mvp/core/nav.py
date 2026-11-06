"""NAV history from mfapi.in (free public API of AMFI NAVs), with an on-disk cache.

Order of preference when loading a fund:
  1. live fetch from mfapi.in (so "today" is really today)
  2. cached JSON in mvp/data/navs/<scheme_code>.json (written by scripts/cache_navs.py)
If both fail, NavUnavailable is raised and the app shows a clear message.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pandas as pd
import requests

MFAPI = "https://api.mfapi.in/mf"
ROOT = Path(__file__).resolve().parent.parent
CACHE_DIR = ROOT / "data" / "navs"
PRESETS_FILE = ROOT / "data" / "presets.json"
TIMEOUT = 12


class NavUnavailable(Exception):
    pass


def parse(payload: dict) -> tuple[dict, pd.Series]:
    """mfapi payload -> (meta, NAV series indexed by date, oldest first)."""
    rows = payload.get("data") or []
    if not rows:
        raise NavUnavailable("No NAV data in the response.")
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%d-%m-%Y", errors="coerce")
    df["nav"] = pd.to_numeric(df["nav"], errors="coerce")
    df = df.dropna().query("nav > 0").drop_duplicates("date").sort_values("date")
    if df.empty:
        raise NavUnavailable("NAV data could not be read.")
    series = pd.Series(df["nav"].to_numpy(), index=pd.DatetimeIndex(df["date"]), name="nav")
    meta = dict(payload.get("meta") or {})
    return meta, series


def clean_category(raw: str) -> str:
    """'Equity Scheme - Mid Cap Fund' -> 'Mid Cap Fund'."""
    raw = (raw or "").strip()
    if " - " in raw:
        raw = raw.split(" - ", 1)[1]
    return raw or "Mutual fund"


def cache_path(code) -> Path:
    return CACHE_DIR / f"{int(code)}.json"


def fetch_live(code) -> dict:
    r = requests.get(f"{MFAPI}/{int(code)}", timeout=TIMEOUT)
    r.raise_for_status()
    payload = r.json()
    if not payload.get("data"):
        raise NavUnavailable(f"mfapi.in returned no data for scheme {code}.")
    return payload


def load_cached(code) -> dict | None:
    p = cache_path(code)
    if p.exists():
        return json.loads(p.read_text())
    return None


def get_nav(code) -> tuple[dict, pd.Series, str]:
    """Returns (meta, series, source) where source is 'live' or 'cached'."""
    try:
        payload = fetch_live(code)
        source = "live"
    except Exception:  # noqa: BLE001 - any network/API problem falls back to cache
        payload = load_cached(code)
        source = "cached"
        if payload is None:
            raise NavUnavailable(
                "Couldn't reach mfapi.in and there's no saved copy of this fund. Try again in a minute, "
                "or pick one of the scenarios.") from None
    meta, series = parse(payload)
    return meta, series, source


def search(query: str, limit: int = 25) -> list[dict]:
    query = (query or "").strip()
    if len(query) < 3:
        return []
    r = requests.get(f"{MFAPI}/search", params={"q": query}, timeout=TIMEOUT)
    r.raise_for_status()
    results = r.json() or []
    # Prefer direct-growth plans and drop payout variants, but keep anything if that empties the list.
    good = [x for x in results if not re.search(r"idcw|dividend|bonus|payout", x.get("schemeName", ""), re.I)]
    good.sort(key=lambda x: (not re.search(r"direct", x["schemeName"], re.I),
                             not re.search(r"growth", x["schemeName"], re.I), len(x["schemeName"])))
    return (good or results)[:limit]


def _norm(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip()


def best_match(query: str, candidates: list[dict]) -> dict | None:
    """Pick the scheme whose name contains every query word, preferring direct growth plans."""
    words = _norm(query).split()
    scored = []
    for c in candidates:
        name = _norm(c.get("schemeName", ""))
        squashed = name.replace(" ", "")
        hits = sum(1 for w in words if w in name or w in squashed)
        if hits < len(words):
            continue
        if re.search(r"idcw|dividend|bonus|payout|regular", name):
            continue
        scored.append((len(name), c))
    scored.sort(key=lambda t: t[0])
    return scored[0][1] if scored else None


def load_presets() -> dict:
    return json.loads(PRESETS_FILE.read_text())


def resolve_preset_code(fund: dict) -> int:
    """Use the saved scheme code; otherwise look it up by name on mfapi.in."""
    if fund.get("scheme_code"):
        return int(fund["scheme_code"])
    match = best_match(fund["query"], search(fund["query"], limit=200))
    if not match:
        raise NavUnavailable(f"Couldn't find '{fund['label']}' on mfapi.in.")
    return int(match["schemeCode"])
