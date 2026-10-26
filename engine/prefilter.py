"""Stage 2: merge raw sources, dedupe, and keep records that could be about SIPs.

Recall-oriented and deliberately cheap: the LLM makes the real relevance call.
Writes data/processed/corpus.jsonl and a funnel (counts per stage per source)
that goes straight into the Evidence Log.
"""
import hashlib
import json
import re

from engine import config as C

TERM_RE = re.compile("|".join(re.escape(t.strip()) for t in C.SIP_TERMS), re.I)
WORD_SIP = re.compile(r"\b(sips?|mutual funds?|mfs?)\b", re.I)


def load_raw():
    rows = []
    for path in sorted(C.RAW.glob("*.jsonl")):
        with path.open(encoding="utf-8") as f:
            rows += [json.loads(line) for line in f if line.strip()]
    return rows


def is_candidate(r, thread_titles):
    text = r["text"] if r["source"] == "youtube" else f"{r.get('title', '')} {r['text']}"
    if len(r["text"]) < C.MIN_CHARS:
        return False
    if WORD_SIP.search(text) or TERM_RE.search(f" {text.lower()} "):
        return True
    # a question-targeted search already scoped the topic (e.g. "check my portfolio daily")
    if str(r.get("query", "")).startswith("targeted:") and len(r["text"]) >= 40 and re.search(
            r"\b(portfolio|invest\w*|returns?|fund|salary|income)\b", text, re.I):
        return True
    # comments inside a SIP-focused thread can be relevant without the keyword
    if r["source"] == "youtube":
        return False
    ctx = thread_titles.get(r["thread_id"], "")
    return r["kind"] == "comment" and len(r["text"]) >= 60 and bool(WORD_SIP.search(ctx))


def run():
    rows = load_raw()
    funnel = {}
    thread_titles = {}
    for r in rows:
        if r.get("title"):
            thread_titles.setdefault(r["thread_id"], r["title"])
    seen, out = set(), []
    for r in rows:
        f = funnel.setdefault(r["source"], {"collected": 0, "after_dedupe": 0, "candidates": 0})
        f["collected"] += 1
        key = hashlib.sha1(re.sub(r"\W+", "", r["text"].lower())[:400].encode()).hexdigest()
        if key in seen:
            continue
        seen.add(key)
        f["after_dedupe"] += 1
        if is_candidate(r, thread_titles):
            f["candidates"] += 1
            r["context"] = thread_titles.get(r["thread_id"], "") if r["kind"] == "comment" else ""
            out.append(r)
    path = C.PROCESSED / "corpus.jsonl"
    with path.open("w", encoding="utf-8") as fh:
        for r in out:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
    totals = {k: sum(v[k] for v in funnel.values()) for k in ("collected", "after_dedupe", "candidates")}
    funnel["_total"] = totals
    (C.PROCESSED / "funnel.json").write_text(json.dumps(funnel, indent=2))
    print(f"prefilter: {totals['collected']} collected -> {totals['after_dedupe']} unique "
          f"-> {totals['candidates']} candidates for AI coding")
    return out


def load_corpus():
    path = C.PROCESSED / "corpus.jsonl"
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
