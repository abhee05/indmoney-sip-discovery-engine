# INDmoney AI Discovery Engine — Evidence Log
Updated 25 October 2026.

Full project brief read directly on NextLeap on 25 October 2026. Exact business metric: percentage of first-time mutual-fund investors with an active SIP 12 months after starting their first one. Active SIP means at least one successful instalment in the last 30 days. The brief specifies no minimum corpus size. The engine supports imports of up to 1,000 public INDmoney records per run; the included source-matched corpus remains 20.

## Scope and collection
Growth PM research into 12-month mutual-fund SIP continuation among first-time Indian investors. Active data: **20 records from 20 different Reddit discussions**, imported from the finalized INDmoney_Labels_Simplified.xlsx. All original text and row-specific URLs are in data/evidence.json. Snapshot provenance: source matching during worksheet preparation; dates not independently normalized are left unknown. Reports describe individual experiences, not verified app behaviour.

The original pilot recorded 500 App Store reviews screened, with 33 selected App Store records, 3 Reddit records and 2 TradingQ&A items. That is **historical collection**, not the current denominator. Its App Store sources could not be matched to usable individual pages for the final sheet. Those items and broader competitor expansion are excluded from active analysis. Do not add historical and active counts: overlap has not been audited. Play Store and investment sites were searched but yielded no included source-matched records. No claim of multi-platform active coverage is made.

Active selection is purposive, not representative. Sampling leaned toward problems, with positive/migration evidence retained. Distinct threads are not proof of distinct users. Quotes preserve spelling and wording; layout was normalized. Images were excluded. Mixed-product posts are included only for their INDmoney content. A referral link in IND19 may bias positive sentiment.

## Analysis
Six populated theme groups, one reserved Other / unclear category. Prepared assistant coding: plan/account clarity 7, payment/KYC recovery 5, convenience/support 3, visibility 2, guidance 2, app experience 1. One primary theme per item. Counts are computed from all classified records, not retrieved top-k results. After live batch failures, the UI exposes classified count and excludes failed outputs from theme percentages.

Investor experience and journey stage are coded conservatively with exact supporting quotations and caveats. Current prepared coding has only one explicit investing beginner; contradictory or incomplete histories remain unknown. This sample cannot estimate first-time investor dropout, 12-month continuation or product impact.

## Reproducibility
data/evidence.json is the active snapshot. data/prepared_analysis.json is assistant-prepared coding, not model evaluation or manual ground truth. Dataset SHA-256 is attached to predictions and evaluation references. discovery.py classifies every record in batches of five, with no prepared labels sent to Groq. Prompt version: indmoney-v2. Live results record model, elapsed time, errors and dataset hash. Exact source quotes and enumerated fields are validated per record. Failed records can be retried without discarding accepted results. The saved run retains retry raw outputs and the initial error summary; the initial rejected batch raw text was not captured by the earlier build and cannot be reconstructed.

Run locally: python -m streamlit run app.py. The standalone deploy_app.py bundles the same code and data for deployment. Run tests: python -m unittest discover -s tests. Set GROQ_API_KEY and GROQ_MODEL in server-side environment or Streamlit Secrets; never commit credentials.

## Evaluation status
Independent human golden set: pending. Live Groq run completed: **20/20 schema-and-quote-valid outputs after retry**, using openai/gpt-oss-120b. Cumulative API processing time: **16.18 seconds**, excluding time between attempts. Initial attempt accepted 10/20; one five-record batch failed validation and another hit HTTP 429. Retrying only the ten pending records in batches of two accepted all ten. This is output coverage, not accuracy. Independent human agreement and accuracy remain unmeasured. The 20 sheet labels were assistant-drafted at the user's request and are not represented as independently hand-labelled. A reference template and agreement calculator are available, with separate 12-item development and 8-item holdout reporting. Existing items are already exposed; use a fresh unseen holdout for stronger validation.

Agreement requires declared independent human provenance and a matching live run. Missing/failed outputs count as disagreements. Syntactically valid quotes do not prove correct interpretations; human review is essential.

## Actual corrections during preparation
These are real assistant-workflow corrections, not fabricated discovery-model failures:
1. Generic or unusable review links: removed from the active dataset; replaced with source-matched Reddit records. User's older labels remain in the workbook archive.
2. Seven separate comment URLs all landed in one discussion: replaced with seven different discussions to improve readability and diversity. The old comment links were not necessarily invalid.
3. Removed Leather-Habit6272's direct-plan claim at the user's request; replaced with the SIP refund/portfolio discrepancy post, IND18. Unsupported universal product-policy conclusions are not made.

## Three observed live-model corrections
Review provenance: assistant review of actual Groq output; these are not independent human evaluation. Raw predictions remain unchanged in the downloadable saved run. Run timestamp: 2026-10-25T03:40:32.478565+00:00; prompt indmoney-v2; model openai/gpt-oss-120b.

| Record | Actual model output | Corrected interpretation | Source evidence and reason |
|---|---|---|---|
| IND14 | stage = ongoing | considering_stop | “Should i cancel this?” explicitly considers cancellation. It does not establish that the SIP stopped. |
| IND15 | first_time = explicit_beginner | unknown | Self-description says beginner, but the same post says Quant ELSS was purchased two years ago. The conflicting history does not establish a first-time investor. |
| IND09 | first_time = unknown | experienced | “These SIPs are between 2-7 years old” explicitly establishes prior SIP experience. |

These are three selected semantic failures, not the complete error count. Exact-quote validation passed but did not prevent incorrect interpretation. Reviewed interpretations are recorded here separately; the original model output is preserved for audit. Source URLs appear in the source index below.


## Validation and remaining gates
Automated tests cover evidence integrity, quote/ID rejection, missing configuration, dataset-version mismatch, assistant-label rejection and failed-output denominators. UI tests cover startup, filtering and missing-configuration fallback. These are software checks, not model-quality results.

Software checks pass, including standalone startup and retry preservation. Public engine: https://indmoney-sip-discovery.streamlit.app/ . Public sharing is enabled; a separate signed-out browser check is still outstanding. Live provider failure and recovery were observed. The engine and real-run evidence are delivered; the remaining submission gate is genuinely independent manual labels and measured agreement. Expand the small, single-platform sample to fill evidence gaps where possible.


## Source index

| Record | Feedback | Source URL |
|---|---|---|
| IND01 | SIPs fail with no KYC retry link | https://www.reddit.com/r/MutualfundsIndia/comments/1niem1z/urgent_help_using_indmoney_for_sip_invested_in_a/ |
| IND02 | Daily SIP deductions skip days | https://www.reddit.com/r/MutualfundsIndia/comments/1pdtxyq/issue_with_indmoney_daily_sip_hdfc_flexi_cap/ |
| IND03 | Unclear payment limit after SIP increase | https://www.reddit.com/r/personalfinanceindia/comments/1tsqcm0/is_there_a_limit_for_sip_in_indmoney_via_autopay/ |
| IND04 | Wallet funding does not work for SIPs | https://www.reddit.com/r/mutualfunds/comments/1crqyez/indmoney_bad_experience_money_stuck_in_wallet/ |
| IND05 | Demat setup confuses mutual fund onboarding | https://www.reddit.com/r/INDmoneyApp/comments/1uoqkbl/mutual_fund_through_indmoney/ |
| IND06 | Unexpected demat holding mode | https://www.reddit.com/r/mutualfunds/comments/1t3er3k/indmoney_moving_mf_purchases_to_demat/ |
| IND07 | Direct mutual funds missing after signup | https://www.reddit.com/r/INDmoneyApp/comments/1qks4tn/i_cannot_see_direct_mutual_funds_in_the_app/ |
| IND08 | Membership hides direct fund options | https://www.reddit.com/r/INDmoneyApp/comments/1ws74cb/indpro_member_and_mutual_funds/ |
| IND09 | Unclear tax impact of switching SIPs | https://www.reddit.com/r/IndianStreetBets/comments/1r2312i/indmoney_keeps_reminding_me_to_switch_my_regular/ |
| IND10 | Incorrect balance and missing daily history | https://www.reddit.com/r/IndiaInvestments/comments/1lw3hdq/i_have_a_feeling_i_lost_40k_in_mutual_fund_but/ |
| IND11 | Promotional banners cannot be dismissed | https://www.reddit.com/r/INDmoneyApp/comments/1uxe4a9/please_stop_with_this_indmoney/ |
| IND12 | Values all investments in one place | https://www.reddit.com/r/INDmoneyApp/comments/1ulcmve/completely_moved_to_indmoney/ |
| IND13 | Beginner unsure which accounts are needed | https://www.reddit.com/r/INDmoneyApp/comments/1l9ms0n/newbie_questions/ |
| IND14 | Considering SIP cancellation over plan confusion | https://www.reddit.com/r/MutualfundsIndia/comments/1re708j/is_this_direct_or_regular_sip/ |
| IND15 | Beginner seeks confidence before increasing SIPs | https://www.reddit.com/r/MutualfundsIndia/comments/1pc6j10/please_review_my_portfolio/ |
| IND16 | New investor needs help choosing funds | https://www.reddit.com/r/mutualfunds/comments/1ojr8cx/investment_question_via_indmoney_app/ |
| IND17 | INDmoney import shows funds the user does not own | https://www.reddit.com/r/MutualfundsIndia/comments/1sia9bj/mutual_funds_portfolio_in_indmoney_showing_funds/ |
| IND18 | SIP refund not reflected in portfolio | https://www.reddit.com/r/MutualfundsIndia/comments/1wng4jh/units_were_bounced_and_returned_to_amc/ |
| IND19 | Moved two SIPs to INDmoney after helpful support | https://www.reddit.com/r/MutualfundsIndia/comments/1h5or9s/looking_for_etmoney_alternative/ |
| IND20 | Wants domestic and overseas investments together | https://www.reddit.com/r/MutualfundsIndia/comments/1j2cva4/switching_to_indmoney/ |

## One-slide explanation for the final deck

# AI discovery surfaces plan clarity and payment recovery as research priorities

**Goal:** improve 12-month SIP continuation for first-time INDmoney mutual-fund investors. Active means at least one successful instalment in the last 30 days.

**Workflow:** Gather public feedback with source URLs → keep INDmoney evidence and remove duplicates → classify themes and journey stage with supporting quotes → count and compare across the corpus → check outputs against hand labels → investigate disagreements.

**Current evidence:** 20 records from 20 Reddit discussions. Prepared coding: plan/account clarity 7, payment/KYC recovery 5, convenience/support 3, portfolio visibility 2, guidance 2 and app experience 1. These are sample counts, not population rates.

**Why these priorities:** one post considers cancelling over plan confusion; several report interrupted instalments or unclear recovery. Interviews must establish whether these issues affect continuation.

**Quality and limits:** source quote checks and unknown handling implemented. Live processing completed for 20/20 records after retry; three actual interpretation corrections are documented. Independent manual agreement remains pending. No confirmed 12-month outcomes; source and selection bias limit inference.

**Engine:** https://indmoney-sip-discovery.streamlit.app/

**Evidence Log:** https://github.com/abhee05/indmoney-sip-discovery-engine/blob/main/AI_Evidence_Log.md

Manual validation is outstanding. No Fellow name. Use at least 14pt in PPT/Google Slides and count this within the final 10 slides.
