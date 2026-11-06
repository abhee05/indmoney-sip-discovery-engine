"""Saves NAV history for the preset funds into mvp/data/navs/ and fills their scheme codes.

Run once from the repo root before pushing (needs internet):
    python mvp/scripts/cache_navs.py
Check the printed fund names: each should be the Direct, Growth plan of the fund in the label.
The app still fetches live prices; these copies are only used if mfapi.in is down.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core import nav  # noqa: E402


def main():
    presets = nav.load_presets()
    nav.CACHE_DIR.mkdir(parents=True, exist_ok=True)
    for key, fund in presets["funds"].items():
        try:
            match = nav.best_match(fund["query"], nav.search(fund["query"], limit=200))
            if not match:
                print(f"  {key}: NOT FOUND for '{fund['query']}', edit the query in data/presets.json")
                continue
            code = int(match["schemeCode"])
            payload = nav.fetch_live(code)
            nav.cache_path(code).write_text(json.dumps(payload))
            fund["scheme_code"] = code
            fund["resolved_name"] = match["schemeName"]
            meta, series = nav.parse(payload)
            print(f"  {key}: {code} {match['schemeName']} | {len(series)} NAVs "
                  f"{series.index[0]:%d %b %Y} to {series.index[-1]:%d %b %Y}")
        except Exception as e:  # noqa: BLE001
            print(f"  {key}: failed ({e})")
    nav.PRESETS_FILE.write_text(json.dumps(presets, ensure_ascii=False, indent=2))
    print("Saved. Commit mvp/data/ with the rest.")


if __name__ == "__main__":
    main()
