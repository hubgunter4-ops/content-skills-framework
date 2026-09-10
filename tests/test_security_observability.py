from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from toolkit import ExecutionMetrics, SandboxPolicy, Supervisor, redact, safe_environment
from toolkit.models import Status

ROOT = Path(__file__).resolve().parents[1]


class SecurityObservabilityTests(unittest.TestCase):
    def test_script_outside_root_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            outside = Path(directory) / "outside.py"
            outside.write_text("print('{}')", encoding="utf-8")
            result = Supervisor(root=ROOT).run_script(outside, {})
        self.assertEqual(result.result.error["code"], "script_outside_root")

    def test_symlink_script_is_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            target = Path(directory) / "target.py"
            link = Path(directory) / "link.py"
            target.write_text("print('{}')", encoding="utf-8")
            link.symlink_to(target)
            result = Supervisor(root=ROOT).run_script(link, {})
        self.assertEqual(result.result.error["code"], "script_symlink_not_allowed")

    def test_extra_secret_environment_is_filtered(self):
        environment = safe_environment(extra={"API_TOKEN": "secret", "SAFE_VALUE": "ok"})
        self.assertNotIn("API_TOKEN", environment)
        self.assertEqual(environment["SAFE_VALUE"], "ok")

    def test_redact_removes_nested_secret_values(self):
        value = redact({"api_token": "secret", "nested": {"password": "hidden", "ok": 1}})
        self.assertEqual(value["api_token"], "[REDACTED]")
        self.assertEqual(value["nested"]["password"], "[REDACTED]")
        self.assertEqual(value["nested"]["ok"], 1)

    def test_metrics_report_percentiles_and_statuses(self):
        metrics = ExecutionMetrics()
        for value in (1, 2, 3, 4, 5, 100):
            metrics.observe(value, Status.READY)
        metrics.observe(10, Status.ERROR)
        snapshot = metrics.snapshot()
        self.assertEqual(snapshot.count, 7)
        self.assertEqual(snapshot.by_status[Status.READY], 6)
        self.assertGreaterEqual(snapshot.p95_ms, snapshot.p50_ms)
        self.assertGreaterEqual(snapshot.p99_ms, snapshot.p95_ms)

    def test_metrics_cap_samples(self):
        metrics = ExecutionMetrics(max_samples=2)
        metrics.observe(1, Status.READY)
        metrics.observe(2, Status.READY)
        metrics.observe(3, Status.ERROR)
        self.assertEqual(metrics.snapshot().count, 2)
        self.assertEqual(metrics.snapshot().by_status[Status.ERROR], 1)


if __name__ == "__main__":
    unittest.main()
