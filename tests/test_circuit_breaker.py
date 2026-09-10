from __future__ import annotations

import time
import unittest

from toolkit import CircuitBreakerManager, CircuitOpenError, CircuitPolicy, CircuitState


class CircuitBreakerTests(unittest.TestCase):
    def manager(self, **kwargs):
        return CircuitBreakerManager(CircuitPolicy(**kwargs))

    def test_closed_opens_after_threshold_and_blocks_worker_creation(self):
        manager = self.manager(failure_threshold=2, cooldown_seconds=0.05, failure_window_seconds=1)
        manager.acquire("tool").failure("error")
        self.assertEqual(manager.snapshot("tool").state, CircuitState.CLOSED)
        manager.acquire("tool").failure("worker_crashed")
        snapshot = manager.snapshot("tool")
        self.assertEqual(snapshot.state, CircuitState.OPEN)
        self.assertEqual(snapshot.opened_count, 1)
        with self.assertRaises(CircuitOpenError):
            manager.acquire("tool")

    def test_half_open_allows_one_probe_and_failed_probe_reopens(self):
        manager = self.manager(failure_threshold=1, cooldown_seconds=0.03, failure_window_seconds=1)
        manager.acquire("tool").failure("timeout")
        time.sleep(0.04)
        probe = manager.acquire("tool")
        self.assertEqual(manager.snapshot("tool").state, CircuitState.HALF_OPEN)
        with self.assertRaises(CircuitOpenError):
            manager.acquire("tool")
        probe.failure("timeout")
        self.assertEqual(manager.snapshot("tool").state, CircuitState.OPEN)

    def test_successful_probe_closes_and_clears_failure_window(self):
        manager = self.manager(failure_threshold=1, cooldown_seconds=0.03, failure_window_seconds=1)
        manager.acquire("tool").failure("error")
        time.sleep(0.04)
        manager.acquire("tool").success()
        snapshot = manager.snapshot("tool")
        self.assertEqual(snapshot.state, CircuitState.CLOSED)
        self.assertEqual(snapshot.failures_in_window, 0)

    def test_non_counted_status_does_not_open(self):
        manager = self.manager(failure_threshold=1, count_statuses=frozenset({"timeout"}))
        manager.acquire("tool").failure("quota_exceeded")
        self.assertEqual(manager.snapshot("tool").state, CircuitState.CLOSED)

    def test_failure_window_expires(self):
        manager = self.manager(failure_threshold=2, failure_window_seconds=0.03, cooldown_seconds=0.03)
        manager.acquire("tool").failure("error")
        time.sleep(0.04)
        manager.acquire("tool").failure("error")
        self.assertEqual(manager.snapshot("tool").state, CircuitState.CLOSED)

    def test_backoff_increases_after_repeated_failed_probes(self):
        manager = self.manager(failure_threshold=1, cooldown_seconds=0.02, max_backoff_seconds=0.08)
        manager.acquire("tool").failure("error")
        first = manager.snapshot("tool")
        time.sleep(0.03)
        manager.acquire("tool").failure("error")
        second = manager.snapshot("tool")
        self.assertEqual(first.state, CircuitState.OPEN)
        self.assertEqual(second.state, CircuitState.OPEN)
        self.assertGreater(second.next_probe_at - time.monotonic(), first.next_probe_at - time.monotonic())

    def test_cancelled_probe_reopens_without_counting_new_failure(self):
        manager = self.manager(failure_threshold=1, cooldown_seconds=0.02)
        manager.acquire("tool").failure("error")
        time.sleep(0.03)
        probe = manager.acquire("tool")
        probe.cancel()
        self.assertEqual(manager.snapshot("tool").state, CircuitState.OPEN)


if __name__ == "__main__":
    unittest.main()
