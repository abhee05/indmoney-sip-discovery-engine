"""SIP maths, all in code (the AI never computes a number).

Conventions
- An instalment is bought once a month at the first NAV on or after the 5th (else the month's last NAV).
- "Your SIP": every instalment from the start month up to the as-of date, valued at the last NAV on or
  before the as-of date.
- "Past SIPs of the same length" (base rates): for every possible start month in the fund's history,
  k instalments, valued one month after the last instalment (just before the next one would be due).
  Only data on or before the as-of date is used, so a replayed past dip never peeks at the future.
- The return of a SIP with a constant instalment does not depend on the amount, so base rates hold for
  any instalment size.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

import numpy as np
import pandas as pd

BUY_DAY = 5
FOLLOW_MONTHS = 12          # "if the SIP had continued another 12 months"
MIN_WINDOWS = 24            # fewer past SIPs than this = not enough history to say what's normal
TOL = 0.05                  # returns within ±0.05% count as break-even (floating-point noise)


def monthly_points(nav: pd.Series, as_of: pd.Timestamp | None = None) -> pd.Series:
    """One NAV per calendar month: the first on/after BUY_DAY, else the month's last."""
    s = nav if as_of is None else nav[nav.index <= as_of]
    if s.empty:
        return s
    picks = []
    groups = list(s.groupby([s.index.year, s.index.month]))
    for n, (_, grp) in enumerate(groups):
        after = grp[grp.index.day >= BUY_DAY]
        if not after.empty:
            picks.append(after.index[0])
        elif n < len(groups) - 1 or as_of is None:
            picks.append(grp.index[-1])     # month with no NAV after the buy day (rare): use its last NAV
        # else: the current, unfinished month hasn't reached its buy day yet, so no instalment
    return s.loc[picks]


def nav_on_or_before(nav: pd.Series, when: pd.Timestamp) -> tuple[pd.Timestamp, float]:
    s = nav[nav.index <= when]
    if s.empty:
        raise ValueError("No NAV on or before that date.")
    return s.index[-1], float(s.iloc[-1])


@dataclass
class SipResult:
    instalments: int
    amount: float
    invested: float
    value: float
    gain: float
    gain_pct: float
    first_date: pd.Timestamp
    as_of: pd.Timestamp
    path: pd.DataFrame = field(repr=False)   # date, invested, value


def simulate(nav: pd.Series, start_month: date, amount: float, as_of: pd.Timestamp) -> SipResult:
    """The user's own SIP: monthly instalments from start_month until as_of."""
    as_of_date, as_of_nav = nav_on_or_before(nav, as_of)
    mp = monthly_points(nav, as_of_date)
    start = pd.Timestamp(start_month.year, start_month.month, 1)
    mp = mp[mp.index >= start]
    if mp.empty:
        raise ValueError("No instalment would have been made by that date. Pick an earlier start month.")
    units = np.cumsum(amount / mp.to_numpy())
    invested = amount * np.arange(1, len(mp) + 1)
    path = pd.DataFrame({"date": mp.index, "invested": invested, "value": units * mp.to_numpy()})
    if as_of_date > mp.index[-1]:
        path.loc[len(path)] = [as_of_date, invested[-1], units[-1] * as_of_nav]
    value = float(units[-1] * as_of_nav)
    inv = float(invested[-1])
    return SipResult(
        instalments=len(mp), amount=float(amount), invested=inv, value=value, gain=value - inv,
        gain_pct=(value / inv - 1) * 100, first_date=mp.index[0], as_of=as_of_date, path=path)


def _window_returns(prices: np.ndarray, k: int) -> list[np.ndarray]:
    """For each start i: returns (in %) after j instalments valued at point i+j, for j = k..end."""
    inv_units = 1.0 / prices                       # units bought per 1 rupee
    csum = np.concatenate([[0.0], np.cumsum(inv_units)])
    n = len(prices)
    out = []
    for i in range(0, n - k):
        js = np.arange(k, n - i)                   # j instalments, valued at index i+j (< n)
        units = csum[i + js] - csum[i]
        value = units * prices[i + js]
        out.append((value / js - 1.0) * 100.0)
    return out


@dataclass
class HistoryStats:
    months: int
    n_windows: int
    sufficient: bool
    years_of_data: float
    pct_below: float | None = None
    median_pct: float | None = None
    worst_pct: float | None = None
    best_pct: float | None = None
    n_below: int = 0
    n_followed: int = 0
    pct_above_after_follow: float | None = None
    n_recovered: int = 0
    max_months_to_recover: int | None = None
    n_never_recovered: int = 0
    outcomes: list = field(default_factory=list, repr=False)   # every past window's return at k, in %


def history_stats(nav: pd.Series, k: int, as_of: pd.Timestamp) -> HistoryStats:
    """How past SIPs of the same length (k instalments) in this fund turned out."""
    mp = monthly_points(nav, as_of)
    prices = mp.to_numpy(dtype=float)
    first = nav.index[0]
    years = round((pd.Timestamp(as_of) - first).days / 365.25, 1)
    if k < 1 or len(prices) <= k:
        return HistoryStats(months=k, n_windows=0, sufficient=False, years_of_data=years)
    windows = _window_returns(prices, k)
    at_k = np.array([w[0] for w in windows])
    stats = HistoryStats(months=k, n_windows=len(at_k), sufficient=len(at_k) >= MIN_WINDOWS,
                         years_of_data=years, outcomes=[round(float(x), 2) for x in at_k])
    stats.pct_below = round(float((at_k < -TOL).mean() * 100), 1)
    stats.median_pct = round(float(np.median(at_k)), 1)
    stats.worst_pct = round(float(at_k.min()), 1)
    stats.best_pct = round(float(at_k.max()), 1)
    below = [w for w in windows if w[0] < -TOL]
    stats.n_below = len(below)
    followed = [w for w in below if len(w) > FOLLOW_MONTHS]
    stats.n_followed = len(followed)
    if followed:
        stats.pct_above_after_follow = round(
            float(np.mean([w[FOLLOW_MONTHS] >= -TOL for w in followed]) * 100), 1)
    recover_months = []
    for w in below:
        hit = np.nonzero(w >= -TOL)[0]
        if hit.size:
            recover_months.append(int(hit[0]))     # extra months after k until back at or above invested
        else:
            stats.n_never_recovered += 1
    stats.n_recovered = len(recover_months)
    stats.max_months_to_recover = max(recover_months) if recover_months else None
    return stats


def find_dips(nav: pd.Series, k: int, min_drop_pct: float = -3.0, limit: int = 6) -> list[tuple]:
    """Past moments when a k-instalment SIP was at least min_drop_pct below invested.

    Returns [(as_of_timestamp, start_timestamp, return_pct)], the deepest moment per calendar year,
    newest first. Used for "Replay a real past dip".
    """
    mp = monthly_points(nav)
    prices = mp.to_numpy(dtype=float)
    if len(prices) <= k:
        return []
    inv_units = np.concatenate([[0.0], np.cumsum(1.0 / prices)])
    best_per_year: dict[int, tuple] = {}
    for i in range(0, len(prices) - k):
        units = inv_units[i + k] - inv_units[i]
        ret = (units * prices[i + k] / k - 1.0) * 100.0
        if ret <= min_drop_pct:
            when, start = mp.index[i + k], mp.index[i]
            cur = best_per_year.get(when.year)
            if cur is None or ret < cur[2]:
                best_per_year[when.year] = (when, start, round(float(ret), 1))
    dips = sorted(best_per_year.values(), key=lambda t: t[0], reverse=True)
    return dips[:limit]
