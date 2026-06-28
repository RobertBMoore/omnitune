import os, tempfile, unittest
import sync_state as S


class TestSyncState(unittest.TestCase):
    def test_roundtrip_and_per_session_map(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, ".sync-state.json")
            S.record(p, "sessA", "snooze", model_seen="claude-fable-5", snooze_until="2099-01-01T00:00:00")
            S.record(p, "sessB", "skip", model_seen="claude-fable-5")
            st = S.load_state(p)
            self.assertIn("sessA", st)
            self.assertIn("sessB", st)              # B did not clobber A
            self.assertEqual(st["sessA"]["decision"], "snooze")
            self.assertEqual(st["sessB"]["decision"], "skip")

    def test_corrupt_file_resets_not_raises(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, ".sync-state.json")
            with open(p, "w") as f:
                f.write("{ this is not json")
            self.assertEqual(S.load_state(p), {})   # tolerate-and-reset
            # a record after corruption still succeeds
            S.record(p, "sessA", "skip")
            self.assertIn("sessA", S.load_state(p))

    def test_snooze_future_is_active_past_is_expired(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, ".sync-state.json")
            S.record(p, "sessA", "snooze", snooze_until="2099-01-01T00:00:00Z")
            st = S.load_state(p)
            self.assertTrue(S.is_snoozed(st, "sessA", "2026-06-14T00:00:00Z"))
            self.assertFalse(S.is_snoozed(st, "sessA", "2099-06-14T00:00:00Z"))

    def test_malformed_or_missing_deadline_is_expired(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, ".sync-state.json")
            S.record(p, "sessA", "skip")                       # no snooze_until
            S.record(p, "sessB", "snooze", snooze_until="garbage")
            st = S.load_state(p)
            self.assertFalse(S.is_snoozed(st, "sessA", "2026-06-14T00:00:00Z"))
            self.assertFalse(S.is_snoozed(st, "sessB", "2026-06-14T00:00:00Z"))
            self.assertFalse(S.is_snoozed(st, "unknown", "2026-06-14T00:00:00Z"))

    def test_atomic_write_leaves_no_temp(self):
        with tempfile.TemporaryDirectory() as t:
            p = os.path.join(t, ".sync-state.json")
            S.record(p, "sessA", "skip")
            leftovers = [f for f in os.listdir(t) if f != ".sync-state.json"]
            self.assertEqual(leftovers, [], leftovers)


if __name__ == "__main__":
    unittest.main()
