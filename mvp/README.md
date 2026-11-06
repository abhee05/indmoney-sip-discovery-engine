# Before you pause (MVP)

A concept prototype for first-time SIP investors. When someone taps **Pause** or **Stop** after their SIP
turns red, they see their real numbers, how every past SIP of the same length in their fund looked at the
same point (bad cases included), plain answers to their questions, and all four options (continue, skip
once, pause until a month, stop). It never recommends funds, never predicts, and never hides Stop.

Not affiliated with INDmoney. Not investment advice.

## How it works

| Step | Done by | Notes |
|---|---|---|
| Fund prices | code | Real daily NAVs from mfapi.in (AMFI data); saved copies in `data/navs/` if the API is down |
| Your SIP and past base rates | code | `core/sip.py`; a replayed past dip only uses prices known at that time |
| Routing a question | code | `core/intent.py`; fund picks and buy/sell/switch → declined; "when will it recover" → declined with base rates |
| Writing the explanation | AI (Groq) | Only for "is this normal / should I stop / money is tight" and the opening message |
| Checking every answer | code | `core/respond.py`: numbers must match the code's, no advice, no predictions, no urgency, history needs its caveat, length |
| Fallback | code | AI off, failed, or blocked twice → a written template answer, marked as such |

## Run locally

```bash
pip install -r mvp/requirements.txt
export GROQ_API_KEY=...          # optional; without it the app uses template answers
streamlit run mvp/app.py
```

## Tests and evaluation

```bash
python -m pytest -q mvp/tests          # maths, routing, gates, and the full app flow with a fake Streamlit
python mvp/eval/run_eval.py            # scores answers against eval/golden_set.csv -> eval/report.json
```

The golden set (23 questions) comes from the INDmoney assistant test, the 6 interviews, the survey, and
edge cases. Its expected labels must be checked by hand before the score is quoted; `label_status`
records that.

## Deploy (Streamlit Community Cloud)

New app → this repo → branch `main` → main file `mvp/app.py`. In **Advanced settings → Secrets** add:

```toml
GROQ_API_KEY = "your key"
```
