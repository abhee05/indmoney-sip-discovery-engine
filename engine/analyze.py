"""Stage 4: turn per-record AI labels into comparable, quantified opportunity areas.

All counting is done in code over every coded record (never over an LLM summary
or a retrieved top-k), so numbers are reproducible from classified.jsonl.
"""
import json
from collections import Counter, defaultdict

from engine import codebook as CB
from engine import config as C
from engine.prefilter import load_corpus

# How directly a product team at INDmoney could act on each need, without
# recommending funds or using fear/FOMO (PM judgement, 0-1; editable in the app).
CONTROLLABILITY = {
    "know_if_on_track": 0.9, "understand_volatility": 0.9, "flexible_control": 1.0,
    "reliable_payments": 1.0, "neutral_help_when_unsure": 0.8, "goal_link": 0.9,
    "trust_support": 0.7, "clear_costs": 0.6,
}
CONTINUING = {"ongoing", "restarted", "first_months"}
FIRST_YEAR = {"first_time_explicit", "early"}


def load_coded():
    from engine.classify import load_done
    corpus = {r["id"]: r for r in load_corpus()}
    rows = []
    for cid, lab in load_done().items():
        if cid in corpus:
            rows.append({**corpus[cid], **lab})
    return rows


def _vals(r, field):
    v = r.get(field)
    return v if isinstance(v, list) else [v]


def _num(v):
    """Scores arrive as ints, or strings like '1.2K' from YouTube."""
    if isinstance(v, (int, float)):
        return v
    try:
        v = str(v).strip().upper()
        mult = 1000 if v.endswith("K") else 1_000_000 if v.endswith("M") else 1
        return float(v.rstrip("KM")) * mult
    except (ValueError, AttributeError):
        return 0


def _quotes(rows, n=4):
    """A few illustrative, source-diverse quotes (one per thread)."""
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: -_num(r.get("score"))):
        if r["thread_id"] in seen or not r.get("quote"):
            continue
        seen.add(r["thread_id"])
        out.append({"id": r["id"], "source": r["source"], "quote": r["quote"][:220], "url": r["url"]})
        if len(out) >= n:
            break
    return out


def distribution(rows, field, drop_unknown=True):
    cnt, threads, by_val = Counter(), defaultdict(set), defaultdict(list)
    for r in rows:
        for v in _vals(r, field):
            if drop_unknown and v in CB.UNKNOWNISH:
                continue
            cnt[v] += 1
            threads[v].add(r["thread_id"])
            by_val[v].append(r)
    total = len(rows)
    return [{"value": v, "label": CB.label(field, v), "n": n, "threads": len(threads[v]),
             "share": round(n / total, 3) if total else 0, "quotes": _quotes(by_val[v])}
            for v, n in cnt.most_common()]


def compare_groups(rows, fields, a_name="at_risk", b_name="continuing"):
    """What separates people near a lapse from people who continue."""
    a = [r for r in rows if int(r["continuation_risk"]) >= 2]
    b = [r for r in rows if r["journey_stage"] in CONTINUING and int(r["continuation_risk"]) <= 1]
    out = []
    for f in fields:
        for v in CB.FIELDS[f]["values"]:
            if v in CB.UNKNOWNISH:
                continue
            na = sum(v in _vals(r, f) for r in a)
            nb = sum(v in _vals(r, f) for r in b)
            if na + nb < 5:
                continue
            sa, sb = na / len(a) if a else 0, nb / len(b) if b else 0
            out.append({"field": f, "value": v, "label": CB.label(f, v),
                        f"{a_name}_n": na, f"{a_name}_share": round(sa, 3),
                        f"{b_name}_n": nb, f"{b_name}_share": round(sb, 3),
                        "difference_pts": round((sa - sb) * 100, 1),
                        "low_sample": na + nb < 15})
    out.sort(key=lambda x: -abs(x["difference_pts"]))
    return {"group_sizes": {a_name: len(a), b_name: len(b)}, "rows": out}


def segments(rows):
    res = {}
    for f in CB.SEGMENT_FIELDS:
        groups = defaultdict(list)
        for r in rows:
            if r[f] not in CB.UNKNOWNISH:
                groups[r[f]].append(r)
        res[f] = []
        for v, g in sorted(groups.items(), key=lambda kv: -len(kv[1])):
            trig = Counter(r["drop_trigger"] for r in g if r["drop_trigger"] != "none")
            need = Counter(r["unmet_need"] for r in g if r["unmet_need"] != "none")
            res[f].append({
                "value": v, "label": CB.label(f, v), "n": len(g),
                "at_risk_share": round(sum(int(r["continuation_risk"]) >= 2 for r in g) / len(g), 3),
                "top_triggers": [{"value": k, "label": CB.label("drop_trigger", k), "n": n} for k, n in trig.most_common(3)],
                "top_needs": [{"value": k, "label": CB.label("unmet_need", k), "n": n} for k, n in need.most_common(3)],
                "low_sample": len(g) < 15})
    return res


def opportunities(rows, controllability=None, w_reach=1.0, w_risk=1.0, w_first=0.5):
    ctl = {**CONTROLLABILITY, **(controllability or {})}
    total = len(rows)
    groups = defaultdict(list)
    for r in rows:
        if r["unmet_need"] != "none":
            groups[r["unmet_need"]].append(r)
    if not groups:
        return []
    max_n = max(len(g) for g in groups.values())
    out = []
    for need, g in groups.items():
        n = len(g)
        at_risk = sum(int(r["continuation_risk"]) >= 2 for r in g) / n
        first = sum(r["investor_experience"] in FIRST_YEAR for r in g) / n
        reach = n / max_n
        score = (reach ** w_reach) * ((0.25 + at_risk) ** w_risk) * ((0.5 + first) ** w_first) * ctl.get(need, 0.5)
        trig = Counter(r["drop_trigger"] for r in g if r["drop_trigger"] != "none")
        pain = Counter(p for r in g for p in r["in_app_pain"] if p != "none")
        out.append({
            "need": need, "label": CB.label("unmet_need", need), "n": n,
            "threads": len({r["thread_id"] for r in g}),
            "sources": dict(Counter(r["source"] for r in g)),
            "share_of_relevant": round(n / total, 3),
            "at_risk_share": round(at_risk, 3), "first_year_share": round(first, 3),
            "indmoney_share": round(sum(r["product"] == "indmoney" for r in g) / n, 3),
            "controllability": ctl.get(need, 0.5), "score": round(score, 3),
            "linked_triggers": [{"label": CB.label("drop_trigger", k), "n": c} for k, c in trig.most_common(3)],
            "linked_pains": [{"label": CB.label("in_app_pain", k), "n": c} for k, c in pain.most_common(3)],
            "need_phrases": [r["need_text"] for r in g if r.get("need_text")][:8],
            "quotes": _quotes(g, 5)})
    top = max(o["score"] for o in out) or 1
    for o in out:
        o["score_index"] = round(100 * o["score"] / top)
    return sorted(out, key=lambda o: -o["score"])


QUESTION_FIELDS = [
    ("Why do people start a SIP, and what do they expect?", ["start_motivation", "expectation"]),
    ("What changes in the months after starting?", ["journey_stage"]),
    ("What leads investors to pause, reduce or stop?", ["drop_trigger"]),
    ("What do investors check, and how often?", ["check_frequency", "what_checked"]),
    ("What confuses or worries them inside the app?", ["in_app_pain"]),
    ("What do they do outside the app when unsure?", ["outside_app"]),
    ("What keeps continuers going?", ["continuation_driver"]),
    ("What unmet needs emerge consistently?", ["unmet_need"]),
]
COMPARE_FIELDS = ["start_motivation", "expectation", "check_frequency", "what_checked",
                  "in_app_pain", "outside_app", "influencer", "income_stability",
                  "investor_experience", "continuation_driver"]


def run():
    coded = load_coded()
    valid = [r for r in coded if r.get("status") != "rejected"]
    relevant = [r for r in valid if r["relevance"] == "core"]
    first_year = [r for r in relevant if r["investor_experience"] in FIRST_YEAR]
    coverage = {
        "coded": len(coded), "rejected_by_gates": len(coded) - len(valid),
        "relevance": dict(Counter(r["relevance"] for r in valid)),
        "core_by_source": dict(Counter(r["source"] for r in relevant)),
        "core_by_product": dict(Counter(r["product"] for r in relevant)),
        "core_threads": len({r["thread_id"] for r in relevant}),
        "first_year_core": len(first_year),
        "models": dict(Counter(r.get("model") for r in coded)),
        "status": dict(Counter(r.get("status") for r in coded)),
    }
    funnel_path = C.PROCESSED / "funnel.json"
    result = {
        "coverage": coverage,
        "funnel": json.loads(funnel_path.read_text()) if funnel_path.exists() else {},
        "questions": [{"question": q, "fields": {f: distribution(relevant, f) for f in fs}}
                      for q, fs in QUESTION_FIELDS],
        "trigger_x_stage": {
            t: dict(Counter(r["journey_stage"] for r in relevant if r["drop_trigger"] == t))
            for t in CB.FIELDS["drop_trigger"]["values"] if t != "none"},
        "continuers_vs_at_risk": compare_groups(relevant, COMPARE_FIELDS),
        "segments": segments(relevant),
        "opportunities": opportunities(relevant),
        "opportunities_first_year": opportunities(first_year),
    }
    (C.PROCESSED / "analysis.json").write_text(json.dumps(result, indent=1, ensure_ascii=False))
    print(f"analyze: {len(relevant)} core records ({len(first_year)} first-year), "
          f"{len(result['opportunities'])} opportunity areas -> analysis.json")
    return result
