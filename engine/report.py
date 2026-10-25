"""Generate a draft AI Evidence Log (markdown) from the engine's real outputs.

  python run.py evidence-log  ->  docs/AI_Evidence_Log_draft.md

Everything numeric is pulled from files. Sections marked TODO are for the
researcher to write (e.g. the 2-3 corrections), never auto-generated.
"""
import json
from datetime import date

from engine import codebook as CB
from engine import config as C


def _load(path, default=None):
    return json.loads(path.read_text()) if path.exists() else default


def run():
    funnel = _load(C.PROCESSED / "funnel.json", {})
    an = _load(C.PROCESSED / "analysis.json", {})
    gold = _load(C.EVAL / "golden_report.json")
    runs_p = C.PROCESSED / "classify_runs.jsonl"
    runs = [json.loads(x) for x in runs_p.read_text().splitlines() if x.strip()] if runs_p.exists() else []
    cov = an.get("coverage", {})
    L = [f"# AI Evidence Log — INDmoney SIP Discovery Engine",
         f"_Draft generated {date.today()} from engine outputs. Prompt version {C.PROMPT_VERSION}._", "",
         "## 1. Sources and volume analysed", "",
         "| Source | Collected | Unique | SIP-related candidates | Core evidence (AI) |",
         "|---|---|---|---|---|"]
    core_src = cov.get("core_by_source", {})
    for src, f in funnel.items():
        if src == "_total":
            continue
        L.append(f"| {src} | {f['collected']} | {f['after_dedupe']} | {f['candidates']} | {core_src.get(src, 0)} |")
    t = funnel.get("_total", {})
    L += [f"| **Total** | **{t.get('collected', 0)}** | **{t.get('after_dedupe', 0)}** | "
          f"**{t.get('candidates', 0)}** | **{sum(core_src.values())}** |", "",
          f"- AI-coded records: {cov.get('coded', 0)}; rejected by quality gates: {cov.get('rejected_by_gates', 0)}",
          f"- Relevance split: {cov.get('relevance', {})}",
          f"- Core evidence by product: {cov.get('core_by_product', {})}; distinct threads: {cov.get('core_threads', 0)}",
          f"- First-year investors (explicit) in core evidence: {cov.get('first_year_core', 0)}",
          f"- Models used: {cov.get('models', {})}", "",
          "Collection notes: TODO — list any source that failed or was thin (see data/raw/*.manifest.json).", "",
          "## 2. How the engine works", "",
          "Collect (public, no login) → prefilter in code → LLM coding against an 18-field codebook with "
          "per-output quality gates (allowed values, exact supporting quote, stage/risk consistency; one retry, "
          "then rejected) → all counts and opportunity scores computed in code → golden-set validation.", "",
          "## 3. Quality gate results", ""]
    st = cov.get("status", {})
    L += [f"- Passed first try: {st.get('passed_first_try', 0)}",
          f"- Passed after one retry: {st.get('passed_on_retry', 0)}",
          f"- Rejected and excluded: {st.get('rejected', 0)}", ""]
    if runs:
        L += ["| Run at | Coded OK | Retry OK | Rejected | API calls | Tokens |", "|---|---|---|---|---|---|"]
        for r in runs:
            L.append(f"| {r['at']} | {r.get('passed_first_try', 0)} | {r.get('passed_on_retry', 0)} | "
                     f"{r.get('rejected', 0)} | {r.get('calls', 0)} | {r.get('tokens', 0)} |")
    L += ["", "## 4. Golden set (hand-labelled by the researcher)", ""]
    if gold:
        L += [f"Blind, source-stratified sample of {gold['items_labelled']} records labelled by hand before "
              "viewing AI output.", "",
              f"- Field-level agreement: **{round(100 * gold['field_level_agreement'])}%**",
              f"- Items where every field agreed: {gold['items_fully_agreed']} / {gold['items_labelled']}", "",
              "| Field | Agree / labelled | Agreement | Cohen's kappa |", "|---|---|---|---|"]
        for f, v in gold["per_field"].items():
            L.append(f"| {f} | {v['agree']} / {v['n']} | {round(100 * (v['agreement'] or 0))}% | {v['kappa']} |")
        L += ["", "### Where the engine failed", ""]
        for it in gold["items"]:
            if it["disagreements"]:
                d = "; ".join(f"{f}: AI={x['ai']} vs human={x['human']}" for f, x in it["disagreements"].items())
                L.append(f"- **{it['id']}** ({it['source']}, [link]({it['url']})): {d}")
        L += ["", "Failure patterns: TODO — group the disagreements above into 2-4 patterns in your own words."]
    else:
        L.append("TODO — run `python run.py golden-score` after labelling data/eval/golden_worksheet.xlsx.")
    L += ["", "## 5. Where I rejected or corrected AI output (2-3)", "",
          "TODO — write these yourself from real cases (golden-set disagreements, explorer review, or "
          "opportunity-score assumptions). For each: what the AI said, what you changed, why, and the record link.",
          "", "## 6. Top opportunity areas (from code)", "",
          "| Unmet need | Mentions | Threads | % at/near lapse | % first-year | Score index |", "|---|---|---|---|---|---|"]
    for o in an.get("opportunities", [])[:8]:
        L.append(f"| {o['label']} | {o['n']} | {o['threads']} | {round(100 * o['at_risk_share'])}% | "
                 f"{round(100 * o['first_year_share'])}% | {o['score_index']} |")
    L += ["", "## 7. Limitations", "",
          "- Public feedback over-represents complaints and vocal users; not a random sample of investors.",
          "- First-time status, age and income are rarely stated; segment groups are small.",
          "- Review or post dates are not investor tenure; the engine cannot measure retention rates.",
          "- User reports are unverified claims about the product.",
          "- Opportunity scores rank where to look; controllability weights are PM judgement.", "",
          "## Appendix: codebook", ""]
    for f, d in CB.FIELDS.items():
        L.append(f"- **{f}** — {d['q']}: " + ", ".join(d["values"]))
    out = C.ROOT / "docs" / "AI_Evidence_Log_draft.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text("\n".join(L), encoding="utf-8")
    print(f"evidence log draft -> {out}")
    return out
