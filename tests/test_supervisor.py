from __future__ import annotations

from pathlib import Path
import json
import tempfile
import textwrap
import unittest
from unittest.mock import patch

from toolkit import QuotaManager, QuotaPolicy, SandboxPolicy, Status, Supervisor, get_policy, safe_environment

ROOT = Path(__file__).resolve().parents[1]


def write_script(directory: str, body: str) -> Path:
    path = Path(directory) / "worker.py"
    path.write_text(textwrap.dedent(body), encoding="utf-8")
    return path


class SupervisorTests(unittest.TestCase):
    def test_supervisor_reserves_and_releases_quota(self):
        with tempfile.TemporaryDirectory() as directory:
            script = write_script(directory, "print('{\"status\": \"ready\"}')")
            policy = QuotaPolicy("worker", max_concurrent=1, burst=1, rate_per_second=10)
            quotas = QuotaManager({"host": policy})
            result = Supervisor(root=ROOT, quota_manager=quotas).run_script(script, {}, quota_scopes=("host",))
        self.assertEqual(result.result.status, Status.READY)
        snapshot = quotas.snapshot()[0]
        self.assertEqual(snapshot.active, 0)
        self.assertEqual(snapshot.accepted, 1)
        self.assertEqual(snapshot.released, 1)

    def test_builtin_tool_runs_through_supervisor_protocol(self):
        script = ROOT / "toolkit/phase-2-datos/validacion-de-datos/run.py"
        input_path = script.parent / "input.example.json"
        payload = json.loads(input_path.read_text(encoding="utf-8"))
        result = Supervisor(root=ROOT).run_script(script, payload)
        self.assertIn(result.result.status, {Status.READY, Status.NEEDS_INPUT, Status.ERROR})
        self.assertEqual(result.isolation, "subprocess-limited")

    def test_successful_json_worker_uses_temp_workspace(self):
        with tempfile.TemporaryDirectory() as directory:
            script = write_script(directory, """
                import json, sys
                payload = json.load(open(sys.argv[2]))
                print(json.dumps({"status": "ready", "deliverable": {"echo": payload["value"]}}))
            """)
            result = Supervisor(root=ROOT).run_script(script, {"value": "ok"})
        self.assertEqual(result.result.status, Status.READY)
        self.assertEqual(result.result.deliverable["echo"], "ok")
        self.assertEqual(result.isolation, "subprocess-limited")

    def test_timeout_kills_worker_group(self):
        with tempfile.TemporaryDirectory() as directory:
            script = write_script(directory, """
                import time
                time.sleep(5)
            """)
            policy = SandboxPolicy("test-timeout", 0.2, 30, 1024, 1_000_000, 1_000_000, 8, 64)
            result = Supervisor(root=ROOT).run_script(script, {}, policy=policy)
        self.assertEqual(result.result.status, Status.TIMEOUT)
        self.assertEqual(result.result.error["code"], "timeout")

    def test_nonzero_worker_is_crashed(self):
        with tempfile.TemporaryDirectory() as directory:
            script = write_script(directory, "raise SystemExit(7)")
            result = Supervisor(root=ROOT).run_script(script, {})
        self.assertEqual(result.result.status, Status.WORKER_CRASHED)
        self.assertEqual(result.returncode, 7)

    def test_invalid_json_output_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            script = write_script(directory, "print('not-json')")
            result = Supervisor(root=ROOT).run_script(script, {})
        self.assertEqual(result.result.status, Status.ERROR)
        self.assertEqual(result.result.error["code"], "invalid_worker_output")

    def test_output_limit_is_enforced_without_unbounded_capture(self):
        with tempfile.TemporaryDirectory() as directory:
            script = write_script(directory, "print('x' * 2000)")
            policy = SandboxPolicy("test-output", 30, 30, 1024, 100, 1_000_000, 8, 64)
            result = Supervisor(root=ROOT).run_script(script, {}, policy=policy)
        self.assertEqual(result.result.status, Status.ERROR)
        self.assertEqual(result.result.error["code"], "output_too_large")
        self.assertGreater(result.stdout_bytes, policy.max_output_bytes)

    def test_input_limit_is_checked_before_process(self):
        with tempfile.TemporaryDirectory() as directory:
            script = write_script(directory, "print('{}')")
            policy = get_policy("untrusted")
            result = Supervisor(root=ROOT).run_script(script, {"x": "y" * policy.max_input_bytes}, policy=policy)
        self.assertEqual(result.result.error["code"], "input_too_large")
        self.assertIsNone(result.returncode)

    def test_missing_script_is_error(self):
        with tempfile.TemporaryDirectory() as directory:
            result = Supervisor(root=ROOT).run_script(Path(directory) / "missing.py", {})
        self.assertEqual(result.result.error["code"], "script_not_found")

    def test_environment_does_not_include_secret_markers(self):
        with patch.dict("os.environ", {"FRAMEWORK_TEST_TOKEN": "inherited-secret", "PATH": "/usr/bin"}, clear=True):
            environment = safe_environment()
        self.assertNotIn("FRAMEWORK_TEST_TOKEN", environment)
        self.assertNotIn("OPENAI_API_KEY", environment)
        self.assertEqual(environment["PATH"], "/usr/bin")

    def test_policy_rejects_unknown_profile(self):
        with self.assertRaises(ValueError):
            get_policy("does-not-exist")


if __name__ == "__main__":
    unittest.main()
