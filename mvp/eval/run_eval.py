"""Scores the MVP's answers against the hand-labelled golden set.

    python mvp/eval/run_eval.py            # uses the AI if GROQ_API_KEY is set, else template answers
    python mvp/eval/run_eval.py --no-ai    # template answers only

A case passes when: the intent is right, the behaviour is right (answer / decline / fallback), and every
quality check on the shown answer passes. Writes mvp/eval/report.json, which the app displays.
Scenarios use fixed synthetic price series so results are reproducible without internet.
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))

from core import facts as factsmod  # noqa: E402
from core import respond as resp  # noqa: E402
from core import sip  # noqa: E402
from core.llm import Groq  # noqa: E402

ANSWER_MODES = {"ai", "template"}
PIPELINE_CHECKS = {"AI available", "AI draft passed checks", "Safe fallback used"}


def synthetic(seed: int, start: str, end: str = "2026-11-05") -> pd.Series:
    idx = pd.bdate_range(start, end)
    rng = np.random.default_rng(seed)
    return pd.Series(25 * np.exp(np.cumsum(rng.normal(0.0004, 0.013, len(idx)))), index=idx)


def scenario_facts() -> dict:
    out = {}
    long = synthetic(7, "2012-01-02")
    as_of = long.index[-1]
    for want_down, name in ((True, "down"), (False, "up")):
        for months in range(3, 25):
            start = (as_of - pd.DateOffset(months=months - 1))
            res = sip.simulate(long, start.date().replace(day=1), 5000, as_of)
            if (res.gain < 0) == want_down:
                hist = sip.history_stats(long, res.instalments, res.as_of)
                out[name] = factsmod.build("Example Midcap Fund", "Mid Cap Fund", res, hist, "synthetic")
                break
        else:   # no month fits: replay a past dip instead
            when, first, _ = sip.find_dips(long, 7)[0]
            res = sip.simulate(long, first.date(), 5000, when - pd.Timedelta(days=1))
            hist = sip.history_stats(long, res.instalments, res.as_of)
            out[name] = factsmod.build("Example Midcap Fund", "Mid Cap Fund", res, hist, "synthetic")
    young = synthetic(11, "2026-01-01")
    res = sip.simulate(young, young.index[0].date().replace(day=1), 5000, young.index[-1])
    out["young"] = factsmod.build("Example New Fund", "Flexi Cap Fund", res,
                                  sip.history_stats(young, res.instalments, res.as_of), "synthetic")
    return out


def behaviour(mode: str) -> str:
    return "answer" if mode in ANSWER_MODES else mode


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--no-ai", action="store_true")
    args = ap.parse_args(argv)
    llm = None if args.no_ai else Groq()
    use_ai = bool(llm and llm.available)
    facts_by = scenario_facts()
    rows = list(csv.DictReader(open(HERE / "golden_set.csv", encoding="utf-8")))
    cases = []
    for r in rows:
        f = facts_by[r["scenario"]]
        a = resp.respond(r["question"], f, llm if use_ai else None)
        gate_checks = [c for c in a.checks if c["name"] not in PIPELINE_CHECKS]
        checks_clean = all(c["passed"] for c in gate_checks)
        got = behaviour(a.mode)
        ok_b = got == r["expected_behaviour"]
        ok_i = a.intent == r["expected_intent"]
        notes = []
        if not ok_i:
            notes.append(f"intent {a.intent}, expected {r['expected_intent']}")
        if not checks_clean:
            notes.append("failed: " + ", ".join(c["name"] for c in gate_checks if not c["passed"]))
        if any(c["name"] == "AI draft passed checks" and not c["passed"] for c in a.checks):
            notes.append("AI draft blocked, template shown")
        cases.append({
            "id": r["id"], "question": r["question"], "source": r["source"], "scenario": r["scenario"],
            "expected": r["expected_behaviour"], "got": got, "mode": a.mode, "intent": a.intent,
            "pass": bool(ok_b and ok_i and checks_clean), "note": "; ".join(notes),
            "must_not": r["must_not"], "answer": a.text, "label_status": r["label_status"],
        })
    labels = ("draft, not yet confirmed by hand"
              if any("draft" in c["label_status"].lower() for c in cases) else "labelled by hand")
    summary = {
        "total": len(cases),
        "passed": sum(c["pass"] for c in cases),
        "behaviour_correct": sum(c["expected"] == c["got"] for c in cases),
        "intent_correct": sum(c["note"].find("intent") == -1 for c in cases),
        "checks_clean": sum("failed:" not in c["note"] for c in cases),
        "ai_answers": sum(c["mode"] == "ai" for c in cases),
        "ai_blocked": sum("AI draft blocked" in c["note"] for c in cases),
        "by_expected": {b: {"total": sum(c["expected"] == b for c in cases),
                            "passed": sum(c["expected"] == b and c["pass"] for c in cases)}
                        for b in sorted({c["expected"] for c in cases})},
    }
    report = {
        "run_at": datetime.now().strftime("%d %b %Y %H:%M"),
        "mode": f"AI ({llm.last_model or llm.models[0]}) with template fallback" if use_ai else "template answers (AI off)",
        "labels": labels,
        "summary": summary,
        "cases": cases,
    }
    (HERE / "report.json").write_text(json.dumps(report, ensure_ascii=False, indent=1))
    print(f"{summary['passed']}/{summary['total']} passed · behaviour {summary['behaviour_correct']}/{summary['total']}"
          f" · checks clean {summary['checks_clean']}/{summary['total']} · AI answers {summary['ai_answers']}"
          f" · AI drafts blocked {summary['ai_blocked']} · labels: {labels}")
    for c in cases:
        if not c["pass"] or c["note"]:
            print(f"  {c['id']}: {'PASS' if c['pass'] else 'FAIL'} {c['note']}")
    return report


if __name__ == "__main__":
    main()
