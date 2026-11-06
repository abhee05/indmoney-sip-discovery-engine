import csv
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

MVP = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(MVP))

from core import facts, nav, respond, sip  # noqa: E402
from core.intent import classify  # noqa: E402

IDX = pd.bdate_range("2014-01-01", "2026-11-05")


def walk(seed=1):
    rng = np.random.default_rng(seed)
    return pd.Series(10 * np.exp(np.cumsum(rng.normal(0.0004, 0.012, len(IDX)))), index=IDX)


# ------------------------------------------------------------- SIP maths

def test_constant_nav_is_break_even():
    s = pd.Series(10.0, index=IDX)
    r = sip.simulate(s, date(2026, 1, 1), 2000, IDX[-1])
    assert r.invested == 2000 * r.instalments and abs(r.gain) < 1e-6
    h = sip.history_stats(s, 6, IDX[-1])
    assert h.pct_below == 0.0 and h.n_below == 0


def test_rising_nav_gains_and_units_bought_monthly():
    s = pd.Series(np.linspace(10, 20, len(IDX)), index=IDX)
    r = sip.simulate(s, date(2026, 5, 1), 1000, IDX[-1])
    assert r.instalments == 7 and r.gain > 0      # May..Nov (5 Nov has a NAV)
    assert sip.history_stats(s, 7, IDX[-1]).pct_below == 0.0


def test_unfinished_month_has_no_instalment():
    s = pd.Series(10.0, index=pd.bdate_range("2020-01-01", "2026-11-03"))   # data ends before the 5th
    r = sip.simulate(s, date(2026, 10, 1), 1000, s.index[-1])
    assert r.instalments == 1


def test_history_never_uses_future_prices():
    s = walk()
    cut = pd.Timestamp("2020-03-20")
    h_past = sip.history_stats(s, 6, cut)
    s_changed = s.copy()
    s_changed[s_changed.index > cut] *= 0.1          # crash the future
    assert sip.history_stats(s_changed, 6, cut) == h_past


def test_return_independent_of_amount():
    s = walk()
    a = sip.simulate(s, date(2025, 1, 1), 1000, IDX[-1])
    b = sip.simulate(s, date(2025, 1, 1), 7000, IDX[-1])
    assert round(a.gain_pct, 6) == round(b.gain_pct, 6)


def test_find_dips_are_real_losses():
    s = walk(2)
    dips = sip.find_dips(s, 7)
    assert dips, "expected at least one past dip"
    for when, start, ret in dips:
        r = sip.simulate(s, start.date(), 1000, when - pd.Timedelta(days=1))
        assert r.gain_pct < 0 and r.instalments == 7


def test_inr_grouping():
    assert facts.inr(123456789) == "₹12,34,56,789"
    assert facts.inr(950) == "₹950" and facts.inr(-1234) == "-₹1,234"


def test_parse_and_best_match():
    payload = {"meta": {"scheme_name": "X", "scheme_category": "Equity Scheme - Mid Cap Fund"},
               "data": [{"date": "05-11-2026", "nav": "12.5"}, {"date": "04-11-2026", "nav": "12.0"}]}
    meta, series = nav.parse(payload)
    assert list(series) == [12.0, 12.5] and nav.clean_category(meta["scheme_category"]) == "Mid Cap Fund"
    cands = [{"schemeCode": 1, "schemeName": "Motilal Oswal Midcap Fund - Regular Plan - Growth"},
             {"schemeCode": 2, "schemeName": "Motilal Oswal Midcap Fund - Direct Plan - IDCW"},
             {"schemeCode": 3, "schemeName": "Motilal Oswal Midcap Fund - Direct Plan - Growth"}]
    assert nav.best_match("motilal oswal midcap direct growth", cands)["schemeCode"] == 3


# ------------------------------------------------------------- responder

@pytest.fixture
def down_facts():
    s = walk(1)
    when, start, _ = sip.find_dips(s, 7)[0]
    r = sip.simulate(s, start.date(), 5000, when - pd.Timedelta(days=1))
    return facts.build("Example Fund", "Mid Cap Fund", r, sip.history_stats(s, r.instalments, r.as_of), "test")


def test_golden_intents_match_rules():
    rows = list(csv.DictReader(open(MVP / "eval" / "golden_set.csv", encoding="utf-8")))
    wrong = [(r["id"], classify(r["question"])[0], r["expected_intent"]) for r in rows
             if classify(r["question"])[0] != r["expected_intent"]]
    assert not wrong


class FakeLLM:
    available = True
    last_model = "fake"

    def __init__(self, replies):
        self.replies, self.calls = list(replies), 0

    def chat(self, system, user):
        self.calls += 1
        r = self.replies.pop(0)
        if isinstance(r, Exception):
            raise r
        return r


def test_good_ai_draft_is_shown(down_facts):
    f = down_facts
    draft = (f"That red number is hard to see. You've put in {f['invested']} and it's worth {f['current_value']} "
             f"({f['gain_pct']}). Of {f['history']['n_windows']} past SIPs this long, {f['history']['pct_below']}% "
             f"were below at this point. Past performance doesn't guarantee future returns. The choice is yours.")
    a = respond.respond("Is this normal?", f, FakeLLM([draft]))
    assert a.mode == "ai" and all(c["passed"] for c in a.checks)


def test_bad_ai_draft_is_blocked_then_template(down_facts):
    bad = "Don't worry, it will recover by 18% soon. You should stay invested."
    llm = FakeLLM([bad, bad])
    a = respond.respond("Should I stop my SIP?", down_facts, llm)
    assert llm.calls == 2 and a.mode == "template"
    blocked = [c for c in a.checks if c["name"] == "AI draft passed checks"]
    assert blocked and not blocked[0]["passed"]
    assert all(c["passed"] for c in a.checks if c["name"] not in ("AI draft passed checks",))


def test_ai_outage_falls_back(down_facts):
    a = respond.respond("Is this normal?", down_facts, FakeLLM([RuntimeError("timeout")]))
    assert a.mode == "template" and any(c["name"] == "Safe fallback used" for c in a.checks)


def test_declines_never_call_ai(down_facts):
    llm = FakeLLM([])
    for q in ["Which fund is best?", "When will it turn green?", "Should I switch to an FD instead?"]:
        a = respond.respond(q, down_facts, llm)
        assert a.mode.startswith("decline")
    assert llm.calls == 0


def test_gates_catch_each_rule(down_facts):
    f = down_facts
    cases = {
        "Numbers match the calculation": "Your SIP is down 37.9% today.",
        "No investment advice": "I recommend you keep going.",
        "No predictions or promises": "It will come back next year.",
        "No fear or urgency": "Act now before it's too late.",
        "History comes with its caveat": "In the past, 40% of SIPs were below at this point.",
    }
    for rule, text in cases.items():
        checks = {c["name"]: c["passed"] for c in respond.run_gates(text, f, "")}
        assert checks[rule] is False, rule
    ok = {c["name"]: c["passed"] for c in respond.run_gates("Past performance doesn't guarantee future returns.", f, "")}
    assert ok["No predictions or promises"]
