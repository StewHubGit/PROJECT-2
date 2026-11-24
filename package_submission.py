"""Package the finished folder and verify an offline replay from the ZIP."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile

HERE = Path(__file__).resolve().parent

def main():
    v = json.loads((HERE / 'evidence/validation.json').read_text(encoding='utf-8'))
    audit = json.loads((HERE / 'evidence/memo_audit.json').read_text(encoding='utf-8'))
    assert v['all_pass'] and audit['all_pass'] and audit['memos_checked'] == 12
    summary = (f"# Validation result\n\nAll {v['checks_total']} acceptance and robustness checks passed. "
               f"The COST known answer matches across {v['cost_comparison_cells']} financial/date cells and all investor verdicts. "
               f"All {audit['memos_checked']} saved memos pass the numeric provenance flag.\n\n"
               "The actual all-memo traversal was tested with an unsupported number injected separately into each investor's memo. "
               "Each injected claim was flagged. The temporary injected claims are not in the submitted memos.\n\n"
               "Changing a copy of Graham's skill rules to the lower threshold changes the expected verdict without changing raw facts or the other investors. "
               "The retained baseline is unchanged. Real bank gaps and a deliberately missing annual cash-flow fact remain unknown. "
               "A future-filed comparative fact is excluded.\n\n"
               "All three SKILL.md files also passed the bundled skill-creator quick validator. "
               "That validator verifies skill format, not investment quality.\n\n"
               "See validation.json and memo_audit.json for individual checks.\n")
    (HERE / 'evidence/VALIDATION_SUMMARY.md').write_text(summary, encoding='utf-8')
    files = sorted(p for p in HERE.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p.name != 'MANIFEST.json')
    manifest = {str(p.relative_to(HERE)).replace('\\', '/'): {'bytes': p.stat().st_size, 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in files}
    (HERE / 'MANIFEST.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    archive = HERE.parent / 'Lab19_Submission.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=7) as z:
        for p in files + [HERE / 'MANIFEST.json']:
            z.write(p, str(Path(HERE.name) / p.relative_to(HERE)))
    with zipfile.ZipFile(archive) as z:
        assert z.testzip() is None
        with tempfile.TemporaryDirectory(prefix='lab19_replay_') as temp:
            z.extractall(temp)
            root = Path(temp) / HERE.name
            for name, meta in manifest.items():
                assert hashlib.sha256((root / name).read_bytes()).hexdigest() == meta['sha256'], name
            for script in ['panel.py', 'validate.py']:
                run = subprocess.run([sys.executable, '-I', script] if script == 'panel.py' else [sys.executable, script], cwd=root, capture_output=True, text=True)
                assert run.returncode == 0, run.stdout[-3000:] + run.stderr[-3000:]
            replay = json.loads((root / 'evidence/validation.json').read_text(encoding='utf-8'))
            assert replay['all_pass'] and replay['checks_total'] == v['checks_total']
    print(json.dumps({'archive': str(archive), 'bytes': archive.stat().st_size, 'files': len(files)+1,
                      'zip_integrity': 'pass', 'extracted_file_checksums': 'pass',
                      'offline_extracted_replay': 'pass', 'acceptance_checks': v['checks_total'],
                      'memos_audited': audit['memos_checked']}, indent=2))

if __name__ == '__main__':
    main()
