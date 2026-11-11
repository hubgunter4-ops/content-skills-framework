"""Smoke test: la skill devuelve fragmentos con procedencia o un aviso claro."""
import json, subprocess, sys
from pathlib import Path

def test_smoke():
    skill = Path(__file__).resolve().parents[1]
    out = subprocess.run(
        [sys.executable, str(skill / "run.py"), "-i", str(skill / "input.example.json")],
        capture_output=True, text=True, timeout=60,
    )
    assert out.returncode == 0, out.stderr
    result = json.loads(out.stdout)
    assert result["skill"] == "busqueda-de-conocimiento-en-git"
    assert result["status"] == "ready"
    assert result["deliverable"], "sin fragmentos para el ejemplo"
    first = result["deliverable"][0]
    for key in ("repo", "file", "start_line", "license", "code"):
        assert key in first, f"falta {key} en el fragmento"
    assert "get_vid_from_url" in first["code"]
