from pathlib import Path
import json, subprocess, sys
def test_example_runs():
    folder = Path(__file__).resolve().parents[1]
    payload = json.loads((folder / "input.example.json").read_text(encoding="utf-8"))
    result = subprocess.run([sys.executable, str(folder / "run.py")], input=json.dumps(payload), text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout)["status"] == "ready"
