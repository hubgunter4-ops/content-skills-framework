from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
PHASE = ROOT / 'phase-4-automatizacion'
def main() -> int:
    folders = sorted(path for path in PHASE.iterdir() if path.is_dir() and (path / 'run.py').is_file())
    failures = []
    for folder in folders:
        payload = json.loads((folder / 'input.example.json').read_text(encoding='utf-8'))
        result = subprocess.run([sys.executable, str(folder / 'run.py')], input=json.dumps(payload), text=True, capture_output=True, cwd=ROOT)
        try: output = json.loads(result.stdout)
        except json.JSONDecodeError: output = {}
        if result.returncode != 0 or output.get('status') != 'ready' or output.get('skill', {}).get('slug') != folder.name or not output.get('deliverable', {}).get('content'):
            failures.append({'slug': folder.name, 'returncode': result.returncode, 'status': output.get('status'), 'stderr': result.stderr})
    print(json.dumps({'tools': len(folders), 'passed': len(folders) - len(failures), 'failures': failures}, ensure_ascii=False, indent=2))
    return 1 if failures else 0
if __name__ == '__main__': raise SystemExit(main())
