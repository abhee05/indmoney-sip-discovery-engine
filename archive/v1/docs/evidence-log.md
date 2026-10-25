# AI Evidence Log — working version

Collection date: 24 October 2026. This is an interim log, not a completed submission.

## Sources and volume

500 unique App Store review records retrieved from India's public RSS feed, pages 1–10. Keyword screening used SIP/SIPs/mutual/MF/XIRR, followed by relevance review. 33 selected for the pilot, including positives and ambiguous SIP asset types. Three Reddit records and two historic TradingQ&A records bring the pilot to 38. Each pilot item has its source link and locator. Apple listing links are not stable deep links to individual reviews; IDs/titles/dates support relocation.

This is purposive discovery sampling. Counts measure collected records, not INDmoney customers or retention rates. Source counts are exact; themes and segmentation have not been formally labelled. Broadly positive reviews are retained to avoid collecting only complaints.

## Early hypotheses to investigate, not findings about dropout

- Users may struggle to understand or locate portfolio information. Check whether this changes continuation decisions or merely causes inconvenience.
- Payment/KYC recovery may be unclear. Establish whether the investor ever made a first successful instalment and whether failures were resolved.
- Some investors use external communities for reassurance. Investigate the trigger, frequency, advice acted on and actual SIP outcome.
- Continued investing can coexist with infrequent portfolio checking. A historic experienced-investor example cannot establish what works for first-time users.

## Golden set

20 candidate records selected in data/manual_labels_blank.json. Human labels: pending. Model predictions: pending. Agreement: not measured. No AI-generated labels are represented as manual annotations. Read original sources before labelling; replace any record whose original cannot be assessed. Freeze a 12-item development / 8-item holdout split by thread before prompt tuning.

## Quality checks completed

Five automated checks passed: reject unknown source IDs, reject fabricated quotations, accept an exact source quotation, reject malformed/empty responses, and return no evidence for an unrelated query. Streamlit AppTest completed startup and missing-API-key fallback without exceptions. These validate software behaviour, not LLM accuracy or real-world reliability.

## Corrections and exclusions during collection

- Excluded the review titled “Unable to cancel SIP” (13845883391) from the pilot because it explicitly concerns US-stock SIPs, not mutual-fund SIPs.
- Kept unspecified SIP asset types marked ambiguous; did not turn them into confirmed MF evidence.
- Kept historic Coin discussions separate from current INDmoney product facts.

These are collection decisions, not substitutes for the required 2–3 documented corrections to actual discovery-engine outputs. That section remains pending live model runs.

## Missing evidence and next work

Need more explicit first-time investors, first-year experiences, income-related interruptions, actual pause/stop/restart events, and positive continuation cases across sources. YouTube/social sources are not collected. Play Store inspection yielded no included pilot records. The pilot is dominated by App Store feedback and cannot support a final opportunity ranking.

Live model selection, 20-item evaluation, free-tier load/latency measurement, public deployment and signed-out mentor testing are pending. No guarantee of error-free free-tier service is claimed.
