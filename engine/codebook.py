"""The codebook: every field the AI labels, its allowed values and what each means.

One source of truth for the LLM prompt, output validation, the dashboard and
the human golden-set worksheet. Each field is tied to a question in the brief.
"""

FIELDS = {
    "relevance": {
        "q": "Gate: is this about staying with (or leaving) a SIP / mutual fund?",
        "multi": False,
        "values": {
            "core": "Describes starting, continuing, checking, pausing, reducing, stopping or restarting a SIP/MF investment",
            "adjacent": "About MFs/SIPs on a platform but not continuation (e.g. one-off KYC, generic app praise)",
            "not_relevant": "Not about SIPs or mutual funds (stocks only, US stocks, credit cards, spam)",
        },
    },
    "product": {
        "q": "Which platform is this experience about?",
        "multi": False,
        "values": {"indmoney": "INDmoney", "other_platform": "Another app/platform",
                   "general": "No specific platform"},
    },
    "investor_experience": {
        "q": "Segment: how experienced is the investor? (explicit evidence only)",
        "multi": False,
        "values": {
            "first_time_explicit": "Says this is their first SIP / first time investing in MFs",
            "early": "Says they started within the last ~12 months, first-time status unclear",
            "experienced": "States multi-year or prior investing history",
            "unknown": "Not stated or contradictory",
        },
    },
    "journey_stage": {
        "q": "Where in the first-12-month journey is the person?",
        "multi": False,
        "values": {
            "considering_start": "Thinking about starting",
            "onboarding": "Setting up account / KYC / first SIP",
            "first_months": "Explicitly in the first ~3 months",
            "ongoing": "Continuing an existing SIP",
            "considering_stop": "Asking or thinking about pausing, reducing or stopping (not yet done)",
            "reduced_or_paused": "Has reduced, skipped or paused",
            "stopped": "Has stopped/cancelled or let it lapse",
            "restarted": "Stopped earlier and started again",
            "unknown": "Cannot tell",
        },
    },
    "start_motivation": {
        "q": "Q1: Why do people start a SIP?",
        "multi": True,
        "values": {
            "long_term_wealth": "Build wealth / beat inflation / retirement",
            "specific_goal": "A named goal (house, child, emergency fund, trip)",
            "tax_saving": "ELSS / tax saving",
            "someone_suggested": "Family, friend, colleague or creator told them to",
            "discipline_habit": "Wanted a saving discipline/habit",
            "trend": "Started because 'everyone is doing it'",
            "unknown": "Not stated",
        },
    },
    "expectation": {
        "q": "Q1: What did they expect to happen?",
        "multi": False,
        "values": {
            "quick_visible_gains": "Expected noticeable gains within months",
            "steady_long_term": "Expected slow, long-term compounding",
            "no_clear_expectation": "Says they did not know what to expect",
            "unknown": "Not stated",
        },
    },
    "behaviour_change": {
        "q": "Q2: What changed in their behaviour after starting?",
        "multi": True,
        "values": {
            "checks_more": "Started checking returns more often / anxiously",
            "checks_less_forgot": "Stopped checking or forgot about the SIP",
            "increased_or_stepped_up": "Increased the amount, stepped up or added SIPs",
            "reduced_skipped_paused": "Reduced, skipped or paused instalments",
            "stopped_or_redeemed": "Stopped the SIP or redeemed",
            "switched_fund_or_app": "Moved to another fund or platform",
            "tinkering": "Keeps changing funds or allocation",
            "sought_outside_help": "Started asking others or reading/watching more",
            "none": "No change in behaviour described",
        },
    },
    "drop_trigger": {
        "q": "Q3: What leads investors to pause, reduce or stop? (primary reason)",
        "multi": False,
        "values": {
            "income_cashflow": "Job loss, salary delay, expenses, can't afford instalment",
            "returns_below_expectation": "Returns flat/underwhelming vs what they expected",
            "market_fall_red_portfolio": "Portfolio shows losses / market fell",
            "payment_mandate_failure": "Autopay/mandate/instalment failed, often unnoticed",
            "app_confusion": "Couldn't understand app, returns or how to modify",
            "needs_money_goal": "Needed the money or goal reached",
            "distrust_platform": "Lost trust in the platform / money stuck / support",
            "advice_to_stop": "Someone (person or creator) told them to stop or switch",
            "switching": "Moving to another platform or fund (not quitting investing)",
            "none": "No pause/stop reason mentioned",
        },
    },
    "check_frequency": {
        "q": "Q4: How often do they check?",
        "multi": False,
        "values": {"daily_or_more": "Daily or more", "weekly": "Weekly",
                   "monthly": "Monthly / on statement", "rarely": "Rarely / forgot about it",
                   "unknown": "Not stated"},
    },
    "what_checked": {
        "q": "Q4: What do they check?",
        "multi": True,
        "values": {
            "total_returns": "Total gain/loss or current value",
            "daily_change": "1-day change",
            "xirr_cagr": "XIRR / CAGR / annualised return",
            "instalment_status": "Whether the instalment went through",
            "compare_others": "Comparing with others / other funds / FD",
            "unknown": "Not stated",
        },
    },
    "in_app_pain": {
        "q": "Q5: What confuses or worries them inside the app?",
        "multi": True,
        "values": {
            "mandate_autopay": "Setting up / limits / errors with autopay or mandate",
            "failed_or_missed_instalment": "Instalment failed, skipped, or deducted wrongly",
            "returns_display": "Returns, XIRR or P&L shown confusingly or changed",
            "modify_pause_flow": "Hard to pause/skip/reduce/stop or unclear what it does",
            "tracking_sync": "External portfolio sync/tracking wrong or missing",
            "kyc_onboarding": "KYC, account opening, verification",
            "support": "Support slow/unhelpful, money stuck",
            "bugs_ui_change": "App bugs, crashes, unwanted UI changes",
            "charges_transparency": "Hidden charges, regular vs direct, unclear fees",
            "none": "No in-app issue",
        },
    },
    "outside_app": {
        "q": "Q6: What do they do outside the app when unsure?",
        "multi": True,
        "values": {
            "reddit_forum": "Asks on Reddit or a forum",
            "youtube_creator": "Watches YouTube / finfluencers",
            "friends_family": "Asks friends, family, colleagues",
            "professional": "Asks an advisor / CA / MFD",
            "other_tool": "Uses another app, calculator or spreadsheet",
            "none": "Not mentioned",
        },
    },
    "continuation_driver": {
        "q": "Q7: What keeps continuers going?",
        "multi": True,
        "values": {
            "automation_habit": "It's automatic / forgot about it in a good way",
            "long_term_belief": "Believes in staying invested long term",
            "goal_progress": "Sees progress toward a goal",
            "reassurance_education": "Was reassured or learned volatility is normal",
            "affordable_amount": "Amount is small enough not to hurt",
            "none": "Not mentioned",
        },
    },
    "income_stability": {
        "q": "Q8 segment: income stability (explicit only)",
        "multi": False,
        "values": {"stable_salaried": "Salaried / stable", "variable_income": "Freelance, business, gig",
                   "student_no_income": "Student or no income", "income_shock": "Recent job loss / pay cut",
                   "unknown": "Not stated"},
    },
    "age_band": {
        "q": "Q8 segment: age (explicit only, never guessed)",
        "multi": False,
        "values": {"under_25": "Under 25 / student / first job", "25_34": "25-34",
                   "35_plus": "35+", "unknown": "Not stated"},
    },
    "money_source": {
        "q": "Q8 segment: where the SIP money comes from",
        "multi": False,
        "values": {"salary": "Monthly salary", "savings": "Existing savings",
                   "family_money": "Parents / pocket money", "windfall": "Bonus / one-off",
                   "unknown": "Not stated"},
    },
    "influencer": {
        "q": "Q8 segment: who influenced them to start",
        "multi": False,
        "values": {"self_research": "Own research", "family": "Family",
                   "friends_colleagues": "Friends or colleagues", "creator_media": "YouTube/Instagram/media",
                   "app_prompt": "An app prompt or offer", "unknown": "Not stated"},
    },
    "unmet_need": {
        "q": "Q9: What unmet need does this reveal? (primary)",
        "multi": False,
        "values": {
            "know_if_on_track": "Know whether my SIP is doing OK / on track for my goal",
            "understand_volatility": "Understand why returns look like this and what is normal",
            "flexible_control": "Pause/skip/reduce without losing the habit or penalties",
            "reliable_payments": "Instalments that just work, and clear alerts when they don't",
            "neutral_help_when_unsure": "Neutral, non-advisory help at a moment of doubt",
            "goal_link": "See the SIP connected to a personal goal",
            "trust_support": "Trustworthy platform and responsive support",
            "clear_costs": "Clear costs and plan type",
            "none": "No unmet need expressed",
        },
    },
    "continuation_risk": {
        "q": "How close is this to a lapsed SIP?",
        "multi": False,
        "values": {"0": "No risk signal", "1": "Friction or doubt",
                   "2": "Considering pause/reduce/stop", "3": "Paused, reduced or stopped"},
    },
}

FREE_TEXT = {
    "need_text": "The unmet need in the person's terms, max 12 words, no advice",
    "quote": "Exact substring of the record supporting the most important label (8-200 chars)",
    "reason": "Why these labels, max 25 words",
}

SEGMENT_FIELDS = ["investor_experience", "income_stability", "age_band",
                  "money_source", "influencer"]
UNKNOWNISH = {"unknown", "none", "0"}


def allowed(field):
    return set(FIELDS[field]["values"])


def describe_for_prompt():
    lines = []
    for name, f in FIELDS.items():
        kind = "LIST of" if f["multi"] else "ONE of"
        vals = "; ".join(f"{k} = {v}" for k, v in f["values"].items())
        lines.append(f"- {name} ({kind}): {vals}")
    for name, d in FREE_TEXT.items():
        lines.append(f"- {name} (string): {d}")
    return "\n".join(lines)


def label(field, value):
    return FIELDS[field]["values"].get(value, value)
