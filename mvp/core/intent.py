"""Rule-based intent routing. Deterministic on purpose: the advice and prediction declines must not
depend on a model's mood. Order matters: the first matching intent wins."""
from __future__ import annotations

import re

RULES: list[tuple[str, list[str]]] = [
    ("advice", [
        r"\bwhich\b.*\b(fund|scheme|mf)s?\b", r"\bbest\b.*\b(fund|scheme|mf)\b", r"\b(fund|scheme)\b.*\bbest\b",
        r"\brecommend", r"\bsuggest\b.*\b(fund|scheme)", r"\bgood fund\b", r"\bbad fund\b",
        r"\b(switch|move|shift)\b.*\b(fund|fd|fixed deposit|gold|stocks?|scheme|another|other)\b",
        r"\b(fixed deposit|fd)\b.*\binstead\b", r"\binstead\b.*\b(fd|fixed deposit|gold|stocks?)\b",
        r"\bshould i (buy|sell|redeem|withdraw|invest in|put)\b", r"\b(put|add|invest|buy) more\b",
        r"\btop[- ]?up\b", r"\bincrease (my )?(sip|amount|instal)", r"\bwaste of money\b",
        r"\b(kill|drop|dump)\b.*\bfund", r"\bredeem\b", r"\bwithdraw\b", r"\bbuy the dip\b", r"\bkaunsa fund\b",
        r"\b(good|bad|right|wrong|safe)\b.*\b(choice|pick|fund|sip|option|investment)\b",
        r"\b(is|was|am)\b.{0,25}\b(choice|pick|fund|sip|investment)\b.{0,15}\b(good|bad|right|wrong)\b\W*$",
        r"\b(choice|pick|fund|sip)\b.*\b(good or bad|bad or good)\b", r"\bsafe (mf|mutual fund|fund)s?\b",
    ]),
    ("prediction", [
        r"\bwhen\b.*\b(will|would)\b", r"\bwill (it|my|the|this)\b.*\b(recover|come back|go up|go down|rise|fall|turn green|bounce|grow|be)\b",
        r"\bprobabilit", r"\bchances?\b", r"\bpredict", r"\bforecast", r"\brecover(y)? by\b",
        r"\bnext (month|quarter|year|week)\b", r"\bin 20\d\d\b", r"\bturn green\b", r"\bhow much (money )?will\b",
        r"\bfuture value\b", r"\bguarantee", r"\bkab\b.*\b(recover|wapas|green)", r"\bwill the market\b",
    ]),
    ("failed", [
        r"\bfail", r"\bmandate\b", r"\bnot (deducted|debited)\b", r"\bdeducted twice\b", r"\berror code\b",
    ]),
    ("cash", [
        r"\bafford\b", r"\b(money|cash|budget) (is |was )?(tight|short|low)\b", r"\btight (month|budget)\b",
        r"\bbroke\b", r"\b(lost|lose|losing) (my )?job\b", r"\bjob loss\b", r"\bcan'?t pay\b", r"\bcannot pay\b",
        r"\bunable to pay\b", r"\bsalary (delay|late|cut|is late)", r"\b(rent|emi|loan|bills?|expenses?)\b",
        r"\bpenalt", r"\bbounce", r"\bbank charg", r"\blow balance\b", r"\bno money\b", r"\bpaise nahi\b",
    ]),
    ("options", [
        r"\bwhat happens\b.*\b(pause|stop|skip|cancel)", r"\b(pause|skip|stop|cancel)\b.*\b(option|button)s?\b",
        r"\bhow (do|can) i (pause|skip|stop|cancel|reduce|change|lower)\b", r"\bwhat are my options\b",
        r"\b(change|reduce|lower|customi[sz]e|adjust)\b.*\b(amount|debit|date|instal)", r"\bskip\b",
        r"\bpause\b.*\b(mean|work|happen)",
    ]),
    ("xirr", [r"\bxirr\b", r"\bcagr\b", r"\bannuali[sz]ed\b"]),
    ("stop", [r"\b(stop|pause|cancel|quit|close|end|exit)\b", r"\bband kar", r"\bnikal", r"\bchhod"]),
    ("doubt", [
        r"\bnormal\b", r"\bloss", r"\bdown\b", r"\bred\b", r"\bnegative\b", r"\bminus\b", r"\bfall", r"\bfell\b",
        r"\bdrop", r"\blower than\b", r"\bnot (growing|increasing|going up)\b", r"\bsafe\b", r"\bworried\b",
        r"\bscared\b", r"\banxious\b", r"\bwrong\b", r"\bmistake\b", r"\bunderperform", r"\breturns?\b",
        r"\bperform", r"\bghata\b", r"\bnuksaan\b",
    ]),
]

COMPILED = [(name, [re.compile(p, re.I) for p in pats]) for name, pats in RULES]


def classify(text: str) -> tuple[str, str]:
    """Returns (intent, the rule that matched). Intent is 'empty' or 'out_of_scope' if nothing fits."""
    t = (text or "").strip()
    if not t:
        return "empty", ""
    for name, pats in COMPILED:
        for p in pats:
            if p.search(t):
                return name, p.pattern
    return "out_of_scope", ""
