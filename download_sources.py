"""Download reproducible SEC inputs; analysis replays these files offline."""
import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
import time
import requests

HERE = Path(__file__).resolve().parent
SOURCES = {
    'COST_companyfacts.json': 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000909832.json',
    'NVDA_companyfacts.json': 'https://data.sec.gov/api/xbrl/companyfacts/CIK0001045810.json',
    'JPM_companyfacts.json': 'https://data.sec.gov/api/xbrl/companyfacts/CIK0000019617.json',
    'COST_submissions.json': 'https://data.sec.gov/submissions/CIK0000909832.json',
    'NVDA_submissions.json': 'https://data.sec.gov/submissions/CIK0001045810.json',
    'VT_nport_index.html': 'https://www.sec.gov/Archives/edgar/data/857489/000085748926000275/0000857489-26-000275-index.html',
    'VT_factsheet.pdf': 'https://fund-docs.vanguard.com/F3141.pdf',
    'ben_graham_original.md': 'https://raw.githubusercontent.com/CinderZhang/FAskills/main/financial-researcher/experts/ben_graham.md',
    'warren_buffett_original.md': 'https://raw.githubusercontent.com/CinderZhang/FAskills/main/financial-researcher/experts/warren_buffett.md',
    'michael_burry_original.md': 'https://raw.githubusercontent.com/CinderZhang/FAskills/main/financial-researcher/experts/michael_burry.md',
}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--user-agent', default='Sam Stewart AIFinance2026 academic research')
    args = parser.parse_args()
    target = HERE / 'evidence' / 'raw'
    target.mkdir(parents=True, exist_ok=True)
    manifest = {}
    for name, url in SOURCES.items():
        path = target / name
        receipt = target / (name + '.receipt.json')
        if path.exists() and receipt.exists():
            meta = json.loads(receipt.read_text(encoding='utf-8'))
            assert meta['sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()
            manifest[name] = meta
            print(name, 'verified cache')
            continue
        r = None
        for attempt in range(2):
            try:
                r = requests.get(url, headers={'User-Agent': args.user_agent}, timeout=25)
                r.raise_for_status()
                break
            except requests.RequestException as exc:
                if attempt:
                    manifest[name] = {'url': url, 'status': 'not found', 'error': str(exc)}
                    print(name, 'not found', str(exc)[:100], flush=True)
                time.sleep(.5)
        if r is None or r.status_code != 200:
            continue
        print(name, r.status_code, len(r.content), flush=True)
        r.raise_for_status()
        if name.endswith('.json'):
            r.json()
        path.write_bytes(r.content)
        meta = {'url': url, 'retrieved_at_utc': datetime.now(timezone.utc).isoformat(),
                'sha256': hashlib.sha256(r.content).hexdigest(), 'bytes': len(r.content)}
        receipt.write_text(json.dumps(meta, indent=2), encoding='utf-8')
        manifest[name] = meta
        time.sleep(.3)
    (HERE / 'evidence' / 'source_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')

if __name__ == '__main__':
    main()
