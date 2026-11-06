"""Before you pause: a moment-of-doubt explainer for first-time SIP investors (concept prototype).

Run locally:  streamlit run mvp/app.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import pandas as pd  # noqa: E402
import streamlit as st  # noqa: E402

from core import facts as factsmod  # noqa: E402
from core import nav as navmod  # noqa: E402
from core import respond as resp  # noqa: E402
from core import sip  # noqa: E402
from core.llm import Groq  # noqa: E402

REPO_URL = "https://github.com/abhee05/indmoney-sip-discovery-engine"
BLUE, GREY = "#1f6feb", "#8b949e"
MODE_LABEL = {
    "ai": "Written by AI, checked by code",
    "template": "Template answer (AI off or blocked)",
    "decline_advice": "Declined: investment advice",
    "decline_prediction": "Declined: prediction",
    "fallback": "Safe fallback",
}

st.set_page_config(page_title="Before you pause · SIP prototype", page_icon="🧭", layout="centered")


# ------------------------------------------------------------------ helpers

def log(event: str, **details):
    st.session_state.setdefault("log", []).append(
        {"time": pd.Timestamp.now(tz="Asia/Kolkata").strftime("%d %b %H:%M:%S"), "event": event, **details})


@st.cache_data(ttl=6 * 3600, show_spinner=False)
def load_fund(code: int):
    return navmod.get_nav(code)


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def preset_code(key: str) -> int:
    return navmod.resolve_preset_code(navmod.load_presets()["funds"][key])


@st.cache_data(ttl=3600, show_spinner=False)
def search_funds(query: str):
    return navmod.search(query)


@st.cache_resource
def get_llm():
    return Groq()


def show_checks(a: resp.Answer):
    ok = sum(1 for c in a.checks if c["passed"])
    with st.expander(f"Quality checks: {ok} of {len(a.checks)} passed · {MODE_LABEL.get(a.mode, a.mode)}"):
        for c in a.checks:
            mark = "✓" if c["passed"] else "✗"
            st.markdown(f"{mark} **{c['name']}**: {c['detail']}")
        if a.model:
            st.caption(f"Model: {a.model}")


def show_answer(a: resp.Answer):
    st.markdown(a.text)
    for s in a.sources:
        st.caption(f"Official source: {s}")
    show_checks(a)


def chart_path(path: pd.DataFrame):
    df = path.melt("date", ["invested", "value"], var_name="series", value_name="amount")
    df["series"] = df["series"].map({"invested": "Invested so far", "value": "Current value"})
    try:
        import altair as alt
        domain = ["Current value", "Invested so far"]
        chart = alt.Chart(df).mark_line(point=True).encode(
            x=alt.X("date:T", title=None),
            y=alt.Y("amount:Q", title="Rupees"),
            color=alt.Color("series:N", scale=alt.Scale(domain=domain, range=[BLUE, GREY]),
                            legend=alt.Legend(orient="top", title=None)),
            strokeDash=alt.StrokeDash("series:N", scale=alt.Scale(domain=domain, range=[[1, 0], [6, 4]]),
                                      legend=None),
            tooltip=[alt.Tooltip("date:T", title="Date"), alt.Tooltip("series:N", title=" "),
                     alt.Tooltip("amount:Q", title="₹", format=",.0f")],
        ).properties(height=260)
        st.altair_chart(chart, width="stretch")
    except Exception:  # noqa: BLE001
        st.line_chart(path.set_index("date")[["invested", "value"]])


def chart_outcomes(outcomes: list, you: float):
    df = pd.DataFrame({"ret": outcomes})
    try:
        import altair as alt
        bars = alt.Chart(df).mark_bar(color=GREY).encode(
            x=alt.X("ret:Q", bin=alt.Bin(maxbins=30), title="Return of each past SIP of the same length (%)"),
            y=alt.Y("count():Q", title="Past SIPs"),
        )
        zero = alt.Chart(pd.DataFrame({"x": [0.0]})).mark_rule(color="#555", strokeDash=[3, 3]).encode(x="x:Q")
        mark = pd.DataFrame({"x": [you], "label": ["You"]})
        line = alt.Chart(mark).mark_rule(color=BLUE, size=3).encode(x="x:Q")
        text = alt.Chart(mark).mark_text(align="left", dx=5, dy=-6, color=BLUE, fontWeight="bold").encode(
            x="x:Q", y=alt.value(12), text="label:N")
        st.altair_chart((bars + zero + line + text).properties(height=220), width="stretch")
    except Exception:  # noqa: BLE001
        counts = pd.cut(df["ret"], bins=20).value_counts().sort_index()
        st.bar_chart(pd.Series(counts.to_numpy(), index=[f"{i.mid:.0f}%" for i in counts.index]))


def month_start(ts: pd.Timestamp, months_back: int):
    d = (ts - pd.DateOffset(months=months_back))
    return pd.Timestamp(d.year, d.month, 1).date()


# ------------------------------------------------------------------ page

st.info("**Concept prototype** for a product course project. Not affiliated with INDmoney or any app. "
        "**Not investment advice.** Fund prices are real public NAV data (AMFI, via mfapi.in). "
        "Past performance doesn't guarantee future returns.")
st.title("Before you pause")
st.caption("What a first-time investor sees when they tap Pause or Stop after their SIP turns red: "
           "their real numbers, what's normal for their fund, and every option explained, without advice.")

llm = get_llm()
tab_try, tab_how = st.tabs(["Try it", "How it works and quality"])

with tab_how:
    st.subheader("What this prototype does")
    st.markdown(
        "First-time investors often hit **Pause** or **Stop** the first time their SIP shows less than they put "
        "in. In our research, none of them got a useful explanation inside their app: they went to YouTube, "
        "Reddit, colleagues or ChatGPT, or decided alone. INDmoney's own assistant answered *\"Should I stop my "
        "SIP?\"* by showing the stop button.\n\n"
        "This screen sits between the tap and the decision:\n"
        "1. **Where you stand:** your real invested amount, current value and return, from real NAVs.\n"
        "2. **Is this normal?** How every past SIP of the same length in this fund looked at the same point, "
        "including the bad cases.\n"
        "3. **Ask anything:** plain answers about your own SIP. Fund picks and predictions are declined.\n"
        "4. **Your options:** continue, skip once, pause until a month, or stop. Stop is never hidden.")
    st.subheader("Where AI earns its place")
    st.markdown(
        "A static chart or FAQ shows everyone the same thing. The AI reads *why* someone came (\"it's red\" vs "
        "\"money is tight\" vs \"should I stop?\"), answers in their words, and explains *their* numbers. "
        "**Code does every calculation; the AI only writes sentences from those numbers, and code checks every "
        "sentence before it's shown.** If the AI is unavailable or its draft fails a check twice, a written "
        "template answer appears instead.")
    st.subheader("Quality checks on every answer")
    st.markdown(
        "- **Routing:** fund picks, buy/sell/switch questions → declined, pointing to a SEBI-registered adviser. "
        "\"When will it recover?\" → declined, with past base rates instead.\n"
        "- **Numbers match the calculation:** any number not produced by the code blocks the answer.\n"
        "- **No investment advice, no predictions, no fear or urgency:** phrase checks block the answer.\n"
        "- **History comes with its caveat:** past results must say past performance doesn't guarantee future "
        "returns.\n"
        "- **Uncertainty:** a fund with too little history gets \"not enough data to say\", not a guess.")
    st.subheader("Golden set results")
    report_path = HERE / "eval" / "report.json"
    if report_path.exists():
        report = json.loads(report_path.read_text())
        s = report["summary"]
        g1, g2, g3 = st.columns(3)
        g1.metric("Cases passed", f"{s['passed']} of {s['total']}")
        g2.metric("Right behaviour", f"{s['behaviour_correct']} of {s['total']}")
        g3.metric("All checks passed", f"{s['checks_clean']} of {s['total']}")
        st.caption(f"Run on {report['run_at']} · answers by: {report['mode']} · labels: {report['labels']}")
        st.dataframe(pd.DataFrame(report["cases"])[["id", "question", "expected", "got", "pass", "note"]],
                     width="stretch", hide_index=True)
    else:
        st.caption("No evaluation report yet. Run: python mvp/eval/run_eval.py")
    st.subheader("Status")
    st.caption(f"AI: {'connected' if llm.available else 'not configured, so template answers are shown'} · "
               f"Code: {REPO_URL}")

with tab_try:
    st.subheader("1. Set up a SIP to test")
    presets = navmod.load_presets()
    source_choice = st.radio("Start from", ["A scenario from our research", "Your own fund"], horizontal=True)

    code, amount, months, name_hint = None, 5000, 7, None
    if source_choice.startswith("A scenario"):
        scen = presets["scenarios"]
        pick = st.selectbox("Scenario", scen, format_func=lambda s: s["label"])
        st.caption(f"Story: {pick['story']} (Fund shown as an example, not a recommendation.)")
        amount, months = pick["amount"], pick["months_ago"]
        name_hint = presets["funds"][pick["fund"]]["label"]
        try:
            code = preset_code(pick["fund"])
        except Exception as e:  # noqa: BLE001
            st.error(f"Couldn't load this scenario's fund: {e}")
            st.stop()
    else:
        query = st.text_input("Search for your fund by name", placeholder="e.g. parag parikh flexi cap")
        results = []
        if query.strip():
            try:
                results = search_funds(query.strip())
            except Exception:  # noqa: BLE001
                st.error("Fund search isn't reachable right now. Try a scenario instead.")
        if not results:
            if query.strip():
                st.warning("No funds found. Try fewer words, like 'nifty 50 index'.")
            st.stop()
        choice = st.selectbox("Fund", results, format_func=lambda r: r["schemeName"])
        code = int(choice["schemeCode"])
        name_hint = choice["schemeName"]
        c1, c2 = st.columns(2)
        amount = c1.number_input("Monthly amount (₹)", min_value=100, max_value=1_000_000, value=5000, step=500)
        months = c2.slider("Months since your first instalment", min_value=1, max_value=24, value=7)

    with st.spinner("Loading real fund prices..."):
        try:
            meta, series, source = load_fund(int(code))
        except navmod.NavUnavailable as e:
            st.error(str(e))
            st.stop()
    fund_name = meta.get("scheme_name") or name_hint or "Your fund"
    category = navmod.clean_category(meta.get("scheme_category", ""))
    latest = series.index[-1]

    when = st.radio("When", ["Today", "Replay a real past dip"], horizontal=True,
                    help="Replay shows a past moment when a SIP like this was in the red, using only prices "
                         "known at that time.")
    as_of, start_month, replay_label = latest, month_start(latest, months - 1), None
    if when == "Replay a real past dip":
        dips = sip.find_dips(series, months)
        if not dips:
            st.info("This fund has no past moment where a SIP this long was more than 3% in the red. Showing today.")
        else:
            dip = st.selectbox("Pick a past moment", dips,
                               format_func=lambda d: f"{d[0]:%b %Y}: a {months}-month SIP was about {abs(d[2])}% "
                                                     f"below what had been invested")
            as_of = dip[0] - pd.Timedelta(days=1)
            start_month = dip[1].date()
            replay_label = f"{dip[0]:%b %Y}"

    try:
        res = sip.simulate(series, start_month, float(amount), as_of)
    except ValueError as e:
        st.error(str(e))
        st.stop()
    hist = sip.history_stats(series, res.instalments, res.as_of)
    f = factsmod.build(fund_name, category, res, hist, source)

    fkey = f"{code}|{amount}|{res.instalments}|{res.as_of.date()}"
    if st.session_state.get("fkey") != fkey:
        st.session_state.update(fkey=fkey, flow=None, answers=[], opening=None, choice=None)
        log("scenario", fund=fund_name, amount=int(amount), months=res.instalments, as_of=f["as_of"],
            replay=bool(replay_label))

    # ---------------------------------------------------------- portfolio card
    st.subheader("2. Your SIP")
    with st.container(border=True):
        st.markdown(f"**{fund_name}**")
        line = (f"{category} · {f['monthly_amount']} a month · {f['months_held']} · first instalment "
                f"{f['first_instalment']} · prices as of {f['as_of']}")
        if replay_label:
            line += f" · **replay of {replay_label}**"
        st.caption(line)
        m1, m2, m3 = st.columns(3)
        m1.metric("Invested", f["invested"])
        m2.metric("Current value", f["current_value"], f["gain"])
        m3.metric("Return", f["gain_pct"])
        chart_path(res.path)
        st.caption(f"Prices: {'live from mfapi.in' if source == 'live' else 'saved copy (mfapi.in unreachable)'}.")
    if not f["is_down"] and not replay_label:
        st.caption("This SIP is above what was invested today. To see the moment this screen is built for, "
                   "choose **Replay a real past dip** above, then tap Pause.")

    b1, b2, b3 = st.columns(3)
    if b1.button("Pause SIP"):
        st.session_state.flow = "pause"
        log("tapped", button="Pause SIP")
    if b2.button("Stop SIP"):
        st.session_state.flow = "stop"
        log("tapped", button="Stop SIP")
    if b3.button("Ask a question"):
        st.session_state.flow = "ask"
        log("tapped", button="Ask a question")

    flow = st.session_state.get("flow")
    if flow:
        st.divider()
        title = {"pause": "Before you pause", "stop": "Before you stop", "ask": "Your SIP, explained"}[flow]
        st.subheader(title)

        st.markdown("**Where you stand**")
        if st.session_state.get("opening") is None:
            with st.spinner("Writing your explanation..."):
                st.session_state.opening = resp.respond("", f, llm, intent="opening")
            log("opening", mode=st.session_state.opening.mode)
        with st.container(border=True):
            show_answer(st.session_state.opening)

        st.markdown("**Is this normal for this fund?**")
        if hist.sufficient:
            h1, h2, h3 = st.columns(3)
            h1.metric(f"Past {hist.months}-month SIPs below invested", f"{hist.pct_below}%")
            h2.metric("Of those, above after 12 more months",
                      f"{hist.pct_above_after_follow}%" if hist.pct_above_after_follow is not None else "n/a")
            h3.metric("Longest to get back above",
                      f"{hist.max_months_to_recover} months" if hist.max_months_to_recover is not None else "n/a")
            chart_outcomes(hist.outcomes, round(res.gain_pct, 2))
            st.caption(f"Each bar counts past SIPs of {hist.months} months in this fund, by their return at the same "
                       f"point; there are {hist.n_windows} of them, using prices up to {f['as_of']}. "
                       f"The blue line is you. Past performance doesn't guarantee future returns.")
        else:
            st.warning(resp.insufficient_sentence(f))

        st.markdown("**Ask anything about your SIP**")
        st.caption("Try: \"Is this loss normal?\" · \"What happens if I pause?\" · \"Money is tight this month\" · "
                   "\"When will it turn green?\"")
        with st.form("ask", clear_on_submit=True):
            q = st.text_input("Your question", label_visibility="collapsed",
                              placeholder="Type your question and press Ask")
            asked = st.form_submit_button("Ask")
        if asked and q.strip():
            with st.spinner("Checking..."):
                a = resp.respond(q.strip(), f, llm)
            st.session_state.answers.insert(0, (q.strip(), a))
            log("asked", question=q.strip(), intent=a.intent, mode=a.mode,
                checks_passed=sum(c["passed"] for c in a.checks), checks_total=len(a.checks))
        for question, a in st.session_state.answers:
            with st.container(border=True):
                st.markdown(f"**You:** {question}")
                show_answer(a)

        st.markdown("**Your options**")
        st.caption("All four are always here. None of them sells the units you already hold.")
        o1, o2 = st.columns(2)
        with o1:
            st.markdown("**Continue**  \nThe next instalment goes in as usual.")
            if st.button("Continue SIP"):
                st.session_state.choice = "Continue SIP"
            st.markdown("**Skip once**  \nOnly the next instalment is skipped. The SIP carries on after.")
            if st.button("Skip next instalment"):
                st.session_state.choice = "Skip next instalment"
        with o2:
            st.markdown("**Pause**  \nNo instalments until the month you pick.")
            restart_options = [(res.as_of + pd.DateOffset(months=i)).strftime("%b %Y") for i in range(2, 8)]
            restart = st.selectbox("Restart in", restart_options, label_visibility="collapsed")
            if st.button(f"Pause until {restart}"):
                st.session_state.choice = f"Pause until {restart}"
            st.markdown("**Stop**  \nNo more instalments. What you've invested stays invested.")
            if st.button("Stop SIP", key="stop_final"):
                st.session_state.choice = "Stop SIP"
        if st.session_state.get("choice"):
            choice = st.session_state.choice
            if not st.session_state.get("log") or st.session_state.log[-1].get("choice") != choice:
                log("decided", choice=choice)
            st.success(f"Prototype: nothing was changed. You chose: **{choice}**.")
            fb = st.radio("Did this screen help you decide?",
                          ["Yes, it helped", "It didn't change anything", "It made it harder"], index=None,
                          horizontal=True)
            if fb and (not st.session_state.get("log") or st.session_state.log[-1].get("feedback") != fb):
                log("feedback", feedback=fb)

    with st.expander("Session log (for user tests)"):
        rows = st.session_state.get("log", [])
        if rows:
            df = pd.DataFrame(rows)
            st.dataframe(df, width="stretch", hide_index=True)
            st.download_button("Download this session as CSV", df.to_csv(index=False).encode("utf-8"),
                               file_name="before_you_pause_session.csv", mime="text/csv")
        else:
            st.caption("Nothing yet.")
