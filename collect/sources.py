"""Collectors for each public source. Run via:  python run.py collect

Every collector fails soft: errors are recorded in the source manifest and the
other sources still run. Nothing here needs login or API keys.
"""
import time

import requests

from collect.common import get_json, record, save
from engine import config as C


# ------------------------------------------------------------------ Play Store
def play_store():
    from google_play_scraper import Sort, reviews

    rows, errors, token = [], [], None
    while len(rows) < C.PLAY_MAX_REVIEWS:
        try:
            batch, token = reviews(C.PLAY_APP_ID, lang="en", country="in",
                                   sort=Sort.NEWEST, count=200,
                                   continuation_token=token)
        except Exception as e:  # noqa: BLE001
            errors.append(f"{type(e).__name__}: {e}")
            break
        for r in batch:
            rows.append(record(
                "play_store", r["reviewId"][:24], r.get("content") or "",
                f"https://play.google.com/store/apps/details?id={C.PLAY_APP_ID}&reviewId={r['reviewId']}",
                rating=r.get("score"),
                published_at=r["at"].isoformat() if r.get("at") else "",
                author=r.get("userName"), kind="review",
                score=r.get("thumbsUpCount")))
        if not batch or token is None:
            break
        time.sleep(1)
    return save("play_store", rows, errors)


# ------------------------------------------------------------------ App Store
def app_store():
    s, rows, errors = requests.Session(), [], []
    for sort in ("mostrecent", "mosthelpful"):
        for page in range(1, C.APPLE_PAGES + 1):
            url = (f"https://itunes.apple.com/in/rss/customerreviews/page={page}/"
                   f"id={C.APPLE_APP_ID}/sortby={sort}/json")
            try:
                feed = get_json(s, url, pause=0.8).get("feed", {})
            except Exception as e:  # noqa: BLE001
                errors.append(str(e))
                continue
            entries = feed.get("entry", [])
            if isinstance(entries, dict):
                entries = [entries]
            for e in entries:
                if "im:rating" not in e:
                    continue  # first entry can be app metadata
                rid = e["id"]["label"]
                rows.append(record(
                    "app_store", rid, e["content"]["label"],
                    f"https://apps.apple.com/in/app/id{C.APPLE_APP_ID}?see-all=reviews#review-{rid}",
                    title=e["title"]["label"], rating=int(e["im:rating"]["label"]),
                    published_at=e.get("updated", {}).get("label", ""),
                    author=e.get("author", {}).get("name", {}).get("label"),
                    kind="review", query=sort))
            if not entries:
                break
    return save("app_store", rows, errors)


# ------------------------------------------------------------------ Reddit
def _reddit_ts(t):
    import datetime as dt
    return dt.datetime.utcfromtimestamp(t).isoformat() + "Z" if t else ""


def reddit():
    s, rows, errors, threads = requests.Session(), [], [], {}
    base = "https://www.reddit.com"
    for sub in C.SUBREDDITS:
        for q in C.REDDIT_QUERIES:
            try:
                data = get_json(s, f"{base}/r/{sub}/search.json",
                                {"q": q, "restrict_sr": 1, "sort": "relevance",
                                 "t": "all", "limit": C.REDDIT_POSTS_PER_QUERY})
            except Exception as e:  # noqa: BLE001
                errors.append(str(e))
                continue
            for child in data.get("data", {}).get("children", []):
                p = child["data"]
                pid = p["id"]
                rows.append(record(
                    "reddit", pid, p.get("selftext", ""), base + p["permalink"],
                    title=p.get("title", ""), published_at=_reddit_ts(p.get("created_utc")),
                    thread_id=pid, author=p.get("author"), query=f"r/{sub}: {q}",
                    score=p.get("score")))
                threads.setdefault(pid, (p.get("num_comments", 0), p["permalink"]))
        print(f"  r/{sub}: {len(rows)} posts so far")
    # comments from the most-discussed threads (where the "why" usually lives)
    top = sorted(threads.items(), key=lambda kv: -kv[1][0])[:C.REDDIT_COMMENT_THREADS]
    for i, (pid, (_, link)) in enumerate(top, 1):
        try:
            data = get_json(s, f"{base}{link}.json",
                            {"limit": C.REDDIT_COMMENTS_PER_THREAD, "depth": 2, "sort": "top"})
        except Exception as e:  # noqa: BLE001
            errors.append(str(e))
            continue
        stack = list(data[1]["data"]["children"]) if len(data) > 1 else []
        while stack:
            c = stack.pop()
            if c.get("kind") != "t1":
                continue
            d = c["data"]
            rows.append(record(
                "reddit", d["id"], d.get("body", ""), base + d.get("permalink", link),
                published_at=_reddit_ts(d.get("created_utc")), thread_id=pid,
                author=d.get("author"), kind="comment", score=d.get("score")))
            rep = d.get("replies")
            if isinstance(rep, dict):
                stack.extend(rep["data"]["children"])
        if i % 20 == 0:
            print(f"  comments: {i}/{len(top)} threads")
    return save("reddit", rows, errors)


# ------------------------------------------------------------------ TradingQ&A
def tradingqna():
    s, rows, errors, topics = requests.Session(), [], [], set()
    base = "https://tradingqna.com"
    for q in C.TQNA_QUERIES:
        try:
            data = get_json(s, f"{base}/search.json", {"q": q})
        except Exception as e:  # noqa: BLE001
            errors.append(str(e))
            continue
        for t in data.get("topics", [])[:C.TQNA_TOPICS_PER_QUERY]:
            topics.add(t["id"])
    for tid in sorted(topics):
        try:
            t = get_json(s, f"{base}/t/{tid}.json")
        except Exception as e:  # noqa: BLE001
            errors.append(str(e))
            continue
        for p in t.get("post_stream", {}).get("posts", []):
            import re
            text = re.sub(r"<[^>]+>", " ", p.get("cooked", ""))
            rows.append(record(
                "tradingqna", f"{tid}-{p['post_number']}", text,
                f"{base}/t/{t.get('slug', '')}/{tid}/{p['post_number']}",
                title=t.get("title", "") if p["post_number"] == 1 else "",
                published_at=p.get("created_at", ""), thread_id=tid,
                author=p.get("username"),
                kind="post" if p["post_number"] == 1 else "comment"))
    return save("tradingqna", rows, errors)


# ------------------------------------------------------------------ YouTube
def youtube():
    rows, errors = [], []
    try:
        import yt_dlp
        from youtube_comment_downloader import SORT_BY_POPULAR, YoutubeCommentDownloader
    except ImportError as e:
        return save("youtube", [], [f"missing package: {e}"])
    videos = {}
    with yt_dlp.YoutubeDL({"quiet": True, "extract_flat": True, "skip_download": True}) as ydl:
        for q in C.YT_QUERIES:
            try:
                res = ydl.extract_info(f"ytsearch{C.YT_VIDEOS_PER_QUERY}:{q}", download=False)
                for v in res.get("entries", []):
                    videos.setdefault(v["id"], (v.get("title", ""), q))
            except Exception as e:  # noqa: BLE001
                errors.append(f"search {q}: {e}")
    dl = YoutubeCommentDownloader()
    for vid, (vtitle, q) in videos.items():
        try:
            for i, c in enumerate(dl.get_comments_from_url(
                    f"https://www.youtube.com/watch?v={vid}", sort_by=SORT_BY_POPULAR)):
                if i >= C.YT_COMMENTS_PER_VIDEO:
                    break
                rows.append(record(
                    "youtube", c["cid"][:30], c.get("text", ""),
                    f"https://www.youtube.com/watch?v={vid}&lc={c['cid']}",
                    title=f"[video] {vtitle}", thread_id=vid, author=c.get("author"),
                    kind="comment", query=q, published_at=c.get("time", ""),
                    score=c.get("votes")))
        except Exception as e:  # noqa: BLE001
            errors.append(f"{vid}: {e}")
        print(f"  youtube: {len(rows)} comments so far")
    return save("youtube", rows, errors)


ALL = {"play_store": play_store, "app_store": app_store, "reddit": reddit,
       "tradingqna": tradingqna, "youtube": youtube}
