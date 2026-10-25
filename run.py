"""INDmoney SIP Discovery Engine - pipeline runner.

  python run.py collect [--only reddit,play_store]   1. gather public feedback
  python run.py prefilter                            2. merge, dedupe, keep SIP-related
  python run.py golden-sheet                         3. blind 20-item worksheet for YOU to label
  python run.py classify [--limit 300]               4. AI coding with quality gates (resumable)
  python run.py analyze                              5. themes, segments, opportunity scores
  python run.py golden-score                         6. your labels vs AI labels
  python run.py evidence-log                         7. draft AI Evidence Log from real outputs
  python run.py all                                  1+2+3+4+5 in one go
"""
import argparse
import json
import sys


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("step", choices=["collect", "prefilter", "golden-sheet", "classify",
                                    "analyze", "golden-score", "evidence-log", "all"])
    p.add_argument("--only", help="comma-separated sources for collect")
    p.add_argument("--limit", type=int, help="max records to code in this run")
    p.add_argument("--golden", action="store_true", help="classify only the hand-labelled golden records")
    a = p.parse_args()

    if a.step in ("collect", "all"):
        from collect.sources import ALL
        names = a.only.split(",") if a.only else list(ALL)
        for name in names:
            print(f"== collecting {name}")
            try:
                ALL[name]()
            except Exception as e:  # noqa: BLE001
                print(f"[{name}] FAILED: {type(e).__name__}: {e} (other sources continue)")
    if a.step in ("prefilter", "all", "collect"):
        from engine.prefilter import run
        run()
    if a.step in ("golden-sheet", "all", "collect"):
        from engine import config as C
        from engine.golden import make_sheet
        labelled = (C.EVAL / "golden_labels.xlsx").exists() or (C.EVAL / "golden_labels.csv").exists()
        if a.step == "golden-sheet" or not labelled:
            make_sheet()
    if a.step in ("classify", "all"):
        from engine import config as C
        from engine.classify import classify
        from engine.prefilter import load_corpus
        from engine.golden import golden_ids
        priority = golden_ids()
        rows = load_corpus()
        if a.golden:
            rows = [r for r in rows if r["id"] in set(priority)]
        classify(rows, limit=a.limit, priority=priority)
    if a.step in ("analyze", "all"):
        from engine.analyze import run
        run()
    if a.step == "golden-score":
        from engine.golden import score
        score()
    if a.step in ("evidence-log", "golden-score", "all"):
        from engine.report import run as report
        report()


if __name__ == "__main__":
    sys.exit(main())
