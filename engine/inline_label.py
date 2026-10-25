"""Labelling by Claude in-session (no API): same codebook, same quality gates.

  python -m engine.inline_label sample           build the stratified sample (golden ids first)
  python -m engine.inline_label show 0 40        print records 0-39 of the sample, compactly
  python -m engine.inline_label ingest FILE      parse compact labels, run gates, append to classified.jsonl

Compact label line:  <id> k=v k=v ... q="exact quote" nt="need text"
Unspecified fields default to unknown / none / 0, product to general.
"""
import hashlib
import json
import re
import shlex
import sys
from collections import Counter
from datetime import datetime, timezone

from engine import codebook as CB
from engine import config as C
from engine.classify import OUT, load_done, validate
from engine.prefilter import load_corpus

MODEL = "claude-opus-5-5 (in-session)"
SAMPLE = C.PROCESSED / "label_sample.json"
QUOTAS = {"reddit": 260, "tradingqna": 80, "youtube": 60, "play_store": 90, "app_store": 30}

ABBR = {
    "rel": ("relevance", {"c": "core", "a": "adjacent", "x": "not_relevant"}),
    "prod": ("product", {"ind": "indmoney", "oth": "other_platform", "gen": "general"}),
    "exp": ("investor_experience", {"ft": "first_time_explicit", "early": "early", "expd": "experienced"}),
    "stage": ("journey_stage", {"cs": "considering_start", "onb": "onboarding", "fm": "first_months",
                                "on": "ongoing", "cst": "considering_stop", "rp": "reduced_or_paused",
                                "st": "stopped", "rs": "restarted"}),
    "mot": ("start_motivation", {"lt": "long_term_wealth", "goal": "specific_goal", "tax": "tax_saving",
                                 "sug": "someone_suggested", "hab": "discipline_habit", "trend": "trend"}),
    "expect": ("expectation", {"quick": "quick_visible_gains", "steady": "steady_long_term",
                               "noexp": "no_clear_expectation"}),
    "trig": ("drop_trigger", {"inc": "income_cashflow", "ret": "returns_below_expectation",
                              "mkt": "market_fall_red_portfolio", "pay": "payment_mandate_failure",
                              "conf": "app_confusion", "need": "needs_money_goal", "trust": "distrust_platform",
                              "adv": "advice_to_stop", "sw": "switching"}),
    "freq": ("check_frequency", {"d": "daily_or_more", "w": "weekly", "m": "monthly", "r": "rarely"}),
    "chk": ("what_checked", {"tot": "total_returns", "day": "daily_change", "xirr": "xirr_cagr",
                             "inst": "instalment_status", "cmp": "compare_others"}),
    "pain": ("in_app_pain", {"mand": "mandate_autopay", "fail": "failed_or_missed_instalment",
                             "disp": "returns_display", "mod": "modify_pause_flow", "sync": "tracking_sync",
                             "kyc": "kyc_onboarding", "sup": "support", "bug": "bugs_ui_change",
                             "chg": "charges_transparency"}),
    "out": ("outside_app", {"forum": "reddit_forum", "yt": "youtube_creator", "ff": "friends_family",
                            "pro": "professional", "tool": "other_tool"}),
    "drv": ("continuation_driver", {"auto": "automation_habit", "belief": "long_term_belief",
                                    "goalp": "goal_progress", "reass": "reassurance_education",
                                    "small": "affordable_amount"}),
    "inc": ("income_stability", {"sal": "stable_salaried", "var": "variable_income",
                                 "stu": "student_no_income", "shock": "income_shock"}),
    "age": ("age_band", {"u25": "under_25", "25": "25_34", "35": "35_plus"}),
    "money": ("money_source", {"sal": "salary", "sav": "savings", "fam": "family_money", "wind": "windfall"}),
    "infl": ("influencer", {"self": "self_research", "fam": "family", "fr": "friends_colleagues",
                            "media": "creator_media", "app": "app_prompt"}),
    "need": ("unmet_need", {"track": "know_if_on_track", "vol": "understand_volatility",
                            "flex": "flexible_control", "pay": "reliable_payments",
                            "help": "neutral_help_when_unsure", "goal": "goal_link",
                            "trust": "trust_support", "cost": "clear_costs"}),
    "risk": ("continuation_risk", {"0": "0", "1": "1", "2": "2", "3": "3"}),
}


def _default():
    d = {}
    for f, spec in CB.FIELDS.items():
        vals = spec["values"]
        empty = "unknown" if "unknown" in vals else ("none" if "none" in vals else "0")
        d[f] = [empty] if spec["multi"] else empty
    d.update(product="general", need_text="", quote="", reason="")
    return d


def make_sample():
    corpus = load_corpus()
    gold = json.loads((C.EVAL / "golden_ids.json").read_text())
    by = {}
    for r in sorted(corpus, key=lambda r: hashlib.md5(r["id"].encode()).hexdigest()):
        by.setdefault(r["source"], []).append(r)
    ids, threads = list(gold), Counter()
    for src, q in QUOTAS.items():
        n = 0
        for r in by.get(src, []):
            if n >= q:
                break
            if r["id"] in ids or threads[r["thread_id"]] >= 2:  # thread diversity
                continue
            ids.append(r["id"])
            threads[r["thread_id"]] += 1
            n += 1
    SAMPLE.write_text(json.dumps(ids))
    print(f"sample: {len(ids)} records", Counter(next(r["source"] for r in corpus if r["id"] == i) for i in ids))


def show(a, b):
    ids = json.loads(SAMPLE.read_text())[a:b]
    corpus = {r["id"]: r for r in load_corpus()}
    done = load_done()
    for i in ids:
        if i in done:
            continue
        r = corpus[i]
        ctx = f" [thread: {r['context'][:90]}]" if r.get("context") else ""
        title = f" TITLE: {r['title'][:150]} |" if r.get("title") and r["kind"] != "comment" else ""
        print(f"## {i} ({r['source']}/{r['kind']}{', rating ' + str(r['rating']) if r.get('rating') else ''}){ctx}{title} {r['text'][:480]}")


def parse_line(line):
    head, rest = line.split(" ", 1) if " " in line else (line, "")
    item = _default()
    item["id"] = head.strip()
    for tok in shlex.split(rest):
        k, v = tok.split("=", 1)
        if k == "q":
            item["quote"] = v
        elif k == "nt":
            item["need_text"] = v
        else:
            field, m = ABBR[k]
            vals = [m[x] for x in v.split(",")]
            item[field] = vals if CB.FIELDS[field]["multi"] else vals[0]
    if item["relevance"] == "not_relevant":
        item["reason"] = "not about SIP/MF continuation"
    else:
        item["reason"] = "labelled in-session against codebook"
    return item


def ingest(path):
    corpus = {r["id"]: r for r in load_corpus()}
    done = load_done()
    failed_p = C.PROCESSED / "inline_gate_failures.json"
    failed = json.loads(failed_p.read_text()) if failed_p.exists() else {}
    ok, bad = 0, []
    with OUT.open("a", encoding="utf-8") as out:
        for line in open(path, encoding="utf-8"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            try:
                item = parse_line(line)
            except Exception as e:  # noqa: BLE001
                bad.append((line[:40], f"parse: {e}"))
                continue
            if item["id"] in done or item["id"] not in corpus:
                bad.append((item["id"], "duplicate or unknown id"))
                continue
            errs = validate(item, corpus[item["id"]])
            if errs:
                bad.append((item["id"], errs))
                failed.setdefault(item["id"], errs)
                continue
            item.update(status="passed_on_retry" if item["id"] in failed else "passed_first_try", model=MODEL, prompt_version=C.PROMPT_VERSION,
                        coded_at=datetime.now(timezone.utc).isoformat(timespec="seconds"))
            out.write(json.dumps(item, ensure_ascii=False) + "\n")
            done[item["id"]] = item
            ok += 1
    failed_p.write_text(json.dumps(failed, indent=1))
    print(f"ingested {ok}; failed gates: {len(bad)}; total coded: {len(done)}")
    for b in bad:
        print("  ", b)


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "sample":
        make_sample()
    elif cmd == "show":
        show(int(sys.argv[2]), int(sys.argv[3]))
    elif cmd == "ingest":
        ingest(sys.argv[2])
