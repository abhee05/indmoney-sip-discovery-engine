"""Central configuration: sources, search queries and paths.

Edit this file to change what the discovery engine collects.
"""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = Path(os.environ.get("DISCOVERY_DATA", ROOT / "data"))  # override for tests
RAW = DATA / "raw"
PROCESSED = DATA / "processed"
EVAL = DATA / "eval"
for _p in (RAW, PROCESSED, EVAL):
    _p.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------- app stores
PLAY_APP_ID = "in.indwealth"          # INDmoney on Google Play
PLAY_MAX_REVIEWS = 4000               # newest-first; English, India
APPLE_APP_ID = "1450178837"           # INDmoney on the Indian App Store
APPLE_PAGES = 10                      # RSS feed caps at 10 pages x 50 reviews

# ---------------------------------------------------------------- reddit
SUBREDDITS = [
    "mutualfunds", "MutualfundsIndia", "IndiaInvestments",
    "personalfinanceindia", "INDmoneyApp", "FIREIndia",
]
REDDIT_QUERIES = [
    "indmoney sip", "first sip", "stopped sip", "stop sip", "pause sip",
    "cancel sip", "skip sip", "sip negative returns", "sip loss",
    "continue sip", "sip not worth", "sip mandate failed", "sip autopay",
    "new to mutual funds", "beginner sip", "sip 1 year", "lost job sip",
]
REDDIT_POSTS_PER_QUERY = 50
REDDIT_COMMENT_THREADS = 120          # threads whose comments we also pull
REDDIT_COMMENTS_PER_THREAD = 60

# targeted searches for the brief's thinly covered questions (Q2, Q4, Q8)
TARGETED_SUBREDDITS = ["mutualfunds", "MutualfundsIndia", "IndiaInvestments",
                       "personalfinanceindia", "IndianStreetBets", "FIREIndia"]
TARGETED_QUERIES = {
    "Q2_behaviour_change": [
        "forgot about my SIP", "stopped checking my portfolio", "months after starting SIP",
        "first year of SIP", "6 months into SIP", "increased my SIP", "step up SIP",
        "kept changing funds", "started SIP last year", "after one year of SIP"],
    "Q4_checking": [
        "check my portfolio daily", "check portfolio every day", "how often check mutual fund",
        "checking returns daily", "don't check my portfolio", "obsessively checking portfolio",
        "check SIP returns", "looking at red portfolio"],
    "Q8_segments": [
        "freelancer SIP", "irregular income SIP", "variable income SIP", "student SIP",
        "college student mutual fund", "first salary SIP", "parents told me to start SIP",
        "dad started SIP for me", "pocket money SIP", "bonus SIP", "business income SIP",
        "SIP in my 40s", "influencer recommended fund", "friend suggested SIP"],
}
TARGETED_PER_QUERY = 25

# ---------------------------------------------------------------- tradingqna
TQNA_QUERIES = [
    "stop sip", "pause sip", "sip loss", "first sip", "sip mandate",
    "sip negative", "continue sip", "skip sip",
]
TQNA_TOPICS_PER_QUERY = 25

# ---------------------------------------------------------------- youtube
YT_QUERIES = [
    "should I stop my SIP", "SIP negative returns what to do",
    "SIP band kare ya continue", "SIP mistakes beginners",
    "first SIP experience", "INDmoney SIP", "SIP pause or stop",
]
YT_VIDEOS_PER_QUERY = 6
YT_COMMENTS_PER_VIDEO = 250

# ---------------------------------------------------------------- prefilter
# Records must mention investing-in-SIP/MF language to reach the LLM. This is
# a cheap recall-oriented screen; the LLM makes the real relevance decision.
SIP_TERMS = [
    "sip", "mutual fund", "mutual funds", "mf ", " mf", "mfs", "nav",
    "instalment", "installment", "mandate", "autopay", "auto pay",
    "systematic", "elss", "index fund", "flexi cap", "small cap", "mid cap",
    "xirr", "redeem", "redemption", "lumpsum", "lump sum", "folio",
]
MIN_CHARS = 25

# ---------------------------------------------------------------- llm
DEFAULT_MODEL = "llama-3.3-70b-versatile"
BATCH_SIZE = 6
PROMPT_VERSION = "codebook-v3"
