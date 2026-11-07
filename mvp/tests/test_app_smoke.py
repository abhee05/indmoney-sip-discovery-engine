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
    monkeypatch.setattr(navmod, "find_funds", lambda q, limit=50: [{"schemeCode": 999, "schemeName": "Young Fund Direct Growth"},
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
    assert "Your options" in md and "You've invested" not in md          # options visible before any reason
    stub.CLICK.clear()
    stub.CHOOSE["What's making you want to pause?"] = "loss"
    calls = run()
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
    stub.CHOOSE["When"] = "A past moment when it was in the red"
    calls = run()
    caps = " ".join(texts(calls, "caption"))
    assert "replay of" in caps
    assert not [c for c in calls if c[0] == "error"]


def test_own_fund_with_little_history_shows_uncertainty():
    stub.CHOOSE["Start from"] = "Your own fund"
    stub.TEXT["Search for your fund by name"] = "young"
    stub.CHOOSE["Months since your first instalment"] = 6
    stub.CHOOSE["When"] = "Today"
    run()
    stub.CLICK.add("Stop SIP")
    stub.CHOOSE["What's making you want to stop?"] = "volatility"
    calls = run()
    assert "Before you stop" in texts(calls, "subheader")
    shown = " ".join(texts(calls, "markdown") + texts(calls, "warning") + texts(calls, "caption"))
    assert "isn't enough to say what's normal" in shown


def test_own_fund_without_query_stops_cleanly():
    stub.CHOOSE["Start from"] = "Your own fund"
    calls = run()
    assert "Invested" not in texts(calls, "metric")                            # no portfolio card
    assert any("Golden set results" == t for t in texts(calls, "subheader"))   # explainer tab still rendered


@pytest.mark.parametrize("reason,expect", [
    ("cash", "skip"), ("restart", "Pausing until a month"), ("elsewhere", "can't suggest other funds"),
    ("goal", "doesn't sell anything"), ("failed", "can't see your bank"),
])
def test_each_reason_gets_its_own_explanation(reason, expect):
    run()
    stub.CLICK.add("Stop SIP")
    stub.CHOOSE["What's making you want to stop?"] = reason
    calls = run()
    md = " ".join(texts(calls, "markdown"))
    assert expect.lower() in md.lower()
    assert "Your options" in md


def test_lower_amount_option():
    run()
    stub.CLICK.add("Pause SIP")
    run()
    stub.CLICK.clear()
    stub.CHOOSE["New monthly amount (₹)"] = 2000
    stub.CLICK.add("Lower to ₹2,000 a month")
    calls = run()
    assert any("Lower to ₹2,000 a month" in t for t in texts(calls, "success"))


def _own_fund(monkeypatch, series, category="Equity Scheme - Mid Cap Fund", name="Some Fund Direct Growth"):
    monkeypatch.setattr(navmod, "get_nav", lambda code: ({"scheme_name": name, "scheme_category": category},
                                                         series, "live"))
    stub.CHOOSE["Start from"] = "Your own fund"
    stub.TEXT["Search for your fund by name"] = "some fund"


def test_closed_fund_is_explained_not_shown(monkeypatch):
    _own_fund(monkeypatch, synthetic_series(start="2012-01-01").loc[:"2019-05-10"])
    calls = run()
    assert any("stopped publishing prices" in t for t in texts(calls, "error"))
    assert "Invested" not in texts(calls, "metric")


def test_liquid_fund_is_explained_not_shown(monkeypatch):
    _own_fund(monkeypatch, synthetic_series(), category="Debt Scheme - Liquid Fund", name="HDFC Liquid Fund")
    calls = run()
    assert any("built for equity and hybrid" in t for t in texts(calls, "warning"))
    assert "Invested" not in texts(calls, "metric")


def test_no_red_moment_stops_with_explanation(monkeypatch):
    idx = pd.bdate_range("2013-01-01", "2026-11-05")
    _own_fund(monkeypatch, pd.Series(np.linspace(10, 40, len(idx)), index=idx))
    calls = run()
    assert any("no red moment" in t for t in texts(calls, "warning"))
    assert "Invested" not in texts(calls, "metric")


def test_history_without_losses_shows_sentence_not_na(monkeypatch):
    idx = pd.bdate_range("2013-01-01", "2026-11-05")
    _own_fund(monkeypatch, pd.Series(np.linspace(10, 40, len(idx)), index=idx))
    stub.CHOOSE["When"] = "Today"
    run()
    stub.CLICK.add("Ask a question")
    calls = run()
    md = " ".join(texts(calls, "markdown"))
    assert "None of the" in md
    assert not any(c[0] == "metric" and len(c[1]) > 1 and c[1][1] == "n/a" for c in calls)
