"""Retrieve public Indian App Store RSS pages. Raw data stays local."""
import json
from pathlib import Path
from urllib.request import urlopen

def main():
    output = Path(__file__).resolve().parents[1] / 'data'
    for page in range(1, 11):
        url = f'https://itunes.apple.com/in/rss/customerreviews/page={page}/id=1450178837/sortby=mostrecent/json'
        try:
            with urlopen(url, timeout=25) as response:
                payload = json.load(response)
            (output / f'apple-page-{page}.json').write_text(json.dumps(payload, ensure_ascii=False))
            print(page, len(payload.get('feed', {}).get('entry', [])))
        except Exception as error:
            print(page, type(error).__name__, 'failed; excluded, not silently counted')
if __name__ == '__main__':
    main()
