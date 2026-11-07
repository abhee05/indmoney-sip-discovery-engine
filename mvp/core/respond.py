"""Turns a question (or the 'Before you pause' opening) into a checked answer.

Pipeline: route intent (rules) -> decline / template / AI draft -> quality gates -> retry once -> template.
Every answer carries the list of checks it passed, so the app can show them.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field

from core.facts import allowed_numbers, extract_numbers
from core.intent import classify

SEBI_INVESTOR = "https://investor.sebi.gov.in/"
AMFI = "https://www.amfiindia.com/"
CAVEAT = "Past performance doesn't guarantee future returns."
MAX_WORDS = 150
AI_INTENTS = {"opening", "doubt", "stop", "cash"}


@dataclass
class Answer:
    text: str
    intent: str
    mode: str                     # ai | fixed | template (AI fallback) | decline_advice | decline_prediction | fallback
    checks: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    model: str | None = None
    rule: str = ""


# ---------------------------------------------------------------- history sentence

def history_sentence(f: dict) -> str | None:
    h = f["history"]
    if not h["sufficient"]:
        return None
    k, n = h["months"], h["n_windows"]
    if h["n_below"] == 0:
        return (f"None of the {n} past {k}-month SIPs in this fund were below what had been invested at this "
                f"point, so a dip like this is unusual for this fund.")
    s = (f"Of {n} past {k}-month SIPs in this fund, {h['pct_below']}% were below what had been invested "
         f"at this point.")
    if h["n_followed"] and h["pct_above_after_follow"] is not None:
        s += (f" Of those that kept going another {f['follow_months']} months, {h['pct_above_after_follow']}% "
              f"were back above what had been invested.")
    if h["max_months_to_recover"] is not None:
        s += f" The longest any took to get back above was {h['max_months_to_recover']} more months"
        s += (f", and {h['n_never_recovered']} still hadn't by the latest data." if h["n_never_recovered"] else ".")
    return s


def insufficient_sentence(f: dict) -> str:
    h = f["history"]
    return (f"This fund has only {h['years_of_data']} years of history, which isn't enough to say what's normal "
            f"for a SIP of this length, so I won't guess. The fund's official documents, listed on AMFI's "
            f"website, describe its risk level.")


def numbers_line(f: dict) -> str:
    return (f"You've invested {f['invested']} over {f['months_held']}, and it's worth {f['current_value']} "
            f"as of {f['as_of']} ({f['gain_pct']}).")


# ---------------------------------------------------------------- templates

def template_answer(intent: str, f: dict, question: str = "") -> tuple[str, str, list]:
    """Returns (text, mode, sources)."""
    hist = history_sentence(f)
    if intent == "advice":
        return ("I can't tell you which funds to pick, keep, add to or drop. That would be investment advice, "
                "and this tool only explains your own SIP. A SEBI-registered investment adviser can help with "
                "choosing funds, and every fund's official risk level (its riskometer) is on its factsheet. What I can "
                "do: show how past SIPs like yours behaved in this fund, and explain what continuing, skipping, "
                "pausing or stopping each mean.", "decline_advice", [SEBI_INVESTOR])
    if intent == "prediction":
        text = "Nobody can know when, or whether, your SIP gets back above what you've invested, so I won't guess."
        if hist:
            text += f" What I can show is what happened before: {hist} {CAVEAT}"
        else:
            text += " " + insufficient_sentence(f)
        return text, "decline_prediction", [AMFI] if not hist else []
    if intent == "failed":
        return ("I can't see your bank or mandate records, so I can't tell why that debit failed. Common reasons "
                "are a mandate limit lower than the instalment, a mandate that isn't fully set up, or a "
                "processing error at the bank. A failed instalment doesn't touch the units you already hold. "
                "Your app's support can check the exact reason, and your bank can confirm whether any charge "
                "was applied.", "fallback", [])
    if intent == "out_of_scope":
        return ("I can only help with your SIP here: what your numbers mean, how past SIPs like yours behaved, "
                "and what each option does. For anything else, your app's support or AMFI's investor pages "
                "are the right place.", "fallback", [AMFI])
    if intent == "xirr":
        if f["instalments"] < 12:
            text = (f"XIRR is a yearly return rate that accounts for when each instalment went in. With "
                    f"{f['months_held']} of instalments, a yearly rate isn't meaningful yet, which is why apps "
                    f"often leave it blank under a year. Your plain return so far is {f['gain_pct']} "
                    f"({f['gain']} on {f['invested']} invested).")
        else:
            text = (f"XIRR is a yearly return rate that accounts for when each instalment went in. Your plain "
                    f"return so far is {f['gain_pct']} ({f['gain']} on {f['invested']} invested).")
        return text, "template", []
    if intent == "options":
        text = ("Here's what each option does. Continue: the next instalment goes in as usual. Skip once: only "
                "the next instalment is skipped and the SIP carries on after. Pause: no instalments until the "
                f"restart month you pick. Lower the amount: future instalments are smaller. Stop: no more "
                f"instalments. In every case the {f['invested']} you've already invested stays invested and keeps "
                f"moving with the market until you choose to redeem it.")
        if re.search(r"real.?time|automatic|dynamic|based on (my )?(bank )?balance", question, re.I):
            text += " A debit that changes automatically with your bank balance isn't something I can set up."
        return text, "template", []
    if intent == "cash":
        return ("If money is tight right now, you have options that don't end the SIP: skip just the next "
                "instalment, pause until a month you choose, or lower the monthly amount. Stopping is an option "
                f"too. With any of them, the {f['invested']} you've already invested stays invested. Check how far "
                "ahead your app needs the change before the debit date, because a debit that fails for low "
                "balance can attract a bank charge.", "template", [])
    # opening, doubt, stop
    if not hist:
        lead = "Before you decide, here's where things stand. " if intent in ("stop", "opening") else ""
        return lead + numbers_line(f) + " " + insufficient_sentence(f), "fallback", [AMFI]
    safe_note = ""
    if re.search(r"\bsafe\b|fixed deposit|\bfd\b", question, re.I):
        safe_note = ("A mutual fund's value moves with the market, unlike a fixed deposit, so a SIP can sit below "
                     "what you invested for a while. ")
    if f["is_down"]:
        feel = ("Seeing your SIP below what you put in is unsettling, especially early on. "
                if intent in ("opening", "stop") else "")
        text = (feel + numbers_line(f) + " " + safe_note + hist + " " + CAVEAT +
                " Whether to continue, skip, pause or stop is your call; the options below explain each one.")
    else:
        text = (numbers_line(f) + " " + safe_note + "Dips are a normal part of SIPs. " + hist + " " + CAVEAT +
                " Whether to continue, skip, pause or stop is your call; the options below explain each one.")
    return text, "template", []


# ---------------------------------------------------------------- gates

ADVICE_OUT = [r"\byou should\b", r"\bi (would )?recommend\b", r"\bi suggest\b", r"\bbest (fund|option for you)\b",
              r"\bswitch to\b", r"\bconsider (investing|switching|buying|redeeming)\b", r"\bkeep (investing|going)\b(?! or)",
              r"\bdon'?t (stop|pause|sell)\b", r"\bdo not (stop|pause|sell)\b", r"\bstay invested\b"]
PREDICT_OUT = [r"\bwill (recover|bounce|come back|go up|rise|grow|be (back|above|positive|fine))\b",
               r"\b(is|are) (likely|certain|sure|bound) to\b", r"\bguarantee(d)?\b", r"\bdefinitely\b"]
URGENCY_OUT = [r"\bhurry\b", r"\bact now\b", r"\bdon'?t miss\b", r"\bmiss out\b", r"\bbefore it'?s too late\b",
               r"\blast chance\b", r"\byou'?ll regret\b", r"\blose everything\b"]
NEGATED_GUARANTEE = re.compile(r"\b(doesn'?t|does not|don'?t|do not|no|not|can'?t|cannot|never)\s+(a\s+)?guarantee(d|s)?\b", re.I)


def run_gates(text: str, f: dict, question: str) -> list[dict]:
    checks = []
    text = text.replace("’", "'").replace("‘", "'")   # curly apostrophes from models
    allowed = allowed_numbers(f) | set(extract_numbers(question))
    stray = sorted({n for n in extract_numbers(text) if n not in allowed})
    checks.append({"name": "Numbers match the calculation", "passed": not stray,
                   "detail": "every number comes from the code" if not stray else f"unexplained numbers: {stray}"})
    cleaned = NEGATED_GUARANTEE.sub("", text)
    hits = [p for p in ADVICE_OUT if re.search(p, cleaned, re.I)]
    checks.append({"name": "No investment advice", "passed": not hits,
                   "detail": "no recommendation found" if not hits else f"matched: {hits}"})
    hits = [p for p in PREDICT_OUT if re.search(p, cleaned, re.I)]
    checks.append({"name": "No predictions or promises", "passed": not hits,
                   "detail": "no forecast found" if not hits else f"matched: {hits}"})
    hits = [p for p in URGENCY_OUT if re.search(p, cleaned, re.I)]
    checks.append({"name": "No fear or urgency", "passed": not hits,
                   "detail": "no pressure language" if not hits else f"matched: {hits}"})
    sentences = re.split(r"(?<=[.!?])\s+", text)
    mentions_past = any(re.search(r"\bpast\b|\bhistor|\bbefore\b", s, re.I) and "%" in s for s in sentences)
    has_caveat = bool(re.search(r"(doesn'?t|does not|no) guarantee", text, re.I))
    checks.append({"name": "History comes with its caveat", "passed": (not mentions_past) or has_caveat,
                   "detail": "caveat present" if has_caveat else ("no history quoted" if not mentions_past
                                                                   else "history quoted without the caveat")})
    words = len(text.split())
    checks.append({"name": "Short enough to read", "passed": words <= MAX_WORDS, "detail": f"{words} words"})
    return checks


def passed(checks: list[dict]) -> bool:
    return all(c["passed"] for c in checks)


# ---------------------------------------------------------------- AI drafting

SYSTEM = """You explain a first-time investor's own SIP to them at a moment of doubt, inside an investing app.
Follow every rule:
1. Use ONLY the facts given. Copy every number exactly as written in the facts (for example "₹38,290", "-4.3%", "32.2%"). Never calculate, round or invent a number, and don't write dates other than those in the facts.
2. Never recommend an action: no "you should", never tell them to continue, stop, pause, buy, sell, switch or stay invested, and name no fund other than theirs.
3. Never predict or promise: never say the fund will recover, rise or come back, and never guess when.
4. No fear, urgency or pressure, and no false comfort.
5. If you mention past SIPs or history, include this exact sentence: "Past performance doesn't guarantee future returns."
6. Plain, warm English. At most 90 words. No headings, lists or emojis.
Shape: one short sentence acknowledging how they feel, their numbers, the most relevant history fact, then say the choice is theirs and the options below explain each one."""

CASH_EXTRA = ("\nThis person is short of money. Say neutrally that skipping one instalment, pausing until a month "
              "they choose, or lowering the amount keeps the SIP going, and that stopping is also an option. "
              "Don't favour any one.")


def llm_facts(f: dict) -> dict:
    h = f["history"]
    out = {k: f[k] for k in ("fund_name", "category", "monthly_amount", "months_held", "invested",
                             "current_value", "gain", "gain_pct", "as_of")}
    out["is_below_invested"] = f["is_down"]
    if h["sufficient"]:
        out["history"] = {
            "past_sips_of_same_length": h["n_windows"], "length_in_months": h["months"],
            "percent_below_invested_at_this_point": f"{h['pct_below']}%",
            "median_return_at_this_point": f"{h['median_pct']}%",
            "worst_return_at_this_point": f"{h['worst_pct']}%",
        }
        if h["n_followed"] and h["pct_above_after_follow"] is not None:
            out["history"][f"of_those_below_percent_above_after_{f['follow_months']}_more_months"] = \
                f"{h['pct_above_after_follow']}%"
        if h["max_months_to_recover"] is not None:
            out["history"]["longest_extra_months_to_get_back_above"] = h["max_months_to_recover"]
    else:
        out["history"] = "not enough history to say what's normal"
    return out


def respond(question: str, facts: dict, llm=None, intent: str | None = None) -> Answer:
    """intent='opening' produces the first message of the Before-you-pause screen."""
    if intent is None:
        intent, rule = classify(question)
    else:
        rule = "flow"
    if intent == "empty":
        return Answer("Type a question about your SIP, for example \"Is this loss normal?\"", intent, "fallback")

    text, mode, sources = template_answer(intent, facts, question)
    use_ai = (llm is not None and getattr(llm, "available", False) and intent in AI_INTENTS
              and mode == "template")
    if use_ai:
        cue = "" if intent == "opening" else f"\nTheir question: {question}"
        user = f"Facts:\n{json.dumps(llm_facts(facts), ensure_ascii=False, indent=1)}{cue}"
        system = SYSTEM + (CASH_EXTRA if intent == "cash" else "")
        feedback = ""
        for _attempt in range(2):
            try:
                draft = llm.chat(system, user + feedback)
            except Exception as e:  # noqa: BLE001
                checks = [{"name": "AI available", "passed": False, "detail": str(e)[:160]},
                          {"name": "Safe fallback used", "passed": True, "detail": "template answer shown"}]
                return Answer(text, intent, "template", checks + run_gates(text, facts, question), sources,
                              rule=rule)
            checks = run_gates(draft, facts, question)
            if passed(checks):
                return Answer(draft, intent, "ai", checks, sources, model=getattr(llm, "last_model", None),
                              rule=rule)
            failed = [f"{c['name']}: {c['detail']}" for c in checks if not c["passed"]]
            feedback = "\n\nYour previous draft broke these rules, fix them:\n- " + "\n- ".join(failed)
        checks = [{"name": "AI draft passed checks", "passed": False,
                   "detail": "blocked after one retry: " + "; ".join(failed)[:200]},
                  {"name": "Safe fallback used", "passed": True, "detail": "template answer shown instead"}]
        return Answer(text, intent, "template", checks + run_gates(text, facts, question), sources, rule=rule)

    if mode == "template" and intent not in AI_INTENTS:
        mode = "fixed"            # written answer by design (options, XIRR), not an AI fallback
    return Answer(text, intent, mode, run_gates(text, facts, question), sources, rule=rule)


# ---------------------------------------------------------------- "what's making you want to pause?"
# Reasons adapted from the reasons INDmoney asks for after a stop. Here they are asked before the decision.
REASONS = {
    "loss": ("My SIP is showing a loss, or returns are lower than I expected", "doubt"),
    "volatility": ("I'm not comfortable with the ups and downs", "doubt"),
    "cash": ("Money is tight right now", "cash"),
    "restart": ("I'll restart after a few months", "restart"),
    "elsewhere": ("I want to invest elsewhere or change funds", "elsewhere"),
    "goal": ("I've reached my goal or need the money", "goal"),
    "failed": ("An instalment failed, or a bank or mandate issue", "failed"),
    "other": ("Something else, or I'd rather not say", "doubt"),
}
HISTORY_FIRST = {"loss", "volatility", "other"}


def reason_answer(key: str, facts: dict, llm=None) -> Answer:
    """The explanation shown after the user says why they want to pause or stop."""
    label, intent = REASONS[key]
    f = facts
    fixed = {
        "restart": (f"Pausing until a month you pick does exactly that: no instalments until then, and the SIP "
                    f"restarts on its own. Stopping instead means setting up a new SIP later. Either way, the "
                    f"{f['invested']} you've already invested stays invested."),
        "elsewhere": (f"That's your decision, and stopping is quick. I can't suggest other funds, as that would be "
                      f"investment advice; a SEBI-registered adviser can help with that. Stopping this SIP doesn't "
                      f"sell the {f['invested']} already invested; that stays in this fund until you redeem it."),
        "goal": (f"Stopping the SIP only ends future instalments. It doesn't sell anything: the {f['current_value']} "
                 f"this SIP is worth stays invested until you redeem it separately. If you need the money, "
                 f"redeeming is a separate step in your app."),
    }
    if intent in fixed:
        text = fixed[intent]
        return Answer(text, intent, "fixed", run_gates(text, f, label),
                      [SEBI_INVESTOR] if intent == "elsewhere" else [], rule="reason")
    if intent == "doubt" and key != "other":
        return respond(label, f, llm, intent="doubt")
    if key == "other":
        return respond("", f, llm, intent="opening")
    return respond(label, f, llm, intent=intent)
