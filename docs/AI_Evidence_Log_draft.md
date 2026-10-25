# AI Evidence Log — INDmoney SIP Discovery Engine
_Draft generated 2026-10-25 from engine outputs. Prompt version codebook-v3._

## 1. Sources and volume analysed

| Source | Collected | Unique | SIP-related candidates | Core evidence (AI) |
|---|---|---|---|---|
| app_store | 243 | 237 | 30 | 4 |
| play_store | 2572 | 2389 | 203 | 14 |
| reddit | 8406 | 8112 | 3652 | 101 |
| tradingqna | 1450 | 1440 | 994 | 16 |
| youtube | 2866 | 2638 | 634 | 29 |
| **Total** | **15537** | **14816** | **5513** | **164** |

- AI-coded records: 534; rejected by quality gates: 0
- Relevance split: {'adjacent': 310, 'core': 164, 'not_relevant': 60}
- Core evidence by product: {'indmoney': 22, 'general': 122, 'other_platform': 20}; distinct threads: 151
- First-year investors (explicit) in core evidence: 38
- Models used: {'claude-opus-5-5 (in-session)': 534}

Collection notes: TODO — list any source that failed or was thin (see data/raw/*.manifest.json).

## 2. How the engine works

Collect (public, no login) → prefilter in code → LLM coding against an 18-field codebook with per-output quality gates (allowed values, exact supporting quote, stage/risk consistency; one retry, then rejected) → all counts and opportunity scores computed in code → golden-set validation.

## 3. Quality gate results

- Passed first try: 533
- Passed after one retry: 1
- Rejected and excluded: 0

| Run at | Coded OK | Retry OK | Rejected | API calls | Tokens |
|---|---|---|---|---|---|
| 2026-10-25T10:21:12+00:00 | 0 | 0 | 0 | 0 | 0 |
| 2026-10-25T11:50:41+00:00 | 1 | 5 | 5 | 12 | 31847 |
| 2026-10-25T11:57:12+00:00 | 2 | 0 | 3 | 4 | 11457 |

## 4. Golden set (hand-labelled by the researcher)

Blind, source-stratified sample of 20 records labelled by hand before viewing AI output.

- Field-level agreement: **46%**
- Items where every field agreed: 2 / 20

| Field | Agree / labelled | Agreement | Cohen's kappa |
|---|---|---|---|
| relevance | 11 / 20 | 55% | 0.39 |
| product | 16 / 20 | 80% | 0.68 |
| investor_experience | 4 / 20 | 20% | -0.016 |
| journey_stage | 4 / 20 | 20% | 0.135 |
| drop_trigger | 11 / 20 | 55% | 0.221 |
| unmet_need | 7 / 20 | 35% | -0.02 |
| continuation_risk | 11 / 20 | 55% | 0.241 |

| AI labeller | Items | Field agreement |
|---|---|---|
| claude-opus-5-5 (in-session) | 7 | 45% |
| code prefilter | 2 | 100% |
| openai/gpt-oss-120b | 11 | 36% |

### Where the engine failed

- **PL-3f7bd9e9-680a-47e8-b6ea-** (play_store, [link](https://play.google.com/store/apps/details?id=in.indwealth&reviewId=3f7bd9e9-680a-47e8-b6ea-6a41dc29a918)): relevance: AI=adjacent vs human=core; investor_experience: AI=unknown vs human=experienced; journey_stage: AI=unknown vs human=ongoing; unmet_need: AI=none vs human=understand_volatility; continuation_risk: AI=0 vs human=1
- **TR-144644-19** (tradingqna, [link](https://tradingqna.com/t/do-we-get-compounding-benefits-in-case-of-lumpsum-investment-in-mutual-funds/144644/19)): relevance: AI=adjacent vs human=core; investor_experience: AI=unknown vs human=first_time_explicit; journey_stage: AI=unknown vs human=considering_start; unmet_need: AI=none vs human=understand_volatility
- **PL-2b28184b-ab0d-4b70-8e4f-** (play_store, [link](https://play.google.com/store/apps/details?id=in.indwealth&reviewId=2b28184b-ab0d-4b70-8e4f-ccf49b8954e4)): investor_experience: AI=unknown vs human=experienced; journey_stage: AI=unknown vs human=ongoing; drop_trigger: AI=none vs human=distrust_platform; unmet_need: AI=none vs human=trust_support; continuation_risk: AI=0 vs human=1
- **TR-20939-1** (tradingqna, [link](https://tradingqna.com/t/sip-elss-lock-in-period/20939/1)): relevance: AI=MISSING vs human=core; product: AI=MISSING vs human=general; investor_experience: AI=MISSING vs human=early; journey_stage: AI=MISSING vs human=considering_start; drop_trigger: AI=MISSING vs human=none; unmet_need: AI=MISSING vs human=understand_volatility; continuation_risk: AI=MISSING vs human=0
- **YO-Ugx3m90x1bFgwSGYsHx4AaABAg** (youtube, [link](https://www.youtube.com/watch?v=hbgQcxPt3Gk&lc=Ugx3m90x1bFgwSGYsHx4AaABAg)): investor_experience: AI=unknown vs human=first_time_explicit; journey_stage: AI=considering_stop vs human=first_months; drop_trigger: AI=returns_below_expectation vs human=market_fall_red_portfolio; unmet_need: AI=none vs human=understand_volatility; continuation_risk: AI=2 vs human=1
- **PL-478c0630-c109-4455-8b1e-** (play_store, [link](https://play.google.com/store/apps/details?id=in.indwealth&reviewId=478c0630-c109-4455-8b1e-7f9867a117f7)): journey_stage: AI=unknown vs human=ongoing
- **TR-13579-6** (tradingqna, [link](https://tradingqna.com/t/non-listing-of-direct-funds/13579/6)): relevance: AI=adjacent vs human=core; investor_experience: AI=unknown vs human=experienced; journey_stage: AI=unknown vs human=ongoing; drop_trigger: AI=none vs human=switching; unmet_need: AI=none vs human=flexible_control; continuation_risk: AI=0 vs human=1
- **PL-82ea0c5d-bb11-49f6-b4bb-** (play_store, [link](https://play.google.com/store/apps/details?id=in.indwealth&reviewId=82ea0c5d-bb11-49f6-b4bb-6d0b1badb4bb)): relevance: AI=MISSING vs human=core; product: AI=MISSING vs human=indmoney; investor_experience: AI=MISSING vs human=unknown; journey_stage: AI=MISSING vs human=ongoing; drop_trigger: AI=MISSING vs human=app_confusion; unmet_need: AI=MISSING vs human=know_if_on_track; continuation_risk: AI=MISSING vs human=1
- **TR-145104-4** (tradingqna, [link](https://tradingqna.com/t/why-trading-actively-in-stockmarket-is-pointless/145104/4)): relevance: AI=not_relevant vs human=core; investor_experience: AI=unknown vs human=experienced; journey_stage: AI=unknown vs human=restarted
- **YO-Ugy3Rn-OwzszvwIsoKV4AaABAg** (youtube, [link](https://www.youtube.com/watch?v=CPEatoLkXNI&lc=Ugy3Rn-OwzszvwIsoKV4AaABAg)): investor_experience: AI=unknown vs human=early; drop_trigger: AI=needs_money_goal vs human=income_cashflow; unmet_need: AI=none vs human=flexible_control
- **PL-bbde2476-6f7b-40b1-9e6e-** (play_store, [link](https://play.google.com/store/apps/details?id=in.indwealth&reviewId=bbde2476-6f7b-40b1-9e6e-07c30018cd21)): relevance: AI=not_relevant vs human=adjacent; product: AI=general vs human=indmoney; investor_experience: AI=unknown vs human=experienced; journey_stage: AI=unknown vs human=ongoing; drop_trigger: AI=none vs human=distrust_platform; unmet_need: AI=none vs human=trust_support; continuation_risk: AI=0 vs human=1
- **TR-171612-1** (tradingqna, [link](https://tradingqna.com/t/how-to-pay-using-the-payment-gateway-method-for-amc-sips/171612/1)): investor_experience: AI=unknown vs human=early; unmet_need: AI=none vs human=reliable_payments
- **PL-7b8c2138-25ec-432e-b065-** (play_store, [link](https://play.google.com/store/apps/details?id=in.indwealth&reviewId=7b8c2138-25ec-432e-b065-f741c895e435)): relevance: AI=adjacent vs human=not_relevant; investor_experience: AI=unknown vs human=experienced; journey_stage: AI=unknown vs human=ongoing
- **TR-111699-5** (tradingqna, [link](https://tradingqna.com/t/about-mf-regular-plan/111699/5)): investor_experience: AI=unknown vs human=experienced; journey_stage: AI=unknown vs human=ongoing
- **PL-85463a37-357e-4781-b37c-** (play_store, [link](https://play.google.com/store/apps/details?id=in.indwealth&reviewId=85463a37-357e-4781-b37c-40a08ddd4cbe)): journey_stage: AI=unknown vs human=ongoing; drop_trigger: AI=none vs human=distrust_platform; unmet_need: AI=none vs human=trust_support; continuation_risk: AI=0 vs human=1
- **TR-21935-15** (tradingqna, [link](https://tradingqna.com/t/issues-of-smallcase/21935/15)): relevance: AI=MISSING vs human=not_relevant; product: AI=MISSING vs human=other_platform; investor_experience: AI=MISSING vs human=experienced; journey_stage: AI=MISSING vs human=ongoing; drop_trigger: AI=MISSING vs human=none; unmet_need: AI=MISSING vs human=none; continuation_risk: AI=MISSING vs human=0
- **YO-UgwsgNtC1Yyp-jXqr5Z4AaABAg** (youtube, [link](https://www.youtube.com/watch?v=x4P6luERcgA&lc=UgwsgNtC1Yyp-jXqr5Z4AaABAg)): investor_experience: AI=unknown vs human=early; journey_stage: AI=unknown vs human=considering_start; unmet_need: AI=know_if_on_track vs human=none
- **PL-6198597c-80ad-4d29-a403-** (play_store, [link](https://play.google.com/store/apps/details?id=in.indwealth&reviewId=6198597c-80ad-4d29-a403-b77f2b0fbb59)): investor_experience: AI=unknown vs human=experienced; journey_stage: AI=unknown vs human=ongoing

Failure patterns: TODO — group the disagreements above into 2-4 patterns in your own words.

## 5. Where I rejected or corrected AI output (2-3)

TODO — write these yourself from real cases (golden-set disagreements, explorer review, or opportunity-score assumptions). For each: what the AI said, what you changed, why, and the record link.

## 6. Top opportunity areas (from code)

| Unmet need | Mentions | Threads | % at/near lapse | % first-year | Score index |
|---|---|---|---|---|---|
| Neutral, non-advisory help at a moment of doubt | 61 | 61 | 20% | 44% | 100 |
| Pause/skip/reduce without losing the habit or penalties | 23 | 21 | 56% | 4% | 65 |
| Understand why returns look like this and what is normal | 13 | 13 | 23% | 31% | 24 |
| Instalments that just work, and clear alerts when they don't | 15 | 15 | 20% | 0% | 22 |
| Know whether my SIP is doing OK / on track for my goal | 13 | 13 | 0% | 8% | 10 |
| See the SIP connected to a personal goal | 4 | 4 | 25% | 25% | 7 |
| Trustworthy platform and responsive support | 7 | 7 | 0% | 0% | 4 |
| Clear costs and plan type | 4 | 4 | 0% | 50% | 3 |

## 7. Limitations

- Public feedback over-represents complaints and vocal users; not a random sample of investors.
- First-time status, age and income are rarely stated; segment groups are small.
- Review or post dates are not investor tenure; the engine cannot measure retention rates.
- User reports are unverified claims about the product.
- Opportunity scores rank where to look; controllability weights are PM judgement.

## Appendix: codebook

- **relevance** — Gate: is this about staying with (or leaving) a SIP / mutual fund?: core, adjacent, not_relevant
- **product** — Which platform is this experience about?: indmoney, other_platform, general
- **investor_experience** — Segment: how experienced is the investor? (explicit evidence only): first_time_explicit, early, experienced, unknown
- **journey_stage** — Where in the first-12-month journey is the person?: considering_start, onboarding, first_months, ongoing, considering_stop, reduced_or_paused, stopped, restarted, unknown
- **start_motivation** — Q1: Why do people start a SIP?: long_term_wealth, specific_goal, tax_saving, someone_suggested, discipline_habit, trend, unknown
- **expectation** — Q1: What did they expect to happen?: quick_visible_gains, steady_long_term, no_clear_expectation, unknown
- **drop_trigger** — Q3: What leads investors to pause, reduce or stop? (primary reason): income_cashflow, returns_below_expectation, market_fall_red_portfolio, payment_mandate_failure, app_confusion, needs_money_goal, distrust_platform, advice_to_stop, switching, none
- **check_frequency** — Q4: How often do they check?: daily_or_more, weekly, monthly, rarely, unknown
- **what_checked** — Q4: What do they check?: total_returns, daily_change, xirr_cagr, instalment_status, compare_others, unknown
- **in_app_pain** — Q5: What confuses or worries them inside the app?: mandate_autopay, failed_or_missed_instalment, returns_display, modify_pause_flow, tracking_sync, kyc_onboarding, support, bugs_ui_change, charges_transparency, none
- **outside_app** — Q6: What do they do outside the app when unsure?: reddit_forum, youtube_creator, friends_family, professional, other_tool, none
- **continuation_driver** — Q7: What keeps continuers going?: automation_habit, long_term_belief, goal_progress, reassurance_education, affordable_amount, none
- **income_stability** — Q8 segment: income stability (explicit only): stable_salaried, variable_income, student_no_income, income_shock, unknown
- **age_band** — Q8 segment: age (explicit only, never guessed): under_25, 25_34, 35_plus, unknown
- **money_source** — Q8 segment: where the SIP money comes from: salary, savings, family_money, windfall, unknown
- **influencer** — Q8 segment: who influenced them to start: self_research, family, friends_colleagues, creator_media, app_prompt, unknown
- **unmet_need** — Q9: What unmet need does this reveal? (primary): know_if_on_track, understand_volatility, flexible_control, reliable_payments, neutral_help_when_unsure, goal_link, trust_support, clear_costs, none
- **continuation_risk** — How close is this to a lapsed SIP?: 0, 1, 2, 3