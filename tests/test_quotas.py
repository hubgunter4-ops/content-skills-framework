from __future__ import annotations

import unittest
import time

from toolkit import QuotaManager, QuotaPolicy
from toolkit.errors import QuotaExceededError


class QuotaTests(unittest.TestCase):
    def manager(self, **kwargs):
        policy = QuotaPolicy("default", **kwargs)
        return QuotaManager({"host": policy, "tool": policy, "tenant": policy})

    def test_burst_and_rate_reject_then_refill(self):
        manager = self.manager(max_concurrent=2, burst=1, rate_per_second=100)
        lease = manager.reserve(("host",), input_bytes=10)
        with self.assertRaises(QuotaExceededError):
            manager.reserve(("host",), input_bytes=10)
        lease.release()
        time.sleep(0.02)
        next_lease = manager.reserve(("host",), input_bytes=10)
        next_lease.release()
        snapshot = {item.scope: item for item in manager.snapshot()}["host"]
        self.assertEqual(snapshot.accepted, 2)
        self.assertEqual(snapshot.released, 2)

    def test_concurrency_is_composed_across_scopes(self):
        policy = QuotaPolicy("scoped", max_concurrent=1, burst=10, rate_per_second=10)
        manager = QuotaManager({"host": policy, "phase-2-datos": policy, "tenant-a": policy})
        lease = manager.reserve(("host", "phase-2-datos", "tenant-a"))
        with self.assertRaises(QuotaExceededError):
            manager.reserve(("host", "phase-2-datos", "tenant-a"))
        lease.release()
        manager.reserve(("host", "phase-2-datos", "tenant-a")).release()

    def test_input_limit_rejects_before_reservation(self):
        manager = self.manager(max_input_bytes=10)
        with self.assertRaises(QuotaExceededError):
            manager.reserve(("host",), input_bytes=11)
        snapshot = {item.scope: item for item in manager.snapshot()}["host"]
        self.assertEqual(snapshot.active, 0)
        self.assertEqual(snapshot.rejected, 1)

    def test_most_restrictive_output_and_duration_limits_win(self):
        manager = QuotaManager({
            "host": QuotaPolicy("host", max_concurrent=2, burst=2, rate_per_second=10, max_output_bytes=100, max_duration_seconds=10),
            "tool": QuotaPolicy("tool", max_concurrent=2, burst=2, rate_per_second=10, max_output_bytes=50, max_duration_seconds=2),
        })
        lease = manager.reserve(("host", "tool"))
        with self.assertRaises(QuotaExceededError):
            lease.release(output_bytes=51)
        self.assertEqual({item.scope: item for item in manager.snapshot()}["tool"].active, 0)

    def test_duplicate_scopes_are_reserved_once(self):
        manager = self.manager(max_concurrent=1, burst=2, rate_per_second=10)
        lease = manager.reserve(("host", "host", "tool"))
        lease.release()
        snapshot = {item.scope: item for item in manager.snapshot()}["host"]
        self.assertEqual(snapshot.accepted, 1)
        self.assertEqual(snapshot.released, 1)

    def test_lease_is_idempotent(self):
        manager = self.manager(max_concurrent=1, burst=2, rate_per_second=10)
        lease = manager.reserve(("host",))
        lease.release()
        lease.release()
        snapshot = {item.scope: item for item in manager.snapshot()}["host"]
        self.assertEqual(snapshot.released, 1)


if __name__ == "__main__":
    unittest.main()
