# Project notes (read this first in a new chat)

NextLeap PM Fellowship graduation project. Product: **INDmoney**. Role: Growth PM.

## Goal
Raise 12-month SIP continuation for first-time MF investors.
Active SIP = at least one successful instalment in the last 30 days.

## Rules
- No fund or stock recommendations.
- No fear, FOMO or urgency nudges.
- Deck: 10 slides, PDF, file name `NL_INDmoney`, font 14pt or larger.
- **No name anywhere in the deck** (slides, footers, notes, file properties). A GitHub username in links is fine.
- Don't copy batchmates' content.
- Deadline: **9 Nov 2026, 3:59 PM IST**.

## Deliverables
1. Discovery engine link (Part 1, DONE): Streamlit app + this repo.
2. 10-slide deck (PDF).
3. Deployed MVP.
4. AI Evidence Log: a Google Doc with view access for anyone with the link (DONE, keep updated).

## Status
- Part 1 is done. The app answers the brief's 9 questions, including Q2, Q4 and Q8, with evidence-strength lines.
- Next: Part 2 (metric breakdown), Part 3 (user interviews), the deck, the MVP.

## Key numbers (Part 1)
- 18,489 records collected, 16,973 unique, 6,923 SIP/MF candidates.
- 676 investor records AI-coded; 238 are core continuation evidence; 66 are first-year.
- 15 staff replies excluded.
- Golden set: 20 records, 46% field agreement.
- Top need: neutral help when unsure (87 mentions, 52% first-year).
- Need closest to lapse: flexible pause (47% of mentions near a lapse).
- Q2 rests on 83 posts, Q4 on 50 (14 state a frequency), Q8 on 83.

## How to run
`bash run_mac.sh <step>`, where step is collect, prefilter, classify, analyze, golden-score or evidence-log.
The Groq key goes in `.env`. I push to GitHub from my Mac.

## Working style
Keep instructions short and minimal.
