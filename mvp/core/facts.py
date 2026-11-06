"""One facts object per screen: the only source of numbers for templates and for the AI."""
from __future__ import annotations

from dataclasses import asdict

from core.sip import FOLLOW_MONTHS, HistoryStats, SipResult


def inr(x: float) -> str:
    """Indian grouping, no decimals: 123456 -> '₹1,23,456'."""
    neg = x < 0
    n = str(int(round(abs(x))))
    if len(n) > 3:
        head, tail = n[:-3], n[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        n = ",".join(groups + [tail])
    return ("-₹" if neg else "₹") + n


def pct(x: float, signed: bool = True) -> str:
    v = round(x, 1)
    if v == 0:
        v = 0.0
    return (f"{v:+.1f}%" if signed else f"{abs(v):.1f}%")


def months_word(n: int) -> str:
    return f"{n} month" if n == 1 else f"{n} months"


def build(fund_name: str, category: str, sip: SipResult, hist: HistoryStats, source: str) -> dict:
    h = asdict(hist)
    h.pop("outcomes", None)
    return {
        "fund_name": fund_name,
        "category": category,
        "monthly_amount": inr(sip.amount),
        "instalments": sip.instalments,
        "months_held": months_word(sip.instalments),
        "invested": inr(sip.invested),
        "current_value": inr(sip.value),
        "gain": inr(sip.gain),
        "gain_pct": pct(sip.gain_pct),
        "is_down": sip.gain < 0,
        "first_instalment": sip.first_date.strftime("%b %Y"),
        "as_of": sip.as_of.strftime("%d %b %Y"),
        "data_source": source,
        "follow_months": FOLLOW_MONTHS,
        "history": h,
    }


def allowed_numbers(facts: dict) -> set[float]:
    """Every number a response may contain, in the forms it may appear."""
    nums: set[float] = set()

    def add(v):
        if isinstance(v, bool) or v is None:
            return
        if isinstance(v, (int, float)):
            for x in (v, round(v), round(v, 1)):
                nums.add(abs(float(x)))

    def walk(obj):
        if isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, (list, tuple)):
            for v in obj:
                walk(v)
        elif isinstance(obj, str):
            for tok in extract_numbers(obj):
                nums.add(tok)
        else:
            add(obj)

    walk(facts)
    return nums


def extract_numbers(text: str) -> list[float]:
    import re
    out = []
    for m in re.finditer(r"(?<![\w.])[-−+]?\d[\d,]*(?:\.\d+)?", text or ""):
        raw = m.group(0).replace(",", "").replace("−", "-").replace("+", "")
        try:
            out.append(abs(float(raw)))
        except ValueError:
            continue
    return out
