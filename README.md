# INDmoney SIP Discovery Engine

Research pilot for understanding 12-month SIP continuation among first-time mutual-fund investors in India. Research support only; no investment advice or fund recommendations.

## Current status — 24 October 2026

- Retrieved and keyword-screened 500 unique Indian App Store reviews (10 RSS pages).
- Curated 38 pilot items: 33 App Store reviews, 3 Reddit items, 2 TradingQ&A items.
- Prepared 20 blank human-labelling records. These are NOT a completed golden set.
- Streamlit evidence explorer and Groq integration scaffold; live AI and deployment not yet validated.
- No measured classification accuracy, latency or retention impact yet.

## Run

Python 3.11+ recommended.

```
pip install -r requirements.txt
streamlit run app.py
python -m unittest discover -s tests
```

Set GROQ_API_KEY and GROQ_MODEL in server environment or Streamlit Secrets. Never put keys in GitHub or the browser UI. Model selection remains pending account availability and evaluation. With no key, source browsing still works; the app clearly labels AI as unavailable.

## Data and methodology

`data/pilot.json` contains source identifiers, short attributed excerpts and AI-assisted paraphrases. Paraphrases are not manual labels. `data/collection_manifest.json` records volume and limitations. Apple URLs point to the app's review listing; use the exact review ID, title and date to locate a review, or rerun the RSS collector. Review ordering changes over time.

The pilot is purposive and heavily App Store weighted. Do not calculate population dropout rates, infer first-time status from age, treat redemption as SIP cancellation, count repeated comments as independent people, or mistake a reported product issue for a verified defect. Unknown publication dates remain unknown. Historic competitor forum posts are comparator evidence only.

## Next gates

1. Expand toward 200–300 relevant records with stronger first-time, first-year, pause/stop/restart and continuation evidence. Log inaccessible or excluded sources.
2. Refine the codebook; hand-label 20 items before exposing AI predictions. Use 12 development and 8 untouched holdout items, grouped by thread.
3. Add batch structured classification, code-derived theme counts and segment comparisons. Do not use retrieved top-k items to estimate prevalence.
4. Evaluate label agreement, citation support, unknown handling, hallucinations, refusals, errors and latency. Document 2–3 real corrections; never invent them.
5. Deploy and test signed-out access and free-tier failures. The first scaffold is not a completed Part 1 submission.
