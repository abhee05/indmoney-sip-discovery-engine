"""Runs app.py end to end against a fake Streamlit and synthetic NAVs, through every main path."""
import runpy
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

MVP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MVP))
sys.path.insert(0, str(MVP / "tests"))

import streamlit_stub as stub  # noqa: E402

sys.modules["streamlit"] = stub._module

from core import nav as navmod  # noqa: E402


def synthetic_series(seed=3, start="2013-01-01"):
    idx = pd.bdate_range(start, "2026-11-05")
    rng = np.random.default_rng(seed)
    return pd.Series(20 * np.exp(np.cumsum(rng.normal(0.0004, 0.013, len(idx)))), index=idx)


@pytest.fixture(autouse=True)
def fake_data(monkeypatch):
    series = synthetic_series()
    young = synthetic_series(start="2025-12-01")
    meta = {"scheme_name": "Test Midcap Fund - Direct Plan - Growth", "scheme_category": "Equity Scheme - Mid Cap Fund"}
    monkeypatch.setattr(navmod, "get_nav", lambda code: (meta, young if int(code) == 999 else series, "cached"))
    monkeypatch.setattr(navmod, "resolve_preset_code", lambda fund: 101)
    monkeypatch.setattr(navmod, "search", lambda q, limit=25: [{"schemeCode": 999, "schemeName": "Young Fund Direct Growth"},
                                                               {"schemeCode": 101, "schemeName": "Old Fund Direct Growth"}])
    stub.reset()
    stub.fresh_session()
    yield


def run():
    try:
        runpy.run_path(str(MVP / "app.py"), run_name="__main__")
    except stub.StopApp:
        pass
    return stub.CALLS


def names(calls):
    return [c[0] for c in calls]


def texts(calls, kind):
    return [str(c[1][0]) for c in calls if c[0] == kind and c[1]]


def test_landing_renders_portfolio():
    calls = run()
    assert "metric" in names(calls)
    assert any("Before you pause" == t for t in texts(calls, "title"))
    assert not [c for c in calls if c[0] == "error"]


def test_pause_flow_full_path():
    run()                                   # first run sets up the scenario
    stub.CLICK.add("Pause SIP")
    calls = run()
    subs = texts(calls, "subheader")
    assert "Before you pause" in subs
    md = " ".join(texts(calls, "markdown"))
    assert "You've invested" in md and "doesn't guarantee" in md
    # ask a question and pick an option, across reruns
    stub.CLICK.clear()
    stub.TEXT["Your question"] = "Which fund should I switch to?"
    stub.CLICK.add("Ask")
    calls = run()
    assert "can't tell you which funds" in " ".join(texts(calls, "markdown"))
    stub.CLICK.clear()
    stub.TEXT.clear()
    stub.CLICK.add("Skip next instalment")
    calls = run()
    assert any("Skip next instalment" in t for t in texts(calls, "success"))
    events = [r["event"] for r in stub._module.session_state["log"]]
    assert events[:2] == ["scenario", "tapped"] and "asked" in events and "decided" in events


def test_replay_past_dip():
    stub.CHOOSE["When"] = "Replay a real past dip"
    calls = run()
    caps = " ".join(texts(calls, "caption"))
    assert "replay of" in caps
    assert not [c for c in calls if c[0] == "error"]


def test_own_fund_with_little_history_shows_uncertainty():
    stub.CHOOSE["Start from"] = "Your own fund"
    stub.TEXT["Search for your fund by name"] = "young"
    stub.CHOOSE["Months since your first instalment"] = 6
    run()
    stub.CLICK.add("Stop SIP")
    calls = run()
    assert "Before you stop" in texts(calls, "subheader")
    warn = " ".join(texts(calls, "warning"))
    assert "isn't enough to say what's normal" in warn


def test_own_fund_without_query_stops_cleanly():
    stub.CHOOSE["Start from"] = "Your own fund"
    calls = run()
    assert "Invested" not in texts(calls, "metric")                            # no portfolio card
    assert any("Golden set results" == t for t in texts(calls, "subheader"))   # explainer tab still rendered
