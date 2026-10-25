# INDmoney SIP Discovery Engine (v2)

AI-powered discovery engine for the question: **why do first-time mutual-fund investors on INDmoney
stop having an active SIP within 12 months, and which unmet needs matter most?**

Research tool only. It never recommends funds or stocks and does not give investment advice.

## What it does

| Stage | How | Output |
|---|---|---|
| 1. Collect | Public sources, no login: Google Play + App Store reviews of INDmoney, Reddit (6 Indian investing subreddits, posts + comments), TradingQ&A, YouTube comments on SIP videos. Authors stored as one-way hashes. | `data/raw/*.jsonl` + manifests |
| 2. Prefilter | Code: dedupe, keep records about SIPs / mutual funds | `data/processed/corpus.jsonl`, `funnel.json` |
| 3. AI coding | Groq LLM labels every record on an 18-field codebook mapped to the brief's questions (`engine/codebook.py`) | `classified.jsonl` |
| 4. Quality gates | Every output: allowed values only, exact supporting quote from the record, stage/risk consistency. One retry, then rejected and excluded. | status per record |
| 5. Analysis | Code, not LLM: theme shares, continuers vs at-risk comparison, segment splits, opportunity score per unmet need | `analysis.json` |
| 6. Golden set | 20 blind, source-stratified records hand-labelled by the researcher; agreement + Cohen's kappa per field | `data/eval/golden_report.json` |
| 7. Ask the engine | Grounded Q&A with 4 visible gates: scope (no advice), enough evidence, exact-quote citations, numbers from code | in the app |

Opportunity score = reach × closeness to a lapse × first-year share × controllability (adjustable in the app).

## Run it (Mac)

```bash
bash run_mac.sh                 # full pipeline; asks for your Groq key once
bash run_mac.sh classify        # resume AI coding (it skips records already coded)
bash run_mac.sh golden-score    # after you label data/eval/golden_worksheet.xlsx
source .venv/bin/activate && streamlit run app.py
```

Groq free-tier daily token limits may stop classification part-way. It is resumable: run
`bash run_mac.sh classify` again later. If a model hits its daily limit, the next model in the fallback
list is used and recorded per record (set `GROQ_MODELS` to control the list).

## Golden set workflow

1. `data/eval/golden_worksheet.xlsx` is created before AI coding and shows no AI labels.
2. Label the yellow columns by hand (dropdowns + `codebook` sheet), save as `data/eval/golden_labels.xlsx`.
3. `bash run_mac.sh golden-score` → agreement report + updated `docs/AI_Evidence_Log_draft.md`.

## Deploy (Streamlit Community Cloud)

Commit `data/processed/` and `data/eval/` (raw data is git-ignored), main file `app.py`, and set
`GROQ_API_KEY` in the app's Secrets. Without a key, the dashboard still works and Ask the engine
falls back to showing evidence.

## Tests

`python -m unittest discover -s tests -v` runs the full pipeline on synthetic records with a fake LLM.

## Limitations

Public feedback over-represents complaints; first-time status, age and income are rarely stated;
post dates are not investor tenure; the engine ranks where to look and cannot measure retention rates.
Version 1 (20-record pilot) is preserved in `archive/v1/`.
