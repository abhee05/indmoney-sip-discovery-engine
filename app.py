"""Streamlit front end for the INDmoney SIP Discovery Engine.  streamlit run app.py"""
import json

import altair as alt
import pandas as pd
import streamlit as st

from engine import analyze as A
from engine import codebook as CB
from engine import config as C

st.set_page_config(page_title="SIP Discovery Engine · INDmoney", page_icon="🔎", layout="wide")
st.markdown("""<style>
.block-container{padding-top:1.6rem;max-width:1250px}
.gate{display:inline-block;padding:2px 10px;border-radius:12px;margin:2px 6px 2px 0;font-size:0.85rem;border:1px solid #888}
.pass{background:#e7f1fb;border-color:#2b6cb0}.fail{background:#fdecea;border-color:#b42318}.partial{background:#fff4e5;border-color:#b54708}
.quote{border-left:3px solid #2b6cb0;padding:2px 10px;margin:6px 0;color:inherit}
</style>""", unsafe_allow_html=True)

st.title("SIP Discovery Engine")
st.caption("INDmoney Growth · Why first-time investors do or don't keep an active SIP for 12 months")
st.info("Research tool built on public user feedback. It does not give investment advice or recommend funds. "
        "Quotes are unverified user claims.", icon="ℹ️")


@st.cache_data(show_spinner=False)
def load():
    rows = A.load_coded()
    funnel_p = C.PROCESSED / "funnel.json"
    funnel = json.loads(funnel_p.read_text()) if funnel_p.exists() else {}
    runs_p = C.PROCESSED / "classify_runs.jsonl"
    runs = [json.loads(x) for x in runs_p.read_text().splitlines() if x.strip()] if runs_p.exists() else []
    gold_p = C.EVAL / "golden_report.json"
    gold = json.loads(gold_p.read_text()) if gold_p.exists() else None
    return rows, funnel, runs, gold


rows, funnel, runs, gold = load()
if not rows:
    st.warning("No coded data yet. Run `python run.py all` locally, then commit data/processed.")
    st.stop()

valid = [r for r in rows if r.get("status") != "rejected"]
core = [r for r in valid if r["relevance"] == "core"]

with st.sidebar:
    st.header("Lens")
    lens = st.radio("Investors included", ["All relevant feedback", "First-year investors only",
                                           "INDmoney feedback only"],
                    help="First-year = says it is their first SIP or that they started within ~12 months.")
    srcs = sorted({r["source"] for r in core})
    pick = st.multiselect("Sources", srcs, default=srcs)
if lens == "First-year investors only":
    view = [r for r in core if r["investor_experience"] in A.FIRST_YEAR]
elif lens == "INDmoney feedback only":
    view = [r for r in core if r["product"] == "indmoney"]
else:
    view = core
view = [r for r in view if r["source"] in pick]

tot = funnel.get("_total", {})
m = st.columns(5)
m[0].metric("Records collected", f"{tot.get('collected', '–'):,}" if tot else "–")
m[1].metric("SIP-related candidates", f"{tot.get('candidates', len(rows)):,}" if tot else len(rows))
m[2].metric("AI-coded (passed gates)", f"{len(valid):,}")
m[3].metric("Core continuation evidence", f"{len(core):,}")
m[4].metric("In current lens", f"{len(view):,}")

tabs = st.tabs(["Opportunity areas", "Research questions", "Continuers vs at-risk", "Segments",
                "Ask the engine", "Evidence explorer", "Quality & evals", "How it works"])


def bar(df, x, y, title=None, color="#2b6cb0"):
    if df.empty:
        st.caption("No data in this lens.")
        return
    ch = alt.Chart(df).mark_bar(color=color).encode(
        x=alt.X(f"{x}:Q", title=None), y=alt.Y(f"{y}:N", sort="-x", title=None),
        tooltip=list(df.columns)).properties(height=max(120, 28 * len(df)), title=title or "")
    st.altair_chart(ch, width="stretch")


def show_quotes(qs):
    for q in qs:
        st.markdown(f"<div class='quote'>“{q['quote']}”<br><small>{q['source']} · "
                    f"<a href='{q['url']}' target='_blank'>{q['id']}</a></small></div>",
                    unsafe_allow_html=True)


# ------------------------------------------------------------------ opportunities
with tabs[0]:
    st.subheader("Which unmet needs could move 12-month SIP continuation the most?")
    st.caption("Score = reach (how often the need appears) × closeness to a lapse (share of mentions "
               "from people considering or having stopped) × first-year weight × controllability "
               "(can the product act on it without advice or FOMO). Adjust the weights to test robustness.")
    c1, c2, c3 = st.columns(3)
    wr = c1.slider("Weight: reach", 0.0, 2.0, 1.0, 0.25)
    wk = c2.slider("Weight: closeness to lapse", 0.0, 2.0, 1.0, 0.25)
    wf = c3.slider("Weight: first-year share", 0.0, 2.0, 0.5, 0.25)
    with st.expander("Controllability assumptions (PM judgement)"):
        ctl = {k: st.slider(CB.label("unmet_need", k), 0.0, 1.0, v, 0.1, key=f"ctl_{k}")
               for k, v in A.CONTROLLABILITY.items()}
    opps = A.opportunities(view, ctl, wr, wk, wf)
    if opps:
        df = pd.DataFrame([{"Need": o["label"], "Score index": o["score_index"], "Mentions": o["n"],
                            "Threads": o["threads"], "% at/near lapse": round(100 * o["at_risk_share"]),
                            "% first-year": round(100 * o["first_year_share"]),
                            "% INDmoney": round(100 * o["indmoney_share"])} for o in opps])
        bar(df[["Need", "Score index"]], "Score index", "Need")
        st.dataframe(df, hide_index=True, width="stretch")
        for o in opps[:6]:
            with st.expander(f"{o['label']} — {o['n']} mentions, {round(100 * o['at_risk_share'])}% at/near lapse"):
                a, b = st.columns(2)
                a.markdown("**Linked stop triggers**")
                a.write(", ".join(f"{t['label']} ({t['n']})" for t in o["linked_triggers"]) or "–")
                b.markdown("**Linked in-app pains**")
                b.write(", ".join(f"{t['label']} ({t['n']})" for t in o["linked_pains"]) or "–")
                st.markdown("**How users put it:** " + " · ".join(f"_{p}_" for p in o["need_phrases"][:6]))
                show_quotes(o["quotes"])
    else:
        st.caption("No needs in this lens.")

# ------------------------------------------------------------------ questions
with tabs[1]:
    st.caption("Share = % of records in this lens carrying that label. One record can carry several "
               "labels for list fields. 'Unknown/none' is excluded from charts but counted in the base.")
    for q, fields in A.QUESTION_FIELDS:
        st.subheader(q)
        cols = st.columns(len(fields))
        for col, f in zip(cols, fields):
            with col:
                d = A.distribution(view, f)
                df = pd.DataFrame([{"Label": x["label"], "% of records": round(100 * x["share"], 1),
                                    "n": x["n"], "threads": x["threads"]} for x in d])
                bar(df, "% of records", "Label", CB.FIELDS[f]["q"])
                if d:
                    with st.expander("Example quotes"):
                        for x in d[:4]:
                            st.markdown(f"**{x['label']}**")
                            show_quotes(x["quotes"][:2])

# ------------------------------------------------------------------ compare
with tabs[2]:
    cmp = A.compare_groups(view, A.COMPARE_FIELDS)
    g = cmp["group_sizes"]
    st.subheader("What separates people near a lapse from people who keep going?")
    st.caption(f"At-risk = considering or having paused/stopped (n={g['at_risk']}). Continuing = ongoing, "
               f"restarted or in first months with no stop signal (n={g['continuing']}). Difference = "
               "percentage-point gap in how often each label appears. Small groups are flagged.")
    if cmp["rows"]:
        df = pd.DataFrame(cmp["rows"])
        df["Label"] = df["field"].map(lambda f: f.replace("_", " ")) + ": " + df["label"]
        top = df.head(20)
        ch = alt.Chart(top).mark_bar().encode(
            x=alt.X("difference_pts:Q", title="At-risk minus continuing (pct points)"),
            y=alt.Y("Label:N", sort="-x", title=None),
            color=alt.condition(alt.datum.difference_pts > 0, alt.value("#b54708"), alt.value("#2b6cb0")),
            tooltip=["Label", "at_risk_n", "at_risk_share", "continuing_n", "continuing_share", "low_sample"]
        ).properties(height=28 * len(top))
        st.altair_chart(ch, width="stretch")
        st.caption("Orange = more common among at-risk; blue = more common among continuers.")
        st.dataframe(df.drop(columns=["field", "value", "label"]), hide_index=True, width="stretch")

# ------------------------------------------------------------------ segments
with tabs[3]:
    st.caption("Only explicitly stated attributes are used; most records don't state them, so groups are small.")
    seg = A.segments(view)
    for f, groups in seg.items():
        st.subheader(CB.FIELDS[f]["q"])
        if not groups:
            st.caption("Not enough explicit evidence.")
            continue
        st.dataframe(pd.DataFrame([{
            "Group": s["label"], "n": s["n"], "% at/near lapse": round(100 * s["at_risk_share"]),
            "Top triggers": ", ".join(f"{t['label']} ({t['n']})" for t in s["top_triggers"]),
            "Top needs": ", ".join(f"{t['label']} ({t['n']})" for t in s["top_needs"]),
            "Small sample": "yes" if s["low_sample"] else ""} for s in groups]),
            hide_index=True, width="stretch")

# ------------------------------------------------------------------ ask
with tabs[4]:
    from engine.ask import ask
    st.subheader("Ask a research question")
    st.caption("Answers are generated only from matching records, and pass four visible gates: "
               "scope (no investment advice), enough evidence, every claim cited with an exact quote, "
               "and numbers computed in code. If a gate fails you get the evidence, not an AI guess.")
    examples = ["Why do people stop their SIP in the first year?",
                "What confuses users about returns in the app?",
                "What happens when an autopay or mandate fails?",
                "What do investors do when they are unsure whether to continue?"]
    ex = st.selectbox("Try an example or write your own", [""] + examples)
    q = st.text_input("Question", value=ex, max_chars=300)
    if st.button("Ask", type="primary") and q.strip():
        with st.spinner("Retrieving evidence and checking the answer…"):
            res = ask(q, view)
        st.markdown(" ".join(f"<span class='gate {s}'>{n}: {s} — {d}</span>" for n, s, d in res["gates"]),
                    unsafe_allow_html=True)
        if res["status"] == "answered":
            for c in res["claims"]:
                st.markdown(f"- {c['text']}")
                for e in c["evidence"]:
                    st.caption(f"   ↳ {e['id']}: “{e['quote']}”")
            if res.get("caveats"):
                st.caption("Caveats: " + res["caveats"])
        else:
            st.warning(res["message"])
        if res.get("counts"):
            with st.expander("Code-computed counts for the matched records"):
                st.json(res["counts"])
        if res.get("evidence"):
            with st.expander(f"Matched evidence ({len(res['evidence'])} records)"):
                for r in res["evidence"]:
                    st.markdown(f"**{r['id']}** · {r['source']} · [open]({r['url']})  \n{r['text'][:400]}")

# ------------------------------------------------------------------ explorer
with tabs[5]:
    c1, c2, c3 = st.columns(3)
    f_stage = c1.multiselect("Journey stage", list(CB.FIELDS["journey_stage"]["values"]))
    f_trig = c2.multiselect("Stop trigger", list(CB.FIELDS["drop_trigger"]["values"]))
    f_need = c3.multiselect("Unmet need", list(CB.FIELDS["unmet_need"]["values"]))
    text = st.text_input("Search text")
    ex_rows = [r for r in view if (not f_stage or r["journey_stage"] in f_stage)
               and (not f_trig or r["drop_trigger"] in f_trig)
               and (not f_need or r["unmet_need"] in f_need)
               and (not text or text.lower() in (r.get("title", "") + r["text"]).lower())]
    st.caption(f"{len(ex_rows)} records")
    for r in ex_rows[:150]:
        with st.expander(f"{r['id']} · {r['source']} · {CB.label('journey_stage', r['journey_stage'])} · "
                         f"{CB.label('drop_trigger', r['drop_trigger'])}"):
            if r.get("title"):
                st.markdown(f"**{r['title']}**")
            st.write(r["text"][:1500])
            st.caption(f"AI quote: “{r['quote']}” · reason: {r.get('reason', '')} · model: {r.get('model')}")
            st.json({f: r[f] for f in CB.FIELDS}, expanded=False)
            st.markdown(f"[Open original]({r['url']})")

# ------------------------------------------------------------------ quality
with tabs[6]:
    st.subheader("Gate results on every AI output")
    status = pd.Series([r.get("status") for r in rows]).value_counts()
    c = st.columns(4)
    c[0].metric("Passed first try", int(status.get("passed_first_try", 0)))
    c[1].metric("Passed after one retry", int(status.get("passed_on_retry", 0)))
    c[2].metric("Rejected (excluded)", int(status.get("rejected", 0)))
    c[3].metric("Models used", ", ".join(sorted({str(r.get('model')) for r in rows})))
    st.caption("Gates: allowed values only · quote must exist verbatim in the record · stage/risk consistency.")
    rej = [r for r in rows if r.get("status") == "rejected"]
    if rej:
        with st.expander("Rejected outputs and why"):
            for r in rej[:50]:
                st.write(r["id"], r.get("gate_errors"))
    st.subheader("Golden set: hand labels vs AI")
    if gold:
        st.metric("Field-level agreement", f"{100 * gold['field_level_agreement']:.0f}%",
                  help="Share of (item, field) pairs where AI matched the human label.")
        st.dataframe(pd.DataFrame([{"Field": f, "Agree": v["agree"], "Labelled": v["n"],
                                    "Agreement %": round(100 * (v["agreement"] or 0)), "Cohen's kappa": v["kappa"]}
                                   for f, v in gold["per_field"].items()]), hide_index=True)
        for it in gold["items"]:
            if it["disagreements"]:
                with st.expander(f"{it['id']} · {it['source']} · {len(it['disagreements'])} disagreement(s)"):
                    st.write(it["text"])
                    st.json(it["disagreements"])
                    st.caption(f"AI reason: {it['ai_reason']}")
    else:
        st.caption("Golden-set report not generated yet.")
    if runs:
        with st.expander("Classification run log"):
            st.dataframe(pd.DataFrame(runs), hide_index=True)

# ------------------------------------------------------------------ how
with tabs[7]:
    st.markdown("""
**Pipeline** (code: `run.py`)

1. **Collect** public feedback: Google Play and App Store reviews of INDmoney, Reddit posts and comments
   from Indian investing subreddits, TradingQ&A threads and YouTube comments on SIP videos. Authors are
   stored only as one-way hashes.
2. **Prefilter** (code, no AI): dedupe and keep records that mention SIPs/mutual funds, or comments inside
   SIP threads.
3. **AI coding** (Groq LLM, temperature 0): every candidate record is labelled against an 18-field
   codebook mapped to the brief's questions: journey stage, why they started, what they expected, stop
   trigger, what they check, in-app pain, outside-app behaviour, segment signals and the unmet need.
4. **Quality gates on every output**: allowed values only, an exact supporting quote from the record,
   and logical consistency. Failures get one retry, then are rejected and excluded.
5. **Analysis in code**: theme shares, continuers vs at-risk comparison, segment splits, and an
   opportunity score per unmet need. No number is produced by the LLM.
6. **Validation**: a blind, source-stratified golden set of 20 records hand-labelled by the researcher;
   agreement and kappa per field are reported in *Quality & evals*.
7. **Ask the engine**: grounded Q&A with four visible gates and safe fallbacks.

**Limits**: public feedback over-represents complaints and vocal users; first-time status, age and income
are rarely stated; review dates are not investor tenure; this cannot measure retention rates — it ranks
where to look, which primary research then validates.
""")
    if funnel:
        st.subheader("Collection funnel by source")
        st.dataframe(pd.DataFrame(funnel).T, width="stretch")
