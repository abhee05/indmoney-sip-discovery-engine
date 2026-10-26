"""Shared helpers for collectors: record schema, hashing, polite HTTP."""
import hashlib
import json
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from engine.config import RAW  # noqa: E402

TODAY = datetime.now(timezone.utc).strftime("%Y-%m-%d")
UA = "Mozilla/5.0 (research; INDmoney SIP discovery student project)"


def anon(name):
    """Authors are stored only as a short one-way hash (dedupe, no identity)."""
    if not name:
        return ""
    return hashlib.sha256(str(name).encode()).hexdigest()[:10]


def clean(text):
    text = re.sub(r"https?://\S+", "[link]", text or "")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def record(source, rid, text, url, *, title="", rating=None, published_at="",
           thread_id="", author="", query="", kind="post", score=None):
    return {
        "id": f"{source[:2].upper()}-{rid}",
        "source": source,
        "kind": kind,
        "title": clean(title),
        "text": clean(text),
        "url": url,
        "thread_id": str(thread_id or rid),
        "author_hash": anon(author),
        "rating": rating,
        "score": score,
        "published_at": published_at or "unknown",
        "captured_at": TODAY,
        "query": query,
    }


def save(source, rows, errors):
    seen, out = set(), []
    for r in rows:
        key = hashlib.sha1((r["title"] + "|" + r["text"]).lower().encode()).hexdigest()
        if r["text"] and key not in seen:
            seen.add(key)
            out.append(r)
    path = RAW / f"{source}.jsonl"
    with path.open("w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    meta = {"source": source, "captured_at": TODAY, "records": len(out),
            "duplicates_removed": len(rows) - len(out), "errors": errors[:50],
            "error_count": len(errors)}
    (RAW / f"{source}.manifest.json").write_text(json.dumps(meta, indent=2))
    print(f"[{source}] saved {len(out)} records ({len(errors)} errors) -> {path.name}")
    return out


def get_json(session, url, params=None, tries=3, pause=1.5):
    last = RuntimeError('rate limited (429)')
    for attempt in range(tries):
        try:
            r = session.get(url, params=params, timeout=20,
                            headers={"User-Agent": UA, "Accept": "application/json"})
            if r.status_code == 403 and "www.reddit.com" in url:
                url = url.replace("www.reddit.com", "old.reddit.com")  # fallback host
                continue
            if r.status_code == 429:
                time.sleep(10 * (attempt + 1))
                continue
            r.raise_for_status()
            time.sleep(pause)
            return r.json()
        except Exception as e:  # noqa: BLE001
            last = e
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"{url}: {type(last).__name__}: {last}")
